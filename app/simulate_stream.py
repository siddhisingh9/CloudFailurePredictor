import pandas as pd
import requests
import time

df = pd.read_csv("data/processed_gct.csv")

features = ["cpu_request", "memory_request", "priority", "scheduling_class"]
df = df[features]

url = "https://cloudfailurepredictorapp.onrender.com/predict"

for idx, row in df.iterrows():
    data = row.to_dict()
    response = requests.post(url, json=data)
    result = response.json()
    print(f"Row {idx}: failure probability = {result['failure_probability']:.2f}")
    time.sleep(1)
