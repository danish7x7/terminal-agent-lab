```bash
# Step 1: Build and install logclean from source
cat > /usr/local/bin/logclean <<'SCRIPT'
#!/bin/bash
set -euo pipefail

DIR="${1:-}"
if [[ -z "$DIR" ]]; then
    echo "Usage: logclean <directory>" >&2
    exit 1
fi

LOGFILE="/var/log/logclean/run.log"
KEEP_DAYS="${LOGCLEAN_KEEP_DAYS:-7}"

# Find and delete old .log files
OLD_FILES=$(find "$DIR" -maxdepth 1 -name '*.log' -mtime +"$((KEEP_DAYS - 1))" 2>/dev/null || true)
COUNT=0
if [[ -n "$OLD_FILES" ]]; then
    while IFS= read -r f; do
        rm -f "$f"
        COUNT=$((COUNT + 1))
    done <<< "$OLD_FILES"
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "$TIMESTAMP cleaned $COUNT files from $DIR" >> "$LOGFILE"
SCRIPT

chown root:root /usr/local/bin/logclean
chmod 755 /usr/local/bin/logclean

# Step 2: Create group and user
groupadd -g 1200 logmgr
useradd -u 1200 -g logmgr -d /home/logmgr -m -s /bin/bash -p '!' logmgr

# Set up directories
mkdir -p /var/log/logclean /var/spool/logclean
chown logmgr:logmgr /var/log/logclean /var/spool/logclean
chmod 775 /var/log/logclean
chmod 750 /var/spool/logclean

# Step 3: Environment configuration
cat > /etc/profile.d/logmgr.sh <<'EOF'
export LOGCLEAN_DIR=/var/log/logclean
export LOGCLEAN_KEEP_DAYS=7
EOF

# Configure logmgr's .bashrc
cat >> /home/logmgr/.bashrc <<'EOF'
export PATH="/usr/local/bin:$PATH"
source /etc/profile.d/logmgr.sh
EOF

chown logmgr:logmgr /home/logmgr/.bashrc

# Step 4: Install cron job for logmgr
echo '15 3 * * * /usr/local/bin/logclean /var/log/app' | crontab -u logmgr -

# Step 5: Smoke test
mkdir -p /var/log/app

# Create 5 old .log files (10 days ago)
for i in 1 2 3 4 5; do
    touch /var/log/app/old_${i}.log
    touch -d '10 days ago' /var/log/app/old_${i}.log
done

# Create 2 new .log files (today)
touch /var/log/app/new_1.log
touch /var/log/app/new_2.log

# Run the tool
/usr/local/bin/logclean /var/log/app

echo "Setup complete. run.log contents:"
cat /var/log/logclean/run.log
```