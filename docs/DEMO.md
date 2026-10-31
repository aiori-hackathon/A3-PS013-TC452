# Five-minute demonstration

The current release handoff is [DEMO_READY.md](../DEMO_READY.md), including verified Windows PowerShell 5.1 commands, all three scenarios and emergency fallbacks. Use that guide for presentation.

Start with `powershell.exe -NoProfile -File scripts/start.ps1`, then open http://127.0.0.1:5173. Optional: run `.\.venv\Scripts\python.exe scripts/smoke.py` to create all three labeled synthetic investigations and export reports. Every smoke run creates new investigations intentionally.

**0:00-0:45 / Create and preserve.** Create `Demo / conflicting clocks`. Import `datasets/A_conflicting_clocks/web.log`, source `Web gateway`, timezone `UTC`, no year needed, correction `0`. Show the preserved SHA-256 and parsed count.

**0:45-1:30 / Make assumptions visible.** Import the matching `auth.log`, source `Linux host A`, timezone `UTC`, year `2026`, initially correction `0`. On Timeline, the host events appear 73 seconds early. In Evidence vault, correct the auth file by `+73` seconds, uncertainty `2`, with reason `Known synthetic clock offset; two-second demonstration bound`. Emphasize that this is fixture ground truth, not an inferred real-world claim.

**1:30-2:30 / Reconstruct and inspect.** Search `R7`, filter by source, inspect a source record, and show original, UTC and corrected timestamps, the uncertainty interval, line/byte provenance and freshly verified original. Shared request IDs are associations only: this fixture does not establish that SSH and HTTP records denote the same event. Do not approve anchor calibration for this fixture merely because IDs match.

**2:30-3:30 / Challenge the record.** Select the seeded `SYNTHETIC / C gaps conflicts` investigation. Its two files contain eight records: three events and five gaps. Show invalid UTF-8, a malformed date, unsupported records and a blank line. Inspect the reused ID with different HTTP statuses and the backwards source timestamp. Explain why neither observation proves malicious activity or unseen missing events.

**3:30-4:30 / Verify and export.** Verify all files; download PDF, JSON and integrity manifest. In a terminal, independently verify an exported manifest:

```powershell
.\.venv\Scripts\python.exe scripts/verify_manifest.py output/json/C_gaps_conflicts-manifest.json
```

**4:30-5:00 / Show validation and boundaries.** Show `python -m pytest -q`, the three-scenario smoke result, and the browser test. Show `docs/EVALUATION.md`: human manual-versus-assisted timing is pending. Explain local-only scope, supported formats, explicit assumptions, and no forensic certification.

The optional anchor workflow is under **Evidence vault → Correct clock → Anchor-based proposal**. Use only sources that independently record the same events, a justified reference clock, and negligible systematic latency. Tests contain a separate same-event fixture; the required scenario A intentionally demonstrates why shared IDs alone are insufficient.
