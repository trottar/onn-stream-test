# SESSION B — done, 2026-11-18 AY (QUEUE_2026-11-18AY: B147 the band inside the picture, B148 the board prepared before its launch, B149 a practice that came and went unseen, B150 PP-H4 written afresh; run ~07:39Z-08:58Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (PP-H3d's record and
queue AY in `1052fe82`; the prompt files untracked-ignored, unchanged); the board's repo clean at `32d5329` (has
`e0ce8c4`, my two files committed there at `a1e648f3…` / `95eb6f89…`). No stream, no companion or keeper restart, no adb,
no sudo, no nft; nothing fetched or installed; nothing written to the drive; the users' cheat setups, their slots and
in-game saves, the kept H7 folders, the rules folder and `runtime/` pictures not opened; **read only:** the app's sources,
the board's tracked files and its `.godot/` cache (B148's test and the md5 records). **No emulator title started.**
**Godot headless only, and only on scratch copies / clones of the board's tree. The board's own folder was not written,
its cache included** (its status 0 lines throughout but for my two files). **Disclosed:** B148's one real-board run, a
cold scratch clone, Godot's `--import` then `step26`, 07:45Z, removed; my settle's three imports on a scratch clone
(07:3xZ, removed); B144's made-up Tk window on the hub's display ~6 s per B144 run (four runs). A made-up frame
(`color`) was drawn once to see the new band, looked at, removed. No title, serial, game id, `profile_id`, character
name, cheat name or path in any record; no picture or sound in git. The `/tmp/b_q36ay` copy holds companion/, tools/,
tests/, PrivyHub/ (its sources) only. Nothing adopted; nothing committed in either repo. Deleted: only my own scratch
(queue AX's `/tmp/b_q35ax` copy, my `~/.cache` scratch and TMPDIR with the temp dirs the older suites left, the mutation copies, the work copy's `logs/` and `__pycache__`, my new test folders' `__pycache__`).

## What was found and built

- **B147 — BUILT** (`evidence/B147_PARTY_BAND_INSIDE_2026-11-18.md`). **The app cannot cut the picture:** it fits
  the whole 16:9 frame to its full-screen `SurfaceView` (MediaCodec's default scale-to-fit, no crop or zoom, no overlay
  at the top). **Only the TV's overscan can.** The same words, with the box's top at `h*5/100` and only as wide as the
  words: **rows 36-85, columns 379-899 of 720p, 3.8 % of a 4:3 title's picture** (B144's: rows 0-58 across the
  frame, 8.2 %), every pixel inside the inner 90 %, +0.22 ms CPU a frame. Every other command equals HEAD's. Tests 2,
  B144's updated.
- **B148 — BUILT** (`evidence/B148_PARTY_BOARD_PREPARED_2026-11-18.md`). **How the hub knows:** every tracked
  `<file>.import` sidecar's `dest_files` must be in the git-ignored `.godot/imported/`, each with a `.md5` whose
  `source_md5` is the source's md5, and every picture or sound must have its sidecar. That test takes **22 ms** on the
  board's folder. When it fails, Godot's `--headless --import` runs first, **bounded at 20 s**, with row `board_import`
  (`needed`, `files`, `seconds`, `rc`; `timeout` / `skipped` / `error`). A failure still launches as today, it never
  runs while the board does, and nothing to prepare means no row and the launch as today. **The import costs 3.8 s
  cold, 2.9 s warm, and writes only `.godot/`.** Tests 6; once on a cold clone of the real board: 24 needed → 3.87 s
  rc 0 → 0, step26 PASS (117), 0 status lines.
- **B149 — BUILT** (`evidence/B149_PARTY_UNSEEN_PRACTICE_2026-11-18.md`): the hub's answer as it is (it carries
  `practices` in every held state). When the count rises while the board still waits on its go, the load screen is
  shown again (marks clear, the gate having kept the pads off it) and the next choice is taken at once. `PrivyParty:
  hub mini game: load screen again` is logged at every re-show after a practice. **The check PASS 97** (was 89); B111
  97 / 68.
- **B150 — PP-H4 written afresh below (no code).**

