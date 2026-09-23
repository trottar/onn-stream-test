---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-P9 — FALSIFIED by the pre-registered reading (underruns 20 -> 25), default reverted to 3 / 8, the setting stays; the cushion itself cut prolonged starvation 98 % at +36.0 ms of measured residence
---

# D-BASE-P9 — the deeper audio cushion

Task: `handoffs/D-BASE-P9_TASK.md` (the user's decision of 2026-09-23 to
spend +45 ms). Evidence: `d_base_p9_2026-09-23/`, SHA-256 of every file in
`d_base_p9_2026-09-23/p9_sha256.txt`. Patch record:
`patches/D-BASE-P9_AUDIO_CUSHION_SETTING.md`. Decision record:
`decisions/D-BASE-P9_AUDIO_CUSHION.md`. Host headless (`H2`), companion
under its systemd user unit (`H3`), host wired to the Opal, onn on the
Opal's 5 GHz, adopted profile (`any_override: false`, `-max_frame_size
90000` in every arm's argv), sampler off, heartbeat default, **0 adb client
processes in every hold** (monitor, 0.5 s polls).

## Classification

**FALSIFIED by the pre-registered reading — on the underrun clause
alone.** B (12 / 17) met the other two: `prolonged_starvation_events`/min
**42.4 → 0.8 (-98.1 %)** and `avg_queue_residence_ms` **+36.0 ms** (band
35-55). But `audio.underruns` rose **20 → 25**, and the handoff's rule is
"does not work if ... underruns rise". Per the rule **the profile default
is reverted to 3 / 8 and the setting stays.** B′ (12 / 24): starvation
-99.8 %, underruns 16, but **+71.7 ms** — outside the promised cost.

**What the underrun counter did instead** (the rule asks): it did not
track the cushion. 20 / 25 / 16 across 8 / 17 / 24 packets is not
monotonic; B's in-series rise is **one event — 8 underruns at 76 s**, a
playback-side stall (the same session's `max_queue_residence_ms` of 174 ms
exceeds its 85 ms ceiling, which only a stalled consumer can do). The
reading was applied as written; whether 20 → 25 is noise is the user's
call, recorded in the decision record, not taken here.

## Before the sessions — what the code says the two numbers do

The handoff asked to say if the code argued against 12 / 24 ("target at
half of capacity"). It did, and the user was asked before any session:

- **`queue_target_packets` is only the startup prefill** — the playback
  loop waits once for `queue.size >= target` (100 ms bound) and never
  consults it again.
- **The running depth sits near `queue_capacity_packets`.** Every arrival
  hole is concealed on the track's timeline and the late burst that
  follows refills the queue until the capacity trims it. `P8` arm A:
  residence **30.9 ms against a 40 ms ceiling**; `smooth_latency_trims`
  4,622 = `concealed_underruns` 4,637 — one trim per concealed packet.
- So 12 / 24 predicts ≈ **+80 ms**, not +45. **The user chose to run
  both**: B = 12 / 17 (+9 packets = +45 ms, the profile default for the
  run) and B′ = 12 / 24 (environment), beside A2 = 3 / 8 (environment).

**Prediction held:** B +36.0 ms, B′ +71.7 ms (predicted +45 / +80, both
≈ 9 ms under — the queue sits ~2 packets under its ceiling at any
capacity).

**And the target never reached the prefill.** The client starts its audio
receiver before posting `native-stream-start`; the companion starts the
audio sender at the end of that request; so the first real PCM is queued
**before the response is parsed** (`cushion_applied_before_first_pcm`
false in all three and the smoke). The prefill ran at the client default
3 every time, the host's capacity took over just after. **The `P2a` hold
and the prefill were untouched by construction**; the cushion under test
is the running one.

## Raw numbers first

Three 20-minute attract-mode sessions of the PS1 reference title, zero
input, RESUME PLAYING, BACK to end, game stopped between
(`p9_run.sh`, derived from `P8`'s `p8_run.sh`; the companion restarted per
arm by `systemctl --user restart privyhub-companion` with the arm's
override in the user manager's environment, 8765 owned by the unit's
MainPID each time; `p9_all.sh` restored it without). Analysis
`p9_analyze.py` → `p9_analysis.txt`, `p9_summary.json`;
`p9_underrun_loss_timing.txt`. P8 arm A beside it for reference.

| field | A2 3/8 | B 12/17 | B′ 12/24 | P8-A 3/8 |
| --- | ---: | ---: | ---: | ---: |
| duration s | 1,207.0 | 1,207.1 | 1,207.0 | 1,208.0 |
| **`underruns`** (total) | **20** | **25** | **16** | 9 |
| **`prolonged_starvation_events`** | 853 | 16 | 2 | 704 |
| … per min | **42.40** | **0.80** | **0.10** | 34.97 |
| `concealed_underruns` | 5,238 | 138 | 14 | 4,637 |
| `stale_drops` = `smooth_latency_trims` | 5,256 | 141 | 27 | 4,622 |
| `lost_packets` (audio) | 282 | 990 | 1,380 | 544 |
| `concealed_loss_packets` | 263 | 980 | 1,380 | 509 |
| **`avg_queue_residence_ms`** | **30.67** | **66.71** | **102.42** | 30.91 |
| `max_queue_residence_ms` | 58 | 174 | 131 | 53 |
| `buffered_ms` (end) | 18 | 16 | 12 | 20 |
| `max_queue_depth` | 8 | 17 | 24 | 8 |
| `startup_wait_ms` | 2,100 | 2,134 | 2,370 | 2,108 |
| `startup_prefill_ms` | 11 | 9 | 1 | 2 |
| `first_write_elapsed_ms` | 2,193 | 2,210 | 2,449 | 2,193 |
| holes > 15 ms (P8 ring) | 3,524 | 3,771 | 3,517 | 3,200 |
| … per min / ≥ 40 ms per min | 175.2 / 109.2 | 187.4 / 113.0 | 174.8 / 111.9 | 158.9 / 101.5 |
| rendered fps | 59.91 | 59.89 | 59.91 | 59.91 |
| spikes ≥ 20 ms / min | 35.5 | 34.9 | 32.5 | 29.3 |
| `spike_50_ms` | 22 | 27 | 14 | 25 |
| `max_output_gap_ms` | 140 | 209 | 132 | 164 |
| `stale_output_drops` | 22 | 26 | 13 | 19 |
| video lost packets / min | 12.1 | 13.3 | 11.0 | 14.2 |

Hole lengths (ms: count) — **unchanged by the cushion**, as it must be
(B +7.0 %, B′ -0.2 % against A2, inside the 20 % band):

| arm | 15-20 | 20-30 | 30-40 | 40-50 | 50-60 | 60-70 | 70-100 | 100-200 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A2 | 400 | 483 | 445 | 267 | 1,747 | 171 | 8 | 3 |
| B | 460 | 472 | 566 | 313 | 1,788 | 161 | 9 | 2 |
| B′ | 417 | 409 | 439 | 276 | 1,788 | 179 | 7 | 2 |

**The pre-registered reading against A2:**

| | starvation/min drop | underruns | Δ avg residence | reading |
| --- | ---: | --- | ---: | --- |
| B 12/17 | **98.1 %** (≥ 80 ✓) | 20 → **25** ✗ | **+36.0 ms** ✓ | **does not work** (underrun clause) |
| B′ 12/24 | 99.8 % ✓ | 20 → 16 ✓ | +71.7 ms ✗ | starvation met, cost outside 35-55 |

**Video path untouched**: fps 59.89-59.91, spikes 32-36/min, video loss
11-13/min in all three. B's `max_output_gap_ms` 209 is one gap; B′ is
132.

## Two things the table does not settle

1. **Underrun timing.** `audio.tick_series` (400 rows) covers only the
   first ~200 s. In it: A2 7 (1 inside first write + 3 s), B 10 (2
   startup, **8 in one row at 76.2 s**), B′ 5. **The rest of each total
   lies after 200 s and is not placed.** With the `P2a` hold in force the
   total is **no longer the startup burst `P2` described** — most of it is
   mid-session in every arm, including A2.
2. **Audio loss rose 282 → 990 → 1,380, and the cushion cannot cause it.**
   `lost_packets` is counted on the receive thread from RTP sequence gaps
   before anything is queued. It is spread across the session (ticks with
   loss 178 / 399 / 461 of 596) and **climbed through the hour in arm
   order**: A2's per-minute series runs 6 → 55, B 20-107, B′ 24-129,
   while video loss stayed at 11-13/min. P8's arms read 544 / 752 / 596.
   **Arm order and elapsed time are confounded here**; a 3 / 8 bookend
   after B′ would separate them and was not run. It matters for the
   listen: concealed-loss packets are glitches too — concealed packets in
   total (underrun + loss) fell **5,501 → 1,118 → 1,394**, still -75-80 %.

## The user's listen

For the user: lip-sync or lag on the TV with the cushion in force —
**their words, recorded as user-stated, never a gate.** Not yet given.
(To hear B: `systemctl --user set-environment
PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS=12 PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS=17`
then `systemctl --user restart privyhub-companion`; undo with
`unset-environment` of both and another restart.)

## State at the end

Profile default **3 / 8** (`audio_cushion.source` `profile`); companion
MainPID serving 8765, **no `PRIVYHUB_*` in its environ or the user
manager's**; `any_override: false`; game inactive. APK
`a9355bb0…4a72` stays installed (the setting, client default 3 / 8).
Teardown: BACK, game stopped, `active: false` after every arm.

## Privacy

Private addresses in the companion journals, reports and status files
replaced with `<IP_REDACTED>`; no MAC, SSID or device identifier in the
evidence.
