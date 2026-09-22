---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# C3.L2c — unconditional `KEY_LOW_LATENCY`, judged on the distribution

## Classification

**RUNTIME EVIDENCE COMPLETE / DECISION: KEPT (user, 2026-09-20, late — see `CURRENT.md`; one real play session, 1,133 motion events, scored the same as the three below).** `CURRENT.md` Next Action
Steps 1-5 (evening of 2026-09-20) performed in full. The low-latency build
is **installed on the onn and the source change is in place**. It was **not**
reverted. The keep/revert decision is the user's, on the numbers below.

`C3.L2c` was rolled back on 2026-09-19 on a single `max_output_gap_ms`
sample. This record is the distribution the `D-BASE` rule asked for: three
fresh sessions of the PS1 reference title, each over 120 s, zero input,
against the 128-session non-low-latency corpus and against a same-day,
same-title, same-procedure control.

## Raw per-session numbers

The three sessions, as the A2 re-score script scores them. Nothing here is
normalized or adjusted; rates are per minute of session wall time.

| | **S1** | **S2** | **S3** |
| --- | ---: | ---: | ---: |
| report | `native_decoder_20260920_152550_060.json` | `native_decoder_20260920_152814_643.json` | `native_decoder_20260920_153035_707.json` |
| received (UTC) | 15:25:50.060 | 15:28:14.643 | 15:30:35.707 |
| `duration_ms` | 133,044 | 131,772 | 131,796 |
| `low_latency_enabled` | **true** | **true** | **true** |
| codec | `c2.realtek.video.avc.decoder` | same | same |
| `encoder_bitrate_kbps` | 7000 | 7000 | 7000 |
| `controller.motion_events` | 0 | 0 | 0 |
| **`spike_20_ms`/min** | **203.39** | **106.55** | **118.82** |
| `spike_50_ms`/min | 54.12 | 9.56 | 8.19 |
| `spike_80_ms`/min | 6.76 | 7.74 | 4.55 |
| `spike_250_ms` (count) | 0 | 1 | 0 |
| `spike_500_ms` (count) | 0 | 0 | 0 |
| **rendered fps** | **58.30** | **58.65** | **59.13** |
| received-AU fps | 58.97 | 59.07 | 59.35 |
| **`stale_output_drops`/min** | **32.92** | **8.65** | **7.28** |
| `queue_overflow_drops` | 16 | 37 | 12 |
| `input_waits` | 20 | 12 | 15 |
| **`max_output_gap_ms`** | **1,352** | **388** | **236** |
| `max_codec_ms` | 209 | 250 | 91 |
| `max_rx_to_decode_ms` | 230 | 250 | 100 |
| `max_codec_in_flight` | 13 | 11 | 11 |
| `max_feed_delay_ms` | 119 | 41 | 30 |
| `video.packets` | 111,602 | 111,268 | 110,507 |
| `video.lost_packets` | 958 | 676 | 520 |
| `video.lost_packets_in_resyncs` | 282 | 386 | 0 |
| `video.robust_missing_packets` | 676 | 290 | 520 |
| lost packets/min | 432.04 | 307.80 | 236.73 |
| `sequence_resyncs` | 2 | 3 | **0** |
| `forward_gap_events` | 27 | 23 | 31 |
| `max_forward_gap_packets` | 112 | 46 | 93 |
| `sequence_gap_au_drops` | 23 | 22 | 31 |
| `fec_recovered_packets` | 25 | 5 | 7 |
| `fec_unrecoverable_groups` | 4 | 3 | 2 |
| `late_or_reordered_packets` | 0 | 0 | 0 |
| `packets_dropped_waiting_for_idr` | 276 | 510 | 0 |
| `max_resync_to_idr_ms` | 216 | 242 | 0 |
| `audio.underruns` | 409 | 106 | 106 |
| audio underruns/min | 184.45 | 48.27 | 48.26 |
| `audio.prolonged_starvation_events` | 212 | 192 | 148 |
| slow events retained | marked 0/64, recent **64/64** (overflowed) | marked 0/64, recent 21/64 | marked 0/64, recent 18/64 |

Per-session discontinuities, verbatim:

