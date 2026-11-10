---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT ADOPTED (session B, queue AF) — the N64 cheat launch: RetroArch's own name for the staged cheat file, and a wait for RetroArch's evidence (the cheat file loaded, the content running) before any cheat command, with a plain error and a clean stop on a miss. Default on; PRIVYHUB_CHEAT_READY=0 = today. RetroArch run by B headless on the synthetic fixture ROM only (B61's form). Nothing committed. No title, serial, code name, path or identifier in this record
---

# B87 — the N64 cheat launch (2026-11-10)

**Why:** HOME-12R's C49: the picker launched an N64 cheat; the hub answered 503 and the onn showed "Launched failed
retroarch did not report cheat-index navigation state"; RetroArch's log had no `[Cheats]` line at all.

**Baseline:** HEAD `051bb4d0` (HOME-12R committed); `git status --short` empty at the check; only the companion and
`privyhub-diag` active. **Design** hashed before code at 22:49:57Z (`b87_2026-11-10/design.sha256`).

## Settled

- **The failed launch vs the working PS1 one** (HOME-12R's records, read in place, order and counts only): PS1 — the
  core's API line, then `Load game-specific cheatfile`, then `[NetCMD]` up, then the toggles; T81 (N64) — the core's
  API line, `[NetCMD]`, the dynarec's start, the shutdown, **no cheat-file line**.
- **The staged file's folder was right** (the log's save redirect names `Mupen64Plus-Next`; B78's / B83's folder), and
  the content's name matched the save's — but **the real title's name holds a dot inside it** (counted in place).
- **The reproduction** (B, headless, the hub's display; the synthetic fixture ROM; made-up `.cht` files; temp folders;
  no stream, no pad; `repro/b87_repro.py`, `repro/run_all.sh`, `repro/results.txt`):
  1. **The name — the cause of HOME-12R's failure.** RetroArch looks for the cheat file under the content's name with
     **one more dot-suffix stripped**: `X v1.1.v64` → `X v1.cht`, `Ab.Cd.Ef.v64` → `Ab.Cd.cht`, a name without an inner
     dot → unchanged. The hub staged `<stem>.cht` (`X v1.1.cht`), so RetroArch never loaded it — the fixture shows
     HOME-12R's exact signature (core API, `[NetCMD]`, dynarec, no `[Cheats]`). The same file under RetroArch's name
     loads at 0.08 s. **Every RetroArch system is exposed** for a title with a dot inside its name.
  2. **The first pulse — a second, latent failure.** With the file loaded (0.08-0.10 s, before `[NetCMD]` at
     0.28-0.38 s), a `CHEAT_INDEX_PLUS` sent at PLAYING is **lost, not late**: unanswered in all 7 recorded runs at
     PLAYING (and 3 of 4 earlier ad-hoc runs); the N64 core's dynarec starts 0-0.27 s after PLAYING and pulses answer
     ~0.02 s after it (probing every 0.25 s: answered on the 2nd probe 5 / 5, at 0.58 s). The design's "9 of 10" was
     written from those runs before they were tallied; these are the counts.
  So the N64 launch would fail at the first pulse even with the right file; on T81 RetroArch also never had the file.

## What was built (`b87.diff`, `companion/games/emulator_manager.py`)

- **The name:** `_retroarch_cheat_name(content)` — the stem with one more dot-suffix stripped, when it differs; the
  staging writes the same bytes under that name too (today's `<stem>.cht` kept); the staging dir removed as a whole, as
  today.
- **The wait** (`_wait_for_cheats_ready`, in `_apply_active_cheat_profile` after the PLAYING check, **before `pause()`
  and before any cheat command**): RetroArch's `Load game-specific cheatfile` line in this launch's log, then a
  `CHEAT_INDEX_PLUS` answered by a `Cheat #n` line (resent every 0.25 s), **within 10 s** (the fixture needs ≤ 0.6 s;
  a real title's dynarec starts after its image is in memory).
- **A miss:** "**cheats not ready — the game did not finish loading**"; the game is **stopped cleanly** (no toggle has
  been sent; the launch's failure path removes the staging) — never left running on the cheat profile's isolated saves.
- Then today's activation (pause, navigate, toggle, verify, resume), unchanged. PS1 / SNES: the same wait; their first
  pulse answers at once.

## Switch

`PRIVYHUB_CHEAT_READY=0` → today's single staged name and today's order, **byte for byte** on the same fixture trees as
HEAD's code (`proof_absent_run.txt`: PS1, a slow N64 core, a dotted title — 3 / 3 SAME).

## Tests (`tests/b87_cheat_ready/test_b87.py`, 6)

The launch through the plugin as the companion constructs it (`handle_post("launch")`) with **a fake RetroArch on
loopback** — a thread bound to the UDP port the hub configured, answering GET_STATUS / PAUSE_TOGGLE, writing
RetroArch's own log lines into the hub's game log: the cheat-file line only when the file sits under RetroArch's name,
`Cheat #n` lines only once its "core runs" (earlier pulses lost), toggles flipping the state.

- **N64, the port up 0.6 s before the core runs** → the hub waits, then navigates and toggles: `activation_verified`,
  the game running, lost pulses counted;
- **a fake that never loads the cheat file** → the plain error within the bound, **no pulse and no toggle sent**, the
  game stopped, the staging removed; **a core that never runs** → the plain error, no toggle;
- **a dotted title** → staged under RetroArch's name and verified (the knob 0 → the file not found, as today);
- **PS1** → the session's rows equal with and without the wait (`enabled_cheat_indexes` with B85's "must be on");
- **the knob 0** on a slow core → today's "did not report cheat-index navigation state", the game stopped.
- **On HEAD's code** the four N64 cases fail with exactly the onn's message (`tests_on_head.txt`); PS1 and the knob-0
  case pass there.
- 3 runs: 6 / 6 each; `tests/art_systems` 120 / 120 (`tests_x3.txt`). Mutations: **6 / 7 caught** (`tests_mutations.txt`); M5 (the stop inside the wait's failure
  path removed) is **equivalent** — the launch's own failure path (today's code) stops the process anyway.

## Disclosed

- **The reproduction ran RetroArch** headless on the hub's display (B61's form: the fixture ROM, made-up cheat files,
  temp folders under `~/.cache`, removed after; no stream, no pad; nothing left running — the script's `pgrep` count
  of 1 was its own subshell, `ps` read 0).
- **The bound (10 s) is not measured on a real title** (only the fixture); a title that takes longer to start its core
  answers the plain error and stops cleanly.
- The design's "9 of 10" (the first pulse) was a pre-tally estimate; the record gives the counts.

## Files

`b87_2026-11-10/`: start files, the design + hash, `b87.diff`, `repro/` (the script, the fixture ROM builder (B61's),
`run_all.sh`, `results.txt`), `proof_absent_run.txt`, `tests_on_head.txt`, `tests_x3.txt`, `tests_mutations.txt`,
`scripts/`, redact / title checks, `manifest.sha256`. Patch note: `patches/B87_N64_CHEAT_LAUNCH.md`.
