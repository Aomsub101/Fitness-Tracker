"""
garmin_api.py

Garmin Connect API integration for V2.0.

Responsibilities:
  1. Authentication  — load credentials from .env, reuse saved session tokens
                       to avoid repeated logins and rate-limit bans.
  2. Fetching        — pull the last N days of Sleep and Activity data as JSON.
  3. Translation     — convert raw JSON responses into Pandas DataFrames whose
                       column names exactly match the V1.0 master CSVs so that
                       data_pipeline.merge_sleep / merge_activities work unchanged.

Session tokens are saved to session/ as oauth1_token.json + oauth2_token.json (git-ignored).
"""

import datetime
import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logger = logging.getLogger(__name__)

SESSION_DIR = Path("session")


# ---------------------------------------------------------------------------
# Phase 2: Authentication
# ---------------------------------------------------------------------------

def get_garmin_client() -> Garmin:
    """Return an authenticated Garmin API client.

    Strategy:
      1. If session/oauth1_token.json exists, try to restore the session via
         garth (client.login(tokenstore=SESSION_DIR)).
      2. If the session is missing or expired, fall back to credential login
         using GARMIN_EMAIL / GARMIN_PASSWORD from .env.
      3. On a fresh credential login, save tokens via client.garth.dump() so
         the next call can skip the password step.

    Returns:
        Authenticated Garmin client.

    Raises:
        ValueError: If credentials are missing from the environment.
        GarminConnectAuthenticationError: If credentials are rejected.
        GarminConnectConnectionError: If Garmin servers are unreachable.
        GarminConnectTooManyRequestsError: If the account is rate-limited.
    """
    load_dotenv()
    SESSION_DIR.mkdir(exist_ok=True)

    if (SESSION_DIR / "oauth1_token.json").exists():
        try:
            client = Garmin()
            client.login(tokenstore=str(SESSION_DIR))
            logger.info("Session login successful from %s.", SESSION_DIR)
            return client
        except (GarminConnectAuthenticationError, Exception) as exc:
            logger.warning("Saved session invalid (%s). Falling back to credentials.", exc)

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        raise ValueError(
            "GARMIN_EMAIL and GARMIN_PASSWORD must be set in your .env file. "
            "See .env.example for the required format."
        )

    logger.info("Logging in with credentials for %s.", email)
    client = Garmin(email, password)
    client.login()

    client.garth.dump(str(SESSION_DIR))
    logger.info("Session tokens saved to %s.", SESSION_DIR)

    return client


# ---------------------------------------------------------------------------
# Phase 3: Translation helpers
# ---------------------------------------------------------------------------

def _seconds_to_hours(seconds) -> Optional[float]:
    """Convert a seconds value to rounded hours, or None if falsy."""
    return round(seconds / 3600, 2) if seconds else None


def translate_sleep_json(daily_sleep: dict) -> dict:
    """Convert a single day's Garmin sleep API response to a V1.0-compatible row.

    Handles the nested structure returned by api.get_sleep_data():
      {
        "dailySleepDTO": {
          "calendarDate": "YYYY-MM-DD",
          "sleepTimeSeconds": ...,
          "deepSleepSeconds": ...,
          "lightSleepSeconds": ...,
          "remSleepSeconds": ...,
          "awakeSleepSeconds": ...,
          "restingHeartRate": ...,
          "sleepScores": { "overall": {"value": ...} }
        }
      }

    Returns a dict with column names matching V1.0 master_sleep.csv.
    """
    dto = daily_sleep.get("dailySleepDTO", daily_sleep)
    scores = dto.get("sleepScores", {})
    overall_score = scores.get("overall", {}).get("value")

    return {
        "Date": dto.get("calendarDate"),
        "Sleep Score": overall_score,
        "Deep Sleep (hours)": _seconds_to_hours(dto.get("deepSleepSeconds")),
        "Light Sleep (hours)": _seconds_to_hours(dto.get("lightSleepSeconds")),
        "REM (hours)": _seconds_to_hours(dto.get("remSleepSeconds")),
        "Awake (hours)": _seconds_to_hours(dto.get("awakeSleepSeconds")),
        "Total Sleep (hours)": _seconds_to_hours(dto.get("sleepTimeSeconds")),
        "Resting Heart Rate": dto.get("restingHeartRate"),
    }