- **S1** — `sequence_resync` at 32,054 ms (jump 139), first IDR at 32,270 ms
  (`resync_to_idr_ms` 216, AU complete, no FEC repair);
  `sequence_resync` at 84,825 ms (jump 143), first IDR at 85,012 ms
  (187 ms, AU complete, no FEC repair).
- **S2** — `sequence_resync` at 66,572 ms (jump 130) -> IDR 66,735 ms
  (162 ms); at 67,987 ms (jump 128) -> IDR 68,226 ms (239 ms); at
  70,488 ms (jump 128) -> IDR 70,731 ms (242 ms). All three AU complete,
  none FEC-repaired, none on an unrecoverable group.
- **S3** — **none.** Zero discontinuities in 131.8 s.

Latency bands, share of queued frames (the fault #1 of the baseline record):

| session | < 20 ms | 20-60 ms, rendered | > 60 ms, stale-dropped |
| --- | ---: | ---: | ---: |
| control (gated build, same day/title) | 0.364 | 0.588 | 0.0478 |
| S1 | 0.943 | 0.048 | 0.0093 |
| S2 | 0.970 | 0.028 | 0.0024 |
| S3 | 0.967 | 0.031 | 0.0020 |

## The comparison set

Two comparisons, both from the same A2 re-score run
(`c3_l2c_2026-09-20/a2_rescore_result_with_l2c_2026-09-20.json`; 152 decoder
sessions on disk, 132 at >= 15 s from 2026-09-16, 128 of them non-low-latency).

**A. The corpus** — 128 non-low-latency sessions, median:

| metric | corpus median | S1 / S2 / S3 | median of the three |
| --- | ---: | ---: | ---: |
| `spike_20_ms`/min | 2,534.7 | 203.4 / 106.6 / 118.8 | **118.8** (21.3x lower) |
| `spike_50_ms`/min | 274.3 | 54.1 / 9.6 / 8.2 | 9.6 |
| `spike_80_ms`/min | 87.4 | 6.8 / 7.7 / 4.6 | 6.8 |
| rendered fps | 55.5 | 58.30 / 58.65 / 59.13 | **58.65** |
| received-AU fps | 59.2 | 58.97 / 59.07 / 59.35 | 59.07 |
| `stale_output_drops`/min | 192.1 | 32.9 / 8.7 / 7.3 | **8.7** (22.2x lower) |
| `max_output_gap_ms` | 288.5 (p90 625.7) | 1,352 / 388 / 236 | 388 |
| `max_codec_ms` | 299.0 | 209 / 250 / 91 | 209 |
| lost packets/min | 197.5 | 432.0 / 307.8 / 236.7 | 307.8 |
| audio underruns/min | 113.3 | 184.5 / 48.3 / 48.3 | 48.3 |

**B. The control** — `native_decoder_20260920_145024_777.json`, the
`D-BASE-R1` session recorded five hours earlier: same title, same day, same
host, same driving procedure, same 7000 kbps, 127.5 s, zero input, the only
difference being the capability-gated build (`low_latency_enabled: false`):

| metric | control | S1 | S2 | S3 |
| --- | ---: | ---: | ---: | ---: |
| `spike_20_ms`/min | 2,258.4 | 203.4 | 106.6 | 118.8 |
| `spike_50_ms`/min | 280.5 | 54.1 | 9.6 | 8.2 |
| rendered fps | 56.27 | 58.30 | 58.65 | 59.13 |
| received-AU fps | 59.19 | 58.97 | 59.07 | 59.35 |
| `stale_output_drops`/min | 169.9 | 32.9 | 8.7 | 7.3 |
| `max_output_gap_ms` | 639 | 1,352 | 388 | 236 |
| `max_codec_ms` | 647 | 209 | 250 | 91 |
| `max_rx_to_decode_ms` | 649 | 230 | 250 | 100 |
| lost packets/min | 327.1 | 432.0 | 307.8 | 236.7 |
| `sequence_resyncs` | 3 | 2 | 3 | 0 |

The three low-latency sessions bracket the control's transport conditions
(2, 3 and 0 resyncs against its 3; 237-432 lost packets/min against its
327), so the decode-path difference is not a quiet-network artifact.

## What the numbers say

**1. The 20-60 ms body — the baseline record's fault #1 — is gone.**
Frames under 20 ms receive-to-output go from 36.4 % (control) and 28.4 %
(corpus median) to **94.3-97.0 %**. The 20-60 ms rendered band goes from
58.8 % to 2.8-4.8 %. This is the single largest change any client patch in
this investigation has produced.

**2. `spike_20_ms/min` meets the `D-BASE` target.** Target < 200; S2 and S3
read 106.6 and 118.8, S1 reads 203.4 — 1.7 % over the line, in the session
with the worst transport of the three. Median 118.8 against a corpus median
of 2,534.7.

**3. `stale_output_drops/min` meets the target in two of three.** Target
< 20; 8.7 and 7.3 in S2 and S3, 32.9 in S1. Corpus median 192.1. The client
stale policy was dropping 4.8 % of frames; it now drops 0.2-0.9 %.

**4. Rendered fps does not reach 59.5 — and the reason has moved.** The
client-side deficit (received-AU fps minus rendered fps) is now **0.67 /
0.42 / 0.22 fps**, against a corpus median of 3.5. The remaining gap is the
received access-unit rate itself (58.97-59.35 against the encoder's
59.995), which this patch cannot touch. Rendered fps is now within 0.7 fps
of everything the network delivers.

**5. `max_output_gap_ms` does not meet the 100 ms target in any session,
and in all three it is an arrival gap, not decode.** Read against each
session's own `stream_discontinuities`, per the `D-BASE` rule:

- **S2 (388 ms)** — the slow-event buffer did **not** overflow (21 of 64
  recent entries retained), so every frame whose receive-to-output latency
  reached 50 ms has a row, and the largest retained `output_gap_ms` is
  241 ms. The 388 ms gap therefore belongs to a frame that arrived and was
  output in under 50 ms: the decoder held nothing. Three resyncs sit at
  66.6-70.5 s with IDR waits of 162/239/242 ms and 510 packets dropped
  waiting for an IDR. Transport.
- **S3 (236 ms)** — the same argument; 18 of 64 retained, largest retained
  `output_gap_ms` 72 ms. **Zero** discontinuities, so this one is not even a
  resync: 31 forward gap events, the largest 93 packets, 31 access units
  dropped on sequence gaps. A loss burst with no AU to output. Transport.
- **S1 (1,352 ms)** — the recent segment overflowed (64/64), so no row
  survives for the event and the attribution is a bound, not an
  identification: `max_codec_ms` 209 and `max_rx_to_decode_ms` 230 cap the
  decode path's possible contribution, leaving **>= 1,122 ms with no access
  unit available to output**. Two resyncs (jumps 139 and 143), 276 packets
  dropped waiting for an IDR, 4 unrecoverable FEC groups, 432 lost
  packets/min — the worst transport of the three. Transport.

This is the Group A A2.7 explanation of the 2026-09-19 385 ms gap,
reproduced three times: **removing the codec hold exposes the arrival gap
that was hiding behind it.** `max_output_gap_ms` on this build is a
transport metric.

**6. Transport and audio are untouched, as expected.** Lost packets/min
237-432 against a target of < 10; audio underruns/min 48.3-184.5 against a
target of < 5. Nothing in this patch addresses either, and nothing in the
numbers suggests it did.

## Judgment per `D-BASE`

On the metrics `D-BASE` named for judging a client change —
`spike_20_ms/min`, `stale_output_drops/min`, rendered fps, with
`max_output_gap_ms` read against `stream_discontinuities` — **the change is
a large, consistent improvement across the whole distribution**, not a
single-sample effect: three of three sessions improve on every decode-path
metric, by factors of 20 on the two rate metrics.

The 2026-09-19 rollback was decided by `max_output_gap_ms` 385 against 359.
That comparison was invalid: the 385 ms was an arrival gap and the 359 ms a
codec hold, and this run shows the same substitution in all three sessions.
**A worst-case statistic overruled a distribution, and the distribution was
right.**

Bearing on the pre-registered client decision (`D-BASE` Success Criteria):
the condition was "if a healthy decode path still cannot reach
`spike_20_ms/min < 200` and fps `>= 59.5`, the onn is the ceiling". The
decode path is now healthy and `spike_20_ms/min < 200` **is** reached in two
of three sessions (median 118.8). fps `>= 59.5` is **not** reached, but the
client is now within 0.22-0.67 fps of the delivered access-unit rate, so the
residual is on the wireless hop and the host's delivery, not on the onn's
decoder. The clause was written expecting the decode path to be the binding
constraint; it no longer is. **This does not by itself resolve the
pre-registered decision**, and it is not read here as resolving it.

## What did not work, and what is not known

- **`max_output_gap_ms` still misses its 100 ms target in every session**,
  and in S1 by 13x. Nothing in this patch improves worst-case stall; the
  2026-09-19 negative result — faster single-frame decode does not imply a
  shorter worst-case stall — is *confirmed*, not overturned. What changed is
  the attribution: the stall's owner is transport.
- **S1 is materially worse than S2 and S3 on every axis** (spike20 203 vs
  107/119, stale 32.9 vs 8.7/7.3, underruns 184 vs 48/48, lost 432 vs
  308/237). Three sessions is enough to see the effect and not enough to
  bound its variance. The S1/S2/S3 spread tracks transport quality, but with
  n=3 that is an observation, not a finding.
- **The slow-event buffer overflowed in S1** (recent 64/64), so the 1,352 ms
  event has no row. The 2,000 ms `markCycleWindow` did not protect anything
  here — `slow_event_retained_marked` is **0 in all three sessions**, because
  the frames arriving after each resync had receive-to-output latency under
  the 50 ms recording threshold. This is the `C3.L2b` design meeting the
  low-latency build: on this build, discontinuity-adjacent frames are fast,
  so nothing lands in the marked segment. Noted for the next evidence pass;
  it is not a defect in this run.
- **`max_output_gap_ms` events are now systematically unrecordable.** A
  slow event is written only when receive-to-output latency >= 50 ms
  (`AvcLowLatencyDecoder.kt`, `SLOW_EVENT_THRESHOLD_MS`). An arrival gap
  ends with a frame that is fast by that measure, so the worst gap of a
  session now routinely has no per-event row. Any future work that needs to
  locate a gap directly needs a second trigger on `outputGapMs`.
- **No perceptual observation was made.** By explicit instruction every
  acceptance metric here is instrumentation. The 2026-09-19 rollback cited a
  subjective report ("gameplay was trash") alongside the 385 ms; nothing in
  this run speaks to that, in either direction. Three attract-mode demos
  with zero input are not a gameplay judgement.
- **Why the decoder holds 20-60 ms without the flag is still unknown.** The
  flag removes the hold; the mechanism is not established, and A1-live has
  already shown the bitstream does not ask for it.

## Deviations from the instruction as written

1. **The installed source bytes are not the 2026-09-19 bytes.** The Next
   Action names the previously installed result as
   `dd67acfe…906e7`. No diff, backup or installer for that file survives —
   `archive/patch_backups/privyhub_c3l2c_low_latency_decode_01_20260919T034939Z/`
   holds only the predecessor. The change was therefore re-derived from the
   patch record's description (drop the `getCapabilitiesForType` /
   `isFeatureSupported(FEATURE_LowLatency)` gate and the now-unused
   `MediaCodecInfo` import; request `KEY_LOW_LATENCY` unconditionally on
   API >= R, `try`/`catch` retained). Predecessor
   `22038e35…71c07` verified before the write; result
   **`9a4e80703169dcbd285de530b44b5c087a0aeab9772a8be3b9549135efcc5f96`**.
   Three formatting variants were tried against the recorded hash and none
   matched, so the difference is whitespace/layout in the rewritten block,
   not behavior: the diff is exactly the gate removal, and
   `low_latency_enabled` reads true in all three reports, which is the
   behavior the hash stood for.
