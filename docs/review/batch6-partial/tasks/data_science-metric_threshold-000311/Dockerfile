FROM python:3.11-slim
RUN pip install --no-cache-dir pytest pandas scikit-learn numpy
COPY transactions.csv /data/transactions.csv
COPY labels.csv /data/labels.csv
RUN mkdir -p /output
WORKDIR /app
