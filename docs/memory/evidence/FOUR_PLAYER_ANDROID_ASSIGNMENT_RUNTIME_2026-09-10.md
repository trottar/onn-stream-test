---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Four-Player Android Assignment Runtime Evidence — 2026-09-10

Classification: `ANDROID_FOUR_CONTROLLER_ASSIGNMENT_CONFIRMED`.

During a normal PrivyHub game session, four real controllers connected to the onn were measured at the host XInput boundary. All four XInput slots were present throughout capture. Physical controller 1 reached slot 1, controller 2 reached slot 2, controller 3 reached slot 3, and controller 4 reached slot 4. Each capture was an isolated physical A press (`0x1000`), each release was confirmed, no simultaneous-A ambiguity was observed, and all four slots remained present through the sequence. The final state was neutral.

This validates the real Android `InputDevice -> NativeControllerSender -> PHI1 -> NativeControllerBridge -> XInput slot` assignment boundary for four distinct controllers. It does not yet prove that RetroArch enumerates/binds all four devices as ports 1-4, that P3/P4 A8 profiles are generated, or that a four-player core/game accepts all four ports.

Raw measurements are preserved in `evidence/raw/four_player_android_assignment_probe_2026-09-10.txt`.
