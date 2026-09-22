---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-S1 — overnight soak on the PC-path topology

## Classification

**CHARACTERIZED.** Four 30-minute attract-mode sessions, **two hours of
streaming**, all four completed; none failed, none was cut short, and
nothing needed a retry. This is the reference for the host -> Windows PC ->
Opal -> onn path, to be compared against `D-BASE-B2` once the host moves to
the Opal.

**The headline: nothing about the stream degrades over 30 minutes.** What
does grow is memory, in three processes, and one of those growths is large.

## The four sessions

| | S1 | S2 | S3 | S4 |
| --- | ---: | ---: | ---: | ---: |
| duration (ms) | 1,805,734 | 1,805,645 | 1,805,647 | 1,805,837 |
| rendered fps | 59.637 | 59.601 | 59.617 | 59.637 |
| received-AU fps | 59.723 | 59.727 | 59.723 | 59.720 |
| `max_output_gap_ms` | 722 | 464 | 280 | 279 |
| `output_age_at_end_ms` | 67 | 4 | 13 | 5 |
| `terminal_slow_event` | none | none | none | none |
| spikes >= 20 ms / min | 103.0 | 92.9 | 95.0 | 92.1 |
| stale drops / min | 1.1 | 0.7 | 0.8 | 1.1 |
| lost packets / min | 120.5 | 114.8 | 124.7 | 128.5 |
| forward-gap events | 287 | 306 | 298 | 279 |
| max forward gap (packets) | 76 | 64 | 74 | 69 |
| late or reordered packets | **0** | **0** | **0** | **0** |
| sequence resyncs | 1 | 0 | 1 | 1 |
| ssrc changes | 0 | 0 | 0 | 0 |
| FEC recovered packets | 107 | 94 | 116 | 107 |
| FEC unrecoverable groups | 64 | 71 | 86 | 58 |
| `prolonged_starvation_events` | 2,384 | 2,179 | 2,290 | 2,229 |
| `underruns` | 69 | 67 | 16 | 47 |
| `concealed_underruns` | 15,019 | 13,779 | 14,206 | 14,181 |
| `avg_queue_residence_ms` | 27.73 | 27.93 | 27.96 | 27.66 |
| `startup_wait_ms` | 2,063 | 2,141 | 2,314 | 2,230 |

Every session ran on the `C5a`/P2a build (hold on). `audio.tick_series` is
**capped at 400 rows = 200 s**, so it covers only the first 11 % of each
30-minute session; the per-minute video series below comes from the
heartbeat log instead, at 2 s resolution for the full duration.

## (1) Does anything degrade with elapsed time?

**No stream metric does.** Per-minute rendered fps from the heartbeat, with
Spearman against elapsed minute within each session:

| session | fps range | Spearman(fps, minute) | max `last_output_age_ms` | minutes with a stall > 1 s |
| --- | --- | ---: | ---: | ---: |
| S1 | 59.125 - 60.008 | -0.298 | 152 | **0** |
| S2 | 58.667 - 60.043 | -0.127 | 157 | **0** |
| S3 | 58.920 - 60.025 | -0.119 | 211 | **0** |
| S4 | 59.170 - 60.214 | +0.246 | 117 | **0** |

The signs do not agree, the magnitudes are small, and the ranges overlap
completely. **In two hours of streaming there was not one output gap over
1 second**, and the largest 2-second-resolution output age all night was
211 ms. Across the four sessions `max_output_gap_ms` falls monotonically
(722 → 464 → 280 → 279, Spearman -1.000) and spikes/min falls too
(Spearman -0.800) — the *link* got quieter through the night; nothing got
worse.

**What does grow, within every session, is memory:**

| process | start | end / peak | Spearman vs minute | per 30 min |
| --- | ---: | ---: | ---: | --- |
| RetroArch | 146-148 MB | **255-259 MB** | 0.887 - 0.976 | **+108 MB** |
| companion | 42.6-45.3 MB | 48.4-49.9 MB | 0.222 - 0.846 | +4.5-6.4 MB |
| encoder (ffmpeg) | 117.1-117.4 MB | 117.8-120.1 MB | ~0.96 | +0.5-3.0 MB |

