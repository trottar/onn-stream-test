---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-R4 — session-report visibility

## Purpose

Four open diagnostic-visibility items, all of which cost evidence in
earlier work:

1. **A gap that never ends is invisible.** `drainOutputs` records a slow
   event only when a frame comes out, so a terminal stall leaves
   `max_output_gap_ms` at the last *completed* gap — `D-BASE-R3` F15 reports
   135 ms for a 46 s stall.
2. **The two rolling segments are FIFO**, so a long session evicts its own
   worst events; the 7,341 ms event of 2026-09-20T00:27 is not in its own
   report, and after `D-BASE-R2` gap rows crowd out latency rows.
3. **`slow_events_marked` reported as emitted empty** (2026-09-18).
4. **`native_stream_heartbeat.log` and `native_stream_recovery.log` grow
   without bound** and `tools/diagnostic_retention.py` does not cover them.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`:
  `b4c608e0384e974657109bf210cd5f1bba34a1fcea53e504cf4c2cc784af66f7`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `731b959518ab04fafd4bc3e9b33648018f1fdfc69012e98a9babd031f2e1aa39`
- `companion/games/native_stream_heartbeat.py`:
  `08b63405aa37e2413e97f1c6d91932bc8a70d2e66b4b474cb9f56542771a28f3` (pre-patch:
  `7ad5d0f98cfb591ed5670cbd8ecee7ccd71d4b8b5c99a1ff0fdeff7dc5ef611a`)
- `companion/games/link_drop_recovery.py`:
  `f0e2fb920a04f11b72deb60d031955c82a11c05caad63105bd920c9b793b7f93`
- `companion/diagnostics/retention.py`:
  policy SHA-256 `…` before the new family (see Result)

## Changed scope

**New: `companion/games/log_rotation.py`**
(`8fb167c23f1e062e864f0b70a96d0bdc1d6beae2ef5b78d1bdaefbbe531e9e20`).
`rotate_if_needed()` and `append_line()`. Rotation runs **before** the
append, never after, so the line being written cannot land in a file that
is about to be renamed. Rotated files go to a sibling
`stream_log_archive/` directory.

**`companion/games/native_stream_heartbeat.py`**
-> `08b63405…a28f3`: appends through `append_line` at `MAX_LOG_BYTES`
4 MiB, `KEEP_ROTATED` 3; the append result reports `rotated`.

**`companion/games/link_drop_recovery.py`**
-> `39bffd32afbf3b85cc9a2da0079aae8a5fa92a55c38e0df7f423c037dc7a8fe0`:
the same, at 1 MiB and 3.

**`companion/diagnostics/retention.py`**
-> `7a9e83f9b7cd60301aa7b5b00743a7592502fa0a3fe27e9d98a768f8cd208170`:
new `stream_log_archive` family, `logs/games/stream_log_archive`, 32 MiB,
`min_keep_files` 3. Deliberately not `logs/games`, which would put the
decoder session JSONs and the native video host log in the same family's
reach. **The policy SHA-256 changes to
`b13fbc32dbf7f46a4ca9321985ea2d410804c15b9faaf82c3f87dce8356971b5`**; any
`--apply` run must quote the new value.

**`AvcLowLatencyDecoder.kt`**
-> `375516b6d50fe3f069fd8befeb693ea7d20cd92f2d59e73bd98c32b613458485`:
`MAX_TOP_SLOW_EVENTS` 16 with two magnitude-ordered lists
(`topGapSlowEvents`, `topLatencySlowEvents`) maintained in
`recordSlowEvent` alongside the untouched marked and recent segments;
`noteOutputStall(nowNs)`, which raises `maxOutputGapMs` when the age since
the last output exceeds it and refreshes a single `terminalSlowEvent` slot;
the slot clears whenever a frame is output, so it means only "a gap that
had not ended when the session ended"; snapshot accessors for all three.

**`NativeStreamActivity.kt`**
-> `4ba8a7a659ef22d82e1a34323134739dfa60b74656a475adac2c7046ca57aff9`:
`noteOutputStall` on the existing 500 ms tick and once more at the top of
`buildSessionReport` before `snapshot()`; new report keys
`output_age_at_end_ms`, `terminal_slow_event` (an object flagged
`terminal: true` with the seven named columns, or null),
`slow_events_top_gap`, `slow_events_top_latency` and their
`slow_event_retained_*` / `slow_event_capacity_*` counters; shared
`elapsedMsOf` / `slowEventRows` helpers.

APK: `2a4b53d8eb135ebdbe0d53b4457966645dcd9ee68e1c69d0ed9bef734b36e6b7`.

**No code was written for item 3** — see Result.

**Unchanged:** every streaming constant, decoder configuration, the 60 ms
stale-drop policy, FEC, transport, the emulator, the recovery state machine
and its constants, and the existing `slow_events_ge_50_ms` array's shape,
meaning and capacities.

## Validation performed

- `ast.parse` on all four companion files; `git diff --check` clean;
- real `sh ./gradlew :app:assembleDebug --no-daemon`, `adb install -r`;
  companion restarted with 8765 checked free first (D-068);
- three 90 s attract sessions plus one terminal-stall session, all on the
  final build, driven per `TOOLS.md`;
- rotation exercised through the real `append_line` path; retention
  dry-runs against the rotated tree and the repository; `--self-test`;
- teardown per `TOOLS.md`: game ended from the client, banner confirmed
  gone, companion stopped last, no process left in state T, no listener
  left.

## Result

**RUNTIME VALIDATED.** Record:
`evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`.

| run | duration | `max_output_gap_ms` | `output_age_at_end_ms` | top-gap max == max gap | top-latency max == max rx | terminal row |
| --- | ---: | ---: | ---: | --- | --- | --- |
| J1 | 98,897 | 212 | 3 | yes | yes | null |
| J2 | 97,830 | 140 | 7 | yes | yes | null |
| J3 | 97,866 | 192 | 18 | yes | yes | null |
| K70 | 108,806 | **68,617** | **68,617** | yes | yes | **`terminal: true`** |

**Item 1.** K70 held the SIGSTOP substitute for 70 s and pressed BACK while
still stopped: `max_output_gap_ms` 68,617 and `output_age_at_end_ms` 68,617,
with a `terminal: true` row carrying `-1` for receive-to-output, feed delay
and codec time, because the frame that would have closed the gap never
arrived. Before this patch the same session would have reported the last
completed gap.

**Item 2.** All four reports retained 16 of 16 in both top lists and in
every one the top-gap maximum equals `max_output_gap_ms` and the
top-latency maximum equals `max_rx_to_decode_ms`. In J1 the worst event was
**not** in the merged array — 64 of 64 recent rows, the maximum already
evicted — and only the top-gap list held it.

**Item 3 needed no change: the defect was already gone.** `C3.L2b`
replaced `slow_events_marked` with a merged `slow_events_ge_50_ms`, and two
reports already on disk show the merged array's length equal to
marked + recent exactly (67 = 3 + 64; 75 = 11 + 64), with no
`slow_events_marked` key present. KNOWN_ISSUES marked closed, citing those
reports.

**Item 4.** Rotation at 4 MiB / keep 3 and 1 MiB / keep 3 confirmed through
the real code path; after each rotation the live log holds exactly the line
that triggered it, and a 5,000-append run across 25 files lost no line and
preserved ordering. `tools/diagnostic_retention.py` lists the family
(`files=5 total_mib=14.000 limit_mib=32.000`).

**One defect in this patch, found by its own validation and fixed.**
`terminal_slow_event` was initially never cleared, so a gap that later
closed was still flagged `terminal: true` — a 70 s run on that build
reported a 43,757 ms "terminal" gap against `output_age_at_end_ms` 24,488,
two different gaps. The slot now clears on output; K70 shows the two equal.

**Also worth knowing:** `terminal_slow_event.elapsed_ms` is the moment of
the last observation, not the gap's start; the top-N lists keep no union,
so an event 17th worst on both axes is in neither; and the `-1` timing
columns are sentinels that must be excluded from any average.
