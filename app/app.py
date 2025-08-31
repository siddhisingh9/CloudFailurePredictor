from fastapi import FastAPI
from pydantic import BaseModel
import joblib

model = joblib.load("models/failure_model.pkl")

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
    return {"failure_probability": float(prob)}
