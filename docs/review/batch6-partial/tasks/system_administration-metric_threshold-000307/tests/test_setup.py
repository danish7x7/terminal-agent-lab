import subprocess, os, stat, pwd, grp, re
from pathlib import Path
import pytest

SCORE_THRESHOLD = 0.85

def _check(cond, weight=1):
    return weight if cond else 0

def compute_score():
    total = 0
    earned = 0

    # 1. logclean binary exists, correct permissions, owner
    p = Path('/usr/local/bin/logclean')
    total += 3
    if p.exists():
        earned += 1
        st = p.stat()
        mode = stat.S_IMODE(st.st_mode)
        if mode == 0o755:
            earned += 1
        try:
            pw = pwd.getpwuid(st.st_uid)
            gr = grp.getgrgid(st.st_gid)
            if pw.pw_name == 'root' and gr.gr_name == 'root':
                earned += 1
        except Exception:
            pass

    # 2. logclean is executable and actually runs
    total += 1
    try:
        r = subprocess.run(['/usr/local/bin/logclean', '--help'],
                           capture_output=True, timeout=5)
        # just check it doesn't crash with no-arg in unexpected way
        earned += 1
    except Exception:
        try:
            r = subprocess.run(['/usr/local/bin/logclean', '/tmp'],
                               capture_output=True, timeout=5)
            earned += 1
        except Exception:
            pass

    # 3. logmgr group exists with GID 1200
    total += 1
    try:
        g = grp.getgrnam('logmgr')
        if g.gr_gid == 1200:
            earned += 1
    except KeyError:
        pass

    # 4. logmgr user exists with UID 1200
    total += 1
    try:
        u = pwd.getpwnam('logmgr')
        if u.pw_uid == 1200:
            earned += 1
    except KeyError:
        pass

    # 5. /var/log/logclean owned by logmgr:logmgr mode 775
    total += 2
    lcd = Path('/var/log/logclean')
    if lcd.exists():
        st = lcd.stat()
        try:
            pw = pwd.getpwuid(st.st_uid)
            gr = grp.getgrgid(st.st_gid)
            if pw.pw_name == 'logmgr' and gr.gr_name == 'logmgr':
                earned += 1
        except Exception:
            pass
        if stat.S_IMODE(st.st_mode) == 0o775:
            earned += 1

    # 6. /var/spool/logclean owned by logmgr:logmgr mode 750
    total += 2
    spool = Path('/var/spool/logclean')
    if spool.exists():
        st = spool.stat()
        try:
            pw = pwd.getpwuid(st.st_uid)
            gr = grp.getgrgid(st.st_gid)
            if pw.pw_name == 'logmgr' and gr.gr_name == 'logmgr':
                earned += 1
        except Exception:
            pass
        if stat.S_IMODE(st.st_mode) == 0o750:
            earned += 1

    # 7. /etc/profile.d/logmgr.sh exports correct vars
    total += 2
    prof = Path('/etc/profile.d/logmgr.sh')
    if prof.exists():
        content = prof.read_text()
        if 'LOGCLEAN_DIR=/var/log/logclean' in content:
            earned += 1
        if 'LOGCLEAN_KEEP_DAYS=7' in content:
            earned += 1

    # 8. /home/logmgr/.bashrc sources profile.d/logmgr.sh
    total += 1
    bashrc = Path('/home/logmgr/.bashrc')
    if bashrc.exists():
        content = bashrc.read_text()
        if '/etc/profile.d/logmgr.sh' in content:
            earned += 1

    # 9. /home/logmgr/.bashrc has /usr/local/bin in PATH
    total += 1
    if bashrc.exists():
        content = bashrc.read_text()
        if '/usr/local/bin' in content:
            earned += 1

    # 10. crontab for logmgr has correct line
    total += 2
    try:
        r = subprocess.run(['crontab', '-u', 'logmgr', '-l'],
                           capture_output=True, text=True, timeout=5)
        cron_out = r.stdout
        if '15 3 * * * /usr/local/bin/logclean /var/log/app' in cron_out:
            earned += 2
        elif '/usr/local/bin/logclean' in cron_out and '15' in cron_out and '3' in cron_out:
            earned += 1
    except Exception:
        pass

    # 11. run.log exists and has a valid summary line
    total += 3
    runlog = Path('/var/log/logclean/run.log')
    if runlog.exists():
        earned += 1
        content = runlog.read_text()
        # format: YYYY-MM-DD HH:MM:SS cleaned N files from DIR
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} cleaned \d+ files from /var/log/app'
        if re.search(pattern, content):
            earned += 2

    # 12. old log files were deleted, new ones kept
    total += 2
    app = Path('/var/log/app')
    if app.exists():
        logs = list(app.glob('*.log'))
        # we check that fewer than 5 old files remain (they should be gone)
        # and at least some files remain (the new ones)
        import time
        now = time.time()
        old_remaining = [f for f in logs if (now - f.stat().st_mtime) > 7*86400]
        new_remaining = [f for f in logs if (now - f.stat().st_mtime) <= 7*86400]
        if len(old_remaining) == 0:
            earned += 1
        if len(new_remaining) >= 2:
            earned += 1

    return earned, total

def test_score_meets_threshold():
    earned, total = compute_score()
    score = earned / total
    print(f'Score: {earned}/{total} = {score:.2f}')
    assert score >= SCORE_THRESHOLD, f'Score {score:.2f} < {SCORE_THRESHOLD}'
