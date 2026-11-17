# SESSION B — done, 2026-11-17 AR (QUEUE_2026-11-17AR: B122 places, B123 T89's N64 start, B124 four seats, B125 A's next two tasks sketched; run 01:17Z-02:16Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (no system unit); `git status --short` empty
(H7-C1 committed in `cb16e0c8` with queue AR). `privyhub-diag` untouched; no stream, no companion or keeper restart, no
adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; **nothing of A's touched** — the kept
T89 pictures and labels read only (numbers out, nothing written beside them), the kept SAVEs not opened (their hashes
read from H7-C1's record), the rules folder not touched (the all-five spec learnt to a scratch folder, removed); no
emulator title started (the tests' titles are B101's fake RetroArch; RetroArch not run at all); **Godot headless only,
in scratch copies** of the board's repo; no picture in any record (I looked at four of T89's results pictures to see the
Place row; none copied). **The board's repo** (`f1adc44`): **only my two files edited**, nothing committed there. The
`/tmp/b_q29ar` copy holds companion/, tools/, tests/, PrivyHub/ (its sources). Nothing adopted; nothing committed in
either repo. Deleted: only my own scratch under `~/.cache/b_q29ar_tmp`.

## What was found and built

- **B122 — BUILT** (`evidence/B122_H7_PLACES_2026-11-17.md`): spec version 3 — a place for every player from labels
  alone (one screen per class; the Place row's spacing and cells found from the place labels by between- / within-place
  variance; one reference per place pooled over the columns, so a place a column never showed is read there at its
  learnt position). **T89, five folds (each match held out):** M1 34 / 34 rows, every place right; M2 5 / 5; M3 39 / 39;
  M4 32 / 32; M5 29 / 29 — **0 places wrong, 0 unread, 0 fights read as the screen**, eight never-seen-in-column places
  right. All five → the spec A will use: 139 / 139 results, 369 / 369 start, 246 / 246 other. Replay K = 3: five ends,
  the right rows, 2 s after each Place row (M5 1 s); K = 2: 1 s. Tone: 1 of 19,604 readings changed (right → `unknown`,
  the darkest gamma + offset pair). T88 identical. Four design amendments, each hashed before the recorded run.
- **B123 — BUILT** (`evidence/B123_H7_N64_START_2026-11-17.md`): `h7-start` loads N64 begin states (the session's core
  folder `Mupen64Plus-Next/`, `<stem>.state8`, **only into a core answering PAUSED**, else a plain refusal with nothing
  sent); the watch ends on the whole row and carries `places`; the places sidecar `{"players": n, "places_to_scores"}`
  (default n..1), the scores in the seats' order.
- **B124 — BUILT** (`evidence/B124_PARTY_FOUR_SEATS_2026-11-17.md`): the board's start answers 4 players / 4 ports
  (also during a mini game); `PRIVYPARTY_ON_HUB=1` in its launch environment; four seats routed, unfit seats refused;
  my board script `MAX_PLAYERS` 4 — two players → two-player titles, four → four-player ones, three → a draw; check
  PASS 40. **The board's rules** call the mini game with every player at a round's end and with the two at a duel;
  **its picker** would still pick its button-mash every other time — **the PC side's one line** in
  `game/minigame_picker.gd` (`play()`, right after `var id := next_id(players.size())`):

  ```gdscript
  	if OS.get_environment("PRIVYPARTY_ON_HUB") == "1" and Registry.minigames().has("hub") and players.size() in [2, 4]:
  		id = "hub"  # on the hub: a duel plays its two-player game, a round's end its four-player one
  ```

Tests: B122 12, B123 6, B124 6, B114 8, B115 6, B110 13, B112 7, B111 2 — 3 runs each green (`b124_2026-11-17/
tests_x3.txt`); the neighbours once: B102 16, B104 19, B103 13, B105 12, B101 14, B99 15, B108 16, B65 7, B61 14, the player prompt 11, the players' session 19, the relaunch 19, the pad slots 5, the stall signal 12, the stall owner 10, the link recovery 16, the fast restart 13, the client contract 5, PS2 93, GameCube 54, N64 28 — all OK.

