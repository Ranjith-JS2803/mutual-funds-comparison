import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Mutual Fund NAV Comparison", layout="wide")

# ---------- Backend Helpers ----------
@st.cache_data
def get_all_funds():
    url = "https://api.mfapi.in/mf"
    res = requests.get(url)
    return res.json()

@st.cache_data
def get_fund_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    df = pd.DataFrame(data['data'])
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    df['scheme_name'] = data['meta']['scheme_name']
    return df[['date', 'nav', 'scheme_name']]

def filter_by_date(df, period):
    today = df['date'].max()
    date_threshold = {
        "1 Month": today - timedelta(days=30),
        "6 Months": today - timedelta(days=180),
        "1 Year": today - timedelta(days=365),
        "5 Years": today - timedelta(days=1825),
        "Max": df['date'].min()
    }[period]
    return df[df['date'] >= date_threshold]

# ---------- UI ----------
st.title("📊 Mutual Funds Comparison Tool")

funds = get_all_funds()
fund_options = {f['schemeName']: f['schemeCode'] for f in funds}
all_scheme_names = list(fund_options.keys())

# Try to use a specific fund as default, else use first available
default_fund = "UTI Nifty 50 Index Fund - Direct Plan - Growth Option"
default = [default_fund] if default_fund in all_scheme_names else [all_scheme_names[0]]

selected_funds = st.multiselect(
    "🔍 Select mutual funds to compare:",
    options=all_scheme_names,
    default=default,
    help="Start typing to search. You can select multiple schemes."
)

selected_period = st.selectbox(
    "📅 Select time range:",
    options=["1 Month", "6 Months", "1 Year", "5 Years", "Max"],
    index=2
)

# ---------- Plot Section ----------
if selected_funds:
    st.subheader("📈 NAV Comparison")
    plt.figure(figsize=(12, 6))

    for name in selected_funds:
        scheme_code = fund_options[name]
        df = get_fund_nav(scheme_code)
        if df is not None:
            df_filtered = filter_by_date(df, selected_period)
            plt.plot(df_filtered['date'], df_filtered['nav'], label=name)

    plt.xlabel("Date")
    plt.ylabel("NAV")
    plt.title(f"NAV Comparison - {selected_period}")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt.gcf())

    # ---------- INR Returns Plot ----------
    st.subheader("💰 Investment Value Over Time")

    initial_investment = st.number_input("Enter investment amount (₹):", value=10000, step=1000)

    if initial_investment > 0:
        plt.figure(figsize=(12, 6))

        for name in selected_funds:
            scheme_code = fund_options[name]
            df = get_fund_nav(scheme_code)
            if df is not None:
                df_filtered = filter_by_date(df, selected_period).sort_values('date')
                if not df_filtered.empty:
                    start_nav = df_filtered['nav'].iloc[0]
                    df_filtered['investment_value'] = initial_investment * (df_filtered['nav'] / start_nav)
                    plt.plot(df_filtered['date'], df_filtered['investment_value'], label=name)

        plt.xlabel("Date")
        plt.ylabel("Value (₹)")
        plt.title(f"Investment Value of ₹{initial_investment:,} Over Time - {selected_period}")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt.gcf())
