FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libblas-dev \
    liblapack-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir sagemaker-training

WORKDIR /opt/ml/code

COPY src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./

ENV SAGEMAKER_PROGRAM=train.py
