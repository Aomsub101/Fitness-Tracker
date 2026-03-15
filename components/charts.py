"""
charts.py

Plotly chart builders for the Garmin health dashboard.
Each function returns a plotly.graph_objects.Figure ready to pass to
st.plotly_chart(). All functions are pure (no Streamlit calls inside).

Expected column names mirror those in insights_engine.py:
  Sleep:      Date, Sleep Score, Deep Sleep (hours), Light Sleep (hours),
              REM (hours), Total Sleep (hours)
  Activities: Date, Activity Type, Distance, Calories, Avg HR
"""

import logging
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COLOUR_SCORE = "#636EFA"
COLOUR_DEEP = "#00CC96"
COLOUR_LIGHT = "#FFA15A"
COLOUR_REM = "#AB63FA"
COLOUR_AWAKE = "#EF553B"
COLOUR_HR = "#FF6692"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_dates(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df.sort_values(date_col).reset_index(drop=True)


def _has_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and df[col].notna().any()


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="gray"),
    )
    fig.update_layout(xaxis_visible=False, yaxis_visible=False)
    return fig


# ---------------------------------------------------------------------------
# Sleep Score trend
# ---------------------------------------------------------------------------

def sleep_score_trend(sleep_df: Optional[pd.DataFrame], days: Optional[int] = None) -> go.Figure:
    """Line chart of Sleep Score over time.

    Args:
        sleep_df: Master sleep DataFrame.
        days:     If set, only the last `days` days are shown.
    """
    if sleep_df is None or sleep_df.empty or not _has_col(sleep_df, "Sleep Score"):
        return _empty_figure("No sleep score data available.")

    df = _parse_dates(sleep_df, "Date")
    df["Sleep Score"] = pd.to_numeric(df["Sleep Score"], errors="coerce")
    df = df.dropna(subset=["Date", "Sleep Score"])

    if days:
        cutoff = df["Date"].max() - pd.Timedelta(days=days - 1)
        df = df[df["Date"] >= cutoff]

    if df.empty:
        return _empty_figure("No sleep score data in the selected range.")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Sleep Score"],
        mode="lines+markers",
        name="Sleep Score",
        line=dict(color=COLOUR_SCORE, width=2),
        marker=dict(size=5),
    ))
    fig.update_layout(
        title="Sleep Score Over Time",
        xaxis_title="Date",
        yaxis_title="Sleep Score",
        yaxis=dict(range=[0, 100]),
        hovermode="x unified",
        template="plotly_white",
    )
    logger.info("Built sleep_score_trend chart (%d data points).", len(df))
    return fig


# ---------------------------------------------------------------------------
# Sleep stage breakdown (stacked bar)
# ---------------------------------------------------------------------------

def sleep_stages_bar(sleep_df: Optional[pd.DataFrame], days: Optional[int] = None) -> go.Figure:
    """Stacked bar chart of Deep / Light / REM / Awake hours per night."""
    stage_cols = {
        "Deep Sleep (hours)": COLOUR_DEEP,
        "Light Sleep (hours)": COLOUR_LIGHT,
        "REM (hours)": COLOUR_REM,
        "Awake (hours)": COLOUR_AWAKE,
    }

    if sleep_df is None or sleep_df.empty:
        return _empty_figure("No sleep stage data available.")

    available = [c for c in stage_cols if _has_col(sleep_df, c)]
    if not available:
        return _empty_figure("Sleep stage columns (Deep/Light/REM/Awake) not found in data.")

    df = _parse_dates(sleep_df, "Date")
    if days:
        cutoff = df["Date"].max() - pd.Timedelta(days=days - 1)
        df = df[df["Date"] >= cutoff]

    fig = go.Figure()
    for col in available:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        fig.add_trace(go.Bar(
            x=df["Date"], y=df[col],
            name=col.replace(" (hours)", ""),
            marker_color=stage_cols[col],
        ))

    fig.update_layout(
        title="Sleep Stages Per Night",
        xaxis_title="Date",
        yaxis_title="Hours",
        barmode="stack",
        hovermode="x unified",
        template="plotly_white",
    )
    logger.info("Built sleep_stages_bar chart (%d nights, %d stage cols).", len(df), len(available))
    return fig


