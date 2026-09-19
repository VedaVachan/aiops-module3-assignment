"""
test_cache_speedup.py

Demonstrates that a repeated, identical /predict request is served from
the Redis cache (fast) instead of recomputed by the model (slower).

Run this AFTER `docker compose up` is running, from the host machine:
    python test_cache_speedup.py
"""

import time
import requests

URL = "http://localhost:8000/predict"
PAYLOAD = {"text": "WIN a FREE iPhone now! Click here"}


def timed_request(label: str):
    t0 = time.perf_counter()
    resp = requests.post(URL, json=PAYLOAD)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    print(f"{label:<20} status={resp.status_code} body={resp.json()} time={elapsed_ms:.2f} ms")
    return elapsed_ms


if __name__ == "__main__":
    miss_time = timed_request("MISS (1st call):")
    hit_time_1 = timed_request("HIT  (2nd call):")
    hit_time_2 = timed_request("HIT  (3rd call):")

    print()
    print(f"Cache miss:      {miss_time:.2f} ms")
    print(f"Cache hit (avg): {(hit_time_1 + hit_time_2) / 2:.2f} ms")
    print(f"Speedup:         {miss_time / ((hit_time_1 + hit_time_2) / 2):.1f}x faster on cache hit")
