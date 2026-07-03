FROM python:3.11-slim
RUN pip install --no-cache-dir numpy pytest
COPY signal.csv /data/signal.csv
RUN mkdir -p /output
WORKDIR /app
