# B87 — the N64 cheat launch (design, written and hashed before code)

**Baseline:** HEAD `051bb4d0` (HOME-12R committed). **Knob:** `PRIVYHUB_CHEAT_READY` — default on; `0` = today's
staging name and today's first pulse, byte for byte.

## Settled (HOME-12R's records read in place, counts / order only; the hub's code; a headless reproduction)

- **The failed launch** (`home12r_2026-11-10/c49/`): RetroArch's log for T81 has the content load, the core's API line,
  `[NetCMD]` up, the N64 dynarec's start, then the shutdown — **no `[Cheats]` line at all**. The same sitting's working
  PS1 check: `Load game-specific cheatfile` right after the core's API line (before `[NetCMD]`), then the `Cheat #n`
  navigation lines, the toggle, `activation_verified` true.
- **The hub's sequence** (`EmulatorManager.launch` → `_wait_for_retroarch_command_ready` → `_apply_active_cheat_profile`):
  GET_STATUS = PLAYING → `pause()` → per target: `CHEAT_INDEX_PLUS`, then up to 1 s for a `Cheat #n: …: on|off` line
  in the session log; none → "RetroArch did not report cheat-index navigation state" → the session force-stopped, 503.
- **The staged file** sits at `<cheat_database_path>/Mupen64Plus-Next/<content stem>.cht` (B78; B83 re-read): the
  folder is right (the log's save redirect names the same core folder), the content name matches.
- **The reproduction** (B, headless, B61's form: the synthetic fixture ROM, a made-up `.cht`, temp folders, the
  companion's display; `repro/`, `repro/results.txt`):
  1. **The name.** RetroArch looks for the cheat file under the content's name **with one more dot-suffix
     stripped**: content `X v1.1.v64` → `X v1.cht`; `Ab.Cd.Ef.v64` → `Ab.Cd.cht`; a name without a dot inside →
     unchanged. The hub stages under the stem (`X v1.1.cht`), so for such a title **RetroArch never loads the cheat
     file** — the log shows exactly HOME-12R's signature (core API, `[NetCMD]`, dynarec, no `[Cheats]`). The real title's
     name has one dot inside it (counted in place; no name read into a record). Every RetroArch system is exposed.
  2. **The first pulse.** With the file loaded (at 0.08-0.10 s, before `[NetCMD]` at 0.28-0.38 s), a
     `CHEAT_INDEX_PLUS` sent at PLAYING is **lost, not late**: no `Cheat #` line in the hub's 1-s window in 9 of 10
     runs; pulses answer ~0.02 s after the N64 core's dynarec starts, 0-0.27 s after PLAYING on the fixture (probing
     every 0.25 s: answered on the 2nd probe 5 / 5 at 0.58 s). PS1's core runs frames at PLAYING (the PS1 check).
  So the hub sent its first pulse before the core ran — and, on T81, toward a cheat file RetroArch had not loaded.

## The design (every RetroArch launch with a cheat session; `PRIVYHUB_CHEAT_READY=0` = today)

1. **The name** (`_prepare_cheat_runtime`): besides today's `<stem>.cht`, the same bytes under **RetroArch's own
   name** (the stem with one more dot-suffix stripped) when that differs. A name without an inner dot → one file, as
   today. The staging dir is removed as a whole at the end, as today.
2. **The wait** (`_apply_active_cheat_profile`, before `pause()` and before any cheat command):
   - **RetroArch's own evidence the cheat file is loaded:** its `Load game-specific cheatfile` line in this launch's
     log, waited for up to the bound;
   - **the content running:** `CHEAT_INDEX_PLUS` sent and a `Cheat #n` line awaited for 0.25 s, resent until one
     answers, up to the bound (an index pulse only moves RetroArch's cheat cursor; the navigation after it reads the
     cursor from the log and assumes nothing about where it starts);
   - **the bound:** 10 s from the start of the wait — the fixture needs ≤ 0.6 s; a real title's dynarec starts after
     its image is in memory, so ~15× the fixture's worst case.
   - **A miss** (no cheat-file line, or no answer, within the bound): **the game is stopped cleanly** — today's failure
     path (no toggle has been sent, nothing saved, the staging removed) — and the onn reads **"cheats not ready — the
     game did not finish loading"**. Never a half-formed session. (Not left running without cheats: the session runs
     on the cheat profile's isolated saves, which a normal game must not be confused with.)
   - Then today's activation unchanged (pause, navigate, toggle, verify, resume).
3. **PS1 / SNES:** the same wait; their first pulse answers at once, so the outcome and the session's rows
   (`enabled_cheat_indexes`, `activation_verified`, `activation_verification_lines`) are unchanged.

## Tests (`tests/b87_cheat_ready/test_b87.py`)

The launch through the plugin as the companion builds it (`handle_post("launch")`, B85's harness), with **a fake
RetroArch on loopback**: a UDP server on the port the hub configured, answering GET_STATUS / PAUSE_TOGGLE and writing
RetroArch's own log lines into the hub's game log — the cheat-file line at its "load", `Cheat #n` lines for index
pulses only once its "core runs", toggles flipping the state. Cases: **N64, port up before the core runs** (pulses lost
for 0.5 s) → the hub waits, then navigates and toggles: `activation_verified`; **a fake that never loads the cheat
file** → the plain error within the bound, the process stopped, no toggle sent, the staging removed; **RetroArch's name**:
a title with an inner dot is staged under both names (the fake "loads" only RetroArch's name); **PS1** (the core runs at
once) → the session's rows equal to the knob-0 run's; **the knob 0** → today's staging and today's first-pulse failure
on the slow fake. The headless reproduction's before / after in the record (the name rule). Mutations; ×3.
