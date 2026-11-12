# SESSION B — done, 2026-11-12 AM (QUEUE_2026-11-12AM: B102 the end-screen learner, B103 the mini game's start and result behind PRIVYHUB_H7=1; run 15:36Z-16:34Z)

- **Baseline:** `8b43a266` (H7-V1 committed). **Checked first:** only the companion and `privyhub-diag` active;
  `git status --short` = the prompt file modified and this queue untracked (the prompt files; not touched).
- **Not done:** nothing committed or adopted; no companion or keeper restart (B103's routes exist only after one with
  the flag), no stream, no adb, no sudo, no nft, the Opal not touched; `privyhub-diag` and `~/privyhub_diag/` untouched;
  nothing fetched (Pillow and numpy are the hub's own Debian packages); nothing written to the drive; **the kept H7
  folder, the rules folder and A's working folders not opened; H7-V1's frames and Cowork's labels read only** (no file
  written beside them; no spec kept); no real title started. Nothing deleted but B's own scratch under
  `~/.cache/b_q25am_tmp/` (the leftovers of two runs B stopped itself) and B's own snapshot's `companion/` (refreshed).
- **RetroArch was run by B, headless, on synthetic fixtures only** (B61's form: B94's PS-X EXE and SNES ROM; temp
  folders under `~/.cache`; the companion's display) — B103's settle, twice. B103's tests use B101's fake. **Counted by
  process: 0 after each settle run and after every batch.**

## What was found and built

| Item | Found | Built | Tests | Mutations |
| --- | --- | --- | --- | --- |
| **B102** | on the user's game's frames (H7-V1's, Cowork's labels), learnt on the first half of each range: **the second halves read 576 / 576 right — start, the P1 end, the P2 end told apart (gaps ~51 grey levels), 0 fight frames read as the screen**; the screen mask 16,498 px (85.9 %), **the outcome mask 124 px — one patch, where the tally sits, found by the tool**; a read 1.0 ms, a learn 1.6 s; without a search 2-4 px of misalignment breaks the read; **with the search, shifts to 8 px and rescales 0.95-1.08 read right; every miss in every moved case reads `unknown`, never the other side; never a fight as the screen** | `tools/h7_endscreen.py` — learn / read / `Ended` (K = 3) / score; the spec = a small JSON + one `.npz`; the learn report with a verdict per class | 16 (synthetic: still panel, moving banner, varying portrait, seven-segment tally) × 3 | 11 / 11 |
| **B103** | the cheapest picture once a second: **the window read in process — 12 ms, no frame lost, nothing written**; ffmpeg one-shot 168-200 ms and ~80 ms CPU a picture; **RetroArch's own screenshot lost 120 PS1 frames a minute** (none on SNES) and writes a PNG each time | `POST /plugins/games/h7-start[?load=0]` (B101's load step alone, then the watcher) and `GET /plugins/games/h7-result` (`no_game` / `no_spec` / `idle` / `watching` / `ended` + the class) behind `PRIVYHUB_H7=1`; the watcher sends nothing to the game; `logs/games/h7_results.jsonl` | 13 × 3 (+ B99 15, B101 14, B102 16, contract 5, b90 10 in the same copy) | 11 / 11 |

**One line for the user:** with the test switch on, the hub can now put your game's mini game at its start and then
watch the game's own screen; when the match ends back on the select screen with the tally raised, it says which side
won, within about three seconds, without anyone telling it.

**On your game's real frames:** the start and the two ends are told apart (576 / 576 held-out frames right), and **0
fight frames were read as the select screen** — in the plain read and in every shifted / rescaled case.

## What I would change (not done — the queue is the task)

1. **A half-pixel step in the search** (27 more candidates, ~30 ms): the only misses on moved pictures (a diagonal
   −6 / +5 px, ±3 %) are frames read half a step off; they read `unknown` (a delay, never a wrong side), but a finer step
   would read them.
2. **Re-learn the spec from H7-V2's own pictures** (the stream's window, other characters, a mirror match) beside
   H7-V1's: the screen mask then drops the portraits by itself, and the read no longer leans on the median for them.
3. **Four players:** a class per placement pattern grows fast (24 orders); the labels should name each place's outcome
   and the learner find **one patch per place** — the tool's masks extend to that, the labels' form does not yet.
4. **`idle`** was added to the result's states (a game and its spec, no watch) — the queue's four do not name it.
5. With the flag on, the companion holds numpy and the learner after the first start (~tens of MB); off, nothing.
6. The end is said ~3 s after the select screen returns (K = 3 at one read a second); K = 2 would halve it — the real
   frames' gaps would allow it, but one live check first.

## A — H7-V2, three matches judged by the game's own end screen (attended, ~10 min at the TV)

The user with the onn and two pads paired to the onn over Bluetooth, as always; **nothing asked of the user on the
hub**; every message to the user starts **"YOU, now:"** and is **a complete step** — the screen, the entry, the
button — naming **only choices the onn will offer**, read from the hub at stage 1. The game = H7-V1's game (HOME-12V's
2-player PS1 title). No title, character name, game id or path in any record.

