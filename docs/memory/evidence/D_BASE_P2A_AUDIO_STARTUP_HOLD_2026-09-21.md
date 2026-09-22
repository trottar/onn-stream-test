---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P2a — hold audio playback until real PCM arrives

## Classification

**RUNTIME VALIDATED, reclassified 2026-09-21 by `D-BASE-P2b`**
(`evidence/D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`). Both misses
below were tested directly against a build with the hold compiled out and
**neither is a property of the fix**: that build measures starvation
125-157, median **151**, the same band, and on a quieter link both arms
clear the fps bar (median 59.53 off, 59.56 on). The underrun result
replicated on five fresh pairs, median 276 off against 19 on.

*Original classification, kept for the record:*

**DEVELOPMENT.** The fix does what it was built to do — **`audio.underruns`
falls from a median 207 to a median 6, with no burst in any of the five
sessions** — and it is **not reverted**. But two of the eight accepting
checks miss, and the task's rule is that all must pass:

- **`prolonged_starvation_events` median 151 against P2's 134-146.** Out of
  range, and the per-session values rise monotonically in run order
  (137, 143, 151, 157, 163) where P2's did not. Small, real, unexplained;
  the analysis below argues it is not link quality.
- **Rendered fps median 59.38 against a >= 59.4 bar.** Missed by 0.02 —
  **but the P2 control on the same link and the same build minus the fix
  measured 59.16**, so video was not degraded; it improved, and the bar was
  above what this link delivered in either arm.

Nothing else missed. `first_write_elapsed_ms` moved 7 ms at the median, no
session timed out, and no session was rejected.

## The change

`playbackLoop` now waits for the first **real** PCM packet before the
existing prefill and before `AudioTrack.play()`, bounded by
`STARTUP_REAL_PCM_TIMEOUT_MS` = 3,000 ms, after which the original
behaviour resumes unchanged. `firstRealPacketQueuedNs` is set by the
receive loop in `enqueueLatest` — the same event `firstWriteAtNs` marks,
one step earlier. Once real PCM has arrived, the 100 ms
`TARGET_QUEUE_PACKETS` prefill runs exactly as before. The report gains
`audio.startup_wait_ms` and `audio.startup_wait_timed_out`.

Nothing else changed: not the queue target or capacity, not concealment,
trim, crossfade, or any steady-state logic. Client only, startup path only.
APK `95b44b2ace97cdc87ef043cb415e5d1ba679cacbe66de22cf924e043b99c945d`.

## Raw numbers

Five attract-mode sessions of the PS1 reference title, 120 s held, zero
input, BACK to end. **None rejected** — every session had zero stream
discontinuities, so none had one in the first 30 s.

```
run    dur_s  wait_ms  timedout  underr  starv  conceal  cncl<3s  firstWr firstVid    fps  maxgap
Q1     129.0     2234     False       0    137      901        3     2291      890  59.66     296
Q2     125.9     1713     False       6    143      889        5     1781      789  59.49     191
Q3     130.9     1762     False      21    151      992        6     1827      769  59.13     259
Q4     131.0     1715     False      20    157     1039       11     1793      739  59.38     292
Q5     133.0     1640     False       3    163     1094       13     1707      810  59.26     175
```

The P2 baseline, five sessions of the same shape on the same build without
the fix: `underruns` 315 / 205 / 207 / 201 / 399 (median **207**);
`prolonged_starvation_events` 138 / 146 / 138 / 145 / 134 (median 138);
`concealed_underruns` 1,213 / 1,210 / 1,181 / 1,211 / 1,304;
`first_write_elapsed_ms` 2,180 / 1,712 / 1,679 / 1,800 / 2,762
(median **1,800**).

### The eight accepting checks

| check | measured | required | verdict |
| --- | ---: | --- | --- |
| `audio.underruns` median | **6** | <= 10 (from 207) | **PASS** |
| `first_write_elapsed_ms` median | **1,793** | within 200 ms of P2's 1,800 | **PASS** (7 ms) |
| `concealed_underruns` in the first 3 s | **6** | falls with the underruns | **PASS** |
| `prolonged_starvation_events` | **151** | unchanged vs 134-146 | **FAIL** |
| `startup_wait_timed_out` | **0 of 5** | false in all five | **PASS** |
| tick series shows no burst | **yes** | no burst | **PASS** |
| rendered fps median | **59.38** | >= 59.4 | **FAIL** (by 0.02) |
| `max_output_gap_ms` median | **259** | in P1's 123-387 | **PASS** |

### The burst is gone

Underruns in the first 3 s, per session: **0, 1, 2, 3, 0** — against P2's
median of ~204 in the same window (98.7 % of 207). The opening ticks are
flat where P2's climbed:

```
P2a Q1  [21,0] [449,0] [754,0] [963,0] [1477,0] [1993,0]
P2  P2A [19,0] [448,45] [666,34] [963,42] [1476,76] [1992,81]
```

`startup_wait_ms` is 1,640-2,234 and tracks `first_write_elapsed_ms` to
within ~60 ms in every session, which is the fix doing exactly one thing:
holding the track for as long as the stream takes to arrive, and no longer.

## The two failing checks, examined

### Rendered fps: the bar, not the fix

| | P2 (no fix) | P2a (fix) |
| --- | ---: | ---: |
| rendered fps median | **59.16** | **59.38** |
| received-AU fps median | 59.54 | 59.66 |
| client-side deficit | 0.38 | **0.27** |

