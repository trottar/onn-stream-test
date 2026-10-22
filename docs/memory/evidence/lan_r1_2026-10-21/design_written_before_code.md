# LAN-R1 design — written before any code edit, hashed (session B, 2026-10-21)

## What §1 found (the reasons for this design)

- **Why 7000 throughout:** every decrease bar of the adopted `live` ladder carries an fps term. The bars are
  capacity_mild (fps < 57 on ≥ 4 of 5 AND lost ≥ 50 on ≥ 3), capacity (fps < 50 on all 5 AND lost ≥ 50 on ≥ 3),
  and the queue/gap FALLBACK / ROUTINE.
  - On Sunday the loss came in few, large reports, with fps mostly ≥ 57. The two terms never met in one 5-report
    window, except at 05:11, where the ladder did step 7000 → 6000.
  - **Loss alone never steps down.** The FEC-unrecoverable groups are in the ladder's telemetry
    (`fec.unrecoverable_groups_delta`, host-computed by `client_feedback.py` from each client-health report). The
    ladder does not read them.
- **G5-S2's rules are not gated on the path:** R2 / R3 run on the LAN; only R3.2 (the 4000 floor) and R5's K depend
  on `path_class`. On the evenings they add only R3.1 at 05:11, on the same tick as the ladder's own `capacity_mild`.
  `lossy` only blocks increases (R5), and at 7000 there is none to block.
- **The threshold search** (`threshold_search.md`) uses per 10-s window (5 evaluated reports), K consecutive windows,
  session age ≥ 60 s.
  - **Post-FEC loss:** no (T, K) with 0 false triggers fires on Sunday between 04:51 and 05:06. Its only pre-05:06
    zero pair (T 10, K 5) fires at 04:45, in King's Field, and not again until 05:06.
  - **FEC-unrecoverable groups:** two zero-false-trigger pairs fire before 05:06: T 3 K 3 (05:01:38) and T 4 K 2
    (05:03:05). **Both are edge cells:** T 3 K 2 has 6 false triggers, T 4 K 1 has 19, T 2 K 3 has 13. The separation
    is real on this data but thin, and the pair was chosen on the data it is scored on (in sample).

## The rule

**`PRIVYHUB_LAN_LOSS_RULE=1`** (`1` only, the module convention of `PRIVYHUB_WAN_ADAPTATION`). Absent, empty or
anything else = today: `adaptive_bitrate_live.py` does not import the module, and `observe()` runs exactly as before.

**In words.** The rule applies on any path class.
- On each report the ladder evaluated (disposition `evaluated`), take the client's FEC-unrecoverable groups since
  its previous report (`telemetry.fec.unrecoverable_groups_delta`; missing = 0).
- When **each of the newest K = 2 non-overlapping 5-report windows** (20 s) holds **≥ T = 4** of them, ask the
  ladder for **one rung down** through its own `_decide("ROUTINE", …)`, with the one-rung target of `capacity_mild`.
  Every gate holds: the hold-downs, the blackout, the 60-s session age, the guards (recovery PLAYING, game not
  paused), the rate limit and the oscillation guard.
