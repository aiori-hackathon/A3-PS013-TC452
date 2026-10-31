# Reviewer answer key — do not open during timed trials

Independent truth: `datasets/ground_truth.json`. All times below are **28 October 2026 UTC**; JSON must use full ISO strings, e.g. `2026-10-28T04:44:07.000000Z`. No human results appear here.

## A — conflicting clocks

Six physical records, six events, zero gaps, no deterministic source-order/status conflicts.

| Source line | Original time | Corrected UTC |
| --- | --- | --- |
| web.log:1 | 10:14:07 +05:30 | 04:44:07 |
| auth.log:1 | 04:42:54 assumed 2026 UTC | 04:44:07 |
| web.log:2 | 10:15:07 +05:30 | 04:45:07 |
| auth.log:2 | 04:43:54 assumed 2026 UTC | 04:45:07 |
| web.log:3 | 10:16:07 +05:30 | 04:46:07 |
| auth.log:3 | 04:44:54 assumed 2026 UTC | 04:46:07 |

Subtract 05:30 for web; add the supplied 73 seconds to auth. Three tied pairs remain without established within-pair order. R7/R8/R9 and IP 198.51.100.24 are associations. SSH and HTTP are not proven to be the same event; IDs alone do not justify automatic calibration, actor identity or causation.

## B — cross-source reconstruction

Six physical records, six events, zero gaps and no deterministic conflicts.

| Ordered source line | UTC | Observation |
| --- | --- | --- |
| web.log:1 | 04:40:00 | GET /admin, HTTP 401 |
| auth.log:1 | 04:41:00 | Failed SSH password |
| web.log:2 | 04:42:00 | POST /login, HTTP 200 |
| auth.log:2 | 04:43:00 | Accepted public key for backup |
| web.log:3 | 04:44:00 | GET /backup.tar, HTTP 200 |
| auth.log:3 | 04:45:00 | sudo /usr/bin/tar |

Auth's -04:00 requires adding four hours; correction is zero. IP 203.0.113.8 and temporal sequence do not prove one actor or data theft.

## C — gaps/conflicts

Eight physical records: three events, **five gaps**.

| Ordered source line | UTC |
| --- | --- |
| web.log:2 | 04:49:00 |
| web.log:1 | 04:50:00 |
| auth.log:1 | 04:52:00 |

| Gap | Reason |
| --- | --- |
| web.log:3 | Invalid day 99 |
| web.log:4 | Unsupported/missing timestamp and request fields |
| web.log:5 | Blank physical record |
| auth.log:2 | Unsupported appliance record |
| auth.log:3 | Invalid UTF-8 FF FE; preserve original bytes |

Two findings: web line 2's timestamp is earlier than line 1; identifier DUP is reused with HTTP 200 and 500. These require review, not an invented attacker or malicious intent. No unseen missing event is proven.

## Integrity and review

`fixture-hashes.json` has the six exact source SHA-256 values. Compare originals and copies/imports. If hashes differ, document the discrepancy rather than silently replacing evidence. Git line-ending conversion is disabled for log fixtures.

Use the component rubric in `../EVALUATION_PILOT.md`. Check references, assumptions, gaps, hashes and cautious conclusions. Record omissions/extras/incomplete tasks; accept either tied order in A. Keep reviewer notes separate from timed answers.
