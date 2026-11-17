# SESSION B — done, 2026-11-17 AV (QUEUE_2026-11-17AV: B137 nothing a player presses reaches the title before the go, B138 A's two next tasks sketched; run ~21:19Z-22:29Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (queue AU in
`498ff031`, the prompt files tracked and unchanged); **the board's repo clean at `4140949`** = the PC side's
`f8d92e38…` plus one commit of the user's holding my two files (`minigames/hub_minigame.gd` `e580c3e1…`,
`checks/hub_minigame_check.gd` `76018a20…`, as B135's record). No stream, no companion or keeper restart, no adb, no
sudo, no nft; nothing fetched or installed; nothing written to the drive; the users' setups, slots and in-game saves
not opened; **read only:** the rules folder (the two titles' specs and sidecars), the kept H7 folders (T89's kept begin
picture) and `runtime/h7_frames/` (the watcher's kept pictures) — offline, through the reader, numbers only; **no
emulator title started** — disclosed: B61's form, the hub's RetroArch with its N64 core on a made-up ROM and its PS1
core on a made-up PS-EXE (the core's built-in OpenBIOS ran its boot animation; no BIOS file), temp folders, nine runs of
~40 s on the hub's display (21:21Z-21:35Z); **Godot headless only**, once: B111's own check of the board in its scratch copy (the board's repo status unchanged). **The board's repo: not
touched.** No title, serial, game id, `profile_id`, character name, cheat name or path in any record; no game's name
anywhere; no picture in git. The `/tmp/b_q33av` copy holds companion/, tools/, tests/, PrivyHub/ (its sources) only.
Nothing adopted; nothing committed in either repo. Deleted: only my own scratch (`~/.cache/b_q32av_tmp`: the probes'
folders and grabs, the label's crop; the mutation copies; `/tmp/b_q33av` kept).

## What was found and built

- **B137 — BUILT** (`evidence/B137_PARTY_NO_PRESS_BEFORE_GO_2026-11-17.md`). **Settled first:** (1) **a state loaded
  into a paused core:** the PS1 core leaves the window as it was until a frame runs — **one `FRAMEADVANCE` shows the
  loaded state**; the N64 core's load runs a frame itself (shown at once) **and that frame reads the pads**; each
  `FRAMEADVANCE` is one frame and reads the pads; `GET_STATUS` stays `PAUSED`; the window keeps the frame; ≥ 50 ms
  apart every command counts; **sent: 2 frames, 60 ms apart** (one of margin). (2) **RetroArch draws "Paused." in the
  window's corner for as long as a core is paused** — offline, **0 of T88's 150 kept start pictures read as the start
  with it** (its text breaks the reader's black-bar cut), **150 / 150 with that corner painted black** (the ends 15 / 15,
  `other` 335 / 335, the same margins); T89 has no kept start picture: the label moves its begin picture's distance by
  +0.0014 against a 0.067 gap — small, not proven (H7-V6 shows it). **Built:** paused → the bridge's mute (every pad
  neutral, every report dropped) → the watch's load → 2 × `FRAMEADVANCE` → the mute off (**~0.2-0.3 s**, the board loses
  those presses too) → `minigame_frame_advance` → the watcher reads the paused window, the label's corner masked →
  `ready`; **the go: route, switch, resume — no second load**; a practice's way back paused first, then the same
  preparation. **The title is never resumed between the launch's answer and the go.** The fallback (the reports dropped
  for a whole run-behind preparation) is not what the bench shows is needed: **not built**. Tests 10 (3 runs);
  **HEAD's code under the same presses → "not recognised"** (with none → ready).
- **B138 — sketched below (no code):** H7-V6 again with B137's order and the paused proof; PP-H3c, the user alone with
  two pads, before four people sit down; PP-H4's changes.

Tests (`b137_2026-11-17/tests_x3.txt`, `tests_others.txt`): **B137 10, B133 9, B134 5 — 3 runs green each**; B133's two
row lists updated for B137's order; mutations 4 / 4 (`tests_mutations.txt`); **the others once, all OK**: B129 5, B130 4, B131 5, B127 9, B124 6, B114 8, B115 6, B110 13, B112 7, B123 6, B122 12, B111 2 (with Godot and the board's repo; without them it skips), B108 16, B105 12, B103 13, B102 16, B104 19, B101 14, B99 15, B65 7, B61 14, the player prompt 11, the players' session 19, the relaunch 19, the pad slots 5 + 7, the stall signal 12, the stall owner 10, the link recovery 16, the fast restart 13, the client contract 5, the input hold 19 + 22, the keyframe request 10, the loss rule 10, impairment 29, audio codec 20, B72 25, art_systems 120 (its one doc test reads `docs/CHEATS.md`, outside the work copy — OK against the repo), PS2 93, GameCube 54, N64 28. **Temp dirs:** B137's, B133's and B134's suites leave none; older suites (B2, B4, B7, B9, B22, B38, B41, G4's) leave theirs, as before — removed with my scratch; nothing left running.

## What I would change (not done — the queue is the task)

1. **RetroArch's on-screen messages for a party mini game's title** (a per-launch appended config turning them off):
   no "Paused." to mask, and no load or cheat notices covering the begin — T88's start is read at 9-10 s mostly because
   of them. It touches the launch path the users' Extras launch shares, so not here.
2. **T89's paused read** is shown small offline, not proven (no kept start picture of its window). If H7-V6 step 10
   gives it up "not recognised", the fallback for that title only (the reports dropped through a run-behind
   preparation, the begin loaded again at the go under the mute) is a small change on top of B137 — chosen by that
   bench, not before.
3. **The pad's Select during the hold:** RetroArch's hotkeys are pairs with Select (the hotkey button) and a paused
   core still takes them — Select + R3 would resume the title behind the board, Select + Start quit it, Select + L1 / R1
   load or save the setup's slot. The board uses A, B, Y, the d-pad and Start, never Select: dropping Select from the
   reports while a held title waits would close it at no cost. Not seen; not built.
4. **The presses before the launch's answer** (~2 s while RetroArch starts the title, unrouted) still reach the booting
   title; its begin's load replaces whatever they did. Muting them too would take the board's presses at the very
   moment the load screen appears — the moment PP-H3c asks the players to press — so left.
5. **The way back's pause first** shows the paused title ("Paused.") on the TV for the switch's 1-4 s before the board.
6. From AU, still open: the onn's Home during the load screen gives the mini game up; `announce_minigame` still says
   "On the hub"; a second start's wording; the bench cannot press Start.

## A — H7-V6 again (B136 with B137's order, the paused proof), then PP-H3c, then PP-H4

T88 = H7's 2-player PS1 title (the duel); **T89** = the users' N64 four-player title; "T88's cheat setup" / "T89's cheat
setup"; `H=http://127.0.0.1:8765/plugins/games`; `$RULES` = the rules folder (B132's name for it); `<T88 id>`,
`<T89 id>`, the setups' ids, `TOKEN2` / `TOKEN4` read at run time, never in a record. **A game's name is run-time data
only.** **The paused proof** (used below): the title's command port is rewritten at each launch, so after each
`minigame_launch` row A reads it from `data/games/retroarch/config/privyhub-input.cfg` and asks once a second:
`P=$(grep -o 'network_cmd_port = "[0-9]*"' data/games/retroarch/config/privyhub-input.cfg | grep -o '[0-9][0-9]*');
python3 -c "import socket,sys;s=socket.socket(2,2);s.settimeout(0.5);s.sendto(b'GET_STATUS',('127.0.0.1',int(sys.argv[1])));print(s.recv(99).decode().split()[1])" "$P"`
— one word a second (`PAUSED` / `PLAYING`; no answer = `none`), the record keeps the words and their seconds only.
**Counted from each preparation's `minigame_watch` row to its go** (before it RetroArch is starting the title — B137
leaves those ~2 s as they were).

