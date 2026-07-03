FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
COPY records/ /data/records/
RUN mkdir -p /output
COPY gen_answers.py /app/gen_answers.py
COPY test_manifest.py /tests/test_manifest.py
RUN python3 /app/gen_answers.py > /tests/answers.txt
WORKDIR /app