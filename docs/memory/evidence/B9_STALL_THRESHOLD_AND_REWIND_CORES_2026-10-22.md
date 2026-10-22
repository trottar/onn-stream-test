---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 0f4b551 (+ B8 uncommitted; B9's predecessors are B8's files)
---

# B9 — the stall threshold's default is 400, and the hold's rewind is SNES-only with a savestate path for PS1

**Classification: BUILT.** No live run, NOT ADOPTED, nothing committed.
- `PRIVYHUB_STALL_SIGNAL=1` now acts at **400 ms** (150 by number).
- `PRIVYHUB_INPUT_HOLD_REWIND=1` rewinds only the allow-list (snes9x, bsnes). `all` keeps B4's behaviour for every
  core. `state` is the scratch-savestate path for PS1, for A to measure.
- **Tests:** 13 new (a loopback fake core speaking SAVE / LOAD_STATE_SLOT), 3 runs green. B2 / B4 / B6 / B7 / B8 green,
  with two disclosed test lines (§4).
- **Proof:** B9's items removed = B8's files; stall_signal differs only in `DEFAULT_MS` and its docstring.

Design `b9_2026-10-22/design_written_before_code.md`, sha256 `2b18888f…15e5`, hashed **19:03:28Z, before any B9
code**.

## 1. The stall threshold

- **`stall_signal.DEFAULT_MS` 150 → 400.** `MIN_MS` stays 150, so `=150` is B7's behaviour by number.
- **The data:**
  - BENCH-R2 d1 at 150: 2.6 stall pauses / 10 min on a clean hour;
  - d2 at 400: **0** (the client sent 9 stalls, all ended under 400 ms);
  - c1 at 150 on a flapping hour: 77 / 10 min.
- **The cost:** a downlink-only drop now pauses the core ~400-455 ms after the client's last frame, against c1's
  150-205 ms. That is ~24-27 frames without a picture instead of 9-12.
  - snes9x's rewind takes them back.
  - PS1 under `1` does not (no rewind). Under `state` there is no save for a stall-only pause (`rewind_skipped`).
- **The client is unchanged:** it sends at 150 (`debug.privyhub.stall_signal=1`). No APK for B9.
- With B8, the "gate bit over fresh output" rule reads age < 400.

## 2. Rewind per core (`rewind_cores.py`, new, 257 lines; `hold_rewind.py` +18, `input_hold.py` +5)

