import streamlit as st
from time import strftime, localtime
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import json
from streamlit_date_picker import date_range_picker, date_picker, PickerType
from SqliteClient import SqliteClient


sqlite_host=st.secrets["sqlite_host"]
sqlite_port=st.secrets["sqlite_port"]
sqlite_key=st.secrets["sqlite_key"]
sqlitecloud_connection_string=f"sqlitecloud://{sqlite_host}:{sqlite_port}/sb-docs?apikey={sqlite_key}"
# Add this at the beginning of the file
from main import check_authentication

check_authentication()

st.title("API Usage Analytics")

# File to store usage data
USAGE_FILE = "api_usage_data.json"

def load_usage_data():
    sqlient = SqliteClient ("sb-docs")
    data = sqlient.get_data("api_usage_data")
    if data:
        json_data = json.dumps(data).replace("request_", "")
        return json.loads(json_data)

def get_usage_data(start_date, end_date):
    data = load_usage_data()
    filtered_data = []
    if data:
        for entry in data:
            entry_date = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            if entry_date >= start_date and entry_date <= end_date:
                filtered_data.append(entry)
    
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


st.subheader('Date Range Picker')
default_start, default_end = datetime.now() - timedelta(minutes=30), datetime.now()
refresh_value = timedelta(minutes=30)
date_range_string = date_range_picker(picker_type=PickerType.time,
                                      start=default_start, end=default_end,
                                      key='time_range_picker',
                                      refresh_button={'is_show': True, 'button_name': 'Refresh Last 30 Minutes',
                                                      'refresh_value': refresh_value})
if date_range_string:
    start, end = date_range_string
    start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
    usage_data = get_usage_data(start, end)
    if usage_data:
        df = process_usage_data(usage_data)
        display_usage_stats(df)

    st.sidebar.success("You are currently on the Usage Analytics page.")


# st.title("Date and Time Range Selector")
# start_date = st.date_input("Select Start Date", value=datetime.now().date())
# end_date = st.date_input("Select End Date", value=datetime.now().date() + timedelta(days=1))
# start_time = st.time_input("Select Start Time", value=time(8, 0))  # Default to 8:00 AM
# end_time = st.time_input("Select End Time", value=time(17, 0))    # Default to 5:00 PM
# start_datetime = datetime.combine(start_date, start_time)
# end_datetime = datetime.combine(end_date, end_time)




# Example of how to add usage data (you would call this function after each API call in your application)
# add_usage_entry(100, "completion")
