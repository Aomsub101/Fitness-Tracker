"""
tests/test_charts.py

Unit tests for components/charts.py.
Tests verify that each chart builder returns a valid Plotly Figure and
handles None / empty / missing-column inputs gracefully.
"""

import pandas as pd
import pytest
import plotly.graph_objects as go

from components.charts import (
    sleep_score_trend,
    sleep_stages_bar,
    activity_log_chart,
    activity_type_pie,
    hr_vs_activity_days,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_sleep(dates, scores, deep=None, light=None, rem=None, awake=None):
    data = {"Date": pd.to_datetime(dates), "Sleep Score": scores}
    if deep is not None:
        data["Deep Sleep (hours)"] = deep
    if light is not None:
        data["Light Sleep (hours)"] = light
    if rem is not None:
        data["REM (hours)"] = rem
    if awake is not None:
        data["Awake (hours)"] = awake
    return pd.DataFrame(data)


def make_activities(dates, types, calories=None):
    data = {"Date": pd.to_datetime(dates), "Activity Type": types}
    if calories is not None:
        data["Calories"] = calories
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_empty_figure(fig: go.Figure) -> bool:
    """Return True if figure has no data traces (only an annotation)."""
    return len(fig.data) == 0


# ---------------------------------------------------------------------------
# sleep_score_trend
# ---------------------------------------------------------------------------

class TestSleepScoreTrend:
    def test_returns_figure(self):
        df = make_sleep(["2024-01-01", "2024-01-02", "2024-01-03"], [70, 75, 80])
        fig = sleep_score_trend(df)
        assert isinstance(fig, go.Figure)

    def test_has_one_trace(self):
        df = make_sleep(["2024-01-01", "2024-01-02"], [70, 80])
        fig = sleep_score_trend(df)
        assert len(fig.data) == 1

    def test_correct_y_values(self):
        df = make_sleep(["2024-01-01", "2024-01-02", "2024-01-03"], [70, 75, 80])
        fig = sleep_score_trend(df)
        assert list(fig.data[0].y) == [70, 75, 80]

    def test_days_filter(self):
        df = make_sleep(
            ["2024-01-01", "2024-01-08", "2024-01-09", "2024-01-10"],
            [50, 70, 75, 80],
        )
        fig = sleep_score_trend(df, days=3)
        assert len(fig.data[0].y) == 3

    def test_handles_none(self):
        fig = sleep_score_trend(None)
        assert isinstance(fig, go.Figure)
        assert is_empty_figure(fig)

    def test_handles_empty_df(self):
        fig = sleep_score_trend(pd.DataFrame())
        assert is_empty_figure(fig)

    def test_handles_missing_score_column(self):
        df = pd.DataFrame({"Date": ["2024-01-01"], "Other": [1]})
        fig = sleep_score_trend(df)
        assert is_empty_figure(fig)


# ---------------------------------------------------------------------------
# sleep_stages_bar
# ---------------------------------------------------------------------------

class TestSleepStagesBar:
    def test_returns_figure_with_stages(self):
        df = make_sleep(
            ["2024-01-01", "2024-01-02"],
            [75, 80],
            deep=[1.5, 2.0],
            light=[3.0, 3.5],
            rem=[1.0, 1.2],
            awake=[0.5, 0.3],
        )
        fig = sleep_stages_bar(df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 4  # 4 stage traces

    def test_handles_partial_stage_columns(self):
        df = make_sleep(["2024-01-01"], [75], deep=[1.5])
        fig = sleep_stages_bar(df)
        assert len(fig.data) == 1

    def test_handles_none(self):
        fig = sleep_stages_bar(None)
        assert is_empty_figure(fig)

    def test_handles_no_stage_columns(self):
        df = make_sleep(["2024-01-01"], [75])  # no stage cols
        fig = sleep_stages_bar(df)
        assert is_empty_figure(fig)


# ---------------------------------------------------------------------------
# activity_log_chart
# ---------------------------------------------------------------------------

class TestActivityLogChart:
    def test_returns_figure(self):
        df = make_activities(
            ["2024-01-01", "2024-01-03"],
            ["Running", "Cycling"],
            calories=[400, 300],
        )
        fig = activity_log_chart(df)
        assert isinstance(fig, go.Figure)
        assert not is_empty_figure(fig)

    def test_days_filter(self):
        df = make_activities(
            ["2024-01-01", "2024-01-08", "2024-01-09"],
            ["Running", "Cycling", "Running"],
            calories=[400, 300, 350],
        )
        fig = activity_log_chart(df, days=2)
        assert not is_empty_figure(fig)

    def test_handles_none(self):
        fig = activity_log_chart(None)
        assert is_empty_figure(fig)

    def test_handles_empty(self):
        fig = activity_log_chart(pd.DataFrame())
        assert is_empty_figure(fig)

    def test_handles_no_numeric_column(self):
        df = pd.DataFrame({"Date": ["2024-01-01"], "Activity Type": ["Running"]})
        fig = activity_log_chart(df)
        assert is_empty_figure(fig)


# ---------------------------------------------------------------------------
# activity_type_pie
# ---------------------------------------------------------------------------

class TestActivityTypePie:
    def test_returns_figure(self):
        df = make_activities(["2024-01-01", "2024-01-02", "2024-01-03"], ["Running", "Running", "Cycling"])
        fig = activity_type_pie(df)
        assert isinstance(fig, go.Figure)
        assert not is_empty_figure(fig)

    def test_correct_labels(self):
        df = make_activities(["2024-01-01", "2024-01-02"], ["Running", "Cycling"])
        fig = activity_type_pie(df)
        labels = list(fig.data[0].labels)
        assert set(labels) == {"Running", "Cycling"}

    def test_handles_none(self):
        fig = activity_type_pie(None)
        assert is_empty_figure(fig)

    def test_handles_empty(self):
        fig = activity_type_pie(pd.DataFrame())
        assert is_empty_figure(fig)


# ---------------------------------------------------------------------------
# hr_vs_activity_days
# ---------------------------------------------------------------------------

class TestHrVsActivityDays:
    def test_returns_figure_with_sleep_only(self):
        sleep = make_sleep(["2024-01-01", "2024-01-02", "2024-01-03"], [70, 75, 80])
        fig = hr_vs_activity_days(sleep, None)
        assert isinstance(fig, go.Figure)
        assert not is_empty_figure(fig)

    def test_returns_figure_with_both(self):
        sleep = make_sleep(["2024-01-01", "2024-01-02", "2024-01-03"], [70, 75, 80])
        acts = make_activities(["2024-01-02"], ["Running"])
        fig = hr_vs_activity_days(sleep, acts)
        assert isinstance(fig, go.Figure)
        # Should have sleep trace + activity bar trace
        assert len(fig.data) == 2

    def test_handles_none_sleep(self):
        acts = make_activities(["2024-01-01"], ["Running"])
        fig = hr_vs_activity_days(None, acts)
        assert is_empty_figure(fig)

    def test_handles_both_none(self):
        fig = hr_vs_activity_days(None, None)
        assert is_empty_figure(fig)
