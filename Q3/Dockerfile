# Validator image for the Kubernetes Indexed Job (Question 3).

FROM python:3.11-slim

WORKDIR /data
COPY shard_*.csv .

WORKDIR /app
COPY validate.py .

ENTRYPOINT ["python", "validate.py"]
