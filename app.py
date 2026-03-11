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
        fy_start_year = (
            anchor_date.year if anchor_date.month >= 4 else anchor_date.year - 1
        )
        return anchor_date.replace(year=fy_start_year, month=4, day=1), anchor_date

    months_back = {
        "Last 1M": 1,
        "Last 3M": 3,
        "Last 6M": 6,
        "Last 12M": 12,
    }[preset]
    # DateOffset handles month arithmetic safely (month lengths vary).
    start_date = (
        pd.Timestamp(anchor_date)
        - pd.DateOffset(months=months_back)
        + pd.Timedelta(days=1)
    ).date()
    return max(start_date, min_date), anchor_date


def normalize_date_range(selected_dates):
    # Handle Streamlit date_input return shapes robustly across reruns/state restores.
    if isinstance(selected_dates, (tuple, list)):
        flat_dates = [d for d in selected_dates if not isinstance(d, (tuple, list))]
        if len(flat_dates) >= 2:
            start_date = pd.to_datetime(flat_dates[0]).date()
            end_date = pd.to_datetime(flat_dates[1]).date()
        elif len(flat_dates) == 1:
            start_date = pd.to_datetime(flat_dates[0]).date()
            end_date = start_date
        else:
            raise ValueError("Date range selection is empty.")
    else:
        start_date = pd.to_datetime(selected_dates).date()
        end_date = start_date

    if start_date > end_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


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
    preset_options = [
        "YTD",
        "FYTD",
        "Last 1M",
        "Last 3M",
        "Last 6M",
        "Last 12M",
        "MTD",
        "All Time",
    ]
    selected_preset = st.sidebar.selectbox("Time Slice", preset_options, index=0)
    start_date, end_date = get_preset_range(selected_preset, anchor_date, min_date)
else:
    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(max(min_date, anchor_date - pd.Timedelta(days=89)), anchor_date),
        min_value=min_date,
        max_value=anchor_date,
    )
    start_date, end_date = normalize_date_range(selected_dates)

# Show the resolved range so users can verify exactly what period is active.
st.sidebar.caption(f"Range: {start_date} to {end_date}")
selected_types = st.sidebar.multiselect(
    "Type", ["Income", "Expense", "Transfer"], default=["Income", "Expense"]
)

# Single source of truth: one filtered DataFrame for the entire dashboard.
filtered = df[
    (df["date"] >= start_date)
    & (df["date"] <= end_date)
    & df["type"].isin(selected_types)
    & ~df["is_opening_balance"]
].copy()

# Get list of all accounts
all_accounts = sorted(df["account"].unique())
account_options = ["All Accounts"] + all_accounts

# --- header ---
st.title("Personal Finance Dashboard")

# --- total stats (always shown) ---
col1, col2, col3 = st.columns(3)

total_income = filtered[filtered["type"] == "Income"]["amount"].sum()
total_expenses = filtered[filtered["type"] == "Expense"]["amount"].sum()
net = filtered["signed_amount"].sum()

col1.metric("Total Income", f"₹{total_income:,.0f}")
col2.metric("Total Expenses", f"₹{total_expenses:,.0f}")
col3.metric("Net", f"₹{net:,.0f}")

st.divider()

