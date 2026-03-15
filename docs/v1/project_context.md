# Personal Health Dashboard (Garmin Data) - Project Context

## 1. MVP Boundaries (Version 1.0)

**Core Problem:** Garmin watch tracking produces a lot of raw data but fails to provide actionable, long-term analytical insights or highlight cross-metric correlations (e.g., how running impacts sleep).
**Solution:** A local, personal health database and dashboard that visualizes trends and provides hard-coded heuristic insights.

### In Scope for V1.0:

* **Local Data Persistence (Smart Merge):** A drag-and-drop UI where the user uploads weekly Garmin CSV exports (Sleep and Activities). The system will automatically read, deduplicate (by date, keeping the most recently uploaded row), and merge these into local `master_sleep.csv` and `master_activities.csv` files.
* **Interactive Dashboard:** Visualization of Sleep Trends, Activity logs, and correlations (e.g., Resting Heart Rate vs. Activity days) using interactive charts.
* **Hard-Coded Insights Engine:** Text-based analysis generated purely via Python/Pandas logic (e.g., "Your average Sleep Score this week is X", "Your Deep Sleep drops when you do a 'Running' activity").
* **Data Sources:** Strictly limited to Garmin's "Sleep" CSVs and "Activities" CSVs.

### Out of Scope for V1.0 (Deferred to V2.0):

* Direct API integrations with Garmin (requires enterprise approval) or automated web-scraping (too brittle).
* LLM / AI API integration (Anthropic/OpenAI) within the app code itself. All V1 insights will be hard-coded metrics.

---

## 2. Tech Stack Selection

* **Language:** Python 3.9+
* **Frontend/UI:** Streamlit (Provides rapid dashboard creation and native drag-and-drop file uploaders).
* **Data Processing:** Pandas (Crucial for CSV concatenation, date parsing, and the "Smart Merge" deduplication logic).
* **Visualization:** Plotly (or Streamlit native charts) for interactive, zoomable graphs.

---

## 3. Security & Environment Plan

Because this app handles sensitive personal health data, strict local-only security is required.

**Environment Variables (`.env` / `.env.example`):**

* No external API keys are required for V1.0.
* `.env.example` will remain empty but should be created as a placeholder for V2.0.

**Git Ignore (`.gitignore`):**

* MUST explicitly ignore the local data directory and all CSV files to prevent accidental health data leaks.

```text
# .gitignore
__pycache__/
.env
.venv/
env/
venv/
data/
*.csv
```

---

## 4. Architecture & Directory Structure

```
my-health-dashboard/
│
├── data/                       # IGNORED IN GIT. Holds the persistent master datasets.
│   ├── master_sleep.csv        # Auto-generated & updated upon user upload
│   └── master_activities.csv   # Auto-generated & updated upon user upload
│
├── docs/                       # Project documentation for the AI Execution Agent
│   ├── project_context.md      # This exact file
│   └── progress.md             # The milestone checklist
│
├── utils/                      # Helper modules for the app
│   ├── __init__.py
│   ├── data_pipeline.py        # Logic for reading, deduplicating, and merging CSVs
│   └── insights_engine.py      # Hard-coded heuristic rules for text insights
│
├── components/                 # UI components
│   ├── __init__.py
│   └── charts.py               # Plotly/Streamlit visualization generation
│
├── app.py                      # The main Streamlit application entry point
├── requirements.txt            # Python dependencies (streamlit, pandas, plotly)
├── .env.example                # Placeholder for future API keys
└── .gitignore                  # Strict exclusion of /data and *.csv
```
