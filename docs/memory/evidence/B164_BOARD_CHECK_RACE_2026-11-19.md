---
memory_schema: 1
as_of: 2026-11-19
status: SETTLED AND FIXED (session B, queue BC) — the board check's one FAIL in nine ("no press made during a practice reaches the load screen shown behind it", got 1) is the check's own timing, not the board's behaviour: its made-up presenter kept "shown behind a practice" from the last practice, and the stand-in hub turns "practice" as it takes the next practice's go, a frame or so before the board's pad gate goes up — a press in that frame was counted against a practice not yet handed over. Not a fault at the TV. Fixed in my check only (the press counted only during the practice the screen was shown behind); hub_minigame.gd unchanged. Nothing adopted; nothing committed in either repo
---

# B164 — the board check's one FAIL in nine

Queue: `handoffs/QUEUE_2026-11-19BC.md` §B164. The board's repo at `9a803d6` (my two files committed there on the PC
side's `bb9dcd5`). The directory is `b164_2026-11-19/`: the design + `.sha256` (hashed 04:42:31Z, before the change),
`b164.diff` (the board's `git diff`: my check only), `sha256_before_after.txt`, the runs (`head_30.txt`,
`mine_30.txt`, `fixed_30.txt`, `probe/`, `counted_after_go.txt`, `step28_with_fixed.txt`), `scripts/b164_runs.sh`, the
checks, `manifest.sha256`. Patch: `patches/B164_BOARD_CHECK_RACE.md`.

## The runs (each with the failing assertion's own trace kept)

The runner (`scripts/b164_runs.sh`, B145's way: a scratch copy of the board's tree, Godot headless, Godot's folders in
the scratch, removed after) adds a trace **to the scratch copy only**: each go the stand-in hub takes in the
three-practice scenario, each showing of the load screen there, and **each press the made-up presenter counts** (its
time, the showings so far and their modes, whether the board's pad gate was in the tree).

| run set | runs | PASS | FAIL | presses counted |
| --- | --- | --- | --- | --- |
| HEAD's two files (`bb9dcd5`), `head_30.txt` | 30 | 28 | **2** (runs 17, 27) | 2: at practice 3's go, 6 and 7 ms after the stand-in took it, the board's gate not in the tree |
| mine (`9a803d6`), `mine_30.txt` | 30 | 28 | **2** (runs 18, 20) | 2: at practice 3's and 2's go, 6 ms after, the gate not in the tree |
| **the fixed check** (`9a803d6` + this diff), `fixed_30.txt` | 30 | **30** | 0 | 0 |
| probe — a press made exactly as the stand-in takes practice 2's go (`probe/probe_press.diff`, scratch only) — the old check (`9a803d6`) | 3 | 0 | **3** | 5: every one 7 ms after practice 2's or 3's go, the gate not in the tree |
| the same probe, the fixed check | 3 | **3** | 0 | 0 |
| the fixed check, **the board's practice gate removed** (`probe/board_mutation.diff`, scratch only) | 2 | 0 | **2** | 20 a run, all inside the practices |

HEAD's and mine ran side by side (two streams, the same load), with the fixed check's thirty, B162's suites and the
mutations alongside part of the time. **The natural FAIL is rare** (1 in 9 in queue BB; **2 in 30 on HEAD's files and 2 in 30 on mine** — the same on both, so not my B160 change); **the probe makes it
every time**: in its runs 2 and 3 a press from the check's own poking loop landed in the same window too.

## What it is

- The assertion counts, in the check's made-up presenter (`FakeScreens._input`), a pad press reaching it while it is
  up, `behind` is set, and the stand-in hub's mode is `"practice"`.
- `behind` is set at a showing of the load screen and changed only at the next showing. After practice 1 the screen
  shown behind it **stays up** (the board does not show it again), so `behind` is still true when practice 2's go is
  sent.
- The stand-in hub turns `"practice"` **as it takes the go** (`_held_answer`), before its answer reaches the board; the
  board puts its gate up **when the answer arrives** (`play()`: `went = true` … `PadGate.new()`).
- So a press in that frame or two — **made on the load screen, before the practice is handed over** — was counted
  "during a practice". Every counted press in the traces is at a practice's go after the first, with the board's gate
  not yet in the tree and the screen still the one shown behind the practice before. The check's own comment (its
  lines 350-351) names exactly this press as harmless; its counter's stale `behind` let it through.

## At the TV: not a fault

The real hub answers the go at once and hands the title over after the planned switch (~1.3-1.9 s); the TV shows the
load screen until then and the board's gate is up from the go's answer. A press in the go's own round trip reaches the
load screen **while it is on the TV, made on that screen**: the board has `went = true`, so no second go is sent, and
the re-show at the hand-over clears every mark (no player left marked ready). On the way back the hub says `starting`
only after its switch to the board has returned (`_way_back`), so the board takes its gate down only once the board is
on the TV. **No ready mark and no go can come from a press nobody made on that screen.** Nothing for the PC side.

## The fix (my check only)

The stand-in hub counts the practice goes it has taken (`practice_goes`); the presenter keeps that count at a showing
behind a practice (`behind_go`) and counts a press only while the count is unchanged — **a press during the practice
the screen was shown behind**, the assertion's own words. 11 lines added, 1 changed; the assertion's text unchanged;
`minigames/hub_minigame.gd` unchanged (sha256 `920d0073…`). The check: `5d51ffa2…` → `a71b4d8f…`, **PASS 98 assertions**
(**30 of 30**); the PC side's **step28 PASS (59)** with it (`step28_with_fixed.txt`).
