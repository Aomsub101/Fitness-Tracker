"""
insights_engine.py

Hard-coded heuristic insights derived purely from Pandas logic.
All functions accept DataFrames (as returned by data_pipeline) and return
human-readable strings or dicts. No external APIs are used.

Expected column names (Garmin CSV defaults):
  Sleep:      Date, Sleep Score, Deep Sleep (hours), Light Sleep (hours),
              REM (hours), Awake (hours), Total Sleep (hours)
  Activities: Date, Activity Type, Distance, Calories, Avg HR
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name constants (Garmin CSV defaults)
# ---------------------------------------------------------------------------
SLEEP_DATE = "Date"
SLEEP_SCORE = "Sleep Score"
SLEEP_DEEP = "Deep Sleep (hours)"
SLEEP_LIGHT = "Light Sleep (hours)"
SLEEP_REM = "REM (hours)"
SLEEP_TOTAL = "Total Sleep (hours)"

ACT_DATE = "Date"
ACT_TYPE = "Activity Type"
ACT_CALORIES = "Calories"
ACT_DISTANCE = "Distance"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _recent(df: pd.DataFrame, date_col: str, days: int) -> pd.DataFrame:
    """Return rows from the last `days` calendar days."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    cutoff = df[date_col].max() - pd.Timedelta(days=days - 1)
    return df[df[date_col] >= cutoff]


def _col(df: pd.DataFrame, col: str) -> bool:
    """Return True if `col` exists and has at least one non-null value."""
    return col in df.columns and df[col].notna().any()


# ---------------------------------------------------------------------------
# Sleep insights
# ---------------------------------------------------------------------------

def avg_sleep_score(sleep_df: pd.DataFrame, days: int = 7) -> str:
    """Return a sentence with the average Sleep Score over the last `days` days.

    Example: "Your average Sleep Score over the last 7 days is 76."
    """
    if sleep_df is None or sleep_df.empty or not _col(sleep_df, SLEEP_SCORE):
        return "Not enough sleep data to calculate an average score."

    window = _recent(sleep_df, SLEEP_DATE, days)
    scores = pd.to_numeric(window[SLEEP_SCORE], errors="coerce").dropna()

    if scores.empty:
        return f"No sleep score data found in the last {days} days."

    avg = round(scores.mean(), 1)
    logger.info("avg_sleep_score (last %d days): %.1f", days, avg)
    return f"Your average Sleep Score over the last {days} days is {avg}."


def sleep_trend(sleep_df: pd.DataFrame, days: int = 14) -> str:
    """Describe whether sleep quality is improving, declining, or stable.

    Uses linear regression slope on Sleep Score over the last `days` days.
    """
    if sleep_df is None or sleep_df.empty or not _col(sleep_df, SLEEP_SCORE):
        return "Not enough sleep data to determine a trend."

    window = _recent(sleep_df, SLEEP_DATE, days).copy()
    window[SLEEP_SCORE] = pd.to_numeric(window[SLEEP_SCORE], errors="coerce")
    window = window.dropna(subset=[SLEEP_DATE, SLEEP_SCORE]).sort_values(SLEEP_DATE)

    if len(window) < 3:
        return "Not enough data points to determine a trend (need at least 3 days)."

    window["day_num"] = (window[SLEEP_DATE] - window[SLEEP_DATE].min()).dt.days
    slope = window["day_num"].cov(window[SLEEP_SCORE]) / window["day_num"].var()

    logger.info("sleep_trend slope (last %d days): %.3f", days, slope)

    if slope > 0.5:
        return f"Your Sleep Score is improving over the last {days} days. Keep it up!"
    elif slope < -0.5:
        return f"Your Sleep Score has been declining over the last {days} days. Consider reviewing your routine."
    else:
        return f"Your Sleep Score has been stable over the last {days} days."


def best_worst_sleep(sleep_df: pd.DataFrame) -> str:
    """Return the best and worst sleep score dates and values."""
    if sleep_df is None or sleep_df.empty or not _col(sleep_df, SLEEP_SCORE):
        return "Not enough sleep data to find best/worst nights."

    df = sleep_df.copy()
    df[SLEEP_SCORE] = pd.to_numeric(df[SLEEP_SCORE], errors="coerce")
    df[SLEEP_DATE] = pd.to_datetime(df[SLEEP_DATE], errors="coerce")
    df = df.dropna(subset=[SLEEP_SCORE, SLEEP_DATE])

    if df.empty:
        return "No valid sleep score data available."

    best = df.loc[df[SLEEP_SCORE].idxmax()]
    worst = df.loc[df[SLEEP_SCORE].idxmin()]

    best_date = best[SLEEP_DATE].strftime("%Y-%m-%d")
    worst_date = worst[SLEEP_DATE].strftime("%Y-%m-%d")

    return (
        f"Best night: {best_date} with a score of {int(best[SLEEP_SCORE])}. "
        f"Worst night: {worst_date} with a score of {int(worst[SLEEP_SCORE])}."
    )


def avg_deep_sleep(sleep_df: pd.DataFrame, days: int = 7) -> str:
    """Return the average deep sleep duration over the last `days` days."""
    if sleep_df is None or sleep_df.empty or not _col(sleep_df, SLEEP_DEEP):
        return "Deep sleep data is not available."

    window = _recent(sleep_df, SLEEP_DATE, days)
    values = pd.to_numeric(window[SLEEP_DEEP], errors="coerce").dropna()

    if values.empty:
        return f"No deep sleep data found in the last {days} days."

    avg = round(values.mean(), 2)
    return f"Your average Deep Sleep over the last {days} days is {avg} hours."


