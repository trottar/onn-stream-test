---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P2b — is the +9 % starvation the fix or the night?

## Classification

**Neither. The startup hold does not move `prolonged_starvation_events`,
and the counter has no run-order trend either.** Ten sessions, five
matched pairs, strictly alternating, hold-off first:

- **Pooled Spearman of starvation against run index: -0.036.** No drift.
- **Sign test: the hold-on arm sits above the hold-off arm in 3 of 5
  pairs**, not 5 of 5, and the two largest deltas point in *opposite*
  directions (+18 and -18). Not the fix.
- **The hold-off arm's median starvation is 151; the hold-on arm's is
  140.** The arm *without* the fix is the higher one.

Pre-registered, the reading was "both arms rise together → drift, the fix
is clear" or "hold-on above hold-off at every pair → the fix". Neither
fired, so by the letter this is the **mixed** outcome — but it is mixed in
one direction only, and the direct control settles the question more
strongly than the drift hypothesis would have: **a build with the hold
compiled out measures 125-157 starvation events per 120 s, median 151, the
same band `D-BASE-P2a` attributed to the hold.** `D-BASE-P2`'s 134-146 was
a narrower sample of that band, not a lower one.

**So `D-BASE-P2a` is reclassified RUNTIME VALIDATED** (see "The two P2a
misses" below).

## The sessions

Ten accepted, in run order. `startup_wait_ms` proves each arm: 0 with
`startup_wait_timed_out: true` for hold-off (`STARTUP_REAL_PCM_TIMEOUT_MS`
= 0, so the wait loop's bound is already exceeded on entry), 2,050-2,199
with `timed_out: false` for hold-on.

| slot | arm | starvation | underruns | concealed | avg queue res (ms) | startup wait (ms) | first write (ms) | rendered fps | video lost/min |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | off | 125 | 363 | 1,499 | 27.70 | 0 | 2,083 | 59.48 | 12.6 |
| 2 | on | 143 | 19 | 1,036 | 27.62 | 2,157 | 2,210 | 59.55 | 1.9 |
| 3 | off | 153 | 276 | 1,390 | 27.80 | 0 | 2,024 | 59.53 | 8.2 |
| 4 | on | 154 | 105 | 1,224 | 27.59 | 2,066 | 2,125 | 59.56 | 6.3 |
| 5 | off | 151 | 241 | 1,445 | 27.29 | 0 | 2,334 | 59.42 | 18.9 |
| 6 | on | 138 | 98 | 1,127 | 27.43 | 2,199 | 2,254 | 59.65 | 8.7 |
| 7 | off | 157 | 299 | 1,365 | 27.37 | 0 | 2,085 | 59.59 | 23.7 |
| 8 | on | 139 | 7 | 850 | 28.21 | 2,050 | 2,131 | 59.65 | 2.9 |
| 9 | off | 139 | 245 | 1,195 | 28.08 | 0 | 2,106 | 59.65 | 7.8 |
| 10 | on | 140 | 7 | 981 | 27.69 | 2,161 | 2,226 | 59.53 | 10.2 |

Pairs, hold-on minus hold-off: **+18, +1, -13, -18, +1**.

**One session was rejected and re-run**, the pilot before the battery
proper (`native_decoder_20260921_023016_433.json`), for two
discontinuities inside the first 30 s. No session in the battery itself was
rejected: all ten ran clean with **zero discontinuities**.

`rendered fps` here is `decoder.rendered_frames / duration_s`, not
`video.recent_fps`. The latter is an instantaneous spot reading and is
useless at this resolution — it ranged 43.8 to 71.6 across the same ten
sessions. `D-BASE-P2a` and `D-BASE-P2` both used the frames/duration form,
so their 59.38 and 59.16 figures are sound and are not corrected here.

## What the fix does do, replicated

The underrun result from `D-BASE-P2a` reproduces cleanly on five fresh
pairs: **median `underruns` 276 with the hold off against 19 with it on**,
a 14.5x reduction, and the hold-off arm's range (241-363) sits squarely in
`D-BASE-P2`'s pre-fix 201-399. `concealed_underruns` follows: median 1,390
off against 1,036 on. `first_write_elapsed_ms` is 2,024-2,334 off and
2,125-2,254 on — the hold still does not delay audio, only the track's
start.

## The mechanism P2a proposed is not there

`D-BASE-P2a` offered a shifted queue equilibrium as the way the hold could
raise starvation. The column says no: **`avg_queue_residence_ms` medians
are 27.70 (off) and 27.62 (on)**, a 0.08 ms difference across a 27.3-28.2
spread that both arms share, and `max_queue_residence_ms` medians are 49 in
both. The hold changes when the track starts; it does not change where the
queue settles afterwards. With no mechanism and no pairwise signal, the
+9 % in the P2a record was within-band session variation.

**What `prolonged_starvation_events` actually is remains unexplained** —
`D-BASE-P2` established it as a second phenomenon and that stands. This run
adds only that it is insensitive to the startup hold and has no run-order
trend across ten sessions; it varies session to session in a 125-157 band
on a quiet link. It does not track video loss either: the loss range here
is 1.9-23.7 per minute and the starvation range does not follow it.

## The two P2a misses

Both are now answered, and neither is a property of the fix:

1. **`prolonged_starvation_events` 138 → 151.** Answered by this run: a
   build with the hold compiled out measures median 151. Not the fix.
2. **Rendered fps 59.38 against a >= 59.4 bar.** On this link both arms
   clear it — **median 59.53 off, 59.56 on** — and the hold-on arm is the
   marginally higher of the two. As the P2a record already argued, the bar
   sat above what that night's link delivered in either arm; on a quieter
   link the same build passes it.

**`D-BASE-P2a` is therefore RUNTIME VALIDATED.** Both remaining checks pass
and the accepting evidence it was judged against is unchanged.

## C5 / C5a — the first natural sequence resyncs on this build

`C5a` installed counters that could not fire, because no injection
available without root produces a sequence resync. **The rejected pilot
session produced two, unprompted**, and they are the first real test of the
C5 hypothesis on this build:

| elapsed | type | jump_packets | resync_to_idr_ms | rejected_idr_aus | dropped_non_idr_aus | au_complete |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 4,446 ms | sequence_resync | 302 | 98 | 0 | 11 | true |
| 29,291 ms | sequence_resync | 151 | 263 | 0 | 14 | true |

Session totals for that report: `packets_dropped_waiting_for_idr` 362,
`lost_packets` 534 of which `lost_packets_in_resyncs` 453,
`max_output_gap_ms` 1,647.

**Verdict by C5a's pre-registered rule: still INDETERMINATE** — two
discontinuities against a floor of six. But the direction is worth
recording, because it is the opposite of the hypothesis: **the one resync
over 250 ms (263 ms) rejected zero IDRs.** It waited out a full GOP with
`au_complete: true` on the IDR it finally accepted, having discarded 14
non-IDR access units on the way. If that shape repeats, C5's
completeness-gate explanation is falsified and the 195-332 ms is simply the
GOP wait — which is what `C5` itself called the unavoidable base cost. The
counters are working; they now need four more discontinuities.

The ten accepted sessions contributed nothing here: zero discontinuities in
all of them.

## Method

Two APKs from one source, differing only in
`STARTUP_REAL_PCM_TIMEOUT_MS` (3,000 vs 0); the patch was not reverted and
the source is back at 3,000
(`NativeAudioReceiver.kt` `76fe6401fb02da3897794b1aff7fe5f9e06815c5d03eb73447306a4a00877131`).
Hold-on APK `c3252ab5fda3e0986adc896ad2b2e856010ffc60484834b6a83422558270c718`
(the `C5a` build); hold-off APK
`1232ce18366f6a021d8b9c42a2bf1c68bbdf137d05414bfd0b104edb90f26f85`.
`adb install -r` of the arm's APK before every session. **The battery ends
with the hold-on build installed** (slot 10 was hold-on).

Sessions 2026-09-21T02:33Z - 02:57Z, PS1 reference title, attract mode,
zero input, 120 s each, BACK to end, game stopped between runs.

## Artifacts

Under `evidence/d_base_p2b_2026-09-21/`, with `p2b_sha256.txt`: the ten
accepted reports and the rejected pilot, `p2b_sessions.csv` (the authority
for every number above), `p2b_analysis.txt`, `p2b_c5_discontinuities.txt`,
`p2b_accepted.txt`, `p2b_all_sessions.txt`, and the harness
(`session.sh`, `battery.sh`, `analyse.py`, `c5_read.py`, `read.py`).

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts.
