---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: a56746e
---

# E2-S1 — whole-system measurements on the frozen suite (and the VOD row)

**Classification:**

- **E1-VOD added to the suite: REPEATABLE** (amendment of 2026-10-05).
- **E2 MEASURED**: 10 runs × 20 min, all OK, 0 missed samples, `--check`
  OK. The three pre-registered questions are answered (§3-§5) and the E3
  candidate list is ordered (§7).
- Measurement only. Nothing optimized, adopted or committed. No hardware
  claim.

**Context:**

- Task: `handoffs/E2-S1_WHOLE_SYSTEM_MEASUREMENTS_TASK.md`, under
  `handoffs/QUEUE_2026-09-29B.md`'s rules.
- The user's answers: the VOD drive is attached; the 1080p-rung row
  stays.
- Files: `e2_s1_2026-10-05/`.
- **Timeline (UTC):**

  | date | time | what |
  | --- | --- | --- |
  | 10-05 | 15:00-15:20 | VOD inventory |
  | 10-05 | 15:18:51 | VOD pre-registration hashed |
  | 10-05 | 15:28-15:47 | VOD dry runs |
  | 10-05 | 15:47-22:14 | **an idle stretch of ~6.5 h**: my mistake, a missed completion notice; nothing ran |
  | 10-05 | 22:18:00 | E2 pre-registration hashed |
  | 10-05 | 22:22:15 | amendment A1 hashed (before any run) |
  | 10-05 → 10-06 | 22:22:15-02:34:11 | **the E2 runs** |

## 1. The VOD row (E2-S1 §1)

**Inventory** (`vod/e1_vod_inventory.md`):

- The drive is a 1.8 TB USB disk with one exFAT partition, mounted
  **read-only** through autofs.
- The library is 91 files, all `.mp4` H.264. They are typically 720×360
  at ~0.92 Mbps; two are 1080p.
- **Direct play**: the app posts `POST /sources/<id>/start`, then
  ExoPlayer plays `range_server.py` HTTP range requests.
  - **No host transcode exists, so E1-CONC-VOD is ABSENT.**
- The fixed file is `movies/Edge Of Tomorrow.mp4` (720×360, 918 kbps,
  1:53:29).
- **Driven unattended** by launcher taps:
  - VOD → MOVIES → the title;
  - "Start Over" if the resume dialog shows;
  - RESTART, so every run starts at 0:00;
  - fullscreen;
  - BACK and the progress text at the window's end;
  - RESTART + STOP as the teardown, which leaves the onn's resume point
    at ~0.

**The two 5-min dry runs** (pre-registered `vod/e1_vod_preregistration.txt`):

| metric | run 1 | run 2 | band | holds |
| --- | --- | --- | --- | --- |
| host CPU % | 0.80 | 0.85 | ± 2 points | ✓ |
| GPU busy % | 0 | 0 | ± 3 points | ✓ |
| range_server RSS | 24.60 MB | 24.61 MB | ± 5 % | ✓ |
| **progress ratio** | 0.998 | 1.001 | ± 0.01 | ✓ |
| stall s/min (reported) | 0.13 | 0 | — | — |
| served kB/s (reported) | 78.5 | 79.8 | — | — |

- **REPEATABLE.**
- Served kB/s is the server's file reads (`rchar`). Its socket `send()`
  is not counted in `wchar`, which the pre-registration named; disclosed,
  as it is a reported figure.

**The amendment:** `architecture/E1_WORKLOAD_SUITE.md`, "2026-10-05 —
E2-S1 §1". E1-VOD is added; the 1080p-rung row is kept by the user; the
user's answers are recorded against the ABSENT rows.

**Found in the inventory:** a stream opened straight after VOD playback
without a unit restart rendered ~2 fps and never reached PLAYING. It
played normally after a restart, and every suite run restarts first.
Recorded, not chased.

## 2. The E2 table

The pre-registration is `e2_preregistration.txt`.

