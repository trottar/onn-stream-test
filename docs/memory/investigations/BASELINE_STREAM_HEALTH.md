---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
---

# Baseline stream health — ACTIVE

Decision: `../decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`
Evidence: `../evidence/BASELINE_STREAM_HEALTH_2026-09-20.md`

**Question:** can the Linux host -> onn client native game stream reach
seamless local play, and if not, what is the ceiling and where is it?

Phase C adaptive-bitrate work is suspended until this closes.

## Target (entry criteria for resuming Phase C)

| metric | target | current median |
| --- | --- | ---: |
| decode spikes >20 ms / min | < 200 | 2,506 |
| rendered fps | >= 59.5 | ~56 |
| max output gap, per session | <= 100 ms | 345 |
| stale output drops / min | < 20 | 181 |
| lost packets / min | < 10 | 199 |
| audio underruns / min | < 5 | 155 |

All distributional. No perceptual gate, by explicit instruction.

## Step 1 — stall-tail regression. NEXT.

Worst stall was **338 ms across 21 sessions** before 2026-09-19 01:37 UTC and
**7,341 ms after**. Two client changes landed in that hour and the data cannot
separate them.

Revert **only** the `C3.L2b` hot-path instrumentation. Keep the flat layout.
Take five sessions of >= 2 minutes of ordinary play, no actuator activity.

- tail <= ~340 ms -> `C3.L2b` caused it. Re-add the instrumentation off the
  hot path (ring buffer written by a separate thread, or sampled rather than
  per-frame).
- tail still high -> the rebuild or the flattening is implicated and the
  layout change needs a direct look.

Acceptance is the tail across five sessions, not one. Session length is not a
confound: a 16.7-minute pre-flatten session maxed at 331 ms.

## Step 2 — decoder path

The dominant fault and the oldest. ~70% of frames over the 16.7 ms budget in
every epoch since at least 2026-09-16.

Mechanism on record: the decoder holds **11-13 frames in flight**, which at
60 fps is 180-220 ms of pipeline depth before any decode work is counted.
`latest_feed_delay_ms` is 0 and `input_waits` stays in the tens, so the client
feeds promptly and is never starved — the decoder is buffering for throughput.
`stale_output_drops` reached 2,461 of 50,515 frames in one session.

Work:

- **reopen `C3.L2c`** and judge it on `spike_20_ms/min`,
  `stale_output_drops` and fps. Its one low-latency session ran 159
  spikes/min against 1,828-2,723 for all 46 others, with the best fps and
  lowest drop rate on record. It was rolled back on a single
  `max_output_gap_ms` sample;
- attack the in-flight depth directly, which the low-latency flag alone did
  **not** fix (12 frames in flight even with it): feed pacing, and whether a
  tunneled or explicitly-timed output path is available on this decoder;
- re-audit the Android receiver's resync and IDR-acceptance policy, which has
  not been looked at since `C3.L0`.

## Step 3 — transport

199 lost packets/min median on a local link, reaching 2,094.

**Record the physical link type first — wired or wireless.** Nothing on record
states which it is, and the loss column is consistent with a wireless link. If
it is wireless, that single fact may explain the whole column and the correct
first action is to wire it, not to change code.

The deferred UDP burst/gap pathology belongs to this step. See
`DEFERRED.md` and `docs/KNOWN_ISSUES.md`.

## Step 4 — audio

69 underruns/min before the 2026-09-19 boundary, 139 after, spiking to 2,555.
No investigation exists. Not started.

## Step 5 — client viability. PRE-REGISTERED.

If after steps 1-3 a healthy decode path on a wired link still cannot reach
`spike_20_ms/min < 200` and fps `>= 59.5`, **the onn is the ceiling and the
client changes.**

Even the low-latency session held 12 frames in flight with a 107 ms worst
frame. The project description calls the onn "the first client", so a second
client is consistent with the architecture.

This criterion is written down now so the conclusion is reached by measurement
rather than by attrition.

## Suspended, not failed

- `C3.L4` automatic controller — suspended. Its gate (`C3.L3a` Part 2) is not
  the blocker; the premise is.
- `C3.L3a` Part 2 — suspended. The probe is installed and carries three known
  defects from its first run: the mark-association window anchors on sequence
  start so ramps close their window before finishing; the telemetry field
  paths were taken from a probe's output artifact rather than the endpoint, so
  settling was never measured; and the picture rating used an unanchored 1-5
  scale that silently rescaled 1-10 answers. Fix these before any rerun. The
  2026-09-20 session's raw marks and per-cycle timings are retained in
  `logs/streaming/c3_l3a_gameplay_acceptance_state.json` and can be re-scored
  without replaying.
- Phase C's completed items stand. The Linux actuator is real and correct.

## Privacy

No network addresses appear in this record. "Link type" means wired versus
wireless.
