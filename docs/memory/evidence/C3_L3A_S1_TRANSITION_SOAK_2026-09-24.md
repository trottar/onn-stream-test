---
memory_schema: 1
as_of: 2026-09-24
status: C3.L3a-S1 TRANSITION SOAK — six attract-mode sessions + T0 smoke, all ran, none INDETERMINATE. A COST PARTIAL (52 of 60 covered; gap median 186.5 ms, codec 7-13 ms, 2 of 60 cost an extra GOP ~410-420 ms); B settling 30 of 30, 21 at the floor, 9 needed a third report, 1 a fourth (≤ 6.0 s); C lifecycle CLEAN; D rendered fps ELEVATED BY TRANSITIONS (−0.24 fps, still ≥ 59.5), every other row WITHIN THE NIGHT'S NOISE; baseline stays met in T — NO (video loss T1 37.5, T2 18.55 /min; the dominant losses are not at transitions and the no-transition H2 read 10.77); E within noise; F zero-input controller loss 213-438 /min (seven sessions). Diagnostic only; authorizes nothing; C3.L4 stays BLOCKED
---

# C3-L3A-S1 — the transition soak

Task: `handoffs/C3-L3A-S1_TRANSITION_SOAK_TASK.md`, run unattended from
`handoffs/OVERNIGHT_2026-09-24_QUEUE.md` (authorized by the user 2026-09-24).
Evidence: `c3_l3a_s1_2026-09-24/`, SHA-256 of every file in
`c3_l3a_s1_2026-09-24/sha256_manifest.txt`. Scoring: `s1_score.py` (the
rules in its docstring, written after T0 and before any of T1-T3 / H1-H3) →
`s1_score.txt`, `s1_summary.json`.

**No companion, client, profile, route or environment change; no probe
change** (the `printf '\n'` headless path worked in T0, so `--headless` was
not needed and no patch exists). Every transition fired from the probe's
seeded schedule through the loopback diagnostic route — `C3.L2`'s authorized
"loopback-only diagnostic bitrate changes"; nothing read a condition and
picked a bitrate.

## The sessions

