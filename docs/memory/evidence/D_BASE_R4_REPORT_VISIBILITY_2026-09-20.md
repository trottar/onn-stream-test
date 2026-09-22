---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-R4 — session-report visibility

## Classification

**RUNTIME VALIDATED.** All four items are closed and every check in the
task's validation plan passes on one build (APK
`2a4b53d8eb135ebdbe0d53b4457966645dcd9ee68e1c69d0ed9bef734b36e6b7`).
Item 3 needed no code: the defect it names was already gone, and the
reports that prove it are named below.

Diagnostic and report-only. No streaming constant, decoder configuration,
stale-drop policy, FEC, transport, emulator or recovery behaviour changed.

## Raw numbers

### Items 1 and 2 — three 90 s sessions and one terminal stall

Each from a fresh attract-mode session of the PS1 reference title, zero
input, opened through RESUME PLAYING and ended with BACK.

| run | duration | `max_output_gap_ms` | `max_rx_to_decode_ms` | `output_age_at_end_ms` | top-gap max | == max gap | top-latency max | == max rx | `terminal_slow_event` |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- |
| J1 | 98,897 | 212 | 133 | 3 | 212 | **yes** | 133 | **yes** | null |
| J2 | 97,830 | 140 | 132 | 7 | 140 | **yes** | 132 | **yes** | null |
| J3 | 97,866 | 192 | 113 | 18 | 192 | **yes** | 113 | **yes** | null |
| K70 | 108,806 | **68,617** | 107 | **68,617** | 68,617 | **yes** | 107 | **yes** | **present** |

Every report carries `output_age_at_end_ms`, `terminal_slow_event`,
`slow_events_top_gap`, `slow_events_top_latency`,
`slow_event_retained_top_gap` / `_top_latency` and their capacities, and
every one retained 16 of 16 in both top lists. **In all four, the top-gap
list's maximum equals `max_output_gap_ms` and the top-latency list's
maximum equals `max_rx_to_decode_ms`** — the cross-check the task asked
for, so each report's worst event is present as a row.

**Item 2 is doing the work it was added for.** In J1 the 212 ms maximum was
*not* in the merged `slow_events_ge_50_ms` array: that array held 64 of 64
recent rows and the worst event had already been evicted. The top-gap list
kept it. (Same shape in an earlier build's session: `max_output_gap_ms` 123
with no row in the merged array and the row present in the top-gap list.)

**Item 1, K70 — the terminal stall.** Settled 25 s, then the `D-BASE-R3`
SIGSTOP substitute applied and **held** for 70 s; BACK pressed while still
stopped; SIGCONT afterwards.

```json
"output_age_at_end_ms": 68617,
"terminal_slow_event": {
  "terminal": true, "elapsed_ms": 108806,
  "rx_to_decode_ms": -1, "feed_delay_ms": -1, "codec_ms": -1,
  "codec_in_flight": 0, "app_queue_depth": 0, "output_gap_ms": 68617
}
```

- `max_output_gap_ms` **68,617 >= 20,000** ✓
- `output_age_at_end_ms` **68,617 >= 20,000** ✓
- a row flagged `terminal: true` ✓, carrying the same seven columns with
  `-1` for receive-to-output, feed delay and codec time, because the frame
  that would have closed the gap never arrived. That is the distinction the
  item asked for: a gap that never ended cannot have those measurements.
- the terminal gap is also the top of `slow_events_top_gap`, which is what
  keeps that list's maximum equal to `max_output_gap_ms`.

The client's own heartbeats through the stall, rising to the last one
before BACK:

```
21:45:38.471  elapsed 101563  age 61375  rendered 1760
21:45:40.475  elapsed 103587  age 63399  rendered 1760
21:45:42.497  elapsed 105614  age 65426  rendered 1760
21:45:44.528  elapsed 107644  age 67456  rendered 1760
```

`rendered_frames` is flat at 1,760 across the whole tail and the age climbs
by ~2,030 ms per heartbeat; the report's 68,617 is the final reading taken
at assembly, 1.2 s after the last heartbeat. **Before this patch the same
session would have reported `max_output_gap_ms` as whatever the last
*completed* gap was** — the `D-BASE-R3` F15 note records 135 ms for a 46 s
terminal stall.

Recovery ran during K70, as the task said it would, and is not what is
being measured: pause at 21:44:28.156, three restart attempts
(`restart` ok → `restart` fail → `full_start` ok), session ended at
21:45:45.836 still in `PAUSED_RECOVERING`.

### Item 3 — `slow_events_marked` serialization: already fixed

The 2026-09-18 defect says `slow_events_marked` "is emitted as an empty
array" while `slow_event_retained_marked` counts rows. **On the current
code that key does not exist at all.** `C3.L2b` replaced it: the marked and
recent segments are merged into the single chronological
`slow_events_ge_50_ms` array, and the two retention counters say how many
of each went in.

