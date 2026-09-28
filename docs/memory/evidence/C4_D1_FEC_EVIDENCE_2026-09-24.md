---
memory_schema: 1
as_of: 2026-09-24
status: C4-D1 DONE (offline) — 38 adopted-build sessions ≥ 5 min (31 holds, 7 transition); 8+1 recovers ~8.7/min at the median and leaves ~9.1/min; the residual is mostly two-packet gaps inside one group (55 % of exact single-gap windows), which k+2 restores; median extra recoverable, UPPER BOUND (the pre-registered computation) k+2 7.72/min, 4+1 5.57/min; point estimate k+2 3.12, 4+1 0.64; capacity pressure by the rule's letter neither ABSENT (rendered fps rho −0.73, loss's own effect) nor PRESENT (no rise in the queue-depth or output-gap substitutes); host offered load rho ≈ 0; rule outcome BUILD (static k+2 first) — a profile-field design task, not adaptive FEC; decision record decisions/C4_ADAPTIVE_FEC_2026-09-24.md
---

# C4-D1 — adaptive FEC, decided on the evidence on disk

Task: `handoffs/C4-D1_ADAPTIVE_FEC_EVIDENCE_TASK.md` (weekend queue item 2,
authorized by the user 2026-09-24). Decision:
`../decisions/C4_ADAPTIVE_FEC_2026-09-24.md`. Evidence:
`c4_d1_2026-09-24/`: the script `c4_d1_analyze.py` (method, substitutions
and rule in its docstring), its output `c4_d1_analysis.txt`, and the
SHA-256 of every input read (`inputs_sha256.txt`, 233 files).

**Scope.** Offline and read-only. There was no session and no companion,
client or profile change. Nothing under `logs/` was modified.

## What 8+1 is, and what the counters mean

From `companion/native_fec_relay.py` and `RtpH264Receiver.kt`:

- **One XOR parity per group of ≤ 8 data packets of one frame.** Groups
  never span frames, so a frame's last group is partial. The measured
  parity overhead is **16.0 %**, not the nominal 12.5 %, at 2.17 groups
  per frame.
- The client builds a group when its parity arrives and **recovers
  exactly one missing packet**.
- A group with ≥ 2 missing is pruned at 40 ms and counted
  `fec_unrecoverable_groups`.
- A group whose parity is lost is never seen.
- `lost_packets` and `forward_gap_events` are counted **after** recovery:
  a recovered packet is released in order into its hole. So each forward
  gap is a run of consecutive packets FEC did not restore.
- `lost_packets_in_resyncs` is restart loss and is excluded throughout.

## Population

- Every decoder report on the adopted build of ≥ 5 min: from `P6a`'s
  validation session V1 (`native_decoder_20260922_062613_928`) through
  rerun session 3.
- The reports carry no cap field, so the build is taken by date. No cap
  or VBV override is recorded after `P6a`. The audio arms of `P9`/`P9a`/
  `P10` vary only the audio path and are kept.
- **38 sessions: 31 holds, 7 transition sessions** (the smoke, S1's T1-T3,
  and reruns 1b, 2 and 3; rerun 2 from its journal-rebuilt copy). The
  table is `c4_d1_analysis.txt` §POPULATION.
- **Excluded**: the two deliberate link-drop runs (`R3b` N150, E30), and
  34 reports under 5 min, each listed with its reason.
- The heartbeat series (2 s, cumulative counters) was found for all 38,
  covering 97-100 % of each: 33,402 rows from the live log, its archive
  and every evidence copy, deduplicated.

## 1. What 8+1 recovers, and what it leaves

Per session, per minute of the report:

| | n | lost/min (post-FEC) | recovered/min | unrecoverable groups/min |
| --- | ---: | ---: | ---: | ---: |
| all | 38 | **9.12** | 8.67 | 2.39 |
| holds | 31 | 9.49 | 9.44 | 2.47 |
| transition | 7 | 4.29 | 4.58 | 0.87 |

