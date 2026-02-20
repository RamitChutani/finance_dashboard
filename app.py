import streamlit as st
import plotly.express as px
from src.helpers import load_data

# setting page config is the first streamlit call in the script
# layout wide uses full browser width
st.set_page_config(page_title="Finance Dashboard", layout="wide")

df = load_data()

# --- sidebar --- 
# this is added first because filters are defined here which will define the filtered df that is used in dashboard

st.sidebar.header("Filters")

months = sorted(df["month"].unique())
selected_months = st.sidebar.multiselect("Month", months, default=months)
selected_types = st.sidebar.multiselect("Type", ["Income", "Expense", "Transfer"], default=["Income", "Expense"])

filtered = df[
    df["month"].isin(selected_months) &
    df["type"].isin(selected_types) &
    df["is_opening_balance"] == False
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
    monthly = filtered.groupby(["month", "type"])["amount"].sum().reset_index()
    # barmode="group" puts bars side by side rather than stacked
    fig1 = px.bar(monthly, x="month", y="amount", color="type", barmode="group")
    # use_container_width=True makes the chart fill whatever column it's in
    st.plotly_chart(fig1, use_container_width=True)

with col5:
    st.subheader("Spending by Category")
    expenses = filtered[filtered["type"] == "Expense"]
    cat = expenses.groupby("category")["amount"].sum().reset_index()
    # hole=0.4 makes it a donut chart — easier to read with many categories
    fig2 = px.pie(cat, values="amount", names="category", hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

# --- log of transactions ---
# st.dataframe is interactive (sortable, scrollable).
# st.table is static — use dataframe for anything the user might want to explore.
st.subheader("Transaction Log")
st.dataframe(
    filtered[["datetime", "type", "amount", "category", "account", "notes"]]
    .sort_values("datetime", ascending=False),
    use_container_width=True
)