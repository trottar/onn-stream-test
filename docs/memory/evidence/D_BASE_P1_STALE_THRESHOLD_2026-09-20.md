---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P1 — stale-drop threshold characterization

## Classification

**CHARACTERIZED.** Thirteen sessions, none rejected. Nothing is accepted or
changed: the product default is 60 ms, the build left on the onn carries no
extra, and the final control session reports `stale_output_ms` 60.

**The headline is a negative result, and it retires the premise this probe
was written on.** On the current build the 60 ms stale threshold discards
**6, 17 and 15 frames** in three 97-second control sessions — 0.10-0.29 %
of frames. **Raising it therefore cannot recover more than ~0.18 fps, and
measured at four thresholds it recovers nothing at all.** The 3.5 fps gap
Group A attributed to this policy was real *before* `C3.L2c`; that change
collapsed the 20-60 ms latency body and took the policy's work with it.

## Raw numbers

Attract mode, PS1 reference title, zero input, 90 s each, interleaved
60 → 90 → 120 → 200 and repeated three times. `stale_output_ms` in every
report equals the threshold requested. **Zero sessions rejected**: no
session had a sequence resync at all, let alone a jump >= 128 packets, and
the largest `max_output_gap_ms` was 387 ms against the 1,000 ms reject line.

Retained-row percentiles (`p50` / `p90` / `rmax`) are **the distribution of
`rx_to_decode_ms` over the rows retained in the report** — the merged
slow-event array plus the two top-16 lists, deduplicated — **not over all
frames**. Retained rows are by construction the slow tail, so these are not
frame-population percentiles; the histogram below is.

```
run     thr    dur    fps  AUfps  stale  stale/m   s20/m  s50/m  s80/m   gap  maxrx   p50   p90  rmax    n   und/m
A60      60   96.8  59.73  59.83      6      3.7    67.5    3.7    1.2   268    106  10.0  17.7   106   92   137.5
A90      90   96.0  59.41  59.61      5      3.1   186.2   10.0    6.2   188    121  10.0  79.5   121   96   139.3
A120    120  105.0  58.92  59.31      2      1.1   202.3    3.4    2.9   173    142  10.0  18.0   142   91   110.3
A200    200   97.0  59.34  59.50      0      0.0   151.6    9.9    8.7   258    181  10.0 115.8   181   93   125.6
B60      60   96.9  59.59  59.79     17     10.5    62.5   11.8    8.7   174    107  11.0  85.2   107   88   139.3
B90      90  101.0  59.56  59.67      7      4.2   150.9    8.3    7.7   123    113  10.0  86.0   113   91   104.6
B120    120  103.0  59.06  59.41      1      0.6   204.5    7.0    1.7   240    171  10.0  51.0   171   85   129.4
B200    200   96.9  59.27  59.39      0      0.0   140.5    8.7    8.7   204    149  10.0 109.2   149   93   149.8
C60      60   97.0  59.65  59.84     15      9.3    69.9   11.1    4.3   147     97  10.0  75.0    97   89   157.2
C90      90   96.9  59.62  59.67      2      1.2   155.4    9.3    2.5   196    114  10.0  54.0   114   93   162.2
C120    120  101.9  59.09  59.42      4      2.4   244.8   22.4   13.5   387    165  10.0 113.0   165   95   115.4
C200    200  102.1  59.22  59.31      0      0.0   226.3   12.3   10.6   176    140  10.0 108.0   140   96   114.0
```

Arm medians:

| threshold | n | rendered fps | received-AU fps | stale/min | spike20/min | spike50/min | spike80/min | `max_output_gap_ms` | `max_rx_to_decode_ms` | underruns/min |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **60** | 3 | **59.65** | 59.83 | 9.3 | 67.5 | 11.1 | 4.3 | 174 | 106 | 139.3 |
| 90 | 3 | 59.56 | 59.67 | 3.1 | 155.4 | 9.3 | 6.2 | 188 | 114 | 139.3 |
| 120 | 3 | 59.06 | 59.41 | 1.1 | 204.5 | 7.0 | 2.9 | 240 | 165 | 115.4 |
| 200 | 3 | 59.27 | 59.39 | **0.0** | 151.6 | 9.9 | 8.7 | 204 | 149 | 125.6 |

