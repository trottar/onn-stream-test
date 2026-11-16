# What the onn will offer (read from the hub's own state and the client's source, 2026-11-16 ~15:38Z)

- **T88's `continue_available`: false** (`GET /plugins/games/details?id=<the hub's id>`); `recovery_available` false;
  `live_session` none → the start box offers **Start Fresh** first. The line says **Start Fresh** (it would either way).
- **The game's box:** "Launch on Companion" (no live session, no recovery save).
- **The PlayStation entry** (`GET /plugins/games/systems`, the `games_system_ps1` node): **"PlayStation (72)"**.
- **T88's place in it:** the 62nd of 72 (`GET /plugins/games/games?system=ps1`, total 72, offset 0, the hub's order; the
  client's grid of 3 columns) → row 21, the middle tile: from the first tile **Down 20 times, then Right once** — as
  H7-V2 / H7-L1 / H7-L2, where the user reached it with these presses.
- **The join lines:** "Hold any button to join", then "P1 joined — hold to add Player 2" (`PlayerPrompt.kt`). **The pads
  are Sony pads** (the recovery log's latest `pad_slots` rows, 2026-11-16 03:37Z, H7-V2's sitting: two pads, class
  "sony") → "hold ✕".
- **The paused bar:** RESUME PLAYING · SAVE · LOAD · END (no DISC on a one-disc game; `PausedBar.kt`); B's stop / END
  line used as written ("Press Home on the first pad (the bar RESUME PLAYING · SAVE · LOAD · END appears), move to END
  and press OK").