- The decision is labelled `reason` / `trigger` **`lan_loss`**.
- **Floor 5000:** at or below 5000 the rule asks nothing (whatever the ladder's list).
- **Re-climb:** the existing increase rule, unchanged (90 reports, ≥ 85 clean; loss does not make a report unclean).
  If the loss persists, the oscillation guard is what stops a down / up / down cycle.

**When it asks.** Only on a tick where:
- the ladder itself made no decision (no `transition` / `would_act` / `refused` / `hold` event);
- the report was evaluated;
- nothing is pending;
- the ladder is not deferring a ROUTINE for an escalation.

That is the same condition as G5-S4's `REMOTE_CAP.after_feed`.

**Its windows** hold evaluated reports only:
- they are cleared at a client-session reset (elapsed goes back);
- they are cleared when the ladder's blackout re-arms (an SSRC change or a transition);
- they are cleared after the rule asked, whatever the answer, so the next ask needs 2 fresh windows.

**Recorded:** a `lan_loss_rule` event on each ask, with the two window sums, T, K, the level and `ladder_result`
(transition / refused:<reason> / hold). Rows exist only with the flag on.

## The code

1. New **`companion/lan_loss_rule.py`** (pure; no clock, no I/O):
   - `FLAG_ENV`, `flag_on`, `T_UNREC = 4`, `K_WINDOWS = 2`, `WINDOW_REPORTS = 5`, `FLOOR_KBPS = 5000`,
     `SOURCE = "lan_loss"`;
   - `LanLossRule.after_feed(policy, s, ctx, telemetry, events)`, for the hook;
   - `LanLossRule.feed(policy, s, ctx, telemetry)`, the harness entry: `policy.feed`, then `after_feed`;
   - `from_environ(environ)`.
2. **`companion/adaptive_bitrate_live.py`:**
   - one guarded module-level import, as G5-S2's: `LAN_LOSS_RULE = None`, built only when the flag is `1`;
   - one `if` in `LiveController.observe`, after the feed and G5-S4's `after_feed`:
     `if LAN_LOSS_RULE is not None: events = LAN_LOSS_RULE.after_feed(self._policy, s, ctx, telemetry, events)`.
   - Nothing else. The actuator path is unchanged: a transition is the policy's `pending`, carried out by the
     existing `_maybe_actuate`.
3. New **`tests/lan_loss_rule/test_lan_loss_rule.py`:**
   - the flag (`1` only);
   - the ladder's import guarded (AST);
   - absent = no module and the plain feed;
   - the windows: exactly T on both fires, T−1 on either does not, one window does not;
   - only evaluated reports count;
   - a session reset and a blackout re-arm clear;
   - one rung: 7000→6000→5500→5000, at 5000 nothing;
   - missing fec counts 0;
   - the guards: session age < 60 s refused, hold-down refused, not PLAYING refused, a decision already taken this
     tick means no ask;
   - the relabel;
   - the actuator rides `pending`.

**Proof (after the code):**
- §1.1's replay repeated: recorded decisions exact, HEAD's controller against the edited one row for row, with the
  flag absent;
- the replay with the rule on, both evenings: the step-down minutes and the rung path (open loop), with the
  heartbeat's unrecoverable groups injected per report (the evenings' run telemetry does not exist; the client-health
  and heartbeat reports are two sends of the same counters, offset ≤ 2 s; disclosed);
- the false-trigger table over the clean windows (the search's, at the chosen pair);
- the G8-S1 cells under the chosen pair;
- the suites green (in the `/tmp/b_` copy of `companion/`, `tools/`, `tests/`).

**Disclosed before the code:**
- **In-sample, thin margin:** see above. The live test (session A) is the out-of-sample check.
- **Random loss:** under G8-S1's shim loss-1 (1 % random loss, unrecoverable groups ~17 / min) the rule fires within
  ~3 min. A lower rate does not reduce random loss, so on such a link the rule costs bitrate for nothing. The
  oscillation guard bounds the cycling. Whether Sunday's loss was congestion-like or random is not known (UX-R1: the
  link or the onn, not split).
- **Not before the 04:56 step:** the rule's first Sunday ask is 05:03:05, ~3 min before the 05:06 burst.
- **What the client already sends that the ladder does not read:**
  - the FEC-unrecoverable groups (used here);
  - the FEC-recovered packets (read into the sample, unused);
  - the heartbeat's audio underruns / concealment / arrival gaps;
  - the decode queue (the session report, end of session only).
  - The per-report output gap is read already (FALLBACK's > 250 ms term, behind fps < 50 on all 5).
  - A per-second client signal (output gap, audio arrival gap) is noted, not built.
