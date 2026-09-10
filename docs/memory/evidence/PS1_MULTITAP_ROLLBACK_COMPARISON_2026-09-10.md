---
memory_schema: 1
as_of: 2026-09-10
---

# Multitap rollback comparison: controller dropout persisted

The exact rollback of the first PS1 game-specific multitap patch restored the audited pre-multitap emulator-manager/controller-override state and Crash Bash again showed Players 3 and 4 greyed out, confirming the multitap behavior had been removed.

The real Android assignment probe still did not return to the earlier four-controller result. Host XInput slots 1-4 remained present. Physical P1, P2 and P3 mapped cleanly and independently to slots 1, 2 and 3, but physical P4 produced no host input. The user confirmed the controllers were charged and chose to retry with a different physical controller.

This comparison weakens the hypothesis that the multitap production patch itself caused the controller-connectivity failure. The game-specific multitap implementation may be re-enabled for further testing, while physical-controller stability during the active Android game-stream session remains a separate active investigation.