Proof from reports already on disk, where the merged array's length equals
marked + recent exactly:

| report | rows in `slow_events_ge_50_ms` | `slow_event_retained_marked` | `slow_event_retained_recent` | marked + recent |
| --- | ---: | ---: | ---: | ---: |
| `d_base_r2_2026-09-20/native_decoder_20260920_180217_204.json` | 67 | **3** | 64 | 67 |
| `d_base_r3a_2026-09-20/native_decoder_20260920_205736_106.json` | 75 | **11** | 64 | 75 |

Neither report contains a `slow_events_marked` key. Marked rows are
serialized, and were countable and inspectable before this patch. **No code
change was made for item 3**; the KNOWN_ISSUES entry is marked closed.

### Item 4 — rotation

The real `append_line` code path, run against a copy of the live logs with
the shipped limits (`4 MiB` / keep 3 for the heartbeat log, `1 MiB` /
keep 3 for the recovery log):

```
heartbeat limit 4194304 keep 3 | recovery limit 1048576 keep 3
heartbeat start bytes 73979
  rotation 1 after 15856 synthetic lines; live log now 262 bytes
  rotation 2 after 31750 synthetic lines; live log now 264 bytes
  rotation 3 after 47638 synthetic lines; live log now 264 bytes
  rotation 4 after 63475 synthetic lines; live log now 265 bytes
  recovery rotation 1 after 3515 synthetic lines; live log now 298 bytes
  recovery rotation 2 after 7034 synthetic lines; live log now 298 bytes
```

Resulting file set — three heartbeat rotations kept (the fourth discarded
the oldest, as `keep: 3` requires) and two recovery rotations so far:

```
logs/games/native_stream_heartbeat.log                        265 bytes
logs/games/native_stream_recovery.log                         298 bytes
logs/games/stream_log_archive/native_stream_heartbeat.log.1   4194443
logs/games/stream_log_archive/native_stream_heartbeat.log.2   4194432
logs/games/stream_log_archive/native_stream_heartbeat.log.3   4194394
logs/games/stream_log_archive/native_stream_recovery.log.1    1048662
logs/games/stream_log_archive/native_stream_recovery.log.2    1048654
```

The live log holds exactly one line after each rotation, which is the line
that triggered it: **rotation happens before the append, never after**, so
the line being written always lands somewhere.

Separately, with `keep` large enough that nothing is discarded, 5,000
appends across 25 files:

```
appended 5000 | lines across live+archive 5000 | none lost: True
ordering preserved across rotations: True
```

`tools/diagnostic_retention.py` now covers both, through a new
`stream_log_archive` family. Dry-run against the rotated tree:

```
stream_log_archive: files=5 total_mib=14.000 limit_mib=32.000 protected=3
                    would_delete=0 would_free_mib=0.000 projected_mib=14.000 blocked=False
```

and against the repository, where nothing has rotated yet, the family is
registered with `files=0`. `--self-test` exits 0. The policy SHA-256 is now
`b13fbc32dbf7f46a4ca9321985ea2d410804c15b9faaf82c3f87dce8356971b5`; an
`--apply` run must quote the new value.

**Why the rotated files live in their own directory.** A family whose
`relative_path` is `logs/games` would also reach the decoder session JSONs
(protected by extension, but in scope) and `native_video_alpha.log` (not
protected, and the host video log the diagnostic bundle reads). Putting
rotations under `logs/games/stream_log_archive/` lets the family bound
exactly the rotated artifacts and nothing else. The live logs are bounded
by rotation itself, at 4 MiB and 1 MiB.

## What did not work, and what is not known

- **A 20 s hold does not produce a 20 s terminal gap.** The first attempt
  followed the task's procedure exactly — settle 25 s, hold 20 s, BACK
  while stopped — and reported `max_output_gap_ms` 12,917 with
  `output_age_at_end_ms` 12,917 and a correct `terminal: true` row. The
  mechanism worked; the number missed 20,000 because the recovery's own
  encoder restart briefly resumed output at ~10 s and split the hold into a
  10,046 ms completed gap and a 12,917 ms terminal one. The task
  anticipated recovery acting during this run but its threshold assumes an
  uninterrupted stall. K70 holds for 70 s so that one segment exceeds
  20 s; both runs are reported, the 20 s one as the procedure-exact
  observation.
- **One defect in this patch, found by its own validation and fixed.** As
  first written, `terminal_slow_event` was only ever refreshed upward and
  never cleared, so a gap that later *closed* was still emitted flagged
  `terminal: true` — the exact confusion item 1 exists to prevent. A 70 s
  run on that build reported `terminal_slow_event.output_gap_ms` 43,757
  against `output_age_at_end_ms` 24,488, two different gaps. The slot now
  clears whenever a frame is output, so it means only "a gap that had not
  ended when the session ended"; K70 shows the two agreeing exactly at
  68,617. All four runs in the table above are on the corrected build.