Harness `c3_l3a_s1_run.sh` (derived from `p9_run.sh`; its header lists every
change), driven by `c3_l3a_s1_night.sh` in tmux; `t2_sample.py` (byte copy)
at 10 s from 05:39:49Z to 07:53:39Z, 804 rows. PS1 reference title, attract
mode, zero input. Before every session the harness confirmed: 0
`PRIVYHUB_*` in the user manager and the companion's environ, the unit's
MainPID owning 8765, and `native-stream-status` `any_override: false`, cap
90,000 (profile), cushion 12/17 (profile), redundancy 2/4 (profile) —
before launch and again at PLAYING, **ADOPTED all 14 times**. 0 foreign adb
in every hold (every adb client seen was the thermal sampler's).

| # | arm | window (UTC) | length | onn cpu start → end (°C) | status | probe |
| --- | --- | --- | ---: | --- | --- | --- |
| 0 | T0 smoke | 05:40:45-05:42:25 | 1.7 min | 58.1 → 56.9 | 0 | 2 traversals, 40-50 s, no park; exit 0 |
| 1 | **T1 cold** | 06:24:17-06:38:43 | 14.4 min | 63.1 → 68.8 | 0 | 10 traversals, exit 0, Phase A 865.5 s |
| 2 | H1 | 06:39:54-06:54:20 | 866 s | 67.6 → 69.7 | 0 | — |
| 3 | T2 | 06:55:29-07:09:00 | 13.5 min | 68.0 → 69.1 | 0 | exit 0, Phase A 810.8 s |
| 4 | H2 | 07:10:08-07:23:39 | 811 s | 68.0 → 70.3 | 0 | — |
| 5 | T3 | 07:24:48-07:38:11 | 13.4 min | 67.6 → 68.2 | 0 | exit 0, Phase A 802.6 s |
| 6 | H3 | 07:39:24-07:52:47 | 803 s | 66.6 → 64.8 | 0 | — |

T1 started 41 min after T0's `session_ended` (05:42:27Z). Every T run: 5
jumps + 5 ramps, fresh seed, 0 marks (by construction: stdin at EOF), not
aborted, every decoy on time (`late_s` 0), the stream at 7000 when Phase A
ended (the restore did not fire) and before BACK. **No session died; none is
INDETERMINATE.**

**T0 gate (headless):** preflight passed headless in attract mode
(controller transport active, telemetry fresh), the one newline started
Phase A, no mark was recorded, no block; 4 of 4 SSRC changes aligned
(spread 0.398 s), gaps 160-201 ms / codec 6-10 ms, settling 2.5 / 2.0 s.

## A. Transition cost, n = 60 — **PARTIAL (52 of 60 aligned and covered)**

Every session aligned (T1 / T2 / T3: offset 9.905 / 7.031 / 7.751 s,
spread 0.401 / 0.489 / 0.508 s, max residual 0.247 / 0.251 / 0.302 s): 60 of
60. **Coverage**: T1 and T2 saturated the slow-event buffer (128 of 128;
marked 64 of 64), covered from decoder 111.6 s and 89.8 s — **the first four
transitions of each** (T1 ramp 0 rungs 1-3 and jump 1; T2 jump 0 and ramp 1
rungs 1-3) are not covered and are not scored; T3 retained 124 of 128, the
whole session covered. 52 < 54 → PARTIAL, as pre-registered. First IDR,
`jump_packets` and host timings cover all 60.

| group | n | max output gap in 1 s after the SSRC change (ms) min / median / p95 / max | its codec_ms | first IDR ms (n 60 split) |
| --- | ---: | --- | --- | --- |
| **all** | 52 | 128 / **186.5** / 224 / 423 | 7 / 9 / 11 / 13 | 0 / 18 / 28 / 242 |
| jump | 13 | 145 / 202 / 224 / 423 | 8-11 | 1 / 19 / 28 / 241 |
| ramp rung | 39 | 128 / 185 / 222 / 405 | 7-13 | 0 / 18 / 27 / 242 |
| down | 25 | 135 / 178 / 207 / 225 | 7-12 | 0 / 18 / 23 / 26 |
| up | 27 | 128 / 193 / 405 / 423 | 8-13 | 3 / 20 / 29 / 242 |
| cold (T1, first 420 s) | 5 | 166 / 171 / 224 / 224 | 9-10 | 0 / 6 / 23 / 23 |
| warm | 47 | 128 / 190 / 225 / 423 | 7-13 | 0 / 19 / 29 / 242 |
| T1 / T2 / T3 | 16 / 16 / 20 | medians 185.5 / 186.5 / 194.5; max 224 / 210 / 423 | ≤ 12 / 13 / 11 | max 26 / 29 / 242 |

`jump_packets` **0 on all 60**. Host side, all 60: spawn 33-566 ms (median
266), first RTP resume 187-719 (median 420), **RTP silence after spawn
151.8-164.3 ms (median 153.1)**, host verified 940-1,472 ms (median 1,173).

**The tail: 2 of 60 cost an extra GOP.** T3 ramp 5 rung 1 (→ 5500) and
jump 9 (→ 7000): first IDR accepted **242 / 241 ms** after the SSRC change
(GOP 15 = 250 ms) instead of ~20, and the largest gap **405 / 423 ms**, at
ssrc + 279 / 277 ms, with `codec_ms` 9 / 8. The first IDR after those
restarts was not usable and the decoder waited for the next. Both were
upward. The other 50 covered gaps are 128-225 ms.

Beside the smoke (n = 8): 125-211 ms, codec 7-11. At n = 52 the body is the
same (median 186.5, p95 224, codec ≤ 13); the new fact is the one-GOP tail.
The floor is the actuator's: a restart's RTP silence is ~153 ms on every
one of the 60 — `video_only_restart` costs one gap of that order at the
decoder, plus a GOP when the first IDR is lost. A fact about the actuator,
not about perception.

## B. Settling, n = 30

30 of 30 measured and settled; never settled **0**; `sample_interval_ms`
2000 throughout, cadence 2,007-2,027 ms, budget 6 intervals (`budget_ok`
true on all). `settled_s` min 1.004 / median 3.0 / p95 4.013 / max 6.016.
**21 of 30 settled at the rule's floor (two distinct reports); 9 needed a
third, one of them a fourth.** In those 9 the first report after the
sequence read `recent_fps` **39.8-53.8** (< 54), fresh, `waiting_for_idr`
false, queue 0, output gap 7-18 ms; the next report read 55.8-61.3. The
restart's ~190 ms gap lands inside the client's recent-fps window for one
report. The fourth-report case (T1 jump 6, 6.016 s) read 51.85 then 53.84,
then 59.81. So: **telemetry settles within one to three client reports
(≤ ~4 s), once in 30 four (6 s)** — the smoke's "first report already clean"
held in 21 of 30, not always.

## C. Lifecycle, 60 transitions — **CLEAN**

FEC send errors, audio send errors, controller bad packets: **0** deltas on
every one of the 60 (totals 0 / 0 / 0). The client's `ssrc_changes`
**20 = 20 expected** in each of T1, T2, T3 (no restore fired: each run's
tenth traversal ended at 7000).

## D. The close-out rows with 20 restarts, against the night's band

Band = H1, H2, H3 and the close-out's C, W (worse = higher, except fps).

| row | T1 | T2 | T3 | H1 | H2 | H3 | C | W | verdict (rule) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| spikes ≥ 20 ms / min | 38.87 | 33.51 | 33.57 | 36.97 | 33.20 | 24.23 | 32.84 | 26.04 | WITHIN NOISE (T median 3.40 better than band worst) |
| rendered fps | 59.68 | 59.66 | 59.65 | 59.91 | 59.91 | 59.92 | 59.90 | 59.91 | **ELEVATED BY TRANSITIONS** (all three worse; median 0.24 below band worst vs width 0.02) |
| stale drops / min | 1.16 | 1.17 | 1.48 | 1.17 | 1.39 | 0.96 | 1.14 | 0.80 | WITHIN NOISE (−0.22) |
| video loss / min post-FEC | **37.50** | **18.55** | 6.21 | 6.60 | **10.77** | 5.39 | 8.67 | 8.40 | WITHIN NOISE (T3 not worse; median +7.77 beyond worst vs width 5.38) |
| audio underruns / session | 16 | 15 | 10 | 19 | 20 | 9 | 17 | 14 | WITHIN NOISE (−5.00) |
| prolonged starvation / min | 0.21 | 0.51 | 0.07 | 0.76 | 0.51 | 0.07 | 0.35 | 0.05 | WITHIN NOISE (−0.55) |
| fec_recovered / min | 3.63 | 12.83 | 12.42 | 10.86 | 3.81 | 12.86 | 14.71 | 16.15 | WITHIN NOISE (−3.73) |
| max output gap (ms) — not ruled | 224 | 369 | 423 | 122 | 172 | 107 | 163 | 110 | (item A) |

**Rendered fps** is the one row the rule calls elevated, and it is
arithmetic: 20 restarts × ~190 ms ≈ 3.8 s without output in ~14.5 min ≈
−0.26 fps; observed −0.24. All three T values stay above the 59.5 target.

**Does the baseline stay met in the T sessions? NO** — video loss
post-FEC **T1 37.50 / min, T2 18.55 / min** against < 10 (T3 6.21 passes;
every other target row passes in all three). Beside the answer, not
instead of it:

- T1's loss is dominated by one `sequence_resync` of **378 packets at
  decoder 4.5 s — 5.4 s before the probe's first fire**, during stream
  start-up; `lost_packets_in_resyncs` 378 of 548. Without it T1 is
  11.6 / min.
- T2's by one resync of **133 packets at decoder 89.3 s, 4.3 s after an
  SSRC change** and outside every transition window (IDR 234 ms);
  `lost_packets_in_resyncs` 133 of 253. Without it 8.8 / min.
- Loss in the 4 s after an SSRC change: T1 0, T2 8, T3 14 packets.
- **The no-transition H2 also missed the target (10.77 / min**, one 91-packet
  burst). The warm-state loss (`T2`/`T3`) is in both arms; by the band rule
  the T arm's video loss is WITHIN THE NIGHT'S NOISE.

## E. Warm-state context

onn cpu-thermal 63.1 °C at T1's start rising to 68-70 °C through H1-H3,
64.8 at the end; **thermal status 0 at every sample**. Audio loss per minute
(heartbeat, after de-duplication) is 0-3 in almost every minute of every
session, with one-minute bursts in T2 (21, first minute) and H2 (28, fifth
minute). Audio loss / min per session (report) T 0.14 / 2.64 / 1.18 against
band 0.69 / 2.79 / 1.77 / 0.25 / 1.44 → **WITHIN THE NIGHT'S NOISE**.

## F. Controller transport `lost_packets`, zero input

Per minute between PLAYING and the end of the hold (`native-stream-status`):

| session | lost / min | received / min | lost % |
| --- | ---: | ---: | ---: |
| T0 | 438 | 24,855 | 1.8 |
| T1 | 367 | 25,603 | 1.4 |
| H1 | 345 | 25,630 | 1.3 |
| T2 | 213 | 25,718 | 0.8 |
| H2 | 253 | 25,756 | 1.0 |
| T3 | 254 | 25,680 | 1.0 |
| H3 | 234 | 25,805 | 0.9 |

`bad_packets` 0 throughout. The probe's own `conditions_before/after` agree
(T1 24 → 5,321; T2 18 → 2,893; T3 13 → 3,416). **With zero input the client
sends ~25,700 controller datagrams a minute and the counter reads 213-438
lost a minute** — the 2026-09-24 smoke's ~345 / min under real play is
inside that range. The close-out's own C / W status files (already on disk)
give ~630 / ~680 per minute, zero input. The 2026-09-20 figure (~23 / min)
is the outlier, not the play session. Recorded as the zero-input baseline
for the `KNOWN_ISSUES.md` item; not investigated further.

## What this does not establish

Nothing about **perception** — no marks were possible (stdin at EOF by
design). Nothing about **the gate** — `C3.L3a` Part 2 is the user's eyes and
needs the pre-registered rerun. Nothing about **real network pressure** —
every transition fired from a schedule, none from a degraded condition.
Nothing about **input** — zero of it. **`C3.L4` stays BLOCKED on the gate;
this task authorizes nothing.**

## End state

Companion under systemd (MainPID 330296 owns 8765), 0 `PRIVYHUB_*` in its
environ and the manager, the profile as adopted, stream at 7000, game
inactive, no "NOW PLAYING" on the launcher, sampler stopped;
`logs/streaming/c3_l3a_runs/` empty (each T run's finalize files were moved
into `runs/finalize_<arm>/`); TV as it was. Nothing on the Opal written
(read over ssh by the sampler). No `nft`.

## Files (`c3_l3a_s1_2026-09-24/`)

- `c3_l3a_s1_run.sh`, `c3_l3a_s1_night.sh`, `t2_sample.py` (byte copy),
  `s1_score.py`; `night_t0.log`, `night_rest.log`;
- `t2_samples.jsonl` (804 rows), `t2_sampler.log` (empty);
- `runs/` per session: `report_<arm>.json` (decoder), `heartbeat_<arm>.jsonl`,
  `frames_<arm>.jsonl`, `companion_<arm>.log` (journal, private addresses →
  `<IP_REDACTED>`), `armcheck_<arm>.json` / `status_end_<arm>.json` /
  `status_<arm>.json` (start / before BACK / after BACK), `encoder_cmd`,
  `alpha`, `adb_during_hold`; per T: `probe_<arm>.log`, `state_<arm>.json`,
  `finalize_<arm>/`; `index.txt`;
- `s1_score.txt`, `s1_summary.json`; `sha256_manifest.txt`.

## Privacy

`h2_prep_redact.py --check` on every text file: its only residual matches
are the loopback address, the all-interfaces bind address and the emulator
core's four-part version string — no private address, MAC, IPv6, SSID, ADB endpoint or device identifier. The
onn's adb endpoint was held in the night script's memory only.
