import redis, os, json

r = redis.from_url('redis://default:xV9mjJOgsXwWuEHpFp6hliiSsPbdVzNN@redis-13193.crce179.ap-south-1-1.ec2.redns.redis-cloud.com:13193', decode_responses=True)

print("Total rows:", r.llen("demo:rows"))
print("First row:", json.loads(r.lindex("demo:rows", 0)))
