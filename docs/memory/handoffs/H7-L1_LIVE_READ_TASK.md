---
memory_schema: 1
as_of: 2026-11-11
status: TASK HANDOFF — H7-L1, the live read beside the user's own eyes (session A, hardware, attended ~10 min; ONE sitting at the TV, the user with the onn and the pads paired to the onn over Bluetooth as always; nothing asked on the hub; the stages move on the user's lines; every reply begins "YOU, now:"). B99's read behind the bench flag `PRIVYHUB_H7=1` for the sitting only (nineteen lines, back to eighteen at the close). The user plays T88's 2-player fight; at each pause the user says who is ahead and the hub's read at that second is set beside it. Pre-registered. Nothing adopted; nothing committed
---

# H7-L1 — does the hub read who is ahead in a fight that is being played?

Read first: `SESSION_B_DONE_2026-11-11AK.md` §"A — H7-L1" (**stage 1's steps, the watcher, the fight's replies, the pre-registered rule, the close and the record's shape are B's — use them exactly**, with the additions below), `B99_H7_LIVE_READ_2026-11-11.md` (the route; what it sends — status and memory reads only; the 0.6 s bound; the floor; the `h7_reads` log; "the hub launches a game paused"), `H7_P3_2026-11-11.md` (the rule; the five saves' values; A's caveat: the leader sat at exactly 140 in all four), `docs/ROADMAP.md` §H7, `docs/memory/CURRENT.md`.

**T88** = HOME-12V's 2-player PS1 title; A names it to the user in replies only. No title, character name, cheat name, serial, game id or path in any record; a character the user names in a line is replaced by its label.

**Additions to B's sketch (Cowork's):**

1. **The fight starts from Continue — a first check that costs nothing.** T88's Continue copy is the user's last save: mid-fight, player 2 ahead (H7-P3: equal by hash to the kept `end_p2_b` copy, which read 110 / 140). A confirms at stage 1 that the Continue copy still has that hash. The user starts T88 **with player 2 joined as usual and picks Continue**: the read at the start must be **110 / 140 → P2** (pre-registered; not independent — it is a save the search used — but it is the first read ever through the live path on the real title). If the Continue copy's hash has changed, or the onn offers no Continue, the user starts a 2-player fight the usual way and this cell is recorded "not run".
2. **Both bars must be seen to fall.** In H7-P3's saves the leader was always at exactly 140. The reply before the pauses asks that **by the second pause both players have taken damage**, so the record shows both numbers below their start and still the right way round.
3. **A fresh round, if the game gives one.** After the knockout, if a new round begins with both bars full, the user says "new round" before pressing anything: the read should be equal → "no winner yet". If the game returns to a menu instead, recorded "not run".
4. **The user's lines are the facts** (who is ahead, roughly how full each bar is, who won) — recorded verbatim, like "who won" at HOME-12V. They are what the read is set beside; nothing else about how it looked is asked.

**The stages by the user's message:** the read line = stage 1 (unattended); "started" = the first read; then three pause lines; then the knockout line; then "new round" or "menu"; the close.

## Stage 1 — unattended (~5 min; no game, no movie; outside 04:30-05:30Z — inside it: "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that")

B §A stage 1 items 1-5 exactly: HEAD named — **queue AK committed; if B98 / B99's files are uncommitted, stop: "YOU, now: commit queue AK first, then send the read line again"**; only the companion and `privyhub-diag`; no game running; eighteen `PRIVYHUB_` lines, `--check` ok; the APK on the onn read back (`ca53df0d…` CONFIRMED; no install in this task); **the bench drop-in for the sitting only** (`b99-h7-live-read.conf` exactly as B wrote it; daemon-reload; the companion restart; its MainPID serving; **nineteen** lines read back, the nineteenth named as the bench flag; the keeper not restarted); **the rule in place** (T88's kept `rule.json` copied into the rules folder under the hub's id for T88; its sha256 = the kept file's); the route answering `{"ok": true, "running": false}`; **the Continue copy's hash** against the kept `end_p2_b` copy (addition 1); the stream's and the recovery log's marks; **the pre-registration hashed** (below); the watcher started (GET only, once a second, off the repo); the presses to Resume in the onn's Home menu counted from the client's source. Exit with: "YOU, now: start [T88] with player 2 joined as usual and pick Continue — it resumes your last save, the one with player 2 ahead. Don't press anything for a few seconds once the fight is on screen. Then tell me 'started'." (or, with no Continue check: "… and go into a 2-player fight …").

