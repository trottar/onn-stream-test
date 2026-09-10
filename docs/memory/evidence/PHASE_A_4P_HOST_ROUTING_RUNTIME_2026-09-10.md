---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Phase A Four-Player Host Routing Runtime Evidence

The representative Crash Bash four-player probe returned `PHASE_A_4P_HOST_ROUTING_CONFIRMED_GAMEPLAY_NOT_CONFIRMED`.

Runtime measurements proved the entire PrivyHub controller path for four real players during a normal game session: physical P1-P4 reached XInput slots 1-4 independently, all releases were clean, RetroArch autoconfigured Xbox controllers on ports 1-4, no XInput fallback occurred, no cross-control occurred, and normal End/Exit removed all four session slots.

Crash Bash Battle Mode still exposed only two human players; Players 3 and 4 were greyed out. The probe found no explicit Beetle PSX HW multitap setting under `data/games/retroarch`.

This is not evidence for reopening PHI1, Android assignment, ViGEm, RetroArch enumeration, or A8. The active hypothesis is now the PS1 core/game topology layer: Beetle PSX HW multitap is not being enabled for the four-player session.

Production behavior changed by this diagnostic: **none**.
