# G5-S2 — the design, written before any G5-S2 code

Flag: `PRIVYHUB_WAN_ADAPTATION=1` (any other value or absent = off). Off: the
ladder module never imports `wan_adaptation`, and `LiveController.observe`
calls `self._policy.feed(s, ctx)` exactly as today.

## Where the rules sit

- **`companion/wan_adaptation.py`** (new). `WanRules` is pure (no clock, no
  I/O). It keeps its own rolling report history, built from the same client
  telemetry the ladder sees (`wan_telemetry.report_from_telemetry`, G5-S1's
  pure functions, imported; G5-S1's own flag and its live object are not
  involved). It classifies with G5-S1's `classify_window`. Per decision tick
  (one evaluated client report) it returns **at most one suggestion**:
  `none`, `hold`, `no_step_up`, `step_down` or `floor_4000`, with the rule id
  and the class.
- **The hook** in `adaptive_bitrate_live.py` is one guarded build and one
  `if`. The build is a module global `WAN_ADAPTATION`, created only when the
  flag is `1`, with the import inside the `if`. The `if` is in
  `LiveController.observe`: with the global set, the report goes through
  `WAN_ADAPTATION.feed(policy, s, ctx, telemetry)`; otherwise through
  `policy.feed(s, ctx)` as today. The ladder (`LivePolicy`) is not edited.
- **The ladder stays the decider.** A suggestion applies only as an
  additional constraint, in one of two ways:
  - `no_step_up` / `hold` block an increase the ladder would take this tick.
    During this one `feed`, the policy's `_decide` is wrapped on the
    instance (removed straight after). An `INCREASE` is refused with the
    reason `wan_no_step_up`; every other kind runs unchanged.
  - `step_down` forces a one-rung decrease the ladder did not take this
    tick. It applies only when the report was evaluated and the ladder made
    no decision of its own. It goes through the ladder's own `_decide` with
    its one-rung trigger (`capacity_mild`'s target rule), and so through
    **every existing gate**: hold-downs, the blackout, the guards, the rate
    limit and the oscillation guard. The resulting rows and the policy's
    reason are then relabelled `wan_rules`.
  - Nothing else: a suggestion never restarts the session, never touches the
    controller path or recovery, and never moves a level directly.
- **Remote vs LAN.** A path is remote when the stream's target address (the
  native status's client address field, if present) is in the overlay block
  (the shared /10 and Tailscale's ULA, built from integers). Otherwise it is
  LAN. Unknown → LAN (the ladder's own floor).

## The rules (R1-R5 of `docs/WAN_ADAPTATION_RULES.md`)

**R1 — control first (`path-changed`).** Path events are:

- an SSRC change or a ladder transition, seen as the policy's blackout
  re-arming;
- a recovery pause or resume (the `recovery_playing` guard changing);
- an overlay path change, if the context carries `overlay_path`. Today it
  does not: the overlay provider is not wired into the ladder (G5-S3).

R1.1: for `BLACKOUT_REPORTS` (3) reports after an event → `hold`. R1.2:
then, until the increase window has refilled (`INCREASE_WINDOW_REPORTS` = 90
reports after the event) → `no_step_up`. R1.3: a relayed-path cap is not
implemented (no number exists). R1.4: no rule touches the session's identity
or endpoints.

**R2 — no runaway latency.** The last two consecutive, non-overlapping
5-report windows both classify `latency-limited` or `starved` (G5-S1's
thresholds, which include D-BASE's stale-drop rate) → `step_down`, one rung.

**R3 — capacity.** The current 5-report window is `capacity-limited` →
`step_down` to the next rung down.

- At the LAN floor (5000) → `none`: the ladder's own floor.
- At 5000 on a remote path, after `capacity-limited` has persisted for
  ROUTINE's down hold-down (60 reports), → `floor_4000`. The persistence
  count was not set by any record; this design sets it to the hold-down.
- **`floor_4000` is recorded, not actuated.** The live actuator's validated
  ladder is 5000-7000 (`LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS`), and a 4000
  level needs an actuator change plus its own validation. That is outside
  G5-S2; it is listed for the user. No rule ever suggests below 4000.

**R4 — FEC.** No change, per C4-M1. Recorded as "FEC switch: not
implemented; the fixed 8+1 stays". No suggestion is ever FEC-related.

**R5 — slow recovery.** An increase is allowed only after **K consecutive
clean windows**: G5-S1's class `clean`, so a `lossy` window is not clean
(R5.3). K = the ladder's increase window in windows (90 / 5 = 18), doubled
on a remote path (36). Short of K → `no_step_up`. One rung at a time is
already the ladder's rule. The rate limit and the oscillation guard
(R5.2) are already in the ladder.

**Precedence, one suggestion per tick:** `step_down` (R2, then R3) /
`floor_4000`, then `hold` (R1.1), then `no_step_up` (R1.2, then R5), then
`none`.

## Recording

Every non-`none` suggestion becomes one `decisions.jsonl` row:
`event: wan_suggestion`, `source: wan_rules`, the suggestion, the rule id,
the window class (primary and all met), `path` (remote / lan), and
`ladder_result`. The result is the ladder's outcome on that tick:
`transition`, `refused:<reason>`, `blocked_increase`, or `none`. A `none`
suggestion writes nothing.

## The proof

- **In-process handler comparison, flag absent.** HEAD's
  `adaptive_bitrate_live.py` (from git) and the edited one are each driven
  through `LiveController.observe` with the same recorded inputs: a
  synchronous actuator and a temporary log. Every row they write must be
  identical, apart from `at_utc` and the actuation duration.
- **Replay of the recorded decisions** (`g5_s2_2026-10-16/replay.py`). Each
  named run's whole session is taken from the live log (the run's
  `decisions.jsonl` starts mid-session). It is fed through the ladder via
  the same entry the hook uses. **Flag absent:** every recorded sample row's
  decision fields and every recorded decision event must be reproduced
  exactly. **Flag present** (LAN as recorded, and the same inputs read as
  remote), tabulated per run:
  - ticks with a suggestion, by rule;
  - ticks where the ladder's decision changed;
  - whether R5 ever allowed the rung back;
  - whether the remote floor would have engaged.

  No claim that the result is better.
- The runs:
  - `e4_s4b_2026-10-10` E1-PS1-STREAM run3 (the lossy one);
  - `e4_s4b_2026-10-10` E1-PS1-STREAM run2 (the cleanest);
  - `cl_b3_2026-10-16` E1-PS1-STREAM run1 (today's best link);
  - `e4_s4_2026-10-10` E1-CONC_flag run1 (grab bursts, two transitions).
- Unit tests per rule with hand fixtures; the G1 / G3 / G5-S1 suites; the
  redactor.
