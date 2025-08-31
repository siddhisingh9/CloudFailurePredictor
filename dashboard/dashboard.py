import streamlit as st
import pandas as pd
import redis
import json
import os
import requests
import time

# --- Config ---
API_URL = os.getenv("API_URL", "https://cloudfailurepredictorapp.onrender.com/predict")
REDIS_URL = os.getenv("REDIS_URL")  # set this in Render
WINDOW_SIZE = 50

# --- Redis connection ---
r = redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("predictions")

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("🌩️ Real-Time Cloud Failure Prediction Dashboard")

# UI Controls
mode = st.radio("Choose Mode:", ["📤 Upload CSV", "🧪 Demo Mode", "📡 Live Stream"])

uploaded_file = None
if mode == "📤 Upload CSV":
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

metrics_container = st.empty()
chart_container = st.empty()
bar_container = st.empty()

history = []

# --- Helper: publish prediction to Redis ---
def publish_prediction(data, prob):
    payload = {"data": data, "failure_probability": prob}
    r.publish("predictions", json.dumps(payload))

# --- DEMO Mode ---
if mode == "🧪 Demo Mode":
    st.info("Running Demo Mode: streaming predictions from a sample CSV.")
    demo_file = "./data/processed_gct.csv"

    df = pd.read_csv(demo_file)[["cpu_request", "memory_request", "priority", "scheduling_class"]]

    for idx, row in df.iterrows():
        data = row.to_dict()
        try:
            response = requests.post(API_URL, json=data)
            prob = response.json()["failure_probability"]
        except Exception as e:
            st.error(f"API request failed: {e}")
            break

        publish_prediction(data, prob)
        time.sleep(3)  # simulate live streaming

# --- CSV Upload Mode ---
elif mode == "📤 Upload CSV" and uploaded_file:
    st.success("Streaming your uploaded CSV to the predictor...")

    df = pd.read_csv(uploaded_file)[["cpu_request", "memory_request", "priority", "scheduling_class"]]

    for idx, row in df.iterrows():
        data = row.to_dict()
        try:
            response = requests.post(API_URL, json=data)
            prob = response.json()["failure_probability"]
        except Exception as e:
            st.error(f"API request failed: {e}")
            break

        publish_prediction(data, prob)
        time.sleep(3)

# --- Live Subscription Mode ---
elif mode == "📡 Live Stream":
    st.info("Listening to Redis Pub/Sub for predictions...")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            payload = json.loads(message["data"])
            data = payload["data"]
            prob = payload["failure_probability"]
        except Exception as e:
            st.error(f"Error parsing message: {e}")
            continue

        history.append(prob)

        # Two-column layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Latest Job Metrics")
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

        with bar_container:
            st.subheader("CPU & Memory Usage")
            st.bar_chart({
                "CPU Request": [data["cpu_request"]],
                "Memory Request": [data["memory_request"]]
            })
