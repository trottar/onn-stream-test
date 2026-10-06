---
memory_schema: 1
as_of: 2026-10-05
status: TASK HANDOFF — E2-S1 (the user's go, 2026-10-05): first, add the VOD row to the frozen suite by E1's own rule (the drive is now attached; inventory the path, two 5-min dry runs, REPEATABLE or not, a dated amendment to E1_WORKLOAD_SUITE.md); the 1080p-rung row stays (the user's call). Then E2 proper — the ROADMAP's whole-system measurement table on the frozen suite at 20-minute windows, one run per workload and two for the two contended rows (SNES-STREAM, CONC), with the finer instrumentation that localizes the EPG-grab contention for E3 — measurement only, no optimization, no hardware claim. Nothing adopted; nothing committed
---

# E2-S1 — whole-system measurements on the frozen suite

**Why.** E1 froze the suite (`architecture/E1_WORKLOAD_SUITE.md`; 6 of
7 repeatable). E2 (`docs/ROADMAP.md`) measures the whole system on it:
CPU total and per core, process CPU, working sets, swap, iGPU, the
video engine (VCN reads 0 here — encoder % of a core stands in),
encoder headroom, storage, network / FEC / decoder telemetry,
end-to-end latency (the C2 block; glass-to-glass ABSENT), temperatures
and throttling, power (socket W from the SMU; wall ABSENT), and
concurrency. **E1 already found the three things E3 will go after**:
EPG grabs wreck the stream (E1-CONC), bsnes costs four cores and the
stream drops below 59.5, and the companion grows 37 → 172 MB at the
first grab. E2's job is to measure them well enough that E3's
hypotheses are narrow, not to fix them. The user's answers: the VOD
drive is attached; the 1080p-rung row stays; NES / Genesis fixtures,
a camera, a power meter and Live TV's unattended start are still
absent (rows stay ABSENT).

Read first: `architecture/E1_WORKLOAD_SUITE.md`,
`evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md` (§2-§5),
`e1_s1_2026-10-05/e1_inventory.md`, `e1_preregistration.txt`,
`e1_s1_host_table.txt`, `e1_s1_conc_check.txt`, `tools/e1_suite.py`,
`tools/e1_sampler.py`; the VOD path: `D091_D5_LINUX_MEDIA_BASELINE_2026-09-16.md`,
`D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION_2026-09-16.md`,
`D094`/`D095` (the external drive's remount and identity),
`D-100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE.md`,
`D122`/`D136` (the automated media acceptance), `D5_TV_MEDIA_CLOSEOUT_2026-09-17.md`;
`TOOLS.md`; `CURRENT.md`.

## 1. The VOD row joins the suite by E1's rule (first)

- **Inventory** the VOD path as it stands: the drive is attached —
  confirm the `vod_root` mount and identity (D095's check), pick **one
  fixed file** (name it in the suite; the largest common container the
  library holds; ≥ 25 min long or looped), and say how the onn plays it
  (direct play from the companion's media route, or a host transcode —
  which process, which argv). What the host does per second of playback
  is the workload.
- **Pre-register** `E1-VOD` the same way as the others: launch through
  the companion's own route with the onn as the client (D122/D136's
  automation), warm-up 60 s, 5-min window, teardown; the key figure
  (the client's dropped frames or stalls per minute, or the companion's
  served bytes/s if the client reports nothing); the E1 bands verbatim.
- **Two dry runs**, compare; **REPEATABLE or NOT YET REPEATABLE**.
- **Amend `E1_WORKLOAD_SUITE.md`** with a dated section: E1-VOD added
  (or added as NOT YET REPEATABLE with the reason); the 1080p-rung row
  confirmed in the suite by the user 2026-10-05; the user's other
  answers recorded against the ABSENT rows.
- If the VOD path transcodes on the host, pre-register one more
  concurrency row **E1-CONC-VOD** (PS1 streaming + the VOD transcode
  running for a second session, if the companion can serve a transcode
  without a second client — otherwise ABSENT, say why) and dry-run it
  the same way.

## 2. Pre-registration for E2 (before any 20-min run)

`evidence/e2_s1_<date>/e2_preregistration.txt`, hashed:

- **The runs**: every suite row that is REPEATABLE (IDLE, PS1-LOCAL,
  SNES-STREAM, PS1-STREAM, PS1-1080P, META, VOD if it passed §1) at a
  **20-minute window** after E1's warm-ups, 2-min idle gaps, one run
  each; **two runs** for SNES-STREAM and CONC (the contended rows,
  NOT-YET-REPEATABLE CONC included — E2 measures it, the bar is E1's
  and is reported, not re-judged); the 1080p row with its flag for that
  row only, entry injected after ≥ 60 s, confirmed 1920×1080, flag
  unset after.
- **The table**, per row (the ROADMAP's E2 list, one column each; the
  sampler already gives most): CPU mean and p95 total; per-core p95 and
  **the busiest core's p95**; PSI cpu/io/mem; per-process CPU and PSS
  (companion, RetroArch/AppRun, encoder, the EPG child, Xorg,
  pulseaudio, other); swap in/out; GPU busy mean/p95; **encoder
  headroom** = the encoder's % of a core and the capture's dup+drop,
  plus the gap between RetroArch's fps and the rendered fps; disk
  write kB/s and await; `eno1` tx/rx and the qdisc/softnet drop
  counters; the C2 latency block (`receive_to_decode_ms`,
  `output_gap_ms`) and the decoder report rows (spikes, fps, stale,
  loss, underruns, max gap, resyncs); Tctl and core max, cpufreq
  mean, `throttle_status` counts by value; socket / CPU / SoC W. Wall
  power and glass-to-glass ABSENT, said in the table.
- **The CONC instrumentation** (measurement, no change to anything):
  1-s per-thread CPU of the companion (the relay, audio, status and
  HTTP threads by name), the encoder process and the grab child,
  aligned on the grab bodies (start/end from `epg.jsonl`); per-CPU
  utilization at 1 s in the same frame; the encoder's capture fps and
  dup/drop per second; `eno1` tx bytes and tx drops per second; the
  grabber's own rx bytes; the controller's decision rows. The analysis
  asks one question, pre-registered: **during grab bodies, which rises
  first and most — the busiest core's utilization, the encoder's
  dup/drop, the relay thread's CPU, or `eno1` drops** — and reports the
  answer as the narrow hypothesis for E3, not as a fix.
- **The SNES instrumentation**: the same per-thread view for bsnes
  (its thread count and the busiest threads), the capture's fps and
  dup/drop against RetroArch's, and the stream's rendered fps per
  minute — so E3 can tell "the emulator starves the encoder" from "the
  encoder starves the emulator".
- **The companion's memory**: PSS per minute across META and CONC with
  `smaps_rollup` deltas by mapping class (anon vs file) at the first
  grab and at the end; the Node child's PSS likewise.

## 3. The runs

`tools/e1_suite.py` extended (`--window 1200`, `--threads`, the
alignment hooks), the pre-registration hash checked by the runner.
Every teardown as E1: flags absent, the APK confirmed, no game, the
adopted PS1 files byte-identical, idle restored. The order: IDLE,
PS1-LOCAL, PS1-STREAM, PS1-1080P, META, VOD, SNES-STREAM ×2, CONC ×2
(the contended rows last, with the longest idle gap before them).

## 4. The record

`evidence/E2_S1_WHOLE_SYSTEM_2026-10-0X.md` + `e2_s1_<date>/`
(pre-registration, every run, summaries, the aligned CONC and SNES
frames, manifest, `--check`):

- **the E2 table**, every row, with the E1 5-min means beside the 20-min
  ones (drift between windows is itself a finding);
- **the known-good reference, stated**: this host (the EliteDesk,
  4650G/16 GB) at each workload — the numbers E4 will call the
  reference, no floor and no lower-tier claim;
- **the CONC answer** to the pre-registered question, with the aligned
  plot data in a table (no picture needed), and the narrow hypothesis
  for E3 in one sentence;
- **the SNES finding** likewise;
- **the memory finding** likewise;
- what E2 could not measure and why (VCN, RAPL, wall power,
  glass-to-glass, NES/Genesis, Live TV, camera);
- **the ordered E3 candidate list**, by expected user impact and
  measured size, each with the one metric that would show it worked
  and the suite row that would measure it — a proposal, the user
  chooses.

`docs/ROADMAP.md` E2 status (and E1's amendment); `investigations/ACTIVE.md`;
`evidence/RUNTIME_VALIDATION.md`; `TOOLS.md`; `handoffs/CURRENT_HANDOFF.md`;
`patches/` + `PATCH_INDEX.md`; the daily file; `check_memory_health.py`;
the redactor `--check`; `git status --short` and `git diff --stat` to
`logs/e2_s1_git_status.txt`; **`CURRENT.md` last** — Next Action 1: the
user's commit; 2: the user picks the first E3 optimization from the
list; 3: E3's loop on that one (measured bottleneck → one change →
fresh benchmark on the suite → accept/reject), on the user's word.

Adopted profile, source and APK throughout; flags absent at the end;
live default intact; the adopted system untouched beyond running its
own workloads (the VOD drive read only); no `nft`, no real `sudo`, the
Opal read-only; no addresses, MACs, SSIDs, ADB endpoints, serials or
credentials anywhere. Nothing optimized. Nothing adopted. Nothing
committed.
