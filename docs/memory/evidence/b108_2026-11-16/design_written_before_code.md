# B108 — the board game as a launch the hub can stream, pause and end: the design, written before code (queue AO)

Baseline HEAD `f302f8a8`. New: `companion/party_session.py`; hooks in `companion/games/emulator_manager.py` and
`companion/plugins/games.py`, **each behind `PRIVYHUB_PARTY=1`** (imported only then, every use guarded by
`_party is not None` — B49 / B69's pattern; absent / `0` = today byte for byte, proved through the real HTTP routes on
`git archive f302f8a8`'s companion against this one: `sources`, `systems`, a system's games, `details`, `launch`,
`status`, the library the onn reads included). Tests: `tests/b108_party_launch/`.

## The settle (from the code; file:line in the record)

**1. How the onn as it is (APK `ca53df0d…`, no client change) can start it — it can, as a game entry.** The client
has no list of systems: the Games screens are whatever category / game nodes the hub sends (`sources` → `lazy_path`s;
`org.json` with `opt*` reads — unknown keys ignored, missing optional fields defaulted; any game `kind` other than a
session is a catalog game). Its only hard requirement on a node is a known `node_type` (an unknown one fails the whole
page) — so the board is listed as **a new system node (`games_system_party`, "PrivyParty") holding one ordinary game
node**, built by the same code as every system and game (nothing new for the client to parse). Launch is the same
"Launch on Companion" → Start Fresh → `POST /plugins/games/launch?id=<id>` (the id must be URL-safe: `_stable_id`'s
`game_party_<hex>` is); the client goes on only when the answer says `active` and `paused` true; then
`native-stream-start` (`alpha_version` "0.7", `active` true) and `native-stream-ready` (`released` true) — all the
plugin's existing routes, unchanged. **So the cheapest way needs no APK change: the board is a game entry and a launch
kind.** No client sketch is needed for starting it; what the client cannot do (below) is stated, with the cells it
would need.

**2. The window.** No hub code moves or sizes a window: each emulator fills 1920 × 1080 by its own fullscreen setting
(PCSX2 `-fullscreen`, Dolphin `Fullscreen=True`, RetroArch its config). PP-H1's plain window (`--resolution
1920x1080 --position 0,0`) lost 51 lines to the panel. The board is started with **Godot's own `--fullscreen`** on the
command line (in its `--help`: "Request fullscreen mode"; the window manager covers the panel for a fullscreen
window), the project's files untouched. The capture finds a window **by the process's pid** (`xdotool search
--onlyvisible --pid`, `getwindowpid == pid`, the largest); the board's executable is started directly (no shell
between), so its pid owns its window. The launch also finds the window **by its title class** (`xdotool search
--onlyvisible --class PrivyParty`) and checks its pid is the launched one — a row; no window in 15 s → the launch
refused, the process ended by the quit path.

**3. Capture and sound.** The capture needs nothing new (the pid's window, as for PCSX2 / Dolphin). The sound is per
process: the stream waits for exactly one PulseAudio sink-input whose `application.process.id` is the pid and moves
it to its null sink. Godot's Linux audio (PulseAudio driver) opens such a stream; the launch waits for it as B50 / B69
do (up to 15 s; a row either way — a board without its sound stream is still launched, the row saying so).

**4. The pads.** Four uinput pads ("PrivyHub Virtual Gamepad P1-P4", 0x1209 / 0x5048) are created in that order by
`ensure_game_controller` **before every launch**; the onn's packet's player byte (0-3) drives P<n+1>, and the onn
chooses that byte (its own hold-to-join, the lowest open slot) — so the onn's player 1 always drives P1, whatever
order the pads joined in. Godot reads joypads itself through SDL, which numbers devices in the order it finds them;
the pads exist before Godot starts and are found in /dev/input order (their creation order) → **P1 = device 0 … P4 =
device 3** (stated from the code; the launch writes a `pads` row with the four devices' event numbers in creation
order; PP-H2 confirms with the user's line). The launch passes Godot the same SDL mapping string PCSX2 gets for
0x1209 / 0x5048 (`SDL_GAMECONTROLLERCONFIG`), so the pads read as standard pads. **The joins:** the onn's join
("hold any button to join", 500 ms) is client-side and only gates which pads send; the board has its own (hold any
button 0.5 s → the next seat). The hub cannot make the board skip its join (its repo is read only), so **one gesture —
hold a button about a second — joins both** (the onn's join at 0.5 s, then the board sees the button held from the
first packet and seats the player 0.5 s later). Stated, not two separate steps; if two players hold together, the
board seats in its own order (the user's line says which).

**5. Home, RESUME, SAVE, LOAD, END** (the client's routes, as today):
- **Home** → the client closes the stream (`native-stream-stop`): the plugin pauses the game, then stops the stream
  (an emulator's today: the stream ends, the game paused). For the board, `pause` = **the board's `pause` action: Esc
  sent once** (`xdotool key --window <id> Escape`, XTEST) — the board's pause is a toggle (its options window), so the
  hub keeps the state and sends nothing when already paused. **At launch** the plugin pauses every game at once (and
  `native-stream-start` pauses again): before the board's first release the hub records "paused" **without a key**
  (the board sits in its lobby; nothing plays); from the first `native-stream-ready` on, pause / resume send Esc.
- **RESUME** → the client starts the stream again and calls `native-stream-ready` → `resume` → Esc once if the hub
  paused it by key, else nothing.
- **SAVE / LOAD** (`save-state` / `load-state`, always on the onn's bar) → `"Saving and loading are not offered for the
  board game; nothing was sent."` (the plugin's EmulatorError path; the onn shows the text), nothing sent.
