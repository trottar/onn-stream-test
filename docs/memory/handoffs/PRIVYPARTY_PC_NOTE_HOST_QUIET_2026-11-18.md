# PrivyParty, PC side — the host stays quiet around a hub mini game; no bare board before the load screen (2026-11-18)

From the hub side, for the PC side. Four people played the board on the hub tonight with four pads: two rounds' ends and two duels went to the hub's games through your selection screen, load screen, ready check and practice, and every result came back to the right players. Your screens did their job. Two things the four said are the board's.

## What they said, verbatim

- After the first round's end: "Mini game, P1 (host spoke on loading then p1 character spoke because of win, host should not speak on load screens ever)"
- After the second: "Mini-game 2...P4(went to board for a second before load this time)"
- After the first duel: "Load screen went properlu then practice. Then started properly / P3 won. No host voice this time only p3 voice upon winning"
- After the second duel: "P4 won, went to board for a second first before load. Host spoke before p4 again"

So: the host spoke around two of the four mini games and not the other two; the bare board showed for about a second before the load screen in two of the four.

## What the board needs

1. **The host never speaks around a mini game that is played somewhere else.** From the moment such a mini game or duel is decided until its result is on the board again: no host line — not on the selection screen, not on the load screen, not while the hub's game or a practice has the TV, not as the TV comes back. A line the host would have said in that time is dropped, not saved up to be said later. The winner's own character speaking at the result stays as it is ("only p3 voice upon winning" was right). First say where tonight's host lines came from (the announcement before the mini game, a line queued earlier that played late, a line at the result) and why only two of four.
2. **No bare board between the decision and the load screen.** Once the mini game is decided, something of yours covers the board until the load screen is up — through the announcement, the wait for the hub's list, the card, and any fade. First say where the second of board came from, and why two of four. **If it comes from the hub side's file** (`minigames/hub_minigame.gd` asks the hub for its list before it calls `choose_minigame`), do not edit that file: say so, and say what method on the presenter the hub side should call first to put a cover up.

## Not to touch

- `minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` — the hub side's.
- The rules: the same seed gives the same game (a line not spoken must not change what is rolled).
- No name or picture of a real game anywhere in git.

## Done when

A headless check in your usual form shows both — no host line asked of the speech between the decision and the result, with a line queued before and one that would fall inside; no frame between the decision and the load screen with neither screen nor cover up — ending PASS; every earlier check PASS; README and HANDBACK as you keep them; committed and pushed.
