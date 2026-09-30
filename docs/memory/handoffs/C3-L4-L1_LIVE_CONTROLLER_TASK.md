---
memory_schema: 1
as_of: 2026-09-28
status: TASK HANDOFF — C3-L4-L1: build the live adaptive-bitrate mode as decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md authorizes it — one transition per event, ramps excluded, the level-preserving recovery restart of C3-F1 — behind PRIVYHUB_ADAPTIVE_BITRATE_MODE=live (off by default, shadow unchanged), proven by replay tests, a silent live hold on a clean link and an injected-trigger session; the fault-injection night with the user's nft is NOT this task; nothing adopted; nothing committed; authorized by the user 2026-09-28 ("Go")
---

# C3-L4-L1 — the live controller, built and proven as far as a clean link allows

**Why.** `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`: C3.L4 is
authorized, single transition per event, live build pending. The shadow
controller (`companion/adaptive_bitrate.py`, `C3_L4_S1`) decided over
3,598 reports and stayed SILENT on a clean link; its decisions were never
wired to the actuator. `C3-F1` made recovery's restart level-preserving,
so a stream that has stepped down no longer breaks recovery. This task
wires the decision to the actuator under the decision's constraints and
proves everything that can be proven without real loss. The night with
real loss needs the user's `nft` and comes after.

