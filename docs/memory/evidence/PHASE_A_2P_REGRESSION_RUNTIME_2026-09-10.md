---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Phase A Two-Player Regression Runtime Validation — 2026-09-10

Classification: `PHASE_A_2P_REGRESSION_CONFIRMED`.

A normal Crash Bash (PS1) session ran with all four session XInput slots present. Physical Player 1 A appeared only on slot 1 and physical Player 2 A appeared only on slot 2. Both releases were clean, neither press was ambiguous, the user reported normal independent two-player gameplay, there was no P1/P2 cross-control, and unused P3/P4 caused no interference. RetroArch autoconfigured ports 1 and 2 through XInput with no startup fallback. Normal PrivyHub End/Exit returned the companion inactive and removed all session XInput slots.

This closes the post-four-player 2P regression. The last gameplay-specific boundary before A9 is representative real 4P gameplay.

Raw evidence: `raw/phase_a_2p_regression_probe_2026-09-10.txt`.
