FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends patch && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest
RUN mkdir -p /data /api/responses /src /output /solution
COPY packages.txt /data/packages.txt
COPY mathutils.json /api/responses/mathutils.json
COPY strhelper.json /api/responses/strhelper.json
COPY netio.json /api/responses/netio.json
COPY mathutils.c /src/mathutils.c
COPY strhelper.c /src/strhelper.c
COPY netio.c /src/netio.c
WORKDIR /app
