# SESSION B — done, 2026-11-17 AT (QUEUE_2026-11-17AT: B129 the watcher's window, B130 the recognition window under a setup, B131 SAVE / LOAD in a mini game, B132 A's H7-V5 re-sketched; run 06:05Z-06:51Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (no system unit); `git status --short` empty
(H7-V5's record in `6c7f5dcc`, H7-D1's and queue AT in `1fc0ced0`). `privyhub-diag` untouched; no stream, no companion
or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; **the users'
cheat setups, their slots and in-game saves, the kept H7 folders, the rules folder and `runtime/h7_frames/` read only**
(the rules folder's specs read in place; H7-D1's / H7-C2's pictures read, nothing written beside them); no emulator
title started (B101's fake RetroArch on made-up fixtures; RetroArch not run); Godot headless only (B111's check in its
scratch copy); **the board's repo not touched** (status before = after). No title, serial, game id, character name,
cheat name or path in any record; **no game picture, crop or reference image in git** — I looked at two T89 watcher
pictures and one H7-C2 keeper picture beside a cut (none copied). The `/tmp/b_q31at` copy holds companion/, tools/,
tests/, PrivyHub/ (its sources) only. Nothing adopted; nothing committed. Deleted: only my own scratch
(`~/.cache/b_q31at_tmp`, the mutation copies).

## What was found and built

- **B129 — BUILT** (`evidence/B129_H7_GAME_WINDOW_2026-11-17.md`). **The cause of T89's desktop pictures, from the
  code:** `WindowPicture` kept the first window's rectangle for the companion's whole life (a screen grab never fails,
  so it was never found again), and T88 — whose window is the whole screen — ran first in both H7-V5 and H7-D1, so
  T89's watches grabbed T88's (0, 0, 1920, 1080). T89's own window is 960 × 720 (the keeper's (960, 384, 960, 720); the
  stream found 960 × 720 in all 20 N64 sessions of its log). **The onn's stream was never affected** (it finds the
  window afresh by the process at every start, by its id, fail closed). Built: the window owned by the game's own
  process, found again for every new process, after a failed grab and every 10 s; none → a picture failure, no read.
  **Offline:** H7-D1's T89 pictures cut by the rule's rectangle → `start` from the 2nd read early (2.0 s), the 1st late
  (1.2 s), least 0.0035 against 0.0932; 0 of 246 fights read as the screen; T88's 90 reads as the watcher read them.
  Tests 5, mutations 3 / 3 (HEAD's code reproduces H7-V5's fault).
- **B130 — BUILT** (`evidence/B130_H7_RECOGNISE_UNDER_SETUP_2026-11-17.md`): **under a cheat setup a watch begun with
  the load waits 15.0 s for the start** (every other 8.0 s, as today). Margin 6.0 s over the slowest seen (T88, 9.00 s
  in the board's order); **cost: a wrong screen under a setup says `false` 7.0 s later.** Replay: H7-D1's four folders
  true at 9.0 / 4.0 / 2.0 / 1.2 s; never-the-start runs false at 15.0 s, never true; H7-C2's slot 1 true at 7.02 s
  under both. Tests 4, mutation 1 / 1.
- **B131 — BUILT** (`evidence/B131_PARTY_SAVE_LOAD_REFUSED_2026-11-17.md`), **with a correction to B127:** the onn's
  SAVE / LOAD during a mini game never reached the users' setups — the manager has refused them since B110 whenever the
  board is set aside (503 "Saving and loading are not offered for the board game; nothing was sent."; HEAD's code in
  the test: nothing sent, every setup file byte-equal). The onn shows "Save state failed" and a "Game State" dialog
  "HTTP 503: {…}". Built: while a mini game is starting / playing, **400 "not during a mini game: nothing was saved" /
  "… loaded"** and one `minigame_state_refused` row; otherwise today. Tests 5; flags absent and outside a mini game →
  HEAD's answers.
- **H7-V5's "savestate_directory the setup's: False", in one line:** `status`'s `cheat_session` carries the profile id,
  source, cheats and activation only — no `savestate_directory` field — so that comparison read a missing key (False),
  while RetroArch's own load line shows the scratch in the setup's own folder: the folder was right.

Tests (`b131_2026-11-17/tests_x3.txt`): **B129 5, B130 4, B131 5 — 3 runs green each, 0 temp dirs**; mutations B129 3 / 3, B130 1 / 1, B131 1 (HEAD's routes: the new line and row missing; nothing sent and the setups byte-equal on HEAD too); the others once: B127 9, B124 6, B114 8 (with the scenario's new options), B115 6, B110 13, B112 7, B123 6, B122 12, B111 2, B102 16, B104 19, B103 13, B105 12, B101 14, B99 15, B108 16, art_systems 120 (the one doc test reads `docs/CHEATS.md`, outside the work copy — OK against the repo), B65 7, B61 14, the player prompt 11, the players' session 19, the relaunch 19, the pad slots 5, the stall signal 12, the stall owner 10, the link recovery 16, the fast restart 13, the client contract 5, PS2 93, GameCube 54, N64 28 — all OK; nothing left running.

## What I would change (not done — the queue is the task)

1. **The onn's refusal dialog:** a refused SAVE / LOAD shows "HTTP 400: {"ok": false, "error": "…"}" — the app could
   show only the `error` field (a client change), or the bar could hide SAVE / LOAD for the board and its mini games
   (already on the smoother-feel list).
2. **The END dialog's "Save"** during a mini game: refused, and then the game is not stopped (the stop runs only after a
   save) — the user must choose END again and "Don't Save". The app could stop anyway after a refused save.
