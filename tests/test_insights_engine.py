"""
tests/test_insights_engine.py

Unit tests for utils/insights_engine.py.
All tests use in-memory DataFrames — no file I/O.
"""

import pandas as pd
import pytest

from utils.insights_engine import (
    avg_deep_sleep,
    avg_sleep_score,
    best_worst_sleep,
    activity_summary,
    generate_all_insights,
    most_common_activity,
    sleep_on_activity_days,
    sleep_trend,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_sleep(dates, scores, deep=None):
    data = {"Date": pd.to_datetime(dates), "Sleep Score": scores}
    if deep is not None:
        data["Deep Sleep (hours)"] = deep
    return pd.DataFrame(data)


def make_activities(dates, types):
    return pd.DataFrame({"Date": pd.to_datetime(dates), "Activity Type": types})


# ---------------------------------------------------------------------------
# avg_sleep_score
# ---------------------------------------------------------------------------

class TestAvgSleepScore:
    def test_returns_correct_average(self):
        df = make_sleep(["2024-01-01", "2024-01-02", "2024-01-03"], [70, 80, 90])
        result = avg_sleep_score(df, days=7)
        assert "80.0" in result

    def test_handles_none(self):
        result = avg_sleep_score(None)
        assert "Not enough" in result

    def test_handles_empty_df(self):
        result = avg_sleep_score(pd.DataFrame())
        assert "Not enough" in result

    def test_only_considers_last_n_days(self):
        # Old score (100) is outside the 3-day window; only recent scores count
        df = make_sleep(
            ["2024-01-01", "2024-01-08", "2024-01-09", "2024-01-10"],
            [100, 60, 60, 60],
        )
        result = avg_sleep_score(df, days=3)
        assert "60.0" in result


# ---------------------------------------------------------------------------
# sleep_trend
# ---------------------------------------------------------------------------

class TestSleepTrend:
    def test_improving_trend(self):
        df = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            [60, 65, 70, 80],
        )
        result = sleep_trend(df, days=14)
        assert "improving" in result.lower()

    def test_declining_trend(self):
        df = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            [80, 70, 65, 60],
        )
        result = sleep_trend(df, days=14)
        assert "declining" in result.lower()

    def test_stable_trend(self):
        df = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            [75, 75, 75, 75],
        )
        result = sleep_trend(df, days=14)
        assert "stable" in result.lower()

    def test_insufficient_data(self):
        df = make_sleep(["2024-01-01", "2024-01-02"], [75, 80])
        result = sleep_trend(df, days=14)
        assert "not enough" in result.lower()

    def test_handles_none(self):
        assert "Not enough" in sleep_trend(None)


# ---------------------------------------------------------------------------
# best_worst_sleep
# ---------------------------------------------------------------------------

class TestBestWorstSleep:
    def test_returns_correct_best_and_worst(self):
        df = make_sleep(["2024-01-01", "2024-01-02", "2024-01-03"], [50, 90, 70])
        result = best_worst_sleep(df)
        assert "2024-01-02" in result  # best
        assert "90" in result
        assert "2024-01-01" in result  # worst
        assert "50" in result

    def test_handles_none(self):
        assert "Not enough" in best_worst_sleep(None)


# ---------------------------------------------------------------------------
# avg_deep_sleep
# ---------------------------------------------------------------------------

class TestAvgDeepSleep:
    def test_correct_average(self):
        df = make_sleep(["2024-01-01", "2024-01-02"], [75, 80], deep=[1.5, 2.5])
        result = avg_deep_sleep(df, days=7)
        assert "2.0" in result

    def test_missing_column(self):
        df = make_sleep(["2024-01-01"], [75])  # no deep sleep column
        result = avg_deep_sleep(df)
        assert "not available" in result.lower()


# ---------------------------------------------------------------------------
# activity_summary
# ---------------------------------------------------------------------------

