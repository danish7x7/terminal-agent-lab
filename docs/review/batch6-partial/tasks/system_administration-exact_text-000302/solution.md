```bash
# 1. Environment file
mkdir -p /etc/profile.d
cat > /etc/profile.d/watchdog_env.sh <<'EOF'
export WATCHDOG_HOME=/opt/watchdog
export WATCHDOG_LOG=/var/log/watchdog/service.log
export PATH=$WATCHDOG_HOME/bin:$PATH
EOF

# 2. Directories and Python health-check script
mkdir -p /opt/watchdog/bin /var/log/watchdog
cat > /opt/watchdog/bin/healthcheck.py <<'EOF'
#!/usr/bin/env python3
import os, time
log = os.environ.get('WATCHDOG_LOG', '/var/log/watchdog/service.log')
with open(log, 'a') as f:
    f.write(f'OK {int(time.time())}\n')
EOF

# 3. User/group/permissions
groupadd -g 7700 watchdogs
useradd -r -u 7700 -g watchdogs -d /opt/watchdog -s /bin/false watcher
chown -R watcher:watchdogs /opt/watchdog /var/log/watchdog
chmod 750 /opt/watchdog/bin/healthcheck.py
chmod 770 /var/log/watchdog

# 4. Cron job for watcher
mkdir -p /var/spool/cron/crontabs
cat > /var/spool/cron/crontabs/watcher <<'EOF'
* * * * * /usr/bin/python3 /opt/watchdog/bin/healthcheck.py
EOF
chown watcher:crontab /var/spool/cron/crontabs/watcher 2>/dev/null || chown watcher /var/spool/cron/crontabs/watcher
chmod 600 /var/spool/cron/crontabs/watcher

# 5. Systemd service unit
cat > /etc/systemd/system/watchdog.service <<'EOF'
[Unit]
Description=Watchdog health-check service
After=network.target

[Service]
Type=simple
User=watcher
EnvironmentFile=/etc/profile.d/watchdog_env.sh
ExecStart=/usr/bin/python3 /opt/watchdog/bin/healthcheck.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Restart controller script
cat > /opt/watchdog/bin/restart_controller.py <<'EOF'
#!/usr/bin/env python3
import os, signal, time, subprocess

proc = subprocess.Popen(['sleep', '300'])
pid = proc.pid
os.kill(pid, signal.SIGTERM)
exited = False
for _ in range(30):
    time.sleep(0.1)
    ret = proc.poll()
    if ret is not None:
        exited = True
        break
status = 'terminated' if exited else 'timeout'
with open('/tmp/restart_controller.pid', 'w') as f:
    f.write(f'{pid}\n')
with open('/tmp/restart_controller.status', 'w') as f:
    f.write(f'{status}\n')
EOF
chmod 750 /opt/watchdog/bin/restart_controller.py
chown -R watcher:watchdogs /opt/watchdog

# 7. Run the controller
python3 /opt/watchdog/bin/restart_controller.py

# 8. Gather and write the report
python3 - <<'PYEOF'
import os, stat, pwd, grp
from pathlib import Path

lines = []

# env_file
lines.append('env_file=' + ('present' if Path('/etc/profile.d/watchdog_env.sh').exists() else 'missing'))

# parse env file for values
env_vals = {}
for line in Path('/etc/profile.d/watchdog_env.sh').read_text().splitlines():
    line = line.strip()
    if line.startswith('export '):
        line = line[7:]
    if '=' in line:
        k, v = line.split('=', 1)
        env_vals[k.strip()] = v.strip()
lines.append('watchdog_home=' + env_vals.get('WATCHDOG_HOME', ''))
lines.append('watchdog_log=' + env_vals.get('WATCHDOG_LOG', ''))

# user/group
pw = pwd.getpwnam('watcher')
gr = grp.getgrnam('watchdogs')
lines.append('watcher_uid=' + str(pw.pw_uid))
lines.append('watcher_gid=' + str(gr.gr_gid))

# healthcheck owner and mode
hc = Path('/opt/watchdog/bin/healthcheck.py')
st = hc.stat()
owner = pwd.getpwuid(st.st_uid).pw_name
lines.append('healthcheck_owner=' + owner)
mode = oct(stat.S_IMODE(st.st_mode))
# convert to 3-digit octal without leading 0o
mode_str = str(oct(stat.S_IMODE(st.st_mode)))[2:]
lines.append('healthcheck_mode=' + mode_str)

# logdir mode
ld = Path('/var/log/watchdog')
st2 = ld.stat()
mode2_str = str(oct(stat.S_IMODE(st2.st_mode)))[2:]
lines.append('logdir_mode=' + mode2_str)

# cron line
cron_file = Path('/var/spool/cron/crontabs/watcher')
cron_lines = [l for l in cron_file.read_text().splitlines() if l.strip() and not l.startswith('#')]
lines.append('cron_line=' + (cron_lines[0] if cron_lines else ''))

# service unit
lines.append('service_unit=' + ('present' if Path('/etc/systemd/system/watchdog.service').exists() else 'missing'))

# controller status
status = Path('/tmp/restart_controller.status').read_text().strip()
lines.append('controller_status=' + status)

Path('/output/report.txt').write_text('\n'.join(lines) + '\n')
print('Report written.')
PYEOF
```