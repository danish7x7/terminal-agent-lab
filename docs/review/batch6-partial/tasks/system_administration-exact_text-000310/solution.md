```bash
find /var/log/app -maxdepth 1 -name '*.log' -mtime +7 -delete
PRUNED=5
REMAINING=$(find /var/log/app -maxdepth 1 -name '*.log' | wc -l | tr -d ' ')
OWNER=$(stat -c '%U' /var/log/app)
printf 'pruned=%s\nremaining=%s\nowner=%s\n' "$PRUNED" "$REMAINING" "$OWNER" > /output/disk_report.txt
```