## The fight — attended

- **"started"** → the watcher's rows since the launch: `paused` true until the stream started, then the read. **Cell L0** (addition 1): 110 / 140 → P2. Reply: B's — "YOU, now: play. Three times, at moments you pick, press Home to pause and tell me in one line who is ahead and roughly how full each bar is (for example 'P1 ahead, P1 about three quarters, P2 about half'). **By your second pause, make sure both players have taken some damage.** Then [N presses] to resume and keep playing."
- **Each pause line** (cells L1, L2, L3) → the watcher's rows during that pause (`paused` true, the values, the leader) beside the user's line. Reply after the first and second: "YOU, now: resume and keep playing; pause again when you like." After the third: B's — "YOU, now: finish the fight with a knockout and tell me who won."
- **The knockout line** (cell L4) → the rows from the last pause to the line: the leader at the knockout and both values. Reply: "YOU, now: if a new round starts with both bars full, tell me 'new round' before you press anything; if it goes to a menu, tell me 'menu'."
- **"new round"** (cell L5) → the read equal → "no winner yet"; or "menu" → not run. Reply (the close): "YOU, now: that's all — END the game. Thank you; I'll tidy up on the hub."

## Pre-registered (hashed at stage 1, before the launch)

- **L0** (if run): the first read after the stream starts = 110 / 140, leader P2.
- **L1-L3:** at every pause **the read's leader is the user's leader** (equal values only if the user says "even"); **the values move the way the bars moved** — a bar the user saw drop since the previous pause reads lower, and a fuller bar reads higher than an emptier one; **by L2 both values are below 140** if the user says both took damage.
- **L4:** at the knockout the read's leader is the player the user says won. What the loser reads at that second is recorded, not judged (H7-P3: a finished fight's loser was not at 0).
- **L5** (if run): equal → "no winner yet".
- **The stream is not disturbed by the reads:** the adaptive bitrate's rows and the recovery log over the sitting read as on a normal session — no stall, no `launch_orphaned`, no recovery row at a read's time (`h7_reads.jsonl`'s times against them); every read's `read_ms` and any "busy" / "not in time" answers counted.
- **MET** = every cell that ran is met and the stream rows are clean; any pause wrong → **NOT MET**, the lines recorded, nothing changed. Nothing here adopts anything.

## The close — the flag off, the record (unattended)

- The watcher stopped; **the drop-in removed**; daemon-reload; the companion restarted (its MainPID serving); **eighteen** lines, `--check` ok; the route gone (400 "Unknown Games plugin action: h7-read"); the keeper not restarted; nothing running; the drive before = after; no profile changed. The rules folder kept (off the repo).
- **The record** `evidence/H7_L1_<the UTC date>.md` + dir (B's shape: `pre/`, `run/` with the watcher's rows as values and leaders only and the table — cell | the user's line verbatim | the read at that second (P1, P2, leader, paused) | met; the stream rows' summary; the reads' count, `read_ms` median and worst, any errors; `close/`; the pre-registration and its hash; title, redact and cheat-name checks); `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 lines (the live check's verdict; what waits: a timed stop that reads the leader when the clock ends; the 4-player title; B's three notes — a fold skipped as "not testable" should not pass, an N64 fixture whose code lands in memory, a lighter read path for faster reads); `logs/h7l1_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — the user's pick).
- **The reply begins "YOU, now: commit"**, then per cell met / not met in one line each with the read's two numbers beside the user's words, whether the reads disturbed the stream, and the eighteen lines.

No sudo, no nft, the Opal read-only, adb for state reads only (no install, no `setprop`); no network addresses, titles, serials, game ids, character names, cheat names or paths to the drive anywhere in git; nothing written to the drive; nothing fetched; nothing deleted; B's code not edited; no `e3_flag.conf`; the bench flag absent at the close; nothing adopted; nothing committed.
