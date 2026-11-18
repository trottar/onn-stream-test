# SESSION B — done, 2026-11-18 AW (QUEUE_2026-11-17AW: B139 a clean window for a party title, B140 the paused begin made sure of, B141 Select held from a held title, B142 A's bench re-sketched; run ~00:13Z-01:48Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (H7-V6's record in
`5786cc0c`, H7-D2's and queue AW in `c1a66bc9`; the prompt files tracked and unchanged); the board's repo clean at
`4140949`, not touched. No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or
installed; nothing written to the drive; the users' setups, slots and in-game saves not opened; **read only:** the rules
folder (the two titles' specs and sidecars), `runtime/h7_frames/` (H7-D2's and the other kept runs' pictures), the hub's
`retroarch.cfg` and the virtual pads' autoconfig — offline, numbers only; **no emulator title started** — disclosed:
B61's form, the hub's RetroArch with its N64 core on B137's made-up ROM and its PS1 core on the made-up PS-EXE
(OpenBIOS's animation; no BIOS file), a made-up cheat file for the fixture, temp folders, 25 runs of ~15 s on the hub's
display (00:20Z-00:29Z); Godot headless only (B111's own check, in its scratch copy). No title, serial, game id,
`profile_id`, character name, cheat name or path in any record; no game's name; no picture, crop or reference image in
git. The `/tmp/b_q34aw` copy holds companion/, tools/, tests/, PrivyHub/ (its sources) only. Nothing adopted; nothing
committed in either repo. Deleted: only my own scratch (the probes' folders and grabs, the snapshots, the mutation copies,
my `__pycache__` folders from runs against the repo, the temp dirs older suites leave).

## What was found and built

- **B139 — BUILT** (`evidence/B139_PARTY_CLEAN_WINDOW_2026-11-17.md`). **The settings:** `video_font_enable = "false"`
  in the session config leaves **nothing of RetroArch's on the window** — no notices, no "Paused.", no content banner —
  paused and running, both cores, full screen and 960 × 720 (24 runs); `GET_STATUS`, the command port, the load line and
  the cheat log lines as before; `menu_show_load_content_animation = "false"` removes the banner alone (written too, so
  the banner stays off should a later RetroArch draw it apart); `menu_enable_widgets = "false"` leaves the notices in the
  old font; the `notification_show_*` keys leave all three. **No text left: no mask.** **Why the mask made T88 worse:**
  on H7-D2's own pictures it did not (masked `start` 54 / 54 at 0.0036, unmasked `other` 0.086-0.091 — the label's text
  stops the right bar's cut); the hub's masked reads sit with the boot frame's (0.17-0.27): they were taken before the
  begin was on the window. **Built:** only a launch made by `party-minigame-start` writes the two keys; the users'
  launches byte for byte today with the flags set; the watch reads unmasked. Tests 5 (offline on the hub's own pictures:
  T88 paused 54 / 54 `start`, least margin 0.1851, `other` as the screen 0 in 7 kept runs).
- **B140 — BUILT** (`evidence/B140_PARTY_BEGIN_SHOWN_2026-11-17.md`): a grab before the load; frames after it in steps
  0, 2, 4, 8, 16, 30 (cap 60), each followed by 80 ms and a grab, until the window **moved ≥ 0.20** from the pre-load grab
  (the share of 64 × 48 cells moved > 16 levels: H7-D2 — still 0.0, notices ≤ 0.10, boot → begin ≥ 0.51) or the start
  is read; never → given up at once, "the title did not show its starting point". **Mute: T88 ~0.3-0.4 s; the cap ~3.9
  s.** Tests 3.
- **B141 — BUILT** (`evidence/B141_PARTY_SELECT_HELD_2026-11-17.md`): the pairs Select + L1 (load), R1 (save), Start
  (quit), R3 (pause toggle); from a held title's launch to the go and on every way back, Select cleared from every
  report; from the go on as today. Tests 4.
- **B142 — sketched below (no code).**

Tests (`b139_2026-11-17/tests_x3.txt`, `tests_others.txt`): **B139 5, B140 3, B141 4, B137 10, B133 9, B134 5 — three runs green each, 0 temp dirs** (B139's offline test run against the repo: OK); mutations 4 / 4 (`tests_mutations.txt`); B137's tests updated for B139 (the label test) and B140 (the N64-shaped case: 0 frames); **the earlier suites once, all OK** (41: B129-B131, B127, B124, B114, B115, B110, B112, B123, B122, B108, B105, B103, B102, B104, B101, B99, B65, B61, the player prompt, the players' session, the relaunch, the pad slots ×2, the stall signal / owner, the link recovery, the fast restart, the client contract, the input hold ×2, the keyframe request, the loss rule, impairment, audio codec, B72, PS2, GameCube, N64), **B111 2 with Godot and the board's repo**, art_systems 120 (its doc test against the repo).

## What I would change (not done — the queue is the task)

1. **T89's frames:** B140 finds them on the hub; if T89 needs 30 frames the mute is ~2 s — the board loses the players'
   presses for that long at every T89 load screen. If H7-V6 shows 14-30, a shorter gap between frames (the 20 ms the
   settle saw lose one in five: frames then over-counted, harmless now that the window is measured) would halve it.
2. **The watcher's own pictures for a party watch** (`keep`) cannot be asked for without a code change; a bench word on
   `party-minigame-start` passing `keep=1` to the watch would let A see a miss with the watcher's own eyes.
3. **A practice's go lets Select through** (as the queue says: "from the go on, as today") — in a practice Select + L1 /
   R1 still load / save over the setup's slot; holding Select through practices too would cost nothing (the board
   never uses it, the titles' own menus seldom do).
4. **H7-V6's step 7 (never the start, by hand)** no longer fits the bench: with a clean window the start is read ~1 s
   after the load, before a hand load can land; the tests carry that case (B137, B140).
5. **B137's mask code** stays in `h7_minigame` unused; it could go.
6. From AU / AV, still open: the onn's Home during the load screen gives the mini game up; `announce_minigame` still says
   "On the hub"; the presses before the launch's answer reach the booting title.

## A — H7-V6 again (B138's with B139-B141), then PP-H3c, then PP-H4

As B138's names: T88, T89, "T88's / T89's cheat setup", `H=http://127.0.0.1:8765/plugins/games`, `$RULES`, `TOKEN2` /
`TOKEN4` read at run time, never in a record; a game's name run-time data only. **The paused proof** as B138's
(`GET_STATUS` once a second on the port read from `data/games/retroarch/config/privyhub-input.cfg` after each
`minigame_launch` row; counted from each `minigame_watch` row to its go). **New — each party launch's keys:** right after
each `minigame_launch` row, `grep -E '^(video_font_enable|menu_show_load_content_animation) = '
data/games/retroarch/config/privyhub-session.cfg` → **exactly the two lines, each `"false"`** (the record keeps the two
lines only). **New — the window's pictures for each preparation (no code change):** from each `minigame_launch` row to
its go (or its give-up), once a second, the title's own window grabbed by its id with the stream's own grab — `P=$(curl -s "$H/status" |
python3 -c "import json,sys;print(json.load(sys.stdin)['pid'])"); WID=$(xdotool search --onlyvisible --pid "$P" | tail -1); ffmpeg -hide_banner -loglevel error -f x11grab
-framerate 60 -draw_mouse 0 -window_id "$WID" -i "$DISPLAY" -frames:v 1 -y runtime/h7v6b_frames/<step>_<n>.png` — into the
git-ignored `runtime/h7v6b_frames/` (never in git; looked at only if a preparation misses); beside them the watch's own
reads in `h7_results.jsonl` (`class`, `distances` per read). (The watcher's own pictures for a party watch need a code
change: not asked for.)

### H7-V6 — again, unattended (B112's bench, ~25 min; `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1` for the task only)

**Stage 1 (pre-registered after it):**

1. The window as before. **This repo with queue AW's B139-B141 committed** and clean but for this task's files (else
   stop: "YOU, now: commit queue AW first, then send the read line again"); the code: B138's six `grep`s, and **`grep -c
   'PARTY_SESSION_SETTINGS = {"video_font_enable": "false", "menu_show_load_content_animation": "false"}'
   companion/party_minigame.py` → 1, `grep -c 'party_settings = getattr(self, "_party_session_settings", None)'
   companion/games/emulator_manager.py` → 1, `grep -c "ADVANCE_STEPS = (0, 2, 4, 8, 16, 30)" companion/party_minigame.py` →
   1, `grep -c "def party_hold_select" companion/native_session_io.py` → 1** (else stop and say which). Only the two
   units; no game; eighteen lines, `--check` ok.
2. **The rules folder as H7-V5b left it**, read only (B132's steps 3-6).
3. Both drop-ins; twenty lines. **Before:** every file under the states, saves and cheat setups (count, sha256); no
   `.state8`; the rows' line counts. Pre-registration hashed.

**Stage 2 — by `curl` as the board would:**

4. **The board** launched and released (B128 step 10); **the list** → `[(2, True), (4, True)]` (B138's line).
5. **T88 held:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN2&seats=1,2&bench=1&hold=1"` → `"starting"`; poll
   once a second → `"preparing"` → **`"ready"` within 5 s of the start (expected ~2.5 s; `prepare_s` ~1.3-1.6 s)**;
   **the launch's two keys**; rows `minigame_start` `"hold": true`, `minigame_launch` `"cheat": true, "profile_matches":
   true`, `minigame_watch`, **`minigame_frame_advance` `"changed": true, "paused": true`, `"frames"` (expected 2),
   `"batches"` (2), `"moved"` (≥ 0.20; expected ~0.5), `"mute_ms"` (expected 250-450)**, `minigame_ready` `"prepare_s"` —
   no `minigame_route`, no `minigame_stream` before the go; `h7_results` `watching` with **no `label_mask`**, `"begin":
   "setup"`, `recognised` true **at the first or second read**. Held 180 s, asked once a second → `"ready"`; **the paused
   proof `PAUSED` every second**. **The go** → `"taken"` → `"playing"`; `minigame_go` `"held_s"` ≥ 180; **no
   `minigame_reloaded`**; route; stream `"switched": false` (bench); one read after the go → `PLAYING`. The kept end P1 by
   hand (B128 step 13) → **`end_P1` `[1, 0]`**; the end.
6. **A go before ready, a second go:** `seats=2,1`; at once the go → `"remembered"`; again → `"already"`; → `"playing"`
   by itself (no reload); the kept end P2 → **`end_P2` `[0, 1]`**.
7. **(B138's never-the-start by hand: dropped** — the start is now read ~1 s after the load, before a hand load can land;
   B137's and B140's tests carry it.)
8. **Practices, T88:** as B138's step 8 — a practice by time → `"practices": 1`, **a `minigame_frame_advance` row after
   it (`"changed": true`)**, `minigame_ready` `"after_practice": true`, the paused proof `PAUSED` from that watch row to
   the next go; a second → 2; a real go (no reload) → `end_P1` `[1, 0]`.
9. **T89:** `seats=3,1,4,2` → **`ready` within 6 s (expected ~3-4 s; `prepare_s` ~1.3-2.5 s)**; the two keys; **the
   frame-advance row's `"frames"` recorded — the number T89 needs (0-30 expected; `"mute_ms"` up to ~2 s)**, `"changed":
   true`; the paused proof; one practice by time; a real go → `results_1` by hand while paused (B128 step 17) → **places
   `[1, 2, 3, 4]`, scores `[4, 3, 2, 1]`, seats `[3, 1, 4, 2]`**.
10. **The close** (B128 step 19); **after:** every file of step 3 before = after; the in-game saves recorded; no
    `.state8`.

**Pre-registered:** 4-10 — **each party launch's config: the two keys, `"false"`; `prepare_s` T88 ≤ 5 s, T89 ≤ 6 s; one
frame-advance row per preparation, `"changed": true`, `"paused": true`; `PAUSED` at every read from each watch row to its
go; no `label_mask`; no `minigame_reloaded`; no route, no switch before a go; still `ready` after 180 s; remembered,
already; practices back to `ready` by time with no scores; the real ends as H7-V5b.** MET → PP-H3c may be offered.
**A preparation given up:** "…did not show its starting point" (the window never moved in 60 frames: the pictures show
what it showed) or "…not recognised" (moved, not read: the pictures and the reads' distances) — not met for that title;
B's next queue from them.

### PP-H3c — as B138's, with B139-B141's rows

Preconditions: **H7-V6 (this one) MET**; the rest as B138's (the board's repo at `f8d92e38…` or later with the screens,
my two files `e580c3e1…` / `76018a20…`). Part 1 as B138's, its bench start (e) with H7-V6's step-5 rows (the two keys,
the frame-advance row `"changed": true`, no `label_mask`, the paused proof). The lines unchanged (B138's: △ + ✕ at the
first two load screens, ✕ on both at the third). **The rows per load screen now:** `minigame_launch` (the first only; the
two keys right after it) → `minigame_watch` → **`minigame_frame_advance` (`"frames"`, `"batches"`, `"changed": true`,
`"moved"`, `"mute_ms"`)** → `minigame_ready` → … as B138's; `watching` without `label_mask`. **Cells:** B138's F, R, S,
PS, PT, M, H, E, U, and **W — the window clean:** every party launch's config carries the two keys (nothing perceptual;
the user's line on what the TV showed is recorded, no bar). **Recorded, no bar:** each `prepare_s`, `mute_ms`, `frames`.

### PP-H4 — as B138's, with

- Preconditions: **H7-V6 (this one) MET and PP-H3c MET**; the checks' sha256 as B138's (`76018a20…`); this repo's B139-B141
  `grep`s as H7-V6's step 1.
- The first streamed proof: B138's, with the two keys after its launch and the frame-advance row `"changed": true`.
- Cells: B138's list with **W** added over every mini game of the sitting.

## Files

B139: `companion/games/emulator_manager.py`, `companion/party_minigame.py`, `tests/b139_party_clean_window/` (new),
`tests/b114_party_minigame_hang/b114_scenario.py`, `tests/b137_party_no_press/test_b137.py`; B140:
`companion/party_minigame.py`, `tests/b140_party_begin_shown/` (new), the scenario, B137's test; B141:
`companion/native_session_io.py`, `companion/party_minigame.py`, `tests/b141_party_select_held/` (new), the scenario;
`evidence/B139_…`, `B140_…`, `B141_…` + their folders (`b139.diff`, `b140.diff`, `b141.diff` — apply in that order on
`c1a66bc9`), `patches/B139_…`, `B140_…`, `B141_…`. Then `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md`
(one paragraph inserted after queue AV's), `logs/b139_|b140_|b141_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one
line), this file.

**The user, now:** this repo — commit the tree (queue AW's B139-B142). The board's repo — nothing to commit.
