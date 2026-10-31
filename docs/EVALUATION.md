# Manual versus assisted triage protocol

**Release pilot:** Anurag and Sangram should follow [EVALUATION_PILOT.md](EVALUATION_PILOT.md), which specifies the two-person assignment, clock sheets, timing, answer template and reviewer key. The broader protocol below is retained for a later study with independent participants.

Status: **human measurements pending**. The automated smoke durations measure software processing and export only. They are not a manual baseline, investigator triage time, or evidence of a speedup. PS-013's human comparison remains open until real trials are recorded.

Use at least three participants who can read basic logs. Record participant pseudonyms, prior experience, machine/OS, tool versions, dataset hashes, trial order and interruptions in the study notes. Obtain consent for timing. Use synthetic data only.

1. Give each participant the two source files for one scenario, a clock sheet with the supplied timezone/year/offset assumptions, and the task below. Keep `datasets/ground_truth.json` hidden until scoring. Scenario A's host A clock is 73 seconds slow; all other supplied clocks have zero correction. Yearless records are from 2026 and use UTC. Explicit zones override assumptions.
2. Manual condition: use a text editor, spreadsheet, clock calculator and local SHA-256 tool. Do not use ALIBI or its parser. Preserve originals separately.
3. Assisted condition: use a fresh ALIBI investigation, import the same evidence with the same assumptions, inspect the timeline and gaps, verify hashes and export the report.
4. Counterbalance condition order across participants and rotate A/B/C. A repeat on the same case produces familiarity bias; use a washout interval and report this limitation. Do not present an unpaired comparison as a within-participant result.
5. Time from opening the source files through saving the answer and integrity/report deliverables. Record interruptions; keep all trials, including failures. Use the timer below. Do not substitute automated pipeline duration.
6. Required task: list every successfully normalized record by `filename:line`, give corrected UTC timestamps, list unparsed lines and reasons, identify observable conflicts, verify each source SHA-256, and provide a short incident account separating observations from hypotheses. No causal claim is required. No unseen event can be inferred from silence.
7. Save answer JSON with `times` (mapping from `filename:line` to UTC ISO timestamp with six fractional digits and `Z`) and `gap_count` (integer). Save the richer written findings, hashes, and report alongside it. The script scores timestamps and gap counts; a reviewer separately assesses provenance, assumptions, and unsupported claims.
8. Report each trial's elapsed time and accuracy, then paired differences and medians. Flag incomplete tasks. Avoid general performance or statistical-significance claims from this small dataset.

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/triage_evaluation.py trial --participant P01 --scenario A_conflicting_clocks --mode manual --answers output/P01-A-manual.json
.\.venv\Scripts\python.exe scripts/triage_evaluation.py trial --participant P01 --scenario A_conflicting_clocks --mode assisted --answers output/P01-A-assisted.json
.\.venv\Scripts\python.exe scripts/triage_evaluation.py compare
```

The interactive timer waits for a real human to start and finish. The comparison command reports pending when no results exist. Results are local in `output/human-trials.csv`; never prefill invented observations.
