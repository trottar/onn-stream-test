---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
---

# Current State

Section headings below are fixed by `tools/check_memory_health.py`. Do not
rename or duplicate them; the checker requires each exactly once.

## Active Objective

**Baseline stream health.** Reach seamless local play on the Linux host ->
onn client native game stream, measured against the numeric target below.
Remote play is unreachable without it.

Phase C adaptive-bitrate work is **SUSPENDED** until this closes. Decision:
`decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`.

## Current Work Item

**Step 1 — the stall-tail regression.** Revert only the `C3.L2b` hot-path
instrumentation, keep the flat Android layout, take five sessions of >= 2
minutes of ordinary play with no actuator activity, compare the tail.

- tail <= ~340 ms -> `C3.L2b` caused it; re-add the instrumentation off the
  hot path;
- tail still high -> the rebuild or the flattening is implicated.

One variable, existing metric, no new tooling. Full plan:
`investigations/BASELINE_STREAM_HEALTH.md`.

## Verified State

The reference stream is **not healthy and never has been**. 47 decoder
sessions, 2026-09-16 to 2026-09-20, all at 7000 kbps, most with no actuator
activity. Record: `evidence/BASELINE_STREAM_HEALTH_2026-09-20.md`.

| metric | target | median now |
| --- | --- | ---: |
| decode spikes >20 ms / min | < 200 | **2,506** |
| rendered fps | >= 59.5 | ~56 |
| max output gap | <= 100 ms | 345 |
| stale output drops / min | < 20 | 181 |
| lost packets / min | < 10 | 199 |
| audio underruns / min | < 5 | 155 |

At 60 fps the frame budget is 16.7 ms, so **~70% of every frame misses budget
in every session on record.** Worst stall 7,341 ms. The stream never reaches
60 fps.

Three faults, ranked:

1. **Decoder path** — chronic, largest, predates everything. The decoder holds
   11-13 frames in flight (180-220 ms of depth) while the client feeds
   promptly and is never starved. `C3.L2c`'s low-latency session is the only
   one at 159 spikes/min against 1,828-2,723 for all 46 others, with the best
   fps and lowest drops on record. **It was rolled back on one
   `max_output_gap_ms` sample and is reopened on this evidence.**
2. **Stall-tail regression**, 2026-09-19 01:37-02:38 UTC. Worst stall 338 ms
   before across 21 sessions, 7,341 ms after. `C3.L2b` is the stronger suspect
   on mechanism; `ANDROID-FLAT` is not excluded. Not separated — that is
   Step 1.
3. **Audio underruns** — 69/min before, 139/min after, peaking 2,555. Never
   investigated.

Phase C itself is sound and is **not discarded**: the Linux actuator is real,
measured and correct, and `C3.L3a` Part 1 showed chained ladder transitions
are clean on both host and client. It is sequenced wrongly — a mechanism
awaiting a reason. Sub-item detail: `investigations/ACTIVE.md`.

## Next Action

Build and install the Step 1 revert probe: `C3.L2b` hot-path instrumentation
out, flat layout kept, then five sessions of >= 2 minutes and a tail
comparison. Session length is not a confound — a 16.7-minute pre-flatten
session maxed at 331 ms.

## Success Criteria

Phase C resumes only when the whole target table above is met, or when the
attempt is formally abandoned.

**Pre-registered client decision:** if after Steps 1-3 a healthy decode path
on a wired link still cannot reach `spike_20_ms/min < 200` and fps `>= 59.5`,
the onn is the ceiling and the client changes. Written down now so it is
reached by measurement rather than attrition.

No perceptual gate. Every acceptance metric is instrumentation, by explicit
instruction.

## Do Not Reopen Without New Evidence

- D4 Games and D5 media/server restoration.
- The Windows-era C3 record (D-063, D-067 through D-071).
- The `C3.L2` classification: Linux is `video_only_restart`, not authorized
  for automatic adaptation during play.
- `C3.L3a` Part 1's result — chained ladder transitions are clean.

## Relevant References

- `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md` — the suspension, the
  target, the ordered plan, the pre-registered client decision.
- `investigations/BASELINE_STREAM_HEALTH.md` — the active investigation.
- `evidence/BASELINE_STREAM_HEALTH_2026-09-20.md` — the 47-session aggregate
  and the epoch split.
- `investigations/ACTIVE.md` — Phase C sub-item states, all suspended.
- `PHASE_C_CONTEXT.md` — Phase C brief; accurate but **not the active line**.
- `roadmap/STATUS.md` — roadmap position.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
