# B160 — one line in my board file (design, written and hashed before the edit)

Queue: `handoffs/QUEUE_2026-11-18BB.md` §B160. The board's repo: only my two files, `minigames/hub_minigame.gd` and
`checks/hub_minigame_check.gd` (before: sha256 `3f32d339…` and `01301ec5…`; the board's HEAD `bb9dcd5`, status 0 lines).

**Settled (read only):** the picker's `elsewhere(script)` (`game/minigame_picker.gd`) takes a mini game's own
`ELSEWHERE` when it says it, else guesses from `FIRST_WHERE` (mine names `PRIVYPARTY_ON_HUB`, so the guess is true
today). The PC side's step28 check builds its own scripts with `ELSEWHERE` true and false.

**The change:**
1. `minigames/hub_minigame.gd`: `const ELSEWHERE := true` after `const ID := "hub"`, with a two-line comment (played on
   the hub's emulator, the board only waits: the board is told, it need not guess). Nothing else in the code.
2. The same file's header comment, line 30: "its Start pressed within a poll of the hand-over" → "its Select pressed
   within a poll of the hand-over" (queue AZ's item 3; a comment).
3. `checks/hub_minigame_check.gd`: one assertion more beside the registry's — the script's constant map has
   `ELSEWHERE == true`, and the picker's `elsewhere()` says true for it.

**Proof:** the check run with Godot headless in a scratch copy of the board's tree (main disk), PASS with the count
one more than before; both files' sha256 after; the board's status shows only my two files.
