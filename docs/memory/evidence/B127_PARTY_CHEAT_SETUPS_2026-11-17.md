---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AS) — the party mini games under each title's cheat setup, behind PRIVYHUB_PARTY=1 + PRIVYHUB_H7=1. Settled from the code: today the mini game's title is launched with no cheat arguments (always the normal setup); the onn's Extras launch is the launch route with cheat_source / cheat_indexes (B85's expansion gives a saved setup's indexes back, so the same profile_id); under a setup h7-start's load already lands in the setup's own states/<core>/ (_state_root() is the setup's — where RetroArch reads); launch_orphaned never touches a mini game's launch; stop flushes the in-game save into the setup's saves/; the onn's SAVE / LOAD during a mini game are not taken and write / read the setup's slots (reported, not changed). Built: the sidecar's "cheat" {source_index, enabled_cheat_indexes, profile_id}; the setup's begin <game id>.<profile_id's first 12>.state; the setup checked on the hub before anything (else 400, nothing launched); the title launched by the plugin's own launch path with the onn's Extras query; the session's profile_id checked; h7-start's begin the setup's under a setup. No spec per setup (B126). Tests 9 (3 runs green after one test fix), mutations 4 / 4; flags absent and a sidecar without cheat → HEAD's answers. Nothing adopted; nothing committed
---

# B127 — the mini games under each title's cheat setup

Queue: `handoffs/QUEUE_2026-11-17AS.md` §B127. T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player
title. The directory is `b127_2026-11-17/`: `design_written_before_code.md` + `.sha256` (hashed 03:19:23Z, before any
code), `b127.diff` (applies on `d9e95e66`), `under_setups_answers.json` (the test child's own answers, fixture and setup
ids replaced), `mutations.md` + `tests_mutations.txt`, `tests_x3.txt` (+ `tests_x3_after_fix.txt`), `test_fix_note.txt`,
`scripts/run_all.sh`, the board repo's status before / after, the checks, `manifest.sha256`. Patch:
`patches/B127_PARTY_CHEAT_SETUPS.md`. No title, serial, game id, character name, cheat name or path. **Nothing of the
users' touched:** their setups, slots, in-game saves, the kept H7 folders and the rules folder not opened (no test runs
against them — every test runs in a temp tree with B85's made-up titles and `.cht`); no emulator title started (B101's
fake RetroArch only); **the board's repo not touched** (its status before = after; only read for B111's scratch copy).

## Settled from the code (HEAD `d9e95e66`)

1. **`party-minigame-start` today** (`party_minigame._start_steps`): the board's session set aside
   (`_party_stash_begin` clears `_active_cheat_session` with the other session fields), then **`emu.launch(game)` —
   no cheat arguments**: the title always runs in the normal setup (normal `states/`, normal `saves/`); then pause,
   route, the switch, `h7-start` (the load, the watch), the release.
2. **The onn's Extras launch** (`plugins/games.py` `launch`): `POST launch?id=…&cheat_source=<source_index>&cheat_indexes=
   <the setup's enabled indexes>` → `_parse_cheat_launch_request` → **B85's expansion** (the cleaned list's picks → the
   file's own indexes + the required codes; a saved setup's indexes are already the file's, so it gives them back) →
   `emu.launch(…, cheat_source_index, cheat_enabled_indexes)` → `_prepare_cheat_profile_storage`: **`profile_id` = sha256
   of (schema, game id, system, relative path, source index, the source file's sha256, the enabled indexes)** — the
   same inputs, the same setup; other inputs would make **a new setup folder** → the session config with exactly one
   `savefile_directory` / `savestate_directory`, the setup's → B87 / B90 activation (needs PLAYING at launch).
3. **`h7-start`'s load under a setup:** `_state_root()` / `<core folder>` / `<stem>.state8`, and `_state_root()` is
   **the setup's `states/`** while its session runs — the file RetroArch reads (`sort_savestates`). **It already lands**
   (H7-C2 did the same by hand); what was missing was the begin: today it loads `<game id>.state` (T89's stays locked
   under the setup).
4. **`launch_orphaned`** (B90): only the launch route's answer to a client that has gone; a mini game's launch is the
   actor's own call (no client connection) — never orphaned.
5. **Stop under a setup** (`emu.stop`): `SAVE_FILES` — **RetroArch flushes the in-game save into the setup's
   `saves/<core>/`** — then `QUIT`; the mini game's end stops its title the same way. **A match played in a mini game
   writes whatever the game writes to its in-game save (records, unlocks) into the users' setup**, as any play of that
   setup does. No save state is written by a stop.
6. **The onn's SAVE / LOAD during a mini game** (not taken: B114's `TAKEN` is Home / RESUME / END): today's path
   against the running title — **under a setup a SAVE writes the setup's slot N and rewrites its slot 0** (the users'
   cheat slot 1 is a slot of that setup); a LOAD loads the setup's slot into the mini game. Not changed (the queue's
   item is the launch); in the reply's "what I would change".

