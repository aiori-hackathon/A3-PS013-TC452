# Verification record — 28 October 2026

Verified locally on Windows with Python 3.12.14 and Node.js 22.14.0. Tests use synthetic data only. All application services bind to loopback. No GitHub push, collaborator change or ownership transfer was performed.

| Check | Result |
| --- | --- |
| Pytest unit/API/acceptance suite | **29 passed**; one third-party Starlette/AnyIO deprecation warning |
| TypeScript check and Vite production build | **Passed** |
| Real HTTP smoke across scenarios A/B/C | **3 passed**, 15 normalized events, five retained gaps |
| Browser smoke using installed Chrome | **Passed**, zero JavaScript/console errors |
| Browser coverage | Create case, two-format import, search/filter, source inspection, manual correction, verification, PDF download, mobile overflow check, anchor preview and explicit approval |
| Desktop/mobile visual inspection | 1440px desktop and 390px mobile screenshots reviewed; timeline scrolls within its container on narrow screens |
| PDF exports | Generated, parsed with pypdf, and visually rendered with Poppler; source references and limitations retained |
| Independent manifest verification | Both scenario C originals **VERIFIED** against exported digests |
| Frontend npm dependency audit | **0 reported vulnerabilities** after Vite update to 6.4.5 |
| Python source compilation | **Passed** |
| Proposal preservation | Git blob matches original `HEAD:ALIBI_AIORI3_Proposal.pdf` |
| Original README preservation | `docs/ORIGINAL_README.md` Git blob matches original `HEAD:README.md` |
| Human manual/assisted comparison | **Pending**; no measurements or speedup claim |

The backend suite covers all three independent ground-truth fixtures, original-byte downloads, line/byte provenance, SHA-256 tampering and missing files, non-accumulating manual offsets, supplied intervals, timezone conversion, DST ambiguity/nonexistence, missing years, malformed dates/records, SQL-literal search, paging, persistence after reopening SQLite, cross-investigation isolation, upload limits/path traversal and cross-origin rejection. Calibration tests cover minimum anchors, span, residual rejection, duplicate IDs, explicit approval, stale references and tampered evidence.

The HTTP smoke writes `output/smoke-results.json`, three PDF reports under `output/pdf/`, and reports/manifests under `output/json/`. Its measured durations are **automated pipeline runtime only** and vary by machine/run. They are not investigator triage time. The browser test produces screenshots and a downloaded PDF under `output/browser/`. Generated data and local evidence are ignored by Git.

## PS-013 acceptance mapping

| Criterion | Implementation / evidence | Status |
| --- | --- | --- |
| Two log formats | Linux auth/syslog + Apache/Nginx access | Implemented, tested |
| Preserve original and normalized copies | Write-once application API, read-only vault + SQLite records | Implemented, tested |
| Evidence hashes | Intake SHA-256, verification, standalone manifest verifier | Implemented, tested |
| Timezone and skew handling | Explicit assumptions, UTC conversion, manual correction; optional reviewed anchors | Implemented, tested |
| Searchable chronological timeline | Search/source/type/date filters, paging, corrected UTC sort | Implemented, browser tested |
| Document parsing gaps | Every failed record retained with raw preview and exact byte range | Implemented, tested |
| Three synthetic scenarios | A/B/C fixtures and separate expected outputs | Implemented, tested |
| Assisted vs manual triage | Real-human timer, scoring and paired comparison protocol | **Human runs pending** |
| Incident summary report | PDF, full JSON, SHA-256 manifest and audit | Implemented, tested |
| Exclusions | No endpoint takeover, malware removal, forensic certification | Respected |

No large-scale performance study, external penetration test, forensic certification, legal chain-of-custody assessment, or production deployment is claimed. The app is intended for a trusted local operator. See `ARCHITECTURE.md` and the README for limitations.
