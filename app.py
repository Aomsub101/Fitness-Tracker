"""
app.py

Main Streamlit entry point for the Garmin Personal Health Dashboard.

Run with:
    streamlit run app.py
"""

import logging

import streamlit as st

from utils.data_pipeline import (
    load_csv,
    merge_sleep,
    merge_activities,
    load_master_sleep,
    load_master_activities,
)
from utils.insights_engine import generate_all_insights
from components.charts import (
    sleep_score_trend,
    sleep_stages_bar,
    activity_log_chart,
    activity_type_pie,
    hr_vs_activity_days,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Garmin Health Dashboard",
    page_icon="🏃",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — CSV upload
# ---------------------------------------------------------------------------
st.sidebar.title("Upload Garmin Data")
st.sidebar.markdown(
    "Export CSVs from [Garmin Connect](https://connect.garmin.com) and upload below. "
    "Duplicate dates are automatically resolved (newest upload wins)."
)

sleep_files = st.sidebar.file_uploader("Sleep CSV", type="csv", key="sleep_upload", accept_multiple_files=True)
activity_files = st.sidebar.file_uploader("Activities CSV", type="csv", key="activity_upload", accept_multiple_files=True)

for sleep_file in sleep_files:
    try:
        new_sleep = load_csv(sleep_file)
        merge_sleep(new_sleep)
        st.sidebar.success(f"{sleep_file.name}: merged {len(new_sleep)} rows.")
        logger.info("Sleep CSV '%s' uploaded and merged.", sleep_file.name)
    except Exception as exc:
        st.sidebar.error(f"{sleep_file.name}: {exc}")
        logger.error("Sleep upload error (%s): %s", sleep_file.name, exc)

for activity_file in activity_files:
    try:
        new_acts = load_csv(activity_file)
        merge_activities(new_acts)
        st.sidebar.success(f"{activity_file.name}: merged {len(new_acts)} rows.")
        logger.info("Activities CSV '%s' uploaded and merged.", activity_file.name)
    except Exception as exc:
        st.sidebar.error(f"{activity_file.name}: {exc}")
        logger.error("Activity upload error (%s): %s", activity_file.name, exc)

# ---------------------------------------------------------------------------
# Load master data
# ---------------------------------------------------------------------------
sleep_df = load_master_sleep()
activities_df = load_master_activities()

# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------
st.title("🏃 Garmin Personal Health Dashboard")

if sleep_df is None and activities_df is None:
    st.info(
        "No data yet. Upload your Garmin Sleep and/or Activities CSVs using the sidebar to get started."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Date range filter
# ---------------------------------------------------------------------------
import pandas as pd

all_dates = []
if sleep_df is not None:
    all_dates.extend(pd.to_datetime(sleep_df["Date"], errors="coerce").dropna().tolist())
if activities_df is not None:
    all_dates.extend(pd.to_datetime(activities_df["Date"], errors="coerce").dropna().tolist())

if all_dates:
    min_date = min(all_dates).date()
    max_date = max(all_dates).date()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Date Range")
    date_range = st.sidebar.slider(
        "Filter data",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
    )

    if sleep_df is not None:
        sleep_df = sleep_df[
            pd.to_datetime(sleep_df["Date"], errors="coerce").dt.date.between(*date_range)
        ]
    if activities_df is not None:
        activities_df = activities_df[
            pd.to_datetime(activities_df["Date"], errors="coerce").dt.date.between(*date_range)
        ]

# ---------------------------------------------------------------------------
# Insights strip
# ---------------------------------------------------------------------------
st.subheader("Insights")
insights = generate_all_insights(sleep_df, activities_df)

insight_display = [
    ("💤 Sleep Score", insights["avg_sleep_score"]),
    ("📈 Trend", insights["sleep_trend"]),
    ("🏆 Best / Worst", insights["best_worst_sleep"]),
    ("🌙 Deep Sleep", insights["avg_deep_sleep"]),
    ("🏋️ Activities", insights["activity_summary"]),
    ("🔗 Correlation", insights["sleep_activity_correlation"]),
]

cols = st.columns(len(insight_display))
for col, (label, text) in zip(cols, insight_display):
    col.metric(label=label, value="")
    col.caption(text)

st.markdown("---")

# ---------------------------------------------------------------------------
# Sleep section
# ---------------------------------------------------------------------------
if sleep_df is not None and not sleep_df.empty:
    st.subheader("Sleep")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(sleep_score_trend(sleep_df), use_container_width=True)
    with col2:
        st.plotly_chart(sleep_stages_bar(sleep_df), use_container_width=True)

# ---------------------------------------------------------------------------
# Activity section
# ---------------------------------------------------------------------------
if activities_df is not None and not activities_df.empty:
    st.subheader("Activities")
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(activity_log_chart(activities_df), use_container_width=True)
    with col4:
        st.plotly_chart(activity_type_pie(activities_df), use_container_width=True)

# ---------------------------------------------------------------------------
# Correlation section
# ---------------------------------------------------------------------------
if sleep_df is not None and activities_df is not None:
    st.subheader("Sleep vs Activity Correlation")
    st.plotly_chart(hr_vs_activity_days(sleep_df, activities_df), use_container_width=True)
