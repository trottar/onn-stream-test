---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S2, queue item 2 (the user's go, 2026-10-06): the companion's ~110 MB anon step at the first EPG grab. Probe what holds it; one change behind a flag; benchmark E1-META ×2. Accept/reject by the pre-registered bar. Nothing adopted; nothing committed
---

# E3-S2 — the companion's memory after a grab

**Measured bottleneck (E2-S1 §5).** The first grab adds 106-114 MB of
anonymous memory to the companion (file-backed unchanged); PSS then
moves in steps to 160-200 MB (META 26 → 161 MB; CONC r2 ended ~200 MB).
The Node child peaks at ~635-660 MB per grab and exits.

**Narrow hypothesis (E2's).** The companion keeps (or fragments) the
parsed guide in-process after each grab: either the parse's retention
or the allocator's high-water mark explains the step.

## 1. Probe (measurement first; decides which of the two)

With the stream idle, one forced grab of one channel, then a second:

- `tracemalloc` (or `gc.get_objects()` sized by type) snapshots in the
  companion before the grab, after the grab's parse and 60 s later, via
  a debug endpoint or a one-off `PRIVYHUB_MEM_PROBE=1` hook that the
  task adds and leaves off;
- `smaps_rollup` anon before/after, as E2;
- `malloc_trim(0)` called once through the probe hook after the second
  grab, anon measured again.

The probe answers: **retention** (live Python objects account for ≥
50 % of the step) or **allocator high-water** (`malloc_trim` returns ≥
50 % of it). `e3_s2_<date>/probe.md`.

## 2. The one change (chosen by the probe, pre-registered either way)

- **Retention** → the parsed guide is not kept in the companion's
  process after the grab's result is written to its store: the
  in-memory copy is dropped (or served from the on-disk store on
  request) — behind **`PRIVYHUB_EPG_RELEASE_PARSE=1`**.
- **Allocator** → `malloc_trim(0)` after each grab completes (and the
  arena cap `MALLOC_ARENA_MAX=2` in the unit's environment for the run) —
  behind **`PRIVYHUB_EPG_MALLOC_TRIM=1`**.

One of the two, the probe's. Absent = today, byte for byte. If the probe
shows neither (both < 50 %), record the split and apply the larger; say
so.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs**: E1-META ×2 with the flag (E2's 20-min window, gaps), the
  flag in a drop-in for those runs only, removed at teardown.
- **Bar, ACCEPTED only if all hold:**
  - companion PSS at the window's end ≤ **60 MB** in both runs (E2:
    161 MB; pre-grab 26-35 MB);
  - companion PSS does not "keep growing" by E2's rule in the last 15
    min;
  - grabs failed 0; grabs ok ≥ 205; median grab ≤ 1.3× E2's (≤ 6.8 s);
  - **the guide still serves**: the EPG read endpoint returns the same
    channel count and a programme count within ± 5 % of a read taken
    before the runs (recorded in the probe);
  - host CPU within ± 2 points of E2's META (9.8).
- **Reported:** anon vs file split at the first grab and at the end;
  the Node child's peak PSS (should be unchanged — the change is in the
  companion).

## 4. The record

`evidence/E3_S2_COMPANION_GUIDE_RETENTION_<date>.md` + `e3_s2_<date>/`
per the queue; `patches/E3-S2_...md`; `logs/e3_s2_git_status.txt`. The
probe hook stays in the tree, off. Flag absent; E2's final state
restored; then queue item 3.