- v1 was hashed at 22:18:00Z.
- **Amendment A1** was hashed at 22:22:15Z, before any run. It fixed the
  relay-thread identification rule after the runner smoke showed the
  first rule was ambiguous.

The runs, in pre-registered order, with 120-s gaps (600 s before the
SNES pair):

| row | runs |
| --- | --- |
| IDLE | 1 |
| PS1-LOCAL | 1 |
| PS1-STREAM | 1 |
| PS1-1080P | 1 |
| META | 1 |
| VOD | 1 |
| SNES-STREAM | 2 |
| CONC | 2 |

The VOD run's first attempt did not find the VOD tile (the launcher
loaded slowly); its retry ran normally.

The full table, every metric of the pre-registration with E1's 5-min
means beside it, is `e2_s1_2026-10-05/e2_table.md` (from
`e2_analysis.py`). The headline rows (20-min window means unless noted;
E1's 5-min mean in brackets):

| | IDLE | PS1-LOCAL | PS1-STREAM | PS1-1080P | META | VOD | SNES r1 / r2 | CONC r1 / r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| host CPU mean % | 0.89 [0.82] | 5.0 [5.0] | 11.7 [10.9] | 13.8 [15.4] | 9.8 [10.2] | 0.83 [0.82] | 43.4 / **50.0** [41.7] | 20.5 / 21.9 [22.2] |
| busiest core p95 % | 3 | 24.5 | 28.7 | 28.3 | 46.9 | 3 | 54.7 / 62.5 | 63.4 / 65.7 |
| busiest-core-per-second p95 % | 4 | 38 | 38.5 | 38.2 | **96** | 4 | 57.7 / 62.9 | **97 / 96** |
| PSI cpu some ms/s | 1.4 | 2.0 | 10.1 | 13.5 | 1.8 | 1.1 | 45 / **103** | 11.4 / 13.9 |
| companion CPU % / PSS MB | 0.0 / 26 | 0.1 / 28 | 24.3 / 38 | 29.8 / 39 | 7.6 / **150** | 0.0 / 26 | 24.9 / 39, 24.4 / 39 | 33.1 / **170**, 33.5 / **195** |
| RetroArch CPU % / PSS MB | — | 33 / 251 | 34 / 231 | 23 / 242 | — | — | **436 / 241, 517 / 241** | 36 / 231, 38 / 232 |
| encoder CPU % / PSS MB | — | — | 36 / 72 | 74 / 75 | — | — | 28 / 66, 21 / 67 | 36 / 72, 38 / 72 |
| EPG child CPU % / PSS MB | — | — | — | — | 67 / 486 | — | — | 79 / 484, 82 / 478 |
| GPU busy mean % | 0 | 17.8 | 22.2 | 19.6 | 0 | 0 | 8.0 / 7.0 | 23.6 / 21.7 |
| encoder capture fps, dup+drop / min | — | — | 60.0, 0.1 | 60.0, 0.1 | — | — | 60.0, 0.1 | 60.0, 0.1 |
| RetroArch / rendered fps | — / — | 60.0 / — | 60.0 / 59.81 [59.92] | 60.0 / 59.87 [59.91] | — | — | 60.0 / 59.66, 60.0 / 59.98 [58.69] | 60.0 / **56.53, 56.57** [54.43] |
| video loss/min (window) | — | — | 32 [31] | 23 [10] | — | — | 49 / 2.5 [44] | **1,622 / 1,602** [2,569] |
| resyncs, audio underruns (window) | — | — | 0, 11 | 0, 20 | — | — | 0, 7; 0, 15 | **199, 448; 204, 312** |
| spikes ≥ 20 ms / min (report, session) | — | — | 60 | **499** | — | — | 39 / 40 | 69 / 77 |
| C2 receive→decode ms median; max output gap ms | — | — | 9; 280 | 13; 66 | — | — | 9; 74 / 65 | 9; 473 / 421 |
| eno1 tx kB/s; host tx drops / s | 3; 0 | 2; 0 | 1,453; 0 | 2,260; 0 | 5; 0 | 127; 0 | 1,451; 0 | 1,422; **0** |
| disk write kB/s; await ms | 21; 0.66 | 26; 0.65 | 82; 0.26 | 85; 0.39 | 77; 0.42 | 21; 0.54 | 82 / 81; 0.38 | 111; 0.23 / 0.37 |
| Tctl mean / core max °C | 33 / 38 | 50 / 60 | 60 / 65 | 62 / 71 | 59 / 68 | 34 / 37 | 59 / 69, 61 / 69 | **70 / 78**, 70 / 77 |
| `throttle_status` (0x800 EDC_CPU, samples) | 0 | 0 | 33 | 52 | 2 | 0 | 1 / 0 | 35 / 74 |
| socket / CPU / SoC W | 4.7 / 1.5 / 1.5 | 13.2 / 6.2 / 4.9 | 20.4 / 11.3 / 6.3 | 20.6 / 12.2 / 5.9 | 14.9 / 10.2 / 2.4 | 4.9 / 1.6 / 1.5 | 21.7 / 14.8 / 4.6, 21.2 / 14.3 / 4.6 | 25.9 / 16.4 / 6.7, 25.3 / 16.4 / 6.2 |
| VOD progress ratio; served kB/s | — | — | — | — | — | 1.000; 119 | — | — |
| EPG grabs ok/failed; median s | — | — | — | — | 228/0; 5.2 | — | — | 208/0; 5.9, 214/0; 5.8 |

- **Swap** stays ≤ 0.02 page/s in and 0 out; memory PSI is 0 in every
  row.
- **ABSENT, stated in the table:**
  - wall power (no meter);
  - glass-to-glass latency (no camera);
  - VCN duty (reads ~0);
  - RAPL (root-only).
- **The encoder's dup+drop** is 2 duplicated frames per 20 min in every
  stream row (the cumulative counter goes 0 → 1 → 2), i.e. ~0.1 per
  minute: capture holds 60.0 everywhere.

**Drift, 5-min vs 20-min, is itself a finding:**

- **SNES-STREAM is NOT YET REPEATABLE at 20 min.** Host CPU was 43.4 vs
  50.0 against the ± 2-point bar, because bsnes went from 436 to 517 % of
  a core between runs. Its rendered fps recovered from E1's 58.5-58.9 to
  59.66 / 59.98: run 1's first 4 minutes were at 59.0-59.2 with loss
  49/min, then settled.
- **E1-CONC at 20 min holds E1's bar**: rendered 56.53 / 56.57, host CPU
  20.5 / 21.9, grabs 5.88 / 5.82 s. This is reported, not re-judged; E1's
  status stands. It is less degraded than at 5 min (loss ~1,600 vs
  ~2,570 per min) but still ~50× PS1-STREAM's loss.
- **PS1-1080P**: the onn's known 1080p decode jitter shows as 499
  spikes ≥ 20 ms per min (PS1 at 720p: 60).

## 3. The CONC answer (pre-registered §3)

`e2_s1_2026-10-05/e2_conc.md` has the aligned tables. The relay thread
was identified by A1's rule in the baseline and both CONC runs (one
candidate each).

