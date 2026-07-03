FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
RUN mkdir -p /workspace/messy /workspace/clean /workspace/reference
COPY gen_fixture.py /gen_fixture.py
RUN python3 /gen_fixture.py
WORKDIR /workspace