| `PRIVYHUB_INPUT_HOLD_REWIND` | launch config's rewind keys | at the release |
| --- | --- | --- |
| absent | none (not imported) | as today |
| `1` | **snes9x, bsnes only** | allowed core: B4 exactly. Other core (Beetle PSX HW): one `rewind_skipped` row (core, reason, counter_before), **no NCI datagram**, the resume as today |
| `all` | every core (B4's bytes) | B4 exactly. Nothing of B9 is wired. For a later PSX test |
| `state` | none (no buffer: 0 MB, 0 CPU) | the scratch savestate (§3) |

- So under `1`, Beetle PSX HW pays **no 1,074-MB buffer and no +16.6 points** (BENCH-R2 f4). That stays true until a
  method confirms PSX rewinds.

## 3. `state`: the PS1 path, designed for A to measure

- **The timing (the design's point):** a save *at* the hold's pause would restore what the paused core already holds.
  So the save comes **inside the silence, at 400 ms** (`PRIVYHUB_INPUT_HOLD_STATE_AT_MS`, 100 to H − 50).
  - It is triggered from B2's detector's 50-ms quiet tick, once per silence, only while the core is playing.
  - It runs on B9's own worker: `SAVE_STATE_SLOT 9`, the acknowledgement read ≤ 100 ms, one `state_saved` row.
  - **Slot 9:** not 0 (the recovery's staging slot), not 1-3 (the user's). Every PrivyHub save and load names its slot.
- **The load at the release** (B4's `rewind()` call sites: the hold's release, B8's resume, v2's controller return,
  B7's stall end):
  - **It needs a matching save.** The pending's onset (B8's `b8_hold_onset` when B8 moved it) must equal the saved
    silence's onset (± 5 ms). The file `<stem>.state9` under the session's state root must exist, be non-empty, and
    be newer than the save − 1 s. Otherwise: `rewind_skipped`, nothing sent.
  - **D-BASE-R3C's caveat, read first:** a mid-FMV state loaded into a PAUSED Beetle PSX HW loops; into a RUNNING core
    it plays.
  - **So the load goes into a running core.** Input masked (B4's mask), then `PAUSE_TOGGLE` and `LOAD_STATE_SLOT 9`
    in the same instant. Then the load's ack and `GET_STATUS` are read ≤ 150 ms. Confirmed = the ack names slot 9 and
    the status is PLAYING.
  - The core may run 0-1 frame with neutral input before the load lands; the load overwrites it.
  - **The row:** `input_release` (method `state`, `save_after_onset_ms`, `frames_restored`, `net_unattended_frames`)
    or `rewind_failed`. A failure never blocks the resume (tested).
- **The cost, stated:**
  - **one savestate write per silence ≥ 400 ms, not per hold:** PSX HW 16.8 MB, snes9x 0.8 MB;
  - from BENCH-R2's bins: 0.9-6.2 such silences / 10 min on the quiet cells (d1 d2 e1 e3 f1-f4), so ≤ ~105 MB of
    writes / 10 min on PSX; 14-52 / 10 min on the bad hours (a1 a2 c1), so up to ~880 MB / 10 min;
  - no rewind buffer.
  - **Unknown:** whether the save stalls a frame (RetroArch serializes on its main thread). A reads the hitch rate in
    a `none` cell under `state`.
- **What it buys:** per hold, the unattended frames become those from the onset to the save (~24-27) instead of ~57.

## 4. Tests (`tests_rewind_cores.txt`, `tests_regression.txt`)

**`tests/rewind_cores`: 13 OK, 3 runs:**
- `parse("1")` = 400, 150 by number; the host acts at 400 (stalls of 160-390 ms: no pause; 450: one);
- the config:
  - `1` (snes9x / bsnes: B4's block; PSX / fceumm: none);
  - `all` (PSX: B4's block); `state` (none);
  - STATE_AT;
- the release:
  - `1` + PSX: `rewind_skipped`, the fake core received nothing, no save mark;
  - `1` + snes9x: B4's REWIND path; `all` + PSX: B4's path, nothing wired;
- `state`:
  - **the save:** once per silence at 400 ms, not twice, not while paused;
  - **the load:** PAUSE_TOGGLE → LOAD_STATE_SLOT 9 → GET_STATUS, **the core running at the load**, the frame counts,
    one load per save, the mask released;
  - B8's moved onset still matches;
  - skipped for another silence, a missing / stale file, a stall-only pause, with nothing sent;
  - a refused load → `rewind_failed` then `resumed`;
- FlagAbsent: absent / `all` import no `rewind_cores`; the class attributes are None.

**The two disclosed test lines:**
- B7's `parse("1") == (150, None)` became 400 (the queue's change).
- B4's per-core-bytes test now generates under `all` (B4's behaviour) for PSX / fceumm. Its expected bytes are
  unchanged.

**Regression:** every suite under `tests/` is green from the copy (`input_hold_rewind`'s 2 env skips as before). The
four `tools/` tests fail identically on an untouched HEAD copy (B8 §3).

**Proof** `proof_flag_absent_host.md`:
- `hold_rewind.py` with its 5 items removed and `input_hold.py` with its 2 removed are identical to B8's;
- `stall_signal.py` is identical once the docstring and `DEFAULT_MS` are set back.

## 5. For BENCH-R3 (A)

- **PS1 `state` on one `@both` cell:** `PRIVYHUB_INPUT_HOLD_REWIND=state`, the rest of the stack as on SNES.
  - Expect one `state_saved` ~0.40-0.45 s into each blackout.
  - Expect one `input_release` with method `state` at B8's resume. `frames_restored` ≈ 33-36, `net_unattended_frames`
    ≈ 24-27.
  - `tools/unattended_frames.py --net` ≈ the latter.
  - Read RetroArch's log for "Loaded state from slot #9" or a failure, and whether the picture after the load plays.
- **The hitch cost of the saves:** a `none` cell under `state` (or the same cell's clean minutes).

## 6. Files

- **`b9_2026-10-22/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b9.diff`, `proof_flag_absent_host.py` / `.md`;
  - `tests_rewind_cores.txt`, `tests_regression.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/rewind_cores.py` (new), `stall_signal.py`, `hold_rewind.py`, `input_hold.py`;
  - `tests/rewind_cores/` (new), `tests/stall_signal/test_stall_signal.py` (1 line),
    `tests/input_hold_rewind/test_hold_rewind.py` (3 lines);
  - `docs/memory/patches/B9_STALL_THRESHOLD_AND_REWIND_CORES.md`, `logs/b9_git_status.txt`.
- **Disclosed:** B9's first quick suite run (B2 / B4 / B6 / B7 / B8) went from the tree, not the copy. It wrote no
  file: the tree's files newer than B8's design hash are only this work's edits.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing fetched, deleted,
  adopted or committed.
