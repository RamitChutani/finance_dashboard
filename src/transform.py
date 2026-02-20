import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
MASTER_CSV = Path(__file__).parent.parent / "data" / "transactions.csv" # this is just a pointed to a location, does not check if it exists yet


# Why do we not ensure path exists here itself?
# Good design principles suggest to:
# 1. Define paths early (cheap, side-effect free)
# 2. Touch the filesystem as late as possible
# 3. Only guard the operations that need guarding
# This keeps code testable, import-safe, and reusable because you can import this file without creating directories, it creates/checks when app is run


def clean_raw(df: pd.DataFrame) -> pd.DataFrame:

    # renaming columns for clarity, using "NOTES " because original csv has blank
    df = df.rename(columns={
        "TIME": "datetime",
        "TYPE": "type",
        "AMOUNT": "amount",
        "CATEGORY": "category",
        "ACCOUNT": "account",
        "NOTES ": "notes",
    })

    # extracting date relevant features from datetime
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["date"] = df["datetime"].dt.date
    df["month"] = df["datetime"].dt.month
    df["year"] = df["datetime"].dt.year
    df["day"] = df["datetime"].dt.day

    # cleaning the type column values to remove prefixes
    df["type"] = df["type"].str.replace(r"^[\(\+\-\*\) ]+", "", regex=True).str.strip()
    
    # creating new column to make amount value positive for income, negative for expense, 0 for transfers across accounts
    df["signed_amount"] = df.apply(
        lambda r: r["amount"] if r["type"] == "Income"
        else (-r["amount"] if r["type"] == "Expense" else 0),
        axis = 1
    )

    # flagging rows that are not real transactions, but opening balance rows for various accounts
    df["is_opening_balance"] = df["notes"].str.lower().str.contains("starting|opening balance", na=False)

    return df

def run():
    raw_files = list(RAW_DIR.glob("*.csv")) # creates a list of paths to be read later
    if not raw_files:
        print("No raw files found in data/raw")
        return
    
    frames = [pd.read_csv(f) for f in raw_files] # creates a list of dataframes from paths
    cleaned = clean_raw(pd.concat(frames, ignore_index=True)) # concat first combines into one big df, then cleans it according to clean_raw() function

    master = pd.read_csv(MASTER_CSV) if MASTER_CSV.exists() else pd.DataFrame() # the master df that gets cleaned df added to it, so starts with an empty df

    combined = pd.concat([master, cleaned], ignore_index=True) # add latest cleaned csv to master
    combined = combined.drop_duplicates()
    combined = combined.sort_values("datetime").reset_index(drop=True)

    MASTER_CSV.parent.mkdir(parents=True, exist_ok=True) # safety measure to prevent FileNotFoundError before we write the combined df to the CSV file
    combined.to_csv(MASTER_CSV, index=False) # write back to CSV file after joining and cleaning the dataframes
    print(f"Done. {len(combined)} rows added to database.")

if __name__ == "__main__":
    run()