Receive-to-output latency of **rendered frames**, the histogram this probe
added (`decoder.rx_to_output_histogram_ms`, 20 ms buckets, summed per arm):

| threshold | 0-20 | 20-40 | 40-60 | 60-80 | 80-100 | 100-120 | 120-140 | 140-160 | 160-180 | >180 | total |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 60 | 17,058 | 276 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 17,343 |
| 90 | 16,710 | 735 | 28 | 12 | 13 | 0 | 0 | 0 | 0 | 0 | 17,498 |
| 120 | 17,176 | 1,014 | 68 | 8 | 9 | 15 | 0 | 0 | 0 | 0 | 18,290 |
| 200 | 16,688 | 789 | 19 | 3 | 4 | 25 | 10 | 6 | 0 | 1 | 17,545 |

Share of rendered frames above 60 ms: **0.000 % / 0.143 % / 0.175 % /
0.279 %**. Percentiles read off the histogram (bucket upper bound):

| threshold | p50 | p90 | p99 | p99.9 |
| ---: | ---: | ---: | ---: | ---: |
| 60 | <= 20 | <= 20 | <= 40 | <= 40 |
| 90 | <= 20 | <= 20 | <= 40 | <= 80 |
| 120 | <= 20 | <= 20 | <= 40 | <= 100 |
| 200 | <= 20 | <= 20 | <= 40 | <= 120 |

## The four questions

**(1) How much rendered fps does each threshold recover? Nothing
measurable, and it cannot recover much.** The arithmetic bound comes from
the control arm alone and needs no cross-arm comparison: at 60 ms the
policy discarded 6, 17 and 15 frames in 96.8, 96.9 and 97.0 seconds, so
recovering *every* dropped frame would add **0.062, 0.175 and 0.155 fps**.
The arm medians agree that nothing is gained: 59.65 (60) → 59.56 (90) →
59.06 (120) → 59.27 (200), which does not rise and in fact drifts down in
step with received-AU fps (59.83 → 59.67 → 59.41 → 59.39). The client-side
deficit (received-AU minus rendered) is 0.18 / 0.11 / 0.35 / 0.12 fps in
the four arms: whatever is keeping rendered fps under 59.5 in the 120 and
200 arms is delivery, not the drop policy.

**The policy is working as designed — there is simply almost nothing for it
to do.** Stale drops per minute fall monotonically with the threshold
(9.3 → 3.1 → 1.1 → 0.0), so the knob does exactly what it claims; the
frames it stops discarding are 0.1-0.3 % of the stream.

**(2) What does it cost in latency? The recovered frames land at 60-120 ms
and the bulk does not move.** p50 and p90 of rendered-frame latency are
<= 20 ms in all four arms — identical. Only the far tail moves: p99.9 goes
from <= 40 ms at the default to <= 80, <= 100 and <= 120 ms at 90, 120 and
200. At 200 ms, 49 of 17,545 rendered frames (0.28 %) are presented more
than 60 ms after they arrived, including one above 180 ms. So the answer to
the question as posed is the second alternative: **the recovered frames
simply land above 60 ms while the bulk stays where it was.**

**(3) Does `max_output_gap_ms` change? No trend.** Medians 174 / 188 / 240 /
204 ms, with per-session values 123-387 ms spread across all four arms.
Consistent with the standing finding that the gap tail is transport; the
drop policy does not touch it.

