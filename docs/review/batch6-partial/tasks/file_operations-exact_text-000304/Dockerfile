FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
RUN mkdir -p /srv/logs /output
COPY access.log /srv/logs/access.log
COPY app.log /srv/logs/app.log
COPY error.log /srv/logs/error.log
COPY debug.txt /srv/logs/debug.txt
WORKDIR /app
