---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AX) — three small things. (1) The hub, behind PRIVYHUB_PARTY=1: the pads' Select is held from a held title's launch until a real go, practices included, so in a practice Select + L1 / R1 / Start / R3 no longer load, save, quit or unpause; a real mini game as today. (2) My board file: once the hub has handed a practice over, the load screen is shown again behind it (every mark clear; the pads still swallowed while the hub's game is on), so the way back lands on the load screen. (3) My board file: one log line for the players' choice ("cards <n>, chose <0 | 1 | random>") and one for each go ("start" / "practice"), never a game's name. Tests: the hub 4 (x3); the board's check PASS 89 (was 81) x5; B111 updated. Nothing adopted; nothing committed in either repo
---

# B145 — three small things

Queue: `handoffs/QUEUE_2026-11-18AX.md` §B145. The directory is `b145_2026-11-18/`: the design + `.sha256` (hashed
04:19:36Z, before any code), `b145.diff` (this repo), `b145_board.diff` (my two files against the board's `4140949`),
`board_files_before.txt` / `board_files_after.txt`, `check_runs.txt`, `scripts/run_check.sh`, the checks,
`manifest.sha256`. The hub's runs are in `b143_2026-11-18/`. Patch: `patches/B145_PARTY_SMALL_THINGS.md`.

**The board's repo:** only `minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` changed (uncommitted there).
Before `e580c3e1…` / `76018a20…`, after **`a1e648f3dfd391580d5450768c9d1ab7bf2e8924d0c0cb3c9f15579de612d0d6`** /
**`95eb6f89ab07430ff1ec078e66a0144d36f27892f309776b81f310889e600014`**. The presenter, the screens and the rules were
not touched. Godot ran headless only, in a scratch copy of the board's tree.

## 1. Select through a practice too (the hub)

`_handover` cleared the hold at every go (B141). It now clears it only for a real go (`if not go["practice"]`), so the
hold that is on from the launch stays through a practice. The way back's hold (already on) and every end's release are
as before. A practice's Start hook (B134) reads Start from the report before the hold clears Select, so **Select +
Start still leaves a practice** (Start passes) **without quitting the title**.

**Tests** (`tests/b145_party_small_things/`, 4, on B114's scenario's `nopress` mode, after B141's case): a held start,
then a practice. While it plays, Select + L1 / R1 / R3 go from all four pads every 0.2 s for 1.5 s, and the virtual
pads are written (> 20 writes) but **never with Select**: **the fake title's hotkey log stays empty and its state
folder byte-equal**. Select + Start then leaves the practice (`"by": "start_button"`), with the title still running and
the log still empty. After a real go, Select alone is written; the hold is off after it and after the end. **The
mutation (HEAD's line restored, `b143_2026-11-18/tests_mutations.txt`):** the same practice lets Select through and the
fake logs the hotkeys (2 of 4 fail).

## 2. The load screen already up when a practice ends (my board file)

The user: "went to the board for a second or two and now back at the load screen". The board used to hide the load
screen at a practice's `"playing"` and show it again at the next `"starting"`, after the hub's way-back switch, so the
board showed for a poll or two. **Now:** at the hub's first `"playing"` after a go that was a practice, the board calls
`show_minigame_loading` again (every mark clear; the presenter's own words: "Called again (after a practice), it starts
again the same way"). It does not hide the screen, and the pad gate stays. At the hub's next `"starting"` the gate goes,
the readiness is told afresh and the go may be sent again, all on the screen that is already up. A real go is hidden at
`"playing"` as before.

## 3. One line for each choice and each decision (my board file)

`PrivyParty: hub mini game: cards <n>, chose <0 | 1 | random>` is printed once the players chose on the selection
screen (any other answer is today's pick, the first card, so `0`). `PrivyParty: hub mini game: <start | practice>` is
printed at each go the hub took. Numbers and words only.

## The check (`checks/hub_minigame_check.gd`, extended: **PASS 89 assertions, five runs**; was 81)

The made-up presenter now records the stand-in hub's mode at each showing and counts pad presses that reach the load screen shown
behind a practice while it plays. The check catches the board's own log lines with a `Logger` of its own (`OS.add_logger`). New
assertions:
- the lines for two cards / card 0, card 1, Random, one card, each with its `start` and the board's existing scores line;
- three practices and a real go: `cards 2, chose 0`, `practice` ×3, `start`, in order;
- no line carries a made-up name;
- **each practice's load screen shown while the hub still answered "playing" (a practice)**, before its answer left
  `"playing"`;
- hidden only at the real playing (1; was 4);
- a pad pressed every 0.3 s through the whole case: **none reached the load screen shown behind a practice**, and
  every go came with the hub ready (none from a press in a practice).

**Found while running it (recorded in `check_runs.txt`):** my first three runs gave PASS, PASS, then one press counted
in a practice. That press came in the frame or so between the hub taking a practice's go and the board's pad gate going
up, while the load screen of before the hand-over was still up. The re-show at the hand-over clears every mark, so it
made no go and nothing reached the board. The check now counts from that re-show, which is what B145 asks; the gate
mutation still fails it (26 presses counted).

`check_runs.txt`: five runs PASS (89) on the final check; B111 (Godot headless, its scratch copy, its own fake hub)
PASS (89) and PASS (63) with its counts and the lines' checks updated, run again on the final check: OK; the PC side's
`step25_before_minigame` PASS (107) and `step8` PASS (210) once (read only). **Mutations (3 / 3):** the show at the hand-over removed, the go's line removed, the gate left off in a practice → the
check FAILs each time (`b143_2026-11-18/tests_mutations.txt`).
