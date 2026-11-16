# SESSION B — done, 2026-11-16 AN (QUEUE_2026-11-16AN: B104 the reader made independent of tone, B105 the watcher's gaps behind PRIVYHUB_H7=1, B106 A's H7-V3 sketched; run 04:12Z-05:55Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (the prompt files
and queue AN already in HEAD `d61f9b56`, H7-V2 committed in it). `privyhub-diag` and its folder untouched; no stream,
no companion or keeper restart, no adb, no sudo, no nft; nothing fetched (Python with Pillow and numpy, both already
on the hub); nothing written to the drive; the kept H7 folder, the rules folder and A's working folders not opened;
`runtime/h7_frames/` read only; no title started; **no RetroArch run at all** (not needed: synthetic fixtures and the
kept pictures; RetroArch processes left: 0); the `/tmp/b_q26an` copy holds companion/, tools/, tests/, PrivyHub/
(build outputs left out). Nothing adopted; nothing committed; nothing of the user's or A's deleted.

## What was found and built

- **B104 — BUILT** (`evidence/B104_H7_TONE_INDEPENDENT_READ_2026-11-16.md`): `tools/h7_endscreen.py` spec version 2 —
  each picture's pixels **ranked against its own tone over the screen's still part** (τ = 2 % of its contrast), so a
  gain, an offset or any monotone curve changes no reading; the game's picture found inside a window by the tool (the
  window's bars, relative to the picture's darkest, one axis, ≥ 5 %), the same in learn, read, replay and the watcher;
  several sources learnt together; a version-1 spec refused ("learn it again"); `replay`. **On the real pictures:
  0 fights read as the screen in every arrangement. Learnt from H7-V1's screenshots alone: 495 / 508 live pictures
  right** (12 range-edge pictures read `other`, + the one `ignore`); learnt from the live run alone: all 1,152 H7-V1
  frames right; learnt from everything (the spec A will use): every class separable — screen threshold 0.0902, classes
  0.1007 / 0.1032 / 0.0990, margin 0.0929, masks 13,756 / 97 px — everything right but the 12 range-edge pictures
  (`unknown`); across matches (2a / 2b) the classes the data cannot show are "not separable" and read `unknown`, never
  the wrong side; **tone: offsets ±30, gains 0.8-1.2, gammas 0.8-1.25 and every pair of extremes — 0 readings changed**
  (held-out halves, and all live pictures with the screenshot-only spec); B102's alignment cases absorbed as before
  except a 1.08 rescale (the start `unknown`), with 12 px and 0.92 now better; one read 1.4 ms (screenshot) / 4.3 ms
  (window); **replay: `ended` 2.0 s after each select screen returned (K = 3), 1.0 s (K = 2), on the user's sides**.
  Four amendments, each hashed before what it changed — two after runs on the real pictures (kept, disclosed).
  **Tests 19 (+ B102's 16 unchanged), 3 runs green; mutations 14 / 15** (the first run 11 / 15 — four tests added;
  still missed: the median → a mean). **A cost found by a test:** the tone reference is the screen's still part, so a
  flat change over more than ~12-15 % of it is no longer read as the screen (B102: up to half); on the real pictures
  other characters cost ~0.04 and every live screen read.
- **B105 — BUILT** (`evidence/B105_H7_WATCHER_GAPS_2026-11-16.md`), behind `PRIVYHUB_H7=1` (absent / 0 = HEAD's
  answers byte for byte through the real HTTP route, `h7-stop` included): a start over a running watch replaces it (one
  `replaced` row); **`recognised` true / false / null within 8 s of a start with the load** (false = nobody plays);
  `POST /plugins/games/h7-stop`; `h7-start?keep=1` → every picture the watcher reads + `index.csv` (class, distances)
  under the git-ignored `runtime/h7_frames/<game id>_<UTC stamp>/` (~5.3 ms, ~5 ms CPU a picture; a 60-fps fixture's
  frames unchanged); `last` with the thresholds and the spec's version; an old-measure spec → `no_spec` with the plain
  line. B103's test updated only where B105 changes its behaviour (disclosed). **Tests 12, 3 runs green; B103 / B99 /
  B101 / B102 / B104 / the client contract / B90 green; mutations 13 / 13.** A slip of mine (a scripted edit that
  wrote a broken file) seen at once and the file restored from HEAD before anything read it; the batch's background run
  stopped by the 30-min limit during the last mutation — its temp folders removed, the mutation run again (disclosed).
