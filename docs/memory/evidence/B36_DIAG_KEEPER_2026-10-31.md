---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8 (B36 uncommitted; built in /tmp/b_q31l_b36, new files only)
---

# B36 — the always-on diagnostics keeper (`privyhub-diag`), the one-line read (`diag_read.py`) and `diag_check.py`

**Classification: BUILT** (new files only; no flag — nothing runs until A installs the unit at home).
- **Tests:** `tests/diag_keeper` 13, `tests/diag_read` 11, `tests/diag_check` 4 — green three runs, with B30's
  `trip_log_keeper` 12 and `trip_check` 8 unedited and green; **5 mutations caught**; every host suite in the copy the
  baseline's outcomes plus the three new.
- **The dry run (read-only) over the trip keeper's copies:** TRIP-R2 §1's restart table **47 / 48 cells the same**
  (the one: TRIP-R2's hand label "31, never PLAYING" against diag_read's "(none PLAYING)", the same fact); TRIP-R2's
  `sessions.tsv` **900 / 900 cells the same** (36 sessions × 25 columns); the joined chunks a byte prefix-match of
  TRIP-R2's `copies/` for all seven logs and 36 / 36 reports.
- **Absent = today, PROVEN:** 0 existing files changed; `trip_log_keeper.py` and `trip_check.py` byte for byte.
- NOT installed, NOT started, NOT adopted; nothing committed.

Design `b36_2026-10-31/design_written_before_code.md`, sha256 `7ab4a878…af775`, hashed **17:38:02Z, before any B36
code**.

## 1. Built (`b36.diff`, 8 new files)

**`tools/diag_keeper.py` — `privyhub-diag`.**
- **B30 made permanent.** `DiagKeeper` subclasses B30's `Keeper` and reuses its redactor, tails (rotation by inode into
  `stream_log_archive/<log>.1..3`), samplers and journal reader. So `tools/trip_log_keeper.py` must stay in the tree
  while the unit exists; it is not edited.
