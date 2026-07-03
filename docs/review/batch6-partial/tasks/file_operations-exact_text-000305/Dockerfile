FROM python:3.11-slim
RUN pip install --no-cache-dir pytest requests
RUN mkdir -p /data/backup /data/current /output

COPY backup_alpha.txt /data/backup/alpha.txt
COPY backup_beta.txt /data/backup/beta.txt
COPY backup_gamma.txt /data/backup/gamma.txt

COPY current_file1.txt /data/current/file1.txt
COPY current_doc_beta.txt /data/current/doc_beta.txt
COPY current_new_delta.txt /data/current/new_delta.txt
COPY current_gamma_copy.txt /data/current/gamma_copy.txt
COPY current_file2.txt /data/current/file2.txt

COPY manifest.json /data/manifest.json

WORKDIR /app
