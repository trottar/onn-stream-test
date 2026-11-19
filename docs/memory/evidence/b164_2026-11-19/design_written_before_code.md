# B164 — the board check's one FAIL in nine (design of the fix, written and hashed before the change)

Queue: `handoffs/QUEUE_2026-11-19BC.md` §B164. The board's repo at `9a803d6` (my two files committed there, on the PC
side's `bb9dcd5`). Written after reading the code and the first traced runs, before any change to either file.

## What the assertion counts, and where the window is

"no press made during a practice reaches the load screen shown behind it" counts, in the check's made-up presenter
(`FakeScreens._input`), a pad press reaching it while `up and behind` and the stand-in hub's mode is `"practice"`.

- `behind` is set at each showing (`show_minigame_loading`) from the stand-in hub's mode then, and **only changed at
  the next showing**. In the three-practice scenario the screen shown behind practice 1 stays up through practice 1's
  end (the board does not show it again, it is already up) — so `behind` is still true when practice 2's go is sent.
- The stand-in hub turns its mode to `"practice"` **when it takes the go** (`_held_answer`, `party-minigame-go`),
  before its answer reaches the board. The board puts its pad gate up **when that answer arrives** (`play()`:
  `went = true` … `gate = PadGate.new()`).
- So for practices 2 and 3, a press from the poking loop (every 0.3 s) that lands between the stand-in taking the go
  and the board's gate going up reaches the presenter with `behind` true (left from the last practice) and the mode
  `"practice"` (the new one) — and is counted, though the practice it is counted against has not been handed over
  and the screen it reached is the one the players are choosing on. The check's own comment (lines 350-351) names this
  press as harmless; the counter's stale `behind` lets it through. Two such windows per run, each a frame or two.

## The board's behaviour at the TV (read, not changed)

The real hub answers the go at once and hands the title over after the planned switch (~1.3-1.9 s): the TV still
shows the load screen in that time, and the board's gate is up from the go's answer. A press in the go's own round
trip reaches the load screen **while it is on the TV, made on that screen**; the board has `went = true` so no second
go is sent, and the re-show at the hand-over clears every mark. On the way back the hub answers `starting` only after
the switch to the board has returned (`_way_back`), so the board takes its gate down only once the board is on the TV.
**Neither a ready mark nor a go can come from a press nobody made on that screen.** So this is the check's timing.

## The fix (my check only; `minigames/hub_minigame.gd` unchanged)

The stand-in hub counts the practice goes it has taken (`practice_goes` beside `mode`); the presenter keeps, at each
showing behind a practice, that count (`behind_go`), and counts a press only while the stand-in's count is still the
same — **a press during the practice the screen was shown behind**, which is what the assertion's words say. A press
before a later practice's hand-over is not that. Nothing else in the check changes; the assertion's text unchanged.

## Shown

Thirty traced runs of HEAD's two files (`bb9dcd5`) and thirty of mine (`9a803d6`), two streams side by side; each
counted press with its trace (its time, the showings so far, whether the board's gate was in the tree). Then thirty of
the fixed check. A scratch probe that presses at the moment the stand-in takes practice 2's go: counted by the old
check (FAIL every time), not by the fixed one (PASS). The fixed check still catches the real fault: the board's
practice gate removed (a scratch mutation of `hub_minigame.gd`) → FAIL. The PC side's step28 with the fixed check.
