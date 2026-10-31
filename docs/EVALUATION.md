# Exploratory human triage pilot

## Method and provenance

This report records a genuine exploratory observation supplied by project participant **Anurag Deb**. It is a participant-reported result, not an independently witnessed or controlled trial. The task used `A_conflicting_clocks`: identify three authentication events and calculate their corrected UTC timestamps using a supplied **+73-second** correction.

The manual condition occurred first. The ALIBI-assisted condition followed, after the correct timestamps were known. The original observations below are preserved, including the manual arithmetic error. No rows were manufactured in `output/human-trials.csv` or the existing interactive timer harness.

## Recorded observations

| Measure | Manual investigation | ALIBI-assisted investigation |
| --- | ---: | ---: |
| Elapsed seconds | **62.000** | **26.029** |
| Relevant events identified | **3/3** | **3/3** |
| Exact timestamp accuracy during timed trial | **0/3** | **3/3** |
| Correction actually applied | +77 seconds, by mistake | Supplied +73 seconds |

| Event | Original auth UTC | Original timed manual answer | Assisted answer | Final reviewed correct UTC |
| --- | --- | --- | --- | --- |
| R7 / auth.log:1 | 04:42:54 | **04:44:11** | 04:44:07 | **04:44:07** |
| R8 / auth.log:2 | 04:43:54 | **04:45:11** | 04:45:07 | **04:45:07** |
| R9 / auth.log:3 | 04:44:54 | **04:46:11** | 04:46:07 | **04:46:07** |

All dates are 28 October 2026, with UTC and year supplied for the yearless auth source. Each manual answer was four seconds late because the participant added 77 instead of 73 seconds. Final reviewed correctness is 3/3, but that review does **not** retrospectively change the manual timed score of 0/3.

## Observed comparison

- Time saved: `62.000 − 26.029 = 35.971 seconds`.
- Observed time ratio: `62.000 / 26.029 = 2.382x`, approximately **2.38x**.
- Observed reduction: `100 × 35.971 / 62.000 = 58.018%`, approximately **58.0%**.

Both methods located all three relevant events. ALIBI applied the supplied correction correctly; the manual trial contained an arithmetic error. This specific observation illustrates the potential value of automatic timestamp correction in reducing manual arithmetic mistakes. It does **not** establish a general 2.38x productivity improvement.

## Limitations

One participant and one synthetic scenario were measured. Trials were sequential rather than randomized or counterbalanced. The participant helped develop ALIBI, the assisted condition followed the manual condition, and correct answers were already known before assisted timing. Learning and familiarity bias are therefore substantial. These results are neither statistically significant nor representative of independent investigators or real incidents.

This narrow three-auth-event task is different from the complete six-event A investigation and the broader manual-versus-assisted protocol. It must not be inserted into that harness as if all its tasks, gap review, hashing and report deliverables had been completed. The broader two-person, three-scenario comparison remains pending.

## Reproducible references

- [Original synthetic auth evidence](../datasets/A_conflicting_clocks/auth.log) and [independent ground truth](../datasets/ground_truth.json).
- [Scenario generator](../scripts/generate_datasets.py) and [interactive timer/scorer](../scripts/triage_evaluation.py).
- [Broader counterbalanced protocol](EVALUATION_PILOT.md), [reviewer answer key](evaluation/ANSWER_KEY.md) and [fixture hashes](evaluation/fixture-hashes.json).

The broader protocol and answer key are retained because they support reproducibility and distinguish completed exploratory observations from unperformed evaluation.
