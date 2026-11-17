# SESSION B — done, 2026-11-17 AU (QUEUE_2026-11-17AU: B133 the title prepared behind the board, B134 the names and practice, B135 the board's script, B136 A's tasks re-sketched; run ~19:20Z-20:54Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (H7-V5b's record and
PP-H4's task in `5d78a57b` / `b07c00f7`, queue AU in `73284310`); **the board's repo clean at `d321b2d`** = the PC side's
`aa58ec6c…` plus one Cowork commit adding only the PC note and prompt at its root. No stream, no companion or keeper
restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; the users' setups, slots,
in-game saves, the kept H7 folders, the rules folder and `runtime/h7_frames/` not opened; **no emulator title started**
— disclosed: B61's form (the hub's RetroArch and N64 core on B61's synthetic ROM, temp folders, no pad) for ~60 s, and
two made-up Tk windows on the hub's display for ~10 s; **Godot headless only**, in a scratch copy of the board's tree.
**The board's repo: only `minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` changed** (uncommitted); the
presenter, the picker and the rules not touched. No title, serial, game id, `profile_id`, character name, cheat name or
path in any record; **no game's name** anywhere but at run time (the tests and the check use made-up names); no picture
in git. The `/tmp/b_q32au` copy holds companion/, tools/, tests/, PrivyHub/ (its sources) only. Nothing adopted;
nothing committed in either repo. Deleted: only my own scratch (`~/.cache/b_q32au_tmp`, the mutation copies).

## What was found and built

- **B133 — BUILT** (`evidence/B133_PARTY_PREPARE_AND_GO_2026-11-17.md`). **Settled first:** (1) **the onn keeps seeing
  the board while the title's window is above it** — the hub composites, and a made-up full-screen window grabbed by its
  id with the stream's own arguments stayed itself under a 960 × 720 and a full-screen made-up window, while the screen
  (what the watcher reads) showed the cover; (2) **RetroArch's notices run out while the core is paused** (~2.8 s, the
  same as running), but a paused core does not show a state loaded into it, and **with no route set the players' pads
  reach a running title too** — so the title runs behind the board only from the load until its start is read, then
  waits paused, and the go loads the begin again; (3) the bounds: the 30-s start limit now covers the preparation only,
  the play limit runs from the hand-over, the hold has none of its own. **Built:** `party-minigame-start?…&hold=1` →
  `preparing` → `ready` (no route, no switch) → `party-minigame-go` (remembered if early) → the begin again → route →
  planned switch → `playing`; never the start / a failed launch → given up with no switch and no route; the onn's Home /
  RESUME during the load screen give the mini game up, then act on the board; END ends everything; `prepare_s`,
  `held_s`, `handover_s` in rows. Tests 9.
- **B134 — BUILT** (`evidence/B134_PARTY_TITLES_AND_PRACTICE_2026-11-17.md`): the list's `"title"` (run-time only);
  **the hub sees any pad's Start press in the bridge's `_apply_report`, before the route** — a hook set only while a
  practice plays (the press also reaches the title); `party-minigame-go?practice=1` → playing, nothing read or scored;
  Start or 90 s → the way back, the title made ready again, `"practices": n`; then a real go scored as today. Tests 5.
- **B135 — BUILT** (`evidence/B135_BOARD_CHOOSE_LOAD_READY_2026-11-17.md`): my two board files — one or two seeded
  cards (Random with two), the load screen while the hub prepares, readiness on it, the go only with the players decided
  and the hub ready (no time limit), practices any number of times, the pads and the frame rate taken only while the
  hub's game is on, `LIMIT_SECONDS` only while playing; a stage without the screens plays as before. **The check PASS
  81 (was 40), three runs; the PC side's step8 PASS 210**; mutations 2 / 2.

Tests (`b134_2026-11-17/tests_x3.txt`): **B133 9, B134 5 — 3 runs green each, 0 temp dirs**; mutations B133 1 (HEAD's code: the held cases cannot run), B134 1 (no Start hook: two fail), B135 2 / 2; the board's check PASS 81 three runs and the PC side's step8 PASS 210 (`b135_2026-11-17/check_runs.txt`); the others once: B129 5, B130 4, B131 5, B127 9, B124 6, B114 8 (with the scenario's new modes), B115 6, B110 13, B112 7, B123 6, B122 12, B111 2 (**updated for B135's check** — its fake hub's held answers, the counts 81 / 56 — after one failing run on the old counts), B102 16, B104 19, B103 13, B105 12, B101 14, B99 15, B108 16, art_systems 120 (the one doc test reads `docs/CHEATS.md`, outside the work copy — OK against the repo), B65 7, B61 14, the player prompt 11, the players' session 19, the relaunch 19, the pad slots 5, the stall signal 12, the stall owner 10, the link recovery 16, the fast restart 13, the client contract 5, PS2 93, GameCube 54, N64 28 — all OK; nothing left running.