**(4) Does the 20 ms spike count change? It differs between arms, but not
because of the threshold — and this is a confound, not an effect.**
`spike_20_ms` is incremented from `latencyMs` before the release decision,
so the threshold cannot change it by construction. The arm medians
nevertheless differ (67.5 / 155.4 / 204.5 / 151.6 per minute), and the
histogram shows why: the 60 arm's sessions genuinely had fewer frames in
the 20-40 ms bucket (276 against 735 / 1,014 / 789). **The interleave
repeated a fixed 60 → 90 → 120 → 200 order, so each threshold always
occupied the same position in its cycle**, and anything that drifts within a
cycle loads the arms systematically. Rotating the order (60,90,120,200 /
90,120,200,60 / …) would remove it. The conclusions above do not rest on
the cross-arm comparison — (1) is bounded by the control arm's own drop
counts and (2) is read within each arm — but any *future* cross-arm claim
from this data must carry this caveat.

## Which threshold, if any — and the decision is the user's

**60, the product default, already meets both conditions**: rendered fps
median **59.65 >= 59.5**, with p50 and p90 of rendered-frame latency at
<= 20 ms and **no rendered frame above 60 ms at all**. 90 also meets them
(59.56 fps, p90 <= 20 ms) at the cost of 0.14 % of frames presented at
60-100 ms. 120 and 200 do not reach 59.5 fps — for reasons that are not the
threshold's.

**On this evidence there is no reason to change the threshold**, and the
strongest statement the data supports is that the question has gone quiet:
the policy's cost fell by more than an order of magnitude when `C3.L2c` was
kept, and what remains is 0.1-0.3 % of frames. **The decision is the
user's; nothing here accepts or changes anything.**

## What this does not show

- **The measurement is of an idle attract-mode demo on a quiet link.** All
  thirteen sessions had zero sequence resyncs. On a session with real
  transport trouble the latency distribution is different and the threshold
  may have far more to do — Group A's corpus is exactly that case. This
  probe characterizes the threshold **on a healthy link, on the current
  build**, and nothing more.
- **The cycle position is confounded with the threshold** (question 4).
- **The histogram counts rendered frames only**, so a frame the policy drops
  is absent from it by construction; drop counts are the separate
  `stale_output_drops` column.
- **Retained-row percentiles are not frame percentiles.** The `p50` column
  reads 10 ms in nearly every session because the retained rows are the
  slow tail plus whatever else the ring held; do not read it as a
  population median. The histogram is the population.
- **No perceptual observation was made.** Whether a frame presented 90 ms
  late looks better than a dropped one is not an instrumentation question,
  and by standing instruction this work does not answer it.
- **n = 3 per arm.**

## The probe build

The knob reaches the decoder through the **launch path `TOOLS.md` records**,
not through a companion-served value: `MainActivity` is exported, so
`am start -n …/.MainActivity --ei privyhub.stale_output_ms N` carries the
value, and `openNativeGameStream()` forwards it into the
`NativeStreamActivity` intent when present. The companion was not touched
and `games.py` was not used. The harness force-stops the app before each
launch so `getIntent()` is the intent carrying the extra.

Guard rails: a value outside 16-1,000 ms is ignored in favour of the
default, and the extra's absence is the product path — the final control
session, launched with no extra, reported `stale_output_ms` **60**,
`rendered_frames` 4,402 in 75.0 s (58.69 fps), 8 stale drops, histogram
`[4080, 298, 24, 0, 0, 0, 0, 0, 0, 0]`.

Changed files, this patch only (predecessors from `D-BASE-R4`):

| file | before | after |
| --- | --- | --- |
| `AvcLowLatencyDecoder.kt` | `375516b6…8485` | `1fcafa837bbcff1210753ffe47477915af9e52717d4a2ce774dda474dc038e81` |
| `NativeStreamActivity.kt` | `4ba8a7a6…aff9` | `4e312415b0a795398067fe35367a98d6383065f7da0639b2c0cbf4434a90deb1` |
| `MainActivity.kt` | `983223ab…0629` | `a727f5155c5b8279f0c98ce1af4d64796a2c3b87f04ba2dac2b38a504e3c44e9` |

