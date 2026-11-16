# What the onn will offer (read from the hub's own state and the client's source, 2026-11-16 ~03:28Z)

- **T88's `continue_available`: false** (`GET /plugins/games/details?id=<the hub's id>`); `recovery_available` false; no
  live session → the start box offers **Start Fresh · Load Save · Extras** (positive "Start Fresh"). The line says
  **Start Fresh** (it would either way).
- **The game's box:** "Launch on Companion" (no live session, no recovery save).
- **The PlayStation entry** (`GET /plugins/games/systems`, the `games_system_ps1` node): **"PlayStation (72)"**.
- **T88's place in it:** the 62nd of 72 (`GET /plugins/games/games?system=ps1`, total 72, offset 0, the hub's order; the
  client's grid of 3 columns) → **row 21, the middle tile**: from the first tile **Down 20 times, then Right once** —
  the same as H7-L1 / H7-L2, where the user reached it with these presses.
- **The join lines:** "Hold any button to join", then "P1 joined — hold to add Player 2" (`PlayerPrompt.kt`). **The pads
  are Sony pads** (the recovery log's latest `pad_slots` rows, 2026-11-14: two pads, class "sony") → "hold ✕ (the cross
  button)".
- **The paused bar** (`now_playing_bar`, above the games grid): the RESUME PLAYING picture · SAVE · LOAD · END (no DISC on
  a one-disc game; `PausedBar.kt`). The bar does not set where the focus lands on Home (the app keeps the grid's last
  tile — the game's, row 21): **press Up until the bar at the top is highlighted (about 21 presses; holding Up works),
  then Right until END (the last button) is highlighted**, then OK.
