---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e (HOME-8 committed; B65 built in /tmp/b_q16x_work, applied to the tree first of four, uncommitted)
---

# B65 — the N64 first start that never got ready: the link and the onn's latched gate (not the Continue load)

**Classification: SETTLED (the queue's hypothesis does not hold) + BUILT.**
- **The cause's fix is client-side,** in B67's APK (item 5, the start gate re-arms).
- **The queue's guard is built, host, inside `PRIVYHUB_N64=1`:** an N64 load only into a core that answers `PAUSED`
  now.
- **Tests:** `tests/b65_n64_continue` **7** green ×3; 3 mutations caught. Absent = today
  (`b65_2026-11-09/proof_flag_absent.md`).
- Nothing committed or adopted.

Design `b65_2026-11-09/design_written_before_code.md`, sha256 `4b9b49ae…8e3dc2e5`, hashed **00:39:19Z, before any
B65 code**.

## 0. Settled (HOME-8 C24's first T6 start, read in place)

- **The Continue load went into a paused core.**
  - The launch at 23:40:59 (`players_joined=3`) pauses the core (the paused handoff).
  - `load-state?slot=1` at 23:41:03 → 200. **`load_state` refuses unless the manager holds the game paused** (every
    system).
  - RetroArch sat at 2.9 % CPU (paused).
  - The second start resumed the same RetroArch.
  - **Not the B61 hazard.**
- **The hub sent a steady stream:** 60 frames and 789-834 packets every second from 23:41:04 to the end.
- **The link lost packets from 23:41:07 to 23:41:21:** 30-700 per 2-s report. The onn's report shows 1,887 lost (7
  %), 4 sequence resyncs, 19 forward gaps and 66 dropped frames.
- **The onn's gate timed out at ≈23:41:20 and latched "Game stream isn't ready".** The gate is 15 s and needs 6
  clean ticks. Only a recovery re-arms it.
- **The link was clean from 23:41:23 to the user's Back at 23:41:38,** but the gate stayed failed.
- **The second start** lost 9 packets in 91 s and was ready in 8 s.
- **PS1 would do the same** with the same loss. **No server-side "launching" status** exists in the protocol: the
  gate's phases are the onn's own.

## 1. Built (`b65_2026-11-09/b65.diff`, 4 files)

- **`EmulatorManager.load_state`** (N64 only, B61's `_n64_core`):
  - right before `LOAD_STATE_SLOT 0`, `GET_STATUS` must answer `PAUSED` within **1.5 s**;
  - **else the load is never sent:** `EmulatorError` "N64 load refused: n64: core not paused <state>" / "…command
    port silent", and a `continue_skipped` event;
  - a done load gives `continue_load` (`slot`, `status_ms`, `load_ms`).
- **The plugin's `load-state`** writes the event as a recovery row (`continue_load` / `continue_skipped`). The onn's
  existing load-failure path follows: the title stays paused at its fresh start, and Resume plays it.
- **The cause's fix:** B67 item 5 (`StartGateRearm`). A start gate whose window ends while frames keep coming re-arms,
  up to 3 times (60 s); `debug.privyhub.start_gate_rearm=0` = before.

## 2. Tests (`tests/b65_n64_continue`, 7; a real `load_state` on a temp project with a fake command port)

- **N64:**
  - `PAUSED` → the `GET_STATUS` right before `LOAD_STATE_SLOT 0`, and `continue_load`;
  - a core answering at 0.8 s → the load waits and goes (`status_ms` ≥ 750);
  - silent → refused in under 2.5 s, no load, `continue_skipped`;
  - `PLAYING` → refused, no load.
- **PS1:** no `GET_STATUS` before the load, no event.
- **A fresh manager:** no event.
- **The plugin:** the row written and the attribute cleared, on a refused load too.
- **Mutations:** the check removed; the bound ignored (one try); the guard on every system. All caught.

## 3. For A (HOME-9 C30)

- **T6 with its stored state (Continue):**
  - the `continue_load` row (`status_ms` small);
  - the ready within the onn's window, or a re-arm (B67) if the link drops then;
  - no "Game stream isn't ready" while frames flow.
- **A `continue_skipped` row** says why the title started fresh.

## 4. Files

`b65_2026-11-09/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `.sha256` + `design_hashed_at.txt`;
- `b65.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`;
- `tests_x3.txt`, `tests_mutations.txt`, `tests_host_baseline.txt`, `tests_host_b65.txt`, `tests_in_the_tree.txt`;
- `redact_check.py` + `.txt`, `title_check.py` + `.txt`, `manifest.sha256`.

Patch note: `patches/B65_N64_CONTINUE_LOAD.md`.

**One line for the user:** the game that "didn't start" was a 15-second Wi-Fi drop right at the start. The TV gave up
just before the link came back. With the new app it keeps waiting while the picture is still coming (up to a minute).
The Continue load was fine.
