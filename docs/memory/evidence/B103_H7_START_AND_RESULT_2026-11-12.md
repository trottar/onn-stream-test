---
memory_schema: 1
as_of: 2026-11-12
status: BUILT, NOT ADOPTED (session B, queue AM) — behind PRIVYHUB_H7=1 only, POST /plugins/games/h7-start loads the mini game's kept state (B101's load step alone, PS1 / SNES; ?load=0 skips it on any system) and starts a watcher; GET /plugins/games/h7-result answers no_game / no_spec / idle / watching / ended with the class. The watcher reads the game's window in process about once a second (settled the cheapest: ~12 ms a picture, no frame lost, nothing written — RetroArch's own screenshot lost 120 PS1 frames a minute and writes a file per picture), runs B102's reader, needs the start seen (or loaded) and K = 3 agreeing end reads, then says ended and stops; it sends nothing to the game. Absent / 0 = today, byte for byte against HEAD's companion through the real HTTP route. Synthetic fixtures, a fake RetroArch and a scripted fake picture only; no real title started. Nothing committed. No title, code name, character name or path in this record
---

# B103 — the mini game's two calls: start and result (`PRIVYHUB_H7=1`) (2026-11-12)

**Why (the user's words, 2026-11-12):** "we need to check per game start and end of each mini game so the end we take
that screenshot"; "what if someone who didn't win accidentally says they won". So the hub must know when a mini game
has ended and who won, from the game's own screen, without a clock, a memory read or a player's claim. B99's read and
B101's clock stay in the tree behind the flag, unused; **B101's load step is reused.** **Baseline:** HEAD `8b43a266`.
**Design** hashed before code at 15:57:07Z (`b103_2026-11-12/design.sha256`), after the settle's PS1 windows.

## Settled: the cheapest way to get the running game's picture once a second (fixtures; `settle/picture.py`)

B61's form: RetroArch headless with the hub's AppImage, cores and base config, temp folders, the companion's display;
B94's synthetic PS-X EXE and SNES ROM; no game, no stream. Six 60-s windows per system; the game's frames counted by the
core's own per-frame word (PS1, B99's) and the fixture's counter (SNES), read only at each window's ends.

| one picture a second for 60 s | PS1 (window 879 × 720) | SNES (window 897 × 672) |
| --- | --- | --- |
| **no reader** (frames) | 3,600 · 3,600 · 3,600 · 3,601 | 3,600 · 3,600 · 3,600 · 3,600 |
| **the window read in process** (Pillow's X11 grab of the window's area; the window found by xdotool as the stream finds it) | **3,601 frames**; 60 / 60; **12.1 ms** a picture (worst 15.1); the reader's CPU 0.61 s a minute (~10 ms a picture); the X server +0.2 s a minute; RetroArch unchanged; **writes nothing** | **3,601**; 60 / 60; **11.5 ms** (13.8); 0.58 s; X +0.1 s; nothing |
| the window read by a one-shot ffmpeg x11grab (B52's form) | 3,600; 60 / 60; 168 ms (174); **4.89 s CPU a minute (~81 ms a picture)**; nothing | 3,601; 200 ms; 4.79 s |
| **RetroArch's own `SCREENSHOT`** (the PNG read back and removed, as A's capture did) | **3,480 frames — 120 lost (2 a picture)**; 60 / 60; 89 ms until the file is there (105); RetroArch +1.0 s CPU a minute (~17 ms a picture) + 0.45 s to read the PNGs; **a PNG written per picture** (~10.7 KB on the fixture) into RetroArch's own screenshot folder | 3,601 — none lost; 52 ms (73); RetroArch +0.5 s; a PNG per picture |

**Built: the window read in process** — the least time and CPU, no frame lost on either system, nothing written, the
stream's own capture untouched, and it works for every emulator the hub runs (PS2 and GameCube are not RetroArch).
RetroArch's screenshot costs PS1 frames, writes a file each time (with the hub's config, which names no screenshot
folder, into RetroArch's own config folder) and is RetroArch only.

