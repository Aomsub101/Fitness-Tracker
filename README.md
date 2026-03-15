# Garmin Personal Health Dashboard

A local, privacy-first dashboard for visualising and analysing Garmin fitness data. Upload your Garmin CSV exports to track sleep trends, activity logs, and cross-metric correlations — all processed entirely on your machine with no external API calls.

---

## Features

- **Smart Merge uploads** — drag and drop one or multiple Garmin CSVs at once; duplicate dates are automatically deduplicated (newest upload always wins)
- **Sleep analytics** — Sleep Score trend, sleep stage breakdown (Deep / Light / REM / Awake), best & worst nights
- **Activity log** — scatter chart of activities over time, type distribution pie chart
- **Heuristic insights** — plain-English summaries (average score, improving/declining trend, most common activity, etc.) generated purely from Pandas logic
- **Cross-metric correlation** — Sleep Score vs activity days overlay chart
- **Date range filter** — sidebar slider to zoom into any time window

---

## Tech Stack

| Layer | Library |
|---|---|
| UI / Dashboard | [Streamlit](https://streamlit.io) |
| Data processing | [Pandas](https://pandas.pydata.org) |
| Charts | [Plotly](https://plotly.com/python/) |
| Tests | [pytest](https://pytest.org) |
| Language | Python 3.9+ |

---

## Project Structure

```
fitness-tracker/
├── app.py                    # Streamlit entry point
├── utils/
│   ├── data_pipeline.py      # CSV ingestion, column normalisation, Smart Merge
│   └── insights_engine.py    # Hard-coded heuristic insight functions
├── components/
│   └── charts.py             # Plotly chart builders
├── tests/
│   ├── test_data_pipeline.py
│   ├── test_insights_engine.py
│   └── test_charts.py
├── data/                     # Git-ignored — holds master_sleep.csv, master_activities.csv
├── docs/                     # Architecture spec and milestone progress
├── requirements.txt
└── .env.example              # Placeholder for future API keys
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd fitness-tracker

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the Dashboard

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## Usage

### Exporting data from Garmin Connect

1. Go to [Garmin Connect](https://connect.garmin.com)
2. Navigate to **Health Stats → Sleep** or **Activities**
3. Click **Export CSV** (top-right of the data table)

### Uploading data

1. Open the sidebar in the dashboard
2. Use the **Sleep CSV** uploader to upload one or more sleep export files
3. Use the **Activities CSV** uploader to upload one or more activity export files
4. The dashboard refreshes automatically — duplicate dates are resolved on every upload

> **Note:** Garmin's Sleep CSV uses non-standard column names (`Sleep Score 4 Weeks` for the date, `Score` for the sleep score). The pipeline normalises these automatically.

---

## Running Tests

```bash
# Run the full test suite
pytest tests/ -v

# Run a single test file
pytest tests/test_data_pipeline.py -v
```

Total: **68 tests** across data pipeline, insights engine, and chart components.

---

## Data & Privacy

All data is stored locally in the `data/` directory, which is excluded from git via `.gitignore`. No health data is ever sent to an external server. The `data/` folder and all `*.csv` files are ignored by git to prevent accidental commits.

---

## Roadmap

- **V2.0** — Direct Garmin Connect API integration, LLM-powered insights (Anthropic / OpenAI)
