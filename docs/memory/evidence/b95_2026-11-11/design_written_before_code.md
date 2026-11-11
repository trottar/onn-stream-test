# B95 — B93's tool reads a state as it stands; "no winner yet"; the proof's statement (design, before code; queue AI)

**Why (Cowork's correction, carried):** the tool runs headless with no pads — a fight is not replayed. What a state can
prove, read as it stands: the "end" state names the player the TV showed, the "begin" state names no winner yet, an end
won by another player names that player, the same on every load.

## Settled first (B94's settle, synthetic fixtures)

A state loaded **while paused** is read exactly: 0 frames pass (the SNES fixture's frame counter unchanged), every byte
as saved, 3 loads the same — on snes9x, Beetle PSX HW and Mupen64Plus-Next. RetroArch 1.22.2 logs a load as
`[State] Loading state "…", N bytes.` (N > 0) and a failure as `Failed to load state from "…"` (a corrupt fixture file:
0 bytes, then the failure) — B93's check ("a `[State]` line with 'oad' and the file's name") would accept the failure
line too; it is tightened.

## Built (`tools/h7_minigame_proof.py`)

- **`--as-is`** (also `--seconds 0`): pause first, load the state paused (the tightened check: the `Loading state …
  N bytes` line with N > 0 and no failure line within 1 s), read, quit — **0 frames run** on the cores measured (stated in
  the help; the test measures it on the fixture's frame counter). `--seconds N > 0` keeps B93's run (load, run, pause).
- **The rule's `"none_when": "equal"`** (or `"none_when": {"floor": V}` — every player at or below V): the answer
  `"winner": null` with `"reason": "no winner yet"`, distinct from `"tie"`; a rule without `none_when` answers as B93's.
- **B94's single-field rules** (`"address"` + `"values": {"P1": v, …}` + `"none_value"`) read too: the player whose value
  it holds; `none_value` → no winner yet; anything else → `"unknown"`.
- **`--runs N`** repeats the whole load-and-read N times (fresh RetroArch each) and reports, in the one JSON line,
  `"runs": N`, `"agreement": "k of N"` (the most common winner's count), every run's winner and values — a disagreement is
  reported, never hidden; the top-level `winner` is the agreed one only when k = N, else `"winner": "disagree"`.
- **The help and ROADMAP §H7:** "Met on a real game when, read as they stand, the 'end' state names the player the TV
  showed, the 'begin' state names no winner, and — where the user has made one — an 'end' state won by another player
  names that player; the same on 3 loads each. The fixed run with real players is tested later, on the stream." (ROADMAP:
  an insertion; the old line kept and marked superseded.)

## Tests (`tests/h7_minigame_proof/test_b95_as_is.py`; B93's five unchanged)

On the counters fixture (`fixture_counters.py`) — states made with `--make-state` and the counters written: begin (equal),
P1 ahead, P2 ahead: **`--as-is --runs 3` → none / P1 / P2, "3 of 3" each**; the frames passed before the read: the
SNES frame counter (a second fixture field written into the state and read back) unchanged — **0, bound 0**; a
disagreement — a rule on the fixture's free-running frame counter at `--seconds 0.3 --runs 3` (each run stops at a
different frame) — reported as fewer than 3 of 3 with `"winner": "disagree"`; the rule logic (none_when equal / floor,
tie, the single-field form) without an emulator; a corrupt state → an error. Temp dirs removed; no RetroArch left.