class TestActivitySummary:
    def test_counts_activities(self):
        df = make_activities(["2024-01-01", "2024-01-02"], ["Running", "Cycling"])
        result = activity_summary(df, days=7)
        assert "2" in result

    def test_breakdown_included(self):
        df = make_activities(
            ["2024-01-01", "2024-01-02", "2024-01-03"],
            ["Running", "Running", "Cycling"],
        )
        result = activity_summary(df, days=7)
        assert "Running" in result
        assert "Cycling" in result

    def test_handles_none(self):
        assert "No activity" in activity_summary(None)

    def test_handles_empty(self):
        assert "No activity" in activity_summary(pd.DataFrame())


# ---------------------------------------------------------------------------
# most_common_activity
# ---------------------------------------------------------------------------

class TestMostCommonActivity:
    def test_returns_correct_top_activity(self):
        df = make_activities(
            ["2024-01-01", "2024-01-02", "2024-01-03"],
            ["Running", "Running", "Cycling"],
        )
        result = most_common_activity(df)
        assert "Running" in result
        assert "2" in result

    def test_handles_none(self):
        assert "No activity" in most_common_activity(None)


# ---------------------------------------------------------------------------
# sleep_on_activity_days
# ---------------------------------------------------------------------------

class TestSleepOnActivityDays:
    def test_detects_lower_deep_sleep_on_activity_days(self):
        sleep = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            [75, 70, 75, 70],
            deep=[2.0, 1.0, 2.0, 1.0],  # activity days have 1.0h deep sleep
        )
        acts = make_activities(["2024-01-02", "2024-01-04"], ["Running", "Running"])
        result = sleep_on_activity_days(sleep, acts, activity_type="Running")
        assert "less" in result.lower() or "affecting" in result.lower()

    def test_detects_higher_deep_sleep_on_activity_days(self):
        sleep = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            [75, 70, 75, 70],
            deep=[1.0, 3.0, 1.0, 3.0],  # activity days have 3.0h
        )
        acts = make_activities(["2024-01-02", "2024-01-04"], ["Running", "Running"])
        result = sleep_on_activity_days(sleep, acts, activity_type="Running")
        assert "more" in result.lower() or "benefit" in result.lower()

    def test_no_correlation(self):
        sleep = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            [75, 75, 75, 75],
            deep=[2.0, 2.0, 2.0, 2.0],
        )
        acts = make_activities(["2024-01-02", "2024-01-04"], ["Running", "Running"])
        result = sleep_on_activity_days(sleep, acts, activity_type="Running")
        assert "similar" in result.lower() or "no strong" in result.lower()

    def test_handles_none_sleep(self):
        acts = make_activities(["2024-01-01"], ["Running"])
        assert "Not enough" in sleep_on_activity_days(None, acts)

    def test_handles_none_activities(self):
        sleep = make_sleep(["2024-01-01"], [75], deep=[2.0])
        assert "Not enough" in sleep_on_activity_days(sleep, None)


# ---------------------------------------------------------------------------
# generate_all_insights
# ---------------------------------------------------------------------------

class TestGenerateAllInsights:
    def test_returns_all_keys(self):
        sleep = make_sleep(
            ["2024-01-01", "2024-01-02", "2024-01-03"],
            [70, 75, 80],
            deep=[1.5, 1.8, 2.0],
        )
        acts = make_activities(["2024-01-02"], ["Running"])
        result = generate_all_insights(sleep, acts)

        expected_keys = {
            "avg_sleep_score",
            "sleep_trend",
            "best_worst_sleep",
            "avg_deep_sleep",
            "activity_summary",
            "most_common_activity",
            "sleep_activity_correlation",
        }
        assert expected_keys == set(result.keys())

    def test_all_values_are_strings(self):
        sleep = make_sleep(["2024-01-01"], [75], deep=[2.0])
        acts = make_activities(["2024-01-01"], ["Running"])
        result = generate_all_insights(sleep, acts)
        for key, value in result.items():
            assert isinstance(value, str), f"Key '{key}' returned non-string: {value!r}"

    def test_handles_both_none(self):
        result = generate_all_insights(None, None)
        assert all(isinstance(v, str) for v in result.values())
