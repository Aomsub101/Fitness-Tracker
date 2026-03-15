# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local personal health dashboard for Garmin CSV data. Built with Python/Streamlit. No external APIs in V1.0 — all insights are hard-coded heuristics.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run tests
pytest

# Run a single test file
pytest tests/test_data_pipeline.py
```

## Architecture

```
fitness-tracker/
├── app.py                  # Streamlit entry point
├── utils/
│   ├── data_pipeline.py    # CSV ingestion, deduplication ("Smart Merge"), merging
│   └── insights_engine.py  # Hard-coded heuristic text insights (Pandas logic only)
├── components/
│   └── charts.py           # Plotly/Streamlit chart generation
├── data/                   # Git-ignored. Holds master_sleep.csv, master_activities.csv
└── docs/
    ├── project_context.md  # Architectural spec and MVP scope
    └── progress.md         # Milestone checklist — update [ ] → [x] as tasks complete
```

**Data flow:** User drags Garmin CSVs into the Streamlit UI → `data_pipeline.py` reads, deduplicates by date (keeping the most recently uploaded row), and merges into `data/master_sleep.csv` or `data/master_activities.csv` → `insights_engine.py` runs Pandas heuristics → `charts.py` renders Plotly charts.

## Development Rules (from `docs/executor.md`)

- **Sequential milestones:** Work on one milestone at a time per `docs/progress.md`.
- **Environment first:** Confirm `.gitignore` and `.env.example` exist before writing app logic.
- **Test with code:** Every functional block must have a corresponding automated test.
- **Human checkpoint:** After completing a milestone's code + tests + progress update, stop and wait for "Tests passed, proceed." before moving to the next milestone.
- **No destructive actions** without explicit user permission.
- **Include logging** in all modules for debuggability.

## Data & Security

- `data/` and `*.csv` are git-ignored — never commit health data.
- No external API keys required for V1.0; `.env.example` is an empty placeholder for V2.0.
- App is strictly local-only.
