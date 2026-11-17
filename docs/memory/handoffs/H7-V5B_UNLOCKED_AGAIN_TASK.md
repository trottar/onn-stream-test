---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — H7-V5b, H7-V5 again with B129-B131 (session A, hardware, UNATTENDED ~30 min; no user, no onn, no pads; nothing asked of the user but the read line). B132's sketch (SESSION_B_DONE_2026-11-17AT.md §"H7-V5 again") run as written, on top of H7-V5's task file and its six changes, with Cowork's changes below. B112's bench; PRIVYHUB_H7=1 and PRIVYHUB_PARTY=1 for the task only (twenty lines, back to eighteen). No new code. Pre-registered. Only if MET is PP-H4 offered. Nothing adopted; nothing committed
---

# H7-V5b — T88 and T89 under their cheat setups from the board, after B129-B131

Read first: `SESSION_B_DONE_2026-11-17AT.md` (all of it — B129's cause: the watcher kept T88's full-screen rectangle for T89; B130's 15.0 s under a setup; B131's refusal and its correction to B127); `handoffs/H7-V5_UNLOCKED_UNATTENDED_TASK.md` (its six changes still apply); `SESSION_B_DONE_2026-11-17AS.md` §"H7-V5" (B128's steps 1-20); `H7_V5_2026-11-17.md` and `H7_D1_2026-11-17.md`; `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title; **T89** = the users' N64 four-player title; "T88's cheat setup" / "T89's cheat setup". No title, character name, cheat name, serial, game id, `profile_id`, path or picture in any record.

## Run B132's sketch as written, with these changes

1. **The window:** outside 04:30-05:30Z and not within 45 min before it — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that". **Queue AT committed** — else stop with "YOU, now: commit queue AT first, then send the read line again"; B132's three `grep -c` checks → 1 each, else stop and say which.
2. **Step 12b on the hub's own slot, never the users':** the SAVE and LOAD sent during the T88 mini game use **`slot=9`** (the hub's), not `slot=1` — the users' unlock save is T88's setup slot 1, and if the refusal ever failed a SAVE to slot 1 would overwrite it. Expected answers and rows as B132's (400 "not during a mini game: nothing was saved" / "… loaded", two `minigame_state_refused` rows, no "Saving state" / "Loading state" line in RetroArch's log, still `playing`, T88's setup's files every sha256 = step 8's).
3. **The order T88 then T89 in one companion** (B132's), so B129's fix is proved on the order that broke it.
4. **Recorded per mini game** (as H7-V5's change 4, `run/recognise.md`): `recognise_s` from the `watching` row, the `recognised` row's `after_s`, any `picture_failed` rows, and for T89 the rectangle the watcher used if the rows carry it.

## Pre-registered (hashed at step 9) — nothing perceptual

B132's: B128's 3-6 (checked read only, as B132 lists) and 10-20 with H7-V5's changes 4-6 and B132's changes — **12 and 16 `recognised` true inside 15.0 s; 12b refused on slot 9 with every setup file byte-equal; 13-15 T88's ends [1, 0] / [0, 1] and the mid-fight never ended; 17-18 T89's places and scores for seats 1,2,3,4 and 3,1,4,2; 19 the board's close; 20 every file before = after (the in-game saves recorded, not a cell), no `.state8`.** **MET = every one. MET → PP-H4 may be offered; NOT MET → not.**

## The close (unattended)

As B128's and H7-V5's: both drop-ins removed; daemon-reload; the companion restarted (no SIGKILL; its MainPID serving); **eighteen** lines, `--check` ok; `party-minigames` and `bench-release` → 400; nothing running; the rules folder as found. **The record** `evidence/H7_V5B_<the UTC date>.md` + dir (`pre/`, `run/` with `cells.md`, `recognise.md`, `loads.md`, `saveload.md`, the rows with ids replaced; `close/`; title and redact checks; manifest). `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 / PrivyParty (one line); `logs/h7v5b_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; Next Action — PP-H4 if MET, else what failed).

**The last reply begins "YOU, now: commit"**, then one line each: T88 — recognised after how many seconds, the SAVE / LOAD refused or not and the setup byte-equal, end_P1 [1, 0], end_P2 [0, 1], the mid-fight never ended; T89 — recognised after how many seconds, any picture failures, places and scores for seats 1,2,3,4 and 3,1,4,2; the users' slots before = after; which in-game saves changed; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb not needed; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots, setups and the rules folder read only (copies into scratch slot 8 only, the scratch removed at once); B's code not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed.
