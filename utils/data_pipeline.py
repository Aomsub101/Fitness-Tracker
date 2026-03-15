"""
data_pipeline.py

Handles all CSV ingestion and Smart Merge logic for Garmin exports.

Smart Merge rules:
  - New upload rows are concatenated after the existing master rows.
  - Deduplication is by date column, keeping the LAST occurrence
    (i.e., newly uploaded data wins over older stored data).
  - Result is sorted ascending by date and written back to master CSV.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
MASTER_SLEEP_PATH = DATA_DIR / "master_sleep.csv"
MASTER_ACTIVITIES_PATH = DATA_DIR / "master_activities.csv"

SLEEP_DATE_COL = "Date"
ACTIVITIES_DATE_COL = "Date"

# Garmin exports the date column as "Sleep Score 4 Weeks" and the score as "Score".
# Normalise these to the internal standard names so all downstream code stays unchanged.
SLEEP_COL_RENAME = {
    "Sleep Score 4 Weeks": "Date",
    "Score": "Sleep Score",
}


def normalize_sleep_df(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw Garmin Sleep CSV columns to internal standard names.

    Specifically maps:
      'Sleep Score 4 Weeks' → 'Date'
      'Score'               → 'Sleep Score'
    """
    rename = {k: v for k, v in SLEEP_COL_RENAME.items() if k in df.columns}
    if rename:
        logger.info("Normalising sleep columns: %s", rename)
        df = df.rename(columns=rename)
    return df


def load_csv(file) -> pd.DataFrame:
    """Read a CSV from a file path string or file-like object.

    Args:
        file: A file path (str/Path) or file-like object (e.g. Streamlit UploadedFile).

    Returns:
        DataFrame with the CSV contents.

    Raises:
        FileNotFoundError: If a path string is given and the file does not exist.
        pd.errors.ParserError: If the file cannot be parsed as CSV.
    """
    df = pd.read_csv(file)
    logger.info("Loaded CSV with %d rows, columns: %s", len(df), list(df.columns))
    return df


def smart_merge(new_df: pd.DataFrame, master_path: Path, date_col: str) -> pd.DataFrame:
    """Merge new_df into an existing master CSV using Smart Merge logic.

    Args:
        new_df:      Newly uploaded DataFrame to merge in.
        master_path: Path to the master CSV file (created if absent).
        date_col:    Name of the column used as the unique date key.

    Returns:
        The merged and deduplicated DataFrame (also persisted to master_path).

    Raises:
        ValueError: If date_col is not present in the combined data.
    """
    master_path = Path(master_path)
    master_path.parent.mkdir(parents=True, exist_ok=True)

    if master_path.exists():
        master_df = pd.read_csv(master_path)
        logger.info("Loaded existing master (%d rows) from %s", len(master_df), master_path)
        combined = pd.concat([master_df, new_df], ignore_index=True)
    else:
        logger.info("No master file at %s — creating new.", master_path)
        combined = new_df.copy()

    if date_col not in combined.columns:
        raise ValueError(
            f"Date column '{date_col}' not found. Available columns: {list(combined.columns)}"
        )

    combined[date_col] = pd.to_datetime(combined[date_col], errors="coerce")

    rows_before = len(combined)
    combined = combined.drop_duplicates(subset=[date_col], keep="last")
    combined = combined.sort_values(date_col).reset_index(drop=True)
    logger.info(
        "Smart Merge: %d rows → %d rows after deduplication.", rows_before, len(combined)
    )

    combined.to_csv(master_path, index=False)
    logger.info("Saved merged data to %s", master_path)
    return combined


def merge_sleep(new_df: pd.DataFrame) -> pd.DataFrame:
    """Smart merge for Garmin Sleep CSV uploads."""
    return smart_merge(normalize_sleep_df(new_df), MASTER_SLEEP_PATH, SLEEP_DATE_COL)


def merge_activities(new_df: pd.DataFrame) -> pd.DataFrame:
    """Smart merge for Garmin Activities CSV uploads."""
    return smart_merge(new_df, MASTER_ACTIVITIES_PATH, ACTIVITIES_DATE_COL)


def load_master_sleep() -> Optional[pd.DataFrame]:
    """Load the persisted master sleep dataset, or None if not yet created."""
    if not MASTER_SLEEP_PATH.exists():
        return None
    df = pd.read_csv(MASTER_SLEEP_PATH, parse_dates=[SLEEP_DATE_COL])
    logger.info("Loaded master sleep (%d rows).", len(df))
    return df


def load_master_activities() -> Optional[pd.DataFrame]:
    """Load the persisted master activities dataset, or None if not yet created."""
    if not MASTER_ACTIVITIES_PATH.exists():
        return None
    df = pd.read_csv(MASTER_ACTIVITIES_PATH, parse_dates=[ACTIVITIES_DATE_COL])
    logger.info("Loaded master activities (%d rows).", len(df))
    return df
