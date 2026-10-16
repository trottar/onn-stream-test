---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G5-S2 (session B, unattended): the WAN adaptation rules G5-S1 wrote (`docs/WAN_ADAPTATION_RULES.md`, R1-R5, ROADMAP §G5's five priorities) implemented as a guarded input to the live ladder, behind `PRIVYHUB_WAN_ADAPTATION=1` (absent = the ladder exactly as adopted). Proved by replaying recorded runs through the ladder's decision logic with and without the rules. No stream; the live smoke is a later session-A item
---

# G5-S2 — WAN adaptation rules, behind a flag

Read first: `docs/WAN_ADAPTATION_RULES.md` (R1-R5 as G5-S1 wrote them:
preserve control/session correctness; prevent runaway latency; reduce
bitrate/quality when capacity tightens; FEC only when loss justifies it
— C4-M1 says no FEC switch today; recover upward slowly with
hysteresis), `G5_S1_…` (the classes, their thresholds, the `wan` object),
`C3_L4_L1_…`, `C3_L4_L2_…`, `C3_L4_N1_…`, `C3_L4_N2_…`, `C3_L4_D1_…` (the live
ladder: its inputs, the capacity trigger, the increase rule with its
hysteresis, how decisions are recorded), `C5_M3_…` (720p/4000 as the
remote floor; the lower rungs that failed transport), the ladder
controller's code and `decisions.jsonl`'s format.

## 1. The design (in the record §1 before the code, hashed)

- **Where the rules sit:** a module `companion/wan_adaptation.py` that
  takes the G5-S1 window class and measures and the ladder's current
  state, and returns **at most one suggestion per decision tick**: hold
  / step down / allow step up / floor-at-4000 — the ladder's existing
  rule remains the decider; with the flag, the suggestion is applied
  **as an additional constraint** (a step-down suggestion forces a
  step-down the ladder would otherwise not take; a "no step up" blocks
  an increase; nothing else). Without the flag the module is not
  imported.
- **R1 (control first):** never a suggestion that would restart the
  session or change the controller path; a `path-changed` class only
  marks a cool-down (no step up for N s).
- **R2 (no runaway latency):** `latency-limited` or `starved` for 2
  consecutive windows → step down one rung; the stale-drop threshold
  from D-BASE.
- **R3 (capacity):** `capacity-limited` → step down to the next rung,
  with the remote floor **720p/4000** (C5-M3) — never below it on a
  remote path; on the LAN the ladder's own floor.
- **R4 (FEC):** no change (C4-M1); the rule is recorded as "FEC switch:
  not implemented; the fixed 8+1 stays".
- **R5 (slow recovery):** step up only after K clean windows (K from the
  ladder's existing hysteresis, doubled on a remote path), one rung at
  a time.
- Every suggestion written to `decisions.jsonl` with `source: wan_rules`,
  the class, the rule id and the ladder's resulting decision.

## 2. The code and the proof

- The module; the guarded hook in the ladder (one `if` on the flag; a
  patch).
- **Replay harness** (`g5_s2_…/replay.py`): feed recorded runs'
  telemetry + decisions through the ladder's decision function in
  process, flag absent → the decisions reproduce the recorded ones
  exactly (the byte-for-byte proof); flag present → the rules'
  suggestions and the resulting decision stream, for: the lossy
  `e4_s4b … run3`, the cleanest `e4_s4b … run2`, `cl_b3 … run1` (today's
  best link), and a CONC run with its grab bursts (`e4_s4 … E1-CONC_flag
  run1`). State, per run: how many ticks the rules changed, which rule,
  whether R5 ever recovered the rung, whether the remote floor would
  have engaged. No claim that the result is better — that is the live
  test's job.
- Unit tests per rule with hand fixtures; the G1/G3/G5-S1 suites still
  green; the redactor.

## 3. The record

`evidence/G5_S2_WAN_ADAPTATION_RULES_2026-10-16.md` + `g5_s2_…/` (the
design + hash, the diff, the test output, the replay tables,
`redact_check.txt`, `manifest.sha256`); `docs/WAN_ADAPTATION_RULES.md`
status lines; ROADMAP §G5; `patches/G5-S2_…md`; `logs/g5_s2_git_status.txt`.
"Pending on the stream": the live smoke with the flag on the LAN (10
min) and the first off-site run with it (G4-S2). Nothing adopted.
