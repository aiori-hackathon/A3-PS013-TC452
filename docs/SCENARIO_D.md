# Scenario D · Community services portal

Load a fresh investigation from the repository root with both services running:

~~~powershell
.\.venv\Scripts\python.exe scripts/seed_scenario_d.py
~~~

Select **SYNTHETIC / D realistic incident** and open **Investigation Brief** on the timeline. Repeated imports create new cases with a time suffix. Each uses the original fixture bytes. The generator can reproduce the three logs in another directory with `scripts/generate_scenario_d.py --out <directory>`; the separate ground truth lists corrected UTC for each physical line.

| Source | Time basis | Records | Result |
| --- | --- | ---: | --- |
| Portal web gateway · access.log | Explicit +05:30 | 20 | 20 events |
| Portal Linux host · auth.log | Supplied 2026 UTC, +90 s correction, ±2 s bound | 13 | 12 events, one truncated record |
| Service monitor · system.log | Explicit −04:00 | 7 | 7 events |

**19 November 2026, corrected UTC.** Routine requests and service checks span 05:00–05:09. At 05:01:50 the gateway records HTTP 401 on an administrative route. Several SSH failures from 203.0.113.24 precede an accepted key at 05:04:05. The engine pairs the latest failure with that acceptance. At 05:05:50 the gateway records a successful backup archive request. At 05:06:15 sudo records a tar version check. Other addresses appear throughout the case.

The existing rules return **five leads**: one authentication sequence, one cross-source IP group, and three observations covering the administrative path, backup archive and sudo command. On the authentication lead, inspect **auth.log line 8**. The original host clock reads 05:02:35. The supplied maintenance correction places it at 05:04:05 UTC, with a 05:04:03–05:04:07 interval. A monitor event has the same central timestamp. Their relative order remains unresolved.

An HTTP status alone cannot establish what data left the host. IP reuse cannot establish actor identity. The sudo record shows a version check. The unparseable auth line retains its original bytes and reference. These limitations travel with the records and case report.

In **Verify & export**, download **Export Complete Case**. Verify the downloaded package with `python scripts/verify_case.py <downloaded-zip>`. For the browser validation download:

~~~powershell
.\.venv\Scripts\python.exe scripts/verify_case.py output/regional/ALIBI_Scenario_D.zip
~~~
