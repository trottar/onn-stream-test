---
memory_schema: 1
as_of: 2026-09-24
status: RULE OUTCOME 2026-09-24 (C4-D1, pre-registered rule applied as written) — BUILD (static k+2 first); adaptive FEC NOT supported; C4 moves to a design task whose first step is a measured arm, queued behind C3 per the roadmap; nothing built, nothing adopted; adoption is the user's
---

# C4 — adaptive FEC: the pre-registered rule's outcome

Evidence: `../evidence/C4_D1_FEC_EVIDENCE_2026-09-24.md` (script, output
and input hashes in `../evidence/c4_d1_2026-09-24/`). Task:
`../handoffs/C4-D1_ADAPTIVE_FEC_EVIDENCE_TASK.md`. Roadmap: `docs/ROADMAP.md`
§C4.

## The rule (pre-registered in the task, before the analysis)

- **DEFER WITH EVIDENCE** if the extra recoverable loss under k+2 or 4+1 is
  under 2 packets/min at the corpus median **and** capacity pressure is
  absent.
- **BUILD (static k+2 first)** if a fixed alternative recovers ≥ 5
  packets/min more at the median with no pressure signal. Then it is a
  profile field, not adaptation.
- **BUILD ADAPTIVE** only if pressure is present and loss rises with it.

The "extra recoverable" figure is the task's own computation: an upper
bound, interleaving ignored.

## The numbers

The corpus is 38 adopted-build sessions of ≥ 5 min: 31 holds and 7
transition sessions.

| | now (8+1) | k+2 (8+2) | 4+1 |
| --- | ---: | ---: | ---: |
| post-FEC loss/min, median | **9.12** | — | — |
| extra recovered/min, **upper bound** (the rule's input) | — | **7.72** | **5.57** |
| extra recovered/min, point estimate (exact gap sizes) | — | 3.12 | 0.64 |
| parity overhead | 16.0 % | 32.1 % | 25.0-32.4 % |
| group completion delay (task's formula) | 9.8 ms | 9.8 ms | 4.9 ms |

**Capacity pressure (per-minute, 687 minutes).**

- **Not ABSENT**: rendered fps rho −0.73. That is what a lost packet costs
  the client.
- **Not PRESENT**: no monotone rise in the queue-depth or output-gap
  substitutes. The telemetry fields the task names are not logged per
  minute on this build; the substitutes are stated in the evidence.
- The load columns (host packets/s, bytes/s, largest frame) sit at rho
  −0.06 to +0.09.
- The warm-state subset reads PRESENT on the output-age substitute (46 → 59
  ms across the buckets, rho +0.11). It is not the rule's input.

## The outcome

| branch | holds? |
| --- | --- |
| DEFER WITH EVIDENCE | **no**: 7.72 / 5.57 ≥ 2, and pressure is not absent |
| **BUILD (static k+2 first)** | **yes**: 7.72 ≥ 5, and pressure is not PRESENT |
| BUILD ADAPTIVE | no: pressure is not present on the corpus |

**Outcome: BUILD (static k+2 first).** C4 does not close. It moves to a
design task for a **static parity-count profile field**. **Adaptive FEC**
(parity driven by conditions) has **no support in this evidence**: nothing
that measures load moves with the loss.

**One reading is needed to apply the rule.** "No pressure signal" is taken
as the rule's own "not PRESENT", because the corpus is neither ABSENT nor
PRESENT by its definitions. Read the other way ("not ABSENT"), no branch
holds and the rule does not decide.

**What the outcome does not establish**:

- **The bound is not a measurement.** The point estimate, 3.12/min, falls
  between the rule's 2 and 5.
- **k+2 doubles the parity packets, 16 % → 32 %, inside the same frame
  bursts.** `P5`/`P6` located the loss at the frame burst meeting the
  wireless queue, so a bigger burst could raise the loss that the second
  parity is meant to repair. Only a measurement answers that.

## What follows (a design task, not a change)

1. **Order.** `docs/ROADMAP.md` puts C4 "only after bitrate adaptation is
   stable". C3 is not (`C3.L4` is BLOCKED on the `C3.L3a` gate). So the
   design task is queued behind C3 and starts nothing now.
2. **Its first step is a measured arm.** It needs a companion relay change
   and a client decoder change (two parities per group), behind a profile
   field that defaults to today's 8+1. Then interleaved k+2 / 8+1 holds,
   cold and warm, scored on the close-out rows, with post-FEC loss/min the
   primary row. This is the same shape as `P6`/`P6a`.
3. **Adoption is the user's**, on that measurement, as with the cap,
   cushion and redundancy.

Nothing was built and nothing changed. The profile stays 8+1.

## The measured arm — `C4-M1`, 2026-09-25: NOT SHOWN (nothing adopted)

Record: `../evidence/C4_M1_FEC_ARM_2026-09-25.md`.
- **Step 0** (the C4-D1 corpus): interleaved 8+1 missed 40 % on one of
  three readings, so the arm built **8+2** (`xor8_2`: the v1 XOR parity
  unchanged plus a v2 Reed-Solomon Q) behind `PRIVYHUB_FEC_SCHEME`.
- **The night**, 3 B/A pairs, cool, low-loss:
  - the arm recovered 2-4× more packets and halved unrecoverable groups;
  - post-FEC loss was lower in only 1 of 3 pairs, with the A median at
    69 % of B's → **NOT SHOWN**;
  - the cost rows were within noise;
  - pre-FEC loss rose 2-3× under the arm: the extra parity sits in the
    same frame bursts.
- **Adoption is the user's call, and on this evidence there is nothing to
  adopt.** The profile stays 8+1 and the override is unset.
- A lossier or warm night is the one measurement that could change it.
