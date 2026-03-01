"""
Data transformation (ETL) module.

Why this file is separate from `app.py`:
- Raw CSV ingestion and normalization are backend/data concerns.
- Running transforms independently keeps dashboard startup lightweight.
- Data logic can be tested and evolved without touching UI code.

This structure is a design choice for clarity and utility, not a Streamlit requirement.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
MASTER_CSV = Path(__file__).parent.parent / "data" / "transactions.csv" # this is just a pointed to a location, does not check if it exists yet
RAW_TO_CANONICAL_COLS = {
    "TIME": "datetime",
    "TYPE": "type",
    "AMOUNT": "amount",
    "CATEGORY": "category",
    "ACCOUNT": "account",
    "NOTES ": "notes",
}
CANONICAL_COLUMNS = [
    "datetime",
    "type",
    "amount",
    "category",
    "account",
    "notes",
    "date",
    "month",
    "year",
    "day",
    "signed_amount",
    "is_opening_balance",
]
TRANSACTION_DEDUPE_KEYS = ["datetime", "type", "amount", "category", "account", "notes"]
ALLOWED_TYPES = {"Income", "Expense", "Transfer"}


# Why do we not ensure path exists here itself?
# Good design principles suggest to:
# 1. Define paths early (cheap, side-effect free)
# 2. Touch the filesystem as late as possible
# 3. Only guard the operations that need guarding
# This keeps code testable, import-safe, and reusable because you can import this file without creating directories, it creates/checks when app is run


def clean_raw(df: pd.DataFrame) -> pd.DataFrame:

    validate_raw_columns(df)

    # Rename export columns to project-level canonical names.
    df = df.rename(columns=RAW_TO_CANONICAL_COLS)

    # Normalize fundamental fields first.
    df["datetime"] = pd.to_datetime(df["datetime"], format="mixed", errors="raise")
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    if (df["amount"] < 0).any():
        raise ValueError("Raw AMOUNT must be non-negative; sign is derived from TYPE.")

    # cleaning the type column values to remove prefixes
    df["type"] = df["type"].str.replace(r"^[\(\+\-\*\) ]+", "", regex=True).str.strip()
    unknown_types = set(df["type"].dropna().unique()) - ALLOWED_TYPES
    if unknown_types:
        raise ValueError(f"Unsupported transaction type(s): {sorted(unknown_types)}")

    df = normalize_canonical_types(df)
    validate_canonical_schema(df)
    return df


def validate_raw_columns(df: pd.DataFrame) -> None:
    # Fail early when the export format changes unexpectedly.
    required_raw = set(RAW_TO_CANONICAL_COLS.keys())
    missing = sorted(required_raw - set(df.columns))
    if missing:
        raise ValueError(f"Raw file is missing required column(s): {missing}")


def validate_canonical_schema(df: pd.DataFrame) -> None:
    # Contract check: app/features can rely on this shape and core constraints.
    missing = sorted(set(CANONICAL_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Canonical schema missing column(s): {missing}")

    if df["datetime"].isna().any():
        raise ValueError("`datetime` contains null values.")
    if (df["month"] < 1).any() or (df["month"] > 12).any():
        raise ValueError("`month` must be between 1 and 12.")
    if (df["day"] < 1).any() or (df["day"] > 31).any():
        raise ValueError("`day` must be between 1 and 31.")
    if df["is_opening_balance"].dtype != bool:
        raise ValueError("`is_opening_balance` must be boolean.")


def normalize_canonical_types(df: pd.DataFrame) -> pd.DataFrame:
    # Canonical type normalization ensures dedupe compares like-for-like values.
    work = df.copy()
    work["datetime"] = pd.to_datetime(work["datetime"], format="mixed", errors="raise")
    work["type"] = work["type"].astype(str).str.strip()
    work["amount"] = pd.to_numeric(work["amount"], errors="raise")
    if (work["amount"] < 0).any():
        raise ValueError("`amount` must be non-negative in canonical storage.")

    work["category"] = work["category"].fillna("").astype(str).str.strip()
    work["account"] = work["account"].fillna("").astype(str).str.strip()
    work["notes"] = work["notes"].fillna("").astype(str)

    work["date"] = work["datetime"].dt.date
    work["month"] = work["datetime"].dt.month
    work["year"] = work["datetime"].dt.year
    work["day"] = work["datetime"].dt.day
    work["signed_amount"] = work.apply(
        lambda r: r["amount"] if r["type"] == "Income"
        else (-r["amount"] if r["type"] == "Expense" else 0),
        axis=1,
    )
    work["is_opening_balance"] = work["notes"].str.lower().str.contains("starting|opening balance", na=False)
    return work[CANONICAL_COLUMNS]


def run():
    raw_files = list(RAW_DIR.glob("*.csv")) # creates a list of paths to be read later
    if not raw_files:
        print("No raw files found in data/raw")
        return
    
    frames = [pd.read_csv(f) for f in raw_files] # creates a list of dataframes from paths
    cleaned = clean_raw(pd.concat(frames, ignore_index=True)) # concat first combines into one big df, then cleans it according to clean_raw() function

    master = pd.read_csv(MASTER_CSV) if MASTER_CSV.exists() else pd.DataFrame(columns=CANONICAL_COLUMNS)
    if not master.empty:
        missing_master_cols = sorted(set(CANONICAL_COLUMNS) - set(master.columns))
        if missing_master_cols:
            raise ValueError(f"Existing master CSV is missing required column(s): {missing_master_cols}")
        master = normalize_canonical_types(master)

    combined = pd.concat([master, cleaned], ignore_index=True) # add latest cleaned csv to master
    combined = normalize_canonical_types(combined)
    combined = combined.drop_duplicates(subset=TRANSACTION_DEDUPE_KEYS)
    combined = combined.sort_values("datetime").reset_index(drop=True)
    validate_canonical_schema(combined)

    MASTER_CSV.parent.mkdir(parents=True, exist_ok=True) # safety measure to prevent FileNotFoundError before we write the combined df to the CSV file
    combined.to_csv(MASTER_CSV, index=False) # write back to CSV file after joining and cleaning the dataframes
    print(f"Done. {len(combined)} rows added to database.")

if __name__ == "__main__":
    run()
