FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends tshark curl scapy && apt-get clean
RUN pip install --no-cache-dir pytest requests scapy
COPY auth_traffic.pcap /data/auth_traffic.pcap
COPY wordlist.txt /data/wordlist.txt
COPY auth.log /data/auth.log
COPY configs/ /data/configs/
COPY auth_server.py /app/auth_server.py
RUN mkdir -p /output
WORKDIR /app
