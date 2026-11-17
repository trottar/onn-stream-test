---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — H7-D1, why neither title's start screen was recognised under its cheat setup in H7-V5 (session A, hardware, UNATTENDED ~15 min; no user, no onn, no pads). Pictures and per-read distances only, from the watcher's own keep=1, for two orders per title — the load as the board makes it (right after the launch) and a late load (15 s after). Bench flag PRIVYHUB_H7=1 for the task only (nineteen lines, back to eighteen). No new code; no fix. Pre-registered. Nothing adopted; nothing committed
---

# H7-D1 — what the window shows after a setup's begin is loaded

Read first: `H7_V5_2026-11-17.md` with `h7v5_2026-11-17/run/` (`recognise.md`, `h7_rows.jsonl`, `party_rows.jsonl`, `s12.txt`, `s16.txt`); `companion/party_minigame.py` `_start_steps` (the board's order: the launch with the cheat query → `pause` → the watch's start with the load → `resume`, all within ~0.2 s of the launch's answer); `companion/h7_minigame.py` `_start` / `_run` (`RECOGNISE_S` 8.0 counted from the load; `keep=1`'s `index.csv` columns; an N64 load only into a core answering `PAUSED`); `H7_C2_2026-11-17.md` (the cheat launch from loopback, the hand pause by `PAUSE_TOGGLE` / `GET_STATUS`); `B112_…` (`bench-release`); `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title; **T89** = the users' N64 four-player title; "T88's cheat setup" / "T89's cheat setup". No title, character name, cheat name, serial, game id, `profile_id` or path in any record; no picture in git.

**What H7-V5 showed and what it did not:** in the board's order the hub loads the setup's begin about 0.1 s after the title's launch answers, and the 8-s window starts there. T88's last read was 0.0916 against 0.082 (just out); T89's was 0.3175 against 0.0932 (far out). Only the last read's distances were kept, and no picture — so whether the screen was covered by RetroArch's notices, still booting, or never showed the loaded state is not known. This task keeps the pictures and every read's distances.

## Stage 1 — unattended (outside 04:30-05:30Z and not within 45 min before it — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that")

- HEAD named with **H7-V5's record committed** and the tree clean but for this task's files (else stop: "YOU, now: commit H7-V5's record first, then send the read line again"); only the two units; no game; **eighteen** lines; `--check` ok.
- **The rules folder as H7-V5 left it:** both specs, both setups' begins (`be4aa243…` / `78c53af3…`), both sidecars — read only, hashed; nothing written there.
- **The setups read as the onn reads them** (`cheat-profiles`; the same `profile_id`, source and indexes as H7-V5's `setups.md`); the cheat launch query for each, as `party_minigame.py`'s `_cheat_query` makes it.
- **The bench flag for the task only:** B99's `.conf` (`PRIVYHUB_H7=1`); daemon-reload; the companion restarted (its MainPID serving); **nineteen** lines. No party flag.
- **Before:** every file under the states, saves and cheat-setup folders (count and sha256); no `.state8`.
- **The pre-registration hashed** (below).

## Stage 2 — four passes (T88 early, T88 late, T89 early, T89 late); nothing pressed in a game

**Early (the board's order, as fast as one shell line allows):** launch the title with its cheat query on loopback (wait for the answer: `active`, `paused`) → at once `curl -s -X POST "$H/h7-start?keep=1&bench=1"` (the load; its answer with `"begin": "setup"`, `load_line_ms`, `keep`) → at once `curl -s -X POST "$H/bench-release"`. The seconds between the launch's answer and the h7-start's answer recorded.

**Late:** launch the same way → `bench-release` at once → **wait 15 s** → pause by `PAUSE_TOGGLE` on the title's command port until `GET_STATUS` answers `PAUSED` → `h7-start?keep=1&bench=1` → `PAUSE_TOGGLE` back, `GET_STATUS` `PLAYING`.

**Each pass:** the watch left on for **45 reads** (`h7-result` once a second, kept); then `h7-stop` (`idle`); the title stopped as H7-C2 stopped it; no RetroArch left; no `.state8` left. Recorded per pass: RetroArch's load line for the begin (present or not, its time against the launch), `recognised` and when it settled, **every read's class and distances from the keep folder's `index.csv`**, the first read naming `start` (seconds after the load) or "never in 45", and the keep folder's name (git-ignored — `git check-ignore` shown). The pictures stay where the watcher wrote them, for Cowork to look at.

## Pre-registered (hashed at stage 1) — nothing perceptual; the findings are measurements, not cells

- **L — the launches:** each pass launched with its setup (`status`'s `cheat_session.profile_id` the title's setup), stopped at its end; nothing left running.
- **D — the loads:** each h7-start answered `"begin": "setup"`; no N64 load sent unless `PAUSED`; RetroArch's load line read for each (its absence is a finding, recorded, not a failed cell).
- **K — the pictures:** each pass's keep folder holds ≥ 40 pictures with an `index.csv` row each.
- **U — nothing of the users' touched:** every file before = after (the setups' in-game saves recorded, not a cell); no `.state8`.
- **MET** = L, D, K and U. MET says the pictures exist; it says nothing about why the start was missed — that is Cowork's to read.

## The close (unattended)

The drop-in removed; daemon-reload; the companion restarted (no SIGKILL); **eighteen** lines, `--check` ok; `bench-release` → 400 "Unknown Games plugin POST action: bench-release"; nothing running. **The record** `evidence/H7_D1_<the UTC date>.md` + dir: `pre/`, `run/` (`passes.md` — one table per pass: second, class, the distances against the thresholds —, the load lines, the `h7-result` polls, the keep folders' names), `close/`, title and redact checks, manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 (one line); `logs/h7d1_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; Next Action — Cowork reads the pictures).

**The last reply begins "YOU, now: commit"**, then one line per pass: the load line (yes / no, seconds after the launch), the first `start` read (seconds after the load, or never in 45), the least start distance seen and its second, the keep folder's name; then whether anything of the users' was touched; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb not needed; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots, setups and the rules folder read only; B's code not edited; no `e3_flag.conf`; the bench flag absent at the close; nothing adopted; nothing committed.
