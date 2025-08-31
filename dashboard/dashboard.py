import streamlit as st
import pandas as pd
import requests
import redis
import os
import json

# --- Config ---
API_URL = os.getenv("API_URL", "https://cloudfailurepredictorapp.onrender.com/predict")
REDIS_URL = os.getenv("REDIS_URL")
WINDOW_SIZE = 50

# --- Redis ---
r = redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("predictions")

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("☁️📊 Real-Time Cloud Failure Prediction Dashboard")

# --- Data selection ---
choice = st.radio("Choose data source:", ["Upload CSV", "Google Cluster Trace (demo)"])
if choice == "Upload CSV":
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.stop()
else:
    df = pd.read_csv("./data/processed_gct.csv")

FEATURES = ["cpu_request", "memory_request", "priority", "scheduling_class"]
df = df[FEATURES]

# --- Session state ---
if "streaming" not in st.session_state:
    st.session_state.streaming = False
if "stream_idx" not in st.session_state:
    st.session_state.stream_idx = 0
if "history" not in st.session_state:
    st.session_state.history = []

# --- Control buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Streaming"):
        st.session_state.streaming = True
with col2:
    if st.button("⏹️ Stop Streaming"):
        st.session_state.streaming = False

# --- Containers ---
metrics_container = st.empty()
chart_container = st.empty()
bar_container = st.empty()

# --- Streaming logic without rerun ---
if st.session_state.streaming and st.session_state.stream_idx < len(df):
    row = df.iloc[st.session_state.stream_idx]

    # Send row to API
    try:
        requests.post(API_URL, json=row.to_dict())
    except:
        pass

    # Check Redis for prediction
    message = pubsub.get_message(timeout=0.01)
    if message and message["type"] == "message":
        try:
            payload = json.loads(message["data"])
            data = payload.get("data", row.to_dict())
            prob = payload.get("failure_probability")
        except:
            data = row.to_dict()
            prob = None
    else:
        data = row.to_dict()
        prob = None

    # Update history
    if prob is not None:
        st.session_state.history.append(prob)

    # --- Metrics display ---
    with metrics_container:
        st.subheader("Latest Job Metrics")
        st.write(data)
        if prob is not None:
            if prob > 0.8:
                st.warning(f"⚠️ High failure risk: {prob:.2f}")
            elif prob < 0.2:
                st.success(f"✅ Low risk: {prob:.2f}")
            else:
                st.info(f"Failure probability: {prob:.2f}")

    # --- Line chart ---
    with chart_container:
        st.subheader("Historical Failure Probabilities")
        if st.session_state.history:
            chart_container.line_chart(st.session_state.history[-WINDOW_SIZE:])

    # --- Bar chart ---
    with bar_container:
        st.subheader("CPU & Memory Usage")
        bar_container.bar_chart({
            "CPU Request": [data["cpu_request"]],
            "Memory Request": [data["memory_request"]]
        })

    # Move to next row
    st.session_state.stream_idx += 1

# --- Auto-refresh every second ---
if st.session_state.streaming:
    st.experimental_set_query_params(_stream_tick=st.session_state.stream_idx)  # dummy
    st_autorefresh = st.experimental_rerun
