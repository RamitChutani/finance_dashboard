"""
Account balance engine.

Purpose:
- Convert canonical transactions into account-level money flows.
- Compute daily running balances per account.

Why this module is separate:
- Keeps financial computation logic independent from UI rendering.
- Makes the balance engine reusable for dashboard pages and tests.
"""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "datetime",
    "type",
    "amount",
    "account",
    "signed_amount",
}


def _validate_columns(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Missing required column(s) for balance engine: {missing}")


def _build_transfer_flows(transfers: pd.DataFrame) -> pd.DataFrame:
    if transfers.empty:
        return pd.DataFrame(columns=["datetime", "account", "net_flow"])

    account_split = transfers["account"].astype(str).str.split("->", n=1, expand=True)
    if account_split.shape[1] != 2:
        raise ValueError("Transfer rows must use `from_account->to_account` format in `account`.")

    source_account = account_split[0].str.strip()
    destination_account = account_split[1].str.strip()

    if (source_account == "").any() or (destination_account == "").any():
        raise ValueError("Transfer `account` must include non-empty source and destination names.")

    outflows = pd.DataFrame(
        {
            "datetime": transfers["datetime"].values,
            "account": source_account.values,
            "net_flow": -transfers["amount"].values,
        }
    )
    inflows = pd.DataFrame(
        {
            "datetime": transfers["datetime"].values,
            "account": destination_account.values,
            "net_flow": transfers["amount"].values,
        }
    )

    return pd.concat([outflows, inflows], ignore_index=True)


def build_account_balance_timeline(df: pd.DataFrame) -> pd.DataFrame:
    # Input contract: canonical transactions from data/transactions.csv.
    _validate_columns(df)

    work = df.copy()
    work["datetime"] = pd.to_datetime(work["datetime"], format="mixed", errors="raise")
    work["amount"] = pd.to_numeric(work["amount"], errors="raise")
    work["signed_amount"] = pd.to_numeric(work["signed_amount"], errors="raise")

    non_transfer = work[work["type"] != "Transfer"][["datetime", "account", "signed_amount"]].rename(
        columns={"signed_amount": "net_flow"}
    )
    transfer = work[work["type"] == "Transfer"][["datetime", "account", "amount"]]
    transfer_flows = _build_transfer_flows(transfer)

    flow_ledger = pd.concat([non_transfer, transfer_flows], ignore_index=True)
    flow_ledger["date"] = flow_ledger["datetime"].dt.date

    daily = (
        flow_ledger.groupby(["account", "date"], as_index=False)["net_flow"]
        .sum()
        .sort_values(["account", "date"])
        .reset_index(drop=True)
    )
    daily["running_balance"] = daily.groupby("account")["net_flow"].cumsum()
    return daily[["date", "account", "net_flow", "running_balance"]]
