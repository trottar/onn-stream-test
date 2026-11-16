# What the onn will offer (read from the hub's own state, the client's source and the board's README, 2026-11-16 ~17:37Z)

- **The systems answer** (`GET /plugins/games/systems`, with the bench flag): eight systems in the hub's order — NES
  (0), SNES (44), Genesis (0), PlayStation (72), PlayStation 2 (115), Nintendo 64 (13), GameCube (27), **"PrivyParty
  (1)"** — the board's entry (`games_system_party`) **the last**.
- **Its one game** (`GET /plugins/games/games?system=party`): total 1, the game node named **"PrivyParty"**
  (`game_party_<hex>`, `node_type` game).
- **The start box:** `details` → `continue_available` false, `recovery_available` false, no live session → the game's
  box offers **"Launch on Companion"**; the start box **Start Fresh** first (the line says Start Fresh).
- **The pads:** the recovery log's latest `pad_slots` rows (2026-11-16 15:43Z, H7-V4's sitting): two pads, class
  **"sony"** → the buttons named as on the pads: **✕ (cross), ○ (circle), △ (triangle)**.
- **The board's own buttons** (its README "Controls", `input/controls.gd`): on a pad A = **confirm**, B = **back**, Y =
  **map**, the d-pad / left stick to move; through the virtual pads' standard mapping A is the pad's bottom button → on
  the user's Sony pads **confirm = ✕, back = ○, map = △**. **In the board's lobby, player 1's confirm starts the game →
  ✕ on the first pad** ("Confirm: start." is the lobby's own prompt). Joining is press-and-hold (0.5 s on the board, any
  button); a button pressed before its pad is seated is not sent as an action, so holding ✕ to join does not start the
  game.
- **The join lines** (the onn's own, `PlayerPrompt.kt`): "Hold any button to join", then "P1 joined — hold to add
  Player 2"; the onn's join closes after two pads (the board has no player metadata → 2).
- **The paused bar:** RESUME PLAYING · SAVE · LOAD · END (`PausedBar.kt`); for the board SAVE / LOAD answer "Saving and
  loading are not offered for the board game; nothing was sent." (B108) — not asked of the user.
