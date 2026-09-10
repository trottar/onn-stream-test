---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Phase A One-Player Regression Runtime Validation — 2026-09-10

Classification: `PHASE_A_1P_REGRESSION_CONFIRMED`.

A normal Crash Bash (PS1) session ran with four live session XInput slots. Physical Player 1 A appeared only on slot 1 (`0x1000`), release was confirmed, no simultaneous ambiguity occurred, and the user reported normal gameplay with no cross-controller takeover. RetroArch autoconfigured port 1 with the XInput driver and no startup fallback. Normal PrivyHub End/Exit returned the companion inactive and removed all session XInput slots.

This closes the 1P regression after the four-player transport/A8 extension. The next regression boundary is ordinary 2P gameplay with P1 fixed to slot 1 and P2 fixed to slot 2 while P3/P4 remain non-interfering.

Raw evidence: `raw/phase_a_1p_regression_probe_2026-09-10.txt`.
