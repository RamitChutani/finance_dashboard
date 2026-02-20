import pandas as pd
import streamlit as st
from pathlib import Path

MASTER_CSV = Path(__file__).parent.parent / "data" / "transactions.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    # central data loaded used by app.py and all future pages
    # if we want to change data source, we only change it here
    df = pd.read_csv(MASTER_CSV)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df