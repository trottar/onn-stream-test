---
memory_schema: 1
as_of: 2026-11-17
status: NOTE for the PC side (PrivyParty, the board game) — the screens before a mini game on the hub: the selection, then the load screen with its ready check and Practice. Sent through the board's repo (this file at its root; the same bytes are in the hub repo's docs/memory/handoffs/). The hub side (session B, queue AU of 2026-11-17) is building its half at the same time. Nothing here touches the rules
---

# PC side — choose, load, ready up: the screens before a mini game on the hub

**The user's asks (2026-11-17, verbatim):** "why don't we just cover things with a load screen while things are situated to avoid possible issues? It could be just a quick breakdown of the scores, items, coins, with character profiles situated near them for immersive feel" — then: "Eventually we will have multiple mini games and such. Perhaps this is a good time to first do the mini game selection screen similar to mario party. We select between two games or random. Then the loading screen shows up as the selected (or random) game is loaded and readied. This should be the same procedure for duels. The load screen then also includes the name of the mini game with a prompt to press button to join game. We could even add an option to practice if thts not too complicated (wouldn't even need the vision model for practice)" — then: "The practice should be there after the selection screen, on the load screen. Practice can be as many times as people want. Pressing enter in the practice (only in practice) leaves the practice and back to load screen with join to start or practice. The controllers are already setup per person in PrivyParty so this is a ready check that lasts until everyone readies up".

**The user's choices since:** one player picks — the last-placed of the players about to play, and in a duel the player who started it; when only one game fits, the selection screen still shows it (no Random); Practice is on the load screen, as often as the players like, and comes back to the load screen (the hub ends it — the pad's Start button, or about 90 seconds); the ready check has no time limit.

**`aa58ec6c…`** (the picker's `first_here()`) is on the hub and reads right; the hub sets `PRIVYPARTY_ON_HUB=1` when it launches the board.

**Why:** on the hub a mini game is an emulator game. The hub needs 3-15 seconds to launch it, load its starting point and make sure the right screen is up. Until now the players watched that and could press buttons too early. From now on the TV stays on the board for those seconds — the hub gets the game ready behind it — and changes to the game only when the hub is ready **and** the players are (every one ready, or a practice asked for).

## The procedure — the same for a round's end and a duel

1. **The selection screen** — one or two games by name, and Random when there are two. One player picks.
2. **The load screen** — the chosen game's name, everyone's standing with their character, a **ready check** for each player in the mini game, and **Practice**. The hub is getting the game ready meanwhile. It stays until every player in the mini game is ready — however long that takes — or one of them asks for practice.
3. The TV changes to the game; afterwards the board is back with the scores, as today.
4. **Practice** — the TV changes to the game with nothing scored; when the hub ends it, **the load screen is back**, the ready marks clear, and the players ready up to start or practise again. As often as they like.

## The seam — five methods on the presenter (the `stage` a mini game is given)

The hub's mini game (`minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd` — **the hub side's files, being changed on the hub right now; please do not edit them**) calls each **only if the presenter has it**, so either side can land first.

- **`choose_minigame(cards: Array, players: Array) -> Dictionary`** — awaited. `cards` is one or two `{"title": String}` (the games' names, sent by the hub when the game runs). `players` are the ones about to play (two for a duel, four for a round's end). It returns `{"card": 0 | 1 | -1}` — `-1` is Random (only offered with two cards; the hub's mini game then makes the seeded pick). **Who holds the cursor is yours:** the last-placed of `players` by the board's own standing (say how a tie is settled — seeded); in a duel, the player who started it. Only that player's pad moves and confirms.
- **`show_minigame_loading(title: String, players: Array) -> void`** — puts the load screen up at once, every ready mark clear, and returns. It is called again, the same way, each time a practice comes back.
- **`set_minigame_loading_ready(ready: bool) -> void`** — what the hub says: false while it is getting the game ready, true once it is. The screen says so in its own words; the players may ready up or ask for practice either way — the game simply changes over once both are so.
- **`minigame_loading_choice() -> String`** — read a few times a second: `""` while the players have not decided, **`"start"`** once every player in `players` is ready, **`"practice"`** once a player in `players` has asked for practice. It keeps its answer until the next `show` or `hide`.
- **`hide_minigame_loading() -> void`** — when the hub's game is on the TV, and on every way out (a draw, a refusal). Called with nothing shown, it does nothing.

**The ready check is with the pads the board already knows as each player's** — nobody joins anew. How a player readies up (a press, a hold), whether they can take it back, and which button asks for practice are yours; a practice asked for by any one player in the mini game is a practice for all of them (the user: "as many times as people want").

The names are the seam. If you would rather have others, or would rather the picker own the choice (so the board's own mini games can sit on the same cards later), say so in your hand-back and the hub side follows — but build these first, so the two halves meet.

## What the screens show

- **The selection screen:** a card for each game with its name; a Random card when there are two; who is picking, plainly. Nothing else can be done on it.
- **The load screen:** the game's name, large; **every player in the board game**, in their order, each with **their character's profile** and beside it **their standing — their score, their coins and the items they hold**, by the board's own names; the players about to play picked out, each with a ready mark that fills when they ready up; how to ready up and how to ask for practice, shown with the board's own button pictures; a line in the board's own voice for what the hub is doing ("Getting the game ready…" / "Ready when you are"); and, so nobody is surprised, how a practice is left (**the Start button, or about 90 seconds**). It reads from the game's own record and decides nothing (as `stats_view.gd` does).
- A card takes a name only, for now; a picture may come from the hub later, the same way.

## What they must hold to

- **The load screen stays up for as long as it is asked** — from `show` to `hide`: a few seconds when everyone is quick, with no upper limit (a ready check lasts until everyone is ready). No timer of its own takes it down or starts the game.
- **Input:** on the selection screen only the picking player's pad; on the load screen only the ready and practice presses of the players in the mini game. Nothing beneath either screen reacts to the pads while it is up. (The hub's mini game no longer swallows the pads until the TV is on the hub's game.)
- **They keep moving a little** — a still picture on the hub reads as a fault.
- **Seen through the hub's stream** at 1920 × 1080: large type, nothing important in the outer few percent.
- **On the PC nothing else changes:** a mini game that never calls the seam plays as today; the rules are not touched.
- **No name or picture of a real game in git:** the names arrive when the game runs; the checks use made-up ones.

## The check

A headless check in your usual form, with made-up names: one card and two cards; the right player holds the cursor (last place; a tie; a duel's starter) and no other pad moves it; card 0, card 1 and Random each come back as chosen; the load screen shows the name, every player's profile and standing, the ones about to play picked out; `minigame_loading_choice()` is `""` until each of them is ready and `"start"` after, and other players' pads do not count; a practice press by one of them gives `"practice"`; shown again, the marks are clear and the answer is `""`; `set_minigame_loading_ready` changes the line and nothing else; it is still up, undecided, after ten minutes of frames; `hide` takes it down and the board is as it was; `hide` with nothing shown does nothing; the same seed gives the same game before and after (the rules were not touched). README and HANDBACK as you keep them.

**When it is pushed,** the user tells the hub side; the hub pulls, and the hub's own bench check and then the four-person sitting follow.
