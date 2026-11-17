# What the onn will offer for T89 (no flag; read from the hub's own state and the client's code, 2026-11-17 ~00:30Z)

- **T89** = the user's N64 four-player fighting title (named to the user in replies only).
- **The systems answer:** … "Nintendo 64 (13)" … **Its place:** the 11th of 13 in the hub's order (index 10); the
  onn's games grid has **3 columns** (`MainActivity.kt` `sourceGrid.columnCount` = 3 off the guide page; the games page
  keeps the hub's order) → from the first tile **Down 3, Right 1**.
- **The players field as the hub sends it:** `max_players` 4, `player_mode` "multi" (metadata); every N64 launch's
  `launch_ports` row gives **four ports** (`--device=1:1 … 4:1`, `ports_set` `players` 4, no multitap needed). **The
  client's join rule** (`streaming/PlayerPrompt.kt`): the join takes pads up to the host's `ports_set.players` (capped at
  4) — so **four pads can join**: "Hold any button to join", then "P1 joined — hold to add Player 2" … to P4.
- **The start box:** `continue_available` **true** (slot 1 holds a save) → "Launch on Companion", then **Start Fresh**
  (not Continue); no recovery save; no live session.
- **The save slots 1-3:** slot 1 **holds a save**; **slots 2 and 3 empty** → this task asks **two SAVEs**: the start
  → slot 2, the first results screen → slot 3; the second results screen: no slot (none left; recorded). Slot 1 never
  touched.
- **The paused bar:** RESUME PLAYING · SAVE · LOAD · END (one disc, no DISC). **SAVE:** a "Save State" list "Slot 1 - …
  - <date>", "Slot 2 - … - Empty", "Slot 3 - … - Empty" → the slot, OK → saved at once (no confirm for an empty slot);
  then RESUME PLAYING → the onn's join comes back ("Hold any button to join") and each pad holds again, first to fourth.
- **The pads:** four Sony pads connected to the onn now (adb `dumpsys input`, four `sony_controller_battery` entries,
  75-95 %); the latest `pad_slots` class "sony". **The hub's N64 mapping** (`n64_session.py` "face_c", the hub's label
  for this title): **A = ✕, B = □, Z = L2, C-buttons = the right stick (also △ = C-up, ○ = C-right), Start = OPTIONS,
  the control stick = the left stick**; the join button: ✕.