**Video was not degraded — it was slightly better**, and the client-side
deficit fell. The >= 59.4 bar was not met by the control either, so it is a
statement about this link on this night, not about the fix. `spike_20_ms`
(112 → 140/min), lost packets (75 → 110/min) and `max_output_gap_ms`
(234 → 259) all moved in the busier direction between the two runs, which
is consistent with a slightly worse link and an unchanged client.

### Starvation: small, real, and not explained by the link

`prolonged_starvation_events`, in run order:

| | s1 | s2 | s3 | s4 | s5 | median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P2 (no fix) | 138 | 146 | 138 | 145 | 134 | 138 |
| P2a (fix) | 137 | 143 | **151** | **157** | **163** | **151** |

The first two P2a sessions sit inside P2's range; the last three do not,
and the sequence is monotonic. **It does not track link quality.** Video
loss per minute in P2a run order is 8.8 / 63.9 / 206.7 / 110.4 / 179.1 —
not monotonic — and the P2 control saw the same spread of loss
(3.8 to 194.3) with starvation flat at 134-146. Audio loss is 29 / 5 / 4 /
13 / 15 packets, far too small to matter.

So this is a **+9 % change at the median that coincides with the fix and
has a shape the fix cannot itself produce** — every session got the same
code. Two readings are open and this evidence does not separate them:

1. **Drift through the run** — something on the host degraded over the
   ~13 minutes, and the next run would show it again from a low start.
2. **A real side effect** — starting the track ~1.7 s later, on a filled
   queue rather than an empty one, shifts where the queue equilibrium sits,
   and `prolonged_starvation_events` counts long starvation runs. Plausible
   as a mechanism, unproven here.

**What would separate them:** five more sessions on this build, run in the
opposite order or interleaved with a reverted build. If starvation again
starts near 137 and climbs, it is drift; if it starts near 151 and stays,
it is the fix. That is one unattended run and it is the obvious next step.

**It is worth keeping in proportion.** `prolonged_starvation_events` was
established by `D-BASE-P2` as a second, unexplained phenomenon that nobody
has related to anything audible, and the change is 13 events per session
against an underrun reduction of ~201.

## What this does not show

- **Five sessions on a quiet link**, all attract mode with zero input and
  zero discontinuities. No session exercised the 3,000 ms bound, so
  `startup_wait_timed_out` is confirmed only as "did not fire when audio
  arrived at ~1.8 s" — the absent-audio path is untested.
- **No perceptual check.** The fix removes silence that was already silent,
  so none was required, but nothing here says how the first two seconds
  *sound*.
- **The starvation question is left open**, as above.
- **n = 5 per arm**, and the two arms ran ~40 minutes apart rather than
  interleaved, which is why the fps and link-quality differences between
  them cannot be attributed.

## What ran, in order (all times UTC, 2026-09-21)

| time | step | result |
| --- | --- | --- |
| 00:2x | fix written; `git diff --check` clean | 2 client files, companion untouched |
| 00:25 | `assembleDebug`, `adb install -r`, companion restarted with 8765 checked free | APK `95b44b2a…c945d` |
| 00:26-00:28 | **Q1** | `underruns` **0**, `startup_wait_ms` 2,234 |
| 00:28-00:34 | **Q2**, **Q3** | 6 and 21 |
| 00:34 | **Q4** first attempt | stream opened but the stabilization gate did not release inside the harness's poll; no report, not counted |
| 00:34-00:37 | **Q5** | 3 |
| 00:37-00:39 | **Q4** re-run | 20 |
| 00:40 | teardown | game ended from the client, banner confirmed gone, companion stopped last; no process in state T, no listener on 8765 / 48100-48102 / 48110 |

## Artifacts

Under `evidence/d_base_p2a_2026-09-21/`:

| file | SHA-256 |
| --- | --- |
| `native_decoder_20260921_002807_069.json` (Q1) | `b1334450ff060e65b224cde3a0cd9dd43ac849251f937e8e95db4fb106b06ca1` |
| `native_decoder_20260921_003036_459.json` (Q2) | `55339a375d78149ac4ec2096e2fc92b69cd0c2ccd4c25ce36fbbe545399fd709` |
| `native_decoder_20260921_003301_452.json` (Q3) | `78c61d0cbdbfffb52028909685518ec82c92457da5a19f314c14475456a8440c` |
| `native_decoder_20260921_003639_832.json` (Q5) | `0dc070bacf1f8e7826b89c10ea164cbb957038fe962854883b6f710b0ca45630` |
| `native_decoder_20260921_003917_220.json` (Q4 re-run) | `abe6de0742c8e09c8f64bbc9f51988968a3559e520295472719d1b1953ef5cfc` |
| `p2a_analysis.txt` | `570bdf2b6e47268bd4fa991d279c3b244731727e35a13689d203e9362ee42aeb` |

The P2 baseline reports are under `evidence/d_base_p2_2026-09-20/`.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts.

## Correction on cross-check (2026-09-21, from report timestamps)

The run labels Q4 and Q5 are swapped relative to wall-clock order:
`native_decoder_20260921_003639_832.json` (starvation **163**, underruns 3)
ran *before* `native_decoder_20260921_003917_220.json` (starvation **157**,
underruns 20). In true run order `prolonged_starvation_events` reads
137, 143, 151, 163, 157 — rising, but **not monotonic**, so the "drift
through the run" reading is weaker than stated. The median 151 against
P2's 134-146, the two open readings, and the separating experiment (five
more sessions, interleaved with a reverted build) are unchanged.
