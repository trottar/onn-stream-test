# WAN adaptation rules (G5) — written, not implemented

**Status: DRAFT (G5-S1, 2026-10-16). Not implemented: G5-S2 implements
them, behind its own flag, after the live smoke of G5-S1's classes.** The
classes are those of `companion/wan_telemetry.py`. Their thresholds are §1
of `docs/memory/evidence/G5_S1_WAN_TELEMETRY_CLASSIFICATION_2026-10-16.md`.
Every number below is quoted from an existing record or the live ladder's
code. Where none exists, the rule says so.

ROADMAP §G5's priority order, as rules:

## 1. Preserve control / session correctness (`path-changed`)

- **R1.1** On a path change (overlay path transition, recovery pause /
  resume, reconnect), the ladder **does not move** for the blackout that
  follows. That is today's `BLACKOUT_REPORTS = 3` after any SSRC change
  (`adaptive_bitrate.py`), applied to every path event.
- **R1.2** No bitrate increase is evaluated across a path change. The
  increase window empties, as it does today after an SSRC change
  (`INCREASE_WINDOW_REPORTS = 90`, C3-L4-L2).
- **R1.3** An overlay path of `relayed` caps the ladder below the reference
  until G5-S2 measures a relayed path. **No number exists:**
  "not classified; G5-S2".
- **R1.4** The session's identity and declared endpoints (G3) are never
  renegotiated by adaptation. Only recovery, or a new setup, changes them.

## 2. Prevent runaway latency (`latency-limited`)

- **R2.1** A window that is `latency-limited` (queue ≥ 1 on ≥ 3 of 5, or
  output gap > 250 ms on ≥ 2 of 5) is a **decrease** signal, whatever the
  fps. It goes one rung down (`ROUTINE`, target 6000), or straight to 5000
  when FALLBACK's gap clause holds (`TARGET_KBPS`, `adaptive_bitrate_live.py`).
- **R2.2** **No buffer may grow to hide the path** (ROADMAP §G5: "Do not hide
  a bad WAN path with ever-growing buffers"). The audio cushion (12 / 17
  packets, D-BASE-P9) and the frame cap (90,000 B, D-BASE-P6a) stay as
  adopted. G5-S2 adds no queue.

## 3. Reduce bitrate when capacity tightens (`capacity-limited`)

- **R3.1** `capacity-limited` (C3-L4-N1 / N2's rules) gives today's live
  actions: FALLBACK to 5000 (`capacity`) or one rung down (`capacity_mild`),
  with today's hold-downs (`HOLDDOWN_REPORTS` in `adaptive_bitrate_live.py`:
  30-60 reports, 60-120 s, by the kind and direction of the last transition).
- **R3.2** Below the live ladder's floor (5000), the off-site rungs are
  C5-M3's screened ones:
  - **720p/4000 is the only one that passed transport** (loss 2.2/min,
    gap 130 ms; "5.0 Mbit/s on the wire");
  - 720p/3000 and 540p/3500 did not.

  So the remote ladder's lowest rung is **720p/4000**, entered only when
  `capacity-limited` persists at 5000 for the hold-down. The persistence
  count is **not set: G5-S2**.

## 4. Use FEC only when loss justifies it (`lossy`)

- **R4.1** `lossy` without `capacity-limited` (loss ≥ 10 / min post-FEC, fps
  held) is the case FEC addresses. **C4-M1's stronger arm (`xor8_2`) did not
  show a post-FEC gain** (lower in 1 of 3 pairs; the median 69 % of B's
  against the ≤ 60 % rule), and pre-FEC loss rose 2-3× under it. So
  **G5-S2 does not switch FEC schemes on the WAN** until a measured WAN
  night shows the gain. Today's `xor8_1` stays.
- **R4.2** The FEC measures (recovered / unrecoverable) are reported
  per window. A class on them is "not classified; G5-S2".

## 5. Recover upward slowly, with hysteresis (`clean`)

- **R5.1** An increase needs today's increase rule: 85 of the last 90
  reports clean (fps ≥ 57, queue ≤ 1, gap ≤ 150), after the blackout, at
  least 60 s into the session, one rung per event (`INCREASE_*`, C3-L4-L2).
- **R5.2** At most 4 transitions in 10 minutes (`RATE_LIMIT_*`, the live
  ladder). G5-S1 proposal: carry over the shadow controller's oscillation
  rule (three direction changes in 10 minutes → HOLD; `OSCILLATION_*` in
  `adaptive_bitrate.py`).
- **R5.3** On the WAN, a `lossy` window counts as **not clean** for the
  increase window even when fps / queue / gap pass. This is a G5-S1
  proposal; G5-S2 tests it.

## Not set by any record (G5-S2 measures them)

- RTT and jitter bars (both are carried and reported:
  `latency.control_round_trip_ms`, `receiver.interarrival_jitter_ms`).
- A relayed-path cap.
- MTU / fragmentation handling (no oversize-drop counter exists).
- The persistence before 720p/4000.
- An audio-starvation bar.
