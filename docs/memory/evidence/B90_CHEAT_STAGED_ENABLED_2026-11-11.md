---
memory_schema: 1
as_of: 2026-11-11
status: BUILT, NOT ADOPTED (session B, queue AG) — the cheat launch without walking the list: only the session's cheats staged, each enabled; RetroArch applies them at load (apply_cheats_after_load) and the hub verifies from RetroArch's own evidence in a handful of pulses; SNES cheats staged under the folder snes9x reads; a launch whose client has hung up stops the game and writes launch_orphaned. Default on; PRIVYHUB_CHEAT_STAGED=0 = today (5 / 5 byte-equal to HEAD). RetroArch run by B headless on synthetic fixture ROMs only (B61's form). Nothing committed. No title, serial, code name, path or identifier in this record
---

# B90 — the cheat launch without walking the list (2026-11-11)

**Why:** HOME-12T's C46: B87's fixes worked on the real N64 title, but the hub selected each cheat by stepping
RetroArch's cheat index one answered pulse at a time round the whole 677-entry list (for each enabled index, and again
to read it back): ~2,000 steps, ~107 s; the onn waits 60 s, hung up ("stuck at launching", "failed from timeout"), and
the game was left running, paused and unseen, until A stopped it.

**Baseline:** HEAD `d1df1f86` (HOME-12T committed); `git status --short` empty at the check (the prompt files tracked);
only the companion and `privyhub-diag` active. **Design** hashed before code at 01:50:43Z (`b90_2026-11-11/design.sha256`).

## Settled (headless, B61's form: synthetic fixture ROMs, made-up lists, temp folders; disclosed below)

