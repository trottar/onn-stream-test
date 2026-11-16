---
memory_schema: 1
as_of: 2026-11-16
status: TASK HANDOFF — PP-H2, PrivyParty on the hub, step 2 of four: the streamed probe (session A, hardware, attended ~12 min; ONE sitting at the TV, the user with the onn and two pads paired to the onn over Bluetooth as always; nothing asked on the hub; every reply begins "YOU, now:" and is a complete step naming only what the onn will offer, read from the hub at stage 1). After PP-H1 (the board runs on the hub at 60 frames a second, quits cleanly by F10; one scripted check, step 19, failed) and queue AO (B107 step 19's numbers; B108 the board as a launch behind `PRIVYHUB_PARTY=1` — the onn as it is can start it). The hub first launches the board by itself and checks its window, sound and quit — any miss and the user is not asked to sit. Then the user starts the board from the onn, joins two pads, plays a round, pauses, resumes, ends. Bench flag for the sitting only (nineteen lines, back to eighteen). Pre-registered. Nothing adopted; nothing committed in either repo
---

# PP-H2 — can the user play the board game from the onn, streamed, with their own pads?

Read first: `SESSION_B_DONE_2026-11-16AO.md` §"A — PP-H2" (**stage 1's steps and commands, the watchers, the lines, the close and the record's shape are B's — use them exactly**, with the changes below) and §"What I would change" 5 (what only the real board can show); `B108_PARTY_LAUNCH_2026-11-16.md` (the settle: the entry, the window, the sound, the pads, Home / RESUME / SAVE / LOAD / END, the rows in `logs/games/party.jsonl`); `B107_PP_STEP19_NUMBERS_2026-11-16.md`; `PP_H1_2026-11-16.md`; the hand-back (`PRIVYPARTY_PC_HANDBACK_2026-11-12.md`) and the board repo's `README` "Controls"; `docs/memory/CURRENT.md`.

**The board game's repo** is read only for this task but for Godot's own import step; nothing in it edited or committed. **The owner's pictures never enter git** — no picture, screenshot, face, file name or listing; a count and a size only. No path of the user's in git: the config file lives off the repo and only its field names are recorded.

**The stages by the user's message:** the read line = stage 1 (unattended); then B's messages — "ready", "paused", the user's one line, "ended" — and for the second renderer "ended" or "skip". A never holds a turn while the user plays.

**Changes to B's sketch (Cowork's), and why:**

1. **The PC side has pushed since PP-H1 and the user has pulled the board's repo on the hub** (if its HEAD is still `21e7e44`, say so in the record and go on with step 19 noted as open). With a new HEAD: the import step, then the 25 checks headless as PP-H1 — **cell C: 25 of 25 PASS**. C not met does **not** stop the sitting (the streamed probe does not rest on step 19); the verdict then reads "MET but for C".
2. **Stage 1's own launch is a gate with its own cells** (B's step 6): W — the board's window found by class, **1920 × 1080 at 0, 0**; A — **one sound stream with the board's pid**; D — the `pads` row P1-P4 in event order; Q — the stop **quits by F10 with exit code 0**, no `sigterm` row. **Any of W, A, D, Q not met → no sitting:** the close, and the reply "YOU, now: commit" with one plain sentence on what the hub's own launch showed. Also tried, recorded, not a cell: a headless Godot line of A's own (off both repos) listing the joypads while that launch is up — devices 0-3 against the pads P1-P4.
3. **Every button in a line is named as it is on the user's pads**, read at stage 1: the pads' class from the recovery log (Sony → ✕ / ○ / △), the board's actions from its README ("confirm", "back", "map" → which pad button). The lobby line says which button starts the game.
4. **The stream's cell is "no stall, no recovery row, no new `launch_orphaned`, frames a second median ≥ 55"**; the bitrate's level and whether it acted are recorded, not a bar — the board's busy textures may well move it, and that is a finding.
5. **The second renderer is the user's choice at the time:** after the first "ended" A offers it in one line ending "…or tell me 'skip'".
6. **Time:** outside 04:30-05:30Z (inside: "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that").

## Stage 1 — unattended (~15 min if the 25 checks run, else ~4)