# ---------------------------------------------------------------------------
# Activity log (scatter by type)
# ---------------------------------------------------------------------------

def activity_log_chart(activities_df: Optional[pd.DataFrame], days: Optional[int] = None) -> go.Figure:
    """Scatter plot of activities over time, coloured by Activity Type."""
    if activities_df is None or activities_df.empty:
        return _empty_figure("No activity data available.")

    df = _parse_dates(activities_df, "Date")
    if days:
        cutoff = df["Date"].max() - pd.Timedelta(days=days - 1)
        df = df[df["Date"] >= cutoff]

    if df.empty:
        return _empty_figure("No activities in the selected range.")

    y_col = "Calories" if _has_col(df, "Calories") else "Distance" if _has_col(df, "Distance") else None
    color_col = "Activity Type" if _has_col(df, "Activity Type") else None

    if y_col is None:
        return _empty_figure("No numeric activity metric (Calories/Distance) found.")

    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")

    fig = px.scatter(
        df, x="Date", y=y_col,
        color=color_col,
        title=f"Activities Over Time ({y_col})",
        labels={"Date": "Date", y_col: y_col},
        template="plotly_white",
    )
    fig.update_traces(marker=dict(size=8))
    fig.update_layout(hovermode="x unified")
    logger.info("Built activity_log_chart (%d activities).", len(df))
    return fig


# ---------------------------------------------------------------------------
# Activity type distribution (pie)
# ---------------------------------------------------------------------------

def activity_type_pie(activities_df: Optional[pd.DataFrame]) -> go.Figure:
    """Pie chart of activity type distribution across all recorded data."""
    if activities_df is None or activities_df.empty or not _has_col(activities_df, "Activity Type"):
        return _empty_figure("No activity type data available.")

    counts = activities_df["Activity Type"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.35,
    ))
    fig.update_layout(
        title="Activity Type Distribution",
        template="plotly_white",
    )
    logger.info("Built activity_type_pie (%d types).", len(counts))
    return fig


# ---------------------------------------------------------------------------
# Cross-metric: Resting HR vs activity days
# ---------------------------------------------------------------------------

def hr_vs_activity_days(
    sleep_df: Optional[pd.DataFrame],
    activities_df: Optional[pd.DataFrame],
) -> go.Figure:
    """Dual-axis chart: Sleep Score (line) with activity days highlighted (bar).

    Provides a visual correlation between workout days and sleep quality.
    """
    if sleep_df is None or sleep_df.empty or not _has_col(sleep_df, "Sleep Score"):
        return _empty_figure("No sleep score data for correlation chart.")

    sleep = _parse_dates(sleep_df, "Date").copy()
    sleep["Sleep Score"] = pd.to_numeric(sleep["Sleep Score"], errors="coerce")
    sleep = sleep.dropna(subset=["Sleep Score"])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Sleep Score line
    fig.add_trace(
        go.Scatter(
            x=sleep["Date"], y=sleep["Sleep Score"],
            name="Sleep Score", mode="lines+markers",
            line=dict(color=COLOUR_SCORE, width=2),
        ),
        secondary_y=False,
    )

    # Activity markers
    if activities_df is not None and not activities_df.empty:
        acts = _parse_dates(activities_df, "Date")
        act_dates = acts["Date"].dt.normalize().unique()

        activity_mask = sleep["Date"].dt.normalize().isin(act_dates)
        act_sleep = sleep[activity_mask]

        if not act_sleep.empty:
            fig.add_trace(
                go.Bar(
                    x=act_sleep["Date"], y=[1] * len(act_sleep),
                    name="Activity Day",
                    marker_color="rgba(255,161,90,0.4)",
                    showlegend=True,
                ),
                secondary_y=True,
            )

    fig.update_layout(
        title="Sleep Score vs Activity Days",
        hovermode="x unified",
        template="plotly_white",
    )
    fig.update_yaxes(title_text="Sleep Score", range=[0, 100], secondary_y=False)
    fig.update_yaxes(title_text="", showticklabels=False, secondary_y=True)
    logger.info("Built hr_vs_activity_days chart.")
    return fig