2. **`scipy`/`numpy` are not installed in this shell**, so the A2 script's
   Spearman/Mann-Whitney/Fisher outputs read `scipy_missing` in this run's
   result JSON. No statistic used in this record needs them; the frozen
   Group A artifacts keep the correlation figures.
3. **Ending the game from the client needed one extra tap.** The launcher's
   END control raises a modal "Save a state before ending?"
   (Cancel / Don't Save / Save). **Don't Save** was chosen, so no savestate
   was written and the per-game slot inventory is unchanged. Recorded in
   `TOOLS.md`.
4. **The TV screensaver took over the idle launcher once**, between opening
   `MainActivity` and tapping RESUME PLAYING, and the first attempt at S1
   failed with `dreamx` on top. `NativeStreamActivity` holds
   `FLAG_KEEP_SCREEN_ON`, so no session in progress is at risk; only the
   idle launcher gap is. The runner now sends `KEYCODE_WAKEUP` and
   re-opens `MainActivity` immediately before the tap. Recorded in
   `TOOLS.md`. The failed attempt opened no stream and produced no report.

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 15:19 | `AvcLowLatencyDecoder.kt` edited | predecessor hash verified first; result `9a4e8070…5f96`; `git diff --check` clean |
| 15:20 | `sh ./gradlew :app:assembleDebug --no-daemon` (from `PrivyHub/`) | `BUILD SUCCESSFUL in 8s`; APK `10e99088…da00` |
| 15:21 | `adb install -r …/app-debug.apk` | `Success`; no force-stop issued at any point |
| 15:21:3x | `python3 ./companion/privyhub_service.py` (detached) | listening on 8765; idle `active: false` |
| 15:21:37 | `POST /plugins/games/launch?id=<Tekken 3 (USA)>` | `active: true, paused: true` |
| 15:22:35 | first S1 attempt | **failed** — screensaver on top, see Deviation 4; no stream, no report |
| 15:23:32-15:25:50 | **S1** | RESUME PLAYING tap 15:23:33, stream on top 15:23:37, demo held 130 s with no input, BACK 15:25:48, report 15:25:50, 133,044 ms |
| 15:25:58-15:28:14 | **S2** | stream on top 15:26:03, 130 s, BACK 15:28:13, report 15:28:14, 131,772 ms |
| 15:28:19-15:30:35 | **S3** | stream on top 15:28:24, 130 s, BACK 15:30:34, report 15:30:35, 131,796 ms |
| 15:31 | END on the launcher, then **Don't Save** | game `active: false`, stream `active: false`, `pid: null` |
| 15:31 | `uiautomator dump` | **0 occurrences of "NOW PLAYING"** — banner gone, `MainActivity` on top |
| 15:32 | SIGTERM to the companion | no companion, RetroArch, ffmpeg, FEC relay or process-audio process left; no listener on 8765 or 48100-48102/48110 |

In each session the status poll taken at stream open showed FEC, audio and
controller all active; the game was unpaused by the client's
`native-stream-ready`. `controller.motion_events` is 0 in all three reports
and the only device input during a session was the single BACK key.

## Artifacts

Under `evidence/c3_l2c_2026-09-20/`:

| file | SHA-256 | bytes |
| --- | --- | ---: |
| `native_decoder_20260920_152550_060.json` (S1) | `064f6f94445d4343b6d63917a51d36bc20c6b498fabf330be398f1a54d767b75` | 11,272 |
| `native_decoder_20260920_152814_643.json` (S2) | `cb6e4a86a4f0c22ef1188742827eb4134c83eaba552056768528aac042715b18` | 7,283 |
| `native_decoder_20260920_153035_707.json` (S3) | `456441c5335da7804b961c2889a091b30c2acacda3e10ca11a0217f40184aa61` | 6,039 |
| `a2_rescore_result_with_l2c_2026-09-20.json` | `6533a3471f906b38423a08246871dda9463d2ffce2c3dcf9555b204413bf4bb7` | — |
| `a2_session_table_with_l2c_2026-09-20.csv` | `9b3d1cd454406d3c874a17b07a16acb8df65fe8149db2735de46ad3853d31784` | — |

The frozen Group A table under `group_a_2026-09-20/` is left untouched; the
re-score above was written to this directory instead. The three reports also
remain in `logs/games/decoder_sessions/`.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied reports.
