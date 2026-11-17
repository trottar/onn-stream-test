---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — H7-C2, the two mini-game titles with everything unlocked: pictures only (session A, hardware, UNATTENDED ~25 min; no user, no onn, no pads; nothing asked of the user but the read line). The user's ask (2026-11-17, verbatim): "One adjustment is I have a cheat save (from extras) that has a cheat for all characters unlocked. Anyway that we could use that for the actual mini game incorporation? It wouldn't change the training so this is a feature for after." — then "I just created a save for <T89> and I also made an unlock all save for <T88>." and "Both are at the character selection screens". Each title now has a cheat setup on the hub with its own slot 1 at the character select. Unlocking changes the select screens — for T88 its start AND both end screens are that select screen (the tally on it) — so the readers must be shown the unlocked screens before the mini games use them. This task launches each title with its cheat setup by the hub alone, loads the user's cheat slot 1 and the kept end states, and keeps the window's pictures for Cowork to label. Bench flag PRIVYHUB_H7=1 for the task only (nineteen lines, back to eighteen). No new code. Pre-registered. Nothing adopted; nothing committed
---

# H7-C2 — the unlocked select screens, pictured with nobody at the TV

Read first: `SESSION_B_DONE_2026-11-17AR.md` §"A — H7-V5" (steps 9-13: launching by the hub alone, the hand load into a **paused** N64 core — `PAUSE_TOGGLE`, `GET_STATUS` `PAUSED`, the copy to `<stem>.state8`, `LOAD_STATE_SLOT 8`, the scratch removed, `PAUSE_TOGGLE` back), `B123_H7_N64_START_2026-11-17.md` (why an N64 core takes a state only while paused), `B112_NO_CLIENT_BENCH_2026-11-16.md` (`bench-release`), `B90_…` (how a launch picks a cheat setup; the setup's own saves and states folders), `H7_C1_2026-11-17.md` (the picture keeper; T89's labels' classes), `H7_V1_2026-11-12.md` / `H7_V3_2026-11-16.md` (T88's kept states: end P1, end P2, two mid-fight; their hashes), `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title (the duel mini game); **T89** = the users' N64 four-player title (the round's-end mini game). No title, character name, cheat name, serial, game id or path in any record; no picture in git; the users' cheat setups named only as "T88's cheat setup" / "T89's cheat setup".

**What is on the hub now** (Cowork read only, 2026-11-17 ~01:10Z): T88 has a second cheat setup (one cheat; created 01:05Z) whose own states folder holds the user's **slot 1** (saved 01:06Z); T89's cheat setup holds the user's **slot 1** in its own states folder (saved 01:07Z). The user: both "are at the character selection screens". The normal slots of both titles are separate and stay untouched.

## Stage 1 — unattended (outside 04:30-05:30Z and not within 45 min before it — else "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that")

- HEAD named with **queue AR committed** and the tree clean but for this task's files (else stop: "YOU, now: commit queue AR first, then send the read line again"); only the two units; no game; eighteen lines; `--check` (not ok on adb alone noted, not a stop).
- **From the code (read, recorded in `pre/cheat_launch.md`):** how a launch picks a cheat setup — the exact loopback call the onn's Extras → Cheats → launch makes, its fields by name (never the cheat's name); which states folder RetroArch reads under a cheat setup (the setup's own); how the hub's own LOAD of a slot works under it. **If a launch with a cheat setup cannot be made from loopback without the onn, stop here:** "YOU, now: commit" with one plain sentence — nothing else is run.
- **The kept states and the users' cheat slots** read only, hashed (the cheat slot 1 of each setup with its picture; T88's kept end P1 / end P2 / one mid-fight; T89's kept `begin` and `results_1`).
- **The bench flag for the task only** (B99's `.conf`, `PRIVYHUB_H7=1`; daemon-reload; the companion restarted, its MainPID serving; **nineteen** lines).
- **The picture keeper** (H7-C1's, the visible window of class `retroarch`, one a second, full window, `index.csv`), one new run folder per title: `runtime/h7_frames/t88_c2_<UTC stamp>/` and `runtime/h7_frames/t89_c2_<UTC stamp>/` — `git check-ignore` before the first file.
- **Before:** every save-state file under the hub's states root **and under every cheat setup's folder** (count and sha256), no `.state8`; the in-game save files of both setups (hashed, recorded — the game's own records, not cells); `launch_orphaned`.
- **The pre-registration hashed** (below).

## Stage 2 — the run (per title; nothing is pressed in a game: no pads, no client)

**For each title** (T88 first, then T89): launch it **with its cheat setup** by the loopback call read at stage 1 (wait for the answer) → `active`, `paused`. **Load the user's cheat slot 1 by hand while the core is paused** (B's H7-V3 step 10 / H7-V5 step 11: the copy of the setup's slot 1 file to `<stem>.state8` **in the folder RetroArch reads under the setup**, `LOAD_STATE_SLOT 8`, its reply and the load line, the scratch removed — for N64 only after `GET_STATUS` says `PAUSED`) → `bench-release` → the keeper running → **40 s of pictures**. Then, each by hand the same way (pause first for N64; `PAUSE_TOGGLE` back after the load):

- **T88:** the kept **end P1** state → 40 s; the kept **end P2** state → 40 s; one kept **mid-fight** state → 20 s.
- **T89:** the kept **results_1** state → 40 s; the kept **begin** state → 20 s.

Then `stop` (RetroArch gone, the keeper's run folder closed). A line in the record per load: the time of its load line, the run folder's picture range it covers. **Recorded, no bar, in words with no names:** for each loaded screen, whether the select screen's grid shows the unlocked roster or the locked one (the "?" boxes) — the key question being whether the **kept locked end states** show the unlocked grid once loaded under the cheat setup.

## Pre-registered (hashed at stage 1, before the first launch) — nothing perceptual; nothing here adopts anything

- **L — the launches:** each title launched with its cheat setup from loopback (the call's answer and the session's own row naming the setup), stopped at the end; nothing left running.
- **D — the loads:** every load above answered and its load line in RetroArch's session log (the cheat slot 1 and every kept state); no N64 load sent to a core not answering `PAUSED`; every scratch copy removed.
- **K — the pictures:** one a second through each run with no gap over 3 s while the game runs; each load's stretch inside its run (counts per stretch).
- **U — nothing of the users' touched:** every save-state file under the states root and every cheat setup's folder before = after (count and sha256); no `.state8` left anywhere; the in-game saves recorded (not cells).
- **MET** = L, D, K and U. What the screens show is for Cowork's labels, not a cell.

## The close (unattended)

The keeper stopped; nothing running; **the drop-in removed**; daemon-reload; the companion restarted (its MainPID serving); **eighteen** lines, `--check` as at stage 1; `bench-release` → 400 "Unknown Games plugin POST action: bench-release"; the keeper not restarted; the drive before = after; no profile changed. **The record** `evidence/H7_C2_<the UTC date>.md` + dir: `pre/` (`STAGE1.md`, `cheat_launch.md` — the call and its fields by name, the setup's folders, no names —, the hashes, the before listings, the pre-registration and its hash), `run/` (`cells.md`, `loads.md` — each load's time and its picture range, and the grid in words —, the keeper's notes per run, the session rows with names replaced), `close/`, title and redact checks, manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 / PrivyParty (the user's ask in the user's words; what waits — Cowork's labels, then B: the readers taught the unlocked screens, the mini games launched with each title's cheat setup and its slot 1 as the begin; then H7-V5 and PP-H4 with everything unlocked); `logs/h7c2_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — Cowork labels these pictures).

**The last reply begins "YOU, now: commit"**, then in one line each: the cheat launch from loopback (made or not, by which call); per title — the loads made, the pictures kept (count, the run folder's name), the grid locked or unlocked on each loaded screen; whether anything of the users' was touched; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb not needed; no network addresses, titles, serials, game ids, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots and cheat setups read only (copies into scratch slot 8 only, removed); B's code not edited; no `e3_flag.conf`; the bench flag absent at the close; nothing adopted; nothing committed.
