import streamlit as st
import pandas as pd
import requests
import time

# --- Config ---
API_URL = "https://cloudfailurepredictorapp.onrender.com/predict"
CSV_FILE = "/app/data/processed_gct.csv"
FEATURES = ["cpu_request", "memory_request", "priority", "scheduling_class"]
DELAY = 1  # seconds between rows
WINDOW_SIZE = 50  # last N predictions to display

# --- Load CSV ---
df = pd.read_csv(CSV_FILE)
df = df[FEATURES]

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("🌩️ Real-Time Cloud Failure Prediction Dashboard")

metrics_container = st.empty()
chart_container = st.empty()
bar_container = st.empty()

history = []

# --- Simulate streaming ---
for idx, row in df.iterrows():
    data = row.to_dict()
    
    try:
        response = requests.post(API_URL, json=data)
        prob = response.json()["failure_probability"]
    except Exception as e:
        prob = None
        st.error(f"API request failed: {e}")

    if prob is not None:
        history.append(prob)

    # Two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Row {idx} Metrics")
        st.write(data)
        if prob > 0.8:
            st.warning(f"⚠️ High failure risk: {prob:.2f}")
        elif prob < 0.2:
            st.success(f"✅ Low risk: {prob:.2f}")
        else:
            st.info(f"Failure probability: {prob:.2f}")
    
    with col2:
        st.subheader("Historical Failure Probabilities")
        st.line_chart(history[-WINDOW_SIZE:])

    # CPU & Memory bar chart
    with bar_container:
        st.subheader("CPU & Memory Usage")
        st.bar_chart({
            "CPU Request": [data["cpu_request"]],
            "Memory Request": [data["memory_request"]]
        })

    time.sleep(DELAY)