### H7-V6 — the new order, unattended (B112's bench, ~25 min; `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1` for the task only)

**Stage 1 (pre-registered after it):**

1. The window as before (outside 04:30-05:30Z, not within 45 min before it). **This repo with queue AV's B137
   committed** and clean but for this task's files (else stop: "YOU, now: commit queue AV first, then send the read
   line again"); the code is AV's: AU's three `grep`s (`def go(self, practice_text` in `companion/party_minigame.py`,
   `_party_buttons = None` in `companion/native_session_io.py`, `action == "party-minigame-go"` in
   `companion/plugins/games.py`) → 1 each, and **B137's: `grep -c "def party_mute" companion/native_session_io.py` → 1,
   `grep -c '"FRAMEADVANCE"' companion/party_minigame.py` → 1, `grep -c "def label_mask" companion/h7_minigame.py` → 1**
   (else stop and say which). Only the two units; no game; eighteen lines, `--check` ok.
2. **The rules folder as H7-V5b left it**, checked read only as B132's steps 3-6.
3. Both drop-ins; **twenty** lines. **Before:** every file under the states, saves and cheat setups (count, every
   sha256); no `.state8`; `party.jsonl` and `h7_results.jsonl` line counts. Pre-registration hashed.

**Stage 2 — by `curl` as the board would** (T88 then T89 in one companion):

