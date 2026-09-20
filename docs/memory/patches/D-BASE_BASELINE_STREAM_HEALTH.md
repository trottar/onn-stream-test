---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
durable_memory_updated: true
---

# D-BASE — baseline stream health, and Phase C suspended

## Purpose

Record that the reference stream fails its own baseline, suspend Phase C,
and install the ordered plan that replaces it.

Durable memory only. No source, tool or probe change.

## Expected predecessor

`e2fd7b566534f4bbd9a74d6456916bace7abfc29`

## What was found

47 decoder sessions of >= 15 s, 2026-09-16 to 2026-09-20, all at the 7000 kbps
reference, most with no actuator activity. Median 2,506 decode spikes over
20 ms per minute against 3,600 frames at 60 fps — **~70% of every frame misses
the 16.7 ms budget, in every code epoch.** The stream never reaches 60 fps.
Worst stall 7,341 ms. Audio underruns median 155/min. Lost packets median
199/min on a local link.

Split by client code epoch, the decode fault is constant and the stall tail is
not: worst stall 338 ms across 21 sessions before the 2026-09-19 flattening,
7,341 ms after.

Three faults, none of them bandwidth. Therefore Phase C — which exists to
build adaptive bitrate control — is suspended.

## Changed scope

Added:

- `docs/memory/evidence/BASELINE_STREAM_HEALTH_2026-09-20.md`;
- `docs/memory/decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`;
- `docs/memory/investigations/BASELINE_STREAM_HEALTH.md`;
- `docs/memory/2026-09-20.md`;
- this record.

Replaced:

- `docs/memory/CURRENT.md` — rewritten for the new objective, 8,507 -> 4,558
  bytes;
- `docs/memory/investigations/ACTIVE.md` — baseline health added as the active
  line, Phase C marked suspended;
- `docs/memory/roadmap/STATUS.md` — active section and the reason;
- `docs/memory/MEMORY.md` — durable-fact block;
- `docs/KNOWN_ISSUES.md` — the three faults, the unrecorded link type, and the
  three `C3.L3a` probe defects.

Generated: `docs/memory/patches/PATCH_INDEX.md`.

Unchanged: all source, all tools, all probes, every evidence record. **No
completed Phase C result is retracted.**

## Negative results

- **Phase C ran its full length on an unexamined premise.** Every one of the
  47 session reports was on disk the whole time. Nothing aggregated them, so
  nothing contradicted the assumption that the stream underneath was healthy
  enough to optimize adaptation on. This is the single largest process failure
  on record for this project.
- **A worst-case statistic overruled a distribution.** `C3.L2c` was rolled
  back on `max_output_gap_ms` 359 -> 385, one sample per session, while the
  same data showed a 15x improvement in spikes/min, the best fps and the
  lowest drop rate on record. Reopened here.
- **Instrumentation is the prime suspect in the fault it was built to
  measure.** `C3.L2b` added per-frame and per-packet work to the hot path and
  is the stronger candidate for the stall-tail regression.
- **The two 2026-09-19 changes are not separated.** Epoch B has four sessions,
  two of them sub-30-second fragments. Step 1 settles it with one variable;
  this record does not guess.
- **The physical link type is unrecorded** after five days of transport
  measurement. Loss of 199/min median on a supposedly local link may be fully
  explained by it.
- **Three defects in the `C3.L3a` Part 2 probe** were found by its first run:
  window anchored on sequence start, telemetry paths taken from a probe's
  output artifact rather than the endpoint, and an unanchored rating scale.
  All three are mine, all three are logged, none is fixed here — the probe is
  suspended with Phase C.
- **This patch fixes nothing.** It records, re-sequences and sets a target.
  The first actual repair is Step 1.

## Validation performed

- installer Python compile;
- every figure re-derived by parsing `logs/games/decoder_sessions/*.json`
  directly, not transcribed — 47 sessions, grouped by `received_at_utc`
  against the two patch-record mtimes that bound the code epochs;
- the `C3.L2c` session excluded from both epoch groups so the low-latency
  effect cannot contaminate the epoch comparison;
- sessions under 15 s excluded, and the exclusion stated;
- payload and installed SHA-256 per file, wrong-state rejection before
  modification;
- generated index regenerated and verified after writing;
- LF line endings and trailing newline on every written file;
- `tools/check_memory_health.py` post-write gate with exact-byte rollback;
- `CURRENT.md` re-measured at 4,558 B / 111 lines, `MEMORY.md` at 23,490 B,
  both inside their soft limits;
- ZIP integrity.

**Deliberately not performed:** no self-test, no fixture, no sandbox install.
Tier 1.

No runtime validation applies; this patch changes no executable behavior.

## Privacy

No network addresses appear in this patch or in any file it writes. "Link
type" means wired versus wireless.

## Result

Recorded on install.