## What I would change (not done — the queue is the task)

1. **The capture's own size:** T89's window is 960 × 720 with black bands on two sides that the tool's bar cut (one axis,
   symmetric) leaves in; version 3 now drops them from the screens' masks, but cutting asymmetric bands in `game_area`
   would make both versions cleaner — a version-2 change, so not done here.
2. **A covered digit:** a character's pointer standing on a digit for the whole results screen gives a draw after 30 s.
   Most games let the players skip the results screen — the sitting's line asks them to wait on it; a reader of the KO
   row as a second view, or deducing the last place from three distinct read places, would remove the draw, but the queue
   says never guess, so not built.
3. **The darkest tone pair** turned one held-out picture's row to `unknown`; harmless with K reads (the next pictures
   read), but a slightly wider place margin from more training pictures (another match) would remove it.
4. **One capture would settle the two never-seen pairs directly:** a match with the Place row 2 1 4 3 (1P 2nd, 3P 4th).
   Not needed for the sitting by the folds; worth taking whenever four people play T89 again.
5. **The picker line is the PC side's,** and until it is in, the hub's game comes up every other time: PP-H4 takes
   longer, but still works.

## A — H7-V5 then PP-H4 (B125)

T88 = H7's 2-player PS1 title; **T89** = the users' N64 four-player title. No title, character name, game id, serial
or path in any record; no picture in git. `H=http://127.0.0.1:8765/plugins/games`; `$RULES` = the rules folder;
`<T89 id>` / `<T88 id>` read from the hub at stage 1 (never written into a record).

### H7-V5 — T89 proved with nobody at the TV (unattended, ~20 min; PRIVYHUB_H7=1 only)

**Stage 1 (pre-registered after it):**