# ---------------------------------------------------------------------------
# Activity insights
# ---------------------------------------------------------------------------

def activity_summary(activities_df: pd.DataFrame, days: int = 7) -> str:
    """Summarise activity count and breakdown by type over the last `days` days."""
    if activities_df is None or activities_df.empty:
        return "No activity data available."

    window = _recent(activities_df, ACT_DATE, days)

    if window.empty:
        return f"No activities recorded in the last {days} days."

    total = len(window)
    summary = f"You logged {total} activit{'y' if total == 1 else 'ies'} in the last {days} days."

    if _col(window, ACT_TYPE):
        breakdown = window[ACT_TYPE].value_counts()
        parts = ", ".join(f"{count} {atype}" for atype, count in breakdown.items())
        summary += f" Breakdown: {parts}."

    return summary


def most_common_activity(activities_df: pd.DataFrame) -> str:
    """Return the activity type performed most often."""
    if activities_df is None or activities_df.empty or not _col(activities_df, ACT_TYPE):
        return "No activity type data available."

    top = activities_df[ACT_TYPE].value_counts().idxmax()
    count = activities_df[ACT_TYPE].value_counts().max()
    return f"Your most frequent activity is '{top}' ({count} sessions total)."


# ---------------------------------------------------------------------------
# Cross-metric correlation
# ---------------------------------------------------------------------------

def sleep_on_activity_days(
    sleep_df: pd.DataFrame,
    activities_df: pd.DataFrame,
    activity_type: Optional[str] = None,
) -> str:
    """Compare average Deep Sleep on activity days vs rest days.

    Args:
        sleep_df:      Master sleep DataFrame.
        activities_df: Master activities DataFrame.
        activity_type: Filter to a specific activity type (e.g. 'Running').
                       If None, all activity types are used.

    Returns:
        A human-readable insight string.
    """
    if sleep_df is None or sleep_df.empty:
        return "Not enough sleep data for correlation analysis."
    if activities_df is None or activities_df.empty:
        return "Not enough activity data for correlation analysis."
    if not _col(sleep_df, SLEEP_DEEP):
        return "Deep sleep column is missing — cannot compute correlation."

    sleep = sleep_df.copy()
    acts = activities_df.copy()

    sleep[SLEEP_DATE] = pd.to_datetime(sleep[SLEEP_DATE], errors="coerce")
    acts[ACT_DATE] = pd.to_datetime(acts[ACT_DATE], errors="coerce")
    sleep[SLEEP_DEEP] = pd.to_numeric(sleep[SLEEP_DEEP], errors="coerce")

    if activity_type and _col(acts, ACT_TYPE):
        acts = acts[acts[ACT_TYPE].str.lower() == activity_type.lower()]

    activity_dates = set(acts[ACT_DATE].dropna().dt.normalize())

    sleep["is_activity_day"] = sleep[SLEEP_DATE].dt.normalize().isin(activity_dates)

    on_days = sleep.loc[sleep["is_activity_day"], SLEEP_DEEP].dropna()
    off_days = sleep.loc[~sleep["is_activity_day"], SLEEP_DEEP].dropna()

    if on_days.empty or off_days.empty:
        label = f"'{activity_type}'" if activity_type else "activity"
        return f"Not enough data to compare sleep on {label} days vs rest days."

    avg_on = round(on_days.mean(), 2)
    avg_off = round(off_days.mean(), 2)
    diff = round(avg_on - avg_off, 2)
    label = f"'{activity_type}'" if activity_type else "activity"

    logger.info(
        "sleep_on_activity_days (%s): on=%.2f, off=%.2f", label, avg_on, avg_off
    )

    if diff < -0.1:
        return (
            f"Your Deep Sleep averages {avg_on}h on {label} days vs {avg_off}h on rest days "
            f"({abs(diff)}h less). {label.capitalize()} may be affecting your deep sleep."
        )
    elif diff > 0.1:
        return (
            f"Your Deep Sleep averages {avg_on}h on {label} days vs {avg_off}h on rest days "
            f"({diff}h more). {label.capitalize()} seems to benefit your deep sleep!"
        )
    else:
        return (
            f"Your Deep Sleep is similar on {label} days ({avg_on}h) vs rest days ({avg_off}h). "
            "No strong correlation detected."
        )


# ---------------------------------------------------------------------------
# Convenience: generate all insights at once
# ---------------------------------------------------------------------------

def generate_all_insights(
    sleep_df: Optional[pd.DataFrame],
    activities_df: Optional[pd.DataFrame],
) -> dict:
    """Return a dict of all available insight strings.

    Keys: 'avg_sleep_score', 'sleep_trend', 'best_worst_sleep',
          'avg_deep_sleep', 'activity_summary', 'most_common_activity',
          'sleep_activity_correlation'
    """
    top_activity = None
    if activities_df is not None and not activities_df.empty and _col(activities_df, ACT_TYPE):
        top_activity = activities_df[ACT_TYPE].value_counts().idxmax()

    return {
        "avg_sleep_score": avg_sleep_score(sleep_df),
        "sleep_trend": sleep_trend(sleep_df),
        "best_worst_sleep": best_worst_sleep(sleep_df),
        "avg_deep_sleep": avg_deep_sleep(sleep_df),
        "activity_summary": activity_summary(activities_df),
        "most_common_activity": most_common_activity(activities_df),
        "sleep_activity_correlation": sleep_on_activity_days(
            sleep_df, activities_df, activity_type=top_activity
        ),
    }