### Stage 1 — unattended

1. **Preconditions:** HEAD with queue AM committed and the tree clean (else "YOU, now: commit queue AM first"); only the
   companion and `privyhub-diag`; no game running (`curl -s http://127.0.0.1:8765/plugins/games/status` →
   `"active": false`); outside 04:30-05:30Z; eighteen `PRIVYHUB_` lines, `--check` ok.
2. **The game's spec, learnt from H7-V1's frames with Cowork's labels** (H7-V1's record names the frames folder and the
   labels file; read only): `python3 tools/h7_endscreen.py learn <H7-V1's frames folder for the game> <Cowork's labels
   file> ~/privyhub_h7/rules/<the hub's id>.endscreen.json` — **all frames** (no `--half`); the printed report kept:
   every class **"separable"**, the screen "separable", `usable` true. Then `python3 tools/h7_endscreen.py score <the same
   folder> <the same labels> ~/privyhub_h7/rules/<the hub's id>.endscreen.json` → every class right, **
   `other_read_as_screen` 0**. Both files' sha256 recorded (`.endscreen.json`, `.endscreen.npz`).
3. **The kept start:** the game's kept **"begin"** state at `~/privyhub_h7/rules/<the hub's id>.state` (sha256 = the
   kept file's; copy it from the kept H7 folder if it is not there). B99's `<id>.json` may stay (B103 never reads it).
4. **The bench flag for the sitting only:** `evidence/b99_2026-11-11/b99-h7-live-read.conf` exactly as B wrote it →
   `~/.config/systemd/user/privyhub-companion.service.d/`; `systemctl --user daemon-reload`;
   `systemctl --user restart privyhub-companion`; its MainPID owns 8765; **nineteen** lines (`--check` not ok on the
   environ only — the bench flag, named).
5. **Both routes answering:** `curl -s http://127.0.0.1:8765/plugins/games/h7-result` → `{"ok": true, "state":
   "no_game"}`; `curl -s -X POST http://127.0.0.1:8765/plugins/games/h7-start` → 400 `"error": "no game is running"`.
