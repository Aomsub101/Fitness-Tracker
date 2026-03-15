# Progress

## Milestone 0: Project Bootstrap
- [x] Create .gitignore
- [x] Create .env.example
- [x] Create requirements.txt
- [x] Populate progress.md with milestones

## Milestone 1: Data Pipeline
- [x] Create utils/__init__.py
- [x] Create utils/data_pipeline.py (Smart Merge logic)
- [x] Create tests/test_data_pipeline.py
- [x] Tests verified by human

## Milestone 2: Insights Engine
- [x] Create utils/insights_engine.py (heuristic rules)
- [x] Create tests/test_insights_engine.py
- [x] Tests verified by human

## Milestone 3: Visualization Components
- [x] Create components/__init__.py
- [x] Create components/charts.py (Plotly charts)
- [x] Create tests/test_charts.py
- [x] Tests verified by human

## Milestone 4: Main Streamlit App
- [x] Create app.py (integrate all modules)
- [x] Tests verified by human

## Milestone 5: Multi-file Upload Support & Column Normalisation
- [x] Changed `st.file_uploader` for Sleep and Activities to `accept_multiple_files=True`
- [x] Updated upload handling loops to iterate over the list of files (each file merged individually with its filename shown in success/error messages)
- [x] Added `normalize_sleep_df()` in `data_pipeline.py` to rename raw Garmin Sleep CSV columns to internal standard names (`'Sleep Score 4 Weeks'` → `'Date'`, `'Score'` → `'Sleep Score'`) before merging, so all downstream code (insights engine, charts) remains unchanged
- [x] Added 6 tests for `normalize_sleep_df` including end-to-end `merge_sleep` test with raw Garmin column names
