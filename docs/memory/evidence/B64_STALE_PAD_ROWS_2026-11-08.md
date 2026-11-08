---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 6fcd2f23 (B64 built after B63 in /tmp/b_q15w_work; its diff against the after-B63 snapshot; applied to the tree fourth, uncommitted)
---

# B64 — the stale pre-session `pad_slots` rows: tagged `stale: true`

**Classification: SETTLED + BUILT**, host logging only (no behaviour; no flag: the hold-to-join rows' own fields).
- **Tests:** `tests/b64_stale_pad_rows` **5** green ×3; `pad_slots` 5, `pad_slots_changes` 7, `player_prompt` 11
  green; every host suite as the baseline, plus B61-B64's.
- **Mutations:** 3. M3 survived the first run; a test was added and all 3 are caught.
- Nothing committed or adopted.

Design `b64_2026-11-08/design_written_before_code.md`, sha256 `61db151b…ec152828`, hashed **23:18:10Z, before any
B64 code**.

## 0. Settled (HOME-7's recovery log, 21:55-22:37Z)

- **After every start that follows a session (14 of 14),** one `pad_slots` `change` row:
  - `heartbeat_sequence` 1, state `ENDED`;
  - **the previous game's `players_joined`**, labels but **no `claimed_by`**.
  - The real joins follow with claims, some also before `session_started`.
- **The source:** the host's start row (`native-stream-start` carries no join fields) resets the count. The client's
  first heartbeat then sends the count its prompt still holds from the last game, before any claim.
- **The client's order** is a client change (an APK), not built.

## 1. Built (`b64_2026-11-08/b64.diff`, 3 files)

- **`pad_slots.SlotsLog`:** `since_start` is set by `start` and cleared by the first row with a claim (or
  `players_joined` 0).
- **A change while it holds, with `players_joined` > 0 and no claim,** gets `stale: true`, and the heartbeat row
  `pad_slots_stale: true`.
- **One deviation from the hashed design, disclosed:** the design said a stale row would not update `last_joined`.
  That would repeat the stale row at every heartbeat until a claim. So `last_joined` is updated as today; the first
  real join still writes a change row, because its claims change the slots.
- **Not tagged:**
  - a client that sends no `players_joined` (byte for byte);
  - `players_joined` 0;
  - rows with claims, including pre-session ones;
  - an unclaimed row after a claim.
- `diag_read` takes each session's last map inside the session, so its tables are unchanged.

## 2. Tests (`tests/b64_stale_pad_rows`, 5)

- **HOME-7's sequence:** start → seq 1 `joined 2` with no claims (`stale`) → seq 2 the same (no new row; the
  heartbeat still `pad_slots_stale`) → seq 3 a claimed join (no tag) → seq 4.
- **A restart:** tagged again.
- **Not tagged:** claimed pre-session rows, no join key, `joined 0`; an unclaimed row after a claim.
- **A no-join client:** its row byte for byte.
- **Mutations:** the tag condition dropped; the start not arming it; a claim not disarming it (survived first; caught
  after the added test).

## 3. For A (HOME-8)

At every start: the seq-1 carry-over row reads `stale: true`, and records count only untagged rows.

## 4. Files

`b64_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `.sha256` + `design_hashed_at.txt`;
- `b64.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md` (the default proof);
- `tests_x3.txt`, `tests_mutations.txt`, `tests_host_baseline.txt`, `tests_host_b64.txt`, `tests_in_the_tree.txt`;
- `redact_check.py` + `.txt`, `title_check.py` + `.txt`, `manifest.sha256`.

Patch note: `patches/B64_STALE_PAD_ROWS.md`.