- **RetroArch 1.22.2 (the hub's AppImage, its strings):** `apply_cheats_after_load` (absent from the hub's config →
  off); `[Cheats] Load game-specific cheatfile: "…"`, `[Cheats] Applying cheat changes.` (once per apply — **no
  per-cheat line**), `[Cheats] Cheat #n: <desc>: on|off` (an index pulse's answer).
- **A file's enabled cheats are applied at load with no command** on all three cores — `measure/load_results.jsonl`:
  with the setting on, RetroArch logs `Applying cheat changes.` right after the cheat-file line and **the core's own
  memory holds the cheat values** at the picks' addresses (`READ_CORE_MEMORY` / `READ_CORE_RAM`); with it off, no
  apply line and the memory untouched — while the index pulse reports `on` either way (RetroArch's state, not the
  core's). So the evidence is the apply line; the pulses confirm which cheats.
- **SNES, found while settling:** the hub runs snes9x (`PRIVYHUB_SNES_CORE=snes9x`), library name `Snes9x`; RetroArch
  looks under `<cheat db>/Snes9x/`, the hub stages under `bsnes/` → **never loaded** (no cheat-file line, no apply, no
  pulse answered). On HEAD every SNES cheat launch ends in B87's "cheats not ready" (`tests_on_head.txt` shows the 503).
- **Pulses back to back are lost** (one-frame virtual input): verification paces them ≥ 0.1 s and re-sends after 0.5 s.

## The measurement (the hub's own `_apply_active_cheat_profile`, HEAD's for the walk, B90's for staged, driven against the real RetroArch; `measure/`)

| core | list | picks | today's walk (HEAD's code): s / pulses | staged (B90): s / pulses | staged: verified | core memory holds the picks (staged) |
| --- | --- | --- | --- | --- | --- | --- |
| Mupen64Plus-Next | 12 | 1 | 1.6 s / 19 | 0.77 s / 3 | True | 1/1 |
| Mupen64Plus-Next | 12 | 2 | 2.8 s / 34 | 0.89 s / 4 | True | 2/2 |
| Mupen64Plus-Next | 12 | 4 | 5.0 s / 61 | 1.13 s / 6 | True | 4/4 |
| Mupen64Plus-Next | 188 | 1 | 14.9 s / 283 | 0.77 s / 3 | True | 1/1 |
| Mupen64Plus-Next | 188 | 2 | 26.5 s / 503 | 0.26 s / 3 | True | 2/2 |
| Mupen64Plus-Next | 188 | 4 | 47.8 s / 906 | 1.13 s / 6 | True | 4/4 |
| Mupen64Plus-Next | 677 | 1 | 52.1 s / 1016 | 0.14 s / 2 | True | 1/1 |
| Mupen64Plus-Next | 677 | 2 | 92.6 s / 1807 | 0.89 s / 4 | True | 2/2 |
| Mupen64Plus-Next | 677 | 4 | 166.7 s / 3253 | 1.13 s / 6 | True | 4/4 |
| Mupen64Plus-Next | 2,092 | 1 | 160.2 s / 3139 | 0.77 s / 3 | True | 1/1 |
| Mupen64Plus-Next | 2,092 | 2 | 284.9 s / 5580 | 0.26 s / 3 | True | 2/2 |
| Mupen64Plus-Next | 2,092 | 4 | 513.4 s / 10045 | 0.51 s / 5 | True | 4/4 |
| snes9x | 12 | 1 | — | 0.20 s / 2 | True | 1/1 |
| snes9x | 12 | 2 | — | 0.34 s / 3 | True | 2/2 |
| snes9x | 12 | 4 | — | 0.60 s / 5 | True | 4/4 |
| snes9x | 188 | 1 | — | 0.20 s / 2 | True | 1/1 |
| snes9x | 188 | 2 | — | 0.34 s / 3 | True | 2/2 |
| snes9x | 188 | 4 | — | 0.60 s / 5 | True | 4/4 |
| snes9x | 677 | 1 | — | 0.20 s / 2 | True | 1/1 |
| snes9x | 677 | 2 | — | 0.34 s / 3 | True | 2/2 |
| snes9x | 677 | 4 | — | 0.60 s / 5 | True | 4/4 |
| snes9x | 2,092 | 1 | — | 0.20 s / 2 | True | 1/1 |
| snes9x | 2,092 | 2 | — | 0.34 s / 3 | True | 2/2 |
| snes9x | 2,092 | 4 | — | 0.62 s / 5 | True | 4/4 |
| Beetle PSX HW | 12 | 1 | — | 0.20 s / 2 | True | 1/1 |
| Beetle PSX HW | 12 | 2 | — | 0.32 s / 3 | True | 2/2 |
| Beetle PSX HW | 12 | 4 | — | 0.60 s / 5 | True | 4/4 |
| Beetle PSX HW | 188 | 1 | — | 0.16 s / 2 | True | 1/1 |
| Beetle PSX HW | 188 | 2 | — | 0.31 s / 3 | True | 2/2 |
| Beetle PSX HW | 188 | 4 | — | 0.60 s / 5 | True | 4/4 |
| Beetle PSX HW | 677 | 1 | — | 0.20 s / 2 | True | 1/1 |
| Beetle PSX HW | 677 | 2 | — | 0.32 s / 3 | True | 2/2 |
| Beetle PSX HW | 677 | 4 | — | 0.59 s / 5 | True | 4/4 |
| Beetle PSX HW | 2,092 | 1 | — | 0.20 s / 2 | True | 1/1 |
| Beetle PSX HW | 2,092 | 2 | — | 0.32 s / 3 | True | 2/2 |
| Beetle PSX HW | 2,092 | 4 | — | 0.60 s / 5 | True | 4/4 |

runs failed to complete: 0; RetroArch left running at the end: [0]

- **Today's walk ≈ 0.05 s per answered pulse; its pulses ≈ the distance to each pick + one full lap per pick** — on 677
  entries, 2 picks: 1,807 pulses, 93 s (HOME-12T's real launch: ~107 s, its picks with "must be on" codes).
- **Staged: ≤ 1.2 s and ≤ 6 pulses on every list size and core, including the 2,092-entry fixture** (target ≤ 15 s), and
  the core's memory holds every pick afterwards.

## What was built (`b90.diff`)

- **`emulator_manager.py`:** `_staged_cheat_file` — the session's real indexes (B85's picks, parts, "must be on"
  codes) only, in source order, renumbered, every source key copied, each `cheatN_enable = true`; staged in place of
  the whole file on Mupen64Plus-Next / Snes9x / Beetle PSX HW when the session has picks (the source's SHA-256 still
  verified on read; the staged bytes against what was built; the profile identity unchanged); the session's config
  gets `apply_cheats_after_load = "true"` (exactly one); `_verify_staged_cheats` after B87's ready wait — the apply
  line after the cheat-file line, then every staged cheat `on` with its description, ≤ 2k + 4 pulses, ≤ 10 s; no pause,
  no toggle; a miss → today's fail-closed path (the game stopped, "Cheat profile activation failed closed: …");
  `activation_verified` as today, plus `activation_mode: "staged"`, `activation_pulses`. SNES with snes9x → `Snes9x/`.
  Other cores (FCEUmm, BlastEm, bsnes — not measured, no lists on the hub) keep today's whole file and walk.
- **`launch_orphan.py` + `privyhub_service.py` (the games `launch` answer only):** before the 200 is written — the
  client's socket closed (readable, `MSG_PEEK` empty) or ≥ 60 s since the request (the onn's read timeout), or the
  write fails → no answer; **`plugins/games.py` `launch_orphaned`**: under the emulator's lock, if the running game is
  still this launch's (its pid), the emulator's stop (the onn's Stop: SAVE_FILES, graceful close), then the rest of the
  onn's Stop path (recovery, adaptive bitrate, the stream's game session); one row **`launch_orphaned`** (reason
  `client_closed` / `client_wait_passed` / `answer_failed`, seconds, `stopped`) in the games recovery log.
- **Per core:** the staged form applies on all three measured cores; none keeps a walk (no "shorter direction" change).

## Switch

`PRIVYHUB_CHEAT_STAGED=0` → today's file, folder, config, walk and launch answer: **5 / 5 SAME** against HEAD's code on
the same fixtures through the real HTTP route — the whole answer, the session config, the staged file, the fake's
counts, the status read, the recovery rows (`proof_absent_run.txt`; times, pids, the free port and temp paths
normalised).