APK on the onn: `af5193dfb73bf7b64682b210859c2225022aec664f7aeac4f6ba4716a5255343`.

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 22:3x | probe knob and histogram written; `git diff --check` clean | 3 client files, no companion change |
| 22:36 | `assembleDebug`, `adb install -r`, companion started with 8765 checked free | — |
| 22:37 | smoke test at 200 ms | `stale_output_ms` 200, histogram populated, 0 stale drops |
| 22:38-23:02 | **twelve sessions**, 60/90/120/200 × 3, interleaved | all twelve pass the outage screen |
| 23:04 | **final control, no extra**, 60 s | `stale_output_ms` **60** |
| 23:06 | teardown | game ended from the client ("Don't Save"), banner confirmed gone, companion stopped last; no process left in state T, no listener on 8765 / 48100-48102 / 48110 |

One session (A120, first attempt) opened the stream but its stabilization
gate did not release gameplay inside the harness's 25 s poll; the poll was
widened to 45 s and the session re-run. It produced no report and is not
counted. No other run needed a retry.

## Artifacts

Under `evidence/d_base_p1_2026-09-20/` — the twelve session reports, the
final control report, `session_index.txt` (label → threshold → report) and
`analysis_output.txt` (the table above as produced).

| file | SHA-256 |
| --- | --- |
| `native_decoder_20260920_224005_823.json` (A60) | `517c02e999157ab72ce7bc6364ebadddb72adcb38e20a8303e16405951d416a8` |
| `native_decoder_20260920_224155_940.json` (A90) | `090890e536e00c041f944d6f175975c8a133a47ea2f21ce94f4ba651551c4eb7` |
| `native_decoder_20260920_224457_139.json` (A120) | `cf6f8cf963b31f58315fea8fd0053bf2ea6e0520ca8341feaf27a123a30f3cd2` |
| `native_decoder_20260920_224648_618.json` (A200) | `5d592cf81650d67abdb1686957c294c78f6212c91f695735a01a28ea868f06ee` |
| `native_decoder_20260920_224847_830.json` (B60) | `bbfeeb12232a6288692889b5d4b112d2c63c309eab141894ec429eb44f8de9b0` |
| `native_decoder_20260920_225042_695.json` (B90) | `668e78e6845c2719e007b173326dca176dbf742e363adbb3bcda23660f74c18b` |
| `native_decoder_20260920_225240_129.json` (B120) | `5e832ae66d266a51ad978cf8d66572471591696f74b75e13ac6ea07958a3c18f` |
| `native_decoder_20260920_225439_859.json` (B200) | `8a6cb0b77e9927d32c16bd092263fba681977c733551419af2bf4056a55e4338` |
| `native_decoder_20260920_225631_151.json` (C60) | `d85536dec817521df487c16aa350625035a328b9cf9db6b030945fd3fd577731` |
| `native_decoder_20260920_225822_468.json` (C90) | `3c0153bfb0022cdaa7ff6beeb543deca8a0ff1eb8df215faaa8d5f5d24cffe73` |
| `native_decoder_20260920_230032_380.json` (C120) | `0c9a287ed831e4a9515a40fe469336d8e99356fbda37b76e8077716a538a2051` |
| `native_decoder_20260920_230229_153.json` (C200) | `d542d18f3abe780b44b752518a741cb1f53badffc2afcc7ab6ae28f21abb7e60` |
| `native_decoder_20260920_230540_902.json` (final control, no extra) | `a3f6df8f29b8eb1ea0f802f60bd4985deef07b39a45b63c6739056d96347b4af` |
| `session_index.txt` | `f998500c1a8270dafd2788ebc58575aeda10cb68d150cba59d41f94365e487ef` |
| `analysis_output.txt` | `47f744fec5b06df3f0381ced49f2512b14e2f9b716b3ea5c57f7720b0823bfe9` |

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts.
