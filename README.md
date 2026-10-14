# Project ALIBI: Evidence-First Incident Reconstruction Framework

### **AIORI-3 (Advanced Internet Operations Research in India)**\[cite: 1]

**Track:** Cybersecurity | **Problem Statement:** PS-013: Incident Timeline and Evidence Collection for Small Teams\[cite: 1]

**Team Code:** `A3-PS013-TC452` | **Team Name:** TEAM EXPOSE\[cite: 1]

\---

### **Official Video Presentations**

\---

\---

## Table of Contents

* [Executive Overview](https://www.google.com/search?q=#executive-overview)
* [The Problem \& The Naive Sorting Fallacy](https://www.google.com/search?q=#the-problem--the-naive-sorting-fallacy)
* [Core Philosophy: Evidence-First Forensics](https://www.google.com/search?q=#core-philosophy-evidence-first-forensics)
* [System Architecture \& UML Design](https://www.google.com/search?q=#system-architecture--uml-design)
* [Data Flow Architecture (DFD Level-1)](https://www.google.com/search?q=#data-flow-architecture-dfd-level-1)
* [Algorithmic Foundations](https://www.google.com/search?q=#algorithmic-foundations)
* [Anchor-Based Causal Clock Skew Calibration](https://www.google.com/search?q=#1-anchor-based-causal-clock-skew-calibration)
* [Temporal Uncertainty Intervals](https://www.google.com/search?q=#2-temporal-uncertainty-intervals)
* [Gap Ledger \& Contradiction Detection](https://www.google.com/search?q=#3-gap-ledger--contradiction-detection)
* [Byte-Range Cryptographic Provenance](https://www.google.com/search?q=#4-byte-range-cryptographic-provenance)



* [Comparative Feature Matrix](https://www.google.com/search?q=#comparative-feature-matrix)
* [Synthetic Evaluation \& Baseline Benchmarks](https://www.google.com/search?q=#synthetic-evaluation--baseline-benchmarks)
* [Project Roadmap \& Hackathon Milestones](https://www.google.com/search?q=#project-roadmap--hackathon-milestones)
* [Team \& Academic Credits](https://www.google.com/search?q=#team--academic-credits)
* [References \& Prior Art](https://www.google.com/search?q=#references--prior-art)

\---

## Executive Overview

**ALIBI** (*A Proposed Evidence-First Incident Reconstruction Framework*) is a lightweight, local, offline-first digital forensics workbench developed by **Team EXPOSE** for small, resource-constrained IT teams\[cite: 1]. When cyber attacks strike organizations lacking a dedicated Security Operations Center (SOC), responders face multi-source text logs with conflicting formats, drifted system clocks, unrecorded gaps, and missing evidence provenance\[cite: 1].

Conventional tools either demand multi-node infrastructure (Splunk, Elastic, Wazuh) or blindly trust timestamps, causing causal inversions\[cite: 1]. Rather than introducing another generic dashboard, ALIBI implements a mathematically grounded, defensible audit path:



$$\\text{Original Evidence} \\longrightarrow \\text{Supported Clock Model} \\longrightarrow \\text{Interval-Aware Events} \\longrightarrow \\text{Typed Relationships} \\longrightarrow \\text{Challenged Conclusions} \\longrightarrow \\text{Independently Verifiable Export}$$



\[cite: 1]

\---

## The Problem \& The Naive Sorting Fallacy

Small teams investigate breaches using terminal pipelines (`grep`, `awk`, `cut`, `sort`) and copy findings into spreadsheets\[cite: 1]. This process breaks evidentiary chain of custody and conceals clock skew errors\[cite: 1].

### Why Naive Sorting Fails

Converting timestamps to UTC resolves timezone notation differences, but **it does not correct inaccurate system hardware clocks**\[cite: 1]. If an unmanaged application server has drifted 73 seconds slow and an internal SSH bastion host is 88 seconds slow, standard timeline sorting produces an impossible chronology\[cite: 1]:

```
RAW LOG TIMESTAMPS:
• APP (Drifted -73s)  : 04:42:54Z          auth.success R72
• SSH (Drifted -88s)  : 04:43:31Z          Accepted :49812
• WEB (UTC+05:30)     : 10:14:07 +05:30    POST /login R72 (= 04:44:07Z)
• FIREWALL (Accurate) : 04:44:58Z          Flow allowed :49812

NAIVE CHRONOLOGICAL SORTING:
\[04:42:54Z] APP  ── auth.success R72
\[04:43:31Z] SSH  ── Accepted :49812
\[04:44:07Z] WEB  ── POST /login R72
\[04:44:58Z] FW   ── Allow :49812

RESULTING INVESTIGATION ERROR:
Application authentication and internal SSH access appear to occur BEFORE
the inbound HTTP web request and the perimeter firewall flow that enabled them!
The tool displays a confident but inverted story while hiding the uncertainty.

```

*Figure 1: The Causal Timestamp Inversion failure mode observed in multi-source logs\[cite: 1].*

\---

## Core Philosophy: Evidence-First Forensics

ALIBI rejects speculative narrative generation and destructive log normalization\[cite: 1]. It operates around five deterministic pipeline stages\[cite: 1]:

```
+-----------------------------------------------------------------------------------------------------------+
|                                      THE 5-STAGE ALIBI METHODOLOGY                                        |
+-----------------------------------------------------------------------------------------------------------+
|  1. PRESERVE   │ Ingest raw files immutably; compute SHA-256 digests; map exact byte coordinates.         |
|  2. CALIBRATE  │ Convert timezones to UTC; infer clock skew from repeated anchors; keep \[t\_min, t\_max].|
|  3. RECONSTRUCT│ Build searchable SQLite FTS5 timeline; construct typed, partial-order causality edges.   |
|  4. CHALLENGE  │ Run Challenge Engine; isolate parser failures; flag telemetry silences and conflicts.    |
|  5. VERIFY     │ Trace every claim to source file, byte offset, and cryptographic hash in the report.     |
+-----------------------------------------------------------------------------------------------------------+

```

*Figure 2: The five core stages of the ALIBI incident reconstruction lifecycle\[cite: 1].*

1. **PRESERVE:** Original evidence is stored in an immutable, read-only evidence vault\[cite: 1]. A master SHA-256 hash is computed at intake, and every parsed record retains byte/line offsets (`\[byte\_start, byte\_end]`) back to the raw disk file\[cite: 1].
2. **CALIBRATE:** Discovers reciprocal causal anchors across hosts (e.g., matching HTTP request IDs, identical TCP flow tuples) to calculate mathematically supported clock offsets ($\\Delta t$)\[cite: 1]. Events retain calibrated uncertainty windows ($\[t\_{\\min}, t\_{\\max}]$) instead of falsified point-in-time certainty\[cite: 1].
3. **RECONSTRUCT:** Organizes events into a unified, sub-millisecond searchable timeline powered by SQLite FTS5\[cite: 1]. Establishes deterministic, typed evidence edges (`TRIGGERED\_BY`, `CORRELATED\_NETWORK\_FLOW`, `AUTHENTICATED\_AS`) based on partial ordering concepts\[cite: 1].
4. **CHALLENGE:** Scans for anti-forensic activity, sequence-number disruptions, and missing records\[cite: 1]. Unparseable lines are quarantined as potential exploit payloads and logged to a dedicated *Gap Ledger* rather than silently dropped\[cite: 1].
5. **VERIFY:** Outputs verifiable PDF/JSON incident reports paired with standalone cryptographic verification manifests\[cite: 1]. Auditors can independently verify that claims map to unaltered raw bytes\[cite: 1].

\---

## System Architecture \& UML Design

ALIBI is architected with a strict local system boundary\[cite: 1]. It requires no continuous background daemons, external database services, or paid cloud APIs\[cite: 1].

```
+-------------------------------------------------------------------------------------------------------+
|                                      ALIBI LOCAL SYSTEM BOUNDARY                                      |
+-------------------------------------------------------------------------------------------------------+
|                                                                                                       |
|  \[ LOG FILE INTAKE ]                                                                                 |
|  ├── Linux Syslog / Auth.log (RFC 3164 / RFC 5424)                                                    |
|  ├── Apache / Nginx Combined Access Logs                                                              |
|  └── Extensible CSV / JSON Adapters                                                                   |
|             │                                                                                         |
|             ▼                                                                                         |
|  \[ EVIDENCE VAULT ]                                                                                  |
|  ├── Immutable Local Raw File Storage                                                                 |
|  └── Cryptographic SHA-256 Intake Hashes                                                              |
|             │                                                                                         |
|             ▼                                                                                         |
|  \[ PARSER \& PROVENANCE LAYER ] ────────────► \[ SQLITE + FTS5 STORAGE ]                             |
|  ├── Exact Byte/Line Offset Extractor        ├── Normalized Events Table                              |
|  └── Parser Gap \& Quarantine Ledger          ├── Full-Text Search (FTS5) Index                       |
|             │                                └── Clock Calibration Models                             |
|             ▼                                                 ▲                                       |
|  \[ TIME ENGINE ] ─────────────────────────────────────────────┤                                      |
|  ├── Timezone Normalization (ISO-8601 UTC)                    │                                       |
|  ├── Robust Constant-Offset Skew Estimator                    │                                       |
|  └── Interval Generator (\[t\_min, t\_max])                   │                                       |
|             │                                                 │                                       |
|             ▼                                                 │                                       |
|  \[ RECONSTRUCTION ENGINE ] ──────────────────────────────────┤                                       |
|  ├── Searchable Multi-Source Timeline Builder                 │                                       |
|  └── Deterministic Typed Relationship Rules                   │                                       |
|             │                                                 │                                       |
|             ▼                                                 │                                       |
|  \[ CHALLENGE MODULE ] ───────────────────────────────────────┘                                       |
|  ├── Silence \& Cadence Collapse Detector (Anti-Forensics)                                            |
|  └── Causal Order Contradiction Checker                                                               |
|             │                                                                                         |
|             ▼                                                                                         |
|  \[ PRESENTATION \& OUTPUT LAYER ]                                                                    |
|  ├── Local Interactive Web UI (FastAPI local service + Canvas/DOM Graph)                              |
|  └── Export Engine (Self-Verifying JSON Manifest + Evidentiary PDF Report)                            |
|                                                                                                       |
+-------------------------------------------------------------------------------------------------------+

```

*Figure 3: UML Component Architecture for Project ALIBI\[cite: 1].*

\---

## Data Flow Architecture (DFD Level-1)

The system maintains a strictly controlled dataflow where raw evidence is written once (`D1`) and never altered\[cite: 1]. Intermediate models require human-in-the-loop validation before application\[cite: 1].

```
                  +-----------------------------------------------+
                  |            E1: Lead Investigator              |
                  +-----------------------------------------------+
                     │ Raw Log Files              ▲ Timeline Views,
                     │                            │ Challenge Reports,
                     ▼                            │ Verified Exports
               \[ 1.0 ACQUIRE ] ─────────────► \[ 4.0 RECONSTRUCT ] ◄───┐
                     │ Raw Bytes                  ▲                     │
                     │ + SHA-256 Digest           │ Normalized          │
                     ▼                            │ Intervals \&        │
           ======================                 │ Typed Edges         │
           D1: ORIGINAL EVIDENCE                  │                     │
           (Raw bytes, SHA-256,                   │                     │
            source metadata)                      │                     │
           ======================                 │                     │
                     │                            │                     │
                     │ Raw stream                 │                     │
                     ▼                            │                     │
                \[ 2.0 PARSE ]                    │                     │
                     │ Events, coordinates,       │                     │
                     │ and parsing gaps           │                     │
                     ▼                            │                     │
           ======================                 │                     │
              D2: EVENT STORE                     │                     │
           (Normalized events,                    │                     │
            byte offsets, gaps)                   │                     │
           ======================                 │                     │
                     │                            │                     │
                     │ Uncalibrated records       │                     │
                     ▼                            │                     │
              \[ 3.0 CALIBRATE ] ────────► ======================       │
                     ▲                    D3: MODELS + RESULTS          │
                     │                     (Approved offsets,           │
                     │                      edges, contradictions)      │
                     │                    ======================        │
                     │ Proposed offsets              │                  │
                     │ \& review gate                │ Verified         │
                     │                               │ Manifest         │
           +--------------------+                    ▼                  │
           |   Flow Control:    |          +--------------------+       │
           | Investigator Gate  |          |   E2: Reviewer /   |       │
           | (Model Approval)   |          |      Mentor        |───────┘
           +--------------------+          +--------------------+

```

*Figure 4: Level-1 Data Flow Diagram (DFD) showing the immutable evidence path and investigator approval gate\[cite: 1].*

\---

## Algorithmic Foundations

### 1\. Anchor-Based Causal Clock Skew Calibration

Rather than forcing investigators to guess millisecond offsets, ALIBI searches across ingested logs for **causal anchor invariants**—pairs of distinct log entries that represent the same physical network interaction\[cite: 1]:

* **Application-Level Anchors:** Shared correlation identifiers such as an HTTP Request ID (`X-Request-ID: R72`) logged by both an edge proxy and an internal API microservice\[cite: 1].
* **Transport-Level Anchors:** Matching 4-tuple network handshakes (`src\_ip`, `src\_port`, `dst\_ip`, `dst\_port`) recorded by a boundary firewall and the target server's `auth.log` / `sshd` daemon\[cite: 1].

```
ANCHOR IDENTIFICATION \& SKEW RESOLUTION:

Step 1: Discover shared tokens across independent hosts
  • WEB Proxy logs  : 04:44:07Z POST /login R72
  • APP Server logs : 04:42:54Z auth.success R72
  ──> Time Delta: 04:44:07Z - 04:42:54Z = +73 seconds drift on APP host\[cite: 1].

Step 2: Discover flow tuples
  • FIREWALL logs   : 04:44:58Z ALLOW :49812 -> :22
  • SSH Daemon logs : 04:43:31Z Accepted publickey :49812
  ──> Time Delta: 04:44:58Z - 04:43:31Z = +88 seconds drift on SSH host\[cite: 1].

Step 3: Multi-Anchor Requirement \& Approval Gate
  ALIBI rejects single-match calibration to prevent noise artifacts\[cite: 1]. 
  The engine requires recurring anchor support and presents proposed 
  offsets to the investigator for manual approval before applying calibration\[cite: 1].

```

### 2\. Temporal Uncertainty Intervals

Real-world systems experience variable transmission latency, OS buffering, and scheduling jitter. ALIBI abandons artificial pinpoint timestamps for calibrated events, assigning each an explicit confidence window $\[t\_{\\min}, t\_{\\max}]$\[cite: 1]:

```
CALIBRATED TIMELINE WITH UNCERTAINTY BOUNDS:

Time Window (UTC)     Host   Event Description                   Status
04:44:05Z - 04:44:09Z APP    auth.success R72 (calibrated +73s)  CONFIDENT: WEB -> APP\[cite: 1]
04:44:06Z - 04:44:08Z WEB    POST /login R72 (reference UTC)     CONFIDENT: WEB -> APP\[cite: 1]
04:44:56Z - 04:45:00Z FW     Allow :49812 (reference UTC)        UNCERTAIN: FW vs SSH\[cite: 1]
04:44:57Z - 04:45:01Z SSH    Accepted :49812 (calibrated +88s)   UNCERTAIN: FW vs SSH\[cite: 1]

```

* **Confident Deductions:** The `WEB` request demonstrably preceded and caused the `APP` authentication; the entire web-application interaction preceded the `SSH` lateral movement\[cite: 1].
* **Surfaced Uncertainty:** Because the calibrated windows for `FW` (04:44:56–04:45:00) and `SSH` (04:44:57–04:45:01) overlap by 3 seconds, ALIBI explicitly highlights the temporal ambiguity to the investigator rather than guessing an arbitrary order\[cite: 1].

### 3\. Gap Ledger \& Contradiction Detection

Traditional log tools only index received events. ALIBI monitors the **negative space** of logs to detect tampering and blind spots\[cite: 1]:

* **Cadence Collapse Analysis:** Identifies broken background periodicities (e.g., cron jobs, health checks, DHCP renewals)\[cite: 1]. If an application server normally emits 4 log events per minute and experiences 0 events between `04:45:10Z` and `04:52:10Z`, ALIBI inserts an explicit **"Telemetry Gap Event"** into the timeline\[cite: 1].
* **Parser Failure Quarantine:** Malformed lines containing exploit injections (such as `${jndi:...}`, raw binary shellcode, or non-RFC URL paths) are not dropped\[cite: 1]. They are flagged, quarantined, and inserted into the incident report under the **Parser Gap Ledger**\[cite: 1].

### 4\. Byte-Range Cryptographic Provenance

To ensure legal admissibility and support third-party audit verification, ALIBI links every derived finding to raw disk evidence\[cite: 1]:

* **Ingestion Digest:** Computes an immediate SHA-256 hash across the raw log file upon intake\[cite: 1].
* **Byte Coordinates:** Retains exact slice offsets `\[start\_byte, end\_byte]` for every parsed event\[cite: 1].
* **Verification Proof:** Exported reports include an audit manifest allowing an auditor to execute a verification script that hashes the specified byte slices against the raw file to prove the evidence was not manipulated\[cite: 1].

\---

## Comparative Feature Matrix

|Feature / Capability|Enterprise SIEM (Splunk, Elastic)|Endpoint Security (Wazuh)\[cite: 1]|Forensic Timeline (Timesketch / Plaso)\[cite: 1]|Project ALIBI (Team EXPOSE)\[cite: 1]|
|-|-|-|-|-|
|**Operating Footprint**|Massive multi-node cluster|Multi-node manager/agent\[cite: 1]|Heavy multi-container stack\[cite: 1]|**Zero-footprint, local single-binary/script**\[cite: 1]|
|**Pre-Incident Setup**|Requires persistent agents|Requires persistent agents\[cite: 1]|Offline / Post-incident\[cite: 1]|**Zero pre-installed agent requirements**\[cite: 1]|
|**Clock Skew Handling**|Assumes synchronized NTP|Real-time agent ingestion\[cite: 1]|Manual global user offset only\[cite: 1]|**Anchor-based causal calibration**\[cite: 1]|
|**Precision Model**|Rigid scalar timestamp|Rigid scalar timestamp|Rigid scalar timestamp|**Temporal uncertainty intervals ($\[t\_{\\min}, t\_{\\max}]$)**\[cite: 1]|
|**Negative Space Telemetry**|Silent (renders empty white space)|Silent / manual alert rule|Silent (only displays extracted records)|**Automated Gap Ledger \& cadence monitoring**\[cite: 1]|
|**Parsing Failures**|Dropped to ingest error log|Dropped or discarded|Dropped to unparsed log file|**Quarantined as potential exploit payloads**\[cite: 1]|
|**Evidence Provenance**|Raw log detached from index|Encrypted manager database|Indexed into OpenSearch indices|**Direct byte/line offsets to raw SHA-256 source**\[cite: 1]|

\---

## Synthetic Evaluation \& Baseline Benchmarks

Project ALIBI is evaluated against three synthetic enterprise breach scenarios to benchmark investigative performance\[cite: 1]:

```
+----------------------------------------------------------------------------------------------------------+
|                                    SYNTHETIC TEST SUITE (PS-013)                                         |
+----------------------------------------------------------------------------------------------------------+
|  INCIDENT 1: Multi-Host Lateral Movement with Clock Drift                                                |
|  • Attack Chain: Web vulnerability exploitation -> Lateral SSH pivot -> DB exfiltration.                 |
|  • Injected Flaw: Server A (+73s drift), Server B (+88s drift) relative to edge firewall\[cite: 1].      |
|  • Target Metric: Resolves inverted event order automatically via Request-ID/Flow anchors\[cite: 1].     |
|----------------------------------------------------------------------------------------------------------|
|  INCIDENT 2: Anti-Forensics \& Telemetry Silence (Negative Space)                                        |
|  • Attack Chain: Privilege escalation -> Daemon termination (`systemctl stop rsyslog`) -> Log wipe.      |
|  • Injected Flaw: 7-minute telemetry void (04:45:10Z to 04:52:10Z) across authentication logs\[cite: 1]. |
|  • Target Metric: Autodetects background cadence collapse and logs gap anomaly to ledger\[cite: 1].      |
|----------------------------------------------------------------------------------------------------------|
|  INCIDENT 3: Obfuscated Exploit Injection \& Parsing Breakdown                                           |
|  • Attack Chain: Log4Shell / Path Traversal injecting raw binary, null bytes, and multiline strings.     |
|  • Injected Flaw: Exploit breaks standard RFC 3164/Common Log Format parsers.                            |
|  • Target Metric: Captures payload via Quarantine Stream without dropping or crashing pipeline\[cite: 1].|
+----------------------------------------------------------------------------------------------------------+

```

*Figure 5: The three synthetic validation incident scenarios mandated under PS-013\[cite: 1].*

### Baseline Comparison Protocol

In compliance with PS-013 requirements, ALIBI’s performance is validated against a manual baseline investigation\[cite: 1]:

* **Manual Baseline:** Responders utilize standard command-line tools (`grep`, `awk`, `sort`) and spreadsheet software to reconstruct Incident 1\[cite: 1].
* **ALIBI Automated Workflow:** Ingestion, anchor detection, model confirmation, and report generation via ALIBI\[cite: 1].
* **Evaluation Metrics:** Time to Root-Cause Identification (minutes), False Order Rate (number of inverted causal pairs), and Provenance Integrity Verification (percentage of findings traceable to raw file hashes)\[cite: 1].

\---

## Project Roadmap \& Hackathon Milestones

The team is executing a six-phase delivery schedule targeting the technical demonstration on **October 29, 2026**\[cite: 1]:

```
+-------------------------------------------------------------------------------------------------------+
|                                  ENGINEERING SPRINT ROADMAP (OCT 2026)                                |
+-------------------------------------------------------------------------------------------------------+
|  OCT 12 - 15  │ PHASE 1: FOUNDATION                                                                   |
|               │ Evidence vault, raw file ingestion, SHA-256 computation, baseline parsers\[cite: 1].  |
|---------------+---------------------------------------------------------------------------------------|
|  OCT 16 - 19  │ PHASE 2: REQUIRED TIMELINE                                                            |
|               │ UTC normalization, manual offset support, SQLite FTS5 searchable timeline\[cite: 1].  |
|---------------+---------------------------------------------------------------------------------------|
|  OCT 20 - 23  │ PHASE 3: TEMPORAL MODEL                                                               |
|               │ Anchor calibration solver, \[t\_min, t\_max] intervals, typed edge logic\[cite: 1].   |
|---------------+---------------------------------------------------------------------------------------|
|  OCT 24 - 26  │ PHASE 4: CHALLENGE \& PROOF                                                           |
|               │ Gap/contradiction detector, report generator, 3 synthetic incident corpora\[cite: 1]. |
|---------------+---------------------------------------------------------------------------------------|
|  OCT 27 - 28  │ PHASE 5: VALIDATE \& BENCHMARK                                                        |
|               │ Integration testing, manual baseline triage time-trial, demo rehearsal\[cite: 1].     |
|---------------+---------------------------------------------------------------------------------------|
|  OCT 29, 2026 │ PHASE 6: TECHNICAL SHOWCASE                                                           |
|               │ Final prototype presentation to AIORI-3 jury and evaluators\[cite: 1].                |
+-------------------------------------------------------------------------------------------------------+

```

*Figure 6: Development timeline for Project ALIBI\[cite: 1].*

> \*\*MVP Gate Policy:\*\* Mandatory requirements of PS-013 must be completely satisfied and validated before implementing optional extensions (such as cryptographic signing or constrained AI narration)\[cite: 1].

\---

## Installation \& Quickstart

### Prerequisites

* Python 3.12+\[cite: 1]
* Modern web browser (Chrome, Firefox, Safari, or Edge)
* Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Team-EXPOSE/ALIBI-Forensics.git
cd ALIBI-Forensics

# Initialize virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Launch the ALIBI local service
python -m alibi.server --host 127.0.0.1 --port 8000

```

Navigate to `\[http://127.0.0.1:8000](http://127.0.0.1:8000)` to access the local investigation workbench.

### Basic CLI Usage

```bash
# 1. Ingest evidence into the immutable vault
alibi ingest --vault ./case\_001\_vault /var/log/auth.log /var/log/nginx/access.log

# 2. Run anchor calibration solver across ingested logs
alibi calibrate --vault ./case\_001\_vault --auto-anchor

# 3. Detect telemetry gaps and parse failures
alibi challenge --vault ./case\_001\_vault

# 4. Export self-verifying incident report
alibi export --vault ./case\_001\_vault --format pdf --output incident\_report\_001.pdf

```

\---

## Team \& Academic Credits

**Team EXPOSE** (`A3-PS013-TC452`), participating in the **AIORI-3 Hackathon** under Track **Cybersecurity**\[cite: 1]:

* **Anurag Deb** — Core Engineering, Forensic Parsers \& Algorithmic Design\[cite: 1]
* **Sangram Keshari Patra** — System Architecture, Evidence Lineage \& Full-Stack Implementation\[cite: 1]
* **Faculty Mentor:** **Prof. Partha Chakraborty**, Institute of Engineering and Management (IEM), Kolkata\[cite: 1]

\---

## References \& Prior Art

1. **K. Kent, S. Chevalier, T. Grance, and H. Dang**, *Guide to Integrating Forensic Techniques into Incident Response*, NIST SP 800-86, National Institute of Standards and Technology, Aug. 2006. doi: [10.6028/NIST.SP.800-86](https://www.google.com/search?q=https://doi.org/10.6028/NIST.SP.800-86)\[cite: 1]
2. **A. Nelson et al.**, *Incident Response Recommendations and Considerations for Cybersecurity Risk Management*, NIST SP 800-61 Rev. 3, Apr. 2025. doi: [10.6028/NIST.SP.800-61r3](https://www.google.com/search?q=https://doi.org/10.6028/NIST.SP.800-61r3)\[cite: 1]
3. **Timesketch Team**, *Timesketch: Collaborative forensic timeline analysis*, [https://timesketch.org/](https://timesketch.org/)\[cite: 1]
4. **Plaso Development Team**, *Plaso: log2timeline super-timeline extraction engine*, [https://plaso.readthedocs.io/](https://www.google.com/search?q=https://plaso.readthedocs.io/)\[cite: 1]
5. **Wazuh Inc.**, *Wazuh System Architecture Documentation*, [https://documentation.wazuh.com/](https://www.google.com/search?q=https://documentation.wazuh.com/)\[cite: 1]
6. **L. Lamport**, *"Time, Clocks, and the Ordering of Events in a Distributed System"*, *Communications of the ACM*, 21(7), pp. 558–565, Jul. 1978. doi: [10.1145/359545.359563](https://www.google.com/search?q=https://doi.org/10.1145/359545.359563)\[cite: 1]
7. **J. Kelsey, J. Callas, and A. Clemm**, *Signed Syslog Messages*, RFC 5848, IETF, May 2010. [https://www.rfc-editor.org/rfc/rfc5848](https://www.google.com/search?q=https://www.rfc-editor.org/rfc/rfc5848)\[cite: 1]
8. **BaggaByte**, *Chronos: Automated Multi-Source Forensic Timeline Parser \& Incident Reconstruction Engine*, GitHub, Oct. 2026. [https://github.com/BaggaByte/chronos](https://www.google.com/search?q=https://github.com/BaggaByte/chronos)\[cite: 1]
9. **AIORI Hackathon 3 Committee**, *Problem Statement PS-013: Incident Timeline and Evidence Collection for Small Teams*, Advanced Internet Operations Research in India, 2026\[cite: 1].

