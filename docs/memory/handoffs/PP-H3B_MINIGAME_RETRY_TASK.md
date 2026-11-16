---
memory_schema: 1
as_of: 2026-11-16
status: TASK HANDOFF — PP-H3b, PP-H3 again with the fixes (session A, hardware; part 1 UNATTENDED on the bench, then — only if part 1 is fully met — ONE sitting at the TV ~15 min, the user with the onn and two pads paired to the onn over Bluetooth as always; nothing asked on the hub; every reply to the user begins "YOU, now:" and is a complete step naming only what the onn will offer, read from the hub at stage 1). After PP-H3 (NOT MET: one hub mini game right end to end, then the hand-back by the recovery and a hang on the second start) and queue AQ (B114 the hang named, reproduced and fixed; B115 the hand-overs planned both ways; B116 the board at 10 fps behind the title). Bench flags `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1` for the task only (twenty lines, back to eighteen). Pre-registered per part. Nothing adopted; nothing committed in either repo
---

# PP-H3b — four hub mini games from inside the board, every hand-over planned, END always works

Read first: `SESSION_B_DONE_2026-11-16AQ.md` §"A — PP-H3b" (**stage 1, the route watcher, part 1 (P11b, P13, P14b, P15), the sitting's lines, "stuck", "close", both pre-registrations, the close and the record's shape are B's — use them exactly**, with the changes below); `PP-H3_MINIGAME_FROM_THE_BOARD_TASK.md` (its eight changes, which still hold unless changed here); `PP_H3_2026-11-16.md`; `B114_…`, `B115_…`, `B116_…`; `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title; named to the user in replies only. No title, character name, game id, serial or path in any record; no picture in git; the owner's pictures never listed. **The user's standing word:** "I'm not playing when it doesn't work" — nobody is asked to sit down unless part 1 is fully met.

**The stages by the user's message:** the read line = stage 1 and part 1 (unattended), ending with the close and "YOU, now: commit" plus one plain sentence (part 1 not met) or with the sitting's first line (part 1 fully met, the flags left on); then "ready", the user's line after each of matches 1-3, "ended"; at any time "stuck", "left" or "close". A never holds a turn while the user plays.

**Changes to B's sketch (Cowork's), and why:**

1. **Time:** the read line outside 04:30-05:30Z and not within 45 min before it (else "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that").
2. **The board's two files committed** as B's stage 1 says (their sha256 `4706a28b…` / `c09036b7…`); and the companion running HEAD's code — the restart at stage 1 after the drop-ins is the one that loads queue AQ's code; its MainPID's start time after HEAD's commit time, recorded.
3. **R is checked live during the sitting:** if a route watcher line shows `ok` 0 or `seconds` ≥ 2.0 while the user plays, A says so at the user's next message in one plain sentence, records R not met, and goes on with B's lines — the user is not asked to stop unless "stuck" applies.
4. **The held frame each way is a recorded number, no bar** (B115 expects ~4-5.5 s on the onn): from each `minigame_stream` row's start to the client's first frame of the new stream, from the stream and client rows; and the user may say how it looked — recorded verbatim, not judged.
5. **Godot's CPU behind the title (C)** recorded per match beside PP-H3's 98 % and the board's own figure in front.
6. **The close's journal:** no SIGKILL in the companion's restart (recorded); a SIGKILL there is a finding, not a failure of the close.

## Pre-registered

B's part 1 and part 2 cells exactly (part 1: PP-H3's plus R from part 1's start, P11b's two results [1, 0] / [0, 1], Home taken and the title paused, P14b's END taken, the title and the board gone, exit code 0; part 2: M1, M2, M3, X, R, H, E, C, U; MET = part 1 met and M1, M2, M3, X, R, H, E, U met), each hashed before what it judges.

## The record and the last reply

B's record shape (`evidence/PP_H3B_<the UTC date>.md` + `pph3b_<the UTC date>/`), title and redact checks, manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` — PrivyParty on the hub: the verdict; what waits — a faster switch (the adopted fast restart for the hand-overs, then a capture that follows a window); more mini games by the labels-only recipe with pictures from `keep=1`; four players and placements; a draw; the onn's entry and bar for the board; one join instead of three; `tests/input_hold_b8`'s one failing assertion on HEAD (B's note 4); `logs/pph3b_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — Cowork's).

**The last reply begins "YOU, now: commit"**, then in one line each: part 1 (R's maximum per route; P11b's results; Home taken; END during a mini game — exit code; met or not and what failed); per match — the user's winner, the hub's class and scores, the seat the board credited, met or not; the hand-overs (planned and switched both ways or not, any recovery row, any board key, any bitrate step, the held frame each way); R through the sitting (the maximum per route); Home / RESUME; END during the fourth mini game; Godot's CPU behind the title; whether anything of the user's was touched; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb for state reads only (no install, no `setprop`); no network addresses of ours, titles, serials, game ids, character names, paths or names from the pictures' folder anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; B's code not edited; the board's files not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed in either repo.
