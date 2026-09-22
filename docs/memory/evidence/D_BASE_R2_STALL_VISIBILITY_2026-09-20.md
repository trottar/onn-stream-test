---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-R2 — stall visibility and launcher reconcile

## Classification

**COMPLETE / RUNTIME VALIDATED.** All three pieces are implemented, built
with the real toolchain, installed on the onn, and confirmed against live
sessions. Diagnostic and UX only. **No automatic recovery was implemented**,
and no streaming constant, decoder configuration, FEC, transport or emulator
behaviour was changed.

## Raw numbers

### Piece 1 — the worst gap always gets a row

Three attract-mode sessions of the PS1 reference title, zero input,
`low_latency_enabled: true` in all three. A row is
`[elapsed_ms, rx_to_decode_ms, feed_delay_ms, codec_ms, codec_in_flight, app_queue, output_gap_ms]`.

| | **R2** | **R2B** | **R2C** |
| --- | ---: | ---: | ---: |
| report | `native_decoder_20260920_180217_204.json` | `native_decoder_20260920_180728_652.json` | `native_decoder_20260920_181014_280.json` |
| `duration_ms` | 93,280 | 93,053 | 91,784 |
| `max_output_gap_ms` | 276 | 744 | 474 |
| **row for that gap** | `[87932, 10, 0, 10, 1, 0, 276]` | `[92073, 11, 0, 11, 1, 0, 744]` | `[68428, 18, 4, 13, 2, 1, 474]` |
| `max_codec_ms` | 138 | 610 | 116 |
| `max_rx_to_decode_ms` | 140 | 614 | 117 |
| rows retained | 67 | 64 | 64 |
| — of those, gap-triggered (`rx_to_decode < 50`) | 67 | 61 | 57 |
| — latency-triggered (`rx_to_decode >= 50`) | 0 | 3 | 7 |
| `slow_event_retained_marked` | **3** | 0 | 0 |
| `slow_event_retained_recent` | 64/64 | 64/64 | 64/64 |
| retained span (`elapsed_ms`) | 7,593-92,880 | 66,839-93,041 | 66,871-90,973 |
| `stream_discontinuities` | 3 | 0 | 0 |

**Three sessions out of three: the session's `max_output_gap_ms` now has its
own per-event row.** Under the predecessor trigger none of them would have:
every one of those three rows carries `rx_to_decode_ms` of 10-18 and
`codec_ms` of 10-13, far under the 50 ms latency threshold that was the only
way to record an event.

Those three rows are also the finding. A 276 / 744 / 474 ms output gap
whose ending frame was received and output in 10-18 ms, with
`codec_in_flight` 1-2 and an app queue of 0-1, is a decoder that was holding
nothing and had nothing to hold. R2C reached 474 ms with **zero**
discontinuities in the whole session.

**The `C3.L2b` cycle window now protects something.** R2 recorded
`slow_event_retained_marked` **3** against its 3 sequence resyncs. Every
low-latency session before this patch read 0 marked rows despite five
resyncs between them, because no discontinuity-adjacent frame was slow by
the latency measure. The marked segment was live code with nothing to hold;
it now holds the events it was built for.

### Piece 2 — a terminal stall leaves a trace on the host

`logs/games/native_stream_heartbeat.log`, two sessions (R2B and R2C; R2 ran
against a companion that predated the patch, see Deviations):

| | session 1 (R2B) | session 2 (R2C) |
| --- | ---: | ---: |
| lines | 46 | 46 |
| `sequence` | 1..46 | 1..46 |
| `elapsed_ms` covered | 517..91,929 | 424..90,884 |
| cadence min / median / max (ms) | 2,006 / 2,008 / 2,513 | 2,006 / 2,008 / 2,076 |
| `last_output_age_ms` min / median / max | -1 / 10 / 601 | -1 / 10 / 57 |
| `rx_packets` first..last | 25..77,371 | 3..74,968 |
| `rendered_frames` first..last | 0..5,305 | 0..5,398 |

One line, verbatim:

```json
{"schema": "privyhub_native_stream_heartbeat_v1", "received_at_utc": "2026-09-20T18:07:25.277Z", "sequence": 45, "interval_ms": 2000, "last_output_age_ms": 8, "rendered_frames": 5220, "queued_frames": 5379, "rx_packets": 76158, "elapsed_ms": 89922}
```

`last_output_age_ms` rises and resets exactly as intended. It reads **-1**
on the first heartbeat of each session (nothing decoded yet), settles at
5-12 ms, and lifts at the slow moments: in R2B at 13,097 ms (193),
15,107 (57), 25,146 (125), 53,777 (92), and **601 on the final heartbeat**,
which lands as the session is being torn down by BACK and output has already
stopped. R2C, the cleaner session, lifts once, to 57 ms at 50,728 ms.

