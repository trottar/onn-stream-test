# PrivyParty, PC side — a practice is left by Select, not Start (2026-11-18)

From the hub side, for the PC side. Small: one line of words, its check, and the two documents.

## What changed on the hub, and why

Until now the hub ended a practice when any pad pressed **Start** (or after about 90 seconds). One of the hub's games needs Start to begin its match, so a practice of it would end the moment anyone tried to start. The owner chose: **the pad's Select button (Share on a PlayStation pad) leaves a practice, in every game; Start goes to the game.** The 90 seconds stay. The hub side is building that now; the band the hub draws on the TV during a practice will read "PRACTICE — press Select (Share) to go back".

Nothing about the five methods, the ready check, who picks, or the board's own buttons changes. The board's own pause is still its Start button.

## What the board needs

1. `game/minigame_screens.gd` — `PRACTICE_ENDS` now says "A practice ends with the Start button, or after about 90 seconds." Change the words so they name the **Select** button, say that on a PlayStation pad it is **Share**, and keep "about 90 seconds". Word it as you word the rest of the screen; it must still fit on its line.
2. `checks/step25_before_minigame.gd` — the assertion on `PRACTICE_ENDS` (it looks for "Start" and "90"): look for "Select" and "90", and that "Start" is not there.
3. `README.md` and `HANDBACK.md` — wherever they say a practice ends with the Start button (HANDBACK: "the practice's Start button is the hub's"), say Select (Share).

## Not to touch

- `minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` — the hub side's.
- The rules: the same seed gives the same game.
- No name or picture of a real game anywhere in git.

## Done when

Every check PASS (say each count that changed), the load screen's line reads right at 1920×1080, README and HANDBACK updated, committed and pushed.
