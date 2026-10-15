---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 7331184
---

# E4-S1 — the reference on the adopted state

**"The known-good reference for this host on the adopted state,
2026-10-09; no floor and no lower-tier claim."**

**Classification: REFERENCE RE-MEASURED.**

- 8 rows × 1 run × 20 min, all valid; 0 replaced attempts.
- `--check` OK; 0 controller pauses; 0 saves.
- **No bar.** The D-BASE table on PS1-STREAM: spikes, stale and rendered
  hold; the loss row fails on tonight's link (169/min).
- Measurement only; nothing adopted, nothing committed.

**Context:**

- Task: `handoffs/E4-S1_REFERENCE_ON_ADOPTED_STATE_TASK.md`, under
  `handoffs/QUEUE_2026-10-09.md`.
- **Baseline commit: `7331184`** (the user's E3-close commit). The tree
  was clean at the start.
- Files: `e4_s1_2026-10-09/`.
- The state measured is the four-line adopted state (live, the guide
  index, Snes9x, recovery v2), checked in `precondition.json` before
  the pre-registration. No E3 flag was set.
- **Timeline (UTC, 2026-10-09):**

  | time | what |
  | --- | --- |
  | 05:55 | precondition ok |
  | **05:57:09** | **pre-registration hashed** (`8cb72549…aa2f`) |
  | 05:57-09:17 | the 8 runs, E2's order and gaps (600 s before SNES) |
  | 09:17 | analysis; manifest; `--check` OK |

## 1. The reference — the ROADMAP's four rows

Each value is a 20-min window mean. E2 (2026-10-06, before E3's
adoptions) is in brackets. **Heaviest** = the highest host-CPU row other
than the contended one, a rule written before the data; it came out as
PS1-1080P.

| workload | row | host CPU % (p95) | busiest core p95 % | PrivyHub CPU, % of one core | PrivyHub PSS MB | socket W | Tctl °C | stream |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| idle | IDLE | 1.2 (1.8) [0.9] | 3 [3] | ~0 | companion 26 + range server 14 = 40 [40] | 5.3 [4.7] | 34 [33] | — |
| streaming | PS1-STREAM | 10.9 (12.9) [11.7] | 29.9 [28.7] | companion 25 + RetroArch 34 + encoder 36 = **95** [94] | 38 + 230 + 72 (+14) = 354 [355] | 20.1 [20.4] | 61 [60] | 59.53 fps, loss 169/min [59.81, 32] |
| contended | CONC | 21.4 (29.4) [20.5 / 21.9] | 64.7 [63-66] | companion 26 + RetroArch 36 + encoder 35 + node 75 = **172** [184 / 191] | 47 + 230 + 72 + 493 (+14) = **856** [971 / 991] | 25.7 [25.3-25.9] | 68 [70] | 58.46 fps, loss 813/min [56.5, ~1,600] |
| heaviest | PS1-1080P | 15.3 (17.1) [13.8] | 27.8 [28.3] | companion 29 + RetroArch 37 + encoder 73 = **139** [126] | 39 + 234 + 74 (+14) = 362 [369] | 22.0 [20.6] | 64 [62] | 59.63 fps, loss 102/min [59.87, 23] |

**Every row:**

| row | host CPU % (p95) | busiest core p95 | PrivyHub CPU total | PrivyHub PSS MB | socket W | Tctl | rendered fps | loss/min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IDLE | 1.2 (1.8) | 3.0 | 0.0 | 40 | 5.3 | 34 | — | — |
| PS1-LOCAL | 5.3 (6.8) | 23.8 | 33 | 293 | 14.5 | 51 | — | — |
| PS1-STREAM | 10.9 (12.9) | 29.9 | 95 | 354 | 20.1 | 61 | 59.53 | 169 |
| PS1-1080P | 15.3 (17.1) | 27.8 | 139 | 362 | 22.0 | 64 | 59.63 | 102 |
| META | 10.8 (17.3) | 58.6 | 74 | 535 | 15.8 | 59 | — | — |
| VOD | 1.2 (1.7) | 3.0 | 0.1 | 42 | 4.9 | 33 | ratio 1.000, 118 kB/s | — |
| SNES-STREAM (Snes9x) | **7.4 (8.8)** | 16.5 | **60** | 230 | **15.2** | **49** | 58.74 | 54 |
| CONC | 21.4 (29.4) | 64.7 | 172 | 856 | 25.7 | 68 | 58.46 | 813 |

- **The full table** is `e4_s1_2026-10-09/e4_s1_table.md`, with every E2
  metric, E2's run(s) beside, and the ABSENT rows stated.
- **Still ABSENT:** wall power (no meter), glass-to-glass latency (no
  camera), VCN duty (reads ~0), RAPL (root-only), and the NES, Genesis,
  Live TV, camera and browser rows.
- **Swap:** ≤ 0.003 page/s in, 0 out. Memory PSI is 0.

## 2. The checks (pre-registered §3)

**(a) The D-BASE close-out table on PS1-STREAM:**

| metric | target | tonight | holds |
| --- | --- | --- | --- |
| spikes ≥ 20 ms/min (session report) | < 200 | 82.2 | yes |
| stale drops/min (session report) | < 20 | 2.6 | yes |
| rendered fps (heartbeat, window) | ≥ 59.5 | 59.53 | yes (barely) |
| video loss/min (post-FEC) | < 10 | **169** | **no**, tonight's link; reported, not the system's |

**(b) Validity** (`validity.json`):

- Every row is valid; no attempt was replaced.
- PS1-STREAM and SNES-STREAM reached PLAYING on the onn's second launch
  try, inside one runner attempt.
- PS1-1080P was at 1920×1080 for the whole window (entry at the first
  injection, 12,600 kbps). Its rung flags were unset after.
- VOD progress ratio 0.9999.

**Recovery v2 on the four stream rows** (from the gap log and the
recovery log; `gaps/`):

| row | gaps (count / > 1 s / max ms) | controller pauses | client pauses (resume s) | `gave_up_saved` |
| --- | --- | --- | --- | --- |
| PS1-STREAM | 18 / 0 / 930 | 0 | 1 (7.8) | 0 |
| PS1-1080P | 52 / **5** / 1,806 | 0 | 0 | 0 |
| SNES-STREAM | 10 / 0 / 965 | 0 | 0 | 0 |
| CONC | 9 / 0 / 904 | 0 | 0 | 0 |

The 1080p row had five uplink silences over 1 s. None paused the game;
the old 1-s rule would have.

## 3. Drift from E2 (pre-registered §4)

`e4_s1_drift.md`: **14 of 89 compared metrics moved** beyond E1's bands.

| row | metric | E4 | E2 | explained by |
| --- | --- | --- | --- | --- |
| SNES | host CPU % | 7.4 | 43.4 / 50.0 | **Snes9x (E3-A2)** |
| SNES | RetroArch CPU (% of a core) | 8.3 | 436 / 517 | **Snes9x** |
| SNES | RetroArch RSS / PSS | 147 / 113 MB | 281 / 247 MB | **Snes9x** |
| META | companion CPU / PSS | 0.2 % / 34 MB | 7.6 % / 153 MB | **the guide index (E3-S6A)** |
| META | companion RSS (main process) | 44 MB | 164 MB | **the guide index** |
| CONC | companion CPU / PSS | 26 % / 48 MB | 33 % / 174-200 MB | **the guide index** |
| META | node child CPU | 74 % | 67 % | nothing does |
| CONC | node child CPU | 75 % | 79-81 % | nothing does |
| PS1-1080P | RetroArch CPU | 36.5 % | 22.5 % | nothing does |
| SNES | rendered fps | 58.74 | 59.66 / 59.98 | nothing does; see §4 |
| CONC | rendered fps | 58.46 (better) | 56.53 / 56.57 | nothing does |

- **PS1-1080P RetroArch:** E2's 22.5 % was the odd one out. Tonight's
  36.5 % matches the 720p rows (33-36 %), as the source is the same 4x
  render.
- **The node grabber:** the index changed the companion's side, not the
  grabber. Its ±5-8 points are within run-to-run noise for a 20-min
  cycle of ~214-259 grabs. Its peak PSS per grab is ~650 MB in both, and
  META's last grab peaked at 855 MB.
- **CONC rendered fps:** better than E2 (loss 813/min vs ~1,600) on a
  link that varies by the hour. No adoption targets the grab-vs-stream
  loss: S7's pacing was not adopted, and S6's stream clause was
  REJECTED.
- **Recovery v2** explains no drift. Its gap log costs ~0.003 point of a
  core (E3-A3B); the stream rows' companion CPU is within band
  (25.0 vs 24.3).
- **Everything else** (75 metrics) is within E1's bands of E2, including
  PS1-STREAM's whole stack (94.6 vs 94.3 % of a core) and idle.

**The memory reading (E2 §5, reported).** The first grab now adds
~6 MB anon to the companion, against ~110 MB in E2. The companion ends
META at 34 MB and CONC at 49 MB. CONC "keeps growing" by E2's rule,
slope 5.9 %/15 min at 42-49 MB.

**The CONC aligned frame (E2 §3, reported).** The busiest core still
rises first and most: +4.2 sd, 75 % at 1 s after a grab's start. The
relay thread is flat, and there are 0 host tx drops. Lost packets in
grab bodies are 13/s, against ~65/s at the 1-s peak in E2.

## 4. Found: SNES captured at exactly 59 fps

On SNES-STREAM tonight, the encoder output **exactly 59.0 fps, with one
frame dropped every second** (964 dropped in the window; 0 duplicated).
This held from the first minute to the last.

- RetroArch held 59.999 fps at 8 % of a core.
- The core log (Snes9x 60.0988 Hz) is identical to E3-A2's.
- E3-A2's and E3-S4's Snes9x runs captured 60.0 fps with 0 drops.

**So this is not load.** Load would not be exactly 1/s, at 7 % host
CPU. E2 §4's analysis code mechanically reads it as "the emulator
starves the encoder"; that reading does not apply.

- It probably explains the row's 58.74 rendered fps.
- **Not chased** (measurement only). It is an open item for the user,
  and the next SNES run will show whether it repeats.
- E4-S2's pass rule judges the SNES row's capture against this
  reference (its reference-relative clause). This record was written
  before E4-S2's pre-registration.

**Also found:** the sampler's summary capture fps and dup+drop are
first-to-last over the window. Any encoder restart (a live-ladder
transition, a recovery) breaks them; E3-A3B's PS1 window reads 12.3 fps
by it. The table adds a **segment-aware** row. Tonight's E4-S1 windows
had one encoder segment each, so both figures agree here.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 09:17:30Z):
  - the four `PRIVYHUB_*` lines; the manager none; no `e3_flag.conf`;
  - no game, no RetroArch, no encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- No `nft`, no `sudo`, the Opal untouched. Nothing fetched; the VOD drive
  only read. No other task's script was run (`e2_analysis.py` was
  copied, not run).
- **Files** (`e4_s1_2026-10-09/`):
  - `precondition.json`, `git_status_at_start.txt`;
  - the pre-registration, its `.sha256` and `preregistration_hashed_at.txt`;
  - `runs/` (8 runs, `manifest.sha256`, `check.txt`), `runs_console.log`;
  - `e4_s1_analysis.py` and its outputs: `analysis_console.txt`,
    `e4_s1_table.md/.json`, `e4_s1_drift.md`, `e4_s1_reference.md`,
    `validity.json`, `gaps/`, `e4_s1_conc.md`, `e4_s1_snes.md`,
    `e4_s1_memory.md`, `e4_s1_analysis.json`;
  - `redact_check.txt`.
- **Tools:** `tools/e1_suite.py` was extended during these runs, for
  E4-S2. The running suite had already loaded the predecessor, so E4-S1
  ran on the predecessor (`334528a3…b186`). See E4-S2's record and
  `patches/`.
- Git status: `logs/e4_s1_git_status.txt`.