- **What a launch with no client does** (from the code; B106): `POST /plugins/games/launch` from loopback starts the
  game **paused** and does not start the stream (`plugins/games.py:3711, 3725`); `launch_orphaned` fires only when the
  caller hangs up before the answer, the answer comes after 60 s, or it cannot be written (`launch_orphan.py:32-38`,
  `privyhub_service.py:2554-2566`; on unless `PRIVYHUB_CHEAT_STAGED=0`) — a caller that waits for the answer never
  triggers it; **no timer ends a game no client ever joined** (the recovery monitor starts only at
  `native-stream-ready`, and its silence check needs a controller packet first — `link_drop_recovery.py:200-216, 488`,
  `native_session_io.py:2579`); it lives until a Stop, another launch or the companion's exit. `h7-start` needs the
  stream up: `POST /plugins/games/native-stream-start` from loopback starts the capture, encoder and relay sending to
  127.0.0.1 (nobody), `active` true; `native-stream-ready` releases the pause.

## What I would change (not done — the queue is the task)

1. **"Again over the outcome mask", read literally, breaks B102's own test** (an all-bright 0-0 and an all-dark 1-1
   become the same patch); I ranked the outcome against the picture's own screen-mask tone. Consequence for the queue's
   limit test: a whole-picture tone difference is "not separable" (tested), but a tally whose tone alone differs IS
   told apart (tested, stated). I would keep it so.
2. **Labels: leave the range edges out.** Cowork's live labels include the first ~3 s after a launch and the last
   4-5 s before an END (RetroArch's own notice; H7-V1's labels marked those `ignore`). The learner now copes (counted
   as `unlike_label`), but I would mark them `ignore` in future labels.
3. **For a new game, every end class from at least two pairings, or the start and each end in one run** — arrangement
   2 showed an end class seen with only one pair of characters cannot teach the tally; `keep=1` runs of whole matches
   give exactly that.
4. **8 s for `recognised`** is chosen without a live measure of RetroArch's notice after a load; H7-V3 part 1 measures
   it (the `recognised` row's seconds).
5. **An unattended check needs the stream up** (capture + encoder to nobody) because `h7-start` refuses without it; a
   watcher-only mode that does not need the stream would make part 1 lighter. Not built (not asked).
6. **The 1.08 rescale:** a finer scale step in the search would recover it; not needed for H7-V3 (the window's scale
   is fixed and identity).
7. **The 12-15 % limit:** a reference that ignores the still part's portrait areas (learnt from several pairs, as
   arrangement 3 does) keeps it from mattering; a game whose select screen changes more with the characters needs its
   labels from several pairs before its first sitting.
8. **The median → mean mutation is not pinned by a test** (thresholds relearn in either); I would add a real-picture
   regression (a few reduced arrays, not pictures) if pictures may not be in git — not done.
9. **The rules folder's version-1 spec must be learnt again** before any sitting (the watcher refuses it with the
   plain line) — H7-V3 part 1 step 2.

## A — H7-V3 (B106): the live path proved with nobody at the TV, then the sitting

Two parts. **Part 2 is offered only if part 1 is fully met.** The game = T88 (H7-V1's / H7-V2's 2-player PS1 title).
No title, character name, game id, serial or path in any record; no picture in git.

### Part 1 — unattended, no user, no onn (~10 min)

**Stage 1 (pre-registered after it):**

1. **Preconditions:** HEAD with queue AN committed and the tree clean (else stop); only the companion and
   `privyhub-diag`; no game (`curl -s http://127.0.0.1:8765/plugins/games/status` → `"active": false`); eighteen
   `PRIVYHUB_` lines, `--check` ok (adb not needed — no onn in part 1; `--check` not ok on adb alone is noted, not a
   stop).
