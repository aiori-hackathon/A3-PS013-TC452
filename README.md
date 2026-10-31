# ALIBI — Evidence-First Incident Reconstruction

**Team EXPOSE · A3-PS013-TC452 · AIORI Hackathon 3 · PS-013**

A working local prototype for small IT teams: create an investigation, import logs, preserve original evidence, normalize timestamps, reconstruct a timeline, inspect gaps, and export a verifiable report.

**Implemented and tested:** React + Vite + TypeScript frontend, Python 3.12 + FastAPI + Pydantic backend, SQLite persistence, two log families, SHA-256 verification, explicit clock correction, searchable timeline, gap ledger, PDF/JSON/manifest exports and reviewed anchor calibration. No cloud services or AI APIs are required.

**Still pending:** real human manual-versus-assisted triage measurements. A reproducible protocol and timer/scoring harness are provided; no human times or speedup claims are fabricated.

## Quick start (Windows PowerShell)

From the repository root, with Python 3.12 and Node.js 22 installed. The launch script was verified with **Windows PowerShell 5.1**; PowerShell 7 / `pwsh` is not required. Dependencies are already installed in this working checkout; run setup only on a fresh installation.

```powershell
powershell.exe -NoProfile -File scripts/setup.ps1
powershell.exe -NoProfile -File scripts/start.ps1
```

Open **http://127.0.0.1:5173**. API health: http://127.0.0.1:8000/api/health. API contract: http://127.0.0.1:8000/api/openapi.json. Services bind to `127.0.0.1` only. The start script opens hidden background processes and records PIDs and logs under `.alibi/`; it does not replace an existing listener on either port. Existing listeners must be identified if startup reports a collision.

On the build machine, Python was not on PATH and the default npm shim was broken. The verified setup uses bundled Python 3.12.14 and npm next to `D:\node.js\node.exe`; the setup script detects these. After setup, the virtual environment and local Node dependencies are sufficient. Dependency installation needs internet; the application works offline.

To run in two visible terminals and stop with Ctrl+C:

```powershell
# Terminal 1, repository root
Set-Location 'D:/HACKATHONS/AIORI 3/A3-PS013-TC452'
.\.venv\Scripts\python.exe -m uvicorn alibi.main:app --app-dir src/backend --host 127.0.0.1 --port 8000

# Terminal 2, repository root
Set-Location 'D:/HACKATHONS/AIORI 3/A3-PS013-TC452/src/frontend'
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
```

On macOS/Linux, create `.venv` with `python3.12 -m venv .venv`, install `src/backend/requirements-lock.txt`, run `npm ci` in `src/frontend`, and use `.venv/bin/python` for the backend command. Windows is the verified platform; these Unix commands are provided for portability and were not executed here.

## Use the workbench

1. **Create investigation.** Give it a name and scope.
2. **Import evidence.** Drag/drop or browse. Select a source label, parser, explicit timezone and year when required. Import different source clocks separately. Limits: 10 MiB and 50,000 records per file.
3. **Preserve and calibrate.** Review the SHA-256 and counts in Evidence vault. Correct a slow clock with a positive offset; corrections are absolute, not cumulative. Record the supporting reason. Original bytes and normalized UTC remain unchanged.
4. **Reconstruct.** Search messages/IPs/IDs; filter source, event type and UTC range. Inspect original, UTC and corrected times, supplied intervals, line number, byte range and verified original record.
5. **Challenge.** Review every unparsed line and observed identifier/status or source-order conflict. Silence and parsing failures are not evidence of malicious activity.
6. **Verify and export.** Recalculate file hashes. Download PDF, lossless JSON and the SHA-256 manifest. Audit history records intake, clock changes, proposals and verification.

Traditional syslog without a year needs an explicit year. Timezone-free timestamps need an explicit timezone assumption; the visible default is UTC. Ambiguous/nonexistent DST times are rejected as gaps. Explicit offsets in web logs override timezone assumptions. No timestamp, New Year rollover, clock offset or causal link is invented.

Optional anchor calibration is under **Evidence vault → Correct clock**. It requires at least three unique same-event anchors across distinct sources, a >=60-second span, small residuals, an investigator-provided semantic basis and explicit approval. Shared IDs alone do not prove same-event identity. Stale proposals and tampered anchors are rejected. This is a constant-offset model, not drift estimation or a causal graph.

## Reproducible validation

```powershell
# Backend unit/API/acceptance tests
$testDirectory = ".alibi/tests-$([guid]::NewGuid().ToString('N'))"
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $testDirectory

# Recreate the six synthetic evidence files; independent truth remains unchanged
.\.venv\Scripts\python.exe scripts/generate_datasets.py

# With both services running: import all three cases and export reports
.\.venv\Scripts\python.exe scripts/smoke.py

# Production build (works even with the machine's broken npm shim)
Set-Location src/frontend
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build

# Browser smoke; installed Chrome required by default
node smoke.mjs
Set-Location ../..

# Independent manifest verification and pending human benchmark status
.\.venv\Scripts\python.exe scripts/verify_manifest.py output/json/C_gaps_conflicts-manifest.json
.\.venv\Scripts\python.exe scripts/triage_evaluation.py compare
```

