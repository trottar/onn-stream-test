---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AO) — behind PRIVYHUB_PARTY=1 only (absent / 0 = today byte for byte through the real HTTP routes against HEAD f302f8a8's companion, the library the onn reads included): the board game (PrivyParty, a Godot project) is a game entry in its own system, launched as a new `godot` kind — **the onn as it is (APK ca53df0d…) can start it with no client change**, as any game (Games → PrivyParty → the game → Launch on Companion → Start Fresh). The executable started directly with Godot's own `--fullscreen`, the renderer and the owner's pictures from a config file off the repo; its window found by title class (pid checked) and captured by pid; its sound by pid; the four virtual pads made before it starts (P1 = device 0 …); Home → the board's own pause (Esc once, the state kept; nothing before its first release); RESUME → Esc once; SAVE / LOAD → a plain refusal, nothing sent; **END → F10 (the board's quit), the exit awaited 8 s and its code in a row; no exit → SIGTERM with a row, then SIGKILL**. Tests through the real HTTP server on loopback: 16, 3 runs green; B90 / the client contract / B103 / B105 / PS2 / GameCube green; mutations 18 / 18. Nothing adopted; nothing committed. No title, path, address or picture in this record
---

# B108 — the board game as a launch the hub can stream, pause and end (2026-11-16)

**Why:** PrivyParty's step 2 (a streamed probe, PP-H2) needs the hub to launch the board like a game: from the onn,
streamed, its pads, pause and quit from the onn. **Baseline:** HEAD `f302f8a8`. **Design** hashed 16:53:45Z, before
code (`b108_2026-11-16/design.sha256`); no amendment.

## The settle — answered from the code (the design's §1-7; file:line under `PrivyHub/app/src/main/java/` for the client, `companion/` for the hub)

1. **The onn as it is can start it — as a game entry, no APK change.** The client has no list of systems: the Games
   screens are the category / game nodes the hub sends (`GET /sources` → `root`, then each node's `lazy_path` →
   `nodes`; MainActivity.kt 1416-1499); parsing is `org.json` with `opt*` reads — unknown keys ignored, missing
   optional fields defaulted, missing art skipped (1531-1680, 2509-2584). The one hard rule: a node's `node_type` must
   be known (an unknown one fails the whole page, 1675-1679) — so the board is **an ordinary system node holding one
   ordinary game node** (`games_system_party`, the game `game_party_<hex>`, URL-safe as the client needs: it does not
   encode the id, 12686-12694). Launch: "Launch on Companion" → Start Fresh → `POST /plugins/games/launch?id=…`, going
   on only when the answer says `active` and `paused` (12778); then `native-stream-start` (`active`, `alpha_version`
   "0.7"; NativeStreamActivity.kt 886-936, 1031-1040) and `native-stream-ready` (`released`; 3464-3486) — the plugin's
   own routes, unchanged. **What the client cannot do without a change** (stated; none needed for PP-H2): hide SAVE,
   LOAD (always on the paused bar, 15573-15589), Cheats, Mods and Input Profile (always listed, 7350-7511, 9280-9283)
   — the hub answers them with a plain line the onn shows ("HTTP 400: …", 16093-16098). The client change, if wanted
   later: a per-entry capability (e.g. `states: false`, `extras: false`) read in the bar and the Extras / Options
   lists — **app cells:** the bar hides SAVE / LOAD for such an entry; Extras / Options skip Cheats, Mods, Input
   Profile; an older hub (no field) shows them as today; **hub cells:** the board's `details` carries the fields; every
   other entry's answer byte-equal.
2. **The window.** No hub code moves a window; emulators fill the screen by their own fullscreen setting (PCSX2
   `-fullscreen`, `ps2_session.py:371`; Dolphin `Fullscreen=True`, `gamecube_session.py:211`). The board gets
   **Godot's own `--fullscreen`** (in its `--help`), the project's files untouched. The capture finds a window by pid
   (`xdotool search --onlyvisible --pid`, `getwindowpid == pid`, the largest; `native_stream.py:843-1019`); the
   executable is started directly (no shell), so its pid owns its window. The launch also finds it **by its title
   class** (`xdotool search --onlyvisible --class PrivyParty`, its pid checked) — a `window` row; no window in 15 s →
   refused and ended by the quit path.
3. **Capture and sound.** The capture needs nothing new. The sound is per process: the stream waits for **exactly
   one** PulseAudio sink-input whose `application.process.id` is the pid and moves it to its null sink
   (`native_session_io.py:287-314, 989-1119`); the launch waits for it (15 s) as PS2 / GameCube do
   (`emulator_manager.py:7579-7583`) — an `audio` row either way.
4. **The pads.** Four uinput pads "PrivyHub Virtual Gamepad P1-P4" (0x1209 / 0x5048) are made in that order before
   every launch (`plugins/games.py:3684` → `native_session_io.py:2093, 1644-1647, 1911-1924`); the onn's packet's
   player byte (0-3) drives P<n+1> (`native_session_io.py:2337`), and **the onn chooses that byte** (its own
   hold-to-join, the lowest open slot: PlayerPrompt.kt 342-376, 406-430; PadSlots.kt 18-19) — so the onn's player 1
   always drives P1, whatever order the pads joined (tested with the bridge). Godot reads joypads through SDL, which
   numbers them as it finds them; the pads exist before Godot starts, in /dev/input order = their creation order →
   **P1 = device 0 … P4 = device 3** (stated from the code; the launch writes a `pads` row with their event numbers;
   PP-H2 confirms it). The board gets the same SDL mapping as PCSX2 (`SDL_GAMECONTROLLERCONFIG`, the 0x1209 / 0x5048
   string). **The joins:** the onn's join ("Hold any button to join", 500 ms) is client-side and only decides which
   pads send (an unclaimed pad's keys are dropped on the onn); the hub does not gate input. The board has its own join
   (any button held 0.5 s → the next seat; `input/controls.gd`). The board's repo is read only, so the hub cannot drop
   the board's join — **one gesture, a button held about a second, does both** (the onn's join at 0.5 s; the board
   sees the button from the first packet and seats the player 0.5 s later). If two hold together, the board seats in
   its own order (PP-H2's user line says which). **The onn's player count:** the board has no player metadata, so the
   stream's start says 2 players (the onn's join closes after two pads); a third or fourth onn pad would ask the hub
   to relaunch with more ports, which the board refuses (no state) — enough for PP-H2's two pads; four waits.
5. **Home, RESUME, SAVE, LOAD, END** — the client's routes as today (there is no pause route; Home / Back closes the
   stream: `native-stream-stop`, NativeStreamActivity.kt 4641-4653, 1288-1292; games.py 4317-4343 pauses the game, then
   stops the stream — an emulator's today: the stream ends, the game paused):
   - **Home** → `pause` → **Esc once** by XTEST (`xdotool windowactivate --sync <id> key --clearmodifiers Escape`, as
     PP-H1's F10); the board's pause is a toggle (`input/controls.gd` 85-86, 200-201: it opens its options window),
     so the hub keeps the state: **nothing when already paused**, and **nothing before the board's first release**
     (the plugin pauses every game at launch and again at the stream's start; the board then sits in its lobby).
   - **RESUME** (the stream again, then `native-stream-ready` → `resume`) → **Esc once** if it was paused by key.
   - **SAVE / LOAD** (`save-state` / `load-state`) → "Saving and loading are not offered for the board game; nothing
     was sent." (400; the onn shows it), nothing sent.
   - **END** (`stop`) → **F10 by XTEST** (the board's `quit`), the exit awaited **8 s**, the code in an `exited` row;
     **no exit → SIGTERM** (a `sigterm` row: "no exit 8 s after F10"), then SIGKILL after 5 s more (a `sigkill` row).
     Another game's launch and `launch_orphaned` reach the same stop.
   - **Per route, not for this launch:** `save-state`, `load-state`, the recovery save / load / relaunch-state /
     copy-to-slot (the link-drop recovery's give-up save gets the refusal and logs it, as B49 / B69's) — refused with
     the line above; a launch with a cheat or mod pick → "Cheats and mods are not offered for the board game." (what
     the onn's Cheats / Mods screens list for the board was not checked); `disc-swap` and PS2 patches — not offered (no discs; `ps2_patches.available`
     false); the mapping editor — not offered (`controller_profile_selectable` false; the profile catalog returns
     none for the board, as for PS2 / GameCube); the recovery rewind — never reached (RetroArch's; the `godot` kind
     has no core).
6. **The status the onn polls** (`GET status`, after returning to the menu): as any game (`active`, `paused`,
   `game{…}`, `pid`), plus with the flag `"launch_kind": "godot"` and `"party": {"renderer", "window",
   "paused_by_key"}`.
7. **Two launches** (today's rule, unchanged): another id → the running game stopped first (the board by F10;
   an emulator by its own stop); the same id → "A PrivyHub game session is already running".

## What was built (all behind the flag)

- `companion/party_session.py`: the config (`PRIVYHUB_PARTY_CONFIG`, else `$XDG_CONFIG_HOME/privyhub/party.json`;
  `{"godot", "project", "pictures", "renderer"}`; the plain refusals: "The board game is not set up on this hub (no
  config file)", "…config is incomplete: <field>", "…<field> was not found", "…renderer must be gl_compatibility or
  mobile"); the command `[godot, --path, project, --rendering-method, renderer, --rendering-driver, opengl3 | vulkan,
  --fullscreen, --, --content=<pictures>]` (Compatibility when unsaid); the window by class and pid; the sound stream;
  the pads row; pause / resume by its keys; the quit; one row per step in `logs/games/party.jsonl` (field names and
  numbers, never paths).
- `emulator_manager.py`: `_launch_party` (the board's own log `logs/games/<ts>-party.log`), `_party_pause_resume`,
  `_party_stop`, the dispatch in `launch` / `pause` / `resume` / `stop`, the seven state refusals, the profile bypass,
  the status fields, the self-ended cleanup. `plugins/games.py`: the system listed, its one entry scanned, the stream
  start's `party_mode` and a `party_session` row in the recovery log.

## Tests (`tests/b108_party_launch/`, 16; the real HTTP server on loopback; no Godot, no emulator, no window)

A stand-in board (a small executable script as the config's `godot`: records its command line and environment, says
its pid, exits 0 on the fake F10 or ignores it), a fake `xdotool` / `pactl` (recorded), a fake /proc pads listing, a
stub stream recording its starts; B101's fake RetroArch for the emulator side; QUIT_WAIT_S 1 s in the test.

- **Listed:** `games_system_party` with one `game_party_…` entry; its `details` 200.
- **The refusals:** no config, a missing field, a missing folder, a bad renderer word, a mod pick — each its plain
  line; nothing started.
- **The launch** (renderer `mobile`): the command line exactly (`--path`, `--rendering-method mobile`,
  `--rendering-driver vulkan`, `--fullscreen`, `--`, `--content=…`), the SDL mapping present, no key at launch, the
  window by class with its pid, the sound stream, `active` / `paused` true, `launch_kind` `godot`; no path in any row.
- **The pads:** the row lists P1-P4 in event order (the fake listing shuffled); the bridge with a shuffled join
  (players 2, 0, 3, 1) drives P3, P1, P4, P2 — each its own; the names P1-P4 in creation order.
- **The stream as for a game:** `native-stream-start` 200 with `party_mode`, the stream asked once with the board's
  pid; `native-stream-ready` `released`, no key at the first release.
- **Home** → Esc once; Home again → nothing; **RESUME** → Esc once; the rows.
- **SAVE / LOAD** → the plain refusal, no command at all.
- **END** → F10, `quit 0`, graceful, the board gone, `exited` code 0, under a second; **END with a board that ignores
  F10** → SIGTERM after the wait (`sigterm` row "no exit 1 s after F10"), not graceful.
- **Two launches:** the board again while it runs → "already running"; a PS1 title while the board runs → the board
  quit by F10 first, then the title; the board while the title runs → the title stopped first, then the board.
- **The board's toggle** (the session directly): Esc only to change the state — none in the lobby, one per pause /
  resume, none for a pause while paused (the plugin also pauses only an unpaused game: a second guard).
- **`launch_orphaned`** → the board quit by F10. **Only** `xdotool search / getwindowpid / windowactivate` and
  `pactl list` were called.
- **The flag absent and `0`** (`FlagAbsentIsToday`): `sources`, `systems`, the board's (absent) games, `details` of
  the board's (absent) id and of a PS1 title, the PS1 games list — **byte for byte as `git archive f302f8a8`'s
  companion** (the fixture tree's own folder named the same in both runs); `status` equal with its running counters
  masked; a PS1 launch and stop the same codes; no `party` anywhere in the systems answer.
- Results: `tests_x3.txt`, `tests_mutations.txt` — **3 runs × 16 green; B90 10, the client contract 5, B103 13, B105 12, PS2 93, GameCube 54 OK; stand-ins / RetroArch left 0; temp dirs left 0; mutations 18 / 18 caught** (the second batch; the first's results kept as `*_first.txt`).

## Disclosed

- **A slip of mine, found by the GameCube suite in the first batch** (`tests_x3_first.txt`: `gamecube_session` 1
  error; HEAD's own code passes it): one of the seven refusals was inserted between the GameCube recovery load's
  source check and its `return`, so the GameCube branch lost its `return` — **with the board's flag off too** (the
  flag-absent HTTP comparison does not reach a GameCube recovery). Fixed (the refusal after the branch); all seven now
  follow a GameCube line that returns or raises; both companion files' diffs against HEAD are insertions only (no HEAD
  line removed or changed); the slip itself is mutation P18, run against B108's and the GameCube suite.
- **The first mutation run caught 16 / 17** (`tests_mutations_first.txt`): P4 (a pause while paused sends Esc again)
  was not reachable through the routes — the plugin pauses only an unpaused game — so a direct test of the session's
  toggle was added; the batch was run again.

- The settle's client and companion answers were gathered by two read-only code searches (sub-agents) and checked
  against the code where the build touched it; the file:line above are theirs and mine.
- Not proved here (no Godot or display used — the queue allows Godot headless only): that `--fullscreen` covers the
  panel on the hub's window manager, that Godot's sound stream appears as one sink-input with the board's pid, that
  SDL numbers the pads in creation order, and that Esc / F10 by XTEST reach the fullscreen window — each is a row in
  PP-H2's stage 1 / the sitting.
- Three test-side fixes during writing (no code change): the stream stub's keyword, a check that matched a field name
  instead of a path, the library answer naming each run's fixture folder; and one code fix found by the first run:
  `details` asked for an emulator profile the board does not have (the board now returns none, as PS2 / GameCube).

## Files

`b108_2026-11-16/`: start files, the design + hash, `b108.diff` (applies on `f302f8a8`), `diffs_apply_in_order.txt`,
`sha256_before_after.txt`, `tests_x3.txt`, `tests_mutations.txt`, `scripts/` (`run_all.sh`, `mutate.py`,
`mutations.json`), redact / title checks, `manifest.sha256`. Patch note: `patches/B108_PARTY_LAUNCH.md`.
