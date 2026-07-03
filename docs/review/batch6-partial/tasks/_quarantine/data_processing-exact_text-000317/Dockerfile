FROM python:3.11-slim
RUN pip install --no-cache-dir pytest flask pyyaml
RUN mkdir -p /data /output
RUN python3 -c "
import bz2
data = b'vendor_id|name|category|price\nV001|Acme Corp|widgets|10.00\nV002|Beta Ltd|gadgets|20.00\nV003||parts|5.00\nV002|Beta Dup|gadgets|20.00\n|NoId|widgets|1.00\nV004|Delta Inc|parts|15.00\nV005|Echo LLC|widgets|8.50\n'
with bz2.open('/data/vendors.bz2', 'wb') as f:
    f.write(data)
"
WORKDIR /app
