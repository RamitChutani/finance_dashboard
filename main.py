import pandas as pd
from pathlib import Path
from src.balance import build_account_balance_timeline

MASTER_CSV = Path(__file__).parent / "data" / "transactions.csv"


def main():
    # Minimal runtime check for the account balance engine.
    transactions = pd.read_csv(MASTER_CSV)
    transactions["datetime"] = pd.to_datetime(transactions["datetime"])
    balances = build_account_balance_timeline(transactions)
    print(f"Transactions: {len(transactions)}")
    print(f"Balance rows: {len(balances)}")
    print("Columns:", ", ".join(balances.columns))


if __name__ == "__main__":
    main()
