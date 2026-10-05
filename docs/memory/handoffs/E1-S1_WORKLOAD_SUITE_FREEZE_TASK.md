---
memory_schema: 1
as_of: 2026-10-05
status: TASK HANDOFF — E1-S1, the first Phase E task (the user's go, 2026-10-05, "let's start E1"): freeze the workload suite — inventory what each ROADMAP E1 workload is on this host and whether it can run unattended today, build one runner with one sampler set, dry-run every runnable workload twice for repeatability, write the frozen suite as a document with a pre-registered repeatability bar, and list for the user what is absent (fixtures, a camera, a power meter, the concurrency pairs). Nothing optimized, nothing adopted, nothing committed
---

# E1-S1 — freeze the workload suite

**Why.** Phase C is closed; Phase E's first step (`docs/ROADMAP.md`,
E1) is a **repeatable** workload suite, because E2's measurements, E3's
optimization loop and E4's floor all compare against it. "Repeatable"
means: started by one command, no hands, the same inputs every time, a
defined warm-up and steady state, one sampler set, and a run-to-run
agreement bar written before the runs. Phase E's scope is NES / SNES /
Genesis / PS1; N64 and above are excluded. **No optimization in this
task** — E3 is later and needs this suite first. No hardware claim.

Read first: `docs/ROADMAP.md` Phase E (E1-E7); `CURRENT.md`;
`docs/memory/MEMORY.md`; `evidence/D_BASE_CLOSEOUT_2026-09-23.md` (the
stream rows); `evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md` §2
and `c5_m4_2026-10-01/c5_m4_sampler.py`, `c5_m4_host_table.py` (the
1-s host sampler: CPU per core, GPU busy, GPU W, per-process % of a
core, Tctl); `d_base_t2_2026-09-23/` (T2 host rows); `D5_TV_MEDIA_CLOSEOUT_2026-09-17.md`,
`D122_D54_TV_MEDIA_REGRESSION_RUNTIME_ACCEPTANCE_2026-09-17.md`,
`D136_FOCUSED_TV_MEDIA_AUTOMATED_ACCEPTANCE_2026-09-17.md` (how Live TV
and VOD are driven without hands); `D7_R1_LINUX_REGRESSION_2026-09-25.md`
and `tools/d7_regression.py` (the scripted launch rows per system);
`D090_D4_LINUX_GAMES_ACCEPTANCE_2026-09-16.md` and
`A9_NES_GENESIS_NO_FIXTURE_CORRECTION_2026-09-10.md` (which systems have
fixtures); `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md` (the host);
`TOOLS.md` (routes, samplers, the host-shell operation, the onn).

## 1. Inventory — before anything runs (`e1_inventory.md`)

For each ROADMAP E1 workload, one row: **what it is on this host** (the
companion route or launch path; the fixture; what the onn shows), **can
it run unattended today** (yes / no and what is missing), **its natural
steady state** (attract loop, a playing VOD, a tuned channel, an idle
desktop), and the telemetry it already produces:

idle Linux + PrivyHub · Live TV (a tuned channel on the onn through the
companion; the EPG warmer) · VOD (a local file playing on the onn) ·
browser / live source (what exists, if anything) · camera / live source
(is a camera attached? `pc_camera.log` says what it last was) · NES ·
SNES · Genesis (fixtures: SNES and PS1 exist; NES / Genesis had none —
say so, the user supplies them or the rows stay ABSENT) · PS1 local
emulation (RetroArch on the host, no stream) · PS1 + native streaming
(the adopted 720p/7000 stream, live adaptive by default, 4x source) ·
the 720p60 reference profile (same as the previous row — say whether E1
needs it separately) · higher Phase-C profiles (the 1080p rung behind its
flag; one row, flag on, injected entry) · metadata / storage work (the
library scan, EPG grab, thumbnail or metadata reconcile — whatever the
companion runs that is storage-bound) · concurrent core workloads (the
pairs the companion can actually run at once: PS1 streaming + Live TV on
the onn is not possible on one client — say what is; e.g. PS1 streaming
+ the EPG grabber, PS1 streaming + a VOD transcode if one exists, the
library scan during a stream).

