FROM python:3.11-slim
RUN apt-get update && apt-get install -y golang-go curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest requests
RUN mkdir -p /app/simserver /output
WORKDIR /app