**Pre-registered question:** during grab bodies, which rises first and
most?

**Answer: the busiest core's utilization, in both runs. It rises first
(offset 0 s) and most (+5.2 baseline sd).** None of the other signals
crosses its threshold at any offset:

- the encoder's dup+drop: 0, never;
- the relay thread's CPU: +0.5 to +0.8 sd;
- `eno1`'s transmit drops (qdisc, softnet and the interface): **0, never**.

| per-second, mean across ~210 grabs per run | 0 s | 1 s | 2 s | 3 s | 4 s | 5 s | 6-10 s | baseline (PS1-STREAM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % (run 1) | 40 | 57 | **78** | 60 | 52 | 54 | 30-34 | 26.8 (sd 5.4) |
| busiest core % (run 2) | 45 | 67 | **73** | 49 | 57 | 44 | 24-45 | |
| lost packets / s (run 1) | 34 | **65** | 43 | 6 | 10 | 7 | 19-23 | 0.55 |
| lost packets / s (run 2) | 35 | **61** | 39 | 9 | 9 | 8 | 21-32 | |
| relay thread CPU % (run 1) | 7.7 | 8.2 | 8.9 | 8.8 | 8.5 | 8.4 | 7.5-8.0 | 7.8 (sd 0.9) |
| eno1 tx drops / s | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- The stream's loss peaks at 1 s, with the busiest core peaking at 1-2 s:
  the start-up of each grab (npm, then node).
- The packets leave the host without a host-side drop.
- The relay thread's per-second CPU barely moves.

**The narrow hypothesis for E3, in one sentence:** each grab's start-up
burst saturates one core for ~1-3 s; that delays the stream's send-side
threads at sub-second scale (not visible as more CPU, nor as host drops),
and the resulting send bursts are lost on the wireless hop — so lowering
the grabber's CPU priority, or keeping it off the stream threads' cores,
or deferring grabs while a stream is live, should bring E1-CONC's loss
back toward E1-PS1-STREAM's.

## 4. The SNES answer (pre-registered §4)

`e2_s1_2026-10-05/e2_snes.md`.

**The measurements:**

- RetroArch: 59.99 / 60.00 fps.
- Capture: 60.02 / 60.00 fps, with 2 duplicated frames per 20 min.
- Rendered: 59.66 / 59.98 fps.
- bsnes runs 27 threads. **About ten are busy at ~37-44 % of a core
  each**, many in `running` state. RetroArch's total is 436 / 517 % of a
  core.
- Busiest core p95 55 / 63 %; PSI cpu 45 / 103 ms/s.
- The encoder used 28 / 21 % of a core.

**The pre-registered reading:**

- The analysis code returns "the emulator's load starves the
  capture/encoder" because dup+drop > 0.
- The pre-registered text says "dup/drop **rising**". Two duplicated
  frames in 20 min, with capture at 60.0, is not rising.
- Read by the text:
  - RetroArch ≥ 59.9;
  - capture ≥ 59.5;
  - rendered ≥ 59.5 in both runs;
  - so **none of the three readings applies.**
- I report both and take the text's reading.

**The finding:** at 20 min neither the emulator nor the encoder starves
the other.

- bsnes is expensive and variable: +81 points of a core run to run, which
  is why the row is NOT YET REPEATABLE.
- It leaves headroom: no core is saturated, and capture holds 60.
- E1's 58.5-58.9 rendered fps was an early-session effect (run 1's first
  minutes) plus link loss.

