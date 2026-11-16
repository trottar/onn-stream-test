# SESSION B — done, 2026-11-16 AO (QUEUE_2026-11-16AO: B107 step 19's numbers, B108 the board game as a launch behind PRIVYHUB_PARTY=1, B109 A's PP-H2 sketched; run 16:42Z-17:21Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (PP-H1 committed in
`f302f8a8` with queue AO). `privyhub-diag` and its folder untouched; no stream, no companion or keeper restart, no adb,
no sudo, no nft; nothing fetched or installed; nothing written to the drive; nothing of A's touched; no emulator
started; nothing of the user's deleted. **The board game's repo** (at `21e7e44`, the hand-back — the PC side has not
pushed since PP-H1) read only: its tree clean and its `.godot` cache identical before and after; **Godot run headless
only**, in scratch copies of the repo with its own folders redirected, all removed after; **the pictures' folder never
opened**. The `/tmp/b_q27ao` copy holds companion/, tools/, tests/, PrivyHub/ (build outputs left out). Nothing
adopted; nothing committed.

## What was found and built

- **B107 — step 19's numbers** (`evidence/B107_PP_STEP19_NUMBERS_2026-11-16.md`): the Hips piece of the committed
  `models/template_body.glb` (sha256 `c3e5545e…`) counts **front 9, sides 4, back 18** — sides 4 is not "more than
  four". **The same after PP-H1's import, two fresh imports, the import's compression switched off, and on the file read
  raw with no import** (every normal equal to the imported one; the import's mesh is stored uncompressed). Not a value
  at a limit: the side corners' |n.x| are 0.9999 ×2 and 0.9626 ×2, the next 0.8315 against the cut 0.92. UpperChest
  14 / 8 / 28, LeftUpperLeg 17 / 10 / 24, RightLowerLeg 16 / 10 / 24 pass. **For the PC side:** compare the PC's body
  model's sha256 with `c3e5545e…` (the README has the checks run after Blender rebuilds it); if equal, run
  `b107_2026-11-16/step19_numbers.gd` there.
- **B108 — BUILT** (`evidence/B108_PARTY_LAUNCH_2026-11-16.md`), behind `PRIVYHUB_PARTY=1` (absent / 0 = HEAD's
  answers byte for byte, the library the onn reads included): the board is **a game entry in its own system, so the
  onn as it is starts it** (Games → PrivyParty → the game → Launch on Companion → Start Fresh; no APK change); Godot
  started directly with `--fullscreen`, the renderer and the pictures from a config file off the repo; window and
  sound by pid; the pads made before it starts; Home → Esc (the board's pause; kept state, nothing before its first
  release); RESUME → Esc; SAVE / LOAD → "Saving and loading are not offered for the board game; nothing was sent.";
  **END → F10 (the board's quit), the exit awaited 8 s, its code in a row; no exit → SIGTERM with a row, then
  SIGKILL**. Tests 16 (3 runs green), B90 / the client contract / B103 / B105 / PS2 / GameCube green; mutations 18 / 18.
  **A slip of mine, caught by the GameCube suite in the first batch and fixed:** one refusal had been inserted inside
  the GameCube recovery load's branch, cutting off its `return` even with the flag off; now both companion files'
  diffs are insertions only, and the slip is a mutation the batch catches.

## What I would change (not done — the queue is the task)

1. **Step 19:** nothing on the hub can change the count — the body model as committed has four side corners on its
   Hips piece. Either the PC's model differs (commit it), or the check's bar for the Hips piece is too tight for the
   model; that is the PC side's call.
2. **A client capability for non-emulator entries** (states / extras off) so SAVE, LOAD, Cheats, Mods and Input Profile
   are not offered for the board at all — today they are answered with a plain refusal (the cells are in B108's
   record). Not needed for PP-H2.
3. **Four players for the board:** the onn's join closes after two pads (no player metadata → 2); a `players` answer of
   4 for the board's entry would let four join — a small hub change, not built (two pads in PP-H2).
4. **One join instead of a long hold:** only the board can drop its own join (e.g. take the onn's seats from the
   devices that send first); the hub cannot without editing the board.
5. **What only the sitting can show** (B108's tests use a stand-in): `--fullscreen` over the panel, Godot's sound
   stream as one sink-input with its pid, SDL's pad order, Esc / F10 by XTEST reaching the fullscreen window — PP-H2
   stage 1 checks each with the real board before the user is asked.

## A — PP-H2, the streamed probe (B109; attended, ~12 min at the TV)

The user with the onn and two pads paired to the onn over Bluetooth, as always; **nothing asked of the user on the
hub**; every message to the user starts **"YOU, now:"** and is **a complete step** — the screen, the entry, the button
— naming **only what the onn will offer, read from the hub at stage 1**; the stages go by the user's messages; **A
never holds a turn while the user plays** (every read is a watcher already running or a read after the user's message).
No title, path, address or picture in any record.

### Stage 1 — unattended (pre-registered after it)

1. **Preconditions:** HEAD with queue AO committed, the tree clean (else "YOU, now: commit queue AO first"); only the
   companion and `privyhub-diag`; no game (`curl -s http://127.0.0.1:8765/plugins/games/status` → `"active": false`);
   eighteen lines, `--check` ok; `adb connect` from the hub if the device is not listed (as HOME-4+), the APK
   `ca53df0d…` read back CONFIRMED.
2. **The board's checks:** `git -C <the board's repo> log -1 --format=%h` — if not `21e7e44` (the PC side has pushed),
   the import then the 25 checks headless exactly as PP-H1 (`GODOT --headless --path . --import`, then each
   `checks/stepN_*.gd`), the PASS lines in `pre/checks.md`; else **step 19 noted as open** (B107's numbers) and the
   checks not re-run.
3. **The config file, off the repo:** `$XDG_CONFIG_HOME/privyhub/party.json` (the companion's environment's config
   home) = `{"godot": "<the Godot executable>", "project": "<the board's repo>", "pictures": "<the owner's pictures>",
   "renderer": "gl_compatibility"}`; its field names recorded, never its values.
4. **The bench flag for the sitting only:** a drop-in `privyhub-party.conf` with `[Service]` /
   `Environment=PRIVYHUB_PARTY=1` → the companion's drop-in folder; `systemctl --user daemon-reload`;
   `systemctl --user restart privyhub-companion`; MainPID owns 8765; **nineteen** lines (`--check` not ok on the
   environ only).
5. **What the onn will offer, from the hub's own state** (`pre/onn_offers.md`): the systems list
   (`curl -s http://127.0.0.1:8765/plugins/games/systems`) — the board's entry's exact name and count (expected
   "PrivyParty", 1) and its place among the systems (Down / Right presses from the first tile on the onn's Games
   grid); its one game's tile; the start box (Start Fresh · Load Save · Extras); the pads' class from the recovery
   log's `pad_slots` rows (Sony → "hold ✕"); the join lines "Hold any button to join", "P1 joined — hold to add Player
   2"; the paused bar RESUME PLAYING · SAVE · LOAD · END.
6. **The board on the hub before anyone is asked** (no user; the onn not involved): `curl -s -m 120 -X POST
   'http://127.0.0.1:8765/plugins/games/launch?id=<the board's id>'` → `active`, `paused` true; then
   `tail logs/games/party.jsonl` → **`window` found (class PrivyParty) and `audio` `sink_input` true**, and
   `xdotool getwindowgeometry <id>` → **1920 × 1080 at 0, 0** (fullscreen over the panel); the `pads` row P1-P4 in
   event order; then `curl -s -X POST http://127.0.0.1:8765/plugins/games/stop` → `party_exit` `"quit 0"`, an
   `exited` code 0 row. **If any of these is not so, stop here — no sitting** (one plain line to the user).
7. **Watchers from stage 2's start** (read only, once a second): `h7`-style status watch
   (`curl -s -m 2 http://127.0.0.1:8765/plugins/games/status`), `tail -F logs/games/party.jsonl`; the CPU of the
   encoder (the stream's `ffmpeg` process) and of Godot from `/proc/<pid>/stat` (utime + stime per second), the
   graphics device's `gpu_busy_percent` under `/sys/class/drm/card*/device/` — each a TSV with UTC seconds.
8. **Before:** the saves listing as PP-H1 (161; no `.state8`); the pictures folder's count and bytes (116 / 15,039,288
   at PP-H1); the stream marks (bitrate rows, recovery log, `launch_orphaned` count).
9. **Pre-registration hashed** (below).

### Stage 2 — the user (the lines filled in at stage 1)

- **"YOU, now: on the onn's PrivyHub home, open Games, then [the board's entry's exact name]. Press OK on its one
  game. In the box that opens choose 'Launch on Companion' and press OK. In the box 'Start …' choose 'Start Fresh' and
  press OK. When the picture shows 'Hold any button to join' at the bottom, hold ✕ on the first pad for about two
  seconds — until 'P1 joined — hold to add Player 2' shows and the board's lobby shows a first player — then do the
  same on the second pad. Then tell me 'ready'."**
- On "ready" (A reads the status and the rows): **"YOU, now: start a game in the board's lobby with the first pad and
  play through to the first mini game and one or two rounds of it. Then press the Home button on the first pad (the
  bar RESUME PLAYING · SAVE · LOAD · END appears) and tell me 'paused'."**
- On "paused": **"YOU, now: choose RESUME PLAYING and press OK, play on for a minute — each of you move your own
  figure once, player 1 first, then player 2 — and tell me in one line whether each pad moved its own figure."**
- On the user's line: **"YOU, now: press Home on the first pad, move to END and press OK. Tell me 'ended'."**
- **The second renderer** (if time allows; stated in the record either way): A sets `"renderer": "mobile"` in the
  config file (no restart needed — read at each launch); **"YOU, now: open the board's game again — Launch on
  Companion, Start Fresh — join both pads the same way, play one round of the mini game, then Home, END, and tell me
  'ended'."**

**Pre-registered (hashed before stage 2), nothing perceptual:** **each pad drives its own seat** — the `pads` row P1-P4
in event order (P1 = device 0, P2 = device 1) **and** the user's line; **Home pauses and RESUME resumes** — a `pause`
row with key Escape after Home and a `resume` row with key Escape after RESUME, the status `paused` true then false;
**END quits by F10 with exit code 0** — a `quit` row then `exited` code 0, no `sigterm` row; **the stream's rows as a
normal game session's** — the bitrate's level, frames a second near 60, loss as a normal session's, no stall, no
recovery row; **audio packets flowing** (the stream's audio counters growing); **the encoder's and Godot's CPU and the
graphics busy share** under Compatibility (and Mobile, if run) — recorded as medians over the play, no bar; **nothing
of the user's touched** — the saves 161 = 161, no `.state8`, the pictures folder's count and bytes unchanged. All met →
**MET**.

### The close

Watchers stopped; the drop-in removed; `systemctl --user daemon-reload`; the companion restarted (MainPID owns 8765);
**eighteen** lines, `--check` ok; the board's entry gone (`curl -s http://127.0.0.1:8765/plugins/games/systems` without
"PrivyParty"); no board process left (`pgrep -f Godot_v4` empty). The config file stays off the repo.

### The record

`evidence/PP_H2_<date>.md` + `pph2_<date>/`: `pre/` (HEAD, both repos' heads, the checks or the step-19 note, the
config's field names, the drop-in's hash, nineteen lines, `onn_offers.md`, stage 1's own launch rows, the before
listings), `run/` (`cells.md`, `party_rows.jsonl`, the status watch, `cpu_gpu.tsv`, `stream_rows.md`,
`user_lines.txt`), `close/`, `preregistration.md` + `.sha256`, title / redact checks, `manifest.sha256`.

## Files

B107: `evidence/B107_PP_STEP19_NUMBERS_2026-11-16.md` + `b107_2026-11-16/` (no code; no patch). B108:
`companion/party_session.py`, `companion/games/emulator_manager.py`, `companion/plugins/games.py`,
`tests/b108_party_launch/`, `evidence/B108_PARTY_LAUNCH_2026-11-16.md` + `b108_2026-11-16/`,
`patches/B108_PARTY_LAUNCH.md`. Then `docs/KNOWN_ISSUES.md` (one line), `docs/ROADMAP.md` (one paragraph after PP-H1),
`logs/b107_git_status.txt`, `logs/b108_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.
