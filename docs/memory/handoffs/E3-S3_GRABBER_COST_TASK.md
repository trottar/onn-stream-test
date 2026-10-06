---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S3, queue item 3 (the user's go, 2026-10-06): the EPG grabber's own cost (node 67-82 % of a core, ~480 MB mean / ~650 MB peak PSS per grab, `npm run` per channel). Probe where the CPU-seconds go; one change behind a flag; benchmark E1-META ×2. Accept/reject by the pre-registered bar. Nothing adopted; nothing committed
---

# E3-S3 — the EPG grabber's own cost

**Measured bottleneck (E2-S1 §8 item 3).** Per grab: the Node child at
67-82 % of a core, ~480 MB mean and ~635-660 MB peak PSS, median grab
5.2-5.9 s; one `npm run grab` invocation per channel, six channels per
cycle, ~210-230 grabs per 20 min in META.

**Narrow hypothesis.** A large share of each grab's CPU-seconds and
peak memory is fixed start-up (npm's wrapper, node's module load, the
grabber's own initialization) repeated per channel, not the channel's
fetch and parse.

## 1. Probe (measurement first)

Three forced grabs of one channel with the stream idle, the per-second
per-thread sampler on; from `threads.jsonl` and the process tree:
CPU-seconds and peak PSS split into **(a) npm wrapper, (b) node until
the first network byte, (c) the fetch+parse to exit**. `e3_s3_<date>/probe.md`.

## 2. The one change (by the probe, pre-registered either way)

- **(a)+(b) ≥ 40 % of CPU-seconds** → start-up is the cost: the
  companion invokes `node <grabber entry>` directly with the same
  arguments and environment (no `npm run`), **behind
  `PRIVYHUB_EPG_DIRECT_NODE=1`**.
- **otherwise** → the per-channel repetition is the cost: one grabber
  invocation per refresh cycle for the configured channel set (the
  grabber's own multi-channel mode if it has one; else a channel list
  passed once), **behind `PRIVYHUB_EPG_BATCH_CHANNELS=1`**; the plugin's
  per-channel status and the refresh endpoint's contract unchanged.

Absent = today, byte for byte. One of the two.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs**: E1-META ×2 with the flag (E2's window, gaps; drop-in for
  those runs only). Note: with batching, "a grab" is the cycle; the
  metric is per channel-grab, i.e. CPU-seconds and the cycle's peak PSS
  divided by the channels it covered — said in the pre-registration so
  the two variants compare on the same unit.
- **Bar, ACCEPTED only if all hold:**
  - EPG child CPU-seconds per channel-grab ≤ **0.7×** E2's (E2: ~5.9 s ×
    0.67-0.82 ≈ 4.0-4.8 CPU-s; so ≤ 3.3 CPU-s), both runs;
  - peak PSS per invocation not above E2's (≤ 660 MB);
  - grabs failed 0; every configured channel refreshed at least as often
    as in E2's cycle (≥ 34 refreshes per channel per 20 min);
  - the guide still serves (same channel count, programme count ± 5 %
    of a pre-run read);
  - host CPU mean ≤ E2's META (9.8) — reported if higher but the
    per-grab CPU-seconds bar holds; gated only on the per-grab figure.
- **Reported:** median grab/cycle wall time; the companion's PSS (S2's
  flag is absent here; no compounding).

## 4. The record

`evidence/E3_S3_GRABBER_COST_<date>.md` + `e3_s3_<date>/` per the
queue; `patches/E3-S3_...md`; `logs/e3_s3_git_status.txt`. Flag absent;
E2's final state restored; then queue item 4.
