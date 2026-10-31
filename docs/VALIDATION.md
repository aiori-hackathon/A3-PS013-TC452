# Release verification record — 31 October 2026

Revalidated locally on Windows with Python 3.12.14, Node.js 22.14.0 and Windows PowerShell 5.1.26100.9711. Tests use synthetic data only. All application services bind to loopback. No GitHub push, collaborator change or ownership transfer was performed. The pre-release working application was checkpointed as `bedcf0d` on `codex/alibi-prototype`; the previous 29-test validation remains in that commit's history.

| Check | Result |
| --- | --- |
| Pytest unit/API/acceptance suite | **30 passed in 7.04s**; one third-party Starlette/AnyIO deprecation warning |
| TypeScript check and Vite production build | **Passed** |
| Real HTTP smoke across scenarios A/B/C | **3 passed**, 15 normalized events, five retained gaps |
| Browser smoke using installed Chrome | **Passed**, zero JavaScript/console errors |
| Browser coverage | Create case, two-format import, search/filter, source inspection, manual correction, verification, PDF/JSON downloads, anchor preview/approval, five gaps and two findings |
| Responsive inspection | **1440px desktop, 768px tablet, 390px mobile**; timeline, upload, clock, source inspection and export views checked; no page-width overflow |
| PDF exports | **All three generated**, three pages each; pypdf content checks and all nine rendered pages visually reviewed; source references, hashes, original/corrected times and limitations retained |
| Audit preservation | New regression proves readable PDF generation leaves JSON audit records unchanged; full history remains in JSON |
| Independent manifest verification | **All six originals VERIFIED** across A/B/C |
| Evidence tampering | Isolated synthetic tests pass for hash mismatch, missing files, tampered anchor rejection and red/critical PDF mismatch reporting |
| Windows startup | `powershell.exe -NoProfile -File scripts/start.ps1 -Service backend` successfully restarted the identified ALIBI backend under PowerShell 5.1; frontend and API reachable |
| Dependency audit | Prior 28 October result: 0 npm vulnerabilities after Vite 6.4.5 update; not rerun in this release sprint; dependencies unchanged |
| Proposal preservation | Bytes match `ba55f33:ALIBI_AIORI3_Proposal.pdf` |
| Original README preservation | `docs/ORIGINAL_README.md` matches `ba55f33:README.md`, allowing only Git newline normalization |
| Original PS-013 preservation | Bytes match checkpoint `bedcf0d:docs/PS-013.pdf` |
| Human manual/assisted comparison | **Pending**; no measurements or speedup claim |

The backend suite covers all three independent ground-truth fixtures, original-byte downloads, line/byte provenance, SHA-256 tampering and missing files, non-accumulating manual offsets, supplied intervals, timezone conversion, DST ambiguity/nonexistence, missing years, malformed dates/records, SQL-literal search, paging, persistence after reopening SQLite, cross-investigation isolation, upload limits/path traversal and cross-origin rejection. Calibration tests cover minimum anchors, span, residual rejection, duplicate IDs, explicit approval, stale references and tampered evidence.

The final HTTP smoke completed around 16:57 UTC. It writes `output/smoke-results.json`, three PDFs under `output/pdf/`, and reports/manifests under `output/json/`. Its durations are **automated pipeline runtime only**, not investigator triage time. The final browser result at 16:58 UTC is in `output/browser/smoke-results.json`; additional dialog checks and screenshots are in `output/browser/release-dialogs/`. Generated data and local evidence are ignored by Git.

The rendered PDF review used local Poppler. It emitted a missing Symbol display-font warning, but all pages rendered and were visually checked; the reports use Helvetica. Pytest's single deprecation warning is in installed Starlette's AnyIO alias and did not fail tests.

## Reproduce this release gate

Run from the repository root with services running. A fresh local test directory avoids Windows temporary-directory permission/cleanup issues:

~~~powershell
$testDirectory = ".alibi/tests-$([guid]::NewGuid().ToString('N'))"
.\.venv\Scripts\python.exe -m pytest -q --tb=short -p no:cacheprovider --basetemp $testDirectory
.\.venv\Scripts\python.exe scripts/smoke.py
foreach ($scenario in @('A_conflicting_clocks','B_cross_source','C_gaps_conflicts')) {
    .\.venv\Scripts\python.exe scripts/verify_manifest.py "output/json/$scenario-manifest.json"
    if ($LASTEXITCODE) { throw "Manifest verification failed: $scenario" }
}
Set-Location src/frontend
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
node smoke.mjs
Set-Location ../..
.\.venv\Scripts\python.exe scripts/triage_evaluation.py compare
~~~

The human comparison command currently prints **PENDING**. Use [the two-person pilot](EVALUATION_PILOT.md) to collect actual measurements. No human speedup is claimed.

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