Tests (`b147_2026-11-18/tests_x3.txt`, `tests_recent.txt`, `tests_others.txt`, `tests_mutations.txt`; `b149_2026-11-18/check_runs.txt`): **B147 2, B148 6 (its real-board class run once, disclosed), B144 5 (updated) — three runs green each, 0 temp dirs**; the recent suites once, all OK (B143 5, B145 4, B141 4, B140 3, B139 5, B137 10, B133 9, B134 5, start_rung 17, encoder_rc 16); **the earlier suites once, all OK** (B114 8 with its flags-absent test, **B108 16 with its flag-absent test**, B111 2 with Godot and the board's repo, the client contract 5, audio codec 20, and the rest of B137's list; art_systems 120 against the repo, its doc test reading `docs/CHEATS.md`); **mutations 7 / 7** (B147's old band; B148's prepare always, no bound, import while running; my board file's unseen branch and its line); **the board's check PASS 97 three runs**, B111 97 / 68, and the PC side's step25 107, step26 117, step27 56, step8 210 with my files.

## What I would change (not done — the queue is the task)

1. **The switch's own gap with no sound** (~1.5-3.3 s on the hub, PP-H3d's arrival gaps 1.6-1.8 s): still there. For a
   planned switch the new audio could start before the encoder's 0.75-s check. It is in the users' start path, so it
   needs its own design.
2. **The import's bound against a big push:** 20 s covers the board's whole tree cold (3.8 s) five times over. A push
   of many new models could pass it; the board would then launch unprepared, as today, and the row would say `timeout`.
   A second launch would finish the job, because Godot keeps what it imported.
