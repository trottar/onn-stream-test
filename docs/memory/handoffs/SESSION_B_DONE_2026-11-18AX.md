# SESSION B — done, 2026-11-18 AX (QUEUE_2026-11-18AX: B143 the sound across a planned switch, B144 a practice banner, B145 three small things, B146 A's next tasks sketched; run ~04:14Z-06:22Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (PP-H3c's second
record and queue AX in `246c67da`; the prompt files untracked-ignored, unchanged); the board's repo clean at `4140949`.
No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the
drive; the users' cheat setups, their slots and in-game saves, the kept H7 folders and the rules folder not opened;
**read only:** the onn's heartbeat rows and the sitting's party rows (numbers only), the app's sources. **No emulator
title started.** **Disclosed:** a made-up 960 × 720 Tk window on the hub's display, ~6 s per B144 run (four runs). The
probes' own made-up ffmpeg sources (`testsrc2`, `color`) were drawn to PNGs in my scratch, looked at once to see the
band, then removed. Godot ran headless only, in scratch copies of the board's tree. No title, serial, game id,
`profile_id`, character name, cheat name or path in any record; no game's name; no picture in git. The `/tmp/b_q35ax`
copy holds companion/, tools/, tests/, PrivyHub/ (its sources) only. Nothing adopted; nothing committed in either repo.
Deleted: only my own scratch (the probes' PNGs, the stage trees, the mutation copies, the temp dirs a stopped run and the older suites left in my TMPDIR, the work copy's `logs/` and `__pycache__`, my new test folders' `__pycache__`).

## What was found and built

- **B143 — BUILT** (`evidence/B143_PARTY_AUDIO_ACROSS_SWITCH_2026-11-18.md`). **Why the sound was silent:** every
  `native_stream.start` begins a new audio sender at sequence 0. PHA1 has no SSRC or marker, and the app drops a frame
  that is behind what it has already played (`OpusReorder.offer`, LATE) until the new count passes it. Only a new
  receiver starts over: a new client session (Home / RESUME), or the app's own restart (B11), never a hub-side switch.
  **The rule replayed on PP-H3c's twelve streams predicts every silent stretch within one heartbeat row (max error
  2.0 s).** **Built (hub only, the app as adopted):** every planned switch arms the audio streamer for the new process,
  and its sender continues the last run's sequence and timestamp. The users' own starts begin at 0, byte for byte
  today's. **The silent stretch left:** the new process's first frame plays as it arrives (0 ms in the model; bound
  50 ms). The switch's own gap of no sound is unchanged: ~770 ms in the harness, at most the switch's own 1.7-3.6 s on
  the hub, the new sender's first datagram ~0.25 s before the row. Tests 5.
- **B144 — BUILT** (`evidence/B144_PARTY_PRACTICE_BANNER_2026-11-18.md`): the hub's ffmpeg `drawtext` with
  fontconfig's `Sans` (no font path, no image, nothing fetched) draws "PRACTICE — press Start to go back" across the top
  of the onn's picture. It sits after `format=nv12` and before `hwupload`, in rows 0-58 of 720, white on black at 72 %,
  and costs **+0.38 ms CPU a frame** (~2.3 % of a core at 60 fps). It is on only from a practice's planned switch to
  the way back's start; the title's window is never drawn on, so the watcher cannot see it. Every other start's command
  equals HEAD's. Tests 5.