**Narrow hypothesis for E3:** the SNES cost is the bsnes core's own
multi-threaded (and partly spinning) work. A lighter core is the
candidate; that is a fidelity choice for the user. The stream itself
needs no fix here.

## 5. The memory answer (pre-registered §5)

`e2_s1_2026-10-05/e2_memory.md`.

| run | companion PSS before → after the first grab (MB) | window end (MB) | growth | last 15 min | node child PSS peak per grab |
| --- | --- | --- | --- | --- | --- |
| META | 26.3 → 132.9 | 161.0 | **100 % anon** | +22 %: **keeps growing** (a +20 MB step at ~10 min) | 659 → 635 MB |
| CONC r1 | 34.7 → 142.6 | 158.3 | 100 % anon | −9 %: plateaus | 649 → 634 MB |
| CONC r2 | 53.7 → 167.2 | 199.6 | 100 % anon | 0 %: plateaus | 652 → 635 MB |

**Answer:**

- **The first grab adds ~106-114 MB of anonymous memory to the companion
  (file-backed unchanged).**
- After that the PSS moves in steps, not a steady climb:
  - META "keeps growing" by the rule (one +20 MB step);
  - both CONC runs plateau;
  - CONC run 2 ended near 200 MB.
- The Node grabber peaks at ~635-660 MB PSS per grab, ~480 MB mean.