Browser smoke uses a fresh headless Chrome session. Set `$env:ALIBI_BROWSER_CHANNEL = 'msedge'` to use installed Edge instead. It creates labeled synthetic investigations, checks form submission, upload, search/filter, provenance, manual correction, hash verification, PDF/JSON downloads, five gaps plus two review findings, and reviewed anchor calibration. It checks 1440px desktop, 768px tablet and 390px mobile layouts. Screenshots and the result JSON are in `output/browser/`.

| Required scenario | Normalized | Parsing gaps | Coverage |
| --- | ---: | ---: | --- |
| A / conflicting clocks and timezones | 6 | 0 | +05:30 access timestamps; explicit 2026 UTC syslog; +73-second host correction |
| B / cross-source reconstruction | 6 | 0 | Alternating web/auth observations; explicit -04:00 conversion; shared IP is not causation |
| C / gaps and conflicts | 3 | 5 | Bad date, unsupported/missing fields, blank line, invalid UTF-8, reversed order and differing statuses for reused ID |

`datasets/ground_truth.json` is hand-authored separately from the parsers and fixture generator. Automated acceptance asserts corrected times against it, byte preservation, hashes, tamper detection, ordering, gap accounting and exports. See [validation results](docs/VALIDATION.md), [two-person human evaluation](docs/EVALUATION_PILOT.md) and [five-minute demonstration handoff](DEMO_READY.md).

Release checks on 31 October 2026: **30 Pytest tests passed**, TypeScript and Vite build passed, three HTTP scenarios passed, and browser smoke passed without console errors. Human triage evaluation remains pending. The PDF now presents identification, overview, integrity, chronology, clock assumptions, gaps and limitations; complete audit details remain in the lossless JSON export. See the validation record for scope and known warning.

## Project structure

```text
src/backend/alibi/       API, schemas, SQLite, parsers, calibration, reporting
src/backend/tests/       Pytest unit/API/acceptance tests
src/frontend/            React workbench, production build and browser smoke
datasets/                Six reproducible synthetic logs + independent ground truth
scripts/                 Setup/start, generator, HTTP smoke, human timer, verifier
docs/                    Architecture, API contract, demo, validation, preserved docs
.alibi/                  Local evidence vault, SQLite database, service logs (ignored)
output/                  Generated reports, screenshots and evaluations (ignored)
```

Keep the database and vault together. Close the backend before copying `.alibi/` for backup. All original evidence is local and unencrypted. `ALIBI_DATA_DIR` can point the backend to a different data directory.

## Known limitations and exclusions

- Only the documented Linux syslog/auth and common/combined web access formats are supported. Other formats become visible gaps; no CSV/JSON or structured RFC5424 adapter is implemented.
- No forensic certification, endpoint takeover, malware removal, threat detection, digital signatures or pre-intake authenticity guarantee. Read-only files and hashes are not tamper-proof storage or legal chain of custody.
- Single-investigator local prototype, no authentication, encryption, multi-user authorization, schema migration system or production hardening. Never expose the ports to a network.
- Yearless files spanning New Year must be split with documented assumptions. Timezone/year corrections require a new import; the original import remains available.
- Supplied uncertainty and anchor bounds are assumptions, not statistical confidence intervals. No full partial-order graph, clock drift model or proof of missing unseen events is implemented. The visible-page overlap indicator is limited to adjacent events in the current filter.
- Search uses SQLite literal substring matching rather than FTS5. Large investigations/export generation are synchronous and have not been load-tested. Atomic database transactions do not make file/database writes one atomic operation; interrupted intake can leave unindexed vault files.
- PDF uses a Latin-1 font and substitutes unsupported characters with `?`; gap previews are limited to 1,000 characters. JSON, source-byte inspection and original downloads preserve the full content. Interactive API docs use default CDN assets; the OpenAPI JSON and application remain offline-capable.
- The human triage benchmark is pending. Automated runtimes are not human performance results.

## Project references

[Original proposal](ALIBI_AIORI3_Proposal.pdf) · [Original PS-013](docs/PS-013.pdf) · [Preserved original README](docs/ORIGINAL_README.md) · [Architecture and API](docs/ARCHITECTURE.md) · [Introduction video](https://youtu.be/RhR5dDCjA2M)

Developed by Anurag Deb and Sangram Keshari Patra

Mentored by Prof. Partha Chakraborty

| Contributor | Role | Profile |
| --- | --- | --- |
| Anurag Deb | Team Lead & Full-Stack Developer | [LinkedIn](https://www.linkedin.com/in/debanurag) |
| Sangram Keshari Patra | Backend Developer | [LinkedIn](https://www.linkedin.com/in/sangramkpatra/) |
| Prof. Partha Chakraborty | Faculty Mentor | [LinkedIn](https://www.linkedin.com/in/partha-chakraborty-bb506638/) |

ALIBI is an independent Team EXPOSE project and does not imply government affiliation.

Local development branch: `codex/alibi-prototype`. Existing Git history and documents are preserved. No changes have been pushed to GitHub.