6. **What the onn will offer, from the hub's own state** (as H7-L2's `pre/onn_offers.md`; written into the lines
   below before stage 2): `continue_available` for the game (`GET /plugins/games/details?id=<id>`; the start box is
   Start Fresh · Load Save · Extras without it, with Continue when it is true — the line says **Start Fresh** either way);
   the PlayStation entry's exact name (`GET /plugins/games/systems`, `games_system_ps1`); the game's place in that list
   (`games?system=ps1`'s order, the 3-column grid: Down / Right presses from the first tile); the pads' class from the
   recovery log's `pad_slots` rows (Sony → "hold ✕"); the join lines "Hold any button to join", "P1 joined — hold to add
   Player 2".
7. **Before:** the game's slot files and every other game's saves (count and sha256); the stream marks (bitrate rows,
   recovery log, `launch_orphaned`) as H7-L1's; no `.state8` anywhere.
8. **Watchers (read-only, once a second, from stage 2's start):**
   `while :; do printf '%s ' "$(date -u +%FT%T.%3NZ)"; curl -s -m 2 http://127.0.0.1:8765/plugins/games/h7-result; echo; sleep 1; done >> $W/h7_result_watch.txt`;
   and **the picture keeper**: once a second while the game runs, the game's window (the companion's display; the
   RetroArch process's largest visible window by `xdotool search --onlyvisible --pid`, `getwindowgeometry --shell`;
   Pillow's `ImageGrab.grab(bbox=…, xdisplay=":0")`) saved as JPEG (quality 90) with `seconds,file` in an `index.csv`,
   under `runtime/h7_frames/` in a new run folder (git-ignored — `git check-ignore` before the first file; outside git;
   for later learning). It costs ~12 ms a picture (B103's settle) and writes only there.
9. **Pre-registration hashed** (below) before stage 2.

### Stage 2 — the user (the lines, filled in at stage 1)

- **"YOU, now: on the onn's PrivyHub home, open Games, then [the PlayStation entry's exact name]. From the first tile
  press Down [n] times and Right [m] times to reach the game, and press OK. In the box that opens choose 'Launch on
  Companion' and press OK. In the box 'Start [the game]' choose 'Start Fresh' and press OK. When the game's picture
  shows 'Hold any button to join' at the bottom, hold ✕ on the first pad until 'P1 joined — hold to add Player 2'
  shows, then hold ✕ on the second pad until Player 2 has joined. Then tell me 'ready' — any screen of the game is
  fine."**
- **Match 1.** A: `curl -s -X POST http://127.0.0.1:8765/plugins/games/h7-start` → `{"ok": true, "watch": "started",
  "game": "<id>", "loaded": true, "load_line_ms": …}`; `h7-result` → `"state": "watching"`, `"seen_start": true`.
  **"YOU, now: the character select screen is on the TV with the score at 00 – 00. Each of you pick a character — not
  the two you played in the saved fights — and confirm. Play one normal match to its end, until the game is back on this
  select screen. Player 1 should win this one. Don't tell me anything yet."**
- When the watcher shows `"state": "ended"`: **"YOU, now: the hub says the match is over and [Player 1 — the left
  side / Player 2 — the right side] won. Tell me in one line who won."** (`end_P1` → Player 1, the left side; `end_P2`
  → Player 2, the right side.)
- **Match 2.** A calls `h7-start` again (the select screen back at 00 – 00). **"YOU, now: the select screen is back
  with the score at 00 – 00. Pick two different characters again — not the ones from match 1 if you can — and play one
  match to its end. Player 2 should win this one."** → the same lines.
- **Match 3.** A calls `h7-start` again. **"YOU, now: the select screen is back at 00 – 00. This time both of you pick
  the same character, and play one match to its end — either of you may win."** → the same lines.
- **"YOU, now: press Home on the first pad (the bar RESUME PLAYING · SAVE · LOAD · END appears), move to END and
  press OK."** (the game stops; `h7-result` → `no_game`.)

**Pre-registered (hashed before stage 2):** in **all three matches** `h7-result` says `ended` with **the side the user
names** (`end_P1` = Player 1, `end_P2` = Player 2); **`ended` within a few seconds of the select screen returning**
(≤ 8 s from the first kept picture showing the select screen after the fight to the `ended` row) and **never during a
fight** (no `ended` row while the kept pictures show the fight; `seen_start` true from the start); `unknown` reads are
recorded, not failures — **a match whose select screen returns and is not `ended` within 30 s is "not met"** (the
pictures kept; A calls the next start); **the stream's rows as a normal session's** (no stall, orphan or recovery row
caused by the watcher); **the game's slots and every other game's saves before = after**; no `.state8` left. All met →
**MET**.

### The close

Watchers stopped (the picture keeper stops with the game); the drop-in removed; `systemctl --user daemon-reload`; the
companion restarted (MainPID owns 8765); **eighteen** lines, `--check` ok; `curl -s
http://127.0.0.1:8765/plugins/games/h7-result` → 400 `"error": "Unknown Games plugin action: h7-result"` and `curl -s
-X POST http://127.0.0.1:8765/plugins/games/h7-start` → 400 `"error": "Unknown Games plugin POST action: h7-start"`
(both routes gone). The rules folder kept (the spec, its arrays and the state; off the repo; nothing deleted); the kept
pictures stay under `runtime/h7_frames/` (git-ignored).

### The record

`evidence/H7_V2_<date>.md` + `h7v2_<date>/` (`pre/`: HEAD, units, the learn report and score, the spec's two hashes,
the state's hash, the drop-in's hash, nineteen lines, the routes' first answers, `onn_offers.md`, the saves before;
`run/`: the three `h7-start` answers, `h7_results.jsonl`'s rows, the watcher, the picture keeper's counts (pictures,
seconds; no picture), the table — match | the hub's class and `ended_after_s` | seconds from the select screen's return
to `ended` | the user's line (verbatim, a character's name replaced by its label) | met; the stream rows' summary;
`close/`; `preregistration.md` + `.sha256`; title and redact checks; `manifest.sha256`); `logs/h7v2_git_status.txt`. No
title, character name, serial, game id or path; nothing committed.

## Files

`evidence/B102_H7_END_SCREEN_LEARNER_2026-11-12.md` + `b102_2026-11-12/`; `evidence/B103_H7_START_AND_RESULT_2026-11-12.md`
+ `b103_2026-11-12/` (each: the design (+ B102's amendment) + hashes, the diff, tests ×3, mutations, scripts,
`sha256_before_after.txt`, redact / title checks (0 FAILS each), manifest; B102 also the real-frame evaluation's
scripts and numbers, B103 `settle/`); patch notes `patches/B102_H7_END_SCREEN_LEARNER.md`,
`patches/B103_H7_START_AND_RESULT.md`; code `tools/h7_endscreen.py`, `tests/b102_h7_endscreen/`,
`companion/h7_minigame.py`, `companion/plugins/games.py`, `tests/b103_h7_minigame/` (new but `games.py`);
`docs/ROADMAP.md` §H7 and `docs/KNOWN_ISSUES.md` (insertions); `logs/b102_git_status.txt`, `logs/b103_git_status.txt`;
`handoffs/SESSION_B_STATUS.txt`. Left (not deleted): `~/.cache/b_q25am_tmp/` (B's scratch: the evaluation's and
settle's raw outputs, numbers only), `/tmp/b_q25am/` (the snapshot: `companion/`, `tools/`, `tests/`, `PrivyHub/` only).

Written last, 2026-11-12T16:34:01Z, after the status line, the logs and both manifests.