**Post-FEC gap sizes.** They are exact in the 1,510 heartbeat windows that
hold exactly one gap event and no restart:

| b (packets) | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9-16 | > 16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| windows | 138 | **836** | 206 | 61 | 125 | 57 | 22 | 34 | 20 | 11 |
| % | 9.1 | **55.4** | 13.6 | 4.0 | 8.3 | 3.8 | 1.5 | 2.3 | 1.3 | 0.7 |

- **What 8+1 leaves is mostly a two-packet gap inside one group.** A 1+1
  split across two groups would have been recovered, so a residual
  two-packet gap sits in one group.
- **Those 36.6 % of lost packets** (in gaps of ≤ 2) are exactly what a
  second parity restores.
- The rest are runs of 3 to 91 packets, which no parity count of this
  shape restores whole.

**Alternatives, per the task's computation (upper bound, interleaving
ignored).** Per post-FEC gap of b packets, k+2 (two parities per 8-group)
restores at most min(b, 4) and 4+1 at most min(b, 2). This is summed over
2 s windows as min(L, 4G) and min(L, 2G).

| corpus median, per min | extra recovered, **upper bound** | point estimate (b ≤ 2 gaps; b = 1 and 1-in-7 of b = 2 for 4+1) | post-FEC loss would be (point) | parity overhead |
| --- | ---: | ---: | ---: | ---: |
| 8+1 (now) | — | — | 9.12 (actual) | **16.0 %** |
| **k+2** (8+2) | **7.72** | **3.12** | 5.19 | 32.1 % |
| **4+1** | **5.57** | 0.64 | 8.25 | 25.0-32.4 % |

Holds alone: k+2 has an upper bound of 8.01 and a point estimate of 3.26;
4+1 has 5.64 and 0.71. **The bound is not a measurement.** It is what the
task pre-registered, and the rule reads it. The point estimate counts only
what the exact gap sizes show k+2 restores for certain.

## 2. Is any of it capacity pressure?

**Minutes.** 687 full client minutes without a restart, 583 of them with
loss. Loss/min is set against every column that exists per minute.

**Substitutions.** `queue_depth`, `output_gap_ms`, `recent_fps`,
`interarrival_jitter_ms` and `send_call_avg/max_us` live only in the
latest-only `/diagnostics/stream-telemetry` snapshot. No per-minute series
of them exists on the adopted build, so substitutes are used:

- `recent_fps` → rendered fps.
- `queue_depth` → frames queued-not-rendered per minute.
- `output_gap_ms` → the largest `last_output_age_ms` at the 2 s beats.
- Jitter and send-call timing: **not available** per minute.

| column | rho | loss 0 / 1-5 / 6-20 / > 20 (bucket medians) | monotone rise |
| --- | ---: | --- | --- |
| rendered fps (for `recent_fps`) | **−0.73** | 60.0 / 60.0 / 59.9 / 59.9 | no |
| queued-not-rendered / min (for queue depth) | +0.12 | 0 / 0 / 0 / 1 | no |
| max output age at beats (for output gap) | +0.04 | 52 / 49 / 52 / 52 ms | no |
| host packets / s (offered load) | **+0.01** | 822 / 823 / 823 / 821 | no |
| host payload bytes / s | +0.09 | 876.9K / 876.9K / 877.0K / 876.9K | no |
| largest frame, packets | −0.06 | 76 / 76 / 76 / 76 | no |
| frames ≥ 40 packets / min | −0.02 | 128 / 131 / 131 / 140 | yes |
| Opal tx retries / min (255 t2 minutes) | +0.19 | 3,603 / 3,316 / 4,066 / 4,159 | no |

`tx_failed` tracks `tx_retries` one for one in these samples.

**Reading, per the pre-registered rule.**

- **Not ABSENT**: |rho| ≥ 0.3 on rendered fps (−0.73).
- **Not PRESENT**: neither the queue-depth nor the output-gap substitute
  rises across the buckets.