def translate_activity_json(activity: dict) -> dict:
    """Convert a single Garmin activity API record to a V1.0-compatible row.

    Handles the structure returned by api.get_activities_by_date():
      {
        "activityName": ...,
        "activityType": {"typeKey": "running"},
        "startTimeLocal": "YYYY-MM-DD HH:MM:SS",
        "distance": <metres>,
        "calories": ...,
        "duration": <seconds>,
        "averageHR": ...,
        "maxHR": ...
      }

    Returns a dict with column names matching V1.0 master_activities.csv.
    """
    start_local = activity.get("startTimeLocal", "")
    date_only = start_local.split(" ")[0] if start_local else None

    type_key = activity.get("activityType", {}).get("typeKey", "")
    type_display = type_key.replace("_", " ").title() if type_key else None

    distance_m = activity.get("distance") or 0
    distance_km = round(distance_m / 1000, 2) if distance_m else None

    duration_s = activity.get("duration") or 0
    duration_str = str(datetime.timedelta(seconds=int(duration_s))) if duration_s else None

    return {
        "Date": date_only,
        "Activity Type": type_display,
        "Title": activity.get("activityName"),
        "Distance": distance_km,
        "Calories": activity.get("calories"),
        "Time": duration_str,
        "Avg HR": activity.get("averageHR"),
        "Max HR": activity.get("maxHR"),
    }


# ---------------------------------------------------------------------------
# Phase 3: Fetch functions
# ---------------------------------------------------------------------------

def fetch_recent_sleep(client: Garmin, days: int = 14) -> pd.DataFrame:
    """Fetch and translate the last `days` days of sleep data.

    Calls api.get_sleep_data() for each date in the range, skips days with no
    data, and returns a DataFrame ready to pass into merge_sleep().

    Args:
        client: Authenticated Garmin client from get_garmin_client().
        days:   Number of days back from today to fetch.

    Returns:
        DataFrame with V1.0 sleep column names. Empty DataFrame if no data.
    """
    today = datetime.date.today()
    rows = []

    for i in range(days):
        date = today - datetime.timedelta(days=i)
        date_str = date.isoformat()
        try:
            raw = client.get_sleep_data(date_str)
            dto = raw.get("dailySleepDTO", {}) if raw else {}
            if not dto or not dto.get("calendarDate"):
                logger.debug("No sleep data for %s, skipping.", date_str)
                continue
            rows.append(translate_sleep_json(raw))
            logger.debug("Fetched sleep data for %s.", date_str)
        except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as exc:
            logger.error("API error fetching sleep for %s: %s", date_str, exc)

    if not rows:
        logger.info("No sleep data returned for the last %d days.", days)
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    logger.info("Fetched sleep data: %d rows over last %d days.", len(df), days)
    return df


def fetch_recent_activities(client: Garmin, days: int = 14) -> pd.DataFrame:
    """Fetch and translate the last `days` days of activity data.

    Uses api.get_activities_by_date() for the full date range in one call.

    Args:
        client: Authenticated Garmin client from get_garmin_client().
        days:   Number of days back from today to fetch.

    Returns:
        DataFrame with V1.0 activity column names. Empty DataFrame if no data.
    """
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=days - 1)).isoformat()
    end_date = today.isoformat()

    try:
        activities = client.get_activities_by_date(start_date, end_date)
    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as exc:
        logger.error("API error fetching activities (%s to %s): %s", start_date, end_date, exc)
        return pd.DataFrame()

    if not activities:
        logger.info("No activities returned for %s to %s.", start_date, end_date)
        return pd.DataFrame()

    rows = [translate_activity_json(a) for a in activities]
    df = pd.DataFrame(rows)
    logger.info("Fetched %d activities from %s to %s.", len(df), start_date, end_date)
    return df