## Built (behind the flags; `b127.diff`)

- **The sidecar** may carry `"cheat": {"source_index": n, "enabled_cheat_indexes": [...], "profile_id": "<id>"}` beside
  `players` / `scores` / `places_to_scores` — checked (a non-negative integer; distinct non-negative integers, at least
  one, kept sorted; 64 hex characters, compared case-blind); malformed → not listed. No cheat name.
- **The setup's begin:** `<game id>.<the profile_id's first 12 characters, upper case>.state` in the rules folder, beside
  `<game id>.state`; a sidecar with `cheat` is listed only when it is there. The listing's answer unchanged.
- **The start:** with `cheat`, the setup checked through the manager first (one call, ≤ 1.5 s): `cheat_profiles` lists
  that `profile_id` (valid on the hub) with the same source and indexes, and B85's expansion gives the indexes back.
  Else **400 "the cheat setup this mini game names is not on the hub (or its cheats changed): nothing was launched"**
  and one `minigame_refused` row (`check`: `no_profile` / `profile_differs` / `cheats_changed` / `busy` /
  `unreadable` / `no_game`) — nothing set aside, nothing launched, no folder made.
- **The launch:** with `cheat`, **the plugin's own launch path with the onn's Extras query** (`id`, `cheat_source`,
  `cheat_indexes`), under the manager's lock for that call only; then the session's `profile_id` must be the sidecar's
  (else given up "the title did not start under its cheat setup", the title stopped by the hub's end);
  `minigame_launch` carries `"cheat": true, "profile_matches": true` only then.
- **`h7-start` under a setup:** the begin is the setup's own when the rules folder holds it, else the normal one (today's);
  `"begin": "setup" | "normal"` in the answer and the `watching` row only under a setup. N64 only while PAUSED (B123,
  unchanged).
- **No spec per setup** (B126: one spec per title reads locked and unlocked alike).

## Tests (`tests/b127_party_cheat_setups/test_b127.py`, 9; the `cheat` / `cheat_today` modes in B114's scenario)

The real HTTP server on loopback; B101 / B103's fake RetroArch **reading its states folder from the session config the
launch wrote** (not the hub's `_state_root()`); RetroArch's network side of the cheat toggles stubbed as B83's harness
does (disclosed); B108's stand-in board; B114's onn thread and status / result / native-stream-status every 0.1 s.

| test | what it showed (`under_setups_answers.json`) |
| --- | --- |
| 0 the setups | made by the onn's Extras launch from loopback (PS1 pick → [0, 1] with its required code; N64 split cheat → [2, 5, 6]); read back by `cheat-profiles`: one each, the `profile_id` the launch's; 11 files hashed (both setups' slots, pictures, in-game saves, the normal states) |
| 1 `h7-start` under the PS1 setup | no setup begin → `"begin": "normal"`; with it → `"begin": "setup"`, **loaded through `<setup>/states/<core>/<stem>.state8`** (where RetroArch reads), the memory the setup begin's (7, 9), no scratch left |
| 2 N64 | running → 400 "the N64 game is not paused …; nothing was sent", **no `LOAD_STATE_SLOT` sent**; paused → loaded from the setup's folder (3, 4) |
| 3 refusals | a `profile_id` not on the hub, the setup's folder moved away, the indexes changed → each **400 with the plain line, 0 RetroArch started**, one `minigame_refused` row (`no_profile` / `no_profile` / `profile_differs`), the board still the session, no mini game on; **no new setup folder**; a malformed `cheat` not listed |
| 4 two back to back | two-player under the PS1 setup (seats 2,1) then four-player under the N64 setup (seats 3,1,4,2, Home / RESUME in it): **the launch's query `id=<id>&cheat_source=0&cheat_indexes=0,1` / `…=2,5,6` — the onn's Extras query**; the session's `profile_id` the setup's (the manager and `status`); the begin loaded from the setup's folder; **end_P2 [0, 1]**; **places [2, 1, 4, 3] → scores [3, 4, 1, 2]**; RESUME answering 4 / 4 ports |
| 5 hand-overs | each mini game two switches, both `planned`; no recovery act; no key to the board; no escalation; every route < 2 s while a mini game is on (max: status 0.55 s, ns_status 0.60 s, board end 0.61 s) |
| 6 the users' files | **every file of both setups and the normal states byte-equal; no `.state8` anywhere; nothing running** (the fake's `SAVE_FILES` writes nothing: the real flush is settled item 5) |
| Today: flags absent | `PRIVYHUB_PARTY` / `PRIVYHUB_H7` each absent (and both): **HEAD's companion and mine answer the cheat launch, `cheat-profiles`, `h7-start`, `h7-result`, `party-minigames`, `party-minigame-start`, status and stop the same** (numbers of 4+ digits, decimals and times masked) |
| Today: no `cheat` | B124's four-player run on HEAD's code and on mine: the same results (state, class, places, scores, seats), the same rows, routes, switches and refusals |

**Mutations (`mutations.md`): 4 / 4 caught** — no setup begin; the launch without the setup; no setup check (a launch
went ahead and the setups' tree changed); the load into the normal `states/`.

**Runs (`tests_x3.txt`):** the first three runs: 1 and 2 failed `test_a_sidecar_without_cheat_is_heads`, 3 green — the
test compared B114's row snapshot, taken before the switch-window rows (written 3 s after each switch) land, so it held
them or not as the machine's load had it, on HEAD's code and mine alike. **Fixed in the test** (those rows compared from
the list the scenario waits for; `test_fix_note.txt`), then **three runs again: 9 / 9 green each, 0 temp dirs, nothing
left running** (`tests_x3_after_fix.txt`). **The other suites once (`tests_x3.txt`), all green:** B124 6, B114 8 (with
the two new modes in its scenario), B115 6, B110 13, B112 7, B123 6, B122 12, B111 2 (the board's check under Godot
headless in a scratch copy), B102 16, B104 19, B103 13, B105 12, B101 14, B99 15, B108 16, art_systems 120 (one error:
`test_b81.Docs` reads `docs/CHEATS.md`, left out of the work copy by the rule; run against the repo itself — OK), B65 7,
B61 14, the player prompt 11, the players' session 19, the relaunch 19, the pad slots 5, the stall signal 12, the stall
owner 10, the link recovery 16, the fast restart 13, the client contract 5, PS2 93, GameCube 54, N64 28; nothing left
running; the 54 temp dirs left are the older suites' own (b7 / b9 / b22 / b34 / b41, as in B124's run), in my scratch,
removed with it.

## What waits

H7-V5 (A, unattended, with everything unlocked — `SESSION_B_DONE_2026-11-17AS.md` §A); then PP-H4. Nothing adopted.

## Correction (queue AT, 2026-11-17, B131)

**Settled item 6 above is wrong.** The onn's SAVE / LOAD during a hub mini game never reach the title: since B110 the
manager refuses both whenever the board is the session or set aside (`_party_stash`), which covers every moment of a mini
game — 503 "Saving and loading are not offered for the board game; nothing was sent.", nothing sent, no slot touched
(`B131_PARTY_SAVE_LOAD_REFUSED_2026-11-17.md`; HEAD's code in its test: nothing sent, every setup file byte-equal).
Item 5 (the stop's in-game-save flush into the setup) stands.