- **`terminal_slow_event.elapsed_ms` is the moment of the last observation,
  not the start of the gap.** In K70 it reads 108,806, the session
  duration. The gap's start is `elapsed_ms - output_gap_ms`.
- **The top-N lists use one criterion each and keep no union.** An event
  that is 17th worst by gap and 17th worst by latency is in neither list.
- **`-1` in the terminal row's three timing columns is a sentinel**, not a
  measurement. Any consumer that averages those columns must exclude it.
- **The rotation limits are untested against a real multi-day log**; the
  4 MiB crossing was reached with synthetic lines of the real shape.
- **No perceptual observation was made**, by standing instruction.

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 21:1x | gate checked: `D-BASE-R3a` is recorded in `CURRENT.md` | proceeded |
| 21:1x | four items implemented; Python compiled; `git diff --check` clean | 1 new + 3 changed companion files, 2 client files |
| 21:20 | `assembleDebug`, `adb install -r`, companion restarted with 8765 checked free | — |
| 21:22-21:28 | first pass: three 90 s sessions and a 20 s held stall | items 1 and 2 working; terminal-slot defect found |
| 21:29 | 70 s held stall on that build | exposed the uncleared terminal slot |
| 21:31 | terminal slot now clears on output; rebuilt | `BUILD SUCCESSFUL in 12s` |
| 21:32 | `adb install -r` | **`adb: device offline`** — see Deviation |
| 21:33 | `adb reconnect offline`, then `adb connect` | device back; install succeeded |
| 21:37-21:42 | **J1, J2, J3** on the final build | all checks pass |
| 21:44-21:45 | **K70** on the final build | `max_output_gap_ms` 68,617, terminal row, ages agree |
| 21:46 | rotation exercised through the real code path; retention dry-runs; self-test | all pass |
| 21:48 | teardown | recovery save already absent; game ended from the client ("Don't Save"); banner confirmed gone (0 occurrences); companion stopped last. **No process left in state T**, no listener on 8765 / 48100-48102 / 48110. |

## Deviations

1. **ADB went offline between the rebuild and the install.**
   `adb install -r …` returned `adb: device offline` twice; per the task the
   action was not retried a third time. The connection was recovered with
   `adb reconnect offline` followed by `adb connect <endpoint>`, after which
   the install succeeded. Nothing was lost; the runs before the drop are
   reported as the first pass.
2. **Two sessions failed to reach `PLAYING` and were re-run.** After the
   reinstall the client was left in a stranded `NativeStreamActivity` with
   the stream already stopped; BACK returned it to the launcher and the
   sessions then ran normally. A later terminal-stall attempt opened the
   stream but the stabilization gate did not release gameplay within the
   25 s poll window; it was run once more and succeeded. Neither attempt
   produced a report or is counted.
3. **The terminal-stall hold was extended from 20 s to 70 s** for the
   recorded run, for the reason given above. The 20 s run is reported too.

## Artifacts

Under `evidence/d_base_r4_2026-09-20/`:

| file | SHA-256 | bytes |
| --- | --- | ---: |
| `native_decoder_20260920_213856_797.json` (J1) | `db38165f829e78643d11b1aa4b484b7394d7f82cffb6bba1fe41d97126a59ca9` | 14,090 |
| `native_decoder_20260920_214046_650.json` (J2) | `a42a3a98c2056ec5561b21d7ad2a789feb9f86c63f4196f12b5e5c551e21701e` | 14,078 |
| `native_decoder_20260920_214236_241.json` (J3) | `38452d3232a551436d707aadc081f8bc3333774fb73d44e498e643e00717f81d` | 14,033 |
| `native_decoder_20260920_214545_804.json` (K70) | `ba8f2f53aa3477bf827116a1f96442b9019b254055e2c22bbd1c64218b7ea813` | 14,674 |
| `native_stream_heartbeat.log` | `9bca4d99c174170704b47873481992277ccf5571ab44a100cc6ef7950cbe3a55` | 73,979 |
| `native_stream_recovery.log` | `21eacabf8b9eaedc88e332f5485864ef3713459c16244465c908ef4e905ae847` | 2,589 |
| `retention_plan_families_rotated_tree.txt` | `7705011eab916976b6385ab234a172300d3f6a3f1893d68665bcfc796e007ef9` | 587 |

The rotation exercise ran against a scratch copy and left the repository's
own logs untouched; its file listing and counts are quoted above in full.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts. The recovered ADB endpoint is
referred to as `<endpoint>`.
