---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G5-S1 (overnight, session B): WAN-aware telemetry, the classification half. ROADMAP §G5 says reuse Phase C's telemetry rather than build a parallel WAN streamer. This task reads what the live ladder, the FEC sender, the heartbeat and the recovery state already produce, adds the overlay provider's path state, and classifies a session's link into the eleven measures §G5 lists — behind `PRIVYHUB_WAN_TELEMETRY=1` (absent = today, byte for byte). No adaptation change (that is G5-S2, with the rule set written here). Verified by replaying recorded runs. No stream, no restart
---

# G5-S1 — WAN telemetry classification

Read first: ROADMAP §G5 (the eleven measures and the five-step
adaptation priority); `C2_TELEMETRY_CONTRACT_INVENTORY_…`,
`C2_STREAM_TELEMETRY_RUNTIME_VALIDATED_…` (what the heartbeat carries),
`C3_L4_L1_LIVE_CONTROLLER_…` and `C3_L4_L2_…` (the live ladder's
decisions and their inputs), `C4_M1_FEC_ARM_…` and `D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_…`
(FEC recovered / unrecoverable groups, loss counters), `D_BASE_P5_WHICH_QUEUE_…`
and `D_BASE_P6_…` (queue growth, sender pacing), `D_BASE_P1_STALE_THRESHOLD_…`
(stale drops), `E3_A3B_…` (recovery v2's gap log), `companion/overlay/`
(G1-S1's path state); the recorded runs' `telemetry.jsonl`,
`decisions.jsonl`, `gaps.jsonl`, `recovery.jsonl` under any
`e4_s4b_2026-10-10/runs/…` and `cl_b2_2026-10-16/runs/…` (the formats).

## 1. The module (`companion/wan_telemetry.py`)

- **Inputs, all existing:** the per-second heartbeat fields (delivered
  bytes/frames, loss counters, resyncs, stale drops, decoder starvation,
  client pauses), the FEC sender's recovered / unrecoverable group
  counts, the live ladder's decisions (rung, reason), the sender's pacing
  and queue depth readings, recovery v2's gap log, the controller
  return-path RTT if the protocol has an echo (say if not: "RTT: not
  measured; G5-S2 adds an echo"), and the overlay provider's `state()`
  (direct / relayed / none; path-change events as state transitions).
- **Output, per session, a `wan` object** on the session report and on
  `/status` while PLAYING (only with the flag): the eleven measures as
  §G5 lists them — delivered goodput (kbit/s, 10-s window), packet loss
  (per min, pre- and post-FEC), FEC recovered / unrecoverable groups,
  jitter / inter-arrival (p50 / p95 ms if the heartbeat carries arrival
  times; else "not carried"), RTT / echo latency, sender pacing state,
  queue / buffer depth and trend, decoder starvation / stale drops,
  overlay path (direct / relayed / none), MTU / fragmentation symptoms
  (from the provider's MTU constraint and any oversize-drop counter;
  else "not observed"), reconnect / path-change events (count,
  timestamps relative to session start). Each measure carries its source
  field name, so a reader can trace it.
- **A classification** per 10-s window and per session: `clean`,
  `lossy`, `capacity-limited`, `latency-limited`, `path-changed`,
  `starved` — with the thresholds **written in the record §1 before the
  code** and taken from existing records (D-BASE's loss row < 10/min,
  the stale row < 20/min, the live ladder's capacity trigger, C5-M3's
  rung wire rates); where no number exists, the class is "not
  classified; G5-S2". No new threshold invented.
- **The adaptation rule set, written, not implemented:** §G5's five
  priorities as concrete rules against these classes (what the ladder
  would do at each class, with hysteresis), as `docs/WAN_ADAPTATION_RULES.md`
  — the input to G5-S2.
- **Flag absent = today:** no import at runtime, no field, no thread.

## 2. Verification (no stream)

- `tests/wan_telemetry/`: unit tests per measure with hand fixtures;
  **replay tests** that feed recorded runs' telemetry files through the
  module (at least: a lossy LAN run from `e4_s4b_…/runs/E1-PS1-STREAM/run3`
  (652/min), the cleanest available (`e4_s4b … run2`, 66/min), and
  tonight's `cl_b2_…/runs/E1-PS1-STREAM_flag/run1`) and assert the
  classes those nights earned — the fixtures redacted to ports and
  counters, no address; the module's per-window output for each replay
  saved in the record's directory.
- The byte-for-byte check: `/status` and the session report schema
  without the flag identical to today (the handler comparison as G3-S1
  did, in-process).
- The redactor over everything written.

## 3. The record

`evidence/G5_S1_WAN_TELEMETRY_CLASSIFICATION_2026-10-16.md` +
`g5_s1_2026-10-16/` (the thresholds table with sources, the diff, the
test output, the replay outputs, `redact_check.txt`, `manifest.sha256`);
`docs/WAN_ADAPTATION_RULES.md`; ROADMAP §G5 status; `patches/G5-S1_…md`;
`logs/g5_s1_git_status.txt`. "Pending on the stream": the live smoke with
the flag (session A, after CL-B2 closes). Nothing adopted.
