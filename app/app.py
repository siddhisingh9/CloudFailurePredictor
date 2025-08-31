from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import redis
import os
import json

# --- Load model ---
model = joblib.load("./models/failure_model.pkl")

# --- Redis connection ---
REDIS_URL = os.getenv("REDIS_URL")  # set in Render env vars
r = redis.from_url(REDIS_URL, decode_responses=True)

class Metrics(BaseModel):
    cpu_request: float
    memory_request: float
    priority: int
    scheduling_class: int

app = FastAPI(title="Cloud Failure Prediction API")

@app.post("/predict")
def predict(metrics: Metrics):
    features = [[
        metrics.cpu_request,
        metrics.memory_request,
        metrics.priority,
        metrics.scheduling_class
    ]]
    prob = model.predict_proba(features)[0][1]
    prob = float(prob)

    # --- publish to Redis ---
    payload = {
        "data": metrics.dict(),
        "failure_probability": prob
    }
    r.publish("predictions", json.dumps(payload))

    # --- still return response for API clients ---
    return {"failure_probability": prob}
