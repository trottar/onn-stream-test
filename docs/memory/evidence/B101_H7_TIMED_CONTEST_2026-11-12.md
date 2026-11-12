---
memory_schema: 1
as_of: 2026-11-12
status: BUILT, NOT ADOPTED (session B, queue AL) — behind PRIVYHUB_H7=1 only, POST /plugins/games/h7-contest?seconds=N loads a mini game's kept state into the running PS1 / SNES game (scratch slot 8, never a user's), arms when the values first leave the state's, runs N seconds with a read every second, and names the leader when the clock ends; it ends RUNNING — the onn cannot resume a pause it did not ask for (from the client's source). Absent / 0 = today, byte for byte against the baseline's companion through the real HTTP route. Settled on fixtures: a state loads into running content in ~33 ms with RetroArch's own line and reads exactly; 10 / 30 / 60 s by the hub's clock = 600 / 1,800 / 3,600 frames; the final read is in 3 frames after "time is up". Synthetic fixtures and a fake RetroArch only; no real title started. Nothing committed. No title, serial, code name, character name, cheat name or path in this record
---

# B101 — the timed contest (`PRIVYHUB_H7=1`) (2026-11-12)

**Why:** H7-L1 met — the read names the leader in a fight being played. Two things a mini game must live with were seen
there: the number never reaches 0 at a knockout, and a new round resets both to full. So the first mini-game form is the
roadmap's own: **a kept state, a fixed time, the leader when the clock ends**, the samples kept so a reset is seen.
**Baseline:** HEAD `33d8d2cf`. **Design** hashed before code at 01:15:07Z (`b101_2026-11-12/design.sha256`), after the
settle and the client study.

## Settled (synthetic fixtures, B61's form; `settle/contest.py`, `settle/contest_results.jsonl`)

