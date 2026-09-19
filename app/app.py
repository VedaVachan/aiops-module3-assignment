import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODEL_PATH = "model.joblib"

app = FastAPI(title="Spam Detection API")

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:  # noqa: BLE001
    model = None
    _load_error = str(e)
else:
    _load_error = None


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
    label = model.predict([req.text])[0]
    return PredictResponse(label=label)
