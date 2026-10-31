# ALIBI — demonstration handoff

Team EXPOSE · A3-PS013-TC452 · AIORI Hackathon 3 · PS-013

## Start on Windows PowerShell 5.1

Dependencies already exist in this checkout. No PowerShell 7 is needed. From the repository root:

~~~powershell
# Run from your ALIBI repository root
powershell.exe -NoProfile -File scripts/start.ps1
~~~

The script starts hidden local processes and logs under `.alibi/`. If it reports an existing listener, check the URLs below; do not start duplicates or terminate an unidentified process.

Alternatively, use two visible terminals (Ctrl+C stops each):

~~~powershell
# Terminal 1
# Run from your ALIBI repository root
.\.venv\Scripts\python.exe -m uvicorn alibi.main:app --app-dir src/backend --host 127.0.0.1 --port 8000
~~~

~~~powershell
# Terminal 2
# From the repository root
Set-Location src/frontend
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
~~~

- App: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- API contract: [http://127.0.0.1:8000/api/openapi.json](http://127.0.0.1:8000/api/openapi.json)

The app runs locally without cloud services. A fresh machine needs Python 3.12, Node 22 and dependencies installed with `powershell.exe -NoProfile -File scripts/setup.ps1`; installation needs internet. Windows is the verified platform.

## Before the audience arrives

Run from the repository root:

~~~powershell
.\.venv\Scripts\python.exe scripts/smoke.py
~~~

This imports all three **synthetic** cases and saves fallback PDF/JSON/manifest exports under `output/`. Each run intentionally creates fresh cases. In the investigation selector, locate the latest `SYNTHETIC / B cross source` and `SYNTHETIC / C gaps conflicts`. Open a fallback PDF once before presenting. Keep this guide and the app visible.

Exact evidence files:

| Scenario | Web file | Auth file |
| --- | --- | --- |
| A | `datasets/A_conflicting_clocks/web.log` | `datasets/A_conflicting_clocks/auth.log` |
| B | `datasets/B_cross_source/web.log` | `datasets/B_cross_source/auth.log` |
| C | `datasets/C_gaps_conflicts/web.log` | `datasets/C_gaps_conflicts/auth.log` |

Import files separately so each source has its own clock settings. Choose Apache/Nginx access for web and Linux auth/syslog for auth, or use Auto detect. A/C auth require year 2026 and UTC. Explicit web zones and B auth's -04:00 override the timezone assumption.

## Five-minute live script

**0:00–0:45 — Create and preserve.** Say: “ALIBI helps a small IT team organize evidence and check its limits.” Create `Demo / conflicting clocks`. Import A's web file with source `Web gateway`, timezone UTC and correction 0. Import A's auth file with source `Linux host A`, UTC, year 2026 and initially correction 0. Keep uncertainty 0. Show the two evidence files and their SHA-256 values. A hash is a fingerprint used to detect changed bytes.

**0:45–1:35 — Correct the 73-second clock error.** Open Evidence vault → auth.log → Correct clock. Set Correction (seconds) to **73**, uncertainty to **2**, and reason to `Known synthetic clock offset; supplied two-second demonstration bound`. Apply correction & record assumption. Explain: positive adds time to a slow source clock; this is documented fixture knowledge, not an automatic discovery. On Timeline, auth line 1 moves from 04:42:54 UTC to **04:44:07 UTC**. Original bytes and original/normalized timestamps remain available. The ±2-second interval is a supplied bound, not a statistical estimate.

**1:35–2:15 — Inspect and reconstruct.** Search `R7`; two records remain. Inspect a row to show original, UTC and corrected time, source line/byte range and verified original bytes. Clear filters. Switch to seeded B: six alternating web/auth events run from **04:40 to 04:45 UTC**. Search `203.0.113.8`. Explain: a shared IP and sequence are observations; they do not establish the same person or causation.

**2:15–3:10 — Challenge the evidence.** Select seeded C and open Gaps & review. Show **three normalized events and five gaps**: web line 3 invalid day, web line 4 unsupported/missing fields, web line 5 blank, auth line 2 unsupported, auth line 3 invalid UTF-8. Open the invalid-byte record to show preserved evidence. Show two review warnings: source timestamps move backward, and identifier DUP has different statuses (200/500). Neither proves an attack or an unseen missing event.

**3:10–4:15 — Verify and export.** Open Verify & export → Verify all files. Both files should be green/verified. Download PDF report, JSON report and SHA-256 manifest. Show the PDF's overview, chronology, clock assumptions, gaps and limitations. Explain that JSON retains complete audit details. Independently verify the seeded C manifest:

~~~powershell
.\.venv\Scripts\python.exe scripts/verify_manifest.py output/json/C_gaps_conflicts-manifest.json
~~~

Expected: two VERIFIED lines and exit code 0. Do not edit real vault files for a live tampering demonstration; automated tests use isolated synthetic copies and confirm a mismatch is detected.

**4:15–5:00 — Validation and boundaries.** Show `docs/VALIDATION.md` and `output/smoke-results.json`. State: “30 automated tests pass; the three scenarios and browser workflow were checked. A one-person exploratory pilot is documented; the broader evaluation remains pending.” Show the ready-to-run [Anurag/Sangram pilot](docs/EVALUATION_PILOT.md). Explain local-only use, supported formats and no certification, drift estimation or causal graph. Close with the team credits.

## Emergency fallback

- If a live import/correction stalls, switch to the seeded A case, already corrected by +73 seconds. State clearly that it was prepared by the reproducible smoke.
- If the browser or API fails, open `output/pdf/A_conflicting_clocks-report.pdf`, `B_cross_source-report.pdf` and `C_gaps_conflicts-report.pdf`. The JSON counterparts and manifests are in `output/json/`. Present them as saved verified run artifacts, not a successful live action.
- Browser screenshots are in `output/browser/` for desktop/tablet/mobile and source inspection. Do not claim a failed action passed.
- Check `.alibi/backend.stderr.log` and `.alibi/frontend.stderr.log`. Restart only the identified ALIBI process; use direct commands above. Do not reinstall dependencies during the talk.
- If hashing fails, stop claiming integrity for that file and display the discrepancy. Keep the original unchanged.

## Credits

Developed by Anurag Deb and Sangram Keshari Patra

Mentored by Prof. Partha Chakraborty

Anurag Deb — Team Lead & Full-Stack Developer

Sangram Keshari Patra — Backend Developer

Prof. Partha Chakraborty — Faculty Mentor

A one-person exploratory pilot is documented; the broader evaluation remains pending. See README and the validation record for implementation limitations.