3. **Content-folder files** (the owner's clips in the content folder) are loaded at run time, not imported, so B148
   neither needs nor tests them. A missing clip is the user's copy step (PP-H3d), not an import.
4. **The cards and the load screen re-show** leave no hub row: PP-H4's L cell reads the board's own log for them.
5. From AW / AX, still open: T89's frame count and mute; the watcher's own pictures for a party watch; the onn's Home
   during the load screen gives the mini game up; `announce_minigame` still says "On the hub"; presses before the
   launch's answer reach the booting title; RESUME during a practice shows it without its band.

## B150 — A: PP-H4, four people with four pads (run from this alone)

**T88** = H7's 2-player PS1 title, **T89** = its 4-player N64 title, each under "its cheat setup". In replies to the
users the games may be named; **in every record only T88 / T89**. No title, character name, cheat name, serial, game id,
`profile_id`, path, address, port or picture in git; no answer carrying a `"title"` copied. Names read at run time,
never in a record: `H=http://127.0.0.1:8765/plugins/games`; `$RULES` (the rules folder) and `$KEPT` (the kept H7 states)
from the hub's own config as H7-V5b used them; `$BOARD` (the board's repo) and `$PROJECT` (the board's folder the hub
launches, party.json's `project`); TOKEN2 / TOKEN4 from `party-minigames`. `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1` for the
task only (twenty lines, back to eighteen at the close). Pre-registered; nothing perceptual. **Nobody is asked to sit
down unless part 1 and the self-proof's S are MET.**

### Stage 1 (pre-registered after it, before part 1)

1. **The window:** outside 04:30-05:30Z and not within 45 min before it, else reply only "YOU, now: the hub's nightly
   window runs until 12:30 am Eastern; send the read line again after that".
2. **This repo:** queue AY and PP-H3d's record committed, clean but for this task's files, else "YOU, now: commit queue
   AY first, then send the read line again". **The code**, each → the number given, else stop and say which:
   `grep -cF 'y=h*5/100+10:box=1:boxcolor=black@0.72:boxborderw=10|16|10|16' companion/native_stream.py` → 1;
   `grep -c "def import_needed" companion/party_session.py` → 1; `grep -c "IMPORT_LIMIT_S = 20.0"
   companion/party_session.py` → 1; `grep -cF '_party.prepare(cfg, self._party_row, log_handle, os.environ)'
   companion/games/emulator_manager.py` → 1; `grep -c "def party_continue_next" companion/native_session_io.py` → 1;
   `grep -c "def party_banner_next" companion/native_stream.py` → 1; `grep -c '# B145: held through a practice too'
   companion/party_minigame.py` → 1; `grep -c
   'PARTY_SESSION_SETTINGS = {"video_font_enable": "false", "menu_show_load_content_animation": "false"}'
   companion/party_minigame.py` → 1; `grep -c "ADVANCE_STEPS = (0, 2, 4, 8, 16, 30)" companion/party_minigame.py` → 1;
   `grep -c "def party_hold_select" companion/native_session_io.py` → 1.
3. **The board's repo:** clean (`git -C "$BOARD" status --short` → 0 lines); **`git -C "$BOARD" merge-base
   --is-ancestor e0ce8c4 HEAD` → true** (any later commit of the PC side's is accepted: record HEAD and `git -C "$BOARD"
   diff --name-only e0ce8c4 HEAD` (names only)); **my two files committed at sha256 `3f32d339…`
   (`minigames/hub_minigame.gd`) and `01301ec5…` (`checks/hub_minigame_check.gd`)**, else "YOU, now: in the board's
   repo commit the hub side's two files, then send the read line again"; `grep -c 'PrivyParty: hub mini game: load
   screen again' "$BOARD/minigames/hub_minigame.gd"` → 2; `grep -c 'PrivyParty: hub mini game: cards %d, chose'
   "$BOARD/minigames/hub_minigame.gd"` → 3. **The board's folder the hub launches is that same commit** (its HEAD =
   `$BOARD`'s HEAD).
4. **The joining and ready-up words, read from the board's README at that HEAD** ("The opening screen", "Before one of
   the hub's mini games", "After a mini game or a duel") and `game/minigame_screens.gd` (`READY_BUTTON`, `PAD`,
   `PRACTICE_ENDS`). At `32d5329`: hold any button to join (up to four), left / right changes your character, player 1
   picks the board, the rules and the rounds (up / down picks a line, left / right changes it), confirm (A, ✕) says
   ready, back (B, ○) takes it back; on the load screen confirm = ready, back = not ready, **the map button (Y, △) asks
   for a practice**; "A practice ends with the Start button, or after about 90 seconds"; after a mini game a result
   screen, then the winner presses confirm. If the README at HEAD says otherwise, word the lines from it.
5. **adb** as PP-H3c's second try used it; **never a question at the TV** (if the onn is not a `device`, go on from the
   hub's rows and say so once in the first message).
6. **The rules folder as H7-V5b left it** (both specs, both setups' begins, both sidecars with `cheat`); each setup
   read through `curl -s -X POST "$H/cheat-profiles?id=<the title's id>"` → the sidecar's `profile_id`, source and
   indexes (the values compared in memory, never written down).
7. **Before:** every file under `data/games/retroarch/states/`, `…/saves/`, `…/cheat_profiles/` (count, sha256); no
   `.state8`; the line counts of `logs/games/party.jsonl`, `logs/games/h7_results.jsonl`,
   `logs/games/native_stream_heartbeat.log` (N_HB), `logs/games/native_video_alpha.log` (N_ENC). **B148's test, read
   only:** `python3 -c 'import sys;sys.path.insert(0,"companion");import party_session as p;print(p.import_needed(sys.argv[1]))' "$PROJECT"`
   → recorded (0 when nothing new has been pushed since A's import; else the number of files the launch will import).
8. Both drop-ins; daemon-reload; the companion restarted (no SIGKILL); **twenty** lines. **The pre-registration
   hashed. Nothing of part 1 before the hash.**

### Part 1 — unattended, the gate (~12 min)

(a) **Every board check PASS on a scratch copy** of `$BOARD` at HEAD (`git archive HEAD`, Godot headless, Godot's own
folders in the scratch, removed after): `checks/hub_minigame_check.gd` **PASS (97)**, `step25_before_minigame` PASS,
`step26_sound_and_ready` PASS, `step27_winner_screen` PASS, `step8_modules` PASS, and every check changed since
`e0ce8c4` (`git diff --name-only e0ce8c4 HEAD -- checks/`) PASS.
(b) **The board launched on the bench:** `curl -s "$H/games?system=party"` → the board's id; `curl -s -m 120 -X POST
"$H/launch?id=<id>"` → `active`; `curl -s -X POST "$H/bench-release"` → `"released": true`. **B148:** if stage 1's test
gave 0, **no `board_import` row**; if it gave n > 0, **one `board_import` row `"needed": true, "files": n, "rc": 0`**,
`seconds` ≤ 20, before the `launch` row, and the test → 0 after. A `timeout` or `rc` ≠ 0 → not met.
(c) **The list:** `curl -s "$H/party-minigames"` → two entries, `"players"` 2 and 4 (TOKEN2, TOKEN4).
(d) **T88 held, seats 1,2:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN2&seats=1,2&bench=1&hold=1"` →
`"starting"`; `ready` within 5 s; rows `minigame_launch` `"cheat": true, "profile_matches": true`, the session config's
two keys `"false"` (`grep -E '^(video_font_enable|menu_show_load_content_animation) = '
data/games/retroarch/config/privyhub-session.cfg`), `minigame_frame_advance` `"changed": true, "paused": true`;
**PAUSED** (the paused proof: `GET_STATUS` once a second on the port in `data/games/retroarch/config/privyhub-input.cfg`
from the `minigame_watch` row to the go); `curl -s -X POST "$H/party-minigame-go"` → `"taken"` → `playing`, **no
`minigame_reloaded`**; the kept end P1 by hand into T88's setup's `states/<core>/<stem>.state8` (`cp "$KEPT/t88/end_p1.state"
…`; `LOAD_STATE_SLOT 8` on the port; the scratch removed) → **`ended` `end_P1` `[1, 0]`**; `curl -s -X POST
"$H/party-minigame-end"`.
(e) **T89 held, seats 3,1,4,2, a practice, its way back, then a real go:** `…party-minigame-start?id=$TOKEN4&seats=3,1,4,2&bench=1&hold=1`
→ `ready` within 6 s, PAUSED, the two keys, the cheat row; **`curl -s -X POST "$H/party-minigame-go?practice=1"`** →
`playing`, `"practice": true`. **On the bench no pad presses Start, so the practice ends by its own bound:
`PRACTICE_S = 90.0` s in the code (the bench has no shorter bound); this costs 1.5 min plus the way back (~3 s).** →
`minigame_practice_end` `"by": "time"`, `practice_s` ≥ 90, no `minigame_ended` inside; `minigame_ready`
`"after_practice": true`; PAUSED from that watch row; then `curl -s -X POST "$H/party-minigame-go"` → `playing`, no
`minigame_reloaded`; `results_1` by hand while paused (`PAUSE_TOGGLE` → `GET_STATUS PAUSED`; `cp "$KEPT/t89/results_1.state"
"<T89's setup>/states/Mupen64Plus-Next/<stem>.state8"`; `LOAD_STATE_SLOT 8`; the scratch removed; `PAUSE_TOGGLE`) →
**`ended`, `"places": [1, 2, 3, 4]`, `"scores": [4, 3, 2, 1]`, `"seats": [3, 1, 4, 2]`**; the end.
(f) The board quit (`curl -s -X POST "$H/stop"` → F10, exit 0); **every file of stage 1's 7 before = after**; no
`.state8`.
**Part 1 MET = (a)-(f).** Not met → no line asks anyone to pick up a pad: one plain sentence naming what failed, the
close, "YOU, now: commit".

### The streamed self-proof — the user alone, before anyone else sits down

Line 1 (the user alone, two pads are enough): "YOU, now: on the onn's PrivyHub home open Games, then 'PrivyParty (1)',
press OK on its one game, choose 'Launch on Companion' and press OK, then 'Start Fresh' and OK. When the board's
opening screen shows, put both pads down and reply ok — I will switch the TV to a game and back once, by myself, in
about 20 seconds; nothing to press."
**A waits for the user's "ok".** Then, by `curl` as the board would: `…party-minigame-start?id=$TOKEN2&seats=1,2&hold=1`
(no `bench`) → `ready`; the go → the switch to T88 (`minigame_stream` `"switched": true`); **the title held 6 s after
`playing`** (A waits 6 s); then `curl -s -X POST "$H/party-minigame-end"` → the switch back (`minigame_stream`
`"window": "board"`, `"switched": true`). **Then A waits 4 s and reads S on both switches** (below). **S not met on
either → stop:** one plain sentence, the close, "YOU, now: commit". Rows recorded: each switch's `seconds`, the band
absent from both encoder argv lines (`tail -n +$((N_ENC+1)) logs/games/native_video_alpha.log | grep -a '^encoder argv:'`).

### S — the sound after a planned switch (worded so the sound alone meets or fails it)

The switches are the party log's `minigame_stream` rows with `"switched": true`, in order. Each has a time T (the row's
`time_unix`) and `seconds`; its start is T − `seconds`. **Read: every switch whose next switch starts 4 s or more after
its T.** A switch followed sooner is **listed, not read**. For each read switch: among the onn's heartbeat rows after
N_HB, **a row with `audio_queue_depth` > 0 within 4 s after T**, and **from that row to the next switch's start (or 30 s,
or the END), `audio_underruns` rising ≤ 20 from one row to the next** (rows 2 s apart; PP-H3c's healthy rows: median 0,
p95 4; its silent ones ≥ 50). The read, exactly:
`python3 -c 'import json,sys;[print(r["received_at_utc"],r["audio_queue_depth"],r["audio_underruns"],r["audio_lost_packets"]) for r in map(json.loads,open("logs/games/native_stream_heartbeat.log").read().splitlines()[int(sys.argv[1]):])]' N_HB`
beside `grep minigame_stream logs/games/party.jsonl`. Recorded, no bar: `audio_lost_packets`, `audio_max_arrival_gap_ms`
at each switch.