Also inventory **the samplers**: what `c5_m4_sampler.py` and T2 already
give; what is missing for E2 and whether it is available on this host
without new hardware — RAM working set per process (`/proc/<pid>/smaps_rollup`
PSS), swap, storage latency / throughput (`/proc/diskstats` deltas; the
block device the data lives on), network bytes per interface, the
hardware video engine (whether `amdgpu` exposes VCN busy; if not, say
"encoder % of a core" stands in), power (RAPL package energy if
exposed; wall power needs a meter the user does not have — ABSENT),
throttling (`cpufreq` current / max, thermal throttle counters). Build
one `tools/e1_sampler.py` from these at 1 s with a per-run summary
(mean, p95, max per metric; per-process rows for the companion, ffmpeg,
RetroArch, the EPG/metadata processes).

## 2. Pre-registration (`e1_preregistration.txt`, hashed, before any run)

- The suite: the runnable workload ids, each with its launch, warm-up
  (default 60 s, longer where the inventory says so — e.g. the stream's
  startup burst, P2a), steady-state window (**5 min** in E1; E2 may use
  20), and teardown to the idle state; the order; ≥ 2 min idle between
  workloads.
- **The repeatability bar**, per workload, over two runs of the same
  5-min window: host CPU mean within ± 2 points; GPU busy mean within ±
  3 points; RSS of the main process within ± 5 %; the workload's own
  key figure (the stream's rendered fps and loss/min; RetroArch's fps;
  VOD/Live TV's dropped frames or stalls; the scan's duration) within a
  band the inventory names per workload. **REPEATABLE** if every metric
  holds; otherwise the metric that did not, and the workload is marked
  NOT YET REPEATABLE with the suspected cause (the link's loss row is
  expected to fail the band for the streaming rows — say so up front:
  for those, loss is reported, not banded).
- Nothing is tuned between the two runs.

## 3. The runner and the dry runs (`tools/e1_suite.py`, `runs/`)

One command runs the whole suite or one workload id: warm-up, window,
teardown, the sampler, the workload's own telemetry, a `summary.json`
per run. Every workload twice, back to back with the idle gap, the
streaming rows through the companion's normal routes with the onn as the
client (the harness pieces from C5 — launch, PLAYING, BACK, teardown
checks, the APK hash — reused). The 1080p-rung row: flag set for that
row only, the entry injected after ≥ 60 s at PLAYING, confirmed
1920×1080, flag unset after. Live TV / VOD rows: driven as D5/D122 did.
Absent rows are skipped and listed.

## 4. The frozen suite and the record

- **`docs/memory/architecture/E1_WORKLOAD_SUITE.md`** — the frozen
  definition: each workload id, launch, fixture, warm-up, window,
  steady-state definition, teardown, the sampler set, the summary
  schema, the repeatability bar, the ABSENT rows and what would fill
  them. This is the document E2-E4 cite; it changes only by a dated
  amendment.
- **`evidence/E1_S1_WORKLOAD_SUITE_2026-10-0X.md`** and
  `e1_s1_<date>/` (inventory, pre-registration, both runs per workload,
  summaries, manifest, `--check`): the dry-run table (per workload: the
  two runs' key metrics side by side, REPEATABLE or not, why); the
  sampler coverage table (what E2 can and cannot measure on this host
  without new hardware); **the user's list**: NES / Genesis fixtures,
  a camera (yes/no), a power meter, which concurrency pairs matter to
  them, and whether the 1080p-rung row stays in the suite.
- `docs/ROADMAP.md` E1: status, the suite document named; E2 next.
  `investigations/ACTIVE.md` (a Phase E item); `evidence/RUNTIME_VALIDATION.md`;
  `TOOLS.md` (the runner and sampler); `handoffs/CURRENT_HANDOFF.md`
  (Phase E); `patches/` + `PATCH_INDEX.md`; the daily file;
  `check_memory_health.py`; the redactor `--check`; `git status --short`
  and `git diff --stat` to `logs/e1_s1_git_status.txt`; **`CURRENT.md`
  last** — Active Objective: Phase E, E1 in progress / frozen; Next
  Action 1: the user's commit; 2: the user's answers to the list; 3:
  E2 (whole-system measurements on the frozen suite, 20-min windows) on
  the user's word.

Adopted profile, source and APK throughout; flags absent at the end;
live default intact; no `nft`, no real `sudo`, the Opal read-only; the
adopted system untouched beyond running its own workloads; no
addresses, MACs, SSIDs, ADB endpoints, serials or credentials anywhere.
Nothing optimized. Nothing adopted. Nothing committed.
