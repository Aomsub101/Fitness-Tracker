# Personal Health Dashboard (Garmin) - V2.0 Automation Upgrade Context

## 1. V2.0 Boundaries (The Automation Upgrade)

**Core Problem:** Manually exporting CSVs from the Garmin Connect web interface every week is tedious and creates friction, leading to stale data.
**Solution:** Integrate the `garminconnect` Python library to securely authenticate and fetch the latest Sleep and Activity data directly via an API call, translating it on-the-fly to match our V1.0 data structure.

### In Scope for V2.0:

* **API Integration:** Use `garminconnect` to log in and fetch the last 7-14 days of Sleep and Activity data.
* **Session Management:** Save the Garmin API session tokens locally so the app doesn't have to re-authenticate with a password on every single sync (prevents rate-limiting/bans).
* **The Translation Layer:** A new utility script that takes Garmin's raw JSON API response and reshapes it into the exact Pandas DataFrame columns our V1.0 app expects (e.g., mapping JSON `sleepScore` to our CSV's `Sleep Score`).
* **UI Update:** A "🔄 Sync Latest Data" button in the Streamlit sidebar that triggers the fetch, translate, and Smart Merge pipeline.

### Out of Scope for V2.0:

* LLM / AI API integration (Anthropic/OpenAI) for text insights. We are still relying on our V1.0 hard-coded Insights Engine for this phase.
* Fetching older historical data (years back) via API. The API sync will focus on recent/incremental updates (e.g., the last 14 days) to append to the master files.

---

## 2. Tech Stack Additions

* **Existing:** Python, Streamlit, Pandas, Plotly, pytest.
* **New Integrations:** * `garminconnect` (The unofficial Garmin API wrapper).
  * `python-dotenv` (For securely loading credentials from a `.env` file).

---

## 3. Security & Environment Plan

This is the most critical update. We are introducing real credentials.

**Environment Variables (`.env`):**

* Create a `.env` file in the root directory (do not commit this).
* Required variables:
  * `GARMIN_EMAIL=your_email@example.com`
  * `GARMIN_PASSWORD=your_secure_password`

**Git Ignore (`.gitignore`) Updates:**

* MUST explicitly ignore the `.env` file.
* MUST explicitly ignore the local session token directory (e.g., `session/` or `~/.garth` depending on where we configure `garminconnect` to save tokens).

---

## 4. Updated Architecture & Directory Structure

```text
my-health-dashboard/
│
├── data/                   
│   ├── master_sleep.csv    
│   └── master_activities.csv   
│
├── session/                    # NEW: IGNORED IN GIT. Holds Garmin auth tokens.
│
├── docs/                   
│   ├── project_context.md      # V1 Context
│   ├── v2_project_context.md   # This exact file
│   └── v2_progress.md          # The new milestone checklist
│
├── utils/                  
│   ├── __init__.py
│   ├── data_pipeline.py    
│   ├── insights_engine.py  
│   └── garmin_api.py           # NEW: API auth, fetching, and JSON->Pandas translation
│
├── components/             
│   ├── __init__.py
│   └── charts.py           
│
├── app.py                  
├── requirements.txt            # UPDATED: Add garminconnect, python-dotenv
├── .env                        # NEW: IGNORED IN GIT. Holds email/password.
├── .env.example                # UPDATED: Add GARMIN_EMAIL and GARMIN_PASSWORD stubs.
└── .gitignore                  # UPDATED: Ignore .env and session/
```