### The sitting (~30-35 min, four people, four pads paired to the onn)

**Every line starts "YOU, now:", is one complete step, and says first what the hub already decided when there is
something to say.**

- **Joining (the board is already up from the self-proof):** "YOU, now: four of you, each with a pad paired to the onn.
  On the board's opening screen, each of you in turn — first pad, second, third, fourth — hold any button until your
  place fills and your character comes in. Left / right changes your character. The first player picks the board
  (Witch Hill), the rules and **4 rounds** with up / down and left / right. Then each of you press ✕ to say you are
  ready (○ takes it back); the game starts when all four are. Tell me 'started'."
- **On "started":** "YOU, now: play. Two things send the TV to a game on the hub. **A duel** (a duel space or a sword):
  the two in it see one card, T88, picked by the one who started the duel. **A round's end:** all four see one card,
  T89, picked by the last-placed player. Then a load screen shows everyone's standing while the game gets ready: each
  player about to play presses ✕ when ready (○ takes it back), and **△ asks for a practice. A band at the top of the
  TV says 'PRACTICE — press Start to go back'. Anyone's Start ends it (or it ends after about 90 seconds) and you are
  back on the load screen.** Please practise at least once in each game. In a practice or a real game every character
  is there to pick. **While T88 or T89 is on, don't choose SAVE or LOAD on the onn's bar** (it would say no anyway).
  The picture holds still for a second or two each time the TV changes over. After each real game the board shows who
  won; the winner presses ✕. After each one, tell me in one line: for a duel, who won and whom the board gave the win
  to; for a round's end, the Place row as T89's results screen showed it (1P 2P 3P 4P) and how the board paid the four
  of you; and if any character showed as locked."
