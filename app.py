"""
Main Streamlit UI layer.

Why this file is separate:
- `app.py` focuses on rendering widgets, charts, and tables.
- Data preparation/cleaning lives in `src/transform.py`.
- Shared loading utilities live in `src/helpers.py`.

This separation is not required by Streamlit syntax, but it keeps the app easier
to maintain, test, and grow as features/pages are added.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from src.helpers import load_data, load_account_balances

# In Streamlit, page config must be set before rendering any widgets or text.
# `layout="wide"` allows charts/tables to use the full browser width.
st.set_page_config(page_title="Finance Dashboard", layout="wide")

# Load once from the cached helper, then copy so local edits never mutate shared cache state.
df = load_data()
df = df.copy()

# Guard clause: stop early with a clear UI message when no data exists.
if df.empty:
    st.warning("No transactions found. Run the transform step and reload.")
    st.stop()

# Keep a pure date column for sidebar date filtering (faster/cleaner than filtering datetimes repeatedly).
df["date"] = df["datetime"].dt.date
balances = load_account_balances().copy()


def get_preset_range(preset: str, anchor_date, min_date):
    # Presets are converted to concrete [start_date, end_date] boundaries.
    # `anchor_date` is the latest date in your data, so filters are data-driven.
    if preset == "All Time":
        return min_date, anchor_date
    if preset == "MTD":
        return anchor_date.replace(day=1), anchor_date
    if preset == "YTD":
        return anchor_date.replace(month=1, day=1), anchor_date
    if preset == "FYTD":
        fy_start_year = anchor_date.year if anchor_date.month >= 4 else anchor_date.year - 1
        return anchor_date.replace(year=fy_start_year, month=4, day=1), anchor_date

    months_back = {
        "Last 1M": 1,
        "Last 3M": 3,
        "Last 6M": 6,
        "Last 12M": 12,
    }[preset]
    # DateOffset handles month arithmetic safely (month lengths vary).
    start_date = (
        pd.Timestamp(anchor_date) - pd.DateOffset(months=months_back) + pd.Timedelta(days=1)
    ).date()
    return max(start_date, min_date), anchor_date

# Sidebar controls should be defined first because they determine the filtered dataset
# that every metric, chart, and table uses below.

st.sidebar.header("Filters")

# Use data bounds so widgets can never select dates outside available transactions.
anchor_date = df["date"].max()
min_date = df["date"].min()

# Two filtering modes:
# 1) Preset: common business windows (YTD, FYTD, last N months)
# 2) Custom Range: explicit start/end dates
time_filter_mode = st.sidebar.radio("Timeline Filter", ["Preset", "Custom Range"])

if time_filter_mode == "Preset":
    preset_options = ["YTD", "FYTD", "Last 1M", "Last 3M", "Last 6M", "Last 12M", "MTD", "All Time"]
    selected_preset = st.sidebar.selectbox("Time Slice", preset_options, index=0)
    start_date, end_date = get_preset_range(selected_preset, anchor_date, min_date)
else:
    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(max(min_date, anchor_date - pd.Timedelta(days=89)), anchor_date),
        min_value=min_date,
        max_value=anchor_date,
    )
    # date_input may return a single date if only one is selected; normalize to a 2-date range.
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = selected_dates, selected_dates
    # Defensive normalization if user input comes in reverse order.
    if start_date > end_date:
        start_date, end_date = end_date, start_date

# Show the resolved range so users can verify exactly what period is active.
st.sidebar.caption(f"Range: {start_date} to {end_date}")
selected_types = st.sidebar.multiselect("Type", ["Income", "Expense", "Transfer"], default=["Income", "Expense"])

# Single source of truth: one filtered DataFrame for the entire dashboard.
filtered = df[
    (df["date"] >= start_date) &
    (df["date"] <= end_date) &
    df["type"].isin(selected_types) &
    ~df["is_opening_balance"]
]

# --- scorecards ---
st.title("Personal Finance Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Total Income", f"₹{filtered[filtered['type']=='Income']['amount'].sum():,.0f}")
col2.metric("Total Expenses", f"₹{filtered[filtered['type']=='Expense']['amount'].sum():,.0f}")
col3.metric("Net", f"₹{filtered['signed_amount'].sum():,.0f}")

st.divider()

# --- charts ---
col4, col5 = st.columns(2)

with col4:
    st.subheader("Monthly Income vs Expenses")
    monthly = (
        # Convert each timestamp to month-start so bars represent calendar months.
        filtered.assign(year_month=filtered["datetime"].dt.to_period("M").dt.to_timestamp())
        .groupby(["year_month", "type"])["amount"]
        .sum()
        .reset_index()
        .sort_values("year_month")
    )
    # barmode="group" puts bars side by side rather than stacked
    fig1 = px.bar(
        monthly,
        x="year_month",
        y="amount",
        color="type",
        barmode="group",
    )
    # width="stretch" makes the chart fill whatever column it's in
    st.plotly_chart(fig1, width="stretch")

with col5:
    st.subheader("Spending by Category")
    # Donut shows expense composition only; income/transfer are excluded intentionally.
    expenses = filtered[filtered["type"] == "Expense"]
    cat = expenses.groupby("category")["amount"].sum().reset_index()
    # `hole=0.4` turns a pie into a donut, improving label readability.
    fig2 = px.pie(cat, values="amount", names="category", hole=0.4)
    st.plotly_chart(fig2, width="stretch")

st.divider()

# --- account views ---
st.subheader("Account Balance Views")
account_col1, account_col2 = st.columns(2)

# Timeline shows only dates inside the selected filter window.
balances_in_range = balances[
    (balances["date"] >= start_date) &
    (balances["date"] <= end_date)
].copy()

# Allocation snapshot uses the latest known balance per account up to end_date.
allocation_snapshot = (
    balances[balances["date"] <= end_date]
    .sort_values(["account", "date"])
    .groupby("account", as_index=False)
    .tail(1)
    .sort_values("running_balance", ascending=False)
)

with account_col1:
    st.caption("Running balance by account")
    if balances_in_range.empty:
        st.info("No account balance data available for the selected date range.")
    else:
        fig3 = px.line(
            balances_in_range,
            x="date",
            y="running_balance",
            color="account",
            markers=True,
        )
        st.plotly_chart(fig3, width="stretch")

with account_col2:
    st.caption("Asset allocation at period end")
    if allocation_snapshot.empty:
        st.info("No account balances found up to the selected end date.")
    else:
        positive_balances = allocation_snapshot[allocation_snapshot["running_balance"] > 0]
        if positive_balances.empty:
            st.info("No positive balances available for allocation view.")
        else:
            fig4 = px.pie(
                positive_balances,
                values="running_balance",
                names="account",
                hole=0.4,
            )
            st.plotly_chart(fig4, width="stretch")

# --- log of transactions ---
# Transaction log is kept interactive (sorting, scrolling, column resize).
st.subheader("Transaction Log")
st.dataframe(
    filtered[["datetime", "type", "amount", "category", "account", "notes"]]
    .sort_values("datetime", ascending=False),
    width="stretch"
)
