FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
COPY sales.csv /data/sales.csv
RUN mkdir -p /output
WORKDIR /app