B's steps 1-9: HEAD named with queue AO committed and the tree clean but for this task's files (else stop: "YOU, now: commit queue AO first, then send the read line again"); only the companion and `privyhub-diag`; no game; eighteen `PRIVYHUB_` lines; `adb connect` from the hub if needed; `--check` ok; the APK read back (`ca53df0d…` CONFIRMED; no install). The board's repo: its HEAD, `git status --short`; change 1. The config file written off the repo (its field names recorded; renderer `gl_compatibility`). The bench drop-in (`PRIVYHUB_PARTY=1`; daemon-reload; the companion restart; its MainPID serving; **nineteen** lines, the nineteenth named; the keeper not restarted). **What the onn will offer, from the hub's own state** (the systems answer: the board's entry's exact name and count; its one game; the start box; the pads' class; the join lines; the paused bar) and change 3's button names. **The hub's own launch** (change 2): W, A, D, Q. The watchers ready. Before: the saves listing (161 at PP-H1; no `.state8`), the pictures' count and bytes, the board repo's status, the stream marks. **The pre-registration hashed.** Exit with B's first line, filled in.

## The lines

B's five lines, filled in at stage 1, with change 3's button names and change 5's offer. If the board's entry does not appear on the onn or a launch is refused: one plain sentence on what the hub said, and the complete step to try once more; a second failure ends the sitting with the lines recorded.

## Pre-registered (hashed at stage 1, before the user's launch) — nothing perceptual; nothing here adopts anything

- **C — the board's checks** (only if its HEAD changed): 25 of 25 PASS, exit 0.
- **W, A, D, Q — the hub's own launch** (change 2). Not met → no sitting, NOT MET.
- **P — each pad drives its own seat:** the `pads` row P1-P4 in event order (P1 = device 0, P2 = device 1) **and** the user's one line, verbatim.
- **H — Home pauses and RESUME resumes:** a `pause` row with key Escape after Home and a `resume` row with key Escape after RESUME; the status `paused` true, then false.
- **E — END quits the board:** a `quit` row, then `exited` with code 0; no `sigterm` row.
- **S — the stream:** no stall, no recovery row, no new `launch_orphaned`; frames a second median ≥ 55 over the play. The bitrate's level, whether it acted, loss and PRESSURE recorded beside a normal game session's.
- **AU — sound:** the stream's audio counters growing through the play.
- **Recorded, no bar:** the encoder's and Godot's CPU and the graphics device's busy share, medians over the play, under Compatibility (and Mobile if run); how long the join took by the rows; what the onn showed for SAVE / LOAD if the user happened to press them (not asked).
- **U — nothing of the user's touched:** the saves before = after (count and hashes), no `.state8`; the pictures' count and bytes unchanged; the board repo's `git status --short` after = before.
- **MET** = W, A, D, Q, P, H, E, S, AU and U met (and C, if it was run; C alone not met → "MET but for C").

## The close — the flag off, the record (unattended)

B's close: the watchers stopped; **the drop-in removed**; daemon-reload; the companion restarted (its MainPID serving); **eighteen** lines, `--check` ok; the board's entry gone from the systems answer; no board process left; the keeper not restarted; the drive before = after; no profile changed; the config file stays off the repo. **The record** `evidence/PP_H2_<the UTC date>.md` + dir in B's shape (`pre/` with the checks' table or the step-19 note, `onn_offers.md`, the hub's own launch rows and cells; `run/` with `cells.md`, the party rows, the status watch, the CPU / graphics table, the stream rows' summary, the user's lines verbatim; `close/`; the pre-registration and its hash; title and redact checks — no title, path, file name from the pictures' folder or address of ours; manifest). `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` — PrivyParty on the hub: step 2's verdict; what waits — step 3 the adapter mini game behind `play(players) -> scores` calling `h7-start` / `h7-result`; step 4 the stream switched between the board's window and the emulator's; four pads for the board; SAVE / LOAD / Cheats / Mods not offered for the board (a client change); one join instead of two; `logs/pph2_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — step 3's design, Cowork's).

**The last reply begins "YOU, now: commit"**, then in one line each: the board's checks (how many of 25, or not run); the hub's own launch (window, sound, pads, quit); each pad its own seat — the row and the user's words; Home / RESUME; END (exit code, any SIGTERM); the stream (stall or not, frames a second, the bitrate's level and whether it acted); sound packets; the CPU and graphics shares per renderer run; whether anything of the user's was touched; MET / MET but for C / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb for state reads only (no install, no `setprop`); no network addresses of ours, titles, serials, paths or names from the pictures' folder anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; B's code not edited; the board's files not edited; no `e3_flag.conf`; the bench flag absent at the close; nothing adopted; nothing committed in either repo.
