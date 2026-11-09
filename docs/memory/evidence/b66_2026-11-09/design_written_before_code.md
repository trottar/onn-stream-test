# B66 — design, written before any B66 code (the hitch metric and the hold; the launch_ports row)

Queue: `handoffs/QUEUE_2026-11-09X.md` §B66. Built after B65 in `/tmp/b_q16x_work` (the diff against the after-B65
snapshot). Tools and one host row; default-on (logging / reading only), disclosed.

## 0. Settled

- **UX-R3's count** (`tools/diag_read.py`, B36):
  - a UTC second is a hitch second if R (the heartbeat interval rendered < 50 fps), C (a control gap ≥ 250 ms
    starts), G (an output gap ≥ 200 ms) or L (≥ 30 packets lost after FEC);
  - `summarize` counts them per window, and `session_row` gives `hitch_s`, `hitch_by`, `hitch_s_per_10min`;
  - the sessions table and the per-10-min table print them;
  - `tools/diag_check.py` prints a `last session:` line only for a PS2 row.
- **HOME-8 C28:** a 3:01 N64 session read 6.6 / 10 min from 2 hitch seconds:
  - 00:15:57 R, **the second of the `resumed` row (00:15:57.987) after a Home hold** (a stall: `client_stall` →
    `stall_end`);
  - 00:16:32 L, one link-loss second.
  - **The hold's resume second is the user's own pause, not a stream hitch.**
- **The holds' resumes in the hub's logs:** `resumed` rows with `via` `stall_end` / `stall_quiet` /
  `client_ready_stall` (the stall owner) after a `desync_pause` `trigger: client_stall`; the input hold's resume is
  `input_release` / `hold_*`. A link-drop recovery's resume (`client_ready`, the give-up) is not a hold.
- **Not logged as a row today:** a launch's `--device` arguments (only in RetroArch's command line, in the probe log
  that each launch resets), and the start payload's `capable` / `capped_from` (B63) and `layout` (B62).

## 1. Built

1. **`diag_read`'s hold split:**
   - **a hold resume** = a `resumed` row whose `via` is `stall_end`, `stall_quiet`, `client_ready_stall`,
     `input_release`, or starts with `hold`;
   - **its seconds** = the row's own UTC second and the next two (3 s);
   - `summarize` adds **`hold_resume_s`** (the hitch seconds inside those) and **`hitch_s_bar`** (`hitch_s` minus
     them), `session_row` adds `hold_resume_s`, `hitch_s_bar`, `hitch_s_bar_per_10min`;
   - **`hitch_s` / `hitch_s_per_10min` stay today's numbers** (both shown). **The pre-registered bars compare
     `hitch_s_bar_per_10min`** from now on (the record says so for A);
   - the sessions table gains the columns "hold-resume s" and "bar hitch s / 10 min"; the per-10-min table gains
     "hold-resume s". The per-second view marks a hold-resume second with `h` beside its letters.
2. **`diag_check`:** the `last session:` line also covers an N64 row (core `mupen64plus-next`), and both forms add
   `bar <x> / 10 min, hold-resume <n> s`. A PS1 / SNES newest row: still no line (today).
3. **The `launch_ports` row** (the plugin, after every successful `launch`; one recovery-log row):
   - `system`, `kind` (`retroarch` / `pcsx2`), `device_args` (from `EmulatorManager._last_device_args`, which the
     RetroArch launch sets from its own command; `[]` for PCSX2);
   - **`ports_set`** (`players_session.ports_set`, with `capable` / `capped_from` when B63 set them);
   - `layout` / `remap_binds` (an N64 launch's `n64_session`), `players_joined` / `players_chosen` as the query
     carried;
   - **an added row only:** every other row as today.
4. **Absent / old logs:** sessions with no hold resume read `hold_resume_s 0`, `hitch_s_bar` = `hitch_s`. Nothing
   else in either tool changes.

## 2. Tests (`tests/b66_hitch_split/`, plus B36's `tests/diag_read` and `tests/diag_check` unchanged and green)

- **A fixture session** (B36's fixture builder): a stall → `resumed via stall_end` with an R hitch in its second and
  one 2 s later, plus an L hitch 30 s later → `hitch_s` 3, `hold_resume_s` 2, `hitch_s_bar` 1, the per-10-min split;
  the table columns and the `h` mark.
- **Not a hold:** a link `resumed via client_ready` with a hitch → `hold_resume_s` 0.
- **The window:** a hitch 3 s after → not counted.
- **`diag_check`:** an N64 row → the line with the bar; a PS2 row → the bar added; a PS1 row → none.
- **The row:** a fake launch through the plugin's `launch` (a fake emulator with `_last_device_args`, a players
  session, an `n64_session`) → one `launch_ports` row with the fields; a launch that raises → no row.
- **Mutations:** the window 3 → 1; the via set widened to every resume; `hitch_s` reduced instead of `hitch_s_bar`;
  the row's `device_args` dropped.
