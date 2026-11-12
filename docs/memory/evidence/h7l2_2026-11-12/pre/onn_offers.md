# What the onn will offer (read from the hub's own state and the client's source, 2026-11-12 ~06:27Z)

- **T88's `continue_available`: false** (`GET /plugins/games/details?id=<the hub's id>`); `recovery_available` false; no
  live session → the start box offers **Start Fresh · Load Save · Extras** (`MainActivity.showGameLaunchModeDialog`:
  positive "Start Fresh", negative "Load Save", neutral "Extras"; title "Start <the game>"). No Continue in it.
- **The game's box:** "Launch on Companion" (positive; no live session, no recovery save) and "Options".
- **The PlayStation entry** as the onn lists it (`GET /plugins/games/systems`, the `games_system_ps1` node): **"PlayStation
  (72)"** — beside "PlayStation 2 (115)".
- **T88's place in it:** the 62nd of 72 (`GET /plugins/games/games?system=ps1`, the hub's order, A-Z; the client shows a
  games page in that order, unsorted, in a grid of **3 columns**, `renderCurrentPage`) → **row 21, the middle tile**: from
  the first tile, Down 20 times, then Right once.
- **The join line:** "Hold any button to join", then "P1 joined — hold to add Player 2" (`PlayerPrompt.kt`). **The pads
  are Sony pads** (the recovery log's `pad_slots` rows, class "sony"): B's "hold A" is written "hold ✕ (the cross button)".
- **The paused bar:** the RESUME PLAYING picture · SAVE · LOAD · END (no DISC on a one-disc game; `PausedBar.kt`,
  `MainActivity`): from SAVE, **Left once** reaches RESUME PLAYING, then OK. Where the focus lands on coming back to
  PrivyHub is not set by the bar (the app restores the list's last tile), so the line says "move to SAVE" first.