2. **The spec, learnt B104's way from both sources** (read only; the rules folder as H7-V2's; first move the
   version-1 spec's two files aside, renamed `<id>.endscreen.v1.json` / `.v1.npz` — nothing deleted):
   `python3 tools/h7_endscreen.py learn runtime/h7_frames/t88 runtime/h7_frames/t88/labels.json runtime/h7_frames runtime/h7_frames/h7v2_20261116_run/labels.json <rules folder>/<id>.endscreen.json`
   → the report kept (`pre/learn_report.json`); **expected = B104's arrangement 3**: every class "separable", screen
   threshold **0.0902**, class thresholds **0.1007 / 0.1032 / 0.0990**, margin needed **0.0929**, masks **13,756 / 97
   px**, `unlike_label` **3 / 4 / 5**, `"version": 2`. Then `score` with the same four arguments and the spec → H7-V1
   1,152 / 1,152 right; live 495 / 507 labelled right, the 12 range-edge pictures `unknown`; **`other_read_as_screen`
   0**. Then `python3 tools/h7_endscreen.py replay runtime/h7_frames/h7v2_20261116_run <rules folder>/<id>.endscreen.json --k 3`
   → `ended` end_P1 at 153.0 s and end_P2 at 420.0 s (2.0 s after 151.0 / 418.0). The spec's two sha256 recorded.
3. **The kept states:** the kept "begin" at `<rules folder>/<id>.state` (H7-V2's `361e4007…`); from the kept H7 folder,
   read only, H7-V1's kept **end P1**, **end P2** and the **two mid-fight** states (their sha256 as H7-V1's record).
4. **The bench flag for the task only:** B99's `.conf` byte for byte → the companion's drop-in folder;
   `systemctl --user daemon-reload`; `systemctl --user restart privyhub-companion`; MainPID owns 8765; **nineteen**
   lines (`--check` not ok on the environ only).
5. **The routes:** `h7-result` → `{"ok": true, "state": "no_game"}`; `h7-start` → 400 "no game is running";
   `curl -s -X POST http://127.0.0.1:8765/plugins/games/h7-stop` → `{"ok": true, "watch": "none"}`.
6. **Before:** the saves listing as H7-V2's (161 then; T88's 4; no `.state8`); the marks (bitrate rows, recovery log,
   `launch_orphaned` count); `runtime/h7_frames/` folder list.
7. **Pre-registration hashed** (below).

**Stage 2 — the run:**

8. **Launch with no client** (wait for the answer — no short `--max-time`):
   `curl -s -m 120 -X POST 'http://127.0.0.1:8765/plugins/games/launch?id=<id>'` → 200, the game started **paused**;
   `launch_orphaned` count unchanged. Then `curl -s -X POST http://127.0.0.1:8765/plugins/games/native-stream-start`
   → the stream `active` (to 127.0.0.1, nobody listening); then
   `curl -s -X POST http://127.0.0.1:8765/plugins/games/native-stream-ready` → `"paused": false`. Read the game's
   status every 10 s through part 1: **it must stay running and unpaused** (nothing should end it — see above); if it
   ends, relaunch the same way (the same id; nothing adopted touched) and note it; if it pauses, part 1 stops there
   ("not met: paused with no client").
9. **The start, kept:** `curl -s -X POST 'http://127.0.0.1:8765/plugins/games/h7-start?keep=1'` →
   `{"ok": true, "watch": "started", "loaded": true, "replaced": false, "keep": "<folder>"}`; `h7-result` once a
   second → **`recognised` true within 8 s** (the `recognised` row's `after_s` recorded — it measures RetroArch's
   notice). If false: part 1 NOT MET, stop here (`h7-stop`, then step 15).
