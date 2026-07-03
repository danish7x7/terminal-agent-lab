FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends cron systemd passwd procps && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest
RUN mkdir -p /output
WORKDIR /app
