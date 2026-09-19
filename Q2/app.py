"""
app.py

FastAPI service for the spam-detection API, with a Redis cache in front
of the model so repeated identical requests skip re-computation.

Endpoints:
    POST /predict   {"text": "..."}  ->  {"label": "spam"} or {"label": "ham"}
    GET  /healthz    ->  200 once the model is loaded

Run locally:
    uvicorn app:app --reload
"""

import hashlib
import os

import joblib
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODEL_PATH = "model.joblib"

# REDIS_HOST defaults to "cache", which is the service name Docker Compose
# gives the Redis container (see docker-compose.yml). Falls back to
# "localhost" for running the API outside Docker.
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 3600))

app = FastAPI(title="Spam Detection API")

# Load the trained pipeline once, at import/startup time.
# If this fails, we keep `model` as None so /healthz can report not-ready
# instead of crashing the whole process on import.
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:  # noqa: BLE001
    model = None
    _load_error = str(e)
else:
    _load_error = None

# Single shared Redis client. redis-py connections are lazy, so this
# doesn't fail even if Redis isn't reachable yet at import time.
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def _cache_key(text: str) -> str:
    # Hash the text so arbitrary/long input never produces a malformed
    # or oversized Redis key.
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"prediction:{digest}"


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str


@app.get("/healthz")
def healthz():
    if model is None:
        raise HTTPException(status_code=503, detail=f"model not loaded: {_load_error}")
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="model not loaded")

    key = _cache_key(req.text)

    # Cache HIT: return the stored label without touching the model.
    try:
        cached_label = cache.get(key)
    except redis.exceptions.RedisError:
        cached_label = None  # treat a Redis outage as a cache miss, not a failure

    if cached_label is not None:
        return PredictResponse(label=cached_label)

    # Cache MISS: compute, then store for next time.
    label = model.predict([req.text])[0]
    try:
        cache.set(key, label, ex=CACHE_TTL_SECONDS)
    except redis.exceptions.RedisError:
        pass  # prediction still succeeds even if caching the result fails

    return PredictResponse(label=label)
