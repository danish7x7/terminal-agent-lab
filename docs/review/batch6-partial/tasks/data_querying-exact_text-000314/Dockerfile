FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
RUN mkdir -p /data /output
COPY system_a.csv /data/system_a.csv
COPY system_b.csv /data/system_b.csv
WORKDIR /app