| | SNES (snes9x; the fixture's frame counter) | PS1 (Beetle PSX HW; the core's per-frame word, B99) |
| --- | --- | --- |
| **the load:** a state made paused (values 0 / 0) put in the core's folder as `<stem>.state8`, `LOAD_STATE_SLOT 8` into **running** content (values 50 / 60 before) | answer `LOAD_STATE_SLOT 8` in 16.1 ms; RetroArch's own line `[State] Loading state …, 823,432 bytes` **32.0 ms** after the command; no failure line; **the first read 0 / 0 = the state's own**; still running | answer in 17.2 ms; the line (16,777,240 bytes) **33.4 ms** after; the first read = the state's; still running |
| **the clock** (the hub's clock; a read every second) | 10.005 s → **600** frames · 30.011 s → **1,800** · 60.004 s → **3,600** | 10.016 s → **601** · 30.001 s → **1,800** · 60.001 s → **3,600** |
| **the end:** "time is up" → the final read | 33.3 ms; **3 frames** | 32.8 ms; 3 frames |
| "time is up" → a hub-side pause taking hold (measured, not used) | 33.0 ms; 2 frames; 0 frames in the next 0.5 s; the read after it unchanged | 49.9 ms; 2 frames; 0 |
| the core's state folder under the hub's base config | `Snes9x`; **bsnes: `bsnes`** | `Beetle PSX HW` |

## How the contest ends: running — from the client's source

A read-only study of `PrivyHub/app/src/main/java`, its key lines checked by B:
- **During a stream the onn never reads `paused`:** the heartbeat's reply is discarded (`NativeStreamActivity`);
  `paused` is read only on the main screen (`MainActivity`'s session banner and tile). The only in-stream pause overlay
  ("Reconnecting… / The game is paused until the stream returns") comes from the client's own check (≥ 1 s of silence).
- **The hold's pause is ended by the hub itself:** the first controller packet back resumes it
  (`link_drop_recovery.note_input_release` → `_resume_game`); the onn never has to handle it.
- A pause the hub keeps would leave a frozen picture: the user would have to leave the stream (Home / Back — the paused
  bar RESUME PLAYING · SAVE · LOAD · END) and pick RESUME PLAYING (which would work: `native-stream-ready` resumes on the
  manager's paused flag), and every unpause asks the pads to join again ("Hold any button to join").
- **So the onn does not handle a hub-side pause as it handles the hold's → the contest ends without a pause
  (`"ended": "running"`)**, the final read taken at "time is up" (3 frames late, settled).

## Built (`b101.diff`)

- **`companion/h7_contest.py`** (new) and two routes in `plugins/games.py`, both only with `PRIVYHUB_H7=1` (B99's flag;
  absent / `0`: neither exists — today's "Unknown Games plugin action" / "… POST action: h7-contest", 400).
- **`POST /plugins/games/h7-contest?seconds=N`** (5-300). **(1) Plain refusals** (400, one row each): no game; PS2 /
  GameCube "not supported yet"; N64 "not supported yet — a state cannot be loaded into a running N64 game"; another
  system; "no rule for this game"; "no state for this game's contest" (`<rules folder>/<game id>.state`); "the stream is
  not up"; "a contest is already running"; an unknown core folder; seconds out of range. **(2) The load**, under the
  manager's lock (the hub's LOAD's own): the state copied to **`<state root>/<core folder>/<stem>.state8`** — scratch
  slot 8 (not the user's 1-3; not slot 0, `<stem>.state`, the hub's save/load staging and the last-save copy A calls
  "Continue"; not the rewind's 9; not the recovery's `.state.recovery`); refused if a `.state8` is already there;
  `LOAD_STATE_SLOT 8`; the answer and **RetroArch's own load line within 1.5 s** required, no failure line; **the
  scratch removed in every case**; a failed load → 503 "the contest's state did not load; the game is as it was" (the
  POST path's code for a plain runtime error). The POST then answers `{"contest": "started", "seconds", "load_line_ms",
  "state_values"}`. **(3) Arm:** a read every 0.25 s until the values leave the state's own — at most 20 s
  (`armed_after_s`); else the contest ends "the fight did not start within 20 s; the game left running". **(4) Run:** N
  seconds from arming, a read every second (`samples` `[[t, P1, P2], …]`). **(5)** At "time is up" the final read →
  `{"winner", "reason", "values", "seconds", "armed_after_s", "samples", "resets_seen", "ended": "running"}`;
  **`resets_seen`** counts the samples where every value is back at its armed value after one had been lower (a new
  round) — never used for the winner.
- **`GET /plugins/games/h7-contest`** → `{"contest": null}`, the running contest (`state` arming / running,
  `elapsed_s`, the samples so far) or the last outcome (`done` with the answer, `error`, `ended`).
- **END:** every step checks that the same game still runs and the stream is up; the user's END (the game stopped) or
  the stream stopping → `ended` with one row, no answer; no scratch (removed at the load), no lock held between reads.
- **The log:** one row per step in `logs/games/h7_contests.jsonl` (refused, loaded with the load line's ms, armed /
  not_armed, done with the answer, ended, error); every read also a B99 `h7_reads` row.
- **It changes only what a load changes:** only GET_STATUS, READ_CORE_RAM and one LOAD_STATE_SLOT 8 are sent — no
  pause, save, write or cheat; the user's slots and `<stem>.state` never written.

## Tests (`tests/b101_h7_contest/`, 14; the companion's real HTTP server on loopback)

B99's harness; the fake RetroArch extended (a load that sets its memory from a made-up `<stem>.state8`, writes
RetroArch's own load line into the game log and answers; refuses on demand with RetroArch's failure line; its memory
following a script timed from the load; a command log); a stream stub; made-up slot files 1-3 and the slot-0 copy.

| case | result |
| --- | --- |
| before any contest / no game | `{"contest": null}`; 400 "no game is running" |
| the refusals | "no rule for this game", "no state for this game's contest", "the stream is not up", seconds 3 refused, a second contest "a contest is already running" |
| **end to end** (0 / 0 for 1 s, the bars fill, P1 ahead at the clock) | started with `state_values` 0 / 0; armed at the filled 140 / 140 after ~1 s; `samples` every second to 5 s; **winner P1** (120 / 100), `ended: running`, `resets_seen` 0 |
| **the fake's command log** over a contest | GET_STATUS, READ_CORE_RAM and **one** LOAD_STATE_SLOT — nothing else |
| a new round inside the time (every value back to full) | `resets_seen` **1**; the winner still the leader at the clock (P2) |
| equal at the clock | `winner` null, "no winner yet" |
| a load the fake refuses | 503 "the contest's state did not load; the game is as it was"; **the fake's memory as before** (77 / 33); no scratch left; the last outcome kept |
| a RetroArch that answers the load but writes no load line | the same plain error within the line's bound (1.5 s); the memory as before (added after the first batch's mutation V3 was missed) |
| never armed | "the fight did not start within 20 s; the game left running", within the bound |
| N64 / PS2 sessions | the two "not supported yet" answers |
| **END** (`POST /plugins/games/stop`) during a 30 s contest | `ended`, "the game stopped", no winner; the lock free; no scratch |
| **the user's slots 1-3 and the slot-0 copy** | byte-equal before and after every case |
| the log | rows refused, loaded (game id, load-line ms), armed, done, error, not_armed, ended |
| **flag absent and `0`** | GET / POST `h7-contest` before and after a launch, and seconds=999, on **the baseline's companion** (`git archive 33d8d2cf`) and on this one: **codes and bodies byte for byte equal** |

**3 runs, 14 / 14 each** (`tests_x3.txt`, a work copy of the snapshot with `PrivyHub/`); B99's `tests/b99_h7_live_read` 15 / 15, `tests/client_contract` 5 / 5, `tests/b90_cheat_staged` 10 / 10 in the same copy. Mutations **10 / 10 caught** (`tests_mutations.txt`: the POST route without the flag, the scratch left, the load line not required, armed too early, a new round not counted, a pause at the end, the stream not checked, END not noticed, a second contest, the scratch in a user's slot — refused, as the slot file was there). The first batch: 13 tests, 9 / 10 (V3 missed; `*_first.txt`).

## Disclosed

- The load goes **into running content** (the hub's own LOAD loads while paused); the settle shows it reads exactly.
- A state is loaded by RetroArch's slot command, so RetroArch's current state slot may read 8 afterwards; the hub never
  uses RetroArch's current slot (every save and load names its slot), so nothing changes for the user.
- bsnes' state folder (`bsnes`) is measured here; the hub's default SNES core is bsnes.
- The contest arms on the first values different from the state's own; a game whose bars do not change at a fight's
  start would never arm (the plain error says so).
- **The first batch missed one mutation** (V3: the load line not required) — no case had RetroArch answering the load
  without any line; that case was added and the whole batch run again (`tests_x3_first.txt`, `tests_mutations_first.txt`
  kept).
- RetroArch headless in the settle only (synthetic fixtures); the tests use the fake. Counted: **0 at the end** (`ps`, 02:03Z, after every batch). Intermediate counts of 2 were one headless session of the other item's batch running beside it from its own work copy (noted in `b101_2026-11-12/tests_x3.txt`, `tests_mutations.txt`, `tests_mutations_first.txt`).

## Files

`b101_2026-11-12/`: start files, the design + hash, `settle/` (`contest.py`, `contest_results.jsonl`), `b101.diff`
(applies on `33d8d2cf` + `b100.diff` — it touches neither's files), `tests_x3.txt`, `tests_mutations.txt`, `scripts/`,
`sha256_before_after.txt`, redact / title / cheat-name checks, `manifest.sha256`. Patch note:
`patches/B101_H7_TIMED_CONTEST.md`.
