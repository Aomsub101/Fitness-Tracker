"""
tests/test_garmin_api.py

Unit tests for utils/garmin_api.py.
All Garmin API calls and file I/O are mocked — no real credentials or network
access are required.
"""

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from utils.garmin_api import (
    fetch_recent_activities,
    fetch_recent_sleep,
    get_garmin_client,
    translate_activity_json,
    translate_sleep_json,
)


# ---------------------------------------------------------------------------
# Fixtures / sample data
# ---------------------------------------------------------------------------

SAMPLE_SLEEP_RESPONSE = {
    "dailySleepDTO": {
        "calendarDate": "2024-01-01",
        "sleepTimeSeconds": 28800,   # 8h
        "deepSleepSeconds": 5400,    # 1.5h
        "lightSleepSeconds": 14400,  # 4h
        "remSleepSeconds": 7200,     # 2h
        "awakeSleepSeconds": 1800,   # 0.5h
        "restingHeartRate": 55,
        "sleepScores": {
            "overall": {"value": 78}
        },
    }
}

SAMPLE_ACTIVITY = {
    "activityName": "Morning Run",
    "activityType": {"typeKey": "running"},
    "startTimeLocal": "2024-01-01 06:30:00",
    "distance": 5000.0,
    "calories": 400,
    "duration": 1800.0,
    "averageHR": 145,
    "maxHR": 170,
}


# ---------------------------------------------------------------------------
# translate_sleep_json
# ---------------------------------------------------------------------------

class TestTranslateSleepJson:
    def test_extracts_date(self):
        row = translate_sleep_json(SAMPLE_SLEEP_RESPONSE)
        assert row["Date"] == "2024-01-01"

    def test_extracts_sleep_score(self):
        row = translate_sleep_json(SAMPLE_SLEEP_RESPONSE)
        assert row["Sleep Score"] == 78

    def test_converts_seconds_to_hours(self):
        row = translate_sleep_json(SAMPLE_SLEEP_RESPONSE)
        assert row["Total Sleep (hours)"] == 8.0
        assert row["Deep Sleep (hours)"] == 1.5
        assert row["Light Sleep (hours)"] == 4.0
        assert row["REM (hours)"] == 2.0
        assert row["Awake (hours)"] == 0.5

    def test_extracts_resting_hr(self):
        row = translate_sleep_json(SAMPLE_SLEEP_RESPONSE)
        assert row["Resting Heart Rate"] == 55

    def test_handles_missing_score(self):
        data = {"dailySleepDTO": {"calendarDate": "2024-01-01"}}
        row = translate_sleep_json(data)
        assert row["Sleep Score"] is None

    def test_handles_missing_sleep_seconds(self):
        data = {"dailySleepDTO": {"calendarDate": "2024-01-01", "deepSleepSeconds": 0}}
        row = translate_sleep_json(data)
        assert row["Deep Sleep (hours)"] is None

    def test_handles_flat_dto_without_wrapper(self):
        """Should work when the dict is passed without the dailySleepDTO wrapper."""
        flat = {
            "calendarDate": "2024-01-02",
            "sleepTimeSeconds": 25200,
            "sleepScores": {"overall": {"value": 70}},
        }
        row = translate_sleep_json(flat)
        assert row["Date"] == "2024-01-02"
        assert row["Sleep Score"] == 70

    def test_output_has_all_v1_columns(self):
        row = translate_sleep_json(SAMPLE_SLEEP_RESPONSE)
        expected_cols = {
            "Date", "Sleep Score", "Deep Sleep (hours)", "Light Sleep (hours)",
            "REM (hours)", "Awake (hours)", "Total Sleep (hours)", "Resting Heart Rate",
        }
        assert expected_cols == set(row.keys())


# ---------------------------------------------------------------------------
# translate_activity_json
# ---------------------------------------------------------------------------