1. This repo's HEAD **with queue AR committed** and clean but for this task's files (else stop: "YOU, now: commit queue
   AR first, then send the read line again"); only the two units; no game; **eighteen** lines, `--check` ok; outside
   04:30-05:30Z and not within 30 min before it.
2. **The spec, from Cowork's labels:** `python3 tools/h7_endscreen.py learn runtime/h7_frames
   runtime/h7_frames/t89_c1_20261117T003035Z/labels.json "$RULES/<T89 id>.endscreen.json"` → the report: `"version": 3`
   in the spec, `usable` true, the row spacing 40, offsets (57, 129) (57, 169) (57, 209) (57, 249), the screens' and the
   places' thresholds — **expected equal to B122's all-five numbers** (the learner is deterministic).
3. **Read back:** `python3 tools/h7_endscreen.py score runtime/h7_frames runtime/h7_frames/t89_c1_20261117T003035Z/
   labels.json "$RULES/<T89 id>.endscreen.json"` → `places_wrong` 0, `other_read_as_screen` 0, every row right;
   `python3 tools/h7_endscreen.py replay runtime/h7_frames/t89_c1_20261117T003035Z "$RULES/<T89 id>.endscreen.json"` →
   **exactly five `ended` lines**, places [1, 2, 3, 4], [4, 1, 2, 3], [3, 4, 1, 2], [3, 4, 2, 1], [1, 3, 2, 4], each
   within 2 s of its Place row — **the mid-match pictures never ended**.
4. **The kept begin state:** `cp ~/privyhub_h7/t89/begin.state "$RULES/<T89 id>.state"` (sha256 `bc8ff296…` before and
   after the copy).
5. **T88 still right:** `python3 tools/h7_endscreen.py score runtime/h7_frames/t88 runtime/h7_frames/t88/labels.json
   runtime/h7_frames runtime/h7_frames/h7v2_20261116_run/labels.json "$RULES/<T88 id>.endscreen.json"` → H7-V3's /
   B104's numbers (H7-V1 72 / 72, 74 / 74, 788 / 788, 218 / 218; the live run 113 / 117, 98 / 103, 70 / 73, 214 / 214;
   0 read as the screen).
6. **The bench flag for the task only:** B99's `.conf` (`PRIVYHUB_H7=1`) → the companion's drop-in folder;
   `systemctl --user daemon-reload`; `systemctl --user restart privyhub-companion`; MainPID owns 8765; **nineteen** lines.
7. **Before:** the saves listing (count and every hash — T89's slots in `Mupen64Plus-Next/` among them); no `.state8`;
   `logs/games/h7_results.jsonl` line count.
8. **Pre-registration hashed.**

**Stage 2 — the run:**

9. **T89 by the hub alone:** `curl -s -m 120 -X POST "$H/launch?id=<T89 id>"` → `active`, `paused` (an N64 session,
   four ports).
10. **The start with the kept begin:** `curl -s -X POST "$H/h7-start?bench=1"` → `"watch": "started"`, `"loaded": true`,
    `load_line_ms` a number (the row `loaded`); **at once** `curl -s -X POST "$H/bench-release"` → `"released": true`
    (a paused N64 core shows the loaded picture at its first frame after the release); poll `curl -s "$H/h7-result"` once
    a second → **`recognised` true within 8 s** (the four-player select screen), `seen_start` true.
11. **The kept results screen by hand** (an N64 core takes a state only while paused): the command port from the launch
    row (`network_cmd_port`); `python3 -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);
    s.settimeout(2);[s.sendto(c.encode(),('127.0.0.1',<port>)) for c in ['PAUSE_TOGGLE']];s.sendto(b'GET_STATUS',
    ('127.0.0.1',<port>));print(s.recv(256).decode())"` → `GET_STATUS PAUSED …`; `cp ~/privyhub_h7/t89/results_1.state
    "<the states root>/Mupen64Plus-Next/<stem>.state8"`; `LOAD_STATE_SLOT 8` the same way → the reply and RetroArch's
    load line in its session log; remove the scratch; `PAUSE_TOGGLE` → `GET_STATUS PLAYING` → **`ended`, class `end`,
    places [1, 2, 3, 4] within 8 s** (the `ended` row with the places).
12. **The refusal on a running core:** `curl -s -X POST "$H/h7-start?bench=1"` while it plays → 400 "the N64 game is not
    paused: its state is loaded only into a paused core; nothing was sent" (no `LOAD_STATE_SLOT` in RetroArch's log).
13. **The end:** `curl -s -X POST "$H/h7-stop"`; `curl -s -X POST "$H/stop"` → RetroArch gone.
14. **After:** the saves listing before = after (every hash), no `.state8`.

**Pre-registered:** steps 2-5 and 9-14 as stated (the places exactly [1, 2, 3, 4]; five replay ends and no other).
**All met → MET → PP-H4 may be offered.** The close: the drop-in removed; daemon-reload; the companion restarted;
**eighteen** lines, `--check` ok; `h7-start` → 400 "Unknown Games plugin POST action: h7-start"; no RetroArch left.
The spec, the state and the sidecars stay in the rules folder (off the repo).

### PP-H4 — the four-person sitting with the board (only if H7-V5 is fully met; ~30 min at the TV)

**As PP-H3b** (its stage 1, its watchers — the route watcher with its own timings, the status watch with Godot's CPU,
the party log, the board's own log, the recovery log — its part 1 on the bench with two mini games back to back and the
concurrent calls, its close), with these changes:

- **Preconditions:** queue AR committed; **the board's repo with B124's two files committed** (sha256 `e246478b…`,
  `b016167d…`; else stop: "YOU, now: commit the board's two files first, then send the read line again"); **the PC
  side's picker line in `game/minigame_picker.gd`** (`grep -c PRIVYPARTY_ON_HUB game/minigame_picker.gd` = 1; if 0,
  say so in one line and go on — the hub's game then comes every other round, the sitting takes longer).
- **The rules folder:** T88's spec, state and two-player sidecar as PP-H3b; T89's version-3 spec and begin state from
  H7-V5; **T89's sidecar `<T89 id>.party.json` = `{"players": 4}`** (places 1-4 → 4, 3, 2, 1 coins-worth of score).
  Both drop-ins (`PRIVYHUB_H7=1`, `PRIVYHUB_PARTY=1`); **twenty** lines.
- **Part 1 adds:** `curl -s "$H/party-minigames"` → **two entries, `"players"` 2 and 4**; with the board launched and
  released, a four-player bench mini game: `curl -s -X POST "$H/party-minigame-start?id=<the 4-player token>&seats=1,2,3,4&bench=1"`
  → `playing`, `recognised` true; the kept results_1 by hand as H7-V5 step 11 (paused first) → **`ended`, places
  [1, 2, 3, 4], `"scores": [4, 3, 2, 1]`**; the end; seats 3,1,4,2 the same → **scores [4, 3, 2, 1] in that seat
  order**; refused: the 4-player token with `seats=1,2` and the 2-player one with `seats=1,2,3,4` (400 "this mini game
  takes … different seats, 1-4"); `native-stream-start?…&player_prompt=1` is not run on the bench (no stream): the four
  ports are read in the sitting.

**The lines** (every message "YOU, now:", a complete step, the onn's own words read at stage 1):

- **First:** "YOU, now: four of you, each with a pad paired to the onn. On the onn's PrivyHub home open Games, then
  'PrivyParty (1)', press OK on its one game, choose 'Launch on Companion' and press OK, then 'Start Fresh' and OK. When
  'Hold any button to join' shows, hold ✕ on the first pad until 'P1 joined' shows, then the second, third and fourth
  pad the same way, in that order. Then on the board's screen each of you hold ✕ until the board shows you as a player
  — four players. Tell me 'ready'."
- **On "ready":** "YOU, now: start a game in the board's lobby — ✕ on the first pad — and play. Two things change the
  TV: **a duel** — the two players in it go to [T88]'s character select (00 – 00): those two pick and play one match;
  **the end of a round** — all four go to [T89]'s four-player select screen: all four pick, choose a stage, and play the
  match (one life each) to its results screen; wait on the results screen until the board comes back by itself. The
  picture holds still for a few seconds each time the TV changes over; that is expected. After each one, tell me in one
  line: for a duel, who won and whom the board gave the win to; for a round's end, the Place row as the results screen
  showed it (1P 2P 3P 4P) and how the board paid the four of you."
- **After the first round's-end mini game:** "YOU, now: play on. In the next [T89] match, once, press Home on the first
  pad (the bar RESUME PLAYING · SAVE · LOAD · END appears), choose RESUME PLAYING and press OK; when 'Hold any button to
  join' shows again, hold ✕ on each of the four pads in turn until it clears, and finish the match. Tell me the Place
  row and the board's payout as before."
- **When one duel and two rounds' ends are done:** "YOU, now: play on until the TV changes to [T88] or [T89] once more.
  When its select screen shows, press Home on the first pad, move to END and press OK. Tell me 'ended'."
- **"stuck"** (the picture frozen more than ten seconds, the pads not driving the match, the board not coming back): A
  reads `party-minigame-result` and `status` (both within 2 s) and says in one plain sentence what the hub shows; **a mini
  game on** → `curl -s -m 5 -X POST "$H/party-minigame-end"` → "YOU, now: the board is back on the TV — that mini game
  counts as a draw. Play on, and tell me when the TV changes again."; **the results screen covered** (the hub reads the
  screen but not every place — a character's pointer on a number) → the same end, the same line; **no mini game on and
  the board not back** → "YOU, now: press Home on the first pad, move to END and press OK. Tell me 'ended'."; **no bar
  within ten seconds** → "YOU, now: leave the game from the onn's own top bar, then tell me 'left'." and the close. Every
  "stuck" recorded; that mini game "not met".
- **"close":** the END step if a game is running, then the close.

**Pre-registered, nothing perceptual (hashed before the first line):**

- **J — four seats:** the board's start answer `players` 4, `ports_set.players` 4 (the start's row); `pad_slots` 4
  joined; the board's log naming four players.
- **D — each duel:** `minigame_start` with **two seats** and the 2-player token; `minigame_ended` class and scores making
  **the user's winner** the winner; **the board's log crediting that seat** ("PrivyParty: hub mini game: scores [..] for
  seats a,b").
- **P — each round's end:** `minigame_start` with **four seats**; `minigame_ended` with **places = the user's Place row**
  and scores = (4, 3, 2, 1 by place) **in the seats' order**; **the board's log "scores [..] for seats a,b,c,d"** with
  the same numbers; the user's payout line agreeing with the board's own record of that mini game.
- **X — every hand-over planned** (both ways, every mini game): two `minigame_stream` rows `"switched": true,
  "planned": true`, a `minigame_switch_window` row each; between `minigame_start` and `minigame_end` no recovery act
  (`client_stall`, `desync_pause`, `stall_handover_v2`, `encoder_restart`, `resumed`, `gave_up_saved`; Home / RESUME only
  `session_ended` / `session_started`), no board key row but END's own `quit`, no `escalation_armed` / `transition`; the
  seconds each way recorded.
- **R — every route within 2 s throughout:** every `route_watch.tsv` line `ok` 1 and `seconds` < 2.0.
- **H — Home / RESUME once in a [T89] match:** `minigame_taken` home → `paused` true (the title's), `minigame_taken`
  resume_start / resume_ready → `paused` false, the RESUME's start answering 4 / 4; the match then ends with its places.
- **E — END during a hub mini game:** `minigame_given_up` "ended from the onn", `minigame_taken` end,
  `minigame_title_stopped`, `minigame_end` "onn", the board's `quit` and `exited` **code 0**; RetroArch gone; `status` →
  not active; no board, Godot or RetroArch process left.
- **C — recorded, no bar:** Godot's CPU behind each title (median while `minigame_playing`); the seconds each way;
  frames a second, loss, the bitrate's level.
- **U — nothing of the users' touched:** the saves before = after (every hash), no `.state8`; the pictures unchanged;
  the board repo's status after = before.
- **MET** = part 1 met and J, D (every duel), P (every round's end), X, R, H, E, U met.

**The close:** as PP-H3b's (both drop-ins removed, daemon-reload, the companion restarted with no SIGKILL, **eighteen**
lines, the routes gone, nothing left running). The record `evidence/PP_H4_<date>.md` + `pph4_<date>/` in PP-H3b's
shape with `part2/places.md` (each round's end: the user's row, the hub's, the board's). The last reply begins "YOU,
now: commit".

## Files

B122: `tools/h7_endscreen.py`, `tests/b122_h7_places/`, `evidence/B122_…` + `b122_2026-11-17/`,
`patches/B122_H7_PLACES.md`. B123: `companion/h7_minigame.py`, `companion/h7_contest.py`, `companion/party_minigame.py`,
`tests/b123_h7_n64_start/`, `tests/b103_h7_minigame/test_b103.py` (one line), `evidence/B123_…` + `b123_2026-11-17/`,
`patches/B123_H7_N64_START.md`. B124: `companion/players_session.py`, `companion/player_count.py`,
`companion/party_session.py`, `tests/b124_party_four_seats/`, `tests/b114_party_minigame_hang/` (the harness's `four`
mode, the flag test's ports), `tests/b111_party_board/test_b111.py`, the board's two files (uncommitted there),
`evidence/B124_…` + `b124_2026-11-17/`, `patches/B124_PARTY_FOUR_SEATS.md`. Then `docs/KNOWN_ISSUES.md` (one line
inserted), `docs/ROADMAP.md` (one paragraph inserted after H7-C1's), `logs/b122_|b123_|b124_git_status.txt`,
`handoffs/SESSION_B_STATUS.txt`, this file.

**The user, now:** this repo — commit the tree (queue AR's B122-B125); the board's repo — `git add
minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m "Hub mini game: four players get the hub's
four-player games, two its two-player ones, with its check"`; the PC side — the one picker line above.