Read first: the decision record (what it authorizes and what it does
not); `architecture/ADAPTIVE_BITRATE.md` (states, trigger classes,
blackout 3 reports, hold-downs 30 / 60 reports, increase after 90 clean
reports, the oscillation guard, the actuator contract, the live-mode
section added by `R4`); `companion/adaptive_bitrate.py` and
`tools/test_adaptive_bitrate_shadow.py`; `C3_L4_S1_SHADOW_CONTROLLER_2026-09-24.md`;
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` (`video_only_restart`,
what it is authorized for); `C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`
(the level-preserving primitive; the recovery state machine's contract);
`C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md` (cost ~190 ms, settling 1-4 s,
lifecycle clean at 24 per session); `C4_D1_FEC_EVIDENCE_2026-09-24.md`
and `CTRL_L1_CONTROLLER_LOSS_LOCATION_2026-09-24.md` (recorded loss series
to replay); `evidence/D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md` (how
recovery and a controller must not fight); `TOOLS.md`.

**Scope.** Companion only; no profile, encoder flag, cap, cushion,
redundancy or FEC change; no client change (the adopted APK stays;
`CL-B1`'s adoption is a separate step). `PRIVYHUB_ADAPTIVE_BITRATE_MODE`
gains `live`; `off` stays the default and `shadow` behaves exactly as
before (the shadow test suite must still pass unchanged). Live mode
never runs in this task except in the two sessions below, and the flag
is unset and confirmed absent at the end.

## The constraints live mode must enforce (write them as code and as tests)

1. **One transition per event.** A FALLBACK or ROUTINE trigger produces
   at most one `video_only_restart`, to the target the policy names from
   the ladder (5000, 5500, 6000, 7000) — never a sequence of rungs. An
   increase is one rung per event. No two transitions closer than the
   hold-down that applies (30 reports FALLBACK-hold, 60 ROUTINE, 90 clean
   before an increase; state the seconds at the 2 s cadence).
2. **Blackout after any SSRC change**, its own or recovery's: 3 reports,
   during which no decision is taken and no telemetry is scored (`S1`:
   settling 1-4 s; the blackout must cover the p95).
3. **Never acts unless** the stream is PLAYING with a game active, the
   reference profile is in force, `any_override` is false, and the
   session is at least 60 s old. It never acts while the recovery state
   machine is anywhere but its idle state, and recovery's restart
   (`C3-F1`) keeps the current level — say where the two are serialized.
4. **Rate limit**: at most 4 transitions in any 10-minute window; beyond
   it the controller holds at the current level and logs `RATE_LIMITED`.
5. **Return to reference**: every session ends at 7000 — on `session_ended`
   the controller resets; a session that starts finds 7000 (a full start
   resets, C1).
6. **Kill switch**: the flag; unset + unit restart = off. Also a runtime
   route `POST /plugins/games/adaptive-bitrate/disable` that switches to
   shadow for the rest of the session, idempotent, for the user's `nft`
   night. No enable route.
7. **Every decision logged** in the controller's existing log with the
   inputs it was made from, the class, the target, the hold-downs in
   force; `native-stream-status` shows `adaptive_bitrate.mode`,
   `state`, `level`, `last_action`, `transitions_this_session`,
   `rate_limited`.

## Steps

1. **Design note** (`c3_l4_l1_design.txt`): the policy as the shadow has
   it (does it name a target or a step? if it steps rungs, the live
   policy names the target as the lowest rung the trigger's severity
   maps to — write the mapping and keep it in one table); how the
   actuator is invoked (the same code path as the loopback transition
   route / `C3-F1`'s primitive, not a new one); where recovery and the
   controller are serialized.
2. **Build + tests**, all offline, before any session:
   - **Parity**: the shadow night's 3,598 reports replayed through the
     live decision path produce the same decisions as shadow — zero
     actions.
   - **Replay of recorded loss**: the `C4-D1` and `CTRL-L1` series through
     the live path; output the would-fire list (time, class, from, to)
     and the transitions-per-10-min it implies; the rate limit must never
     trip on any recorded night, else say so.
   - **Synthetic sequences** for every constraint above: the blackout,
     each hold-down, the increase cadence, the rate limit, the
     `any_override` and age guards, the recovery interlock, the disable
     route, the session reset.
   - `py_compile`; the shadow suite unchanged and passing.
3. **Injection hook**, test-only: `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1`
   enables `POST /plugins/games/adaptive-bitrate/inject?class=FALLBACK`
   (and `ROUTINE`), which feeds the controller one synthetic degraded
   report so it decides as it would on real loss. Refused with 403 unless
   both the flag and live mode are set; absent from status otherwise;
   never left set (teardown confirms).
4. **Session A — silent live hold**: 30-minute attract-mode hold, live
   mode on, clean link, `T2` sampler on. Pre-registered: **SILENT** if
   zero transitions and the close-out rows meet their targets; anything
   else is recorded as what fired and why (from the decision log), and
   the row that missed. `any_override` false at PLAYING.
5. **Session B — injected trigger**: live + inject; after 120 s of
   PLAYING, one injected FALLBACK. Pre-registered: exactly **one**
   `ssrc_change`, the level after = the target the mapping names, output
   gap reported against 186.5 ms, blackout observed (no decision for 3
   reports), then the hold-down, then — with the link clean — the
   increase path brings the stream back to 7000 **one rung per event**,
   each ≥ the increase cadence apart, recorded as times; a second
   injection 30 s after the first must be **refused by the hold-down**
   (logged, no transition). BACK → report stored; lifecycle clean. Outcome
   **WIRED** if all of that holds; **PARTIAL** naming what did not.
6. **Teardown**: mode flag and inject flag unset and confirmed absent in
   the manager and the companion's environ, companion under systemd,
   profile adopted, stream at 7000, game inactive, banner cleared.

## Record and memory

`evidence/C3_L4_L1_LIVE_CONTROLLER_<date>.md` (the design, the mapping
table, the tests with their outputs incl. the would-fire lists, the two
sessions with their numbers, the outcomes, and the plan for the `nft`
night as a numbered hand-step list for the user: what to inject, when,
what the controller should do, what is recorded); evidence dir with
tests, logs, reports, heartbeats, decision log, thermal, manifest;
`patches/C3-L4-L1_*.md`; `PATCH_INDEX.md`; `architecture/ADAPTIVE_BITRATE.md`
(live mode as built); `docs/ROADMAP.md` C3; `docs/PROJECT_STATUS.md`;
`CURRENT.md` (C3.L4: BUILT, live proven on injection; the `nft` night is
the user's); `investigations/ACTIVE.md`; `TOOLS.md` (the flags, the
routes, the rule: never leave live or inject set); the daily file;
`evidence/RUNTIME_VALIDATION.md`. No addresses. Nothing adopted. Nothing
committed.
