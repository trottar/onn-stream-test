---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — H7-V5, both mini-game titles proved through the board's own mini-game routes with everything unlocked (session A, hardware, UNATTENDED ~30 min; no user, no onn, no pads; nothing asked of the user but the read line). B128's sketch (SESSION_B_DONE_2026-11-17AS.md §"H7-V5", steps 1-20) run as written, with Cowork's changes below. B112's bench; PRIVYHUB_H7=1 and PRIVYHUB_PARTY=1 for the task only (twenty lines, back to eighteen). No new code. Pre-registered. Only if MET is PP-H4 (the four-person sitting) offered. Nothing adopted; nothing committed
---

# H7-V5 — T88 and T89 under their cheat setups, from the board, with nobody at the TV

Read first: `SESSION_B_DONE_2026-11-17AS.md` §"A — H7-V5 then PP-H4" (the steps, the strings, the commands, the expected numbers) and its "One risk" paragraph (`recognised` at 6.97 s against 8 s); `B126_H7_UNLOCKED_SCREENS_2026-11-17.md` and `b126_2026-11-17/h7v5_expected/` (the learn / score / replay answers to match); `B127_PARTY_CHEAT_SETUPS_2026-11-17.md` (the sidecar's `cheat`, the setup's begin, `"begin": "setup"`, what the stop flushes); `B112_NO_CLIENT_BENCH_2026-11-16.md` (`bench-release`); `B123_H7_N64_START_2026-11-17.md` (an N64 core takes a state only while paused); `H7_C2_2026-11-17.md` (the cheat launch from loopback; the setups' slot 1 hashes); the PP-H3b record (the board on the bench); `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title (the duel mini game); **T89** = the users' N64 four-player title (the round's-end mini game). No title, character name, cheat name, serial, game id, `profile_id` or path in any record; no picture in git; the setups named only "T88's cheat setup" / "T89's cheat setup" (`<T88 setup>` / `<P88>` as B wrote them).

## Run B128's steps 1-20 as written, with these changes

1. **The window (step 1):** outside 04:30-05:30Z **and not within 45 min before it** — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that". The precondition stop stays B's: queue AS committed, else "YOU, now: commit queue AS first, then send the read line again".
2. **The labels are as committed (step 3-4):** Cowork has **not** relabelled H7-C2's T88 pictures 4-7 — B's expected numbers were computed with the labels as they are, so the learn and score must match `h7v5_expected/` exactly (numbers, not the `.npz` hash). A relabel waits for a later B queue that recomputes them.
3. **Nothing overwritten in the rules folder (steps 3 and 6):** before any learn or sidecar write, if `<T89 id>.endscreen.json` / `.npz` or `<T89 id>.party.json` already exist, rename each aside the same way (`.h7c1.json` / `.h7c1.npz` / `.party.prev.json`) and list every rename in `pre/`. Nothing deleted.
4. **The recognition time, recorded per mini game (steps 12 and 16):** from `h7_results`' rows, the seconds from the `watching` row's load to the row where `recognised` settles — a number for each start (T88 and T89 at least once each). **If `recognised` is false for either title, stop that title there** (`party-minigame-end`, the board kept), record the number and the window's last read, do the other title's steps, and the run is NOT MET with the cause named (B's 8 s window under a setup) — no retry.
5. **Step 20 split into a cell and a record:** the setups' **slots and slot pictures** (`.state*` and their `.png`) and every normal state and save **before = after** — the cell. The setups' **in-game saves** recorded before and after with which differ, **not a cell** (B127: each mini game's stop flushes the in-game save, even with no match played). No `.state8` anywhere.
6. **The hand loads:** every scratch `.state8` removed right after its load reply, before the next step (a count of `.state8` = 0 after each); no N64 load sent unless `GET_STATUS` answered `PAUSED` that second.

## Pre-registered (hashed at step 9, before step 10) — nothing perceptual

B128's 3-6 and 10-20 as stated, with change 4 (a `recognised` false = that title NOT MET, no retry) and change 5 (the in-game saves recorded, not a cell). **MET** = every one of them. **MET → PP-H4 may be offered; NOT MET → it is not.**

## The close (unattended)

As B128's: both drop-ins removed; daemon-reload; the companion restarted (no SIGKILL; its MainPID serving); **eighteen** lines, `--check` as at stage 1; `party-minigames` → 400 "Unknown Games plugin action: party-minigames"; `bench-release` → 400 "Unknown Games plugin POST action: bench-release"; no board, Godot or RetroArch process left; the specs, the setups' begins and the sidecars stay in the rules folder with the renamed-aside files beside them. **The record** `evidence/H7_V5_<the UTC date>.md` + dir: `pre/` (`STAGE1.md`, the setups read as the onn reads them with ids replaced, the learn reports, the scores and replays against `h7v5_expected/` line by line, the renames, the before listings, the pre-registration and its hash), `run/` (`cells.md`, `recognise.md` — the seconds per start —, `loads.md`, the party and `h7_results` rows with ids replaced), `close/`, title and redact checks, manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 / PrivyParty (one paragraph); `logs/h7v5_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — PP-H4 if MET, else what failed).

**The last reply begins "YOU, now: commit"**, then in one line each: the specs learnt matching `h7v5_expected/` (yes / which number differed); T88 — recognised in how many seconds, end_P1 [1, 0], end_P2 [0, 1], the mid-fight never ended; T89 — recognised in how many seconds, places and scores for seats 1,2,3,4 and 3,1,4,2; the users' slots before = after; which in-game saves changed; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb not needed; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots and cheat setups read only (copies into the rules folder and scratch slot 8 only, the scratch removed); B's code not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed.
