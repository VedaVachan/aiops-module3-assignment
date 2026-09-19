# Multi-stage build (same approach as Question 1's Dockerfile.multistage),
# used here as the "api" service's image for Docker Compose.

# ---- Stage 1: builder ----
FROM python:3.11 AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---- Stage 2: final ----
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY app.py .
COPY model.joblib .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
