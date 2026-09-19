# AIOps Module 3 Assignment — Spam Detection API

This repository contains my implementation for AIOps Module 3: packaging a spam-detection API with Docker (naive vs. multi-stage builds), adding Redis caching with Docker Compose, and deploying it on Kubernetes (an Indexed Job for batch validation, and a Deployment for self-healing / rolling updates).

## Project Structure

```
AIOPS_Module3/
├── app/                # Shared: dataset generation, training, base FastAPI app
│   ├── generate_data.py
│   ├── train.py
│   ├── app.py
│   ├── model.joblib
│   └── requirements.txt
├── Q1/                 # Docker: single-stage vs. multi-stage builds
│   ├── Dockerfile.naive
│   └── Dockerfile.multistage
├── Q2/                 # Redis caching + Docker Compose
│   ├── app.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── test_cache_speedup.py
├── Q3/                 # Kubernetes Indexed Job: parallel shard validation
│   ├── generate_shards.py
│   ├── validate.py
│   ├── Dockerfile
│   ├── indexed-job.yaml
│   └── collect_results.py
└── Q4/                 # Kubernetes Deployment: self-healing + rolling updates
    ├── app.py
    ├── Dockerfile
    ├── deployment.yaml
    └── service.yaml
```

## Prerequisites

- Docker
- Python 3.11+
- minikube (multi-node) + kubectl, for Questions 3 and 4

---

## Setup (once)

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 generate_data.py   # creates spam_dataset.csv
python3 train.py           # creates model.joblib
```

This trains the TF-IDF + Naive Bayes pipeline used by every question below.

---

## Question 1 — Naive vs. Multi-Stage Docker Build

```bash
cd Q1
cp ../app/app.py ../app/requirements.txt ../app/model.joblib .

# Naive build
docker build -f Dockerfile.naive -t spam-api:naive .
docker images | grep spam-api

# Multi-stage build
docker build -f Dockerfile.multistage -t spam-api:multistage .
docker images | grep spam-api
```

Run and test either image:
```bash
docker run -d --rm -p 8000:8000 --name spam-api spam-api:multistage
curl http://localhost:8000/healthz; echo
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"text": "WIN a FREE iPhone now!"}'; echo
docker stop spam-api
```

---

## Question 2 — Redis Caching with Docker Compose

```bash
cd Q2
cp ../app/model.joblib .

docker compose up -d --build
curl http://localhost:8000/healthz; echo

python3 test_cache_speedup.py         # prints cache miss vs. hit timing
docker compose exec cache redis-cli keys '*'   # confirm keys stored in Redis

docker compose down
```

---

## Question 3 — Kubernetes Indexed Job

```bash
cd Q3
python3 generate_shards.py            # creates shard_0.csv ... shard_7.csv

docker build -t shard-validator:latest .
minikube image load shard-validator:latest

kubectl apply -f indexed-job.yaml
kubectl get pods -o wide -w           # watch parallelism reach 4 concurrent pods

kubectl get job shard-validator       # confirm 8/8 completions
pip install kubernetes
python3 collect_results.py            # collects invalid-row counts via the K8s API

kubectl delete -f indexed-job.yaml    # cleanup
```

---

## Question 4 — Kubernetes Deployment: Self-Healing & Rolling Update

```bash
cd Q4
cp ../app/model.joblib .

# Build and deploy v1
docker build -t spam-api:v1 .
minikube image load spam-api:v1
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl get pods -l app=spam-api

# Self-healing test
kubectl delete pod <pod-name>
kubectl get pods -l app=spam-api -w

# Rolling update: bump VERSION in app.py to "v2", then
docker build -t spam-api:v2 .
minikube image load spam-api:v2
kubectl set image deployment/spam-api spam-api=spam-api:v2
kubectl rollout status deployment/spam-api
kubectl rollout history deployment/spam-api

# Verify
kubectl get svc spam-api-service      # note the NodePort
curl http://$(minikube ip):<nodePort>/healthz; echo
```

---

## Notes

- All images are CPU-only; no GPU is required anywhere in this assignment.
- `model.joblib` is trained once in `app/` and copied into each question's folder as needed, so every question runs against the same trained pipeline.
- Evidence (screenshots, terminal logs) referenced in the write-up is in `Q4/evidence/`.
