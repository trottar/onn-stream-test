# PrivyParty, PC side — a mini game that ends in a draw pays half (2026-11-20)

From the hub side, for the PC side. One rule, its check, and the two documents.

## Why

The hub can now read a winner from the scores on a game's final screen, so a mini game can end level (both sides on the same score). Today the board pays that as if everyone had won: `rules/game.gd`'s mini game turns equal scores into places `[0, 0, …]` and pays every player `minigame_payout[0]` (10 coins by default), with nobody counted as winning. A mini game the hub has to give up comes to the board as a draw too, and pays the same.

The owner's choice, in his words: **"I guess half makes more sense then the full amount."**

## What the board needs

1. **A mini game where every player ends level** — every place 0, including the board's own draw (an answer that is not one number per player, i.e. given up) — pays every player **half of `minigame_payout[0]`, rounded down** (5 coins by default). Nobody is counted as winning (as today).
2. **Nothing else changes:**
   - **Duels:** a draw already pays nothing and moves no stake. Keep it.
   - **A partial tie** (some players level for a place, but not all of them level) pays as today: players tied for a place each get that place's payout.
   - The payout table itself, the record's fields, and the winner screen's behaviour for a real win stay as they are. Say what the result screen shows for a draw now, and keep it truthful (no winner named).
3. Say in your reply whether this belongs in `game_config.gd` as its own setting (e.g. a draw's share) or as a fixed rule, and why.

## The checks

- A new assertion, or a change to the check that covers mini-game payouts: two players level → 5 each; four players level → 5 each; the board's own draw (a given-up mini game) → 5 each; a partial tie as today; a duel draw pays nothing. Every earlier check still PASS (say each count that changed).
- **The same seed gives the same game** as far as the dice and the board go; coin totals after a drawn mini game change by design — say which checks' expected numbers you updated and why.

## Not to touch

- `minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` — the hub side's.
- No name or picture of a real game anywhere in git.

## Done when

Every check PASS, README and HANDBACK say how a draw pays, committed and pushed.