## Built (`b103.diff`)

- **`companion/h7_minigame.py`** (new) and two routes in `plugins/games.py`, both only with `PRIVYHUB_H7=1` (B99 /
  B101's flag block; absent / `0`: neither exists — today's "Unknown Games plugin action: h7-result" / "… POST action:
  h7-start", 400). B102's learner is imported at the first start or result, not when the companion starts.
- **`POST /plugins/games/h7-start[?load=0]`.** **Refusals (400, one row each):** "no game is running"; "a mini game is
  already being watched"; "no end-screen spec for this game" (`<rules folder>/<game id>.endscreen.json` + its `.npz`) /
  "the end-screen spec for this game cannot be read: …"; with the load: PS2 / GameCube "not supported yet", N64 "not
  supported yet — a state cannot be loaded into a running N64 game", another system "not supported yet", "no state for
  this game's mini game" (`<game id>.state`); "the stream is not up"; an unknown core folder; "load is 0 or 1".
  **The load:** B101's `_load` and `_core_file` themselves, through a small subclass whose rows go to this item's log
  (B101's file not edited): scratch slot 8, `LOAD_STATE_SLOT 8`, RetroArch's own load line within 1.5 s, the scratch
  removed in every case; a failed load → 503 "the mini game's state did not load; the game is as it was". **No clock,
  no read of memory, no B99 rule.** Then the watcher begins → `{"watch": "started", "game", "loaded", "load_line_ms"}`.
  With `?load=0` the load is skipped (any system) and the watcher must see the start itself.
- **The watcher** (a thread): every 1.0 s — the same game still running (else **`stopped`**, one row, "the game
  stopped"); one picture (a failure → one `picture_failed` row, the watch goes on); B102's `Reader` (its alignment kept
  per watch) and `Ended` (K = 3; **an end class counts only after the start was seen, or the load done**); `ended` →
  the class, one row, **it stops reading**. `unknown` is the current class, logged once per stretch, never an end. **It
  sends nothing to the game** — no pause, save, key or memory read.
- **`GET /plugins/games/h7-result`** → `{"state": "no_game" | "no_spec" | "idle" | "watching" | "ended", "class",
  "seen_start", "since_s", "reads", "last": {"distances", "margin"}}` (+ `ended_after_s`, `loaded`,
  `picture_failures`; `no_game` carries `"stopped"` after a watch the game's stop ended). **`idle`** (a game and its
  spec, no watch) is added — the queue's four states do not name that case.
- **The log:** `logs/games/h7_results.jsonl` (new, git-ignored, beside `h7_reads` / `h7_contests`): `refused`,
  `loaded`, `error`, `watching`, `start_seen`, `unknown_screen`, `ended`, `stopped`, `picture_failed`.

## Tests (`tests/b103_h7_minigame/`, 13; the companion's real HTTP server on loopback)

B101's harness and fake RetroArch (its load, refusal, silence and command log); a stream stub; **a fake picture source
the test scripts** — synthetic frames drawn as in B102's tests (start 0-0, end_P1 1-0, end_P2 0-1, unknown 1-1, other);
a spec learnt in the test from B102's synthetic runs and put in the test's rules folder; reads every 0.2 s in the test.

| case | result |
| --- | --- |
| no game | `no_game`; the start 400 "no game is running" |
| no spec / a spec that cannot be read | `no_spec` with the reason; the start 400; then `idle` |
| **the load's refusals as B101's** | no state, "load is 0 or 1", the stream not up, N64 and PS2's answers; a load the fake refuses and one with no line → 503, **the fake's memory as before**, no scratch left; `idle` after |
| **start → watching → the end screen → `ended` after K** | loaded; start ×2, other ×5, P1 end ×2, other, P1 end ×3 → **`ended`, end_P1, at read 13 exactly**, `watching` before; then **no more reads** (13 pictures taken in all); a second start meanwhile refused |
| **the fake's command log** | over the loaded watch **one `LOAD_STATE_SLOT` and nothing else**; over two `load=0` watches **nothing at all** |
| **an end before any start** (`load=0`) | P2 end ×5 not counted (`seen_start` false), other ×3, start ×3, P2 end ×3 → `ended` end_P2 at read 14 |
| **an unknown screen** (1-1) | `watching`, `class: unknown` — never `ended`; one `unknown_screen` row; then P1 end ×3 → ended |
| a failed picture | two `picture_failed` rows; the watch goes on → `ended` at read 6 |
| the watcher alone on a PS2 session (`load=0`) | started, `ended` end_P2, no command sent |
| **an `other` stretch, then END** | 25+ other reads: `watching`, never `ended`; `POST /plugins/games/stop` → `no_game`, `"stopped": "the game stopped"`, one `stopped` row; the lock free; no scratch |
| **the user's slots 1-3 and the slot-0 copy** | byte-equal before and after |
| the log | one row per change: 5 `ended` (the right classes), 1 `stopped`, 2 `picture_failed`, 1 `unknown_screen`, `refused` / `loaded` / `error` / `watching` / `start_seen`; nothing in B101's log |
| **flag absent and `0`** | GET `h7-result`, POST `h7-start` and `?load=0` before and after a launch on **HEAD's companion** (`git archive 8b43a266`) and on this one: **codes and bodies byte for byte equal** |

**3 runs, 13 / 13 each** (`tests_x3.txt`, a work copy of the snapshot with `PrivyHub/`); in the same copy **B99's
`tests/b99_h7_live_read` 15 / 15, B101's `tests/b101_h7_contest` 14 / 14, B102's 16 / 16, `tests/client_contract`
5 / 5, `tests/b90_cheat_staged` 10 / 10**; temp dirs left 0; RetroArch 0. **Mutations 11 / 11 caught**
(`tests_mutations.txt`: the routes without the flag, the start taken as seen without a load, K ignored, a row per
unknown read, a failed picture stopping the watch, the game's stop not noticed, a command sent at the end, a second
start loading before its refusal, `load=0` still loading, the stream not checked, the load's rows in B101's log).

## Disclosed

- **The first batch found a defect in my code:** with the flag on, the module imported B102's learner from `tools/`
  when the companion started, so a companion without that file in `tools/` failed to start — B99's and B101's suites
  (whose fixture trees carry no `tools/`) errored (`tests_x3_first.txt`). **Fixed:** the learner is imported at the
  first start or result. The first batch's mutations were stopped part-way (7 run, 7 caught;
  `tests_mutations_first.txt`) and the whole batch run again on the fixed code. Leftover temp folders of the stopped
  runs (7, under B's own `~/.cache` scratch) removed.
- **The settle's first RetroArch-screenshot windows looked in the wrong folder** (the content folder; RetroArch writes to
  its own config folder's `screenshots/`) and read 0 of 60 — their frame and CPU costs stand (RetroArch did take every
  picture). Measured again with the right folder (`picture_results_r.jsonl`); the 60 files of the first run were in the
  settle's temp folder and went with it.
- The window read takes the window's area on the display (what is visible there); the stream's capture reads the same
  window. A window covered by another would be read covered (the hub's display shows only the game).
- B102's evaluation ran beside the settle (one core, niced); the frame counts are the core's own.
- RetroArch headless in the settle only; **0 left at the end** (counted after each run, `settle/*.jsonl`).

## Files

`b103_2026-11-12/`: start files, the design + hash, `settle/` (`picture.py`, `picture_results_first.jsonl`,
`picture_results_r.jsonl`), `b103.diff` (applies on `8b43a266` + `b102.diff`), `tests_x3.txt`, `tests_mutations.txt`
(+ `*_first.txt`), `scripts/` (`run_all.sh`, `mutate.py` — B101's runner, unchanged — `mutations.json`),
`sha256_before_after.txt`, redact / title checks, `manifest.sha256`. Patch note: `patches/B103_H7_START_AND_RESULT.md`.
