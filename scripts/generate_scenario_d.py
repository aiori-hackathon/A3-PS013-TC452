"""Generate the fixed Scenario D fixture. No parser or ground-truth dependencies."""
import argparse
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "datasets/D_realistic_incident"
WEB = [
    ("00:00", "192.0.2.12", "/", 200), ("00:12", "192.0.2.12", "/styles.css", 200),
    ("00:45", "198.51.100.12", "/hours", 200), ("01:10", "192.0.2.30", "/health", 200),
    ("01:50", "203.0.113.24", "/admin", 401), ("02:05", "192.0.2.45", "/contact", 200),
    ("02:35", "192.0.2.12", "/favicon.ico", 304), ("03:00", "198.51.100.12", "/calendar", 200),
    ("03:09", "192.0.2.30", "/health", 200), ("03:42", "203.0.113.24", "/help", 200),
    ("04:00", "198.51.100.31", "/events", 200), ("04:40", "192.0.2.12", "/about", 200),
    ("05:20", "192.0.2.30", "/health", 200), ("05:50", "203.0.113.24", "/exports/backup.tar.gz", 200),
    ("06:10", "192.0.2.45", "/map.svg", 304), ("06:35", "198.51.100.12", "/news", 200),
    ("07:00", "192.0.2.30", "/health", 200), ("07:40", "192.0.2.12", "/schedule", 404),
    ("08:20", "198.51.100.31", "/hours", 200), ("09:00", "192.0.2.30", "/health", 200),
]
AUTH = [
    "04:59:05 sshd[311]: Accepted publickey for scheduler from 192.0.2.80 port 50001 ssh2",
    "04:59:18 sshd[311]: pam_unix(sshd:session): session opened for user scheduler",
    "05:00:40 sshd[347]: Failed password for invalid user ops from 203.0.113.24 port 51001 ssh2",
    "05:01:00 sshd[348]: Failed password for ops from 203.0.113.24 port 51003 ssh2",
    "05:01:20 sshd[349]: Failed password for ops from 203.0.113.24 port 51005 ssh2",
    "05:01:25 sshd[311]: pam_unix(sshd:session): session closed for user scheduler",
    "05:02:00 sshd[352]: Failed password for deploy from 198.51.100.90 port 51300 ssh2",
    "05:02:35 sshd[355]: Accepted publickey for ops from 203.0.113.24 port 51111 ssh2",
    "05:02:36 sshd[355]: pam_unix(sshd:session): session opened for user ops",
    "05:03:30 sshd[360]: Accepted publickey for monitor from 192.0.2.81 port 51400 ssh2",
    "05:04:45 sudo[380]: ops : TTY=pts/1 ; PWD=/srv ; USER=root ; COMMAND=/usr/bin/tar --version",
    "05:06:00 sshd[355]: pam_unix(sshd:session): session closed for user ops",
    "truncated authentication relay record",
]
SYSTEM = [
    ("00:05", "systemd[1]: Started daily housekeeping"),
    ("01:00", "cron[201]: Scheduled inventory check completed"),
    ("02:00", "systemd[1]: Reloaded application configuration"),
    ("03:00", "kernel: Network link remains up"),
    ("04:05", "cron[254]: Refreshed service inventory"),
    ("06:20", "systemd[1]: Finished scheduled journal rotation"),
    ("08:55", "cron[302]: Periodic service check completed"),
]


def generate(directory):
    directory.mkdir(parents=True, exist_ok=True)
    logs = {
        "access.log": [f'{ip} - - [19/Nov/2026:10:{30+int(clock[:2]):02d}:{clock[3:]} +0530] "GET {path} HTTP/1.1" {status} {0 if status == 304 else 512}' for clock, ip, path, status in WEB],
        "auth.log": ["Nov 19 " + line[:8] + " portal-host " + line[9:] if line[:1].isdigit() else line for line in AUTH],
        "system.log": [f"2026-11-19T01:{clock}-04:00 portal-monitor {message}" for clock, message in SYSTEM],
    }
    for name, lines in logs.items():
        (directory/name).write_bytes(("\n".join(lines)+"\n").encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT)
    generate(parser.parse_args().out)
