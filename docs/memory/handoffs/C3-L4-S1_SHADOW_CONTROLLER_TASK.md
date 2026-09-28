---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L4-S1, the shadow controller: implement the C3 adaptive-bitrate policy engine in the companion behind a flag that defaults OFF, in a SHADOW mode that reads telemetry and logs every decision it would make but never actuates; unit-test the policy against synthetic telemetry; run it in shadow over one night of attract-mode holds and report false triggers on a healthy stream; the design answers C3-L2's video_only_restart classification explicitly; authorizes nothing; authorized by the user 2026-09-24 for the weekend queue
---

# C3-L4-S1 — the shadow controller

**Why.** `C3-L2` blocks automatic adaptation during play until the gate
(`C3.L3a`) is read; three of four rerun sessions are in and the pooled
table so far (W 5.0) says ramps were marked 11/15 (20 marks against 5.6
by chance), jumps 5/15 (5 against 2.1), decoys at chance (4/30 and
9/30). Whatever the user's reading, most of `C3.L4` is the same
controller: the states, the ladder, the asymmetry, the hold-down, the
blackout after acting, the reason codes, the fallback. What differs is
**when it is allowed to act**. So build the policy engine now in a mode
that **cannot act** — it watches the same telemetry a live controller
would and writes down what it would have done — and measure the one
thing measurable without the user: does it stay silent on a healthy
stream, cold and warm, for a night? A controller that would have stepped
down during a clean hold fails before any gate question arises.

