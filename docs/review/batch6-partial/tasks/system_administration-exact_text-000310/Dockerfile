FROM python:3.11-slim
RUN pip install --no-cache-dir pytest
RUN groupadd -r appgrp && useradd -r -g appgrp appuser
RUN mkdir -p /var/log/app && chown appuser:appgrp /var/log/app && chmod 775 /var/log/app
RUN touch -d '30 days ago' /var/log/app/old1.log /var/log/app/old2.log /var/log/app/old3.log
RUN touch -d '10 days ago' /var/log/app/med1.log /var/log/app/med2.log
RUN touch /var/log/app/new1.log /var/log/app/new2.log /var/log/app/new3.log
RUN touch /var/log/app/config.conf
RUN mkdir -p /output
WORKDIR /app
