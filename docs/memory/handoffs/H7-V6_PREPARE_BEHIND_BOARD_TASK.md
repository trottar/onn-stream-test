---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — H7-V6, the new order on the bench: each title prepared paused behind the board, handed over on the go, practices, and no press able to reach it before the go (session A, hardware, UNATTENDED ~30 min; no user, no onn, no pads; nothing asked of the user but the read line). B138's sketch (SESSION_B_DONE_2026-11-17AV.md §"H7-V6", steps 1-10 and its paused proof) run as written, with Cowork's changes below. B112's bench; PRIVYHUB_H7=1 and PRIVYHUB_PARTY=1 for the task only (twenty lines, back to eighteen). No new code. Pre-registered. T88 MET → PP-H3c (the user alone, two pads) may be offered; both MET → PP-H4 after it. Nothing adopted; nothing committed
---

# H7-V6 — choose, load, ready or practise: the hub's half, with nobody at the TV

Read first: `SESSION_B_DONE_2026-11-17AV.md` (all of it — B137's order: pause → the pads muted → the load → two frames advanced → the mute off → the watcher reads the paused window with RetroArch's "Paused." corner masked → `ready`; the go with no second load; the paused proof's commands) and `SESSION_B_DONE_2026-11-17AU.md` (B133's hold and go, B134's practice); `B137_…`, `B133_…`, `B134_…` records; `H7_V5B_2026-11-17.md` (the hand loads, the kept states, the close); `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title; **T89** = the users' N64 four-player title; "T88's cheat setup" / "T89's cheat setup". No title, character name, cheat name, serial, game id, `profile_id`, path or picture in any record. **A game's name is run-time data only:** the list's answer and any answer that carries a `"title"` is never pasted, copied or logged into a record — only B's one printed line of counts and booleans.

## Run B138's steps 1-10 as written, with these changes

1. **The window:** outside 04:30-05:30Z and not within 45 min before it — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that". **Queue AV committed** — else stop with "YOU, now: commit queue AV first, then send the read line again"; B's six `grep -c` checks → 1 each, else stop and say which.
2. **A verdict per title.** T88 = steps 5-8; T89 = step 9; 4 and 10 belong to both. **MET** = both. **T88 MET, T89 NOT MET** is a result of its own: PP-H3c needs T88 only and may be offered; T89 goes back to B (the fallback B137 did not build).
3. **Every paused read recorded, whichever way it goes** (`run/reads.md`, from `h7_results` — numbers only): for each preparation, each read from the `watching` row to the `recognised` row — its second, its class, its distances against the thresholds — and the second of the first `start`. **T89's are the open question** (B137 could not prove its start is read with the "Paused." label on the window): if step 9's first preparation is given up "not recognised", read as B says, stop T89 there (no retry), do the close, and say so in one plain line.
4. **The paused proof is a cell for every preparation:** one word a second from each `minigame_watch` row to its go — `PAUSED` every time; a `PLAYING` or a missing answer in that stretch is NOT MET for that title, with its second.
5. **The hand loads:** every scratch `.state8` removed right after its load reply (a count of 0 after each); an N64 load only after `GET_STATUS` answered `PAUSED` that second; A's own `FRAMEADVANCE` only in step 7.
6. **Step 10's cell:** the setups' slots and slot pictures and every normal state and save before = after (every sha256); the setups' in-game saves recorded before and after with which differ, not a cell.

## Pre-registered (hashed at step 3, before the board is launched) — nothing perceptual

B138's list for 4-10, with changes 2-6: `prepare_s` T88 ≤ 20 s and T89 ≤ 15 s; one `minigame_frame_advance` per preparation (`"frames": 2, "paused": true`, `"mute_ms"` < 1000); `PAUSED` at every read from each watch row to its go; no `minigame_reloaded` at any go; no route and no switch before any go; still `ready` after 180 s; `remembered`, `already`; the never-the-start start given up with no route; practices back to `ready` by time with no scores; the real ends as H7-V5b (T88 `end_P1` [1, 0], `end_P2` [0, 1]; T89 places [1, 2, 3, 4], scores [4, 3, 2, 1], seats [3, 1, 4, 2]).

## The close (unattended)

As H7-V5b's: both drop-ins removed; daemon-reload; the companion restarted (no SIGKILL; its MainPID serving); **eighteen** lines, `--check` ok; `party-minigames` and `bench-release` → 400; no board, Godot or RetroArch process; the rules folder as found. **The record** `evidence/H7_V6_<the UTC date>.md` + dir: `pre/`, `run/` (`cells.md` per title, `reads.md`, `paused_proof.md` — the words and their seconds —, `practices.md`, `loads.md`, the rows with ids replaced and no name), `close/`, title / redact / name checks, manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §PrivyParty (one paragraph); `logs/h7v6_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — PP-H3c if T88 is MET).

**The last reply begins "YOU, now: commit"**, then one line each: T88 — `prepare_s`, the first `start` read's second, `PAUSED` throughout or not, held 180 s, the go with no reload, the never-the-start start, two practices by time, the real ends; T89 — the same for its one preparation and practice, places and scores; the users' slots before = after and which in-game saves changed; T88 MET / NOT MET; T89 MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb not needed; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots, setups and the rules folder read only (scratch slot 8 only, removed at once); B's code and the board's repo not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed.
