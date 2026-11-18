# B145 — three small things: design (written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AX.md` §B145. Baseline `baseline_head.txt`; the board's repo at `4140949` (clean), my
two files `minigames/hub_minigame.gd` `e580c3e1…`, `checks/hub_minigame_check.gd` `76018a20…`.

## 1. Select through a practice too (the hub; `PRIVYHUB_PARTY=1`, absent = today)

Today (B141) `_handover` clears the hold at every go: `self._hold_select(mg, False)` — a practice's go too, so in a
practice Select + L1 / R1 load / save over the setup's slot, Select + Start quits, Select + R3 toggles the pause.
**Changed:** that line runs only for a real go (`if not go["practice"]`). So Select is dropped from every pad's report
from a held title's launch (the hold already on there, B141) **until a real go, practices included**; the way back's
`_hold_select(mg, True)` stays (already on: no change on the wire); every end's release as today; a real mini game from
its go as today. The practice's Start hook (B134) sees the report before the hold clears Select (it reads Start only):
unchanged. A start without `hold`: no practices, unchanged.
**Tests** (`tests/b145_party_small_things/`, B141's way on the B137 `nopress` scenario through the real HTTP server):
from a practice's go to its way back, Select + L1 / R1 / Start / R3 from all four pads every 0.2 s → **no virtual
pad's Select written, the fake RetroArch's hotkey log empty, its state folder byte-equal**; the practice left by a
Start alone (passes); a real go after it → Select alone from pad 1 written (passes). HEAD's code (the mutation): the
same presses in a practice reach the fake (its hotkey log not empty).

## 2. The load screen already up when a practice ends (my board file)

The user: "went to the board for a second or two and now back at the load screen". Today the board hides its load
screen at the hub's first `"playing"` (a practice's too) and shows it again at the first `"starting"` after it — after
the hub's way-back switch, so the TV shows the board for a poll or two first.
**Changed (`minigames/hub_minigame.gd`):** when the hub answers `"playing"` for a go that was a practice (the go this
showing sent was `practice`), the load screen is **shown again at once** (`show_minigame_loading`: every mark clear —
the presenter's own comment: called again, it starts again the same way), not hidden; the pad gate stays (the pads
swallowed while the hub's game is on: no press made during the practice reaches the load screen); when the hub answers
`"starting"` again the gate goes, the readiness line is told afresh, the go may be sent again — **the screen is already
up, so the way back's switch lands on it.** A real go: hidden at `"playing"` as today. A stage without the screens: as
before.
**The check (`checks/hub_minigame_check.gd`, extended):** the made-up presenter records the stand-in hub's mode at each
`show`: after each practice's go the show comes **while the hub still answers "playing" (a practice)** — before its
answer leaves `"playing"`; the load screen hidden only at the real playing (1); a pad press made during each practice
reaches neither the board's controls nor the load screen; **no go from it** (three practice goes, one plain, each with
the hub ready).

## 3. One line in the board's log for each choice and each decision (my board file)

`print("PrivyParty: hub mini game: cards %d, chose %s")` once the players chose on the selection screen — the number of
cards, then `0` / `1` (the card) or `random`; anything else (today's pick, the first card) → `0`. And
`print("PrivyParty: hub mini game: %s")` with `start` / `practice` at each go the hub took. Numbers and words only —
**never a game's name** (the names stay on the screens). **The check reads them** with a logger of its own (Godot's
`Logger` / `OS.add_logger`): the lines for one card, two cards with card 0, card 1, Random, and the decisions
`practice` ×3 then `start` in order; no line carries a made-up name.

## Then

The check PASS three runs (the stand-in hub); B111's test (Godot headless, the scratch copy, the test's fake hub) with
its counts updated; the two board files' sha256 before / after in the record; the PC side's step8 once (read only).
