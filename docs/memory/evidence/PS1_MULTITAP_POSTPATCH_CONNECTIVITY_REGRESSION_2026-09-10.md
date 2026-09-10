---
memory_schema: 1
as_of: 2026-09-10
---

# PS1 multitap post-patch controller-connectivity regression

Runtime after `privyhub_phase_a_ps1_multitap_game_override_01_2026-09-10` changed one important game-layer result: Crash Bash exposed four human players instead of greying out Players 3 and 4.

The same run did not preserve the previously validated physical-controller path. Host XInput slots 1-4 and RetroArch ports 1-4 remained present, but only physical Player 1 produced XInput activity; Players 2-4 produced none. The user also observed that with PrivyHub/game streaming active only 2-3 physical controllers would stay connected, while with the server/session off all four remained connected. The controllers were plugged in and charged.

This is a regression correlation, not yet proof of mechanism. The multitap patch is therefore development-only and causally suspect. The next action is an exact rollback to the pre-multitap production bytes followed by the previously validated four-controller Android assignment test under a normal active game session.

Do not reopen PHI1, ViGEm, A8 mappings, or RetroArch enumeration unless the rollback test produces new evidence requiring it.
