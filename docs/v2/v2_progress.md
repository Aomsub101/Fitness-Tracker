# V2.0 Progress Tracker

## Phase 1: Security & Dependencies

- [x] Update `requirements.txt` to include `garminconnect` and `python-dotenv`.
- [x] Update `.gitignore` to explicitly block `.env` and `session/`.
- [x] Update `.env.example` with `GARMIN_EMAIL` and `GARMIN_PASSWORD` placeholders.
- [x] Install new dependencies locally.

## Phase 2: API Authentication Engine

- [x] Create `utils/garmin_api.py`.
- [x] Write an initialization function that loads credentials from `.env` using `python-dotenv`.
- [x] Implement the Garmin client login logic. **Crucial:** Configure it to save and load session tokens from the local `session/` directory to avoid rate limits and repeated password logins.
- [x] Write a simple test script (or unit test) to verify successful login without exposing credentials.

## Phase 3: The Fetch & Translate Layer

- [x] In `utils/garmin_api.py`, write a `fetch_recent_sleep(days=14)` function that pulls sleep JSON.
- [x] Write a translator function that converts the sleep JSON into a Pandas DataFrame matching V1.0's exact column names (e.g., standardizing the date, mapping the score).
- [x] In `utils/garmin_api.py`, write a `fetch_recent_activities(days=14)` function that pulls activity JSON.
- [x] Write a translator function that converts the activity JSON into a Pandas DataFrame matching V1.0's exact columns.
- [x] Write unit tests to ensure the translated DataFrames can seamlessly pass into V1.0's existing `normalize_sleep_df` and merge logic.

## Phase 4: UI Integration

- [x] In `app.py`, load the `.env` variables at the top of the script.
- [x] Add a new section in the Streamlit sidebar (above the CSV uploaders) titled "Auto-Sync".
- [x] Add a "🔄 Sync Last 14 Days" button.
- [x] Wire the button to:
  - Trigger the API fetch & translate functions.
  - Pass the resulting DataFrames directly into V1.0's existing Smart Merge logic in `data_pipeline.py`.
  - Show a Streamlit success spinner and message upon completion.
  - Rerun the app to refresh the charts with the new data.
- [x] Verify the old CSV uploaders still work as a manual fallback.
- [x] Update `README.md` to reflect the new V2.0 Auto-Sync capabilities.
