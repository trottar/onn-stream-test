---
memory_schema: 1
as_of: 2026-09-10
---

# Final four-player runtime closure

Representative four-player gameplay is COMPLETE/runtime validated.

With a replacement physical controller, the real Android assignment probe again produced exact first-touch mapping P1->slot1, P2->slot2, P3->slot3, P4->slot4 with clean releases, four-slot continuity, and a neutral final state while the game session was active.

With game-specific Beetle PSX HW Port-1 multitap re-enabled, Crash Bash Battle Mode exposed four human players. The final representative gameplay probe confirmed four live XInput slots, exact P1-P4 host routing, RetroArch Xbox autoconfiguration on ports 1-4 with no xinput fallback, independent four-player gameplay with no cross-control, and clean End/Exit teardown.

The earlier dropout did not reproduce with the replacement controller and persisted once during the exact no-multitap rollback, so it is not classified as a proven PrivyHub multitap/software regression. Preserve it as a controller-specific/pairing/transient Bluetooth observation; reopen only if representative controllers reproduce it.

A9 full emulator regression/checkpoint is now the active Phase A gate.
