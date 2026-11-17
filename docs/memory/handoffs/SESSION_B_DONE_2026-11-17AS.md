# SESSION B — done, 2026-11-17 AS (QUEUE_2026-11-17AS: B126 the readers on the unlocked screens, B127 the mini games under the cheat setups, B128 A's next two tasks re-sketched; run 03:05Z-03:58Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (no system unit); `git status --short` empty
(H7-C2 committed in `d9e95e66` with queue AS; the prompt files tracked and unchanged). `privyhub-diag` untouched; no
stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the
drive; **the users' cheat setups, their slots and in-game saves, the kept H7 folders and the rules folder read only** —
the setups and kept folders not opened (their names listed, their hashes from H7-C2's record), the rules folder's T88
spec read in place to score it (sha256 = H7-V3's), nothing copied into it; Cowork's pictures and labels read only,
nothing written beside them; no emulator title started (B101's fake RetroArch on made-up fixtures only); **Godot
headless only** (B111's check, in its own scratch copy of the board's repo); **the board's repo not touched** (status
before = after). No title, serial, game id, character name, cheat name or path in any record; I looked at two C2
pictures (none copied). The `/tmp/b_q30as` copy holds companion/, tools/, tests/, PrivyHub/ (its sources) only. Nothing
adopted; nothing committed in either repo. Deleted: only my own scratch (`~/.cache/b_q30as_tmp`, the mutation copies).

## What was found and built

- **B126 — DONE, the tool unchanged** (`evidence/B126_H7_UNLOCKED_SCREENS_2026-11-17.md`): **H7-V3's T88 spec as it
  stands already reads the unlocked start / end_P1 / end_P2** — on H7-C2's T88 run start 34 / 38 (the 4 others are
  pictures 4-7 under RetroArch's notices), end_P1 37 / 37, end_P2 37 / 37, fights 17 / 17, 0 wrong, 0 fights as the
  screen — but with less headroom (0.041 from its reference against 0.090; the locked screens 0.002-0.003).
  **Learnt from all three sources** (H7-V1, the live run, c2): screen 0.0820, start 0.0958, end_P1 0.1044, end_P2
  0.0983, margin 0.0921, masks 12,244 / 104 px — **per source: H7-V1 788 / 72 / 74 / 218 all right; the live run
  70 / 73, 113 / 117, 98 / 103, 214 / 214 (the 12 range-edge pictures); c2 34 / 38, 37 / 37, 37 / 37, 17 / 17; 0 wrong,
  0 fights as the screen anywhere**; the unlocked screens then at 0.0036. **Folds:** without c2 → c2 as above; without
  H7-V1 → H7-V1 all right; **without the live run → the live run NOT met: the start not separable (73 `unknown`) and
  one live fight read as the screen (class `unknown`, never an end)** — c2's four notice-covered pictures labelled
  `start`; with them `ignore` (in memory) it holds (70 / 113 / 98 / 214, 0 fights). Tone grid: H7-V3's spec on held-out
  c2 — 0 misread, 0 fights as the screen, but the two darkest pairs drop 112 of 129 screens to `other`; the
  three-source spec on c2 (not held out) — gamma 1.25 with −30 still drops 109; the first-halves arrangement cannot
  learn the start (the live run's range-edge pictures 285-287). **T89: B122's spec already reads the unlocked start
  38 / 38, the locked start 17 / 17, the results 38 / 38; learnt from c1 + c2: c1 all right (369, 246, 139 rows), c2
  all right; c1's five folds again M1 34, M2 5, M3 39, M4 32, M5 29 — 0 places wrong, 0 fights as the screen; tone 0
  changes.** **One spec per title** (no spec per setup). Replay: each end load `ended` 2 s after its end screen with
  the right side / places; c1 unchanged line for line; the live run's end_P2 1 s earlier (an `ignore` fade now read).
- **B127 — BUILT** (`evidence/B127_PARTY_CHEAT_SETUPS_2026-11-17.md`): settled — today the mini game's title is
  launched with no cheat arguments; the onn's Extras launch is the launch route with `cheat_source` / `cheat_indexes`
  (B85's expansion gives a saved setup's indexes back → the same `profile_id`); under a setup `h7-start`'s load already
  lands in the setup's own `states/<core>/`; `launch_orphaned` never touches a mini game's launch; stop flushes the
  in-game save into the setup; **the onn's SAVE / LOAD during a mini game are not taken and use the setup's slots**
  (reported). Built: the sidecar's `cheat`; the setup's begin `<game id>.<profile_id's first 12>.state`; the setup
  checked on the hub before anything (else 400 "the cheat setup this mini game names is not on the hub (or its cheats
  changed): nothing was launched"); the title launched through the plugin's own launch path with the onn's Extras
  query; the session's `profile_id` checked; `h7-start` under a setup loads the setup's begin (`"begin": "setup"`).
  Tests 9 (B127 x3 green after one test fix — the first three runs had two timing failures in the no-`cheat` compare,
  disclosed), mutations 4 / 4; flags absent and a sidecar without `cheat` → HEAD's answers; the other suites green.

Tests: **B127 9 — 3 runs green after the test fix** (`b127_2026-11-17/tests_x3_after_fix.txt`; the first three runs: two timing failures in the no-`cheat` compare, then fixed and disclosed); mutations 4 / 4; the others once (`tests_x3.txt`): B124 6, B114 8, B115 6, B110 13, B112 7, B123 6, B122 12, B111 2, B102 16, B104 19, B103 13, B105 12, B101 14, B99 15, B108 16, art_systems 120 (one doc test reads `docs/CHEATS.md`, outside the work copy — OK against the repo), B65 7, B61 14, the player prompt 11, the players' session 19, the relaunch 19, the pad slots 5, the stall signal 12, the stall owner 10, the link recovery 16, the fast restart 13, the client contract 5, PS2 93, GameCube 54, N64 28 — all OK; nothing left running.

**One risk for H7-V5 / PP-H4, stated:** on c2 the first start read came **6.97 s** after the load (RetroArch's notices — the cheat applied, the pads — cover the screen for ~6 s); the hub's `recognised` allows 8 s. In the mini game the launch's notices are a few seconds older by the time `h7-start` loads, so it should pass, but if H7-V5 step 12 or 16 shows `recognised` false ("the title's start screen was not recognised"), that is the cause; B's fix would be a longer `RECOGNISE_S` under a setup.

## What I would change (not done — the queue is the task)

1. **SAVE / LOAD during a mini game:** the onn's bar still offers SAVE and LOAD while a hub mini game is on; they are
   not taken by the mini game and act on the running title — under a cheat setup **a SAVE writes one of the users'
   setup slots and rewrites the setup's slot 0** (the users' cheat slot 1 lives there), a LOAD replaces the mini
   game's picture with a users' slot. I would take both during a mini game (refuse with a plain line, or hide them for
   the board and its mini games — already on the "smoother feel" list).
2. **The in-game save under a setup:** every mini game's stop flushes the title's in-game save into the users' setup
   (records, unlocks a match writes). I would run the mini game against a copy of the setup's `saves/` (a per-mini-game
   scratch `savefile_directory`) so a party night leaves the users' setup exactly as it was — a manager change, so
   not done.
3. **Cowork's c2 T88 labels:** pictures 4-7 (RetroArch's notices still on the screen) as `ignore` — the labels' own
   definition; every fold then holds. A one-line relabel, Cowork's.
4. **The learner's own-worst rule:** a labelled screen picture that does not read as the screen (the live run's
   range-edge pictures, c2's notice pictures) should not count towards its class's own worst — it closed the start's
   gap in two arrangements. A version-2 learner change (spec numbers would move), so not done.
5. **The darkest tone pair** drops the 1920 × 1080 unlocked screens to `other` (never a wrong read): only matters if
   the live window ever darkens that much; more unlocked pictures (a live sitting's `keep=1`) would widen it.
6. **The arrays file is not byte-reproducible** (one reference differs by ~2.6e-6 between two learns): H7-V5 checks
   the numbers, not the `.npz` hash; a fixed reduction order in the learner would make it exact.
7. **The listing does not check the setup** (it reads files only, no manager call): a title whose setup is gone is
   listed and refused at its start — the board then draws that mini game. Checking at the listing would hide it instead.

## A — H7-V5 then PP-H4, everything unlocked (B128)

T88 = H7's 2-player PS1 title (the duel); **T89** = the users' N64 four-player title (the round's end). "T88's cheat
setup" / "T89's cheat setup" = the users' Extras setups with slot 1 occupied (H7-C2's). No title, character name,
cheat name, game id, serial or path in any record; no picture in git. `H=http://127.0.0.1:8765/plugins/games`;
`$RULES` = the rules folder (`~/privyhub_h7/rules`); `<T88 id>` / `<T89 id>` and the setups' `profile_id`s read from
the hub at stage 1, never written into a record (`<T88 setup>` / `<T89 setup>`; `<P88>` / `<P89>` = their first 12
characters).

### H7-V5 — both titles proved with nobody at the TV, everything unlocked (unattended, ~30 min; B112's bench)

**Stage 1 (pre-registered after it):**

1. **Preconditions:** this repo's HEAD **with queue AS committed** and clean but for this task's files (else stop:
   "YOU, now: commit queue AS first, then send the read line again"); only the two units; no game; **eighteen** lines,
   `--check` ok; outside 04:30-05:30Z and not within 30 min before it.
2. **The setups, read as the onn reads them:** `curl -s -X POST "$H/cheat-profiles?id=<T88 id>"` → the profile whose
   `occupied_slots` holds 1 (T88 has a second setup with no slot — not used): its `profile_id`, `source_index`,
   `enabled_cheat_indexes`; the same for `<T89 id>` (one setup, two cheats, slot 1). The setups' slot 1 files — the one
   `<stem>.state1` under each setup's `states/` (`find data/games/retroarch/cheat_profiles/<id>/<setup>/states -name
   '*.state1'`) — sha256 **`be4aa243…`** (T88) and **`78c53af3…`** (T89) (H7-C2's); else stop and say which.
3. **The specs (B126), the old ones renamed aside first, nothing deleted:** `mv "$RULES/<T88 id>.endscreen.json"
   "$RULES/<T88 id>.endscreen.h7v3.json"`; `mv "$RULES/<T88 id>.endscreen.npz" "$RULES/<T88 id>.endscreen.h7v3.npz"`;
   then
   `python3 tools/h7_endscreen.py learn runtime/h7_frames/t88 runtime/h7_frames/t88/labels.json runtime/h7_frames
   runtime/h7_frames/h7v2_20261116_run/labels.json runtime/h7_frames runtime/h7_frames/t88_c2_20261117T024815Z/labels.json
   "$RULES/<T88 id>.endscreen.json"` → the spec: **`"version": 2`, `usable` true, `screen_threshold` 0.082,
   `class_thresholds` start 0.0958 / end_P1 0.1044 / end_P2 0.0983, `margin_needed` 0.0921, `screen_mask_px` 12244,
   `outcome_mask_px` 104**; and
   `python3 tools/h7_endscreen.py learn runtime/h7_frames runtime/h7_frames/t89_c1_20261117T003035Z/labels.json
   runtime/h7_frames runtime/h7_frames/t89_c2_20261117T024815Z/labels.json "$RULES/<T89 id>.endscreen.json"` →
   **`"version": 3`, `usable` true, screens start 0.0932 / end 0.1011 (masks 8826 / 5785), the row spacing 40,
   offsets (57, 129) (57, 169) (57, 209) (57, 249), places 0.2212 / 0.2218 / 0.1744 / 0.1915, `margin_needed`
   0.0796.** (The numbers are deterministic; the `.npz`'s bytes are not — compare the numbers, not its hash.)
4. **Read back:** `python3 tools/h7_endscreen.py score <the three T88 pairs as in 3> "$RULES/<T88 id>.endscreen.json"` →
   `right_per_source` source_1 start 788 / 788, end_P1 72 / 72, end_P2 74 / 74, other 218 / 218; source_2 70 / 73,
   113 / 117, 98 / 103, 214 / 214; source_3 34 / 38, 37 / 37, 37 / 37, 17 / 17; **`other_read_as_screen` 0**;
   `python3 tools/h7_endscreen.py score <the two T89 pairs as in 3> "$RULES/<T89 id>.endscreen.json"` → rows start
   424 / 424, other 246 / 246, end_r1234 72 / 72, end_r1324 29 / 29, end_r3412 39 / 39, end_r3421 32 / 32, end_r4123
   5 / 5, **`places_wrong` 0, `other_read_as_screen` 0**; `replay runtime/h7_frames/t88_c2_20261117T024815Z …` →
   exactly **one** `ended` end_P1 at 46.02 s; `replay runtime/h7_frames/h7v2_20261116_run …` → end_P1 153.03 s, end_P2
   419.02 s; `replay runtime/h7_frames/t89_c2_20261117T024815Z …` → one `ended`, places [1, 2, 3, 4] at 43.02 s;
   `replay runtime/h7_frames/t89_c1_20261117T003035Z …` → five, places [1, 2, 3, 4], [4, 1, 2, 3], [3, 4, 1, 2],
   [3, 4, 2, 1], [1, 3, 2, 4] (all in `docs/memory/evidence/b126_2026-11-17/h7v5_expected/`).
5. **The setups' begins, copied read only:** `cp "<T88's slot 1 file from 2>" "$RULES/<T88 id>.<P88>.state"` and
   `cp "<T89's slot 1 file>" "$RULES/<T89 id>.<P89>.state"` — sha256 before = after = `be4aa243…` / `78c53af3…`.
6. **The sidecars:** `mv "$RULES/<T88 id>.party.json" "$RULES/<T88 id>.party.normal.json"`; write `<T88 id>.party.json`
   = `{"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}, "cheat": {"source_index": <n>,
   "enabled_cheat_indexes": [<as read>], "profile_id": "<T88 setup>"}}` and `<T89 id>.party.json` = `{"players": 4,
   "cheat": {"source_index": <n>, "enabled_cheat_indexes": [<as read>], "profile_id": "<T89 setup>"}}`.
7. **The bench flags for the task only:** B99's `.conf` (`PRIVYHUB_H7=1`) and PP-H2's party drop-in
   (`PRIVYHUB_PARTY=1`) → the companion's drop-in folder; `systemctl --user daemon-reload`; `systemctl --user restart
   privyhub-companion`; MainPID owns 8765; **twenty** lines.
8. **Before:** every file under `data/games/retroarch/states/`, `data/games/retroarch/saves/` and
   `data/games/retroarch/cheat_profiles/` — the count and every sha256 (both setups' slots, pictures, in-game saves
   among them); no `.state8`; `logs/games/h7_results.jsonl` and `logs/games/party.jsonl` line counts.
9. **Pre-registration hashed.**

**Stage 2 — the run:**

10. **The board by itself:** `curl -s "$H/games?system=party"` → the board's id; `curl -s -m 120 -X POST
    "$H/launch?id=<the board's id>"` → `active`, `paused`; `curl -s -X POST "$H/bench-release"` → `"released": true`.
11. **The list:** `curl -s "$H/party-minigames"` → **two entries, `"players"` 2 and 4** (TOKEN2, TOKEN4).
12. **T88 under its setup, seats 1,2:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN2&seats=1,2&bench=1"` →
    `"starting"`; poll `curl -s "$H/party-minigame-result"` once a second → **`playing`, then `recognised` true within
    20 s of the start** (the unlocked select screen); `curl -s "$H/status"` → `cheat_session.profile_id` = `<T88
    setup>`; the party log's `minigame_launch` row **`"cheat": true, "profile_matches": true`**; `h7_results`'s
    `watching` row **`"begin": "setup"`, `"loaded": true`**; RetroArch's load line naming `.state8` under T88's setup's
    `states/`.
13. **The kept end P1 by hand, into the setup's folder:** the title's command port (`network_cmd_port` of its launch);
    `cp ~/privyhub_h7/t88/end_p1.state "<T88's setup>/states/<core folder>/<stem>.state8"`; `python3 -c "import socket;
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(2);s.sendto(b'LOAD_STATE_SLOT 8',('127.0.0.1',
    <port>));print(s.recv(256).decode())"` → `LOAD_STATE_SLOT 8`; the load line in RetroArch's session log; remove the
    scratch → **`ended`, `end_P1`, `"scores": [1, 0]` within 8 s** (the unlocked tally screen); `curl -s -X POST
    "$H/party-minigame-end"` → `"ended": true`; RetroArch gone; `status` → `launch_kind` godot.
14. **Seats 2,1 with the kept end P2** (12 and 13 again, `seats=2,1`, `end_p2.state`) → **`end_P2`, `"scores": [0, 1]`**;
    the end.
15. **The mid-fight state never ends:** 12 again (`seats=1,2`); `~/privyhub_h7/t88/end_p1_b.state` (sha256
    `45dc8522…`, a fight) by hand as 13 → **still `playing` 45 s later, no `ended`**; the end → `given_up` "ended
    before a result (board)".
16. **T89 under its setup, seats 1,2,3,4:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN4&seats=1,2,3,4&bench=1"`
    → `playing`, **`recognised` true within 20 s** (the unlocked four-player select screen); `cheat_session.profile_id`
    = `<T89 setup>`; `minigame_launch` `"cheat": true, "profile_matches": true`; `watching` `"begin": "setup"`.
17. **The kept results by hand, paused** (an N64 core takes a state only while paused): `PAUSE_TOGGLE` then
    `GET_STATUS` → `GET_STATUS PAUSED …`; `cp ~/privyhub_h7/t89/results_1.state "<T89's setup>/states/Mupen64Plus-Next/
    <stem>.state8"`; `LOAD_STATE_SLOT 8` → the reply and the load line; remove the scratch; `PAUSE_TOGGLE` →
    `GET_STATUS PLAYING` → **`ended`, class `end`, `"places": [1, 2, 3, 4]`, `"scores": [4, 3, 2, 1]` within 8 s**;
    the end.
18. **Seats 3,1,4,2 with the same results** → **`"places": [1, 2, 3, 4]`, `"scores": [4, 3, 2, 1]`, `"seats": [3, 1, 4,
    2]`** (port 1 = seat 3 won: the scores in the seats' order); the end.
19. **The close of the board:** `curl -s -X POST "$H/stop"` → the board quits by F10, exit code 0; no board, Godot or
    RetroArch process left.
20. **After:** every file of 8 before = after (every sha256 — the setups' slots, pictures and **in-game saves**: no
    match is played, the loads only; if an in-game save differs, record which and say so — the stop's flush, settled
    item 5 of B127); no `.state8` anywhere.

**Pre-registered:** 3-6 and 10-20 as stated. **All met → MET → PP-H4 may be offered.** The close: both drop-ins removed;
daemon-reload; the companion restarted (no SIGKILL); **eighteen** lines, `--check` ok; `party-minigames` → 400
"Unknown Games plugin action: party-minigames"; `bench-release` → 400 "Unknown Games plugin POST action: bench-release";
nothing left running. The specs, the setups' begins and the sidecars stay in the rules folder (off the repo); the
renamed-aside files beside them.

### PP-H4 — the four-person sitting, everything unlocked (only if H7-V5 is fully met; ~30 min at the TV)

**As B125's PP-H4** (`SESSION_B_DONE_2026-11-17AR.md` §PP-H4 — PP-H3b's stage 1, watchers, part 1 and close; cells J,
D, P, X, R, H, E, C, U) **with these changes:**

- **Preconditions:** queue AS committed; **the board's repo with B124's two files committed** (sha256 `e246478b…`,
  `b016167d…`; else stop: "YOU, now: commit the board's two files first, then send the read line again"); **the PC
  side's picker line there:** `grep -c PRIVYPARTY_ON_HUB <board repo>/game/minigame_picker.gd` → **1** (else stop:
  "YOU, now: add the PC side's one line in `game/minigame_picker.gd` (in SESSION_B_DONE_2026-11-17AR) and commit it,
  then send the read line again").
- **The rules folder as H7-V5 left it:** both specs (B126's), both setups' begins, both sidecars with `cheat`; stage 1
  re-reads each setup through `cheat-profiles` (the same `profile_id`, source and indexes as the sidecar; slot 1's
  sha256 as H7-V5's); both drop-ins; **twenty** lines.
- **Part 1 adds** (on the bench, before the sitting): with the board launched and released, `party-minigames` → two
  entries (2 and 4); one T88 bench mini game (seats 1,2, the kept end P1 by hand into T88's setup's folder → `end_P1`
  [1, 0]) and one T89 (seats 3,1,4,2, `results_1` by hand into T89's setup's folder, paused → places [1, 2, 3, 4],
  scores [4, 3, 2, 1]) back to back with the concurrent calls, each `minigame_launch` `"cheat": true,
  "profile_matches": true`, each `watching` `"begin": "setup"`.
- **The lines** (every message "YOU, now:", a complete step, the onn's own words read at stage 1):
  - **First:** "YOU, now: four of you, each with a pad paired to the onn. On the onn's PrivyHub home open Games, then
    'PrivyParty (1)', press OK on its one game, choose 'Launch on Companion' and press OK, then 'Start Fresh' and OK.
    When 'Hold any button to join' shows, hold ✕ on the first pad until 'P1 joined' shows, then the second, third and
    fourth pad the same way, in that order. Then on the board's screen each of you hold ✕ until the board shows you as
    a player — four players. Tell me 'ready'."
  - **On "ready":** "YOU, now: start a game in the board's lobby — ✕ on the first pad — and play. Two things change
    the TV, and in both **every character is there to pick** — nothing locked: **a duel** — the two players in it go
    to [T88]'s character select (00 – 00): those two pick anyone and play one match; **the end of a round** — all four
    go to [T89]'s four-player select screen: all four pick anyone, choose a stage, and play the match (one life each) to
    its results screen; wait on the results screen until the board comes back by itself. **While [T88] or [T89] is on,
    don't choose SAVE or LOAD on the onn's bar.** The picture holds still for a few seconds each time the TV changes
    over; that is expected. After each one, tell me in one line: for a duel, who won and whom the board gave the win
    to; for a round's end, the Place row as the results screen showed it (1P 2P 3P 4P) and how the board paid the four
    of you; and if any character showed as locked, say so."
  - **After the first round's-end mini game, the "stuck", the END and the "close" lines:** B125's, unchanged.
- **Pre-registered, added to B125's cells (nothing perceptual):**
  - **L — each mini game under its setup:** every `minigame_launch` row `"cheat": true, "profile_matches": true`; every
    `watching` row `"begin": "setup"`; `status`'s `cheat_session.profile_id` the title's setup while it plays.
  - **U changed:** the setups' **slots and pictures before = after** (every sha256 — nobody chooses SAVE / LOAD in a
    mini game); **the setups' in-game saves recorded before and after, not a cell** — the players' matches may write
    the titles' own records into them, and each mini game's stop flushes them (B127, settled item 5); the normal
    states and every other save before = after; no `.state8`.
  - **The user's lock line:** any "locked" in a line → recorded with the mini game; that mini game's L still read from
    the rows.
  - **MET** = part 1 met and J, D, P, X, R, H, E, L, U met.

The close as B125's (both drop-ins removed, daemon-reload, the companion restarted with no SIGKILL, **eighteen** lines,
the routes gone, nothing left running). The record `evidence/PP_H4_<date>.md` + `pph4_<date>/` with `part2/places.md`.
The last reply begins "YOU, now: commit".


## Files

B126: `evidence/B126_H7_UNLOCKED_SCREENS_2026-11-17.md` + `b126_2026-11-17/` (the design + two amendments,
`scripts/b126_eval.py`, the results, `h7v5_expected/` — the CLI's learn / score / replay answers for H7-V5). B127:
`companion/party_minigame.py`, `companion/h7_minigame.py`, `tests/b127_party_cheat_setups/test_b127.py` (new),
`tests/b114_party_minigame_hang/b114_scenario.py` (the `cheat` and `cheat_today` modes), `evidence/B127_…` +
`b127_2026-11-17/` (`b127.diff`), `patches/B127_PARTY_CHEAT_SETUPS.md`. Then `docs/KNOWN_ISSUES.md` (one line
inserted), `docs/ROADMAP.md` (one paragraph inserted after queue AR's), `logs/b126_|b127_git_status.txt`,
`handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue AS's B126-B128). The board's repo: nothing new from me (B124's
two files as before, if not yet committed). Cowork: optionally, c2 T88 pictures 4-7 → `ignore`.
