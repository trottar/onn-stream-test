---
memory_schema: 1
as_of: 2026-10-05
baseline_commit: f60234e
---

# E1-S1 — the workload suite frozen (Phase E's first task)

**Classification:**

- **E1 FROZEN**
  (`architecture/E1_WORKLOAD_SUITE.md`).
- **6 of 7 runnable workloads REPEATABLE** against the pre-registered
  bar.
- **E1-CONC is NOT YET REPEATABLE**: its rendered fps differs by
  1.03 fps. The stream degrades heavily while EPG grabs run.
- **7 rows ABSENT** and listed for the user.

Nothing optimized, adopted or committed.

**Context:**

- Task: `handoffs/E1-S1_WORKLOAD_SUITE_FREEZE_TASK.md`, under
  `handoffs/QUEUE_2026-09-29B.md`'s rules.
- The user's go, 2026-10-05: "let's start E1".
- Run unattended on 2026-10-05:
  - inventory 06:10-06:45Z;
  - pre-registration hashed 06:22:52Z;
  - runner smoke 06:26-06:35Z (not data);
  - **the suite 06:35:54-08:40:55Z**.
- Files: `e1_s1_2026-10-05/`.

## 1. What was done

1. **Inventory** (`e1_s1_2026-10-05/e1_inventory.md`), before any run:
   one row per ROADMAP E1 workload, plus the samplers.
2. **Pre-registration** (`e1_preregistration.txt`, SHA-256 `244c203f…e910`
   in `e1_preregistration.sha256`, 06:22:52Z):
   - the suite;
   - warm-ups and the 300-s window;
   - the 120-s idle gap;
   - the order;
   - the repeatability bar;
   - stream loss reported but not banded, said up front.
3. **Built:**
   - `tools/e1_sampler.py`: the 1-s sampler set and the per-run summary.
   - `tools/e1_suite.py`: the one-command runner, `compare`, `manifest`,
     `--check`. It refuses to run without a matching pre-registration
     hash.
   - Self-tests pass (`E1_SAMPLER_SELF_TEST_OK`, `E1_SUITE_SELF_TEST_OK`).
4. **Runner smoke** (`runs_smoke/`): 20-s windows on IDLE, PS1-LOCAL,
   PS1-1080P and META. **Not data.** It found three sampler defects, all
   fixed **before the real runs**:
   - RetroArch's working process is the AppImage's `AppRun`, so it was
     counted as "other";
   - the per-pid class cache did not re-key when `comm` changes on exec;
   - `gpu_metrics` activities are in hundredths of a percent.

   It also fixed the title-counter regex, which missed the double space
   in `FPS:  60.04`.
   - None of these touch a pre-registered rule, band or workload
     definition.
   - The fixes are visible in the smoke data (RetroArch 0 %, `AppRun`
     ~30 % in `other`).
5. **The suite**: 7 workloads, 2 runs each, 14 runs.
   - Every run is OK at the first attempt. Stream opens took one retry in
     SNES run 1, as C5's harness allows.
   - **0 missed samples** in every window.
   - `--check`: see §6.

## 2. The dry-run table

Run 1 / run 2, window means; "holds" applies the pre-registered band
(from `runs/repeatability.md`).

| workload | host CPU % (±2) | GPU busy % (±3) | main RSS (±5 %) | key figure (band) | reported, not banded | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **E1-IDLE** | 0.83 / 0.81 ✓ | 0.0 / 0.0 ✓ | companion 37.5 / 37.2 MB ✓ | — | — | **REPEATABLE** |
| **E1-PS1-LOCAL** | 4.95 / 4.96 ✓ | 18.65 / 18.69 ✓ | RetroArch 235.0 / 234.7 MB ✓ | RetroArch 59.999 / 59.999 fps ✓ | — | **REPEATABLE** |
| **E1-SNES-STREAM** | 42.33 / 40.97 ✓ | 8.01 / 8.99 ✓ | RetroArch 281.3 / 281.4 MB ✓ | RetroArch 59.992 / 59.999 ✓; rendered 58.47 / 58.91 ✓ | loss 75.4 / 12.3 /min; underruns 0 / 3; max gap 79 / 46 ms | **REPEATABLE** |
| **E1-PS1-STREAM** (= 720p60 reference) | 11.22 / 10.58 ✓ | 23.06 / 21.42 ✓ | RetroArch 242.0 / 242.3 MB ✓ | RetroArch 59.999 / 59.998 ✓; rendered 59.96 / 59.88 ✓ | loss 8.5 / 54.1 /min; underruns 9 / 8; max gap 26 / 71 ms | **REPEATABLE** |
| **E1-PS1-1080P** | 15.76 / 15.05 ✓ | 23.97 / 24.16 ✓ | RetroArch 255.2 / 253.9 MB ✓ | RetroArch 59.999 / 59.999 ✓; rendered 59.89 / 59.93 ✓; at 1920×1080 1.00 / 1.00 ✓ | loss 8.3 / 11.4 /min; underruns 10 / 4; max gap 60 / 56 ms | **REPEATABLE** |
| **E1-META** | 10.03 / 10.40 ✓ | 0.0 / 0.0 ✓ | companion 172.2 / 173.2 MB ✓ | median grab 5.19 / 5.13 s ✓ | grabs 58/0 and 61/0 (ok/failed); library scan 25 ms | **REPEATABLE** |
| **E1-CONC** | 21.98 / 22.44 ✓ | 23.92 / 24.59 ✓ | RetroArch 242.9 / 242.0 MB ✓ | RetroArch 60.000 / 59.999 ✓; **rendered 53.91 / 54.95 ✗**; median grab 5.93 / 5.91 s ✓ | **loss 2,827 / 2,311 /min**; **underruns 141 / 144**; resyncs 45 / 38; max gap 170 / 376 ms; ladder 5500-7000 | **NOT YET REPEATABLE** |