- **Once, after the first round's end:** "YOU, now: press Home on the onn's remote, wait five seconds, then open
  PrivyHub and choose RESUME. Tell me when the board is back."
- **The per-mini-game reply:** A first says the hub's own `minigame_ended` row (class, scores or places, seats), then
  compares with the user's words and the board's log line `scores … for seats …`; a disagreement is recorded as it
  stands.
- **The plan:** at least one practice in each title; one duel and two rounds' ends. A duel is not forced. If none has
  come by the end of round 3: "YOU, now: in the options (pause), set the rounds to 6 and play on." Still none at 40 min
  → D is "not reached" (recorded; not met).
- **END:** "YOU, now: press END on the onn's bar. Tell me 'ended'."
- **"stuck"** (any user line): B125's — `party-minigame-result`, `status` and the last rows recorded, that step not met;
  "YOU, now: press Home, then RESUME" once; still stuck → the close.

### Pre-registered cells (hashed before part 1) — nothing perceptual

- **J — joining:** four players on the board (the board's log); after the first mini game's start, its `minigame_start`
  `"players"` and seats from the four pads.
- **D — each duel:** one card (`cards 1, chose 0`); `minigame_start` `"players": 2`; ready, PAUSED, no
  `minigame_reloaded`; `minigame_ended` end_P1 / end_P2 with its scores; the board's `scores … for seats …` the same.
- **X — each round's end (two):** one card; `"players": 4`; ready, PAUSED, no reload; `minigame_ended` with `places`
  and `scores` (`places_to_scores` [4, 3, 2, 1]); the board's line the same seats.
- **PR — the practices:** **the band's words in each practice's encoder argv and in no other** (`… | grep -a '^encoder
  argv:' | grep -c 'PRACTICE — press Start to go back'` = the number of practices); `minigame_practice_end` `"by":
  "start_button"` or `"time"`; no `minigame_ended` inside; **`load screen again` in the board's log once per practice**;
  `minigame_ready` `"after_practice": true` before the next go.
- **S** over every read switch of the sitting (above); the listed ones named.
- **L — the board's log against the hub's rows:** in order, for each mini game: `cards 1, chose 0`, then one `practice`
  / `load screen again` pair per practice, then `start`, then `scores …` — each go matching a `minigame_go` row (with
  `"practice": true` for a practice). `grep -h 'PrivyParty: hub mini game:' "$(ls -t logs/games/*-party.log | head -1)"`.
  No name in any line.
- **C — the cheat setups at every launch:** every `minigame_launch` `"cheat": true, "profile_matches": true`; every
  `watching` `"begin": "setup"`; the two keys `"false"` after every party launch.
- **F — PAUSED and no reload at every held read:** the paused proof `PAUSED` every second from each `minigame_watch` row
  to its go; no `minigame_reloaded` anywhere.
- **H — Home / RESUME once:** taken (`minigame_taken` `home`, `resume_start`, `resume_ready` if inside a mini game, or
  the board paused / resumed), the board back.
- **E — END:** the board quit (F10, exit 0), nothing running, `status` idle.
- **U — files:** every file of stage 1's 7 before = after (every sha256) but the setups' **in-game saves, recorded
  before and after, not a cell**; no `.state8`.
- **B148:** the `board_import` row (or its absence) at each launch of the board, as part 1 (b) reads it.
- **MET = part 1, the self-proof's S, and J, D, X, PR, S, L, C, F, H, E, U.** Recorded, no bar: each `prepare_s`,
  `held_s`, `mute_ms`, `frames`; each switch's `seconds`; the users' words on the band and the sound (asked once at the
  END: "YOU, now: in one line each — was the practice band easy to read and fully on the screen? how was the sound
  across the changes?").

### The close

The board quit (if not already); A's watchers stopped; both drop-ins removed; daemon-reload; the companion restarted (no
SIGKILL); **eighteen** lines, `--check` as at stage 1; `party-minigames` → 400 and `bench-release` → 400; nothing
running; every file before = after (U); the rules folder and the board's repo as found (`git -C "$BOARD" status --short`
→ 0 lines). **The record:** `evidence/PP_H4_<the UTC date>.md` + `pph4_<the UTC date>/` — `pre/` (STAGE1.md,
before.txt, code_checks.txt, board_repo_before.txt with HEAD and the changed names, import_needed.txt,
check_before.json), `part1/` (PART1.md, checks.txt), `selfproof/` (SELFPROOF.md, its rows, its heartbeat rows), `part2/`
(cells.md, `sound.md` + `heartbeat_audio.tsv`, `banner.md`, `board_log.md`, `lines.md` — the users' lines verbatim,
the titles and names replaced — `places.md`, `load_screens.md`, `party_rows.txt` with ids dropped, `proof.tsv`),
`close/` (CLOSE.md, after.txt), `preregistration.md` + `.sha256`, title / redact / name checks, `manifest.sha256`.
`KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §PrivyParty (one paragraph); `logs/pph4_git_status.txt`;
`CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action).

