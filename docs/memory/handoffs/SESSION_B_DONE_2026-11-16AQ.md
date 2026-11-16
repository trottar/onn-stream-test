# SESSION B — done, 2026-11-16 AQ (QUEUE_2026-11-16AQ: B114 the hang, B115 the hand-overs, B116 the board idling, B117 A's PP-H3b sketched; run 20:50Z-21:43Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (no system unit); `git status --short` empty
(PP-H3 committed in `8fa398c8` with queue AQ). `privyhub-diag` and its folder untouched; no stream, no companion or
keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; nothing of A's
opened beyond the PP-H3 record and the read-only logs it names; no emulator title started (the tests' titles are B101's
fake RetroArch); **Godot headless only, always in scratch copies** of the board's repo with its own folders redirected;
no picture anywhere. **The board's repo** (`820673c`): **only my two files edited** (`minigames/hub_minigame.gd`,
`checks/hub_minigame_check.gd`), nothing else, nothing committed there. The `/tmp/b_q28aq` copy holds companion/,
tools/, tests/, PrivyHub/ (its sources: the build outputs left out) only. Nothing adopted; nothing committed in either
repo. Deleted: only my own scratch under `~/.cache/b_q28aq_tmp` (work copies, the tests' temp dirs) — nothing else.

## What was found and built

- **B114 — BUILT** (`evidence/B114_PARTY_MINIGAME_HANG_2026-11-16.md`). **The lock:** the manager's own lock, held by
  the mini game's start across the stream switch; the switch's end (`note_recovery_restart`) waited on **the live
  bitrate controller's lock**, held by a **client-health report** that was waiting in `observe()` → the bitrate
  context → `emulator.status()` for **the manager's lock**. Everything else piled on one of the two (status → the
  manager's lock; native-stream-status and later reports → the bitrate lock; the recovery's stall worker → its pause →
  the manager's lock, so no `desync_pause` row and its give-up 120 s later). **Why match 2 and not match 1:** the
  cycle needs a report inside the ~1.2 s between the start and the stream's own lock, once every 2.0 s — match 1's
  route was 0.23 s clear of the next report, **match 2's route came 12 ms before one** (the bitrate log: no
  `ssrc_change`, no sample after 20:29:17.447Z). The recovery's restart after match 1 only moved the reports' phase.
  **The test** (two mini games back to back through a stubbed live stream with its own lock and a capture that follows
  one process; the onn's client-health, heartbeats and stall datagrams through the real workers; status / result /
  native-stream-status / Home / RESUME / END from other threads; the hub's adopted lines on) **hung on HEAD** — rows
  stopped at `minigame_route`, the start's thread in `note_recovery_restart`, status timing out at 12 s — **and passes
  now** (8 / 8, 3 runs). The fix: no lock across a launch, a stream start or stop, or a wait on another thread; every
  route within 2 s while a mini game is on (status from a snapshot; Home / RESUME / END and the board's end taken at
  once onto the mini game's queue, acted on in order); a start stuck 30 s given up and ended by the hub; END always
  works (starting, playing, either hand-over, a stuck start).
- **B115 — BUILT** (`evidence/B115_PARTY_HANDOVERS_2026-11-16.md`). **The way back:** the route cleared → **the stream
  switched to the board's own window while the title still runs** → then the title stopped → the board's session
  back; the stream never goes down. **Both ways planned:** a window on the recovery from the switch to 3 s after it —
  the client's video stalls / stall ends and desyncs in it are not taken (no `client_stall`, `desync_pause`, stall save,
  `stall_handover_v2`, no key to the board); the bitrate controller told it is no recovery restart (no escalation, no
  step); the controller's silence, a stall that outlasts the window and the recovery's monitor still count. Tests 6
  (3 runs): three mini games back to back, every hand-over switched true and planned, no recovery act, no key, six
  `minigame_switch` SSRC rows and no escalation, a real stall in the match handled as today (the title paused).
- **B116 — BUILT** (`evidence/B116_PARTY_BOARD_IDLE_2026-11-16.md`): the board's script caps `Engine.max_fps` at 10
  while it waits and restores the board's own rate before it calls the hub's end and whenever its gate leaves the tree;
  its check **PASS (34 assertions)** (was 20; three mutations caught). Headless shows it applied and restored on every
  path; the CPU behind the title only the sitting can show.

## What I would change (not done — the queue is the task)

1. **The switch is still a full stream start** (~3.6 s on the host each way; the onn holds the last frame ~4-5.5 s).
   The adopted fast restart (B22 / B24: the new encoder before the old one's teardown, the lock released at its check)
   would cut it to ~1-1.5 s with the same planned window — the next small step before a capture that follows a window.
2. **The 2-s rule is the mini game's, not the hub's:** with no mini game on, a 3-s stream start still holds `status`
   for 3 s (today's code). The cycle B114 broke is general — anyone holding the manager's lock while taking the
   bitrate lock — and the bitrate controller's `observe()` asking the manager for its status under its own lock is the
   other half; reading the game's state before taking the bitrate lock would remove the edge for everything.
3. **The board's end and END answer `pending` when the end takes longer than 1.5 s** (with the real switch it will);
   the board ignores the answer, and the onn only needs a 200 — but a client that wants to wait for the end can poll
   `party-minigame-result` until `closed`.
4. **`tests/input_hold_b8`** fails one assertion on HEAD's own code (1347 ≠ 1348 ms, a rounding edge in a fixed
   timeline) — not touched here; worth its own small item.
5. **Home during the hand-over back:** Home is taken in order after the end, so it stops the board's stream; that is
   right, but the onn will show the board's last frame under its bar — fine, noted for PP-H3b's Home cell.

## A — PP-H3b, PP-H3 again with the fixes (B117; part 1 on the bench, then — only if part 1 is fully met — the sitting)

T88 = H7's 2-player PS1 title. No title, character name, game id, serial or path in any record; no picture in git.
**As PP-H3** (its task `handoffs/PP-H3_MINIGAME_FROM_THE_BOARD_TASK.md` and its eight changes, B113's steps in
`SESSION_B_DONE_2026-11-16AP.md`), with these differences.

### Stage 1 (pre-registered after it)

As PP-H3's: this repo's HEAD **with queue AQ committed** (B114 / B115 / B116 in it; else stop: "YOU, now: commit
queue AQ first, then send the read line again"); **the board's repo with B116's two files committed** (`git -C <board
repo> log -1 --format=%h -- minigames/hub_minigame.gd` newer than `820673c`, `sha256sum` = `4706a28b…` and
`c09036b7…`; else stop: "YOU, now: commit the board's two files first, then send the read line again"); only the two
units; eighteen lines; adb up, `--check` ok, the APK `ca53df0d…` CONFIRMED; the sidecar and the board's config as
PP-H3; both drop-ins; the companion restarted, MainPID serving; **twenty** lines; the onn's offers read (as PP-H3's
`onn_offers.md`); before: the saves (count and hashes, no `.state8`), the pictures, both repos, the party log's,
bitrate log's and recovery log's line marks, `launch_orphaned`. **The route watcher** (loopback; runs from part 1's
start to the close; A's own timings):

```
python3 -u - > <dir>/route_watch.tsv <<'EOF'
import time, urllib.request
H = "http://127.0.0.1:8765/plugins/games"
print("utc\troute\tseconds\tok", flush=True)
while True:
    for name, path in (("status", "/status"), ("result", "/party-minigame-result"), ("ns_status", "/native-stream-status")):
        t = time.monotonic()
        try:
            urllib.request.urlopen(H + path, timeout=10).read(); ok = 1
        except Exception:
            ok = 0
        print(f"{time.strftime('%H:%M:%S', time.gmtime())}\t{name}\t{time.monotonic() - t:.3f}\t{ok}", flush=True)
    time.sleep(0.5)
EOF
```

and PP-H3's status watch (once a second, with `godot_cpu` / `retroarch_cpu`), `tail -F logs/games/party.jsonl`, the
board's own log, the recovery log.

### Part 1 — unattended, the bench (`H=http://127.0.0.1:8765/plugins/games`)

B113's steps 6-11 and 13 as PP-H3 ran them (step 12 not run), then:

- **P11b — two mini games back to back with the concurrent calls** (the watcher running): seats 1,2
  (`curl -s -X POST "$H/party-minigame-start?id=$TOKEN&seats=1,2&bench=1"`) → `playing`; the kept end P1 state by hand
  → `ended` `end_P1` [1, 0]; **at once** `curl -s -m 5 -X POST "$H/party-minigame-end"` → `"ended": true` within 2 s;
  **at once** seats 2,1 → `playing`; during it **Home**: `curl -s -m 5 -X POST "$H/native-stream-stop"` → 200 with
  `"taken": "home"` within 2 s, the status `paused` true (the title paused, no board key); `curl -s -X POST
  "$H/bench-release"` → released; the kept end P2 state → `ended` `end_P2` [0, 1]; the end → `"ended": true`. Rows:
  `minigame_taken` for each end and Home; `minigame_stream` "the stream is not up" (the bench: no switch).
- **P13** (the board's script headless against the live hub) as PP-H3 → its draw line and `DRIVER [0, 0]`.
- **P14b — END during a mini game** (replaces P14): seats 1,2 → `playing` → `curl -s -m 5 -X POST "$H/stop"` →
  200 `"taken": "end"` within 2 s → RetroArch gone (`pgrep -f RetroArch` empty) within 10 s, the party rows
  `minigame_given_up` "ended from the onn", `minigame_end` "onn", `quit`, `exited` **code 0**; `curl -s "$H/status"` →
  `active` false.
- **P15** as PP-H3 (the saves before = after, no `.state8`, the pictures).

**Pre-registered (part 1):** as PP-H3's, plus **every line of `route_watch.tsv` from part 1's start: `ok` 1 and
`seconds` < 2.0** (the maximum per route recorded), P11b's two results [1, 0] / [0, 1], Home taken and the title paused,
P14b's END taken, the title and the board gone, exit code 0. (On the bench there is no stream, so the switch — the hang's
other half — is not run here; part 1 shows the routes stay answered and the calls are taken in order; the sitting proves
the switch.) **All met → part 2 may be offered.**

### Part 2 — the sitting (~15 min; the user with the onn and two pads paired to the onn over Bluetooth, as always)

Every message starts **"YOU, now:"**, is a complete step, and names only what the onn offers (stage 1's read); A never
holds a turn while the user plays. Lines (PP-H3's, with the third match and the END match added; ✕ = confirm, the
board's draw sentence from stage 1):

- **First:** PP-H3's launch-and-join line ("…open Games, then 'PrivyParty (1)', press OK on its one game, 'Launch on
  Companion' and OK, then 'Start Fresh' and OK. When 'Hold any button to join' shows, hold ✕ on the first pad for about
  two seconds — until the board shows a first player — then the same on the second pad. Then tell me 'ready'.").
- **On "ready":** "YOU, now: start a game in the board's lobby — ✕ on the first pad — and play on. [The board's draw.]
  When the TV changes to [the game]'s character select screen with the score at 00 – 00, each of you pick a character
  and confirm, and play one match to its end — Player 1 should win. The picture holds still for a few seconds each time
  the TV changes over; that is expected, and the board comes back by itself. When it is back, tell me in one line who
  won the match and whom the board gave the win to."
- **On that line:** "YOU, now: play on in the board until the TV changes to [the game] again; pick characters and play
  one match — Player 2 should win. When the board is back, tell me in one line who won and whom the board gave the win
  to."
- **On that line:** "YOU, now: play on until the TV changes to [the game] a third time; pick characters and play one
  match — Player 1 should win. Once during this match press Home on the first pad (the bar RESUME PLAYING · SAVE · LOAD ·
  END appears), then choose RESUME PLAYING and press OK; when 'Hold any button to join' shows again, hold ✕ on each pad
  until it clears, and play on to the end. When the board is back, tell me in one line who won and whom the board gave
  the win to."
- **On that line:** "YOU, now: play on until the TV changes to [the game] once more. When its character select screen
  shows, press Home on the first pad, move to END and press OK. Tell me 'ended'."
- **"stuck"** (the picture frozen more than ten seconds, the pads not driving the match, the board not coming back):
  A reads `party-minigame-result` and `status` (both answer within 2 s now) and says in one plain sentence what the hub
  shows, then: **a mini game on** → `curl -s -m 5 -X POST "$H/party-minigame-end"` (taken at once; the board gets a draw;
  the stream switches back) and "YOU, now: the board is back on the TV — that mini game counts as a draw. Play on in the
  board, and tell me when the TV changes to [the game] again."; **no mini game on and the board not back** → "YOU, now:
  press Home on the first pad, move to END and press OK. Tell me 'ended'." (END now always works); **the bar does not
  come within ten seconds** → "YOU, now: leave the game from the onn's own top bar, then tell me 'left'." and the close.
  Every "stuck" recorded; the match it happened in is "not met".
- **"close":** the END step if a game is running, then the close.

**Pre-registered, nothing perceptual (hashed before the first line):**

- **M1, M2, M3 — the result:** each match's `minigame_ended` names the class and scores that make **the user's winner**
  the winner, **and the board's own log credits that seat** ("PrivyParty: hub mini game: scores [..] for seats ..");
  the user's lines verbatim.
- **X — every hand-over planned, both ways, in all four mini games:** two `minigame_stream` rows per mini game
  `"switched": true, "planned": true` (window minigame, then board; END's has only the first) and a
  `minigame_switch_window` row for each; between each `minigame_start` and `minigame_end` **no recovery row that acts**
  (`client_stall`, `desync_pause`, `stall_handover_v2`, `encoder_restart`, `resumed`, `gave_up_saved`; M3's Home /
  RESUME bring only `session_ended` / `session_started`), **no board key row** (`pause` / `resume` / `quit` — but END's
  own `quit`), **no bitrate step** (no `escalation_armed`, no `transition` in the bitrate log), no new
  `launch_orphaned`. **Recorded, no bar:** each switch's `seconds`, each window's stalls not taken, from `ended` to the
  board's first frame (the stream rows), what the client reported.
- **R — every route within 2 s throughout:** every `route_watch.tsv` line from the read line to the close `ok` 1 and
  `seconds` < 2.0 (the maximum per route and per stretch recorded).
- **H — Home / RESUME in M3:** `minigame_taken` home → the status `paused` true (the title's pause; no board key), then
  `minigame_taken` resume_start / resume_ready → `paused` false; the match then ends with its result.
- **E — END during a hub mini game** (the title on the TV): `minigame_given_up` "ended from the onn" and `minigame_taken` "end"
  → `minigame_title_stopped` → `minigame_end` "onn" → the board's `quit` and `exited` **code 0**; RetroArch gone
  (`pgrep -f RetroArch` empty within 10 s; its own exit as the title's game log ends it, or "killed" if the hub had to);
  `status` → `active` false; no board, Godot or RetroArch process left.
- **C — Godot's CPU behind the title recorded** (the status watch's median `godot_cpu` while each `minigame_playing`
  stood; PP-H3: 98 %; no bar).
- **U — nothing of the user's touched:** the saves before = after (count and hashes), no `.state8`; the pictures
  unchanged; the board repo's status after = before.
- **MET** = part 1 met and M1, M2, M3, X, R, H, E, U met.

### The close (both parts)

As PP-H3's: the watchers stopped; **both drop-ins removed**; daemon-reload; the companion restarted (MainPID serving —
**no SIGKILL in its journal**, recorded); **eighteen** lines, `--check` ok; the routes gone (`party-minigames` → 400
"Unknown Games plugin action: party-minigames"; `bench-release` → 400 "Unknown Games plugin POST action:
bench-release"); the board's entry gone; no board, Godot or RetroArch process left; the keeper not restarted; the drive
before = after; no profile changed. The record `evidence/PP_H3B_<date>.md` + `pph3b_<date>/` in PP-H3's shape (`pre/`,
`part1/` with `route_watch.tsv`, `part2/` with `route_watch.tsv`, `close/`), the pre-registrations and their hashes,
title / redact checks, manifest. The last reply begins "YOU, now: commit".

## Files

B114: `companion/party_minigame.py`, `companion/plugins/games.py`, `tests/b114_party_minigame_hang/`, `evidence/B114_…`
+ `b114_2026-11-16/`, `patches/B114_PARTY_MINIGAME_HANG.md`. B115: `companion/party_minigame.py`,
`companion/stall_signal.py`, `companion/plugins/games.py`, `tests/b115_party_handovers/`, `evidence/B115_…` +
`b115_2026-11-16/`, `patches/B115_PARTY_HANDOVERS.md`. B116: the board's `minigames/hub_minigame.gd` and
`checks/hub_minigame_check.gd` (uncommitted there), `tests/b111_party_board/test_b111.py`, `evidence/B116_…` +
`b116_2026-11-16/`, `patches/B116_PARTY_BOARD_IDLE.md`. Then `docs/KNOWN_ISSUES.md` (one line inserted),
`docs/ROADMAP.md` (one paragraph inserted after PP-H3's), `logs/b114_|b115_|b116_git_status.txt`,
`handoffs/SESSION_B_STATUS.txt`, this file.

**The user, now:** this repo — commit the tree (queue AQ's B114-B117); the board's repo — `git add
minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m "Hub mini game: the board draws at 10 fps while
the hub's game is on the TV, with its check"`.
