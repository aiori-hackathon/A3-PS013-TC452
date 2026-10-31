<div align="center">

# ALIBI<span>.</span>

### Every incident has a story. Every story needs an ALIBI.

**An evidence-first cybersecurity incident reconstruction framework.**

<sub>AIORI Hackathon 3 &nbsp;·&nbsp; Cybersecurity &nbsp;·&nbsp; PS-013 &nbsp;·&nbsp; Team EXPOSE</sub>

<sub><code>A3-PS013-TC452</code></sub>

<br><br>

[![Watch introduction](https://img.shields.io/badge/Watch_the_Introduction-D92332?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/RhR5dDCjA2M)
[![Read proposal](https://img.shields.io/badge/Read_the_Proposal-242B36?style=for-the-badge&logo=readthedocs&logoColor=white)](./ALIBI_AIORI3_Proposal.pdf)

<br>

[![Watch ALIBI — Team EXPOSE project introduction](https://img.youtube.com/vi/RhR5dDCjA2M/hqdefault.jpg)](https://youtu.be/RhR5dDCjA2M)

<sub>▶ Watch our orientation video: the problem, proposed approach, and team responsibilities.</sub>

</div>

---

### The problem isn't missing data. It's conflicting evidence.

During an incident, a Linux host, a web application, and a firewall may each record part of the same story. Their formats differ, their clocks may disagree, and some records may be missing. Sorting timestamps alone can make the sequence look certain when it isn't.

**ALIBI proposes a local, offline-first workbench to reconstruct the most defensible account of an incident — and show where the evidence runs out.**

### One incident. Two very different stories.

| Source | Raw timestamp (UTC) | Observed event |
|:--|:--|:--|
| Application | `04:42:54` | Authentication success, request `R7` |
| Web server | `04:44:07` | Login request, request `R7` |

A naïve sort places the success **before** its matching request. In our **synthetic** example, repeated matching request IDs support an estimated **+73-second application-clock correction**. ALIBI would retain both the original timestamp and a corrected *interval*, including uncertainty — not silently rewrite the record or claim that every ordering is proven.

> **Our principle:** Evidence first. Assumptions last.

---

## The proposed ALIBI framework

```mermaid
flowchart LR
  P["01 · PRESERVE"] --> C["02 · CALIBRATE"] --> R["03 · RECONSTRUCT"] --> H["04 · CHALLENGE"] --> V["05 · VERIFY"]
  classDef step fill:#15232b,stroke:#2dd4bf,color:#ffffff,stroke-width:1px;
  class P,C,R,H,V step;
```

| Stage | What it means |
|:--|:--|
| **Preserve** | Keep original logs, their SHA-256 hashes, and source references. |
| **Calibrate** | Normalize to UTC; propose clock corrections only when supported by matching evidence. |
| **Reconstruct** | Build a searchable timeline and evidence-backed event relationships. |
| **Challenge** | Surface uncertain ordering, contradictory records, and parsing or coverage gaps. |
| **Verify** | Trace important findings back to the exact preserved evidence. |

### System at a glance

```mermaid
flowchart TB
  S["Linux · Web · Network logs"] --> I["Evidence intake"]
  I --> E[("Original evidence + SHA-256 manifest")]
  I --> P["Parsers + source provenance"]
  P --> N["UTC normalization + clock models"]
  N --> R["Reconstruction engine"]
  R --> T["Searchable timeline + event relationships"]
  R --> G["Gaps + contradictions + uncertainty"]
  E --> X["Report + verifiable evidence references"]
  T --> X
  G --> X
  classDef source fill:#263746,stroke:#7a93a8,color:#ffffff;
  classDef core fill:#123239,stroke:#2dd4bf,color:#ffffff;
  classDef out fill:#23314b,stroke:#8caef7,color:#ffffff;
  class S source;
  class I,P,N,R core;
  class E,T,G,X out;
```

<sub>Proposed MVP: Python / FastAPI, SQLite, format-specific log parsers, UTC normalization, SHA-256 integrity checks, and rule-based reconstruction. Diagrams show intended architecture, not a completed deployment.</sub>

---

## Proposal & project status

**[Read the ALIBI project proposal →](./ALIBI_AIORI3_Proposal.pdf)**

The proposal contains the research context, relevant prior work, optimization rationale, architecture, data flow, and development milestones. The README is intentionally brief; the PDF is the technical reference.

**Current status:** Proposal / initial development. The three synthetic scenarios and manual-versus-assisted triage benchmark are planned validation activities. No unmeasured performance gains are claimed.

---

## Team EXPOSE

| Member | Project role | Profile |
|:--|:--|:--|
| **Anurag Deb** | Team Lead & Full-Stack Developer | [LinkedIn ↗](https://www.linkedin.com/in/debanurag) |
| **Sangram Keshari Patra** | Backend Developer | [LinkedIn ↗](https://www.linkedin.com/in/sangramkpatra/) |
| **Prof. Partha Chakraborty** | Faculty Mentor | [LinkedIn ↗](https://www.linkedin.com/in/partha-chakraborty-bb506638/) |

<div align="center">

---

**ALIBI.** &nbsp;·&nbsp; **TEAM EXPOSE** &nbsp;·&nbsp; `A3-PS013-TC452`

<sub>AIORI Hackathon 3 · 2026</sub>

*Every incident has a story. Every story needs an ALIBI. What's yours?*

</div>
