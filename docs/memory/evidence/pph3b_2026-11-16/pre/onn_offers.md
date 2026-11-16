# What the onn will offer for the board (with both flags on; read from the hub's own state, 2026-11-16 ~21:52Z)

- **The systems answer:** NES (0), SNES (44), Genesis (0), PlayStation (72), PlayStation 2 (115), Nintendo 64 (13),
  GameCube (27), **"PrivyParty (1)"** — the board's entry the last. **Its one game:** "PrivyParty". **The start box:**
  `continue_available` false, no recovery save, no live session → "Launch on Companion", then **Start Fresh**.
- **The pads:** the recovery log's latest `pad_slots` row names class **"sony"** (as PP-H2) → the buttons as on the
  pads: **confirm = ✕** (the pad's bottom button), back = ○, map = △; **the board's lobby starts with ✕ on the first
  pad** (its prompt "Confirm: start."). The title's own select screen is worked with the pads as any PS1 game.
- **The join lines:** the onn's "Hold any button to join", then "P1 joined — hold to add Player 2"; the board's own
  join (any button held 0.5 s); **after every RESUME the onn's join line comes back** and both pads hold again
  (PP-H2).
- **The paused bar:** RESUME PLAYING · SAVE · LOAD · END (SAVE / LOAD refused for the board; not asked).
- **How the board picks a mini game** (`game/minigame_picker.gd`, the registry): each time the rules call for a mini
  game (each round, and each duel) the picker takes the next one from a **shuffled bag of every mini game that fits
  the number of players**; every one comes round before any repeats; the bag is shuffled from the game's seed, drawn at
  random when a game starts from the lobby. For two players two fit: the board's own **"Button mash"** (1-4 players)
  and **"On the hub"** (`minigames/hub_minigame.gd`, exactly 2) — **so of the first two mini games one is the hub's,
  and again of the next two**. No command-line word or config sets the seed or the order without editing the board's
  files (the only words it reads are the pictures folder and, in the hub mini game, the hub's address) — **it is the
  board's draw**.
- **Unchanged since PP-H3:** the board's picker (`game/minigame_picker.gd`, last changed before PP-H3) and its registry;
  B116 changed only the hub mini game's script and its check (the board draws at 10 fps while the hub's game is on the
  TV). The pads' class read from the latest `pad_slots` row (PP-H3's sitting, 20:22Z): "sony", both pads.
