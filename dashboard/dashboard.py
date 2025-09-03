import streamlit as st
import pandas as pd
import requests
import redis
import os
import json

# --- Config ---
API_URL = os.getenv("API_URL", "https://cloudfailurepredictorapp.onrender.com/predict")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WINDOW_SIZE = 50
REDIS_LIST = "demo:rows"

# --- Redis ---
r = redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("predictions")

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("☁️📊 Real-Time Cloud Failure Prediction Dashboard")

# --- Step 1: Upload or Demo ---
choice = st.radio("Choose data source:", ["Upload CSV", "Google Cluster Trace (demo)"])

if choice == "Upload CSV":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        FEATURES = ["cpu_request", "memory_request", "priority", "scheduling_class"]
        df = df[FEATURES]
    else:
        st.stop()
else:
    # Demo mode uses Redis list, no local file
    df = None  

# --- Step 2: Streaming state ---
if "streaming" not in st.session_state:
    st.session_state.streaming = False
if "history" not in st.session_state:
    st.session_state.history = []
if "current_data" not in st.session_state:
    st.session_state.current_data = None
if "current_prob" not in st.session_state:
    st.session_state.current_prob = None
if "row_index" not in st.session_state:
    st.session_state.row_index = 0

def start_streaming():
    st.session_state.streaming = True

def stop_streaming():
    st.session_state.streaming = False
    st.session_state.row_index = 0

col1, col2 = st.columns(2)
with col1:
    st.button("▶️ Start Streaming", on_click=start_streaming, disabled=st.session_state.streaming)
with col2:
    st.button("⏹️ Stop Streaming", on_click=stop_streaming, disabled=not st.session_state.streaming)

# --- Fragment for updates ---
@st.fragment(run_every="3s" if st.session_state.streaming else None)
def update_stream():
    if not st.session_state.streaming:
        return

    # --- Pick row depending on mode ---
    if choice == "Upload CSV":
        # Cycle through uploaded file
        idx = st.session_state.row_index
        if idx >= len(df):
            st.session_state.row_index = 0
            idx = 0
        row = df.iloc[idx]
        st.session_state.row_index += 1
    else:
        # Cycle through Redis list (like pubsub replay)
        row_data = r.lindex(REDIS_LIST, st.session_state.row_index)
        if row_data is None:
            # restart if reached end
            st.session_state.row_index = 0
            row_data = r.lindex(REDIS_LIST, 0)
        row = json.loads(row_data)
        st.session_state.row_index += 1

    # --- Send row to API ---
    try:
        requests.post(API_URL, json=row if isinstance(row, dict) else row.to_dict())
    except Exception as e:
        st.error(f"API request failed: {e}")
        return

    # --- Listen for prediction ---
    message = pubsub.get_message(timeout=5)
    if not message or message["type"] != "message":
        return

    try:
        payload = json.loads(message["data"])
        data = payload["data"]
        prob = payload["failure_probability"]
    except Exception as e:
        st.error(f"Error parsing message: {e}")
        return

    # --- Update state ---
    st.session_state.current_data = data
    st.session_state.current_prob = prob
    st.session_state.history.append(prob)
    if len(st.session_state.history) > WINDOW_SIZE:
        st.session_state.history.pop(0)

    # --- UI Updates ---
    st.subheader("Latest Job Metrics")
    st.write(data)
    if prob > 0.8:
        st.warning(f"⚠️ High failure risk: {prob:.2f}")
    elif prob < 0.2:
        st.success(f"✅ Low risk: {prob:.2f}")
    else:
        st.info(f"Failure probability: {prob:.2f}")

    st.subheader("Historical Failure Probabilities")
    st.line_chart(st.session_state.history)

    st.subheader("CPU & Memory Usage")
    st.bar_chart({
        "CPU Request": [data["cpu_request"]],
        "Memory Request": [data["memory_request"]]
    })

update_stream()