## Tests (`tests/b90_cheat_staged/test_b90.py`, 10; through the companion's real HTTP server on loopback)

The child builds the companion's own `PrivyHubRequestHandler` on `127.0.0.1:0` (tests/client_contract's form) and sends
the onn's `POST /plugins/games/launch?id=…&cheat_source=0&cheat_indexes=…`; RetroArch is B87's fake extended to read the
session config and apply at load.
- a **2,092-entry** list, 1 pick (+ its "must be on") and 3 picks (parts, the last entry): 200, verified, staged,
  **toggles 0, answered pulses ≤ 1 + 2k + 4**, under 15 s;
- **the staged file's contents** byte for byte (only the real indexes, renumbered, enabled);
- a RetroArch that **ignores** apply-at-load → 503 "did not apply the staged cheats at load", the game stopped;
- a RetroArch whose index **never moves** → 503 "did not report every staged cheat" **within the pulse bound** (not
  the 10-s deadline), the game stopped;
- **the knob 0** → today's walk: answered pulses = today's formula, a toggle per index, no config line, the whole file;
- **SNES** staged under `Snes9x/` and verified (the knob 0 → `bsnes/`, "cheats not ready", stopped);
- **a client that hangs up** at 0.3 s → the onn's next status read shows no game, one `launch_orphaned`
  (`client_closed`, stopped), the save flush sent; the knob 0 → the game left running (today);
- the launch call is in `tests/client_contract/calls.json` (POST, its parameters).
- **On HEAD's code** (`tests_on_head.txt`): the staged tests, the fail-closed ones, SNES (503 "cheats not ready") and
  the hang-up fail; the knob-0 tests pass. 3 runs (`tests_x3.txt`). Mutations **9 / 9 caught** (`tests_mutations.txt`) —
  after one test added: M9 (the pulse bound removed) was first missed; the never-moving index case then caught it.
- **Earlier suites pinned to the knob 0 where they assert today's staging** (their assertions unchanged; B90's suite
  tests the staged form): `tests/b87_cheat_ready` (its FLAGS, one line — its fake has no apply at load) and four cases
  in `tests/art_systems` that compare the staged file with the whole source file (`test_b78` staged-for-N64,
  `test_b81` launched-as-a-database-file, `test_b83`'s two launch-staging cases). Found by the host-suite comparison.
- **Found by the host suites and fixed:** `tests/session_identity`'s handler replay runs the POST handler outside the
  module; B90's first lines used the module's names directly ("name 'time' is not defined") — now looked up as B35's
  gate is (`globals().get`), the replay 88 / 88.

## The tree and the host suites

- **HEAD + `b90.diff` + `b91.diff` = the working tree; reversed → HEAD** (0 differences each way; `git diff --check`
  clean) — `diffs_apply_in_order.txt`.
- **Every host suite** on full exports of HEAD and HEAD + B90 (`tests_host_compare.txt`): 75 shared suites, **no result
  line changed**; `tests/b90_cheat_staged` new (10 OK); failing in both, unchanged: the same six `tools/` suites as
  queues AA-AF and `tests/input_hold_b8` (queue AE's time-dependent case).

## Disclosed

- **RetroArch was run by B headless** on the hub's display for the measurement only (B61's form: synthetic ROMs — B61's
  N64 loop, a SNES LoROM loop, a PS-X EXE loop — made-up lists of 12 / 188 / 677 / 2,092 entries, temp folders under
  `~/.cache`, no stream, no pad; nothing left running). The measurement drives the hub's own activation code on a
  manager built with only what the cheat path reads (its log, command port, process); pulses counted through its own
  `_retroarch_network_request`.
- The first memory-read flag compared lower-case hex with RetroArch's upper-case answer (all reads hold the values; the
  table counts case-insensitively from the raw answers); the first read was unaligned on N64's word-swapped memory
  (corrected before the full set).
- Host jobs (tests, mutations, JVM builds) ran beside the measurement's later runs; the walk's per-pulse time is
  RetroArch's frame-bound answer.
- The hang-up check runs when the launch answers: a launch that is still working is not aborted when the onn gives up;
  the staged launch now answers in seconds.
- A description RetroArch prints differently (e.g. one past its 256-byte message) fails closed — as today's walk would.
- `launch_orphaned`'s first version checked the game's pid outside the emulator's lock; changed (before the final runs)
  so a launch retried meanwhile cannot have its new game stopped.

## Files

`b90_2026-11-11/`: start files, the design + hash, `b90.diff`, `diffs_apply_in_order.txt`, `measure/` (the scripts, the fixture builders,
`results.jsonl`, `load_results.jsonl`, `table.md`), `proof_absent_run.txt`, `tests_on_head.txt`, `tests_x3.txt`,
`tests_mutations.txt`, `tests_host_compare.txt`, `scripts/`, redact / title checks, `manifest.sha256`. Patch note:
`patches/B90_CHEAT_STAGED_ENABLED.md`.
