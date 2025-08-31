import streamlit as st
import pandas as pd
import requests
import redis
import os
import json
import time

# --- Config ---
API_URL = os.getenv("API_URL", "https://cloudfailurepredictorapp.onrender.com/predict")
REDIS_URL = os.getenv("REDIS_URL")  # set in Render
WINDOW_SIZE = 50

# --- Redis ---
r = redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("predictions")

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("🌩️ Real-Time Cloud Failure Prediction Dashboard")

# --- Step 1: Upload or Demo ---
choice = st.radio("Choose data source:", ["Upload CSV", "Google Cluster Trace (demo)"])

if choice == "Upload CSV":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.stop()
else:
    # Demo file
    df = pd.read_csv("./data/processed_gct.csv")

# Only keep needed features
FEATURES = ["cpu_request", "memory_request", "priority", "scheduling_class"]
df = df[FEATURES]

# --- Step 2: Streaming controls ---
if "streaming" not in st.session_state:
    st.session_state.streaming = False

def start_streaming():
    st.session_state.streaming = True

def stop_streaming():
    st.session_state.streaming = False

col1, col2 = st.columns(2)
with col1:
    st.button("▶️ Start Streaming", on_click=start_streaming)
with col2:
    st.button("⏹️ Stop Streaming", on_click=stop_streaming)

# --- Streaming Loop ---
if st.session_state.streaming:
    history = st.session_state.get("history", [])
    metrics_container = st.empty()
    chart_container = st.empty()
    bar_container = st.empty()

    for idx, row in df.iterrows():
        if not st.session_state.streaming:
            break  # Stop when user clicks stop

        # Send row to API (publishes to Redis too)
        try:
            requests.post(API_URL, json=row.to_dict())
        except Exception as e:
            st.error(f"API request failed: {e}")
            time.sleep(5)
            continue

        # Wait for pub/sub update
        message = pubsub.get_message(timeout=5)
        if not message or message["type"] != "message":
            continue

        try:
            payload = json.loads(message["data"])
            data = payload["data"]
            prob = payload["failure_probability"]
        except Exception as e:
            st.error(f"Error parsing message: {e}")
            continue

        # Update history
        history.append(prob)
        st.session_state.history = history

        # --- UI updates ---
        with metrics_container:
            st.subheader("Latest Job Metrics")
            st.write(data)
            if prob > 0.8:
                st.warning(f"⚠️ High failure risk: {prob:.2f}")
            elif prob < 0.2:
                st.success(f"✅ Low risk: {prob:.2f}")
            else:
                st.info(f"Failure probability: {prob:.2f}")

        with chart_container:
            st.subheader("Historical Failure Probabilities")
            st.line_chart(history[-WINDOW_SIZE:])

        with bar_container:
            st.subheader("CPU & Memory Usage")
            st.bar_chart({
                "CPU Request": [data["cpu_request"]],
                "Memory Request": [data["memory_request"]]
            })

        time.sleep(5)
