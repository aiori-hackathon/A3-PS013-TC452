import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS investigations (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY, investigation_id TEXT NOT NULL REFERENCES investigations(id),
 filename TEXT NOT NULL, source TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL,
 imported_at TEXT NOT NULL, log_format TEXT NOT NULL, timezone TEXT NOT NULL, year INTEGER,
 offset_seconds REAL NOT NULL, uncertainty_seconds REAL NOT NULL, correction_reason TEXT NOT NULL,
 total_records INTEGER NOT NULL, parsed_records INTEGER NOT NULL, gap_records INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS records (
 id TEXT PRIMARY KEY, evidence_id TEXT NOT NULL REFERENCES evidence(id),
 investigation_id TEXT NOT NULL REFERENCES investigations(id), line_number INTEGER NOT NULL,
 byte_start INTEGER NOT NULL, byte_end INTEGER NOT NULL, raw_line TEXT NOT NULL,
 error TEXT, original_timestamp TEXT, utc_timestamp TEXT, corrected_timestamp TEXT,
 interval_start TEXT, interval_end TEXT, kind TEXT, message TEXT, host TEXT, service TEXT,
 ip TEXT, status TEXT, timezone_basis TEXT, anchor_id TEXT, parser_version TEXT
);
CREATE INDEX IF NOT EXISTS chronological ON records(investigation_id, corrected_timestamp);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT, investigation_id TEXT NOT NULL REFERENCES investigations(id),
 occurred_at TEXT NOT NULL, action TEXT NOT NULL, details TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS calibration_proposals (
 id TEXT PRIMARY KEY, investigation_id TEXT NOT NULL REFERENCES investigations(id),
 created_at TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL
);
'''


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.vault = self.root / 'evidence'
        self.vault.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / 'alibi.sqlite3'
        with self.connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def rows(self, sql, params=()):
        with self.connect() as db:
            return [dict(r) for r in db.execute(sql, params).fetchall()]

    @staticmethod
    def insert(db, table: str, item: dict):
        # Table and field names are internal constants, never user input.
        db.execute(f"INSERT INTO {table} ({','.join(item)}) VALUES ({','.join('?' for _ in item)})", tuple(item.values()))

    @staticmethod
    def audit(db, investigation_id, action, details, now):
        db.execute('INSERT INTO audit(investigation_id,occurred_at,action,details) VALUES (?,?,?,?)', (investigation_id, now, action, json.dumps(details)))
