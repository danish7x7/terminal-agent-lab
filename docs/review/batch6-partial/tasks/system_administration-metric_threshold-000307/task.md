# On-Call SRE: Disk Cleanup Automation Setup

You're on-call and `/var/log` is filling up fast. You need to set up a self-contained log-rotation and disk-cleanup system from scratch on this box. Work through the following steps:

## What you must build

### 1. Build and install `logclean` from source
The source is in `/srv/src/logclean/`. Build the bash script into a standalone executable and install it to `/usr/local/bin/logclean` (mode 755, owner `root:root`). The tool accepts one argument: a directory path. It deletes any `.log` files in that directory older than 7 days and writes a one-line summary to `/var/log/logclean/run.log` in the format:
```
YYYY-MM-DD HH:MM:SS cleaned <N> files from <DIR>
```

### 2. Create a dedicated service user and group
- Group: `logmgr` (GID 1200)
- User: `logmgr` (UID 1200, primary group `logmgr`, home `/home/logmgr`, shell `/bin/bash`, no login password)
- Directory `/var/log/logclean/` must exist, owned by `logmgr:logmgr`, mode 775
- Directory `/var/spool/logclean/` must exist, owned by `logmgr:logmgr`, mode 750

### 3. Configure the environment
- The file `/etc/profile.d/logmgr.sh` must exist and export:
  - `LOGCLEAN_DIR=/var/log/logclean`
  - `LOGCLEAN_KEEP_DAYS=7`
- `/usr/local/bin` must appear in `logmgr`'s PATH (add it via `/home/logmgr/.bashrc` if not already present)
- `/home/logmgr/.bashrc` must source `/etc/profile.d/logmgr.sh`

### 4. Schedule cleanup via cron
- Install a crontab for user `logmgr` that runs `/usr/local/bin/logclean /var/log/app` **every day at 03:15**
- The cron line must be exactly: `15 3 * * * /usr/local/bin/logclean /var/log/app`

### 5. Smoke-test the tool
- Create directory `/var/log/app/`
- Place at least 5 dummy `.log` files in `/var/log/app/` that are older than 7 days (use `touch -d '10 days ago'`)
- Place at least 2 `.log` files with today's date (should NOT be deleted)
- Run `/usr/local/bin/logclean /var/log/app` as root
- Verify the summary line appears in `/var/log/logclean/run.log`

## Output locations
- `/usr/local/bin/logclean` — the installed executable
- `/etc/profile.d/logmgr.sh` — environment config
- `/home/logmgr/.bashrc` — user dotfile
- `/var/log/logclean/run.log` — runtime log written by the tool
- Crontab for `logmgr` installable via `crontab -u logmgr -l`