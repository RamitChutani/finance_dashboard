import streamlit as st
import plotly as px
from src.helpers import load_data

# setting page config is the first streamlit call in the script
# layout wide uses full browser width
st.set_page_config(page_title="Finance Dashboard", layout="wide")

df = load_data()