class TestTranslateActivityJson:
    def test_extracts_date_from_start_time(self):
        row = translate_activity_json(SAMPLE_ACTIVITY)
        assert row["Date"] == "2024-01-01"

    def test_activity_type_title_case(self):
        row = translate_activity_json(SAMPLE_ACTIVITY)
        assert row["Activity Type"] == "Running"

    def test_converts_distance_m_to_km(self):
        row = translate_activity_json(SAMPLE_ACTIVITY)
        assert row["Distance"] == 5.0

    def test_converts_duration_to_time_string(self):
        row = translate_activity_json(SAMPLE_ACTIVITY)
        assert row["Time"] == "0:30:00"

    def test_extracts_calories_and_hr(self):
        row = translate_activity_json(SAMPLE_ACTIVITY)
        assert row["Calories"] == 400
        assert row["Avg HR"] == 145
        assert row["Max HR"] == 170

    def test_handles_underscore_activity_type(self):
        act = {**SAMPLE_ACTIVITY, "activityType": {"typeKey": "fitness_equipment"}}
        row = translate_activity_json(act)
        assert row["Activity Type"] == "Fitness Equipment"

    def test_handles_missing_distance(self):
        act = {**SAMPLE_ACTIVITY, "distance": None}
        row = translate_activity_json(act)
        assert row["Distance"] is None

    def test_handles_missing_start_time(self):
        act = {**SAMPLE_ACTIVITY, "startTimeLocal": ""}
        row = translate_activity_json(act)
        assert row["Date"] is None

    def test_output_has_all_v1_columns(self):
        row = translate_activity_json(SAMPLE_ACTIVITY)
        expected_cols = {"Date", "Activity Type", "Title", "Distance", "Calories", "Time", "Avg HR", "Max HR"}
        assert expected_cols == set(row.keys())


# ---------------------------------------------------------------------------
# get_garmin_client — auth logic
# ---------------------------------------------------------------------------