10. **The end P1 state brought into the running game — B101's load step by hand** (nothing else loads in part 1):
    the RetroArch command port from the launch's own log row (`network_cmd_port`); the state folder and stem as the
    hub's own `loaded` row's load used them (RetroArch's per-core state folder, the running content's file stem):
    `cp <kept end P1 state> "<state folder>/<stem>.state8"`;
    `python3 -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(2);s.sendto(b'LOAD_STATE_SLOT 8',('127.0.0.1',<port>));print(s.recv(256).decode())"`
    → `LOAD_STATE_SLOT 8`; RetroArch's session log shows `[State] Loading state "…", N bytes.` (N > 0) within 1.5 s;
    then remove the scratch copy `<stem>.state8` (A's own copy, B101's last step). **→ `h7-result` `ended` with
    `end_P1` within 8 s of the load** (the select screen returns at the load).
11. **A new start, then end P2:** `h7-start?keep=1` (the watch had ended: `replaced` false) → `recognised` true within
    8 s; the end P2 state as step 10 → **`ended` with `end_P2` within 8 s**.
12. **The mid-fight states never end it:** for each of the two: `h7-start?keep=1` → `recognised` true; the state as
    step 10; **60 s of reads → `watching`, no `ended`** (`class` `other`).
13. **Stop:** `curl -s -X POST http://127.0.0.1:8765/plugins/games/h7-stop` → `{"watch": "stopped"}`; `h7-result` →
    `idle`; the game's status unchanged (running, unpaused).
14. **Replace:** `h7-start?keep=1`, then within 5 s `h7-start?keep=1` again → the second answer `"replaced": true`;
    one `replaced` row; the second watch `recognised` true; then `h7-stop`.
15. **Stop the game:** `curl -s -X POST http://127.0.0.1:8765/plugins/games/stop`; the stream inactive (else
    `POST /plugins/games/native-stream-stop`); `h7-result` → `no_game`.
16. **After:** the saves listing before = after; no `.state8` anywhere; the keep folders (6 expected) listed with their
    picture counts (git-ignored; `git check-ignore` on one); `logs/games/h7_results.jsonl` rows copied (no titles in
    them — game ids are replaced by `<id>` in the record).

**Pre-registered (hashed before stage 2):** the spec's numbers equal B104's arrangement 3 and its score and replay as
above; `recognised` **true within 8 s at every start** (steps 9, 11, 12 ×2, 14); **`ended` end_P1 (step 10) and
end_P2 (step 11) each within 8 s of its load**; **no `ended` in 60 s after either mid-fight state**; stop → `idle`
with the game untouched; replace → one `replaced` row; the game never paused or ended by the hub during part 1 (or
relaunched once, noted); `launch_orphaned` unchanged; the saves before = after; no `.state8`. **All met → part 1 MET
→ part 2 may be offered.** Anything else → NOT MET, the record, no part 2.

### Part 2 — the sitting (~10 min at the TV; only if part 1 is fully met)

The user with the onn and two pads paired to the onn over Bluetooth, as always; **nothing asked of the user on the
hub**; every message to the user starts **"YOU, now:"** and is a complete step — the screen, the entry, the button —
naming **only what the onn will offer, read from the hub at stage 1** (as H7-V2's `pre/onn_offers.md`: the PlayStation
entry's exact name, the Down / Right presses to the game, `continue_available` → **Start Fresh**, the pads' class →
"hold ✕"). Stage 1 as H7-V2's (adb connect if needed, `--check` ok, the APK read back; the spec from part 1; the flag;
the before listings; pre-registration).

- **"YOU, now: on the onn's PrivyHub home, open Games, then [the PlayStation entry's exact name]. From the first tile
  press Down [n] times and Right [m] times to reach the game, and press OK. In the box that opens choose 'Launch on
  Companion' and press OK. In the box 'Start [the game]' choose 'Start Fresh' and press OK. When the game's picture
  shows 'Hold any button to join' at the bottom, hold ✕ on the first pad until 'P1 joined — hold to add Player 2'
  shows, then hold ✕ on the second pad until Player 2 has joined. Then tell me 'ready' — any screen of the game is
  fine."**
- **On "ready":** A calls `curl -s -X POST 'http://127.0.0.1:8765/plugins/games/h7-start?keep=1'` and reads
  `h7-result` until `recognised` is not null (≤ 10 s). **If it is not true, A stops there:** "YOU, now: the hub can't
  read the game's select screen yet, so we stop here and nobody needs to play. Press Home on the first pad (the bar
  RESUME PLAYING · SAVE · LOAD · END appears), move to END and press OK." — then the close; **nobody plays**.