The full metric table (power, temperatures, PSS, disk, net, per process)
is `e1_s1_2026-10-05/e1_s1_host_table.txt` (`e1_s1_table.py`).

**Why E1-CONC fails the band (suspected; not investigated in E1):**

- The stream degrades under the grab cycle:
  - post-FEC loss went from ~8-54/min to ~2,300-2,800/min;
  - 38-45 resyncs in 5 min;
  - the live controller stepped the ladder down to 5500;
  - rendered fps fell to ~54.
- With that much loss, the two runs' fps differ by more than 0.5.
- **The loss sits across each grab's body, not at its end**
  (`e1_s1_conc_check.txt`). Mean lost packets per 2-s interval:
  - run 1: 105 earlier in the grab, against 63 in its last 1.5 s;
  - run 2: 89 earlier, against 47 at the end.
- So the suspect is **the Node grabber child while it runs**, not the
  companion's handling after it exits. The child uses ~83 % of a core;
  the busiest logical CPU's p95 reaches 97-98 % (94 % in E1-META alone).
- The mechanism is untested, for E2:
  - scheduling contention with the encoder or the companion's relay and
    audio threads;
  - or the grabber's network activity on `eno1`.
- **This is the first concurrency finding of Phase E, not a defect of the
  suite.** The row stays in the suite as defined. The bar is unchanged.

## 3. Other findings (recorded, not acted on)

**SNES costs far more than PS1:**

- bsnes RetroArch: **~420 % of one core** (4.2 cores), against PS1's ~35 %.
- Host CPU 41-42 %; CPU PSI "some" 47 ms/s.
- **The stream rendered 58.5-58.9 fps while RetroArch made 59.99**, below
  D-BASE's ≥ 59.5 target. Frames are lost between RetroArch and the onn.
  The suspect is capture and encode under CPU contention: the encoder
  used 20-26 % of a core, against PS1's 36 %.
- bsnes is the installed SNES core. Whether a lighter core belongs in E3
  is a later question.

**Idle is almost all non-PrivyHub:**

- Host CPU 0.8 %, of which the `other` row is ~9 % of a core
  (≈ 0.76 points): resident Claude processes, the desktop app, a VPN
  daemon.
- The companion is at 0.0 % and 27 MB PSS.
- Socket power is 3.7-4.6 W.

**PS1 local vs streamed (the adopted 4x source):**

- RetroArch ~34-37 % of a core and GPU busy ~19-23 % in both.
- Streaming adds:
  - the encoder: 36 % of a core at 720p, 74-80 % at the 1080p rung;
  - the companion: 25 % at 720p, 30-31 % at the rung;
  - Xorg: 5 → 10 %.
- **Socket power:**

  | row | socket power |
  | --- | --- |
  | idle | 4 W |
  | PS1 local | 13 W |
  | PS1 streamed, 720p | 18.5-20.5 W |
  | PS1 streamed, 1080p | 23-27.5 W |
  | concurrent | 27-28 W |

- **Wire rate:** 1.45 MB/s tx at 720p; 2.26 MB/s at the rung.

**The EPG grab:**

- The Node child: ~72 % of a core, ~490 MB PSS.
- The companion's RSS jumps from 37 MB to ~172 MB at the first grab and
  stays there for the rest of the run (CONC: 182 → 211 MB, still
  growing). Where it comes from is for E2 (a candidate for E3's
  memory-footprint item).
- Median grab 5.1-5.9 s, no failures, ~100 kB/s rx.
- The library scan takes 25-34 ms.

**Throttling:**

- `throttle_status` was nonzero only as `0x800` (bit 11, EDC_CPU in the
  SMU12 throttler map: a current-limit flag, not thermal).
- It appeared in up to 42 of a window's 300 samples (PS1-1080P run 2; 45
  over the whole run), in the other stream / concurrent rows, and twice in
  META run 2. It did not appear at idle or PS1 local.
- Tctl ≤ 67 °C.
- No frame-rate effect was visible: RetroArch held 60 in every row.

**VCN:** `gpu_metrics` `average_mm_activity` reads 0.0 at 1 s in every row
(0.5 in CONC) while `h264_vaapi` encodes. It is exposed but does not
measure the engine's duty here, so **encoder % of a core stands in** (as
the task allowed).

