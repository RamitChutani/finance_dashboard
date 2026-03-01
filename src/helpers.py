"""
Shared helper utilities for the Streamlit app.

Why this file is separate from `app.py`:
- Keeps UI code focused on presentation.
- Centralizes data-loading logic in one reusable place.
- Makes it easy to reuse the same loader across future `pages/`.
- Improves maintainability and testability of non-UI logic.
"""

import pandas as pd
import streamlit as st
from pathlib import Path
from src.balance import build_account_balance_timeline

MASTER_CSV = Path(__file__).parent.parent / "data" / "transactions.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    # central data loaded used by app.py and all future pages
    # if we want to change data source, we only change it here
    df = pd.read_csv(MASTER_CSV)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


@st.cache_data
def load_account_balances() -> pd.DataFrame:
    # Build once and cache so account pages/charts can reuse the same timeline.
    return build_account_balance_timeline(load_data())