**Narrow hypothesis for E3:** the companion keeps (or fragments) the
parsed guide data in-process after each grab. Either the guide parse's
retention or the allocator's high-water mark explains the ~110 MB anon
step. A test is to measure PSS after META with the parse moved out of
process or the result trimmed. That is E3's to choose.

## 6. The known-good reference — this host

The HP EliteDesk, Ryzen 5 PRO 4650G, 16 GB (14 GiB visible), NVMe,
wired to the Opal. Each row is a 20-min window mean on the adopted
system; these are the numbers E4 calls "the reference". **No floor and no
lower-tier claim.**

| workload | host CPU % (p95) | busiest core p95 % | PrivyHub CPU (% of one core) | PrivyHub PSS | socket W | Tctl °C | stream |
| --- | --- | --- | --- | --- | --- | --- | --- |
| idle | 0.9 (1.3) | 3 | ~0 | companion 26 MB + range server 14 MB | 4.7 | 33 | — |
| PS1 local (4x source) | 5.0 (6.5) | 24.5 | RetroArch 33 | RetroArch 251 MB | 13.2 | 50 | — |
| PS1 streamed, 720p/7000 | 11.7 (13.5) | 28.7 | RetroArch 34 + encoder 36 + companion 24 | 231 + 72 + 38 MB | 20.4 | 60 | 59.8 fps, 1.45 MB/s |
| PS1 streamed, 1080p rung | 13.8 (16.7) | 28.3 | RetroArch 23 + encoder 74 + companion 30 | 242 + 75 + 39 MB | 20.6 | 62 | 59.9 fps, 2.26 MB/s |
| EPG grab cycle | 9.8 (16.5) | 46.9 | node 67 + companion 8 | node 486 + companion 150 MB | 14.9 | 59 | — |
| VOD direct play | 0.8 (1.2) | 3 | range server ~0 | 16 MB | 4.9 | 34 | ratio 1.000, 119 kB/s |
| SNES streamed (bsnes) | 43-50 (50-53) | 55-63 | RetroArch 436-517 + encoder 21-28 + companion 24 | 241 + 66 + 39 MB | 21.2-21.7 | 59-61 | 59.7-60.0 fps |
| PS1 stream + EPG | 20.5-21.9 (28-29) | 63-66 | RetroArch 37 + encoder 37 + companion 33 + node 80 | 231 + 72 + 170-195 + 480 MB | 25.3-25.9 | 70 | **56.5 fps, loss ~1,600/min** |

**The companion's stream cost by thread** (inferred roles, PS1-STREAM):

| thread | % of a core |
| --- | --- |
| audio sender (SCHED_RR) | 12.9 |
| FEC relay | 7.8 |
| the other poll thread | 3.0 |
| audio reader | 0.1 |

## 7. What E2 could not measure

| item | why |
| --- | --- |
| VCN duty | `gpu_metrics` reads ~0 while encoding |
| package energy | RAPL is root-only; no `sudo` |
| wall / idle power | no meter |
| glass-to-glass latency | no camera |
| NES and Genesis | no fixtures |
| Live TV | no unattended channel start |
| camera and browser sources | Windows-only; no camera |
| a VOD transcode | none exists |
| the companion's thread names | Python 3.13 sets none, and no ptrace tool is installed, so roles are inferred (A1) |
| sub-second send timing | the 1-s sampler cannot see it; that is the CONC hypothesis's gap |

## 8. The ordered E3 candidate list (a proposal; the user chooses)

Ordered by expected user impact, then measured size.