`native-stream-status` returns the newest line under `last_heartbeat`; it
read `null` before any session and the sequence-46 record afterwards.

### Piece 3 — the launcher reconciles from a failed poll

Measured on the final build, companion stopped deliberately with a game
active and the launcher on screen:

| step | observed |
| --- | --- |
| companion up, game active | `NOW PLAYING` present (1), status line `Connected: <host>` |
| companion stopped (`kill`), confirmed gone | — |
| launcher resumed, first UI dump at **+3,312 ms** | `NOW PLAYING` **0**, status line **`Companion unreachable`** |
| orphaned emulator cleared, companion restarted, launcher resumed | `NOW PLAYING` 0, status line **back to `Connected: <host>`** |

Before this patch the same sequence left "NOW PLAYING … PAUSED" on screen
indefinitely — the state the first autonomous teardown left the onn in
(`LEARNINGS.md`, "Teardown is part of the test").

**The +3,312 ms is an upper bound, not the reconcile time.** A
`uiautomator dump` round trip is itself ~2.5 s, so this is the first moment
the screen could be sampled, and it was already reconciled. The code path is
deterministic: `onResume` posts the poll at +350 ms, each companion-
unreachable failure reschedules at +350 ms, and the banner clears after
`UNREACHABLE_RETRIES` (2) further attempts — about **1.05 s of scheduled
delay** plus three connection refusals, which are immediate on a live host
with a dead listener. An earlier run of the same check on the previous
build agreed (cleared by the first sample, +3.2 s).

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 17:59 | three source edits + new companion module | see Changed scope in the patch record |
| 18:00 | `sh ./gradlew :app:assembleDebug --no-daemon` | `BUILD SUCCESSFUL in 23s` |
| 18:00 | `adb install -r` | `Success` |
| 18:00:32 | game launched, session **R2** run (93.3 s, zero input) | report landed; **heartbeat log absent** — see Deviation 1 |
| 18:03 | stale companion identified and stopped; teardown; companion restarted on the patched code | endpoint probe returned `ok: true` and wrote one line, which was then discarded |
| 18:04:28 | game relaunched, session **R2B** run (93.1 s, zero input) | 46 heartbeats, report has the row for its 744 ms gap |
| 18:08:37 | session **R2C** run (91.8 s, zero input) | 46 heartbeats, report has the row for its 474 ms gap |
| 18:11 | first piece-3 check | banner cleared, `Companion unreachable` shown |
| 18:13 | piece 3 completed (notice self-clears), rebuilt, reinstalled | `BUILD SUCCESSFUL in 21s`; APK `097f2fe5…8dad` |
| 18:15:07 | piece-3 check re-run end to end on the final build | cleared, then recovered to `Connected: <host>` |
| 18:16 | teardown | no companion, RetroArch, ffmpeg or FEC relay process left; no listener on 8765 or 48100-48102/48110; launcher on screen with no banner and a correct status line |

`controller.motion_events` is 0 in all three reports and the only device
input during a session was the single BACK key.

## What did not work, and what is not known

- **R2B is an outlier on the decode path and the cause is not established.**
  Scored by the A2 script against its neighbours:

  | session | spike20/min | spike50/min | fps | stale/min | `max_gap` | `max_codec` | lost/min | resyncs |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
  | R2 | 111.9 | 12.2 | 57.06 | 8.4 | 276 | 138 | 1,754.7 | 3 |
  | **R2B** | **390.8** | **145.7** | 57.70 | **85.1** | 744 | 610 | 11.6 | 0 |
  | R2C | 111.1 | 9.8 | 59.39 | 5.9 | 474 | 116 | 115.7 | 0 |

  R2B is 3.5x worse on spikes than either neighbour while having the
  *cleanest* transport of the three (11.6 lost packets/min, no resyncs).
  R2B was the first session with the heartbeat posting, which is why R2C was
  run: **R2C also had the heartbeat active and sits in the ordinary
  `C3.L2c` band** (107-203 spikes/min), so the heartbeat is not implicated
  on this evidence. R2B is recorded as an unexplained outlier, not as a
  regression and not as noise that has been ruled out. n=2 with the
  heartbeat active is not a distribution.
- **Piece 1 makes the worst gap qualify; it does not make it survive.** The
  recent segment filled to 64/64 in all three sessions and its retained span
  narrowed to the last ~26 s in R2B and R2C. The three worst gaps here were
  all late in their sessions; a 744 ms gap at 20 s would have been evicted
  by the gap rows that came after it. The pre-existing item in
  `KNOWN_ISSUES.md` — keep a per-session top-N alongside the tail — is now
  more pressing, not less, and it is not authorized here.
