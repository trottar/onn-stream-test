---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AY) — a practice that came and went unseen, in my board file; the hub's answer as it is (it already carries "practices" in every held state, so nothing more is needed from it). When the hub's practices count rises while the board still waits on a go it sent, the board takes the practice as come and gone, whether or not it ever saw "playing": the load screen shown again (every mark clear, the gate having kept the pads from it), the pads back, the next choice taken at once. One more log line at every re-show after a practice: "PrivyParty: hub mini game: load screen again". The check PASS 97 (was 89); B111 updated (97 / 68). Nothing adopted; nothing committed in either repo
---

# B149 — a practice that came and went unseen

Queue: `handoffs/QUEUE_2026-11-18AY.md` §B149 (my AX item 2). The directory is `b149_2026-11-18/`: the design +
`.sha256` (hashed 07:41:35Z, before any code), `b149.diff` (this repo: B111's test), `b149_board.diff` (my two files
against the board's `32d5329`), `board_files_before.txt` / `board_files_after.txt`, `check_runs.txt`, the checks,
`manifest.sha256`. Patch: `patches/B149_PARTY_UNSEEN_PRACTICE.md`.

**The board's repo:** only `minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` changed (uncommitted there).
Before `a1e648f3…` / `95eb6f89…`, after **`3f32d3392cf878e105b637f98f567395658c0f3ac4f2421c16111f54d1ff3875`** /
**`01301ec5f19fa0e14f325582cd99b96147edc505f70dca54b16a9e514d69341b`**. Godot ran headless on scratch copies only.

## The hub's answer, as it is

`PartyMinigames.result` puts `"practices"` in every answer for a held start (starting, playing, after a way back). The
board needs nothing more.

## Built (`b149_board.diff`)

- The board keeps the `practices` count of the hub's last answer, and at each go the hub takes, the count then
  (`practices_at_go`).
- On a `"starting"` answer while the board still waits on its go (`went`) and the count has risen: if the board already
  re-showed the load screen at the practice's `"playing"` (B145), as before. **If it never saw `"playing"`, it shows
  the load screen again now** (every mark clear: the pad gate kept the pads from it until this moment, so no press made
  during the practice counts), takes the gate down, and tells the readiness afresh. **The next choice is taken at the
  next 0.25-s read, not after the 20-minute bound.**
- `PrivyParty: hub mini game: load screen again` is printed at every re-show after a practice: at B145's re-show at the
  hand-over, and at this one. Once a practice.

## The check (`checks/hub_minigame_check.gd`, extended: **PASS 97 assertions, three runs**; was 89)

- A new stand-in scenario `hunseen`. The hub's answers go `ready` → (the practice go) → `starting` / `preparing` with
  `practices` 1, **never `playing`** → `ready` → (a plain go) → playing → ended. Asserted: the case ends in seconds;
  the load screen shown again (2 shows, the second once the hub was back); hidden only at the real playing; the goes
  `practice`, `start`; **the second go within 1.5 s of the hub's first `ready`**; the lines `cards 2, chose 0`,
  `practice`, `load screen again`, `start`, the scores.
- The three practices case: `load screen again` after each `practice`, in order.
- Every earlier case unchanged.
- B111 (this repo's test, Godot headless on its scratch copy, against its own fake hub, which now answers `hunseen` the
  same way): **PASS (97) and PASS (68)**; the goes `practice`, `start` for `hunseen`; the new line in its output; 20
  mini games ended.

**Mutations** (`b147_2026-11-18/tests_mutations.txt`): the unseen branch removed → the check never finishes (the board
waits on its long bound); the line removed → the check FAILs.