1. **EPG grabs vs a live stream.**
   - Measured: loss 1,600-2,800/min against ~30, rendered 54-56.5 fps,
     ~200 resyncs per 20 min, audio underruns ×30.
   - Change: the grabber at the lowest CPU priority or off the stream's
     cores, or grabs deferred while a stream is live.
   - **Metric:** E1-CONC video loss/min and rendered fps, back toward
     E1-PS1-STREAM's (≤ ~50/min, ≥ 59.5).
   - **Row:** E1-CONC (with E1-PS1-STREAM as the control).
2. **The companion's memory after a grab.**
   - Measured: +106-114 MB anon at the first grab, steps to 160-200 MB.
   - Change: the retention of the parsed guide.
   - **Metric:** companion PSS at the end of E1-META, toward its
     pre-grab ~26-35 MB.
   - **Row:** E1-META (and E1-CONC).
3. **The EPG grabber's own cost.**
   - Measured: node 67-82 % of a core and ~480 MB mean / ~650 MB peak
     PSS per grab; `npm run` per channel.
   - Change: batching channels per grab, or a lighter invocation.
   - **Metric:** epg CPU-seconds and peak PSS per grab, at the same grabs
     ok/failed.
   - **Row:** E1-META.
4. **The SNES core's cost.**
   - Measured: bsnes 4.4-5.2 cores, host CPU 43-50 %, PSI 45-103 ms/s,
     not repeatable run to run.
   - Change: a lighter SNES core is a fidelity choice for the user.
   - **Metric:** RetroArch CPU and host CPU on E1-SNES-STREAM at 60 fps
     and rendered ≥ 59.5.
   - **Row:** E1-SNES-STREAM.
5. **Streaming's fixed cost.**
   - Measured: companion 24-30 % of a core (audio sender 13 %, relay 8 %);
     encoder 36 % at 720p (x11grab copy plus scale); Xorg 10 %.
   - Change: the audio sender's loop; avoidable copies in capture.
   - **Metric:** companion CPU and encoder CPU on E1-PS1-STREAM, at
     rendered ≥ 59.5 and loss unchanged.
   - **Row:** E1-PS1-STREAM.
6. **Not for E3:**
   - idle, where PrivyHub is ~0 and non-PrivyHub residents dominate (a
     measurement-hygiene note for E4);
   - VOD (~0);
   - the 1080p rung's decode jitter (client-side, not adopted).

## 9. State at the end; files

**Final state** (`runs/final_state.json`, 02:34:11Z):

- manager `PRIVYHUB_*` none;
- environ exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`;
- no game; no RetroArch or encoder process;
- **the adopted PS1 files byte-identical**;
- **APK `de072762…835e` CONFIRMED**;
- **flags absent**.

Every teardown was clean. The 1080p row's flags were set for that row
only (entry at 75 s; 1920×1080 the whole window) and unset after. The VOD
drive was only read. No `nft`, no `sudo`, the Opal untouched. The onn's
resume point for the fixed film is ~0, and no CONTINUE WATCHING entry is
left.

**Files** (`e2_s1_2026-10-05/`, 96 MB):

- the E2 pre-registration: `e2_preregistration.txt`, `.sha256` and
  `_v1.sha256`;
- `runs/` (10 runs, `manifest.sha256`, `--check` OK; `repeatability.md`
  is E1's bar on the two-run rows);
- `runs_smoke/` (not data);
- `e2_analysis.py` and its outputs: `e2_table.md`, `e2_conc.md`,
  `e2_snes.md`, `e2_memory.md`, `e2_analysis.json`;
- `vod/` (inventory, pre-registration, `runs/`, `runs_smoke/`);
- `redact_check.txt`.

**Tools extended:**

- `tools/e1_sampler.py --e2`: per-thread rows, the encoder's progress
  records, tx drops, rchar/wchar, PSS by class, the summary's per-core
  p95 / throttle values / thread table.
- `tools/e1_suite.py`: `--e2`, `--plan ID:runs:first_gap`, the E1-VOD
  row, the decision-log slice, the decoder report's paths.
