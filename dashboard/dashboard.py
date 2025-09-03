import streamlit as st
import requests
import redis
import os
import json

API_URL = os.getenv("API_URL", "https://cloudfailurepredictorapp.onrender.com/predict")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WINDOW_SIZE = 50
REDIS_LIST = "demo:rows"

r = redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("predictions")

st.set_page_config(page_title="Cloud Failure Dashboard", layout="wide")
st.title("☁️📊 Real-Time Cloud Failure Prediction Dashboard")

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

col1, col2 = st.columns(2)
with col1:
    st.button("▶️ Start Streaming", on_click=lambda: st.session_state.update({'streaming': True}),
              disabled=st.session_state.streaming)
with col2:
    st.button("⏹️ Stop Streaming", on_click=lambda: st.session_state.update({'streaming': False}),
              disabled=not st.session_state.streaming)

def get_row_from_redis(index):
    list_length = r.llen(REDIS_LIST)
    if list_length == 0:
        return None
    index = index % list_length
    row_data = r.lindex(REDIS_LIST, index)
    if row_data:
        return json.loads(row_data)
    return None

@st.fragment(run_every="3s" if st.session_state.streaming else None)
def update_stream():
    if not st.session_state.streaming:
        return
    row = get_row_from_redis(st.session_state.row_index)
    if row is None:
        st.warning("No rows found in Redis list.")
        return
    try:
        requests.post(API_URL, json=row)
    except Exception as e:
        st.error(f"API request failed: {e}")
        return
    
    st.session_state.row_index += 1
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
    
    st.session_state.current_data = data
    st.session_state.current_prob = prob
    st.session_state.history.append(prob)

    if len(st.session_state.history) > WINDOW_SIZE:
        st.session_state.history.pop(0)

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