**The last reply begins "YOU, now: commit"**, then one line each: part 1 (and B148's row); the self-proof and its S;
joining; each duel (the hub's row, the user's words, the board's credit); each round's end (places, the payout); each
practice (how it ended, the band, `load screen again`); S over the sitting (read / listed); Home / RESUME; END; the
users' words on the band and the sound; files before = after and which in-game saves changed; MET / NOT MET; the eighteen
lines.

## Files

B147: `companion/native_stream.py`, `tests/b147_party_band_inside/` (new), `tests/b144_party_practice_banner/test_b144.py`;
B148: `companion/party_session.py`, `companion/games/emulator_manager.py`, `tests/b148_party_board_prepared/` (new);
B149: `tests/b111_party_board/test_b111.py` and, in the board's repo, `minigames/hub_minigame.gd`,
`checks/hub_minigame_check.gd`; `evidence/B147_…`, `B148_…`, `B149_…` + their folders (`b147.diff`, `b148.diff`,
`b149.diff` — apply in that order on `1052fe82`; `b149_board.diff` on the board's `32d5329`), `patches/B147_…`,
`B148_…`, `B149_…`. Then `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph inserted after
queue AX's), `logs/b147_|b148_|b149_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue AY's B147-B150). **The board's repo** — `git add
minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m "Hub mini game: a practice that came and went
unseen, the load screen again; its check"`.
