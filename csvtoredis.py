import pandas as pd
import redis
import os
import json

# --- Config ---
r = redis.from_url('redis://default:xV9mjJOgsXwWuEHpFp6hliiSsPbdVzNN@redis-13193.crce179.ap-south-1-1.ec2.redns.redis-cloud.com:13193', decode_responses=True)

# Load CSV
df = pd.read_csv("data/processed_gct.csv")

# Keep only needed features
FEATURES = ["cpu_request", "memory_request", "priority", "scheduling_class"]
df = df[FEATURES]

# Push rows into Redis list
for _, row in df.iterrows():
    r.rpush("demo:rows", json.dumps(row.to_dict()))

print(f"✅ Loaded {len(df)} rows into Redis list 'demo:rows'")
