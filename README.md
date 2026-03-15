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
| Garmin API | [garminconnect](https://pypi.org/project/garminconnect/) |
| Env / Secrets | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| Tests | [pytest](https://pytest.org) |
| Language | Python 3.9+ |

---

## Project Structure

```
fitness-tracker/
├── app.py                    # Streamlit entry point
├── utils/
│   ├── data_pipeline.py      # CSV ingestion, column normalisation, Smart Merge
│   ├── insights_engine.py    # Hard-coded heuristic insight functions
│   └── garmin_api.py         # Garmin Connect auth, fetch, and JSON→DataFrame translation
├── components/
│   └── charts.py             # Plotly chart builders
├── tests/
│   ├── test_data_pipeline.py
│   ├── test_insights_engine.py
│   ├── test_charts.py
│   └── test_garmin_api.py
├── data/                     # Git-ignored — holds master_sleep.csv, master_activities.csv
├── session/                  # Git-ignored — holds Garmin session tokens
├── docs/                     # Architecture spec and milestone progress
├── requirements.txt
└── .env.example              # Copy to .env and fill in Garmin credentials
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

### Option A — Auto-Sync (V2.0)

1. Copy `.env.example` to `.env` and fill in your Garmin Connect credentials:
   ```
   GARMIN_EMAIL=your_email@example.com
   GARMIN_PASSWORD=your_secure_password
   ```
2. Open the dashboard sidebar and click **🔄 Sync Last 14 Days**
3. The app authenticates, fetches the latest sleep and activity data, merges it, and refreshes automatically
4. On first sync, credentials are used once and two token files are written to `session/` (`oauth1_token.json`, `oauth2_token.json`). Subsequent syncs load these tokens directly and skip the password step entirely

### Option B — Manual CSV Upload (fallback)

1. Go to [Garmin Connect](https://connect.garmin.com)
2. Navigate to **Health Stats → Sleep** or **Activities** and click **Export CSV**
3. Use the sidebar uploaders to upload one or more CSV files
4. Duplicate dates are resolved automatically (newest upload wins)

> **Note:** Garmin's Sleep CSV uses non-standard column names (`Sleep Score 4 Weeks` for the date, `Score` for the sleep score). The pipeline normalises these automatically.

---

## Running Tests

```bash
# Run the full test suite
pytest tests/ -v

# Run a single test file
pytest tests/test_data_pipeline.py -v
```

Total: **100 tests** across data pipeline, insights engine, chart components, and Garmin API integration.

---

## Data & Privacy

All data is stored locally in the `data/` directory, which is excluded from git via `.gitignore`. No health data is ever sent to an external server. The `data/` folder and all `*.csv` files are ignored by git to prevent accidental commits.

---

## Roadmap

- **V2.0** — Direct Garmin Connect API integration, LLM-powered insights (Anthropic / OpenAI)
