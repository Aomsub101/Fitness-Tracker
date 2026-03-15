"""
tests/test_data_pipeline.py

Unit tests for utils/data_pipeline.py.
All tests use temporary directories so no real data/ files are created or modified.
"""

import io
from pathlib import Path

import pandas as pd
import pytest

from utils.data_pipeline import load_csv, smart_merge, normalize_sleep_df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_df(dates, scores):
    """Build a minimal sleep-like DataFrame for test fixtures."""
    return pd.DataFrame({"Date": dates, "Score": scores})


# ---------------------------------------------------------------------------
# load_csv
# ---------------------------------------------------------------------------

class TestLoadCsv:
    def test_reads_valid_csv_from_file_like(self):
        csv_content = "Date,Score\n2024-01-01,75\n2024-01-02,80\n"
        df = load_csv(io.StringIO(csv_content))
        assert len(df) == 2
        assert list(df.columns) == ["Date", "Score"]

    def test_reads_multiple_columns(self):
        csv_content = "Date,Score,Deep Sleep\n2024-01-01,75,1.5\n"
        df = load_csv(io.StringIO(csv_content))
        assert "Deep Sleep" in df.columns

    def test_raises_for_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_csv("this_file_does_not_exist_xyz.csv")


# ---------------------------------------------------------------------------
# smart_merge
# ---------------------------------------------------------------------------

class TestSmartMerge:
    def test_creates_master_when_none_exists(self, tmp_path):
        master_path = tmp_path / "master.csv"
        new_df = make_df(["2024-01-01", "2024-01-02"], [75, 80])

        result = smart_merge(new_df, master_path, "Date")

        assert len(result) == 2
        assert master_path.exists()

    def test_appends_new_rows(self, tmp_path):
        master_path = tmp_path / "master.csv"
        smart_merge(make_df(["2024-01-01", "2024-01-02"], [75, 80]), master_path, "Date")

        result = smart_merge(make_df(["2024-01-03"], [85]), master_path, "Date")

        assert len(result) == 3

    def test_deduplication_new_upload_wins(self, tmp_path):
        """When the same date is uploaded twice, the newer upload's value wins."""
        master_path = tmp_path / "master.csv"
        smart_merge(make_df(["2024-01-01"], [75]), master_path, "Date")

        result = smart_merge(make_df(["2024-01-01"], [90]), master_path, "Date")

        assert len(result) == 1
        assert int(result.iloc[0]["Score"]) == 90

    def test_partial_overlap(self, tmp_path):
        """Upload with one existing date and one new date: overlap is deduplicated."""
        master_path = tmp_path / "master.csv"
        smart_merge(make_df(["2024-01-01", "2024-01-02"], [75, 80]), master_path, "Date")

        result = smart_merge(make_df(["2024-01-02", "2024-01-03"], [99, 85]), master_path, "Date")

        assert len(result) == 3
        # Overlapping date should use the new value
        row = result[pd.to_datetime(result["Date"]) == pd.Timestamp("2024-01-02")]
        assert int(row.iloc[0]["Score"]) == 99

    def test_result_sorted_ascending_by_date(self, tmp_path):
        master_path = tmp_path / "master.csv"
        df = make_df(["2024-01-03", "2024-01-01", "2024-01-02"], [3, 1, 2])

        result = smart_merge(df, master_path, "Date")

        dates = pd.to_datetime(result["Date"]).tolist()
        assert dates == sorted(dates)

    def test_raises_when_date_col_missing(self, tmp_path):
        master_path = tmp_path / "master.csv"
        df = pd.DataFrame({"WrongCol": ["2024-01-01"], "Score": [75]})

        with pytest.raises(ValueError, match="Date column"):
            smart_merge(df, master_path, "Date")

    def test_creates_parent_directory_if_missing(self, tmp_path):
        master_path = tmp_path / "subdir" / "master.csv"
        assert not master_path.parent.exists()

        smart_merge(make_df(["2024-01-01"], [75]), master_path, "Date")

        assert master_path.exists()

    def test_persists_data_to_csv(self, tmp_path):
        """Data written to master should be readable back as the same content."""
        master_path = tmp_path / "master.csv"
        smart_merge(make_df(["2024-01-01", "2024-01-02"], [75, 80]), master_path, "Date")

        reloaded = pd.read_csv(master_path, parse_dates=["Date"])
        assert len(reloaded) == 2


# ---------------------------------------------------------------------------
# normalize_sleep_df
# ---------------------------------------------------------------------------

class TestNormalizeSleepDf:
    def test_renames_date_column(self):
        df = pd.DataFrame({"Sleep Score 4 Weeks": ["2024-01-01"], "Score": [80]})
        result = normalize_sleep_df(df)
        assert "Date" in result.columns
        assert "Sleep Score 4 Weeks" not in result.columns

    def test_renames_score_column(self):
        df = pd.DataFrame({"Sleep Score 4 Weeks": ["2024-01-01"], "Score": [80]})
        result = normalize_sleep_df(df)
        assert "Sleep Score" in result.columns
        assert "Score" not in result.columns

    def test_preserves_other_columns(self):
        df = pd.DataFrame({
            "Sleep Score 4 Weeks": ["2024-01-01"],
            "Score": [80],
            "Resting Heart Rate": [55],
            "Duration": ["8:00"],
        })
        result = normalize_sleep_df(df)
        assert "Resting Heart Rate" in result.columns
        assert "Duration" in result.columns

    def test_noop_when_columns_already_standard(self):
        df = pd.DataFrame({"Date": ["2024-01-01"], "Sleep Score": [80]})
        result = normalize_sleep_df(df)
        assert list(result.columns) == ["Date", "Sleep Score"]

    def test_partial_rename_only_present_columns(self):
        """Only 'Sleep Score 4 Weeks' present — Score missing — should still rename date."""
        df = pd.DataFrame({"Sleep Score 4 Weeks": ["2024-01-01"], "Quality": ["Good"]})
        result = normalize_sleep_df(df)
        assert "Date" in result.columns
        assert "Sleep Score" not in result.columns  # was never there

    def test_merge_sleep_uses_normalised_columns(self, tmp_path, monkeypatch):
        """End-to-end: raw Garmin-format CSV merges without error."""
        import utils.data_pipeline as dp
        monkeypatch.setattr(dp, "MASTER_SLEEP_PATH", tmp_path / "master_sleep.csv")

        raw = pd.DataFrame({
            "Sleep Score 4 Weeks": ["2024-01-01", "2024-01-02"],
            "Score": [75, 80],
            "Resting Heart Rate": [58, 60],
        })
        result = dp.merge_sleep(raw)
        assert "Date" in result.columns
        assert "Sleep Score" in result.columns
        assert len(result) == 2