- **B145 — BUILT** (`evidence/B145_PARTY_SMALL_THINGS_2026-11-18.md`): Select is held through a practice until a
  real go (the hub; Select + Start still leaves a practice, without quitting). In my board file, the load screen is
  shown again at a practice's hand-over, so the way back lands on it, and the board logs `cards <n>, chose <0 | 1 |
  random>` and `start` / `practice`. The hub's tests 4; **the board's check PASS 89 (was 81)**; B111 updated.
- **B146 — sketched below (no code).**

Tests (`b143_2026-11-18/tests_x3.txt`, `tests_recent.txt`, `tests_others.txt`, `tests_mutations.txt`; `b145_2026-11-18/check_runs.txt`): **B143 5, B144 5, B145 4 — three runs green each, 0 temp dirs**; the recent suites once, all OK (B141 4, B140 3, B139 5, B137 10, B133 9, B134 5, start_rung 17, encoder_rc 16); **the earlier suites once, all OK** (B129-B131, B127, B124, **B114 8 with its flags-absent test**, B115, B110, B112, B123, B122, **B111 2 with Godot and the board's repo**, B108, B105, B103, B102, B104, B101, B99, B65, B61, the player prompt, the players' session, the relaunch, the pad slots ×2, the stall signal / owner, the link recovery, the fast restart, **the client contract 5**, the input hold ×2, the keyframe request, the loss rule, impairment, **audio codec 20**, B72, PS2, GameCube, N64; art_systems 120 against the repo, its doc test reading `docs/CHEATS.md`); **mutations 8 / 8** (B143's arm off, B143's pid check off, B144's arm off, B144's band always, B145's hold released at a practice's go, and three in my board file); **the board's check PASS 89 five runs** on the final check (a first set's third run counted one press in the frame before the board's gate rose — the screen of before the hand-over, cleared by the re-show; the check now counts from the re-show: B145's record), the PC side's step25 PASS 107 and step8 PASS 210.

## What I would change (not done — the queue is the task)

1. **The switch's own gap of no sound** (~1.5-3.3 s on the hub; ~0.77 s in the harness): `_start_linux_locked` stops
   the old audio first and starts the new one last, after the encoder's 0.75-s check. For a planned switch the new
   audio could start before that check, or the old sender could keep sending the old process's sound until the new one
   is up. That is a few lines in the stream's start, but it is the users' start path, so it needs its own design.
2. **A practice whose hand-over the board never sees** (Start pressed within about a second of it): the board's `went`
   stays set, so no further go is sent until the board's own 20-minute bound. This was there before B145 and is not
   made worse. The hub's `"practices"` count in its answer would tell the board a practice came and went.
3. **RESUME during a practice** (a users' start for the title) shows the practice without its banner until the way
   back. A RESUME taken onto a mini game's queue could re-arm it.
4. **The board's load-screen show leaves no row on the hub**, so PP-H3d's "the load screen there when the practice
   ends" rests on the order of the rows and the user's words (below). One board log line at the re-show would make it a
   row; I did not add it, because the queue names exactly two lines.
5. From AW, still open: T89's frame count and mute; the watcher's own pictures for a party watch; B137's mask code
   unused; the onn's Home during the load screen gives the mini game up; `announce_minigame` still says "On the hub";
   presses before the launch's answer reach the booting title.

## B146 — what a bench can and cannot show of B143-B145

**Plainly: an unattended bench shows nothing of these that the tests do not.** The bench has no client: with `bench=1`
there is no stream, so there is no planned switch, no audio sender and no encoder command (B143 and B144 live entirely
in the stream). There are no pads either, so B145's Select hold has nothing to clear. The board's log lines come from
the board's own screens, which the bench drives by `curl` rather than through them. **No new unattended check is
proposed.** What gates PP-H3d is PP-H3c's part 1 unchanged (the board's checks headless in a scratch copy, one held T88
start on the bench to `end_P1` [1, 0]) plus the new code checks in stage 1 below. B143 and B144 can only be read with
the onn as client, which is PP-H3d itself.

## A — PP-H3d: the user alone with two pads, ~10 min at the TV (after part 1)

T88, "T88's cheat setup", `H=http://127.0.0.1:8765/plugins/games` as before; a game's name run-time data only.
`PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1` for the task only (twenty lines, back to eighteen).

**Preconditions (stage 1, before the pre-registration):**
- **PP-H3c (second try) MET** (it is); this repo **with queue AX's B143-B145 committed** and clean but for the task's
  files, else "YOU, now: commit queue AX first, then send the read line again".