- Holds alone read the same (fps −0.72).
- Stated as fact, not as a re-reading: rendered fps is what a lost packet
  costs the client (a frame it cannot decode), so it falls with loss
  whatever the cause.
- **The columns that measure load read nothing.** Offered packets and
  bytes per second, and the largest frame, sit at rho −0.06 to +0.09 with
  flat buckets. The loss does not follow what the host sends.

## 3. The warm state (onn cpu-thermal ≥ 67.5 °C)

255 full minutes carry a t2 sample. They come from 16 sessions (T2, T3,
P10, the close-out and the S1 soak).

| | minutes | lost/min median (mean) | recovered/min median | minutes with a multi-packet gap | exact single gaps: b = 1 / 2 / ≥ 3 |
| --- | ---: | ---: | ---: | ---: | --- |
| warm | 165 | 6.0 (8.73) | **10.3** | 136 | 40 / 260 / 119 (max 91) |
| cool | 90 | 6.0 (11.60) | 6.1 | 73 | 13 / 105 / 75 (max 87) |

- **8+1 absorbs the warm state's extra loss.** Recovered/min is 10.3 warm
  against 6.1 cool, while post-FEC loss has the same median (6.0).
- **Warm minutes did have multi-packet gaps that 8+1 lost**: 136 of 165.
  Their shape is the corpus shape, mostly two-packet gaps.
- By the rule's letter, the warm minutes read **PRESENT**: the output-age
  substitute rises 46 / 52 / 53 / 59 ms across the loss buckets, at rho
  +0.11. So do the Opal retries (3,310 → 4,890, rho +0.21).
- Offered load stays flat there too (rho −0.05).
- This is the subset step 3 asks about. The rule's pressure input is step
  2's corpus reading (above).

## 4. Cost in latency

- The host series gives 814 packets/s on average, a mean interval of
  **1.229 ms**. So the task's group completion delay is:
  - 8+1 and 8+2: **9.8 ms**
  - 4+1: 4.9 ms
  - 16+2: 19.7 ms
- In practice a group never spans a frame, and each frame leaves as one
  unpaced burst. So parity follows its eighth packet by the burst's own
  spacing.
- **k+2 keeps the group size**, so it adds no completion delay. It adds
  one packet per group (+16 points of overhead), and that packet lands in
  the same frame burst.
- The client's measured gap hold peaks at 12-36 ms per session (`fec_max_hold_ms`;
  its timeout is 12 ms).

## The rule, applied as written

| branch | condition | here | holds |
| --- | --- | --- | --- |
| DEFER WITH EVIDENCE | extra < 2/min (k+2 or 4+1) AND pressure absent | 7.72 / 5.57; not absent | **no** |
| BUILD (static k+2 first) | a fixed alternative ≥ 5/min more AND no pressure signal | 7.72 ≥ 5; not PRESENT | **yes** |
| BUILD ADAPTIVE | pressure present AND loss rises with it | not present on the corpus | no |

**Outcome: BUILD (static k+2 first)**: a profile field, not adaptation.
C4 moves to a design task.

**Three facts sit beside the outcome.**

1. **The rule read the upper bound.** The point estimate at the median is
   3.12/min, which falls between the rule's thresholds.
2. **"No pressure signal" is read as the rule's own "not PRESENT".** The
   corpus is also not ABSENT, on the fps column.
3. **k+2 doubles the parity** (16 % → 32 %) inside the same frame bursts.
   The frame burst meeting the wireless queue is what `P5`/`P6` found the
   loss to be.

So the design task's first step is a measured arm, not an adoption:
interleaved k+2 and 8+1 holds scored on the close-out rows. See the
decision record.

## Files (`c4_d1_2026-09-24/`)

- `c4_d1_analyze.py`: method, substitutions and rule in the docstring.
- `c4_d1_analysis.txt`: the full output.
- `inputs_sha256.txt`: every file read.
- `sha256_manifest.txt`.

`h2_prep_redact.py --check` reports 0 residual matches on every text file.
No address, MAC or device identifier appears in any file.