# --- account selector ---
st.subheader("Select Account")
selected_account = st.radio(
    "Choose an account to view detailed stats:",
    options=account_options,
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# Filter data based on selected account
if selected_account == "All Accounts":
    account_filtered = filtered
    account_balances = balances[
        (balances["date"] >= start_date) & (balances["date"] <= end_date)
    ].copy()
else:
    account_filtered = filtered[filtered["account"] == selected_account].copy()
    account_balances = balances[
        (balances["account"] == selected_account)
        & (balances["date"] >= start_date)
        & (balances["date"] <= end_date)
    ].copy()

# Show stats based on selection
if selected_account == "All Accounts":
    # --- overall charts ---
    col4, col5 = st.columns(2)

    with col4:
        st.subheader("Monthly Income vs Expenses")
        monthly = (
            account_filtered.assign(
                year_month=account_filtered["datetime"]
                .dt.to_period("M")
                .dt.to_timestamp()
            )
            .groupby(["year_month", "type"])["amount"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )
        fig1 = px.bar(
            monthly,
            x="year_month",
            y="amount",
            color="type",
            barmode="group",
        )
        st.plotly_chart(fig1, width="stretch")

    with col5:
        st.subheader("Spending by Category")
        expenses = account_filtered[account_filtered["type"] == "Expense"]
        cat = expenses.groupby("category")["amount"].sum().reset_index()
        fig2 = px.pie(cat, values="amount", names="category", hole=0.4)
        st.plotly_chart(fig2, width="stretch")

    st.divider()

    # --- all accounts balance view ---
    st.subheader("Account Balance Overview")

    if account_balances.empty:
        st.info("No account balance data available for the selected date range.")
    else:
        # Summary cards for each account
        account_summary = (
            account_balances.sort_values(["account", "date"])
            .groupby("account", as_index=False)
            .tail(1)
        )

        cols = st.columns(len(all_accounts))
        for i, acc in enumerate(all_accounts):
            acc_balance = account_summary[account_summary["account"] == acc][
                "running_balance"
            ].values
            if len(acc_balance) > 0:
                cols[i].metric(acc, f"₹{acc_balance[0]:,.0f}")

        # Line chart for all accounts
        fig3 = px.line(
            account_balances,
            x="date",
            y="running_balance",
            color="account",
            markers=True,
            title="Running Balance Over Time",
        )
        st.plotly_chart(fig3, width="stretch")

        # Allocation pie chart
        positive = account_summary[account_summary["running_balance"] > 0]
        if not positive.empty:
            fig4 = px.pie(
                positive,
                values="running_balance",
                names="account",
                hole=0.4,
                title="Asset Allocation",
            )
            st.plotly_chart(fig4, width="stretch")

else:
    # --- individual account stats ---
    acc_income = account_filtered[account_filtered["type"] == "Income"]["amount"].sum()
    acc_expenses = account_filtered[account_filtered["type"] == "Expense"][
        "amount"
    ].sum()
    acc_transfers_in = account_filtered[
        (account_filtered["type"] == "Transfer")
        & (
            account_filtered["account"].str.contains(
                "->" + selected_account, regex=True, na=False
            )
        )
    ]["amount"].sum()
    acc_transfers_out = account_filtered[
        (account_filtered["type"] == "Transfer")
        & (
            account_filtered["account"].str.contains(
                selected_account + "->", regex=True, na=False
            )
        )
    ]["amount"].sum()

    # Get current balance
    latest_balance = (
        account_balances.sort_values("date").tail(1)["running_balance"].values
    )
    current_balance = latest_balance[0] if len(latest_balance) > 0 else 0

    st.subheader(f"Stats for {selected_account}")

    acc_col1, acc_col2, acc_col3, acc_col4 = st.columns(4)
    acc_col1.metric("Income", f"₹{acc_income:,.0f}")
    acc_col2.metric("Expenses", f"₹{acc_expenses:,.0f}")
    acc_col3.metric("Transfers In", f"₹{acc_transfers_in:,.0f}")
    acc_col4.metric("Current Balance", f"₹{current_balance:,.0f}")

    st.divider()

    # Account-specific charts
    acc_col1, acc_col2 = st.columns(2)

    with acc_col1:
        st.subheader(f"Monthly Flow for {selected_account}")
        monthly_acc = (
            account_filtered.assign(
                year_month=account_filtered["datetime"]
                .dt.to_period("M")
                .dt.to_timestamp()
            )
            .groupby(["year_month", "type"])["amount"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )
        if not monthly_acc.empty:
            fig5 = px.bar(
                monthly_acc,
                x="year_month",
                y="amount",
                color="type",
                barmode="group",
            )
            st.plotly_chart(fig5, width="stretch")
        else:
            st.info("No transaction data available for this period.")

    with acc_col2:
        st.subheader(f"Category Breakdown for {selected_account}")
        expenses_acc = account_filtered[account_filtered["type"] == "Expense"]
        if not expenses_acc.empty:
            cat_acc = expenses_acc.groupby("category")["amount"].sum().reset_index()
            fig6 = px.pie(cat_acc, values="amount", names="category", hole=0.4)
            st.plotly_chart(fig6, width="stretch")
        else:
            st.info("No expense data available.")

    st.divider()

    # Account balance timeline
    st.subheader(f"Balance Timeline for {selected_account}")
    if not account_balances.empty:
        fig7 = px.line(
            account_balances,
            x="date",
            y="running_balance",
            markers=True,
            title=f"Running Balance - {selected_account}",
        )
        fig7.update_yaxes(title="Balance (₹)")
        st.plotly_chart(fig7, width="stretch")
    else:
        st.info("No balance data available for selected date range.")

    st.divider()

    # Transaction log for this account
    st.subheader(f"Transactions for {selected_account}")
    st.dataframe(
        account_filtered[
            ["datetime", "type", "amount", "category", "notes"]
        ].sort_values("datetime", ascending=False),
        width="stretch",
    )
