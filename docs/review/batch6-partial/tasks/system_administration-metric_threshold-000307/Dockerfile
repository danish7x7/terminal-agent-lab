FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron bash findutils coreutils grep sed gawk \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest
RUN mkdir -p /srv/src/logclean
COPY logclean.sh.src /srv/src/logclean/logclean.sh.src
RUN mkdir -p /var/log/app /var/log/logclean /var/spool/logclean
WORKDIR /root
