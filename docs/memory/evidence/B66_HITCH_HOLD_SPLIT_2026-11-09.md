---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e (B66 built after B65 in /tmp/b_q16x_work; its diff against the after-B65 snapshot; applied to the tree second, uncommitted)
---

# B66 — UX-R3's hold-resume split; the `launch_ports` row

**Classification: BUILT** (tools and one added host row; default-on, disclosed).
- **Tests:** `tests/b66_hitch_split` **6** green ×3; `diag_read` 11, `diag_check` 4, `diag_keeper` 13 unchanged and
  green.
- **Mutations:** 4, all caught. Default proof: `b66_2026-11-09/proof_flag_absent.md`.

Design `b66_2026-11-09/design_written_before_code.md`, sha256 `ecc8fae4…417c38f0`, hashed **00:42:36Z, before any
B66 code**.

## 0. Settled

- **HOME-8 C28's 3:01 N64 session** read 6.6 hitch s / 10 min from 2 seconds:
  - the R second was the Home hold's own resume (`resumed via stall_end`);
  - the L second was one link-loss second.
- **The holds' resumes** come `via` `stall_end` / `stall_quiet` / `client_ready_stall` (the input hold's
  `input_release` / `hold_*`); a link recovery's do not.
- **`--device`, `capable` / `capped_from` and `layout`** were only in the game log or the start response.

## 1. Built (`b66_2026-11-09/b66.diff`, 6 files)

- **`tools/diag_read.py`:**
  - a hold resume's own second and the next two (3 s) are its **hold-resume seconds**;
  - `summarize` / `session_row` add `hold_resume_s`, `hitch_s_bar` and **`hitch_s_bar_per_10min` (the bar's number
    from now on)**;
  - **`hitch_s` / `hitch_s_per_10min` stay today's** (both shown);
  - the tables gain "hold-resume s" and "bar hitch s / 10 min"; the per-second view marks `h`.
- **`tools/diag_check.py`:** the `last session:` line covers N64 too, and adds `(bar <x> / 10 min, hold-resume <n>
  s)` when the row has them.
- **The `launch_ports` row** (`plugins/games.py`, after every successful launch):
  - `system`, `kind`, **`device_args`** (`EmulatorManager._last_device_args` from the RetroArch command; `[]` for
    PCSX2);
  - **`ports_set`** (with B63's `capable` / `capped_from`);
  - an N64 launch's `layout` / `remap_binds`; `players_joined` / `players_chosen`.
  - Never raises.
- **C28 re-read with the split** (`c28_reread.md`, read-only over the keeper's copies): today's 6.6 / 10 min →
  **hold-resume 1 s, bar 3.3 / 10 min** (the L second only).

## 2. Tests (`tests/b66_hitch_split`, 6; B36's fixture evening extended)

- **Without a hold resume:** B36's 4 / 8.0 and a bar equal to it.
- **A `resumed via stall_end` 0.4 s before the fixture's R second:** `hitch_s` 4, `hold_resume_s` 1, bar 3 (6.0 /
  10 min); the tables' columns; `Rh` in the per-second view.
- **Not counted:** a link `resumed via client_ready`; a hold resume whose 3-s window ends before the hitch.
- **`diag_check`:** the N64 line with the bar; an old PS2 row → today's line; PS1 → none.
- **The row:** a fake launch → one `launch_ports` with the fields; a failed launch → none.
- **Mutations:** the window 3 → 1; every resume a hold; `hitch_s` reduced instead of the bar; `device_args` dropped.
  All caught.

## 3. For A

**The pre-registered hitch bars compare `hitch_s_bar_per_10min` from HOME-9 on** (C32); `hitch_s_per_10min` is
reported beside it.

## 4. Files

`b66_2026-11-09/`:
- the start files; the design + hash;
- `b66.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`, `c28_reread.md`;
- `tests_x3.txt`, `tests_mutations.txt`, `tests_host_baseline.txt`, `tests_host_b66.txt`, `tests_in_the_tree.txt`;
- `redact_check` / `title_check` + `.txt`, `manifest.sha256`.

Patch note: `patches/B66_HITCH_HOLD_SPLIT.md`.
