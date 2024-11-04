import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import json
import os

# Add this at the beginning of the file
from main import check_authentication
check_authentication()

st.title("API Usage Analytics")

# File to store usage data
USAGE_FILE = "api_usage_data.json"

def load_usage_data():
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    return []


def get_usage_data(start_date, end_date):
    data = load_usage_data()
    filtered_data = [
        entry for entry in data 
        if start_date <= datetime.fromisoformat(entry['timestamp']) <= end_date
    ]
    return filtered_data

def process_usage_data(data):
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    return df

def display_usage_stats(df):
    if df.empty:
        st.warning("No usage data available for the selected period.")
        return

    total_requests = len(df)
    total_tokens = df['tokens'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Requests", f"{total_requests:,}")
    col2.metric("Total Tokens", f"{total_tokens:,}")

    st.subheader("Usage Over Time")
    fig = px.line(df, y='tokens')
    st.plotly_chart(fig)

    st.subheader("Usage by Request Type")
    type_counts = df['type'].value_counts()
    fig = px.pie(values=type_counts.values, names=type_counts.index)
    st.plotly_chart(fig)

# Time period selection
time_periods = {
    "Last 1 hour": timedelta(hours=1),
    "Last 12 hours": timedelta(hours=12),
    "Last 24 hours": timedelta(hours=24),
    "Last 7 days": timedelta(days=7),
    "Last 30 days": timedelta(days=30)
}

selected_period = st.selectbox("Select time period", list(time_periods.keys()))

end_date = datetime.now()
start_date = end_date - time_periods[selected_period]

usage_data = get_usage_data(start_date, end_date)
if usage_data:
    df = process_usage_data(usage_data)
    display_usage_stats(df)

st.sidebar.success("You are currently on the Usage Analytics page.")

# Example of how to add usage data (you would call this function after each API call in your application)
# add_usage_entry(100, "completion")