**RetroArch's ~108 MB per 30 minutes is the one number here that would
matter in a long play session**, and it is reproducible 4/4 with a
correlation near 1. It **resets between sessions** (every session starts at
146-148 MB), so it is per-emulator-run growth, not a leak that survives a
restart — a 2-hour session would be the test, and nothing here says what
happens when it keeps going. The companion's growth partly releases between
sessions (48.8 → 45.3 → 49.9 → 44.0 → 48.4) so its net drift across the
night is small. The encoder's is negligible.

Thermals ramp and plateau, identically in each session: **CPU 42-44 °C →
57-59 °C**, GPU 38-40 °C → 46-49 °C, both reaching their plateau and
staying. GPU power is flat (19-29 W, Spearman ~0). **Encoder CPU is flat at
26-27 %** all night (Spearman -0.26 to +0.42, no trend). Load average rises
within a session (0.3-0.9 → 1.8-2.3) tracking the emulator, not the
encoder.

**Time-dependent:** RetroArch RSS, companion RSS, encoder RSS, CPU and GPU
temperature (to a plateau), load average. **Not time-dependent:** rendered
fps, output gaps, spike rate, stale drops, loss rate, encoder CPU, GPU
power, audio queue residence, starvation rate.

## (2) `prolonged_starvation_events`: linear, and it starts immediately

Per-session totals 2,384 / 2,179 / 2,290 / 2,229 over 30 minutes =
**79.2 / 72.4 / 76.1 / 74.1 per minute**, and Spearman against session
index is -0.400 (no trend across the night).

**Linear, not stepwise.** The tick series (first 200 s) accrues in flat
10-second blocks — S1: 2, 14, 11, 10, 17, 15, 16, 12, 11, 20, 13, 15, 10,
8, 13, 11, 19, 14, 11, 19 — about 13 per 10 s from the second block
onwards, i.e. ~78/min, the same rate the whole-session total implies. It
begins at once rather than after any warm-up, and roughly half of all
500 ms ticks carry one.

**It does not coincide with anything.** The video series has no stalls over
1 s and no per-minute structure to coincide with, and **`queue_depth`
ranges 0-8 during the drizzle** — these events fire with the audio queue
*full*, which is what separates them from the startup underruns `D-BASE-P2`
explained. Underruns themselves are now 16-69 per 30-minute session, so
the `D-BASE-P2a` hold holds over long durations too.

**The rate matches short sessions**: `D-BASE-P2b` measured 125-157 per
120 s = 63-79/min on the same build. So `prolonged_starvation_events`
scales linearly with duration at ~75/min and is not a soak-specific
phenomenon. Its 749-in-the-300 s-bucket figure from `D-BASE-P2` is the same
rate. **What it actually counts is still unexplained.**

## (3) Natural discontinuities: three in two hours

| session | elapsed | type | jump_packets | resync_to_idr_ms | rejected_idr_aus | dropped_non_idr_aus | au_complete |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| S1 | 46,832 ms | sequence_resync | 128 | 222 | **0** | 10 | true |
| S3 | 565,820 ms | sequence_resync | 128 | 184 | **0** | 14 | true |
| S4 | 566,842 ms | sequence_resync | 128 | 168 | **0** | 14 | true |

**C5a's pre-registered rule returns INDETERMINATE**: three discontinuities
against a floor of six, and **none over 250 ms**. `C5a` stays
INDETERMINATE.

Two observations worth keeping. **All three jumps are exactly 128 packets**,
which is `RESYNC_FORWARD_GAP_PACKETS` itself — these are threshold-grazing
events, not large outages, and `lost_packets_in_resyncs` reads exactly 128
in each of those sessions. And **all three resolved in 168-222 ms, under one
GOP, with zero rejected IDRs** — consistent with the plain GOP wait. Adding
these to the two from `D-BASE-P2b` gives **five natural sequence resyncs on
this build, every one with `rejected_idr_aus` 0**, of which one (263 ms)
was over 250 ms. One more discontinuity reaches C5a's floor.

## (4) Recovery events: none

