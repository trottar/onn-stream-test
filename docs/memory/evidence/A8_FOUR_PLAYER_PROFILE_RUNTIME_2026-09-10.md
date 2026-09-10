---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# A8 Four-Player Profile / Editor Runtime Validation — 2026-09-10

Classification: `A8_FOUR_PLAYER_PROFILE_EDITOR_CONFIRMED`.

The live companion remained on input-profile schema 1 and exposed `player1` through `player4`. All four inspected profiles exposed P1-P4 keys, and a legacy P1/P2 mapping normalized to four players without modifying user profile storage. The installed backend generated analog-D-pad settings for ports 1-4 plus explicit Player 3 and Player 4 RetroArch binds; the generated profile carried 192 override lines.

On the onn, the user confirmed the Android profile UI exposed Player 1-4 edit actions and the copy-from-another-player control, and successfully synchronized custom input mappings across all four players.

This closes the P3/P4 A8 profile/editor/session-remap extension as runtime validated. The remaining four-player acceptance work is gameplay regression: 1P, then 2P, then a representative 4P game/core path before A9.

Raw evidence: `raw/a8_four_player_profiles_probe_2026-09-10.txt`.