- **END** (`stop`) → **the `quit` action: F10 by XTEST** to the board's window, the exit awaited **8 s**, the exit
  code recorded in a row; **no exit in 8 s → SIGTERM** (a row saying so), then SIGKILL after 5 s more (a row).
  `launch_orphaned` and a launch of another game reach the same `stop`.
- **Per route, not for this launch:** `save-state`, `load-state`, the recovery save / load / relaunch / copy-to-slot
  (the link-drop recovery's give-up save logs the refusal, as B49 / B69's), `disc-swap` (no discs: the onn does not
  show it), PS2 patches (not offered: `ps2_patches.available` false), a launch with a cheat or mod pick → refused
  "Cheats and mods are not offered for the board game", the mapping editor (`controller-profile` — the board reads
  its own pads; not offered: `controller_profile_selectable` false; the Input Profile screen still lists, its save is
  for RetroArch systems and does not reach this launch), the recovery rewind (the hold / rewind paths are RetroArch's:
  a `godot` kind has no core and never reaches them). **Not hideable on the onn without a client change: SAVE, LOAD,
  Cheats, Mods and Input Profile** — answered by the hub (above).

**6. The status the onn polls** (`GET status`, after returning to the menu): `active`, `paused`, `game{id,title,
system,system_name}`, `pid` as for any game; plus `"launch_kind": "godot"` and `"party": {"renderer", "window",
"paused_by_key"}` with the flag only.

**7. Two launches.** Today a launch of another id stops the running game first (any kind); the same id while it
runs → "already running" (and the stream torn down). The board is the same: a board launch while an emulator runs
stops the emulator first; an emulator launch while the board runs ends the board by the quit path first; a second
board launch while it runs → today's refusal.

## The config (off the repo)

`PRIVYHUB_PARTY_CONFIG` names a JSON file, else `$XDG_CONFIG_HOME/privyhub/party.json` (else `~/.config/…`): `{"godot":
<executable>, "project": <the board's folder>, "pictures": <the owner's pictures folder>, "renderer":
"gl_compatibility" | "mobile"}`. **Absent** → "The board game is not set up on this hub (no config file)"; a missing
field → "The board game's config is incomplete: <field>"; the executable not a file / the project without
`project.godot` / the pictures folder not a folder → "The board game's <field> was not found"; another renderer word →
"The board game's renderer must be gl_compatibility or mobile". Nothing of the config's paths is logged or answered
(rows carry field names, never values).

## The launch

`[godot, "--path", project, "--rendering-method", renderer, "--rendering-driver", "opengl3" | "vulkan", "--fullscreen",
"--", "--content=" + pictures]`, `cwd` the project, `start_new_session`, stdout to the per-launch log
(`logs/games/<ts>-party.log`), the environment plus the pads' SDL mapping. Then the window (by class, pid checked),
the sound stream, the `pads` row; the answer `active` true, `paused` true (recorded, no key), `launch_kind` "godot".
**One row per step** in `logs/games/party.jsonl`: `launch` (renderer, fields present), `window`, `audio`, `pads`,
`pause` / `resume` (key sent or not), `refused` (the plain line), `quit` (F10 sent), `exited` (code, seconds),
`sigterm` / `sigkill` (after how long).

## Tests (`tests/b108_party_launch/`, the real HTTP server on loopback; B82 / B83's fixture tree)

A stand-in board (a small Python script given as the "executable": records its command line and environment, holds a
fake window, exits 0 on the fake F10 — or ignores it, by a word in the config's project folder); a fake xdotool (the
window search by class / pid, `getwindowpid`, `key`), a fake sink-input lookup and B90's fake pads. Cases: a good
config → the command line (the executable, `--path`, the renderer and its driver, `--fullscreen`, `--content=` after
`--`), the window found, the answer `active` / `paused`, `native-stream-start` asked for as for a game; no config, a
missing field, a missing folder, a bad renderer word → the plain refusals; the pads' order (P1-P4 created before the
launch; a shuffled join on the client side still drives P<n+1>); Home (`native-stream-stop`) → Esc once (a second Home
nothing); RESUME (`native-stream-ready`) → Esc once; at launch no key; SAVE / LOAD refused, nothing sent; END → F10, exit
0 awaited, the row; END with a board that ignores F10 → SIGTERM after 8 s, the row; a second launch while it runs; an
emulator launch while it runs and the reverse; `launch_orphaned`; the flag absent / 0 → HEAD's answers byte for byte
(the library included); B90, the client contract, B103 / B105 green.
