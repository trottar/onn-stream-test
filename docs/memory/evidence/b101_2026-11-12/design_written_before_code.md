# B101 — the timed contest behind `PRIVYHUB_H7=1` (design, written before code; queue AL, 2026-11-12)

Baseline: HEAD `33d8d2cf`. **Changes the companion** (a new module, two flagged routes in `plugins/games.py`); absent /
`0` = today byte for byte. Tests in `tests/b101_h7_contest/`.

## Settled first (synthetic fixtures, B61's form; `settle/contest.py`, `settle/contest_results.jsonl`)

| | SNES (snes9x; the fixture's frame counter) | PS1 (Beetle PSX HW; the core's per-frame word, B99) |
| --- | --- | --- |
| a state (made paused, values 0 / 0) loaded **into running content** as `<stem>.state8`, `LOAD_STATE_SLOT 8` | answer `LOAD_STATE_SLOT 8` in 16.1 ms; RetroArch's line `[State] Loading state …, 823,432 bytes` **32.0 ms** after the command; no failure line; **the first read 0 / 0 = the state's own** (50 / 60 before); still running | answer in 17.2 ms; the line (16,777,240 bytes) **33.4 ms** after; the first read = the state's; still running |
| **the clock** (the hub's clock, a read every second) | 10.005 s → **600** frames; 30.011 s → **1,800**; 60.004 s → **3,600** | 10.016 s → **601**; 30.001 s → **1,800**; 60.001 s → **3,600** |
| **the end**: "time is up" → the final read | 33.3 ms; **3 frames** passed before it was in | 32.8 ms; 3 frames |
| "time is up" → a hub-side pause taking hold | 33.0 ms; 2 frames; 0 frames in the next 0.5 s | 49.9 ms; 2 frames; 0 |
| the core's state folder (the hub's base config) | `Snes9x`; **bsnes**: `bsnes` | `Beetle PSX HW` |

## How the contest ends: **running** (no pause)

From the client's source (`PrivyHub/app/src/main/java`; a read-only study, spot-checked): during a stream the onn never
reads `paused` — the heartbeat's reply is discarded (`NativeStreamActivity`), `paused` is read only on the main screen
(`MainActivity`'s banner and tile); the only in-stream pause overlay is the client's own link check (≥ 1 s of silence).
The hold's pause is **ended by the hub itself** on the next controller packet (`link_drop_recovery.note_input_release`),
so the onn never has to handle it; a pause the hub keeps would leave a frozen picture with no in-stream way back (the
user would have to leave the stream and pick Resume). **The onn does not handle a hub-side pause as it handles the
hold's → the contest ends without a pause** (`"ended": "running"`); the final read is taken at "time is up" (≈ 3 frames
late, settled above).

## The routes (only with `PRIVYHUB_H7=1`)