- **What it copies:** B30's sources (G4-S4's logs in `logs/games/`, `wan_sessions` / `session_audit` / `impairment`,
  each game log from its first byte, new decoder reports and audio-timing files, the companion's journal) **plus B35's
  `logs/vod_client.jsonl` and `logs/vod_range.jsonl`**. The other new client rows (`surface_lost`, `pad_slots` and its
  heartbeat key, `input_release` `why`, the ladder's `in_place`) arrive inside logs already copied.
- **Where:** `~/privyhub_diag/<YYYY-MM-DD>/` (the UTC date of the copy): `raw/<log>/<NNNNNN>_<UTC><ext>` never
  overwritten, `samples/{overlay,session,copies}.jsonl`, `manifest.sha256`. One set of tails runs across days, so
  midnight is not a gap (tested byte for byte).
- **At the root:** `status.txt`, `STOP`, `sessions.jsonl`, `retention.jsonl`, and `state.json` (each tail's inode and
  offset, so a unit restart resumes where it stopped when the file is the same, else from its end as B30). A root
  inside the repo is refused.
- **Cadence:** copies every 300 s, samples every 60 s. **No cap.** It ends on `STOP` or SIGTERM (`systemctl stop`), with a
  final copy; SIGTERM leaves no `STOP` file behind. It holds nothing open; no stream, no restart, no adb, no game.
- **Redacted:** every chunk, sample and summary row, through B30's redactor.
- **Retention — the one deletion it makes:** at the start and at every UTC date change, an entry **directly under the
  root** named `YYYY-MM-DD`, a real directory (not a symlink), dated **more than 30 days before today**, is removed
  whole. One row per removal goes in `retention.jsonl`. Tested: a file named like a date, a symlink named like a date
  (its target intact), a nested date dir, `2026-13-45`, and the 30-day-old dir are all kept.
- **The per-session row (`sessions.jsonl`):**
  - **When:** each `session_ended` seen in the recovery log (checked every 60 s) schedules its row **90 s later**, after
    the client's report and the WAN row have arrived.
  - **How:** `diag_read`'s own reader over the live logs (6 h back).
  - **Columns:** `start_utc`, `end_utc`, `length_s`, `core`, `title` (class + tag), `players`, `slot_map`, `path_class`,
    `rung_history` (with `in place`), `rungs`, `start_rung`, `lost_post_fec`, `rtt_p50_ms` / `rtt_p95_ms`,
    `rendered_fps_med` / `_min`, `resyncs`, `pauses`, `holds`, `stalls`, `rewinds` (method, `why`), `restarts`
    (trigger, paused / away ms, `surface_lost`, the silences and stalls before), `restart_cause`, `surface_lost`,
    `end_kind`, `hitch_s` / `hitch_by` / `hitch_s_per_10min`, `silences` / `silences_user` / `silences_per_10min`,
    `max_silence_ms`, `underruns`, `starvation`, `rssi`.
  - `players` and `slot_map` come from B34's `pad_slots` and are `null` with today's client.
  - A failing summary writes `{"error": <type>}` and the keeper goes on.
- **`tools/privyhub-diag.service`:** the user unit (`ExecStart=/usr/bin/python3 -B
  %h/Projects/onn-stream-test/tools/diag_keeper.py`, `Restart=on-failure`, `Nice=10`, `WantedBy=default.target`;
  equal to `diag_keeper.py --unit`). Autostart as the companion's H3. **Not installed.**

**`tools/diag_read.py <range>`.**
- **The logic** is TRIP-R2's `trip_r2_read.py`, copied (not imported from `evidence/`) and parameterised: the window,
  the sources, the zone, and the tags. UX-R3's hitch definition is unchanged.
- **Ranges:**
  - `last night`: yesterday 17:00 to today 08:00, hub local time; DST is handled (tested across 1 Nov);
  - `today`;
  - `2026-10-30 21:00..05:00` (UTC; an end not after the start is the next day);
  - `…..YYYY-MM-DD HH:MM`;
  - `trip`: the trip keeper's dir, its whole span.
- **Sources:** by default the `~/privyhub_diag` day-dirs that overlap the range. Also `--source` (any keeper dir, or
  TRIP-R2's `copies/` shape), `--live` and `--trip-dir`. All opened read-only; tested by tree hash.
- **Output:** one Markdown file under `docs/memory/evidence/reads/`, never overwritten, with:
  - **the per-session table** (G4-S4's columns + players / slot map, rewinds, restarts with trigger);
  - **the per-10-min table**;
  - **every client restart with its cause:**
    - the client's trigger, paused and away ms from the report of the session the restart started;
    - B32's `surface_lost`;
    - the uplink silences and stalls in the 20 s before;
    - the rung before → after;
    - the last step-up's Δt, and whether it was in the same session;
  - **every rewind / pause / hold / stall** with its cause (B33's `why`);
  - the ladder transitions with `in place`, the `pad_slots` rows, the VOD rows and the range log's summary;
  - **the ±60-s per-second view** around every restart and every stall, every `state_saved` row with
    `--around-saves`, and any `--around HH:MM:SS`.

**`tools/diag_check.py`** is `trip_check.py`'s six lines with the sixth now
`diag-keeper: <~/privyhub_diag/status.txt>; unit privyhub-diag <state>`. Lines 1-5 are the same functions (tested
equal). **`tools/trip_check.py` is kept unchanged.** The trip runbook tells the user to run it from the friend's house,
and nothing is deleted. A may retire it after the trip.

## 2. Tests (`tests_b36_x3.txt`, `tests_mutations.txt`, `tests_regression_after.txt`)

Everything runs on fake logs and a fake clock, in /tmp temp dirs. The shared fixture is
`tests/diag_read/diag_fixture.py`: two sessions; a restart with the report's cause; a stall released by `resume` /
`no_loss`; an in-place step; `pad_slots`; `surface_lost`; VOD rows. Every log is in two chunks split mid-line.
- **The keeper:**
  - midnight roll with no byte lost;
  - VOD logs copied and redacted;
  - resume after a unit restart (same inode: the bytes written while down kept; new inode: from its end);
  - SIGTERM: a final copy and no `STOP`;
  - the repo root refused;
  - a `session_ended` → one row ≥ 90 s and < 90 + 121 s later, and none before;
  - **the real summary over live-layout logs** (slot map, rewinds `resume (no_loss)`, `in place`, every column);
  - a failing summary → an `error` row;
  - retention, alone and in the run (at the start and at the date change);
  - the unit text equal to the file.
- **The reader:**
  - the range parser (including DST);
  - keeper chunks equal to the live layout;
  - both sessions' columns;
  - the restart and its cause;
  - every Markdown section, with the source's tree hash unchanged;
  - never overwrites;
  - `trip`'s span;
  - the default day-dirs.
- **The check:** the sixth line, lines 1-5 equal to `trip_check`'s, every source down, redaction.
- **Mutations, all caught:**

| mutation | result |
| --- | --- |
| retention `<` → `<=` | 2 fail |
| summary delay 0 | 1 fails |
| symlink followed | 1 error; `rmtree` refuses, target intact |
| `in place` dropped | 1 fails |
| the restart's cause not read | 1 fails |

- **Host suites:** `tests_regression_after.txt` = `tests_regression_queue_l_baseline.txt` line for line, plus
  `diag_check` / `diag_keeper` / `diag_read` OK (571 host tests ran). The four tools/ tests fail in a copy as at every
  baseline.
- **One `--once` smoke run with the real readers into a /tmp root:** 1 copy and 1 sample (no-peer, idle); journal
  "-- No entries --". **`~/privyhub_diag` was not created.**

## 3. The dry run (`dry_run/`; the trip dir only read: every existing file's sha256 the same before and after)

- **`diag_trip_r2_window.md`:** `--source trip_2026-10-30 "2026-10-30 21:00..06:10"`, TRIP-R2's window. **`diag_trip_whole.md`:**
  `trip`, the whole span. Both have 36 sessions, 6 restarts and 5 stalls. No game ran outside the window.
- **`compare.md`** (`compare_trip_r2.py`):

| restart | session | rung | step-up Δt | trigger | paused / away ms | before (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| 01:20:44 | 14 Blitz | 4000 → 4000 | 397 s (earlier session) | surface | 1720 / 1787 | silence 1736 |
| 03:26:05 | 20 kart | 4000 → 4000 | none in session (6511 s earlier) | surface | 4511 / 8582 | silences 283, 7467 |
| 04:19:21 | 25 golf | 4000 → 4000 | none in session | surface | 1877 / 2027 | stall 419; silence 1918 |
| 04:30:12 | 26 golf | 6000 → 4000 | 95 s | surface | 2070 / 1039 | stall 464; 292 / 303 / 495 |
| 04:34:41 | (none PLAYING) | 4000 → 4000 | 363 s (earlier session) | surface | 767 / 1188 | silence 1190 |
| 05:19:35 | 35 brawler | 4000 → 4000 | none in session (178 s earlier) | (no report) | — | silence 16079 |

- **Every TRIP-R2 cell the same but one (47 / 48).** TRIP-R2 labels the 04:34:41 start "31, never PLAYING"; that start
  never wrote `session_started`, so diag_read does not number it.
- **TRIP-R2 printed a Δt for two step-ups in an earlier session:** 01:20:44 at 397 s and 04:34:41 at 363 s. For the
  other three it wrote "(none in the session)". diag_read prints both the value and the session.
- **`sessions.tsv`:** 0 of 900 cells differ.
- **The joined chunks:** byte prefix-matches of TRIP-R2's `copies/`. The copies were taken to 16:58Z; the keeper runs on.
- **The other standard reads (`g4_s4_live_reader.txt`):**
  - **G4-S4's window through the live logs:** the same 13 sessions with the same start, end, core and rungs.
  - **Some cells differ by definition, not reproduced:**
    - hitch s: 4 / 1 against G4-S4's 1 / 5 (sessions 10 / 12);
    - resyncs: 8 / 0 against G4-S4's 10 / 2 (sessions 10 / 11);
    - silences: 1 in sessions 10 and 11 against 0;
    - holds: diag_read counts every `input_hold*` row (TRIP-R2's definition, which includes `input_hold_skipped_paused`);
      G4-S4 counted the Home holds.
  - **UX-R3 / UX-R4:** their windows predate the live heartbeat log's oldest row (2026-10-23T18:48Z), so they are not
    reproducible from disk. The reader's tables carry their columns.

## 4. Files

- **`b36_2026-10-31/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `predecessors/` (`trip_log_keeper.py`, `trip_check.py`: unchanged, kept as the sources B36 builds on) +
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `b36.diff`, `proof_flag_absent.md`;
  - `tests_b36_x3.txt`, `tests_mutations.txt`, `tests_regression_queue_l_baseline.txt`, `tests_regression_after.txt`;
  - `dry_run/` (two reads, `compare.md`, `compare_trip_r2.py`, `console.txt`, `run_at.txt`), `g4_s4_live_reader.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `patches/B36_DIAG_KEEPER.md`. The code is in `/tmp/b_q31l_b36` and `b36.diff` (the coordinator
  applies it).
- **Left in /tmp:** `b_q31l_b36` (the copy), `b_q31l_b36_scratch/` (`mut_*` ×5, `smoke_root/`, the trip dir's
  before/after hashes, dry1/dry2), and the tests' `b36_*` temp dirs.
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft;
  - `privyhub-trip-log` and `evidence/trip_2026-10-30/` only read;
  - nothing of A's touched; nothing fetched; nothing committed;
  - nothing deleted but the retention tests' own dirs inside their /tmp roots.

## 5. Coordinator's fix after the merge (`b36.diff` regenerated; `b36_worker_original.diff`; `tests_coordinator_fix.txt`)

- **The mismatch:** the worker read `in_place` from the ladder's `transition` row. B32-host writes it on the step's
  **`transition_done`** row (`adaptive_bitrate_live.py`, with `ssrc_unchanged` / `splice_gap_ms`). As built, `diag_read` would
  never have shown an in-place step.
- **The fix (`tools/diag_read.py` +8):** each `transition` takes `in_place` from the first `transition_done` carrying it within
  10 s after it. The fixture now writes `in_place` on a `transition_done` row 0.6 s after the step, as the ladder does.
- **Tests:** `tests/diag_read` 11 green ×3; a sixth mutation (the carry removed) fails 2. The other row names were checked
  against the code and match: `pad_slots` rows hold `slots`; `vod_client` / `vod_range` rows carry `event` and `at_utc`;
  the range row's close field is `closed`; `surface_lost` and `input_release.why` as named.
- `b36_worker_original.diff` is the worker's diff before this fix; `b36.diff` is the one to apply.
