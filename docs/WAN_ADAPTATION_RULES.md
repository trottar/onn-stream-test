# WAN adaptation rules (G5) — written (G5-S1); implemented behind a flag (G5-S2)

**Status: DRAFT (G5-S1, 2026-10-16).** **G5-S2 (2026-10-16): IMPLEMENTED behind
`PRIVYHUB_WAN_ADAPTATION=1` (`companion/wan_adaptation.py`), proved by replay,
NOT ADOPTED; the live smoke is pending on the stream** (record:
`docs/memory/evidence/G5_S2_WAN_ADAPTATION_RULES_2026-10-16.md`). Per rule,
the G5-S2 line says what was built. **G5-S3 (2026-10-17): the session's routing
class reaches the ladder's context (`path_class`) and 720p/4000 is actuatable on a
remote path, behind `PRIVYHUB_REMOTE_LADDER=1` (`companion/remote_ladder.py`),
replay-proved, NOT ADOPTED, unvalidated live** (record:
`docs/memory/evidence/G5_S3_REMOTE_LADDER_2026-10-17.md`). The
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

- **G5-S2:** R1.1 → `hold` for 3 reports after a path event (an SSRC change or ladder transition, a recovery pause / resume, an overlay path change if the context carries one — not wired today); R1.2 → `no_step_up` until 90 reports after it; R1.3 not implemented (no number); R1.4: no suggestion touches identity or endpoints.

## 2. Prevent runaway latency (`latency-limited`)

- **R2.1** A window that is `latency-limited` (queue ≥ 1 on ≥ 3 of 5, or
  output gap > 250 ms on ≥ 2 of 5) is a **decrease** signal, whatever the
  fps. It goes one rung down (`ROUTINE`, target 6000), or straight to 5000
  when FALLBACK's gap clause holds (`TARGET_KBPS`, `adaptive_bitrate_live.py`).
- **R2.2** **No buffer may grow to hide the path** (ROADMAP §G5: "Do not hide
  a bad WAN path with ever-growing buffers"). The audio cushion (12 / 17
  packets, D-BASE-P9) and the frame cap (90,000 B, D-BASE-P6a) stay as
  adopted. G5-S2 adds no queue.

- **G5-S2:** `latency-limited` or `starved` on 2 consecutive 5-report windows → `step_down` one rung, through the ladder's own gates; no queue added.

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

- **G5-S2:** `capacity-limited` → `step_down` one rung to the LAN floor 5000. At 5000 on a remote path, after 60 reports (ROUTINE's down hold-down, the persistence this sets) → `floor_4000`, **recorded only**: the actuator's validated ladder is 5000-7000, so 4000 needs an actuator change and its own validation first.
- **G5-S3:** R3.2's floor is **actuatable behind `PRIVYHUB_REMOTE_LADDER=1`, unvalidated live**: on a remote path (`path_class` from the session's routing evidence) the ladder and the actuator's validated list are `4000 / 5000 / 5500 / 6000 / 7000`; `floor_4000` and the ladder's own one-rung `capacity_mild` step from 5000 can land on 4000, through every gate; nothing below 4000; on the LAN, 4000 is refused as before.
- **G5-S4 (the user's cap, a data saver):** `PRIVYHUB_REMOTE_RUNG_CAP=<kbps>` (a rung of the remote list; anything else ignored and logged once; it needs G5-S3's flag). On a remote path the ladder's target is clamped to it: the stream moves down to the cap through the ladder's gates (after the 60-s session guard), an increase never goes above it, every step below it is the ladder's own (so `floor_4000` under a 5000 cap still lands on 4000); on the LAN nothing. The user's choice, never automatic; unvalidated live (record: `docs/memory/evidence/G5_S4_REMOTE_RUNG_CAP_2026-10-17.md`).

## 4. Use FEC only when loss justifies it (`lossy`)

- **R4.1** `lossy` without `capacity-limited` (loss ≥ 10 / min post-FEC, fps
  held) is the case FEC addresses. **C4-M1's stronger arm (`xor8_2`) did not
  show a post-FEC gain** (lower in 1 of 3 pairs; the median 69 % of B's
  against the ≤ 60 % rule), and pre-FEC loss rose 2-3× under it. So
  **G5-S2 does not switch FEC schemes on the WAN** until a measured WAN
  night shows the gain. Today's `xor8_1` stays.
- **R4.2** The FEC measures (recovered / unrecoverable) are reported
  per window. A class on them is "not classified; G5-S2".

- **G5-S2:** "FEC switch: not implemented; the fixed 8+1 stays" — no suggestion is FEC-related.

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

- **G5-S2:** an increase only after K consecutive `clean` windows (a `lossy` window is not clean, R5.3): K = 18 (the ladder's 90 reports) on the LAN, 36 on a remote path; short of K → `no_step_up`. R5.2's rate limit and oscillation guard are the ladder's own. The ladder sees no client address today, so "remote" needs the context to carry it (G5-S3).
- **G5-S3:** behind `PRIVYHUB_REMOTE_LADDER=1` the context carries `path_class` (`remote` when the stream's setup was overlay-routed, `lan` otherwise), so R5's K = 36 and R3.2 apply on a remote path live; R5's strictness itself is unchanged.

## Not set by any record (G5-S2 measures them)

- RTT and jitter bars (both are carried and reported:
  `latency.control_round_trip_ms`, `receiver.interarrival_jitter_ms`).
- A relayed-path cap.
- MTU / fragmentation handling (no oversize-drop counter exists).
- The persistence before 720p/4000.
- An audio-starvation bar.