class TestGetGarminClient:
    def test_uses_saved_session_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.garmin_api.SESSION_DIR", tmp_path)
        (tmp_path / "oauth1_token.json").write_text("{}")

        mock_client = MagicMock()
        with patch("utils.garmin_api.Garmin", return_value=mock_client) as MockGarmin:
            client = get_garmin_client()

        MockGarmin.assert_called_once_with()
        mock_client.login.assert_called_once_with(tokenstore=str(tmp_path))
        assert client is mock_client

    def test_falls_back_to_credentials_when_no_session(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.garmin_api.SESSION_DIR", tmp_path)
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "secret")

        mock_client = MagicMock()
        with patch("utils.garmin_api.Garmin", return_value=mock_client) as MockGarmin:
            client = get_garmin_client()

        MockGarmin.assert_called_once_with("test@example.com", "secret")
        mock_client.login.assert_called_once_with()
        mock_client.garth.dump.assert_called_once_with(str(tmp_path))

    def test_falls_back_to_credentials_when_session_invalid(self, tmp_path, monkeypatch):
        from garminconnect import GarminConnectAuthenticationError
        monkeypatch.setattr("utils.garmin_api.SESSION_DIR", tmp_path)
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "secret")

        (tmp_path / "oauth1_token.json").write_text("{}")

        fresh_client = MagicMock()

        def garmin_factory(*args, **kwargs):
            c = MagicMock()
            if not args and not kwargs:
                # session restore attempt — make login raise
                c.login.side_effect = GarminConnectAuthenticationError("expired")
            return c

        with patch("utils.garmin_api.Garmin", side_effect=garmin_factory):
            client = get_garmin_client()

        # Second Garmin() call (credential login) should have succeeded
        client.garth.dump.assert_called_once_with(str(tmp_path))

    def test_raises_value_error_when_no_credentials(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.garmin_api.SESSION_DIR", tmp_path)
        monkeypatch.delenv("GARMIN_EMAIL", raising=False)
        monkeypatch.delenv("GARMIN_PASSWORD", raising=False)

        # Prevent load_dotenv() from re-loading the real .env file
        with patch("utils.garmin_api.load_dotenv"):
            with pytest.raises(ValueError, match="GARMIN_EMAIL"):
                get_garmin_client()

    def test_saves_session_after_credential_login(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.garmin_api.SESSION_DIR", tmp_path)
        monkeypatch.setenv("GARMIN_EMAIL", "test@example.com")
        monkeypatch.setenv("GARMIN_PASSWORD", "secret")

        mock_client = MagicMock()
        with patch("utils.garmin_api.Garmin", return_value=mock_client):
            get_garmin_client()

        mock_client.garth.dump.assert_called_once_with(str(tmp_path))


# ---------------------------------------------------------------------------
# fetch_recent_sleep
# ---------------------------------------------------------------------------

class TestFetchRecentSleep:
    def test_returns_dataframe_with_correct_columns(self):
        mock_client = MagicMock()
        mock_client.get_sleep_data.return_value = SAMPLE_SLEEP_RESPONSE

        df = fetch_recent_sleep(mock_client, days=3)

        assert isinstance(df, pd.DataFrame)
        assert "Date" in df.columns
        assert "Sleep Score" in df.columns
        assert len(df) == 3

    def test_skips_days_with_no_data(self):
        mock_client = MagicMock()
        mock_client.get_sleep_data.side_effect = [
            SAMPLE_SLEEP_RESPONSE,
            {"dailySleepDTO": {}},   # no calendarDate → skipped
            SAMPLE_SLEEP_RESPONSE,
        ]

        df = fetch_recent_sleep(mock_client, days=3)
        assert len(df) == 2

    def test_returns_empty_df_when_all_skipped(self):
        mock_client = MagicMock()
        mock_client.get_sleep_data.return_value = {"dailySleepDTO": {}}

        df = fetch_recent_sleep(mock_client, days=3)
        assert df.empty

    def test_handles_api_error_gracefully(self):
        from garminconnect import GarminConnectConnectionError
        mock_client = MagicMock()
        mock_client.get_sleep_data.side_effect = GarminConnectConnectionError("timeout")

        df = fetch_recent_sleep(mock_client, days=2)
        assert df.empty

    def test_calls_api_correct_number_of_times(self):
        mock_client = MagicMock()
        mock_client.get_sleep_data.return_value = SAMPLE_SLEEP_RESPONSE

        fetch_recent_sleep(mock_client, days=5)
        assert mock_client.get_sleep_data.call_count == 5


# ---------------------------------------------------------------------------
# fetch_recent_activities
# ---------------------------------------------------------------------------

class TestFetchRecentActivities:
    def test_returns_dataframe_with_correct_columns(self):
        mock_client = MagicMock()
        mock_client.get_activities_by_date.return_value = [SAMPLE_ACTIVITY, SAMPLE_ACTIVITY]

        df = fetch_recent_activities(mock_client, days=7)

        assert isinstance(df, pd.DataFrame)
        assert "Date" in df.columns
        assert "Activity Type" in df.columns
        assert len(df) == 2

    def test_returns_empty_df_when_no_activities(self):
        mock_client = MagicMock()
        mock_client.get_activities_by_date.return_value = []

        df = fetch_recent_activities(mock_client, days=7)
        assert df.empty

    def test_handles_api_error_gracefully(self):
        from garminconnect import GarminConnectTooManyRequestsError
        mock_client = MagicMock()
        mock_client.get_activities_by_date.side_effect = GarminConnectTooManyRequestsError("rate limit")

        df = fetch_recent_activities(mock_client, days=7)
        assert df.empty

    def test_uses_correct_date_range(self):
        mock_client = MagicMock()
        mock_client.get_activities_by_date.return_value = []

        today = datetime.date.today()
        expected_start = (today - datetime.timedelta(days=13)).isoformat()
        expected_end = today.isoformat()

        fetch_recent_activities(mock_client, days=14)
        mock_client.get_activities_by_date.assert_called_once_with(expected_start, expected_end)

    def test_translated_df_compatible_with_merge_activities(self, tmp_path, monkeypatch):
        """End-to-end: translated activities DataFrame passes into merge_activities."""
        import utils.data_pipeline as dp
        monkeypatch.setattr(dp, "MASTER_ACTIVITIES_PATH", tmp_path / "master_activities.csv")

        mock_client = MagicMock()
        mock_client.get_activities_by_date.return_value = [SAMPLE_ACTIVITY]

        df = fetch_recent_activities(mock_client, days=7)
        result = dp.merge_activities(df)

        assert len(result) == 1
        assert "Date" in result.columns