3. **The final states before the end:** B131 refuses SAVE / LOAD only while `starting` / `playing` (as the queue
   asked); between `ended` / `given_up` and the board's end the title still runs — today's manager refusal covers it
   (the board is still set aside), so nothing leaks, but the line there is the board's.
4. **A notice-aware read** (counting the window from the first read without RetroArch's notices) would let the
   window stay short for a wrong screen; 15 s was chosen as the plain rule.
5. **The in-game save under a setup** — still flushed into the users' setup at each mini game's stop (B127 item 5);
   a scratch save folder per mini game if the users want their setups untouched.
6. **The keeper's T89 rectangle runs 24 rows below the screen** (the window's bottom is off screen at (960, 384)); the
   spec learnt those rows black. If the window ever opens fully on screen the bottom band differs — the reader's
   alignment search has absorbed less; worth a look when T89 is next pictured.

## A — H7-V5 again with B129-B131, then PP-H4 (B132)

T88 = H7's 2-player PS1 title; **T89** = the users' N64 four-player title; "T88's cheat setup" / "T89's cheat setup";
`H=http://127.0.0.1:8765/plugins/games`; `$RULES` = `~/privyhub_h7/rules`; `<T88 id>` / `<T89 id>` / `<T88 setup>` /
`<T89 setup>` / `<P88>` / `<P89>` read from the hub at stage 1, never written into a record. No title, character name,
cheat name, serial, game id, `profile_id`, path or picture in any record.

### H7-V5 again — B128's steps 1-20 (`SESSION_B_DONE_2026-11-17AS.md` §"H7-V5") with H7-V5's six changes (its task file), and these changes

**Keep the order T88 then T89 in one companion** — exactly the order that exposed B129's fault.

- **Step 1:** queue AT committed and the tree clean but for this task's files (else stop: "YOU, now: commit queue AT
  first, then send the read line again"); and **the code is B129-B131's:** `grep -c "RECOGNISE_SETUP_S = 15.0"
  companion/h7_minigame.py` → 1, `grep -c '"xdotool", "getwindowpid"' companion/h7_minigame.py` → 1, `grep -c "not during a mini
  game: nothing was saved" companion/party_minigame.py` → 1 (else stop and say which). The window as change 1 (outside
  04:30-05:30Z and not within 45 min before it).
