"""Rebuild synthetic evidence. Ground truth is independent, hand-authored JSON."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'datasets'
SOURCES = {
    'A_conflicting_clocks/web.log': '198.51.100.24 - - [28/Oct/2026:10:14:07 +0530] "POST /login HTTP/1.1" 200 412 request_id=R7\n198.51.100.24 - - [28/Oct/2026:10:15:07 +0530] "GET /account HTTP/1.1" 200 812 request_id=R8\n198.51.100.24 - - [28/Oct/2026:10:16:07 +0530] "GET /export HTTP/1.1" 200 3412 request_id=R9\n',
    'A_conflicting_clocks/auth.log': 'Oct 28 04:42:54 host-a sshd[101]: Accepted publickey for analyst from 198.51.100.24 port 49812 request_id=R7\nOct 28 04:43:54 host-a sshd[101]: Session activity for analyst from 198.51.100.24 request_id=R8\nOct 28 04:44:54 host-a sshd[101]: Session closed for analyst from 198.51.100.24 request_id=R9\n',
    'B_cross_source/web.log': '203.0.113.8 - - [28/Oct/2026:04:40:00 +0000] "GET /admin HTTP/1.1" 401 102\n203.0.113.8 - - [28/Oct/2026:04:42:00 +0000] "POST /login HTTP/1.1" 200 281\n203.0.113.8 - - [28/Oct/2026:04:44:00 +0000] "GET /backup.tar HTTP/1.1" 200 8000\n',
    'B_cross_source/auth.log': '2026-10-28T00:41:00-04:00 server-b sshd[202]: Failed password for invalid user admin from 203.0.113.8 port 42200\n2026-10-28T00:43:00-04:00 server-b sshd[202]: Accepted publickey for backup from 203.0.113.8 port 42201\n2026-10-28T00:45:00-04:00 server-b sudo[203]: backup : COMMAND=/usr/bin/tar\n',
    'C_gaps_conflicts/web.log': '192.0.2.7 - - [28/Oct/2026:04:50:00 +0000] "GET /admin HTTP/1.1" 200 200 request_id=DUP\n192.0.2.7 - - [28/Oct/2026:04:49:00 +0000] "GET /admin HTTP/1.1" 500 100 request_id=DUP\n192.0.2.7 - - [99/Oct/2026:04:51:00 +0000] "GET / HTTP/1.1" 200 1\nmissing timestamp and request\n\n',
    'C_gaps_conflicts/auth.log': b'Oct 28 04:52:00 server-c sshd[303]: Failed password for root from 192.0.2.7 port 1234\r\nunsupported appliance format sequence=42\r\n\xff\xfeinvalid encoding\r\n',
}

if __name__ == '__main__':
    for name, content in SOURCES.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode('utf-8') if isinstance(content, str) else content)
    print(f'Wrote {len(SOURCES)} synthetic source files; ground truth unchanged.')
