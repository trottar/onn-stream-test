---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — H7-D2, why neither title's start is read in the paused window (session A, hardware, UNATTENDED ~20 min; no user, no onn, no pads). After H7-V6 (T88 NOT MET, T89 NOT MET: B137's order held — the title PAUSED every second, one frame advance of 2 frames — but both preparations were given up "not recognised" at 15.0 s, the last reads far from the start: T88 screen 0.1641 against 0.082, T89 start 0.2367 against 0.0932; no picture kept). Pictures and every read's distances as the title is stepped forward paused — 0, 2, 10, 30, 90, 210 frames, then run — and one try of the board's own held start with 30 more frames sent by hand. PRIVYHUB_H7=1 and PRIVYHUB_PARTY=1 for the task only (twenty lines, back to eighteen). No new code; no fix. Pre-registered. Nothing adopted; nothing committed
---

# H7-D2 — what the paused window shows, frame by frame

Read first: `H7_V6_2026-11-17.md` with `h7v6_2026-11-17/run/`; `SESSION_B_DONE_2026-11-17AV.md` (B137's order; its settle was made on made-up content, not on a title: a paused PS1 core shows a loaded state after one advanced frame, the N64 core's load runs a frame itself; RetroArch draws "Paused." in the window's corner while paused, which the party's watch masks and a plain `h7-start` does not); `H7_D1_2026-11-17.md` and its task (the direct passes: the cheat launch on loopback, `h7-start?keep=1&bench=1`, the pause by `PAUSE_TOGGLE` / `GET_STATUS`, the keep folders); B's paused proof commands (the command port read from the config after each launch); `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title; **T89** = the users' N64 four-player title; "T88's cheat setup" / "T89's cheat setup". No title, character name, cheat name, serial, game id, `profile_id`, path or picture in any record; no answer carrying a `"title"` copied.

**The question:** B137 loads the begin into a paused core and advances 2 frames. On the titles themselves the watcher then reads something far from the start for 15 s. Either the window does not yet show the begin after 2 frames (a game that draws into a back buffer, a renderer that needs frames after a load), or something else covers or replaces it while paused. The pictures say which, and how many frames it takes.

## Stage 1 — unattended (outside 04:30-05:30Z and not within 45 min before it — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that")

- HEAD named with **H7-V6's record committed** and the tree clean but for this task's files (else stop: "YOU, now: commit H7-V6's record first, then send the read line again"); only the two units; no game; eighteen lines; `--check` (not ok on adb alone noted, not a stop).
- The rules folder read only, hashed; the setups read as the onn reads them; both drop-ins; daemon-reload; the companion restarted (its MainPID serving); **twenty** lines.
- **Before:** every file under the states, saves and cheat-setup folders (count, every sha256); no `.state8`.
- The pre-registration hashed (below).

## Stage 2 — nothing pressed in a game; no pad, no client

**Pass P, once per title (T88 then T89) — the title stepped forward paused, the watcher keeping its own pictures:**
1. Launch with the cheat query on loopback (wait for the answer); `GET_STATUS` → `PAUSED` (if `PLAYING`, `PAUSE_TOGGLE` until `PAUSED`; recorded). **No `bench-release`.**
2. `curl -s -X POST "$H/h7-start?keep=1&bench=1"` → the answer (`"begin": "setup"`, `load_line_ms`, the keep folder). The seconds from the launch's answer recorded.
3. **Segments** — after each, `GET_STATUS` once (`PAUSED` expected through S5); the watcher reads once a second throughout:
   - **S0:** nothing sent — **12 s** (long enough for RetroArch's launch notices to run out, if they do while paused).
   - **S1:** `FRAMEADVANCE` × 2, 60 ms apart (B137's) — 6 s.
   - **S2:** × 8 more (10 in all) — 6 s. **S3:** × 20 more (30) — 6 s. **S4:** × 60 more (90) — 6 s. **S5:** × 120 more (210) — 6 s.
   - **S6:** `PAUSE_TOGGLE` → `PLAYING` for 3 s → `PAUSE_TOGGLE` → `PAUSED` — 6 s paused.
   - **S7:** `PAUSE_TOGGLE` → `PLAYING` — 10 s running (the reference).
4. `h7-stop`; the title stopped as H7-D1 stopped it; no RetroArch left; no `.state8`.
Recorded per segment (`run/passes.md`, from the keep folder's `index.csv` — **these reads are not masked for the "Paused." label; say so**): its seconds, the frames advanced so far, the status word, each read's class and distances against the thresholds, its picture numbers; and the first read naming `start`, or "never". The pictures stay in the keep folders (git-ignored — `git check-ignore` shown).

**Pass Q, once per title — the board's own held start, with more frames by hand:** the board launched and released (H7-V6 step 4); `party-minigame-start?…&bench=1&hold=1` (T88 seats 1,2; T89 seats 3,1,4,2); **as soon as the `minigame_frame_advance` row is written, 30 × `FRAMEADVANCE`, 60 ms apart, on the title's command port**; `party-minigame-result` and `h7-result` once a second (the result's `last`: class and distances — these reads are masked) until `ready` or `given_up`. **`ready` →** the go → `playing` → `party-minigame-end`. **`given_up` →** recorded; no retry. The board closed after both (H7-V6 step 10).

## Pre-registered (hashed at stage 1) — nothing perceptual; the findings are measurements, not cells

- **L:** each launch under its setup (`cheat_session.profile_id` the title's), stopped at its end; nothing left running.
- **D:** each `h7-start` answered `"begin": "setup"`; no N64 load unless `PAUSED`; the status word after every segment recorded (a `PLAYING` before S6 is a finding, recorded with its segment).
- **K:** each pass P's keep folder holds ≥ 55 pictures with an `index.csv` row each.
- **U:** every file before = after (the setups' in-game saves recorded, not a cell); no `.state8`.
- **MET** = L, D, K and U. MET says the pictures and reads exist — not why the start was missed, and not whether Q reached `ready`.

## The close (unattended)

Both drop-ins removed; daemon-reload; the companion restarted (no SIGKILL); **eighteen** lines, `--check` as at stage 1; both routes gone (400); nothing running; the rules folder as found. **The record** `evidence/H7_D2_<the UTC date>.md` + dir: `pre/`, `run/` (`passes.md` — one table per pass and segment —, `q.md` — the rows and the `last` read per second —, the status words, the keep folders' names), `close/`, title / redact / name checks, manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §PrivyParty (one line); `logs/h7d2_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; Next Action — Cowork reads the pictures).

**The last reply begins "YOU, now: commit"**, then per title one line for pass P — the segment (and frames advanced) at which a read first named `start`, or never while paused, and whether the running reference did; the status words; the keep folder's name — and one line for pass Q — `ready` or `given_up`, after how many seconds, the last read; then whether anything of the users' was touched; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb not needed; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots, setups and the rules folder read only; B's code and the board's repo not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed.