- **Steps 3-6 — nothing to relearn, nothing copied, nothing renamed: the rules folder as H7-V5 left it, checked
  read only:** `python3 -c "import json;s=json.load(open('$RULES/<T88 id>.endscreen.json'));print(s['version'],
  s['screen_threshold'],s['class_thresholds'],s['margin_needed'],s['screen_mask_px'],s['outcome_mask_px'])"` → `2 0.082
  {'end_P1': 0.1044, 'end_P2': 0.0983, 'start': 0.0958} 0.0921 12244 104`; the same for `<T89 id>` →
  `version` 3, `screens` start 0.0932 / end 0.1011, `places.thresholds` 0.2212 / 0.2218 / 0.1744 / 0.1915,
  `places.margin_needed` 0.0796; `sha256sum "$RULES/<T88 id>.<P88>.state" "$RULES/<T89 id>.<P89>.state"` → `be4aa243…` /
  `78c53af3…`; both `party.json` with `cheat` naming the setups read at step 2 (`source_index`, `enabled_cheat_indexes`,
  `profile_id` equal). Any difference → stop and say which. (B129 changes what the watcher grabs, not what the specs
  were learnt from: the specs came from the window's own pictures.)
- **Step 12 — T88's recognition:** `h7_results`' `watching` row for T88 carries **`"recognise_s": 15.0`** and
  `"begin": "setup"`; **the `recognised` row `"value": true` with `"after_s"` about 9-10 s** (H7-D1's board order: 9.00
  s; the window 15.0 s); no `picture_failed` row. A `false` (after 15.0 s) → that title NOT MET as change 4, the cause
  named from `last`.
- **New step 12b — SAVE and LOAD during the T88 mini game** (right after 12's `recognised` true, before 13):
  `curl -s -X POST "$H/save-state?slot=1"` → **400 `{"ok": false, "error": "not during a mini game: nothing was
  saved"}`**; `curl -s -X POST "$H/load-state?slot=1"` → **400 `{"ok": false, "error": "not during a mini game: nothing
  was loaded"}`**; `logs/games/party.jsonl` gains two rows **`{"step": "minigame_state_refused", "what": "save", "state":
  "playing"}`** and `… "what": "load" …`; RetroArch's session log gains no "Saving state" / "Loading state" line from
  them; `curl -s "$H/party-minigame-result"` → still `"playing"`; **T88's setup's files listed again — every sha256 =
  step 8's.**
- **Step 16 — T89's recognition:** `watching` `"recognise_s": 15.0`, `"begin": "setup"`; **`recognised` true at the
  first or second read (`after_s` about 1.2-2.0 s)**; **no `picture_failed` row**; `curl -s "$H/h7-result"` → `last`'s
  `start` distance well under 0.0932 (H7-D1's pictures cut to the window: 0.0035-0.031). If `picture_failed` rows appear
  ("the game's window was not found"), record them — B129 found no window owned by the title's process.
- **Steps 13-15 and 17-20** as B128 with changes 4-6 — every hand load into the setup's own folder (T89 only while
  `PAUSED`), every scratch removed at once; step 20's cell the setups' slots and slot pictures and every normal state and
  save before = after; the in-game saves recorded, not a cell.
- **Pre-registered:** B128's 3-6 (as checked above) and 10-20 with these changes; **MET = every one** (12 and 16
  `recognised` true inside 15.0 s, 12b refused with the setups byte-equal). MET → PP-H4 may be offered. The close as
  B128's (eighteen lines; `party-minigames` and `bench-release` → 400; nothing running).

### PP-H4 — the four-person sitting (only if H7-V5 is MET)

**As B128's PP-H4** (`SESSION_B_DONE_2026-11-17AS.md` §"PP-H4": B125's sitting with both titles under their setups;
the preconditions — B124's two board files committed, the PC side's picker line there; the rules folder as H7-V5 left
it; part 1's two bench mini games; the lines; cells J, D, P, X, R, H, E, C, L, U), with these changes:

- **Part 1's two bench mini games** also read `"recognise_s": 15.0` and `recognised` true (T88 ~9-10 s, T89 ~1-2 s).
- **The line about SAVE / LOAD** ("While [T88] or [T89] is on, don't choose SAVE or LOAD on the onn's bar.") **stays
  unless B131 has been adopted by then** — it spares the players a "Save state failed" box; SAVE / LOAD cannot touch the
  setups either way (the hub refuses them while the board is set aside, before and after B131).
- **Cell U:** unchanged from B128 (the setups' slots and pictures before = after; the in-game saves recorded).
- **Added to C (recorded, no bar):** each mini game's `recognised` second from its `recognised` row.


## Files

B129: `companion/h7_minigame.py` (`WindowPicture`), `tests/b129_h7_game_window/` (new), `evidence/B129_…` +
`b129_2026-11-17/` (`b129.diff` — B129's and B130's hunks in `h7_minigame.py`, `scripts/b129_b130_offline.py`,
`offline_results.jsonl`), `patches/B129_H7_GAME_WINDOW.md`. B130: `companion/h7_minigame.py` (`RECOGNISE_SETUP_S`),
`tests/b130_h7_recognise_setup/` (new), `evidence/B130_…` + `b130_2026-11-17/` (`replay_results.jsonl`, `b130.diff`),
`patches/B130_…`. B131: `companion/plugins/games.py`, `companion/party_minigame.py`, `tests/b131_party_save_load/`
(new), `tests/b114_party_minigame_hang/b114_scenario.py` (`saveload` / `board_saveload` options), `evidence/B131_…` +
`b131_2026-11-17/` (`b131.diff`, `tests_x3.txt`), `patches/B131_…`. Also: `evidence/B127_…` (a correction section
appended), `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph inserted after queue AS's),
`logs/b129_|b130_|b131_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue AT's B129-B132).
