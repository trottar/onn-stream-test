---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-R2 — stall visibility and launcher reconcile

## Purpose

Three gaps in what the system can see, each found by earlier work in this
investigation:

1. On the `C3.L2c` build a slow event is recorded only when a frame's
   receive-to-output latency reaches 50 ms. An arrival gap ends with a frame
   that is fast by that measure, so the session's worst `max_output_gap_ms`
   routinely had **no per-event row at all**, and
   `slow_event_retained_marked` read 0 in every low-latency session despite
   five sequence resyncs between them — the `C3.L2b` cycle window was
   protecting nothing.
2. A terminal stall posts no decoder session report, so the host keeps no
   record that the session existed.
3. A companion-unreachable poll was swallowed, leaving "NOW PLAYING" on the
   launcher indefinitely — the state the first autonomous teardown left the
   onn in (`LEARNINGS.md`, "Teardown is part of the test").

Diagnostic and UX only. **No automatic recovery**, by instruction: acting on
a heartbeat is the separately-decided link-drop item.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`:
  `9a4e80703169dcbd285de530b44b5c087a0aeab9772a8be3b9549135efcc5f96`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `94f13294ddeda7e2d6b5f8285dc22d9ed81ec2179350fbe11f0a69bcb92eb8a5`
- `PrivyHub/app/src/main/java/MainActivity.kt`:
  `20309b8af102922fa8c9b952f93f01ae0a0c9ba8ef9dfab0e3e06b899ed4fbf0`
- `companion/plugins/games.py`:
  `13309138200d10b24ca18fcfd548ab4f5f267762858ad36533c7b5f2e1a949ce`

## Changed scope

**Piece 1 — `AvcLowLatencyDecoder.kt`** -> `b4c608e0384e974657109bf210cd5f1bba34a1fcea53e504cf4c2cc784af66f7`.
`drainOutputs` records a slow event when `outputGapMs >= SLOW_EVENT_THRESHOLD_MS`
as well as when receive-to-output latency does; same 7-column row, same
`recordSlowEvent` path, so the marked/recent segmentation is unchanged. Adds
`lastOutputAgeMs()`, a read of the existing `@Volatile lastOutputAtUs`, for
piece 2.

**Piece 2 — `NativeStreamActivity.kt`** -> `7cbd9fe8604957910f77ae8247a7af42a895c1e8c52a84ab7d1069c67c8003cc`,
plus the new `companion/games/native_stream_heartbeat.py`
(`7ad5d0f98cfb591ed5670cbd8ecee7ccd71d4b8b5c99a1ff0fdeff7dc5ef611a`) and
`companion/plugins/games.py` -> `f3ccad7b7e59caafea6060c32d6701e22496d59bf520ead8f3e7fe177c8d3e24`.
The client posts `POST /plugins/games/native-stream-heartbeat` every 2,000 ms
while a session is open, carrying `last_output_age_ms`, `rendered_frames`,
`queued_frames`, `rx_packets` and `elapsed_ms` (plus `sequence` and
`interval_ms`). Gated and reset exactly like the existing client-health post,
on its own daemon thread, failures swallowed. The companion appends one JSON
line per heartbeat to `logs/games/native_stream_heartbeat.log` — host time and
the client's counters, no addresses — and `native-stream-status` gains
`last_heartbeat`, read from the log tail, `null` when there is none.

**Piece 3 — `MainActivity.kt`** -> `dbb2fcd58cc2d3eb988897ae748b6e92edea6178e5257b229e1525839b7e9bb2`.
`refreshGameSessionBanner` gains an `unreachableRetry` counter, separate from
the existing success-side `retry`. A companion-unreachable exception retries
twice at 350 ms, then clears the banner and sets the status line to
"Companion unreachable"; a subsequent reachable poll restores
`Connected: <host>`.

Unchanged: resolution, frame rate, GOP, B-frames, FEC wire format, RTP
payload type, packet size, ports, process audio, controller transport,
emulator lifecycle, decoder configuration (`C3.L2c`'s unconditional
`KEY_LOW_LATENCY` is kept), `D-BASE-R1`'s loss counter, the decoder's
input/output loop and every metric counter.

## Validation performed

- predecessor SHA-256 verified on every changed file before the write;
- `git diff --check` clean; `ast.parse` on both Python files;
- the real `sh ./gradlew :app:assembleDebug --no-daemon`, twice
  (`BUILD SUCCESSFUL in 23s`, then 21s after piece 3 was completed);
- `adb install -r` to the onn, twice; final APK
  `097f2fe57bf40aa1cf1edbee76e049d05d1e6479608174d12aef4d17d6738dad`;
- **runtime**: three attract sessions of the PS1 reference title (93.3 /
  93.1 / 91.8 s, zero input, `low_latency_enabled: true`), plus the
  deliberate companion-stop check of the launcher banner and its recovery;
- teardown per `TOOLS.md`: the client saw the session end before the
  companion stopped, banner confirmed absent and the status line correct; no
  companion, RetroArch, ffmpeg or FEC relay process and no listener left.

## Result

**COMPLETE / RUNTIME VALIDATED.** Record:
`evidence/D_BASE_R2_STALL_VISIBILITY_2026-09-20.md`.

**Piece 1 — three sessions of three: `max_output_gap_ms` has its own row.**
276 / 744 / 474 ms, each ending on a frame with `rx_to_decode_ms` 10-18 and
`codec_ms` 10-13, `codec_in_flight` 1-2, app queue 0-1. None would have been
recorded by the predecessor trigger. R2C reached 474 ms with **zero**
discontinuities. R2 recorded `slow_event_retained_marked` **3** against its
3 resyncs — the first non-zero marked segment on a low-latency build.

**Piece 2 — 46 heartbeats per session at a 2,006-2,076 ms cadence** (one
2,513 ms outlier). `last_output_age_ms` reads -1 before the first output,
settles at 5-12 ms, and lifts at the slow moments (193 / 125 / 92 / 57 ms in
R2B) and to 601 ms on the final heartbeat as BACK tears the session down.
`native-stream-status.last_heartbeat` read `null` before any session and the
newest record after.

**Piece 3 — banner cleared and the notice shown and then retired.** With a
game active and the companion killed, the first UI sample after resume
(+3,312 ms, of which ~2.5 s is `uiautomator dump` latency) already showed no
banner and "Companion unreachable"; the scheduled path is ~1.05 s. Restoring
the companion put the line back to `Connected: <host>`.

**What failed or is unresolved.**

- **The first validation session was run against a stale companion** and
  produced no heartbeats: an older companion held port 8765 and the
  replacement's bind failure was hidden by `nohup … &`. D-068's rule was
  the thing that caught it. Re-run; rule added to `TOOLS.md`.
- **Piece 3 as first written never retired its own notice** — "Companion
  unreachable" survived the companion returning. Found by the check,
  completed, rebuilt, re-validated.
- **Piece 1 makes the worst gap qualify, not survive.** The recent segment
  filled 64/64 in all three sessions and its span narrowed to the last
  ~26 s; a late gap is kept, an early one would be evicted. Gap rows also
  crowd out latency rows — R2B's 610 ms `max_codec_ms` event has no row.
  Both strengthen the standing `KNOWN_ISSUES.md` item for per-session top-N
  retention, which is not authorized here.
- **R2B is an unexplained decode-path outlier**: 390.8 spikes/min against
  111.9 and 111.1 for its neighbours, with the cleanest transport of the
  three. R2C was run specifically to test whether the heartbeat was the
  cause; it had the heartbeat active and sits in the ordinary band, so the
  heartbeat is not implicated on this evidence. n=2 is not a distribution.
- **The heartbeat log is append-only and unrotated** (~360 KB per hour of
  play). Registered in `KNOWN_ISSUES.md`; not fixed.
- **No terminal stall was observed**, so piece 2 is validated on its
  mechanism and not on the event it exists to capture.
- **Piece 3 reconciles only when something polls.** The banner refresh is
  `onResume`-driven; there is no timer, and this patch did not add one.