## What I would change (not done — the queue is the task)

1. **The players' presses during the preparation** reach the title for the seconds it runs behind the board (T88
   ~9-10 s from the launch, T89 ~2 s): harmless — the title is paused at once and its begin loaded again at the go —
   but a frame advance (RetroArch's `FRAMEADVANCE`) after a paused load would let the watcher read the begin without the
   title ever running; not tried here (no title may be started).
2. **The onn's Home during the load screen** gives the mini game up (a draw) before acting on the board; keeping the
   mini game held while the board pauses would need the manager to act on the set-aside board — a bigger change.
3. **The Start press that leaves a practice also reaches the title** (it pauses the game inside, then the hub pauses
   and reloads it); swallowing it would need a per-report filter in the bridge.
4. **`announce_minigame`** still says the board's own title for the hub's mini game ("On the hub") before the choice;
   the PC side could announce the chosen game instead (its picker and presenter).
5. **The bench cannot press Start:** H7-V6 proves practices by time; the Start way is proved by the tests and the
   sitting.
6. **A second start during the preparation** is refused with "the board game is not the running session" (the board
   is set aside), not "a mini game is already on" — plain enough, but the wording could say the latter.

## A — H7-V6 then PP-H4 with the screens (B136)

T88 = H7's 2-player PS1 title (the duel); **T89** = the users' N64 four-player title (the round's end); "T88's cheat
setup" / "T89's cheat setup"; `H=http://127.0.0.1:8765/plugins/games`; `$RULES` = `~/privyhub_h7/rules`; `<T88 id>`,
`<T89 id>`, the setups' ids, `TOKEN2` / `TOKEN4` read at run time, never in a record. **A game's name is run-time data
only: no record, row copy or log excerpt carries it** — the record says of each `"title"` only that it is there and not
empty.

### H7-V6 — the new order, unattended (B112's bench, ~25 min; `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1` for the task only)

**Stage 1 (pre-registered after it):**

1. The window as before (outside 04:30-05:30Z, not within 45 min before it). **This repo with queue AU's B133 / B134
   committed** and clean but for this task's files (else stop: "YOU, now: commit queue AU first, then send the read line
   again"); the code is AU's: `grep -c "def go(self, practice_text" companion/party_minigame.py` → 1, `grep -c
   "_party_buttons = None" companion/native_session_io.py` → 1, `grep -c 'action == "party-minigame-go"'
   companion/plugins/games.py` → 1 (else stop and say which). Only the two units; no game; eighteen lines, `--check` ok.
2. **The rules folder as H7-V5b left it**, checked read only as B132's steps 3-6 (both specs' numbers, both begins'
   sha256 `be4aa243…` / `78c53af3…`, both sidecars' `cheat` = `cheat-profiles`); nothing written there.
3. Both drop-ins; **twenty** lines. **Before:** every file under the states, saves and cheat setups (count, every
   sha256); no `.state8`; `party.jsonl` and `h7_results.jsonl` line counts. Pre-registration hashed.

**Stage 2 — by `curl` as the board would** (T88 then T89 in one companion):

4. **The board:** launched and released (B128 step 10). **The list:** `curl -s "$H/party-minigames" | python3 -c "import
   json,sys;print(sorted((e['players'], bool(e.get('title'))) for e in json.load(sys.stdin)['minigames']))"` →
   **`[(2, True), (4, True)]`** (the record keeps this line only, never the answer itself).
5. **T88 held, the board asking:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN2&seats=1,2&bench=1&hold=1"` →
   `"starting"`; poll `curl -s "$H/party-minigame-result"` once a second → `"phase": "preparing"` → **`"phase":
   "ready"` within 20 s (expected ~12 s)**; `party.jsonl`: `minigame_start` `"hold": true`, `minigame_launch` `"cheat":
   true, "profile_matches": true`, `minigame_watch`, **`minigame_ready` `"prepare_s"` (~12)** — **no `minigame_route`,
   no `minigame_stream` before the go**; `h7_results` `watching` `"recognise_s": 15.0, "begin": "setup"`, `recognised`
   true. **Then held 180 s, the result asked once a second:** `for i in $(seq 180); do curl -s
   "$H/party-minigame-result"; sleep 1; done` → every answer `"starting"`, `"ready"`. **The go:** `curl -s -X POST
   "$H/party-minigame-go"` → `{"ok": true, "go": "taken", "phase": "ready", "practice": false}` → `"playing"`; rows
   `minigame_go` `"held_s"` ≥ 180, `"remembered": false`; `minigame_reloaded`; `minigame_route`; `minigame_stream`
   `"switched": false` ("the stream is not up": the bench); `minigame_playing` `"handover_s"`. **The kept end P1 by
   hand** (B128 step 13) → **`ended` `end_P1` `[1, 0]`**; `party-minigame-end`.
6. **A go before ready, a second go:** start held, `seats=2,1`; **at once** `curl -s -X POST "$H/party-minigame-go"` →
   `"go": "remembered"`, `"phase": "preparing"`; again → `"go": "already"`; → `"playing"` by itself once ready
   (`minigame_go` `"remembered": true`); the kept end P2 → **`end_P2` `[0, 1]`**; the end.
7. **A start whose screen is never the start (nothing of the users' touched):** start held, `seats=1,2`; as soon as
   the `minigame_watch` row is written (`"phase": "preparing"`; T88's start comes only at ~9-10 s), **the kept
   mid-fight state** `~/privyhub_h7/t88/end_p1_b.state` (`45dc8522…`) by hand into scratch slot 8 of T88's setup's
   folder (B128 step 13's commands; the scratch removed at once) → the window shows a fight → **`given_up` "the mini
   game did not start: the title's start screen was not recognised" ~15 s after the load**; **no `minigame_route`, no
   `minigame_stream` row**; RetroArch gone; `status` → `launch_kind` godot.
8. **Practices, T88:** start held `seats=1,2` → `ready`; `curl -s -X POST "$H/party-minigame-go?practice=1"` →
   `"practice": true` → `"playing"` with **`"practice": true`** and `"practice_s"`; **the kept end P1 by hand during it
   → still `"playing"`, practice, no `class`, no `scores`**; **the Start button cannot be pressed on the bench** (it is
   a pad's report from the onn; nothing on the bench sends one — the tests press it through the bridge; **the sitting
   proves it**), so **the practice time stands in: back to `"starting"` → `"ready"` with `"practices": 1` ~90 s after
   the practice began** (`minigame_practice_end` `"by": "time"`, `"practice_s"` ~90; `minigame_ready` `"after_practice":
   true`); **a second practice** the same → `"practices": 2`; then **a real go** → the kept end P1 → **`end_P1`
   `[1, 0]`** (the result's `"practices": 2`); the end.
9. **T89:** start held `seats=3,1,4,2` → **`ready` within 15 s (expected ~4-5 s)**, `prepare_s` in its row; one
   practice by time → `"practices": 1`; a real go → `results_1` by hand **while paused** (B128 step 17) → **places
   `[1, 2, 3, 4]`, scores `[4, 3, 2, 1]`, seats `[3, 1, 4, 2]`**; the end.
10. **The close of the board** (B128 step 19); **after:** every file of step 3 before = after (the setups' slots, slot
    pictures, every normal state and save — the cell); the in-game saves recorded (not a cell); no `.state8`.

**Pre-registered:** 4-10 as stated — **`prepare_s` per title (T88 ≤ 20 s, T89 ≤ 15 s), no route and no switch before
any go, still `ready` after 180 s, remembered, already, never-the-start given up with no route, practices back to
`ready` by time with no scores, the real ends as H7-V5b.** MET → PP-H4 may be offered. The close as B132's.

### PP-H4 with the screens — what changes in `handoffs/PP-H4_FOUR_PERSON_SITTING_TASK.md` (v2)

- **Preconditions (change 1):** **H7-V6 MET**; the board's repo at the PC side's commit with **the screens in its
  tree**: `grep -c -E "func (choose_minigame|show_minigame_loading|set_minigame_loading_ready|minigame_loading_choice|hide_minigame_loading)\("
  game/presenter.gd` → **5** (else stop: "YOU, now: the board's selection and load screens are not in the hub's copy
  yet — pull the PC side's commit, then send the read line again"); **my two files committed** —
  `minigames/hub_minigame.gd` sha256 **`e580c3e1…`**, `checks/hub_minigame_check.gd` **`697587b7…`** (replacing
  `d9e2e6ec…` / `b016167d…`); `grep -c "func first_here" game/minigame_picker.gd` → 1 as before. Part 1's proof (a):
  `checks/hub_minigame_check.gd` → **PASS (81 assertions)** and the PC side's own screen check → PASS.
- **The "On ready" sentence about the small text — removed** (the hub now reads the title behind the board's load
  screen; nobody sees it until it is ready).
- **A first streamed proof before anyone plays (new, after "ready" from the four, before the "On ready" line):** A says
  "YOU, now: everybody hands off the pads for about half a minute — the hub is checking itself; the TV will change to a
  game and come back. I'll tell you when." Then on loopback (no `bench`): `curl -s -X POST
  "$H/party-minigame-start?id=$TOKEN2&seats=1,2&hold=1"` → poll → `"preparing"` → **`"ready"`**, with **no
  `minigame_route` / `minigame_stream` row before the go** and **the stream's last `Capture:` line still the board's
  window** (`grep -a "Capture:" logs/games/native_video_alpha.log | tail -1` — its `window_id` unchanged since the
  board's start); `curl -s -X POST "$H/party-minigame-go"` → **`minigame_stream` `"switched": true, "planned": true`**
  → `"playing"`; at once `curl -s -X POST "$H/party-minigame-end"` → the board back (`minigame_stream` board
  `"switched": true`). Rows only; the players touch nothing. **Not met → "YOU, now: the hub could not get a game ready
  behind the board, so we stop here." , the END step, nobody plays.**
- **The lines (change 4) — the "On ready" line becomes:** "YOU, now: start a game in the board's lobby — ✕ on the
  first pad — and play. Before each hub mini game the board shows a choice of games — the player it names picks one, or
  Random, with their own pad. Then a load screen with the game's name: each player in the mini game readies up there,
  or anyone can ask for Practice; the game starts when every one of them is ready, however long that takes. A practice
  ends when anyone presses Start on their pad, or by itself after about a minute and a half, and brings you back to the
  load screen — practise as often as you like. A duel is [T88] for its two players; the end of a round is [T89] for all
  four, one life each, to its results screen — wait there until the board comes back by itself. Every character is
  there to pick. While [T88] or [T89] is on, don't choose SAVE or LOAD on the onn's bar. After each one, tell me in one
  line: for a duel, who won and whom the board gave the win to; for a round's end, the Place row (1P 2P 3P 4P) and how
  the board paid the four of you; and if any character showed as locked, say so." **Three asks during the sitting**
  (each once, at the next load screen): **the ready check** — "YOU, now: at the next load screen, [the second player in
  it] wait — don't ready up — until the others have, then count slowly to ten and ready up. Tell me 'started' when the
  game starts."; **a practice left by Start** — "YOU, now: at the next load screen, ask for Practice, play a little,
  then press Start on any pad. Tell me 'back' when the load screen is back."; **a practice left by time** — "YOU, now:
  at the next load screen, ask for Practice again and this time don't press Start — just wait until the load screen
  comes back by itself, about a minute and a half. Tell me 'back'." B125's Home / RESUME, END, "stuck" and "close" lines
  unchanged; "don't choose SAVE or LOAD" kept (B131 not adopted).
- **Cells added (nothing perceptual):** **Ch — the choice:** each mini game's `minigame_start` names the chosen game
  (its token) and the board's log the choice ("PrivyParty: hub mini game:" lines; the PC side's screen log as it keeps
  it); **RC — the ready check:** in the asked mini game no `minigame_go` row until the waiting player readied (the go's
  `"held_s"` ≥ the wait the user describes, the user's "started" after it); **PS — a practice left by Start:**
  `minigame_practice_end` `"by": "start_button"` then `minigame_ready` `"after_practice": true`, the user's "back";
  **PT — a practice left by time:** `"by": "time"`, `"practice_s"` ≥ 90; **no practice scored** (no `minigame_ended`
  between a practice's go and its end). **Recorded, no bar:** each mini game's `prepare_s` and `held_s`; and **one
  line in the user's words: what the TV showed while the hub prepared** (asked once: "YOU, now: in one line, what did
  the TV show while the game was being got ready?"). **MET** = part 1 (with the streamed proof) and J, D, P, X, R, H, E,
  L, U, **Ch, RC, PS, PT** met.


## Files

B133: `companion/party_minigame.py`, `companion/h7_minigame.py` (`reload`), `companion/plugins/games.py`,
`tests/b133_party_prepare_go/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the `hold` / `practice` modes,
`QUIET`, the `today` mode's go), `evidence/B133_…` + `b133_2026-11-17/` (`b133.diff`, the two probes and their results),
`patches/B133_…`. B134: `companion/native_session_io.py` (the hook), `tests/b134_party_practice/` (new),
`evidence/B134_…` + `b134_2026-11-17/` (`b134.diff`, `tests_x3.txt`), `patches/B134_…`. B135 (the board's repo,
uncommitted): `minigames/hub_minigame.gd`, `checks/hub_minigame_check.gd`; `evidence/B135_…` + `b135_2026-11-17/`
(`b135_board.diff`), `patches/B135_…`. Then `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph
inserted after queue AT's), `logs/b133_|b134_|b135_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue AU's B133-B136); **the board's repo** — `git add
minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m "Hub mini game: choose, load screen, ready or
practise, then play - the hub prepares behind the board, with its check"`.