- **Gap rows crowd out latency rows.** In R2B the 610 ms `max_codec_ms`
  event has no row: 61 of the 64 recent entries are gap-triggered, and the
  latency event that the predecessor trigger would have kept was evicted.
  The new trigger competes for the same budget as the one it complements.
  Also a case for top-N retention.
- **The heartbeat log is append-only and is not rotated.** ~200 bytes per
  line at 30 lines per minute, so roughly 360 KB per hour of play. Nothing
  trims it. Registered in `KNOWN_ISSUES.md`; not fixed here.
- **Piece 3 reconciles only when something polls.** The launcher's banner
  refresh is driven by `onResume` (plus a short success-side re-poll chain
  while a session is unpausing); there is no timer. A launcher left in the
  foreground with the companion dying underneath it will still show a stale
  banner until the next resume. That is unchanged by this patch, which fixes
  what a *failed* poll does, not how often polls happen.
- **No terminal stall was observed.** Piece 2 is validated on its mechanism
  — cadence, fields, the age rising and resetting, the value on
  `native-stream-status` — and not on the event it exists to capture. The
  first real stall will be its first real test.
- **Nothing acts on a heartbeat or on its absence.** Automatic recovery is
  the separately-decided link-drop item and was not implemented, by
  instruction.

## Deviations from the instruction as written

1. **The first session (R2) ran against a companion that predated the
   patch, so it produced no heartbeats.** A companion started at 17:31 —
   before this work began — was still holding port 8765, and the
   `nohup python3 ./companion/privyhub_service.py &` used to start a fresh
   one failed with `OSError: [Errno 98] Address already in use` into its
   redirected log, where the `&` hid it. The stale process answered
   `native-stream-heartbeat` with `Unknown Games plugin POST action`. This
   is exactly the D-068 rule in `TOOLS.md` — *restart the companion whenever
   companion Python changes; stale-process behavior is not evidence* —
   caught by the check rather than by the procedure. The companion was
   stopped, restarted on the patched code, and the validation re-run as R2B
   and R2C. R2's report is still valid evidence for piece 1, which is
   entirely client-side, and it is reported above as such. Operational rule
   added to `TOOLS.md`: check for an existing listener before starting the
   companion, and check the log after.
2. **Piece 3 was extended once, after its first check.** As first written it
   set the status line to "Companion unreachable" and nothing ever cleared
   it — the line survived the companion coming back, which is the same
   class of stale assertion the piece exists to remove. A reachable
   companion now restores `Connected: <host>`. This is a completion of the
   specified behaviour, not an addition to scope; it was rebuilt,
   reinstalled and re-validated, and the recovery step is in the piece-3
   table above.
3. **Two extra sessions were run** beyond the one the instruction requires.
   R2 was invalidated by Deviation 1; R2C was run because R2B's decode-path
   numbers were an outlier and a second heartbeat-active sample was needed
   before writing "the heartbeat costs nothing" or "the heartbeat costs
   something". Neither could be decided on one session.
4. **The piece-3 check orphaned the emulator twice.** Stopping the companion
   with a game active leaves RetroArch running and untracked; a restarted
   companion reports `active: false` and does not reclaim it. Both orphans
   were killed directly and the host verified clean. `tools/recover_orphan_game_session.py`
   exists for this and was not used — killing was sufficient and the
   sessions held nothing worth recovering.
5. **`pgrep -f` / `pkill -f` match this shell's own wrapper.** Two commands
   exited 144 (killed by their own pattern) because the pattern text appears
   in the wrapper's command line. The intended targets died correctly in
   both cases and the state was verified afterwards. Use
   `ps -eo pid,cmd | awk '/[p]attern/{print $1}'` instead. Recorded in
   `TOOLS.md`.

## Artifacts

Under `evidence/d_base_r2_2026-09-20/`:

| file | SHA-256 | bytes |
| --- | --- | ---: |
| `native_decoder_20260920_180217_204.json` (R2) | `d4fdae99be4e7cad871122acff3f712d6153be9568301b4029553fd83e1f70d7` | 11,805 |
| `native_decoder_20260920_180728_652.json` (R2B) | `d4a45a3ef44af685871634e96483129dd9e3d0d74fd22c95cd60e371d08e1894` | 10,612 |
| `native_decoder_20260920_181014_280.json` (R2C) | `5d9949731ba7ae695725f8c6f762f32f9918463e68d1fac4c0ac23582bfbfea6` | 10,595 |
| `native_stream_heartbeat_2026-09-20.log` (92 lines, both sessions) | `3d7dca5eeb33a3988a1a522a615b47eac78370865aad235fa0737af9b5e04f97` | 22,870 |

The reports also remain in `logs/games/decoder_sessions/`, and the live
heartbeat log at `logs/games/native_stream_heartbeat.log`.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts. The heartbeat records counters and
host time only, by design. The launcher's status line is referred to as
`Connected: <host>`.
