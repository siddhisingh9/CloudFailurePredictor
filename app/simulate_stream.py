import pandas as pd
import redis
import json
import time
import os

# Connect to Upstash Redis
redis_url = os.getenv("REDIS_URL")
r = redis.from_url(redis_url, decode_responses=True)

# Load CSV
df = pd.read_csv("./data/processed_gct.csv")
features = ["cpu_request", "memory_request", "priority", "scheduling_class"]
df = df[features]

# Publish each row
for idx, row in df.iterrows():
    event = row.to_dict()
    r.publish("raw_data", json.dumps(event))
    print(f"Published row {idx}: {event}")
    time.sleep(5)  # 1 row per second