**Memory and storage:**

- Swap is constant at 1,027 MB (paged out long before E1; swap-in and
  swap-out ≤ 1 page/s in every window).
- Disk writes are 15-99 kB/s, await 0.3-0.7 ms.
- No row is storage-bound on this NVMe.

**The sampler's own cost:**

- 12-35 ms per 1-s sample.
- Its process row is 1.1-3.5 % of a core, recorded in every run.

## 4. Sampler coverage — what E2 can measure on this host without new hardware

| E2 metric | measurable here | how |
| --- | --- | --- |
| total / per-core CPU, process CPU | **yes** | `/proc/stat`, `/proc/<pid>/stat` |
| RAM / working sets | **yes** | PSS (`smaps_rollup`; Xorg RSS only, root) |
| swap | **yes** | meminfo / vmstat |
| pressure | **yes** | PSI cpu / io / memory |
| iGPU / render | **yes** | `gpu_busy_percent`, gfx activity |
| hardware video engine | **no usable duty** | VCN activity reads ~0; encoder % of a core stands in |
| encoder headroom | **indirect** | encoder CPU; RetroArch vs rendered fps |
| storage latency / throughput | **yes** | diskstats, per-process IO |
| network / FEC / decoder telemetry | **yes** | `eno1`; heartbeat; C2; decoder report |
| end-to-end latency | **partial** | C2 latency block; **glass-to-glass ABSENT** (needs a camera) |
| temperatures / throttling | **yes** | Tctl, per-core / SoC / gfx, cpufreq, `throttle_status` |
| package power | **coarse** | socket W, CPU / SoC mW from `gpu_metrics`, hwmon PPT; **RAPL not readable** (root-only, no sudo) |
| wall / idle power | **ABSENT** | needs a meter |
| concurrency behaviour | **yes** | E1-CONC |

## 5. The user's list

1. **NES and Genesis fixtures.** None are installed (0 files). Supply
   them, or the rows stay ABSENT.
2. **A camera: no.** No `/dev/video*`. The camera source is Windows-only
   anyway. `pc_camera.log` (2026-09-15) holds only the launcher banner.
3. **A power meter: no.** Wall and idle power stay ABSENT. Socket power
   from the SMU is the stand-in.
4. **The VOD drive.** The configured `vod_root` drive is not attached.
   Attach it if VOD should be a row.
5. **Live TV.** No unattended channel start exists. Choose one:
   - a hand-tuned channel during E2;
   - a channel extra in a later APK;
   - leave the row ABSENT (the host's share is E1-META by
     architecture).
6. **Which concurrency pairs matter to you.** The only pair the system
   can run today is PS1 streaming + EPG grabs (E1-CONC), and it degrades
   the stream. Others to consider:
   - streaming + a VOD served to a second client (needs the drive and a
     second client);
   - streaming + a library scan (in-process, ms; not worth a row).
7. **Whether the 1080p rung row stays in the suite.** It is not adopted.
   It is repeatable and costs +4.6 points host CPU and +6 W over 720p.
8. Optional: **the metadata reconcile as a workload.** It writes library
   metadata; not run without your word.

## 6. State at the end; files

**Final state** (`runs/final_state.json`, 08:40:55Z):

- manager `PRIVYHUB_*` none;
- environ exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`;
- no game;
- no RetroArch or encoder process;
- **the adopted PS1 files byte-identical**;
- **APK `de072762…835e` CONFIRMED**;
- **flags absent**;
- live default intact.

Per run:

- every teardown: `flags_absent` true, the counter override removed, the
  APK confirmed after every stream run;
- stale NOW PLAYING bars were cleared by force-stop + relaunch (0 after);
- the 1080p row's flags were unset and checked after both runs.

No `nft`, no `sudo`, the Opal untouched.

**Integrity checks:**

- `runs/manifest.sha256`: 133 files; `e1_suite.py --check runs`: **OK**.
- The redactor (`redact_check.txt`): 159 files clean and 13 classified
  false positives, **0 findings**. The false positives are:
  - RetroArch's core version string (four dotted numbers) in the title
    logs;
  - loopback in the inventory, the pre-registration and the runner.

The six EPG channels' cache files were refreshed, as the companion
refreshes them in normal use.

**Files** (`e1_s1_2026-10-05/`):

- `e1_inventory.md`
- `e1_preregistration.txt` and `.sha256`
- `runs/`: per workload, `run1/` and `run2/` with:
  - `summary.json`, `samples.jsonl`;
  - `sampler_summary.json`, `sampler_summary_gap.json`;
  - `telemetry.jsonl`, `title.txt`, `status_poll.jsonl`, `epg.jsonl`;
  - plus `suite.log`, `absent.json`, `final_state.json`,
    `repeatability.{json,md}`, `manifest.sha256`.
- `runs_smoke/` (not data)
- `e1_s1_table.py` and `e1_s1_host_table.txt`
- `e1_s1_conc_check.py` and `.txt`
- `redact_check.txt`

Tools: `tools/e1_sampler.py`, `tools/e1_suite.py`.