Read first: `architecture/ADAPTIVE_BITRATE.md` (§C3 control cadence,
safety state, fast-down / slow-up, signal interpretation, telemetry
freshness, bitrate bounds, decision diagnostics — these are the design
and this task implements them, not a new one),
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` (§Authorized use — the
constraint this must answer), `evidence/C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md`
(settling: telemetry can read 40-54 fps for one to three reports after a
restart; the ~190 ms cost; the one-in-thirty extra-GOP tail),
`evidence/C3_L3A_R1_SESSION1_2026-09-24.md` and `…R2_SESSION2…` (a
ramp's three restarts are each noticed; a single jump often not),
`evidence/D_BASE_CLOSEOUT_2026-09-23.md` and `D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`
(what a healthy stream looks like, cold and warm — the warm-state
single-packet loss is normal and covered), `companion/diagnostics/stream_telemetry.py`
(the surface), `companion/native_stream.py` (where the transition
primitive lives), `TOOLS.md`, `evidence/c3_l3a_s1_2026-09-24/c3_l3a_s1_run.sh`
(the hold harness to derive from).

**Scope.** Companion: one new module (`companion/adaptive_bitrate.py` or
under `companion/diagnostics/`), one status field on
`native-stream-status` (`adaptive_bitrate`, schema
`privyhub_adaptive_bitrate_v1`), one environment/profile flag
`PRIVYHUB_ADAPTIVE_BITRATE_MODE` with values `off` (default) and `shadow`;
**no `live` value exists in this task** — the word must not appear as an
accepted mode. The engine calls no actuator in any mode this task ships.
No client, profile, encoder, route-shape or transport change; the adopted
profile stays adopted (confirm before every hold). The companion is
restarted through its unit only; nothing else on the host.

## The design — answer `C3-L2` first

Write it into `architecture/ADAPTIVE_BITRATE.md` as a new section
"C3.L4 shadow controller — S1" before coding:

- **Authorization answer.** `video_only_restart` is authorized for
  fallback/recovery and not for automatic adaptation during play. The
  controller therefore has two trigger classes, and only the first exists
  as an acting path in any future live mode: (1) **FALLBACK** — the stream
  is already failing by the close-out's own rows (the pre-registered
  thresholds below), where a ~190 ms restart is cheaper than what the
  player is already getting; (2) **ROUTINE** — capacity/latency pressure
  short of failure, which `C3-L2` does not authorize and which the gate
  data so far says is noticed. Shadow mode logs both classes separately
  so the night shows how often each would fire. The design says in one
  sentence that ROUTINE acting is gated on the user's `C3.L3a` reading
  and is not built here.
- **Jump, not ramp.** The rerun evidence: three rung restarts in ten
  seconds were marked 11/15, single restarts 5/15. A decrease is one
  transition to the target level, never a ramp; an increase is one level
  per decision (the slow-up rule) — so an increase is inherently a single
  restart per step, at a longer interval.
- **Ladder** `(5000, 5500, 6000, 7000)` (`D-066`, `C3.L3`), max 7000,
  min 5000; reference 7000.
- **Cadence** the 2 s client report; decisions only on fresh, distinct
  snapshots (`session_elapsed_ms` advanced — the probe's rule).
- **Blackout after any action**: ignore the next **3** reports (≥ 6 s) —
  `S1` measured settling at one to three reports, once four. Then a
  **hold-down** of **30 reports** (60 s) before any further decision in
  the same direction, and **60 reports** (120 s) before a reversal.
- **Evidence for a decrease** (`ADAPTIVE_BITRATE.md` §Signal
  interpretation, made numeric against the close-out): over a window of
  **5 consecutive fresh reports** (10 s), FALLBACK when `recent_fps`
  < 50 on all 5 **and** either `queue_depth` ≥ 2 on ≥ 3 of 5 or
  `output_gap_ms` > 250 on ≥ 2 of 5 (the transport's own gaps run 100-
  200 ms and must not trigger); ROUTINE when `recent_fps` < 57 on ≥ 4 of
  5 with `queue_depth` ≥ 1 on ≥ 3 of 5. Recovered FEC packets, stale
  drops, `lost_packets_delta` alone, or `waiting_for_idr` during a known
  resync never count (D-019). Numbers are pre-registered here against
  the close-out band (fps 59.9, queue 0, gap ≤ 163) and the warm-state
  loss (audio 0.25-1.44/min, video post-FEC ≤ 8.7/min — not a trigger).
- **Evidence for an increase**: at a level below 7000, **90 consecutive
  clean reports** (180 s: fps ≥ 59 and queue 0 and gap ≤ 150 on every
  one) → one step up. **Oscillation guard**: a third direction change
  within 10 minutes → `HOLD` for the rest of the session with reason
  `oscillation`.
- **Stale / fail-safe**: telemetry not fresh, `available` false, or no
  distinct snapshot for 3 intervals → `TELEMETRY_STALE`, no decision,
  reason exposed. Actuator failure → `ACTUATOR_FAILED`, frozen for the
  session (shadow: never reached).
- **States** exactly as the architecture lists them; inspectable in the
  status field with: mode, state, current/target level, validated ladder,
  telemetry age, decision sequence, last reason code and its measurements,
  hold-down remaining, clean-sample count, blackout remaining, would-act
  counters by class, and — in shadow — `acted: false` always.
- **Decision log**: one JSON line per decision or state change to
  `logs/games/adaptive_bitrate_shadow.jsonl` (bounded rotation like the
  other logs), never per report.

## Validation before any hold

1. Unit tests with synthetic telemetry sequences (a small test module
   under `tools/` or `companion/tests/`, run with `python3 -m unittest`):
   a clean stream → no decision for 1,000 reports; a FALLBACK pattern →
   exactly one would-decrease, then blackout, then hold-down honoured; a
   ROUTINE pattern → one would-decrease logged as ROUTINE; recovery → one
   would-increase after exactly 90 clean reports and not before; an
   alternating pattern → `oscillation` HOLD on the third reversal; stale
   telemetry → `TELEMETRY_STALE` and no decision; a restart's own
   settling signature (one report at 45 fps then clean) → **no**
   decision. Every test names the rule it checks.
2. `py_compile`; the flag `off` leaves `native-stream-status` unchanged
   except the new field reading `mode: off`; `shadow` set through
   `systemctl --user set-environment` for the night and **unset at the
   end** (`unset-environment`, confirmed in the companion's environ after
   the final restart).

## The night — shadow over healthy holds

Harness derived from `c3_l3a_s1_run.sh` (plain holds only; no probe, no
transitions). PS1 reference title, attract mode, `T2` sampler at 10 s,
companion under systemd with `PRIVYHUB_ADAPTIVE_BITRATE_MODE=shadow`:

| # | hold | length |
| --- | --- | --- |
| 1 | cold (≥ 40 min after the last `session_ended`) | 20 min |
| 2 | warm | 20 min |
| 3 | warm | 60 min |
| 4 | warm | 20 min |

**Pre-registered reading.** The stream is healthy by the close-out rows
in every hold (report them; if a hold fails a target row, its would-act
count is reported separately and does not count against the controller).
On healthy holds: **SILENT** if the would-act count is **0 FALLBACK and 0
ROUTINE** across all four; **NOISY** otherwise, with every would-act
listed (time, class, the five reports that triggered it, what the decoder
report shows at that moment). `TELEMETRY_STALE` entries are reported but
are not would-acts. A NOISY result on a healthy stream means the
thresholds are wrong, not the stream; do not retune in this task — record
the measurements that would have set them right.

## Record and memory

`evidence/C3_L4_S1_SHADOW_CONTROLLER_<date>.md` — the design answer to
`C3-L2`, the constants and their sources, the unit-test list and results,
the four holds with their close-out rows and would-act counts, the
verdict, what the live mode would still need (the gate reading; the
fault-injection night, which is the user's `nft` and not Code's). Evidence
under `evidence/c3_l4_s1_<date>/` (test output, per-hold reports,
heartbeats, thermal jsonl, the shadow decision log, status snapshots,
journal redacted, manifest). `patches/C3-L4-S1_*.md` with per-file
SHA-256s; `PATCH_INDEX.md`. `architecture/ADAPTIVE_BITRATE.md` (the new
section), `investigations/ACTIVE.md` (a `C3.L4` entry: shadow built,
live gated on the gate), `CURRENT.md`, `TOOLS.md` (the flag; never leave
it set), the daily file, `handoffs/CURRENT_HANDOFF.md` one line,
`evidence/RUNTIME_VALIDATION.md` (shadow: SILENT / NOISY). `C3.L4` stays
BLOCKED for live use. Teardown per `TOOLS.md`; flag unset; companion
under systemd; profile adopted; game inactive. No addresses or device
identifiers in any file. Nothing committed.