4. **The board:** launched and released (B128 step 10). **The list:** `curl -s "$H/party-minigames" | python3 -c "import
   json,sys;print(sorted((e['players'], bool(e.get('title'))) for e in json.load(sys.stdin)['minigames']))"` →
   **`[(2, True), (4, True)]`**.
5. **T88 held, the board asking:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN2&seats=1,2&bench=1&hold=1"` →
   `"starting"`; poll the result once a second → `"preparing"` → **`"ready"` within 20 s (expected ~12 s)**, the
   paused proof running; `party.jsonl`: `minigame_start` `"hold": true`, `minigame_launch` `"cheat": true,
   "profile_matches": true`, `minigame_watch`, **`minigame_frame_advance` `"frames": 2, "paused": true`, `"mute_ms"`
   (expected 150-400)**, `minigame_ready` `"prepare_s"` — **no `minigame_route`, no `minigame_stream` before the go**;
   `h7_results` `watching` `"recognise_s": 15.0, "begin": "setup"`, **`"label_mask": true`**, `recognised` true.
   **Held 180 s**, the result asked once a second → every answer `"starting"`, `"ready"`; **the paused proof:
   `PAUSED` at every second from the watch row** (~190 words). **The go:** `curl -s -X POST "$H/party-minigame-go"` →
   `"taken"` → `"playing"`; rows `minigame_go` `"held_s"` ≥ 180, `"remembered": false`; **no `minigame_reloaded`**;
   `minigame_route`; `minigame_stream` `"switched": false` (the bench); `minigame_playing` `"handover_s"`; **one read
   after the go → `PLAYING`**. **The kept end P1 by hand** (B128 step 13) → **`ended` `end_P1` `[1, 0]`**; the end.
6. **A go before ready, a second go:** start held, `seats=2,1`; at once the go → `"remembered"`, `"preparing"`; again →
   `"already"`; → `"playing"` by itself once ready (`minigame_go` `"remembered": true`; no `minigame_reloaded`; the
   paused proof `PAUSED` from the watch row until the phase is `handing_over`); the kept end P2 → **`end_P2` `[0, 1]`**.
