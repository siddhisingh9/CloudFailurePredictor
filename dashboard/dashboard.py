import streamlit as st
import redis
import json
import os

# --- Config ---
REDIS_URL = os.getenv("REDIS_URL")  # set this in Render env vars
WINDOW_SIZE = 50  # last N predictions to display

# --- Redis connection ---
r = redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("predictions")

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("🌩️ Real-Time Cloud Failure Prediction Dashboard")

metrics_container = st.empty()
chart_container = st.empty()
bar_container = st.empty()

history = []

# --- Listen for predictions ---
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
