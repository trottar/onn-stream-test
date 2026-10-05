---
memory_schema: 1
as_of: 2026-10-03
baseline_commit: a402272
durable_memory_updated: true
---

# C5-M5B: the rung's entry from the data, and the PS1 look behind a flag

## Purpose

C5-M5 built the 1080p rung, but its entry (≥ 435 of 450 clean) was
reached once in 2.4 h, and its leave (the mild bar) waits for a sustained
shortfall. C5-M5B selected both rules from the recorded data, by
pre-registered criteria (`evidence/c5_m5b_2026-10-03/c5_m5b_preregistration.txt`):

- **the entry: E415**, ≥ 415 of 450;
- **the leave: no candidate met the three hard conditions**, so the mild
  bar is kept (`c5_m5b_selection.txt`).

Separately, the user asked what 4x alone shows. This patch puts the
Beetle PSX HW look levers behind a per-session flag, with a one-command
helper for the TV.

- Task: `handoffs/C5-M5B_RUNG_RULES_AND_LOOK_TASK.md`.
- Record: `evidence/C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md`.
- **Nothing is adopted.** Both flags are off by default.

## Change

**The rung's entry** (`companion/adaptive_bitrate_live.py`):

- `RUNG_CLEAN_NEEDED` changes from 435 to **415**. N stays 450.
- The docstring records the selection, and that no loss leave was
  selected.
- Nothing else in the policy changed: no `rung_loss` trigger, no new
  injection class.
- Flag absent: 0 differences against `5005615`'s controller over 386
  series (`c5_m5b_stop_rule.txt`).

**The PS1 look** (`companion/games/ps1_look.py`, new;
`companion/games/emulator_manager.py`):

- `PRIVYHUB_PS1_LOOK=<preset>`, read at each launch.
  - Unset, `4x`, or an unknown value (flagged in the launch payload):
    nothing is written, and `privyhub-session.cfg` is byte-identical.
  - A preset with keys, at a Beetle PSX HW launch:
    1. the companion reads the adopted `Beetle PSX HW.opt` (never writes
       it);
    2. it writes `data/games/retroarch/config/privyhub-look-session.opt`
       with the preset's keys replaced (each key must be in the adopted
       file exactly once);
    3. it appends `global_core_options = "true"` and
       `core_options_path = "<that file>"` to the session cfg.
- RetroArch's precedence holds: **a title with its own `.opt` (the six
  per-title copies) uses its own file**, so the look applies to titles
  without one (Tekken 3, the attract title, has none).
- `stop()` ends the look after RetroArch has exited (RetroArch rewrites a
  rejected value on exit):
  - it records the keys RetroArch rewrote;
  - it removes the file;
  - it appends one row to `logs/games/ps1_look_sessions.jsonl`.
- The next launch also removes any stale file first.
- The launch payload carries `ps1_look`, and the RetroArch session log a
  `PS1 look (C5-M5B):` line.
- Presets:
  - `PRESETS` holds `4x` (the adopted config, the same as unset) and
    `remaster`: bilinear + dither disabled + PGXP (memory only, texture,
    vertex). The full preset held 60 in its 720p hold.
  - `MEASURE` holds the cost table's levers (`measure-*`; never offered).
  - `REMASTER_AT_RUNG_OFFERED` gates the helper's `remaster-1080p`. It is
    **False**: at the rung the full preset dropped one frame in 4.8 min.

**The helper** `tools/ps1_look.sh 4x | remaster | remaster-1080p [--attract]`:
see `TOOLS.md`.

**Unchanged:**

- the shadow (`d66211b3…`);
- the adopted `.opt` and `.cfg` (hashed before and after every session);
- the drop-in, the profile, the APK and the client.

## Verification

- `tools/test_adaptive_bitrate_live.py` **120 / 120**:
  - the boundary tests are now 415 / 414;
  - one test spreads 35 / 36 unclean reports through the window.
- `tools/test_ps1_look.py` **13 / 13**: the module, plus EmulatorManager
  on a temporary project. Unset / `4x` / unknown are byte-identical; a
  preset writes and points; the end removes the file and records a
  rewrite; a stale file never carries.
- `tools/test_ps1_look_helper.py` **8 / 8**: the helper's fake run, with
  stubbed `systemctl` / `curl` / `adb`.
- The shadow 21, the nft harness 32, the selector 14, the source contract 7.
  `test_c3_f1` 7/8 (its pre-existing error).
- **Mutations: 14 of 14 caught** (`c5_m5b_mutation_check.sh`). They are
  C5-M5's ten plus the threshold's: 414, 416, back to 435, `>` for `>=`,
  and the window not required full.
- The sessions are in the record.

## Rollback

- **The entry**: `RUNG_CLEAN_NEEDED = 435`, and the two boundary tests back
  to 435 / 434. The pre-patch hashes are in
  `evidence/c5_m5b_2026-10-03/pre_patch_sha256.txt`.
- **The look**: delete `companion/games/ps1_look.py`, the import, and the
  `_prepare_ps1_look` / `_end_ps1_look_session` /
  `_remove_ps1_look_session_options` / `_ps1_look_session_options_path`
  helpers and their four call sites.
- Either way, unset → nothing changes, so leaving the code in with the
  flags unset is equivalent.