7. **A start whose screen is never the start:** start held, `seats=1,2`; **as soon as the `minigame_frame_advance` row
   is written** (~2.5 s; T88's start is read only at ~9-10 s), the kept mid-fight state by hand into scratch slot 8 of
   T88's setup's folder (B128 step 13's commands, the scratch removed at once) **and then one `FRAMEADVANCE` on the
   same port** (`…sendto(b'FRAMEADVANCE', …)`: a paused PS1 core shows a loaded state only after a frame) → the window
   shows a fight → **`given_up` "…the title's start screen was not recognised" ~15 s after the watch row**; no
   `minigame_route`, no `minigame_stream`; the paused proof `PAUSED` throughout; RetroArch gone; `status` → `godot`.
8. **Practices, T88:** start held `seats=1,2` → `ready`; `curl -s -X POST "$H/party-minigame-go?practice=1"` →
   `"practice": true` → `"playing"`; the kept end P1 by hand during it → still `"playing"`, no scores; **by time**: back
   to `"starting"` → `"ready"` with `"practices": 1` ~90 s after the practice began (`minigame_practice_end` `"by":
   "time"`; **a `minigame_frame_advance` row after it**; `minigame_ready` `"after_practice": true`); **the paused proof
   from that watch row to the next go: `PAUSED` every second**; a second practice → `"practices": 2`; a real go →
   **no `minigame_reloaded`** → the kept end P1 → **`end_P1` `[1, 0]`**; the end.
9. **T89:** start held `seats=3,1,4,2` → **`ready` within 15 s (expected ~6 s: the launch ~2.3 s, the load and the
   advances, RetroArch's notices running out paused, a read)** — **this is where T89 is read paused (the label's corner
   masked)**; the frame-advance row; the paused proof; one practice by time → `"practices": 1`; a real go (no reload) →
   `results_1` by hand while paused (B128 step 17) → **places `[1, 2, 3, 4]`, scores `[4, 3, 2, 1]`, seats `[3, 1, 4, 2]`**.
10. **The close of the board** (B128 step 19); **after:** every file of step 3 before = after; the in-game saves recorded
    (not a cell); no `.state8`.

**Pre-registered:** 4-10 as stated — **`prepare_s` T88 ≤ 20 s, T89 ≤ 15 s; one `minigame_frame_advance` per
preparation (`"frames": 2, "paused": true`, `"mute_ms"` < 1000); `PAUSED` at every read from each watch row to its go
(no `PLAYING`); no `minigame_reloaded` at any go; no route and no switch before any go; still `ready` after 180 s;
remembered, already; never the start given up with no route; practices back to `ready` by time with no scores; the real
ends as H7-V5b.** MET → PP-H3c may be offered. **If a title's preparation is given up "not recognised" (5, 8 or 9)
while its own begin was loaded:** A reads, for that watch, `h7_results` (`watching` with `"label_mask": true`, every
read's `class` and `distances`, `recognised`), the frame-advance row (`"paused"`) and the paused proof; then **not met
for that title** — the fallback (the reports dropped through a run-behind preparation, the begin loaded again at the go
under the mute) is not built; B builds it for that title alone; that title stays out of PP-H3c / PP-H4 until then (PP-H3c
needs T88 only). The close as B132's.

### PP-H3c — the first joint run: the user alone with two pads (part 1 on the bench ~10 min, unattended; part 2 ~15 min at the TV)

Why: the board's script (my B135), the PC side's real screens and the stream have never run together — the board's
check uses a made-up stage and, headless, the real screens answer at once. One person with a pad in each hand plays a
two-player board game to its first hub mini game (T88 for two), pressing at every load screen the moment it shows.

**Preconditions:** the window; **H7-V6 MET** (its record committed); this repo as H7-V6's step 1; **the board's repo
clean, at the PC side's `f8d92e38…` or later** (`git -C <board repo> merge-base --is-ancestor f8d92e38 HEAD`, exit 0) with
**the screens**: `grep -c -E "func (choose_minigame|show_minigame_loading|set_minigame_loading_ready|minigame_loading_choice|hide_minigame_loading)\("
game/presenter.gd` → 5 and `game/minigame_screens.gd` there, **my two files** `minigames/hub_minigame.gd` sha256
`e580c3e1…`, `checks/hub_minigame_check.gd` **`76018a20…`**, `grep -c "func first_here" game/minigame_picker.gd` → 1 (else
stop and say which: "YOU, now: in the board's repo run `git pull`, then send the read line again"); two pads paired to
the onn (the user's words at stage 1).

**Part 1 — the bench (gates part 2; pre-registered, hashed):**
(a) the board's checks headless in a scratch copy of its tree (Godot's folders redirected, as B135): `checks/hub_minigame_check.gd`
→ **PASS (81 assertions)**, the PC side's `checks/step25_before_minigame.gd` → **PASS**; (b) the rules folder as H7-V5b
left it (read only); (c) **before:** cell U's files (count, every sha256), no `.state8`, the rows' line counts; (d) both
drop-ins, twenty lines; (e) **one held T88 start on the bench** (the board launched and released as H7-V6 step 4,
`bench=1`): → `ready` (the frame-advance row, `"label_mask": true`, the paused proof `PAUSED` every second) → the go →
`playing`, no `minigame_reloaded` → the kept end P1 by hand → `end_P1` `[1, 0]` → the end; the board closed (B128 step 19).
Not met → no part 2 ("YOU, now: the hub did not pass its own check, so we stop here — nothing to do at the TV.").

**Part 2 — the lines** (every message "YOU, now:", a complete step; the onn's words as B125 read them; the buttons by
what the board's screens show — the load screen's badges **A "ready", B "not ready", Y "practice first"**, the selection
screen's "confirm: choose" — and where they sit on the users' PlayStation-layout pads: **A = ✕ (the bottom button),
B = ○ (the right one), Y = △ (the top one); Start = the pad's Start (OPTIONS on a PlayStation 4 or 5 pad: the small
button right of the touchpad)**; the board's own README, "Controls": confirm A, back B, map Y, pause Start):

- **First:** "YOU, now: you alone, with two pads paired to the onn — one in each hand. On the onn's PrivyHub home open
  Games, then 'PrivyParty (1)', press OK on its one game, choose 'Launch on Companion' and press OK, then 'Start Fresh'
  and OK. When 'Hold any button to join' shows, hold ✕ on the first pad until 'P1 joined' shows, then the same on the
  second pad. Then on the board's screen hold ✕ on each pad in turn until the board shows it as a player — two players.
  Tell me 'ready'."
- **The streamed self-proof** (on "ready", before anyone plays — as B136's, rows only): "YOU, now: put both pads down
  for about half a minute — the hub is checking itself; the TV will change to a game and come back. I'll tell you when."
  Then on loopback (no `bench`): `curl -s -X POST "$H/party-minigame-start?id=$TOKEN2&seats=1,2&hold=1"` → poll →
  `"preparing"` → **`"ready"`**, with the frame-advance row, **no `minigame_route` / `minigame_stream` row before the
  go**, the paused proof `PAUSED` every second and **the stream's last `Capture:` line still the board's window**
  (`grep -a "Capture:" logs/games/native_video_alpha.log | tail -1`: its `window_id` unchanged since the board's start);
  `curl -s -X POST "$H/party-minigame-go"` → **`minigame_stream` `"switched": true, "planned": true`** → `"playing"`; at
  once `curl -s -X POST "$H/party-minigame-end"` → the board back (`minigame_stream` board `"switched": true`). **Not
  met → "YOU, now: the hub could not get a game ready behind the board, so we stop here."**, the END step, no play.
- **Play to the mini game:** "YOU, now: pick the pads up again. In the board's lobby start a game — ✕ on the first pad —
  and play the first round, a pad in each hand: ✕ (bottom) rolls and confirms, the d-pad moves. When the round ends the
  board shows a choice of mini games with one card on it and says which player picks: on that player's pad press ✕
  (the screen says 'confirm: choose'). Then a load screen with the game's name comes up. **The moment it shows, press
  △ on the first pad and ✕ on the second at the same time** — that asks for a practice — and then press nothing until
  the TV changes. Tell me 'select' when you see the game's character select, and don't pick yet."
- **On "select" — a practice left by Start:** "YOU, now: that is a practice: pick and play a little with both pads,
  then press Start on either pad. The load screen comes back. **The moment it shows, press △ on the second pad and ✕
  on the first at the same time** — a practice again — and press nothing until the TV changes. Tell me 'select'."
- **On "select" again — a practice left by time:** "YOU, now: practice again, and this time don't press Start: play
  or wait until the load screen comes back by itself, about a minute and a half after the game came on. **The moment
  it shows, press ✕ on both pads at once** — both ready — and nothing else until the TV changes. Tell me 'select'."
- **On the third "select" — the real match, with one Home / RESUME:** "YOU, now: this one counts. Pick, and play the
  match to its end, a pad in each hand. Once during the fight, press Home on the first pad (the bar RESUME PLAYING · SAVE
  · LOAD · END appears), choose RESUME PLAYING and press OK; when 'Hold any button to join' shows again, hold ✕ on each
  pad in turn until it clears, and finish the match. When the board is back, tell me in one line who won (1P or 2P) and
  whom the board gave the win to."
- **END:** "YOU, now: press Home on the first pad, move to END and press OK. Tell me 'ended'."
- **"stuck"** and **"close":** B125's lines unchanged (a mini game on → `party-minigame-end` → "…that mini game counts as
  a draw…"; no mini game on and the board not back → the END line; no bar → the onn's top bar).

**The rows per step** (`party.jsonl` / `h7_results.jsonl`, nothing else): the board's start (B108's rows, `status`
`godot`); **the choice:** the board's log ("PrivyParty: hub mini game:" lines) and `minigame_start` `"hold": true` with
`TOKEN2`; **each load screen** (three): `minigame_watch` → `minigame_frame_advance` (`"frames": 2`, `"paused": true`,
`"mute_ms"`) → `minigame_ready` (`"prepare_s"`; `"after_practice": true` for the 2nd and 3rd) → `minigame_go`
(`"practice": true` for the 1st and 2nd; `"held_s"`; `"remembered"`) → `minigame_route` → `minigame_stream` (`"switched":
true, "planned": true`) → `minigame_playing`; `h7_results` `watching` `"label_mask": true`, `recognised` true;
**the practices:** `minigame_practice_end` `"by": "start_button"`, then `"by": "time"` with `"practice_s"` ≥ 90; **the
real match:** `minigame_taken` home / resume, `minigame_ended` with `class` and `scores`; **the paused proof** from each
watch row to its go; **END:** everything ended, `status` idle.

**The cells (nothing perceptual):** **F — no press before the go:** at all three load screens, `PAUSED` at every second
of the paused proof from the watch row to the go, and **no `minigame_reloaded`** at any go; **R — the start read:**
`recognised` true for each preparation (none given up); **S — the selection:** one card (the board's log), the
`minigame_start` with `TOKEN2`; **PS / PT — the practices:** `"by": "start_button"` then `"by": "time"` (`practice_s` ≥
90), no `minigame_ended` between a practice's go and its end; **M — the real match scored:** `minigame_ended` with an
end class and its scores; **H — Home / RESUME:** taken, the mini game still `playing` after, then ended as above;
**E — END:** everything ended; **U:** cell U's files before = after (the in-game saves recorded, not a cell).
**Recorded, no bar:** each `prepare_s`, `held_s`, `mute_ms`; the user's words at each "select" and the result line.
**MET** = part 1 (with the streamed self-proof) and F, R, S, PS, PT, M, H, E, U met → **PP-H4 may be offered.**

### PP-H4 with the screens — what changes in `handoffs/PP-H4_FOUR_PERSON_SITTING_TASK.md` (v2): B136's list, with

- **Preconditions (change 1):** **H7-V6 MET and PP-H3c MET** (both records committed); the board's repo as PP-H3c's
  preconditions — the screens in its tree (the five methods → 5), **`minigames/hub_minigame.gd` sha256 `e580c3e1…`,
  `checks/hub_minigame_check.gd` sha256 `76018a20…`** (B136's sketch said `697587b7…`: that was not the file —
  corrected), `grep -c "func first_here" game/minigame_picker.gd` → 1; this repo's B137 `grep`s as H7-V6's step 1.
  Part 1's proof (a): `checks/hub_minigame_check.gd` → **PASS (81)** and the PC side's step 25 check → PASS.
- **The "On ready" sentence about the small text — removed** (B136's), unchanged.
- **The first streamed proof before anyone plays:** B136's, with B137's rows — **`minigame_frame_advance` before
  `minigame_ready`, the paused proof `PAUSED` every second from the watch row to the go, no `minigame_reloaded` at the
  go** — and the `Capture:` line as B136's.
- **The lines (change 4):** B136's "On ready" line and three asks, unchanged but for the buttons named as PP-H3c names
  them (✕ = A "ready", ○ = B "not ready", △ = Y "practice first", Start), and **one sentence added to the "On ready"
  line: "At a load screen you can press ✕ the moment it shows — the game waits for the hub, and nothing you press
  reaches it before it starts."**
- **Cells added:** B136's Ch, RC, PS, PT — and **F (no press before the go)** as PP-H3c's, over every mini game of the
  sitting. **MET** = part 1 (with the streamed proof) and J, D, P, X, R, H, E, L, U, Ch, RC, PS, PT, **F** met.

## Files

B137: `companion/party_minigame.py`, `companion/h7_minigame.py`, `companion/native_session_io.py`,
`tests/b137_party_no_press/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the `nopress` / `nopress_head`
modes), `tests/b133_party_prepare_go/test_b133.py` (its two row lists), `evidence/B137_…` + `b137_2026-11-17/`
(`b137.diff`, the settle's scripts and results, the tests' runs, the checks, `manifest.sha256`), `patches/B137_…`. Then
`docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph inserted after queue AU's),
`logs/b137_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue AV's B137 / B138). The board's repo — nothing to commit.