- The code, each → 1: `grep -c "def party_continue_next" companion/native_session_io.py`; `grep -cF 'run =
  streamer._audio_run = object()' companion/audio_codec.py`; `grep -cF 'self._arm_switch(ns, int(pid))'
  companion/party_minigame.py`; `grep -c 'press Start to go back"'
  companion/native_stream.py`; `grep -cF 'banner=bool(go["practice"]))):   # B144' companion/party_minigame.py`;
  `grep -cF 'if not go["practice"]:                              # B145' companion/party_minigame.py`; and B142's
  greps (H7-V6b's step 1).
- The board's repo with my two files committed: `minigames/hub_minigame.gd` sha256 `a1e648f3…`,
  `checks/hub_minigame_check.gd` `95eb6f89…` (else B138's stop line); `grep -c 'PrivyParty: hub mini game: cards %d,
  chose' minigames/hub_minigame.gd` → 3.
- **Before:** every file of the states, saves and cheat setups (count, sha256) as PP-H3c; **the line counts of
  `logs/games/native_stream_heartbeat.log` and `logs/games/native_video_alpha.log`** (`wc -l`), kept as N_HB and N_ENC.
- Part 1 as PP-H3c's (the board's check now **PASS (89)**; the PC side's `step25_before_minigame` PASS).

**The lines** (PP-H3c's, with these changes):
- After the pads-down line ("YOU, now: put both pads down and reply ok"), **A waits for the user's "ok"** before the
  streamed self-proof starts. PP-H3c did not; the user then saw "<T88> just randomly popped up".
- The play line: "YOU, now: play the board for about two minutes with both pads. When the game's load screen comes up,
  ask for a practice (the practice button, as before); a band at the top of the TV will say PRACTICE — press Start to
  go back. In the practice, press Select and R1 together once, then Start to go back. Then ready both players for the
  real match and play it to the end." (The buttons named both ways as B138 does, read at stage 1 from the board's own
  files.)
- After the practice: "YOU, now: in one line — what did the TV show the moment the practice ended, and did the band
  show during it?"
- After the match: "YOU, now: in one line — how was the sound, on the board and in both rounds?"

**Pre-registered (hashed before part 1), nothing perceptual:**
- **S — the sound after every planned switch** (each `minigame_stream` row with `"switched": true` at time T,
  `"seconds"` s): among the onn's heartbeat rows after N_HB, **a row with `audio_queue_depth` > 0 within 4 s after T**,
  and from that row to the next switch's start (its T − its seconds), **`audio_underruns` rising ≤ 20 per row** (rows
  2 s apart; PP-H3c's healthy rows: median 0, p95 4; its silent ones ≥ 50 a row). The read, exactly:
  `python3 -c 'import json,sys;[print(r["received_at_utc"],r["audio_queue_depth"],r["audio_underruns"]) for r in map(json.loads,open("logs/games/native_stream_heartbeat.log").read().splitlines()[int(sys.argv[1]):])]' N_HB`
  beside the party rows. Recorded, no bar: `audio_lost_packets`, `audio_rx_packets` (~100 / s).
- **B — the banner in the practice's command only:** `tail -n +$((N_ENC+1)) logs/games/native_video_alpha.log | grep -a
  '^encoder argv:'` (`-a`: the log holds ffmpeg's binary noise). The argv line written after the practice's `minigame_stream` (`window` minigame, after a
  `minigame_go` with `"practice": true`) contains `PRACTICE — press Start to go back`; **every other argv line of the
  sitting does not** (`grep -c` over them = the number of practices, 1).
- **L — the board's log lines:** `grep -h 'PrivyParty: hub mini game:' "$(ls -t logs/games/*-party.log | head -1)"` →
  in order `cards 1, chose 0` (T88 is the one two-player title, so one card), `practice`, `start`, then `scores [a, b]
  for seats 1,2` with the hub's `end_P*` scores. No line carries a name.
- **P — Select + R1 in the practice:** the user's press (A reads the time from the user's words). **Every file of the
  states, saves and T88's cheat setup before = after** (sha256), as cell U, so the save hotkey wrote nothing.
- **LS — the load screen there when the practice ends:** the hub's rows cannot see the board's screen. The rows show
  the order: `minigame_playing` (`"practice": true`) at least 2 s before `minigame_practice_end` (`"by":
  "start_button"`) (the board polls each second, so it re-shows within ~1.25 s of the hand-over); then the way back's
  `minigame_stream` (`board`), `minigame_ready` `"after_practice": true`, and **no `minigame_go` before it**. The user's
  line after the practice is recorded as it stands, no bar.
- B138's / PP-H3c's F, R, S (one card), PS (by Start), M, E, U, W as before; **H dropped** (no Home / RESUME in this
  sitting).
- **MET = part 1 and S, B, L, P, LS, F, R, PS, M, E, U, W.** Recorded, no bar: the user's words on the sound and the
  band; each `prepare_s`, `held_s`, `mute_ms`, each switch's `seconds`.

## A — PP-H4's changes on top of B142's

- **Preconditions:** PP-H3d MET; this repo's B143-B145 greps (above); the board's files `a1e648f3…` / `95eb6f89…`; the
  board's check PASS (89).
- **Cell S over every mini game of the sitting:** every planned switch (in, practice, way back, end) read as PP-H3d's S.
- **Cell B:** every practice's encoder argv carries the band; no other argv does.
- **The lines (what the players will see at a practice):** "When you pick practice, a band at the top of the TV says
  PRACTICE — press Start to go back; anyone's Start ends it and brings everyone back to the load screen."
- **The streamed self-proof only after the users' "ok"** to the pads-down line.
- Cell L: the board's lines for every choice and decision of the sitting, in order, with the hub's rows.

## Files

B143: `companion/native_session_io.py`, `companion/audio_codec.py`, `companion/party_minigame.py`,
`tests/b143_party_audio_switch/` (new), `tests/b114_party_minigame_hang/b114_scenario.py`; B144:
`companion/native_stream.py`, `companion/party_minigame.py`, `tests/b144_party_practice_banner/` (new); B145:
`companion/party_minigame.py`, `tests/b145_party_small_things/` (new), the scenario, `tests/b111_party_board/test_b111.py`;
`evidence/B143_…`, `B144_…`, `B145_…` + their folders (`b143.diff`, `b144.diff`, `b145.diff` — apply in that order on
`246c67da`; `b145_board.diff` on the board's `4140949`), `patches/B143_…`, `B144_…`, `B145_…`. Then `docs/KNOWN_ISSUES.md`
(one line inserted), `docs/ROADMAP.md` (one paragraph inserted after PP-H3c's second try), `logs/b143_|b144_|b145_git_status.txt`,
`handoffs/SESSION_B_STATUS.txt` (one line), this file. **The board's repo:** `minigames/hub_minigame.gd`,
`checks/hub_minigame_check.gd` (uncommitted).

**The user, now:** this repo — commit the tree (queue AX's B143-B146). **The board's repo** — `git add
minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m "Hub mini game: the load screen behind a
practice, one log line per choice and decision; its check"`.
