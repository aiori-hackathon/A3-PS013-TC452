# ALIBI prototype architecture

Source requirements: `ALIBI_AIORI3_Proposal.pdf` (11 pages) and original `PS-013.pdf` found in the parent directory, preserved as `docs/PS-013.pdf`. The original README is preserved in `docs/ORIGINAL_README.md`. Instructions in those documents about GitHub ownership/collaborators are not executed as part of implementation.

## Local components

```text
React + TypeScript / Vite (127.0.0.1:5173)
    -> same-origin /api proxy
FastAPI + Pydantic (127.0.0.1:8000)
    -> byte-preserving intake -> SHA-256 -> UUID-named read-only vault
    -> deterministic parser -> timestamp normalization -> SQLite
    -> timeline / gap ledger / source inspection / audit
    -> verification + JSON / PDF / integrity manifest
```

All application code is in `src/`. There are no paid services, cloud databases, AI calls, containers, endpoint agents, Redis, or Elasticsearch. Dependency installation requires internet; normal operation does not. UI assets, fonts, parsing, hashing, storage and reporting are local. FastAPI's optional Swagger documentation uses its default CDN assets, so the JSON OpenAPI contract remains available offline even when Swagger's interactive UI cannot load.

## Evidence contract

An investigation owns evidence and records. The evidence row stores a UUID, user filename/source, SHA-256, byte length, intake UTC, format, timezone/year assumptions, absolute clock correction, uncertainty, reason and record counts. The UUID alone determines the vault pathname. Filenames with path components, control characters or encoded control/path separators are rejected. Original data is written with exclusive creation, flushed/fsynced, then marked read-only; no overwrite/delete endpoint exists.

Each physical record, including blanks, has a UUID, 1-based line number and half-open byte range `[start,end)` including its original terminator. A record either has normalized fields or an explicit error. UTF-8 decoding errors become gaps; original bytes remain intact. Source inspection returns a verified byte slice as base64. The displayed preview replaces invalid characters, and is never substituted for the original.

Parser version is `alibi-1`. Supported formats: traditional English-month Linux syslog/auth, an ISO 8601 timestamp + host/service syslog variant, and common/combined Apache/Nginx access records. Other formats, JSON/CSV and RFC5424 structured syslog are unsupported and go to the gap ledger. Mixed supported formats can be detected per line. Fields and output schemas are defined in Pydantic and SQLite; the generated OpenAPI schema is saved in `docs/openapi.json`.

## Time semantics

1. Explicit timezone offsets take precedence over intake assumptions.
2. Naive timestamps use the investigator's IANA timezone or fixed offset. Ambiguous/nonexistent DST times become gaps; a fixed offset resolves them only through a new documented import.
3. Yearless syslog requires an explicit year. There is no current-year guessing or automatic New Year rollover.
4. `corrected = normalized UTC + absolute correction`, bounded to +/-7 days. Reapplying a correction does not accumulate it. Original timestamp text and normalized UTC are retained.
5. A supplied uncertainty yields a symmetric interval. Zero means no bound supplied, not clock perfection. Equal/overlapping intervals do not establish ordering. The UI overlap indicator compares adjacent records in the visible filtered page; it is not a complete partial-order graph.
6. Optional anchor estimation requires investigator-attested same-event semantics, distinct source labels, at least three unique matching IDs over >=60 seconds, and maximum residual <=2 seconds. The median gives a constant offset. The reported bound is max residual + reference uncertainty + 1 second resolution allowance, not a confidence interval. Duplicate IDs within a source are excluded. A proposal does not change times until separately approved. Source integrity and settings are rechecked on approval; stale proposals are rejected.

Shared identifiers produce explicitly typed associations, never causal edges. Differing statuses for the same ID within one source and backwards timestamps generate review findings, not automatic threat detections. A long quiet period alone is not reported as proven evidence loss.

## API contract

All endpoints are under `/api`. The complete machine-readable contract is `docs/openapi.json`; interactive docs at `/api/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Database/service readiness |
| GET / POST | `/investigations` | List / create investigation |
| GET / POST | `/investigations/{id}/evidence` | List / upload (`file` + JSON-string `options`, multipart) |
| GET | `/investigations/{id}/timeline` | Literal case-insensitive search; source, kind, time filters; paging |
| GET | `/investigations/{id}/gaps` | All unnormalized records |
| GET | `/investigations/{id}/records/{record_id}` | Record, fresh hash check, exact original bytes |
| GET | `/investigations/{id}/evidence/{evidence_id}/original` | Verified original download; 409 on mismatch |
| PATCH | `/investigations/{id}/evidence/{evidence_id}/clock` | Apply absolute correction and audit reason |
| POST | `/investigations/{id}/verify` | Verify all files and audit results |
| GET | `/investigations/{id}/findings`, `/relationships`, `/audit` | Review observations and lineage |
| GET / POST | `/investigations/{id}/calibration/proposals` | List / preview a supported clock model |
| POST | `/investigations/{id}/calibration/proposals/{proposal_id}/approve` | Explicit approval with reason |
| GET | `/investigations/{id}/report.json`, `/report.pdf`, `/manifest.json` | Exports with fresh integrity results |

Timeline filters: `q`, `evidence_id`, `kind`, `start`, `end`, `limit` (1-1000), `offset`. Time filters require explicit timezone offsets. Search uses bound SQL parameters and literal substring matching; FTS5 is deferred at this scale.

## Operational boundaries

Uploads are limited to 10 MiB/file and 50,000 physical records; the multipart request requires Content-Length and is capped at 11 MiB. Records over 64 KiB become gaps. This is a trusted local single-investigator prototype, not a public upload service. Host/origin checks reject unexpected hosts, cross-site browser requests and unknown origins. Bind only to loopback. Anyone with local API access can create/read investigations; there is no login or access-control system.

SQLite foreign keys and transactions protect record writes and calibration changes. The vault and database must be backed up together while the service is stopped. An interruption between writing a file and committing metadata can leave an orphan UUID file; originals are deliberately not deleted on failure. No automated recovery/import migration is supplied. The SQLite schema is initialized with `CREATE TABLE IF NOT EXISTS`; future schema changes need migrations.

Read-only filesystem flags and SHA-256 are not write-once hardware, signatures, trusted timestamps, encrypted storage or a legal chain of custody. A privileged local user could change both the vault and database. Independent copies of exported manifests improve reviewability but do not solve authenticity before intake.
