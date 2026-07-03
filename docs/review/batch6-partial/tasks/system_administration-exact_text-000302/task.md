# Automated Service Watchdog Setup

You are an engineer who needs to script a complete watchdog environment for a Python HTTP health-check service. Complete **all** of the following steps so the final state matches the specification exactly.

## Goal

Set up a self-contained watchdog system and write a summary report to `/output/report.txt`.

---

## Step-by-step specification

### 1. Environment & PATH

Create `/etc/profile.d/watchdog_env.sh` that exports:
- `WATCHDOG_HOME=/opt/watchdog`
- `WATCHDOG_LOG=/var/log/watchdog/service.log`
- `PATH=$WATCHDOG_HOME/bin:$PATH`

### 2. Directories & the Python service script

- Create `/opt/watchdog/bin/` and `/var/log/watchdog/`
- Write a Python script `/opt/watchdog/bin/healthcheck.py` that, when run, appends one line `OK <epoch-seconds>` to `$WATCHDOG_LOG` (read the env var at runtime).

### 3. User/group & permissions

- Create group `watchdogs` (GID 7700)
- Create system user `watcher` (UID 7700, primary group `watchdogs`, home `/opt/watchdog`, shell `/bin/false`)
- Own `/opt/watchdog` and `/var/log/watchdog` recursively by `watcher:watchdogs`
- `chmod 750` on `/opt/watchdog/bin/healthcheck.py`
- `chmod 770` on `/var/log/watchdog`

### 4. Cron job

Install a crontab for the `watcher` user that runs `healthcheck.py` every minute:

```
* * * * * /usr/bin/python3 /opt/watchdog/bin/healthcheck.py
```

(No other lines except the standard `MAILTO=` header line is optional.)

### 5. Systemd-style service unit

Write `/etc/systemd/system/watchdog.service` with **exactly** this content (copy verbatim):

```
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
```

### 6. Python restart-controller script

Write `/opt/watchdog/bin/restart_controller.py`. When executed as root it must:

1. Fork a background process that runs `sleep 300` and record its PID.
2. Send `SIGTERM` to that PID.
3. Wait up to 3 seconds for it to exit.
4. Write `/tmp/restart_controller.pid` containing just the integer PID followed by a newline.
5. Write `/tmp/restart_controller.status` containing either `terminated` or `timeout` followed by a newline.

### 7. Run the controller

Execute `/opt/watchdog/bin/restart_controller.py` with `python3`.

---

## Final report

Write a Python script that gathers the results of **all** steps and writes `/output/report.txt` with **exactly** the following format (one key=value per line, no trailing spaces, Unix newlines):

```
env_file=present
watchdog_home=/opt/watchdog
watchdog_log=/var/log/watchdog/service.log
watcher_uid=7700
watcher_gid=7700
healthcheck_owner=watcher
healthcheck_mode=750
logdir_mode=770
cron_line=* * * * * /usr/bin/python3 /opt/watchdog/bin/healthcheck.py
service_unit=present
controller_status=terminated
```

Write the report to `/output/report.txt`.