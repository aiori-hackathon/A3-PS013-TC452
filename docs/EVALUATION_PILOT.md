# Two-person human triage pilot

**PENDING.** No human timings have been supplied. Automated pipeline runtime is not investigator triage time.

## Prepare before timing

Record Windows/machine details, ALIBI commit, participant experience, prior exposure and interruptions. Both participants built ALIBI; disclose this. Use the same source bytes and machine configuration in both conditions. Start the app first.

Participants receive only this procedure, the assigned folder's two original files and the clock sheet. Do not open `evaluation/ANSWER_KEY.md`, `datasets/ground_truth.json`, previous reports or another participant's answers until **all** trials finish. No internet, AI assistance or collaboration during trials.

Create a blank answer file before each trial; substitute participant, scenario and condition:

~~~powershell
New-Item -ItemType Directory -Force output/pilot | Out-Null
Copy-Item docs/evaluation/answer-template.json output/pilot/Anurag-A-manual.json
~~~

## Counterbalanced assignments

| Round | Scenario | Anurag Deb | Sangram Keshari Patra |
| --- | --- | --- | --- |
| 1 | A | Manual | ALIBI-assisted |
| 2 | B | ALIBI-assisted | Manual |
| 3 | C | Manual | ALIBI-assisted |
| 4 | A | ALIBI-assisted | Manual |
| 5 | B | Manual | ALIBI-assisted |
| 6 | C | ALIBI-assisted | Manual |

Take a 15-minute break after round 3 without reviewing answers. This yields 12 real trials and six participant/scenario pairs, **not six independent participants**. If only rounds 1–3 finish, report six unpaired trials; do not pair different people/scenarios.

## Clock sheet — supplied equally to both conditions

Every folder contains `web.log` and `auth.log`.

| Folder under datasets/ | Settings |
| --- | --- |
| `A_conflicting_clocks` | Web explicit +05:30, correction 0. Auth assumed UTC, year 2026, known 73 seconds slow: correction **+73**. |
| `B_cross_source` | Web explicit +00:00; auth explicit -04:00; correction 0 for both. |
| `C_gaps_conflicts` | Web explicit +00:00; auth assumed UTC, year 2026; correction 0 for both. |

Use supplied uncertainty 0 for comparable scoring; this does not prove perfect clocks. Do not use optional anchor estimation: clock knowledge is supplied equally.

## Questions and deliverables

1. How many physical records exist and how many can be normalized?
2. What is each usable record's corrected UTC timestamp and `filename:line` reference? Sort chronologically and retain ties.
3. Which exact lines cannot be parsed, and why? Include blank lines and invalid encoding.
4. Are source times backward or outcomes different for a reused identifier?
5. Do original and copied/imported file hashes match? Save both full SHA-256 values per file.
6. In two or three sentences, what is established and what remains uncertain?

Save the completed JSON, a short text summary and integrity evidence under `output/pilot/`. Both conditions deliver the same factual content. Additional PDF formatting/export is outside the primary triage timer.

**Manual:** use a text editor, PowerShell and optionally calculator/spreadsheet. No ALIBI, its parsers, normalization scripts or reports. Copy files into a fresh trial folder; never edit originals. Compare source/copy hashes with `Get-FileHash -Algorithm SHA256 ... | Format-List Path,Hash`. Read with line numbers and include blank records. Inspect bad encoding using `Format-Hex -Path datasets/C_gaps_conflicts/auth.log`; editor replacement characters are not original bytes. Subtract 05:30 for +05:30 zones, add four hours for -04:00, then add 73 seconds only to A's auth records. Retain original times in notes and complete all answers.

**Assisted:** create a new investigation named `Pilot / participant / scenario / assisted`; never reuse seeded cases. Import files separately with distinct source labels and the clock sheet. Explain A's correction as `Supplied synthetic clock measurement`. Review timeline/search/filters, inspect source records and gaps, verify evidence and record full hashes. Complete the same JSON and summary. After stopping, download PDF/JSON/manifest as supporting artifacts.

## Timing

Startup, practice and blank-template copying occur before timing. Investigation, evidence copying, hashing and answer writing are timed. Start immediately before opening the assigned evidence; stop only when answers, summary and hashes are saved. Cap at 30 minutes; retain incomplete/capped trials. Record interruptions and use unadjusted elapsed time as primary.

~~~powershell
./.venv/Scripts/python.exe scripts/triage_evaluation.py trial --participant Anurag --scenario A_conflicting_clocks --mode manual --answers output/pilot/Anurag-A-manual.json
./.venv/Scripts/python.exe scripts/triage_evaluation.py trial --participant Sangram --scenario A_conflicting_clocks --mode assisted --answers output/pilot/Sangram-A-assisted.json
~~~

For later rounds substitute participant, folder identifier, mode and answer filename using the assignment table. Keep participant identifiers identical across paired conditions. First Enter starts; second Enter stops and reads the saved JSON.

Use UTF-8 JSON. Map `filename:line` to exact ISO timestamps such as `2026-10-28T04:44:07.000000Z` in `times`; `gap_count` must be an integer. Results append to `output/human-trials.csv`. Never insert simulated times. For a repeat use a new participant-session ID in **both** conditions; duplicate pairs are rejected.

## Scoring and comparison after all trials

Open [the answer key](evaluation/ANSWER_KEY.md). The harness scores exact timestamp strings and gap counts; review reasoning and hashes separately.

| Component | Score/report |
| --- | --- |
| Correct timestamps | A /6, B /6, C /3; list extra/missing records separately |
| Gaps | Correct count plus exact line/reason list; C needs all five |
| Integrity | Correct original and matching copy/import hash per file: /4 |
| Assumptions/provenance | /3: timezone/year; correct correction basis; references for all usable records |
| Review/restraint | /2: correct conflict assessment; no unsupported actor/causation/attack claim |

Report components separately. Accept either order of tied A records. Include incorrect, interrupted and incomplete trials.

~~~powershell
./.venv/Scripts/python.exe scripts/triage_evaluation.py compare
~~~

For each pair, saved seconds = manual − assisted; percentage reduction = 100 × (manual − assisted) / manual, only when manual > 0. Retain negatives: assisted was slower. The harness reports paired saved seconds and their median; calculate percentages from recorded values. Publish all six pairs beside accuracy and completion, not only favorable results.

**Limitations:** two developers, prior familiarity, repeated-case learning despite counterbalancing, tiny synthetic files, unequal scenario difficulty and manual reasoning scores. No statistical significance, population-wide time saving, independent validation or real-incident improvement is established. Until people actually perform these trials, the comparison is **PENDING**.