New module `companion/h7_contest.py` (uses B99's `h7_live_read`: the rule, the read, the rules folder).

- **`POST /plugins/games/h7-contest?seconds=N`** (5 ≤ N ≤ 300, an integer). **(1) Refused plainly** (400) unless: a
  RetroArch game is running — PS1 or SNES (N64 → "not supported yet — a state cannot be loaded into a running N64 game";
  PS2 / GameCube → "not supported yet"); its rule is in the rules folder (B99: "no rule for this game"); **its state is
  beside it** (`<the hub's game id>.state`; else "no state for this game's contest"); **the stream is up**
  (`native_stream.status()["active"]`; else "the stream is not up"); **no contest is running** ("a contest is already
  running"); the core's state folder is known (Beetle PSX HW, Beetle PSX, Snes9x, bsnes; else "not supported yet with
  this game's core").
- **(2) The load** (in the POST, under the manager's lock — the hub's LOAD's own lock — waited for at most 2 s): the
  state copied to **`<state root>/<the core's folder>/<stem>.state8`** — **slot 8**, a scratch slot no part of the hub
  uses for a RetroArch game (the user's slots are 1-3; slot 0, `<stem>.state`, is the hub's own save/load staging and
  the last-save copy A calls "Continue"; slot 9 is the rewind's scratch; the recovery's is `<stem>.state.recovery`; PS2 /
  GameCube's slot 8 is their own emulators', not RetroArch's); refused if a `.state8` is already there (never
  overwritten). `LOAD_STATE_SLOT 8` through the companion's command path (2 s, one try); the answer must start
  `LOAD_STATE_SLOT 8`; **RetroArch's own line** `[State] Loading state "…", N bytes.` (N > 0) within **1.5 s** in the
  session log (the hub's LOAD reads the same log), no failure line; **the scratch file removed** after, in every case.
  Failure → 502 plain ("the contest's state did not load; the game is as it was"), nothing else changed. The game is
  loaded **while running** (the hub's own LOAD loads while paused; the settle shows a running load reads exactly).
- **(3) Arm** (a background thread from here; the POST answers 200 `{"ok": true, "contest": "started", "seconds": N}`
  once the load is confirmed): the state's own read right after the load (B99's read), then a read every 0.25 s until
  the values differ from it (the bars filling) — **at most 20 s**; armed → `armed_after_s`; not armed → the contest
  ends with "the fight did not start within 20 s; the game left running" (an error row, no answer).
- **(4) Run** N seconds from arming, a read every second kept as `samples` `[[t, P1, P2, …], …]` (t in seconds from
  arming, 0.1 s).
- **(5) Time is up** → the final read → **the answer** `{"ok": true, "game", "winner", "reason", "values", "seconds",
  "armed_after_s", "samples", "resets_seen", "ended": "running"}`. **`resets_seen`:** a sample where every player's
  value is back at its armed value after at least one value had been below its armed value since the last such moment
  (a new round) — counted, never used for the winner.
- **`GET /plugins/games/h7-contest`** → `{"ok": true, "contest": null}` before any; else the running contest's state
  (`"state": "arming" | "running"`, `seconds`, `elapsed_s`, `samples` so far) or the last outcome (`"state": "done"`
  with the answer, `"error"` with its words, or `"ended"` with why).
- **END:** each step checks that the same game is still running and the stream still up; the user's END (the game
  stopped) or the stream stopping → the contest ends: one row ("ended: the game stopped" / "the stream stopped"), no
  answer; nothing left behind (the scratch already removed after the load; no lock held between reads).
- **The log:** one row per step in `logs/games/h7_contests.jsonl` (`refused`, `loaded` with the load line's ms,
  `armed` / `not_armed`, `done` with the answer, `ended`, `error`); the reads are also B99's `h7_reads` rows.
- **It changes only what a LOAD changes:** no pause, no save, no write, no cheat; slots 1-3 and `<stem>.state` never
  written; the recovery and the hold untouched.
- **Absent / `0`:** neither route exists — GET answers today's "Unknown Games plugin action: h7-contest", POST
  "Unknown Games plugin POST action: h7-contest" (400).

## Tests (`tests/b101_h7_contest/`, the companion's real HTTP server on loopback)

B99's harness; the fake RetroArch extended: `LOAD_STATE_SLOT n` reads `<core folder>/<stem>.state<n>` (a made-up file
holding the values it sets), writes RetroArch's own load line into the game log, answers `LOAD_STATE_SLOT n`; refuses
(a failure line) on demand; its memory then follows a script in time (the bars filling, falling, a new round); its
command log. A stream stub with `active` set per case. Cases: a contest end to end (armed when the values fill, the
leader at the clock, the samples, the answer, `ended: running`); every value back to full inside the time →
`resets_seen` 1, the winner still the leader at the clock; equal at the clock → "no winner yet"; no state / no rule /
no stream / a second contest → the plain refusals; a load the fake refuses → the plain error, the fake's memory as
before, no scratch file; never armed → the error within the bound; END (`POST stop`) during the contest → ended,
no answer, no scratch, the lock free; the fake's command log: only GET_STATUS, READ_CORE_RAM and one
LOAD_STATE_SLOT 8; N64 and PS2 sessions → "not supported yet"; the user's slots 1-3 and `<stem>.state` byte-equal
before and after; the log rows; **flag absent and `0` → both routes as at the baseline (`git archive 33d8d2cf`) byte for
byte**; B99's tests green.