- **Match 1 (recognised true):** "YOU, now: the character select screen is on the TV with the score at 00 – 00. Each
  of you pick a character — not the two from the saved fights — and confirm. Play one normal match to its end, until
  the game is back on this select screen. Player 1 should win this one. When the select screen is back, tell me
  'back'."
- **On "back":** A reads `h7-result` (it has already decided, or not): `ended` → "YOU, now: the hub says the match
  was over and [Player 1 — the left side / Player 2 — the right side] won. Tell me in one line who won." Not `ended` →
  "YOU, now: the hub did not see the end of that match — tell me in one line who won." (the match recorded not met; the
  next start simply replaces the watch — no relaunch).
- **Match 2:** A calls `h7-start?keep=1` again and reads `recognised` as on "ready" (not true → stop as above).
  "YOU, now: the select screen is back with the score at 00 – 00. Pick two different characters again — not the ones
  from match 1 — and play one match to its end. Player 2 should win this one. Tell me 'back' when the select screen is
  back." → the same.
- **Match 3 (the mirror):** the same start and check. "YOU, now: the select screen is back at 00 – 00. This time both
  of you pick the same character, and play one match to its end — either of you may win. Tell me 'back' when the
  select screen is back." → the same.
- **"YOU, now: press Home on the first pad (the bar RESUME PLAYING · SAVE · LOAD · END appears), move to END and
  press OK."**

**Pre-registered:** `recognised` true at each start before anyone plays; in each match `ended` with the side the user
names, its row **before the user's "back"** and within 8 s of the first kept picture showing the select screen; never
during a fight; the stream's rows as a normal session's; the saves before = after; no `.state8`. All met → **MET**.

### The close (both parts)

`h7-stop`; the watchers stopped; the drop-in removed; `systemctl --user daemon-reload`; the companion restarted
(MainPID owns 8765); **eighteen** lines, `--check` ok; the routes gone: `h7-result` → 400 "Unknown Games plugin action:
h7-result", `h7-start` → 400 "Unknown Games plugin POST action: h7-start", **`h7-stop` → 400 "Unknown Games plugin POST
action: h7-stop"**. The rules folder kept (the version-2 spec, the version-1 one beside it, the state); the kept
pictures stay under `runtime/h7_frames/` (git-ignored) for labelling.

### The record

`evidence/H7_V3_<date>.md` + `h7v3_<date>/`: `pre/` (HEAD, units, the learn report, score and replay, the spec's
hashes, the states' hashes, the drop-in's hash, nineteen lines, the routes' first answers, the saves before, the
marks), `part1/` (the launch, stream and ready answers, the game's status every 10 s, each start / stop / replace
answer, the `h7_results` rows with ids replaced, the load lines' times, the keep folders' counts, `cells.md`: the
pre-registered rows and met / not met), `part2/` (only if run: `onn_offers.md`, the start answers, the `recognised`
reads, the user's lines verbatim, the stream rows, `cells.md`), `close/`, `preregistration.md` + `.sha256` (one per
part), title / redact checks, `manifest.sha256`.

## Files

B104: `tools/h7_endscreen.py`, `tests/b104_h7_tone/`, `evidence/B104_H7_TONE_INDEPENDENT_READ_2026-11-16.md` +
`b104_2026-11-16/`, `patches/B104_H7_TONE_INDEPENDENT_READ.md`. B105: `companion/h7_minigame.py`,
`companion/plugins/games.py`, `tests/b105_h7_watcher/`, `tests/b103_h7_minigame/test_b103.py`,
`evidence/B105_H7_WATCHER_GAPS_2026-11-16.md` + `b105_2026-11-16/`, `patches/B105_H7_WATCHER_GAPS.md`. Then
`docs/KNOWN_ISSUES.md` (one line), `docs/ROADMAP.md` §H7 (one paragraph), `logs/b104_git_status.txt`,
`logs/b105_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.
