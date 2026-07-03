FROM python:3.11-slim
RUN pip install --no-cache-dir pytest cryptography
RUN mkdir -p /challenge /output
COPY gen_challenge.py /gen_challenge.py
RUN python3 /gen_challenge.py
WORKDIR /app
