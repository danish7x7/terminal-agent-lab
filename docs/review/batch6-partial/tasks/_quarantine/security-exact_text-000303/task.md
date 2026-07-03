# Security Hardening Investigation

You are hardening a fresh host. Four artifacts need analysis. Write your findings to `/output/findings.txt` — exactly four lines in this order, each ending with a newline:

```
PCAPTOKEN=<value>
BRUTEPASS=<password>
BADPERM=<filepath>
ANOMALY_IP=<ip_address>
```

### Task 1 – Offline PCAP inspection

A packet capture is at `/data/auth_traffic.pcap`. Inspect it with `tshark` (already installed). Find the Bearer token sent in an HTTP Authorization header. The token is a short alphanumeric string. Write it as `PCAPTOKEN=<value>`.

### Task 2 – Brute-force a local service

A small HTTP basic-auth service is listening on port 7777 (start it first with `python3 /app/auth_server.py &`). A wordlist is at `/data/wordlist.txt`. The username is `admin`. Find the correct password by trying each word in the wordlist against `http://localhost:7777/secret`. Write it as `BRUTEPASS=<password>`.

### Task 3 – Permission review

Inspect the files under `/data/configs/`. One file has dangerously permissive world-writable permissions (`o+w` set on a file that should be protected). Write its full path as `BADPERM=<filepath>`.

### Task 4 – Log parsing and anomaly detection

An SSH auth log is at `/data/auth.log`. One IP address has more than 10 failed login attempts (lines containing `Failed password`). Write it as `ANOMALY_IP=<ip_address>`.

---

Write all four lines to `/output/findings.txt`. No blank lines, no extra text.