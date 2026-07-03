from pathlib import Path

EXPECTED = """env_file=present
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
"""

def test_report_exact():
    p = Path('/output/report.txt')
    assert p.exists(), '/output/report.txt does not exist'
    actual = p.read_text()
    assert actual == EXPECTED, f'Content mismatch.\nExpected:\n{EXPECTED!r}\nGot:\n{actual!r}'
