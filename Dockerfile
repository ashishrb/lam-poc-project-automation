# Simple POC Dockerfile for Enhanced Autonomous PM
# CPU-only, no GPU/CUDA; Ollama is optional and external

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000 \
    DEBUG=False

WORKDIR /app

# System deps (build tools for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install -U pip setuptools wheel && \
    pip install -r requirements.txt

COPY . /app

EXPOSE 5000

CMD ["python", "flask_app.py"]