**Zero `desync_pause` in two hours.** The recovery log carries only
`session_started` / `session_ended` for all four sessions, `restarts` ended
at 0 in every one, and the only states observed were `PLAYING` and `ENDED`.
No recovery save was written; `save_available` was false at the end. The
recovery path was never exercised by this soak — which is a statement about
the link, not about the recovery code, and is why `D-BASE-R3b` is still
owed.

## (5) Rotation: neither log rotated, so rotation is still untested

The heartbeat log grew steadily — 909,906 → 1,139,162 → 1,368,401 →
1,597,652 bytes at the four session ends, about **229 KB per 30-minute
session** — and the recovery log 13,861 → 14,665 bytes. Their thresholds
are 4 MiB and 1 MiB, so neither came close: **`stream_log_archive/` held 0
files all night** and the archive family's limit was never approached.
At 229 KB per session the heartbeat log needs roughly **15 more sessions
(~7.5 hours)** to rotate. `D-BASE-R4`'s rotation remains validated only by
its own synthetic test.

## (6) Loss shape on the PC path — the reference for the morning

Stable all night and worth stating precisely, because this is what `B2` is
measured against:

- **Loss rate 114.8-128.5 packets/min**, mean ~122, with no trend within a
  session and a mild rise across the night (Spearman +0.800 on four
  points — weak).
- **279-306 forward-gap events per 30 minutes**, i.e. roughly **10 gap
  events per minute**, each small: **max forward gap 64-76 packets** in
  three of four sessions, with the three resyncs at exactly 128.
- Dividing loss by gap events gives **~12 packets per gap event**, matching
  the 14-per-gap median Group A measured on the corpus.
- **Zero reordering. `late_or_reordered_packets` is 0 in all four
  sessions** — 7.2 million packets with not one late arrival. The path
  loses packets in small bursts and never reorders them.
- FEC recovered 94-116 packets per session against 58-86 unrecoverable
  groups: the 8+1 XOR recovers single losses and the bursts defeat it, as
  designed.

## Method

Four 30-minute attract-mode sessions of the PS1 reference title, zero
input, opened through RESUME PLAYING per `TOOLS.md`, BACK to end, the game
stopped and the launcher banner checked between sessions, **150 s idle
between runs**. Host sampled every 30 s to `samples.jsonl` per session
(60 samples each): thermals from `hwmon` (`k10temp`, `amdgpu`), load
average, per-process CPU jiffies / RSS / threads for companion, encoder,
audio ffmpeg and RetroArch, the FEC relay counters and `recovery` block
from the companion, and the sizes of both native-stream logs and the
archive directory. Sessions 2026-09-21T03:10Z - 05:50Z.

**One defect in the sampler, corrected mid-soak and disclosed here.** For
**S1 only**, the `companion` process series tracked the *shell wrapper*
whose command line contains `privyhub_service.py`, not the service — the
`pgrep -f` trap already recorded in `TOOLS.md`, which I walked into again.
S1's `comp_rss_kb` (1,904 KB, 1 thread) is therefore meaningless and is
excluded from the table above; the matcher was fixed to require the
argument list to begin with `python3` before S2, and S2-S4 carry correct
companion data. No other series is affected.

## Artifacts

Under `evidence/d_base_s1_2026-09-21/`, with `s1_sha256.txt` (36 files):
the four decoder reports, `samples.jsonl`, `heartbeat_lines.jsonl`,
`recovery_lines.jsonl`, `status_end.json`, `per_minute.csv` and
`host_samples.csv` per session; `s1_sessions.csv` and `s1_analysis.txt`
across the soak; and the harness (`s1_sampler.py`, `s1_session.sh`,
`s1_soak.sh`, `s1_analyse.py`, `s1_soak.log`, `s1_index.txt`).

## Privacy

No network addresses, MACs, SSIDs, ADB endpoints or device identifiers
appear here or in the artifacts. The sampler drops address-like keys and
IP-shaped values from the companion status blocks before writing; the
artifacts were re-scanned afterwards and the only dotted-quad matches are
the RetroArch core version string `0.9.44.1`.
