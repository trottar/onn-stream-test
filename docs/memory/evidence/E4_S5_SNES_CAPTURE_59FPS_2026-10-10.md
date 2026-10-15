---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1/S2 work)
---

# E4-S5 — the SNES 59-fps capture fault

**Classification:**

- **Cause LOCATED** (offline, by the pre-registered reading rule;
  confirmed per encoder segment in fresh sessions).
- **The change: REJECTED by the pre-registered bar**, on rendered fps
  (57.99 / 59.21 against ≥ 59.5, on 956 / 316 losses per min). Every
  capture clause held.
- Not adopted (nothing is); the flag is absent.

**The cause.**

- At each encoder start, ffmpeg estimates the x11grab input's frame rate
  from its first frames (the input line's `tbr`).
- The encoder command sets no output rate, so the encoder adopts that
  estimate for the session's whole life.
- For the SNES core's small 897×672 window the estimate is usually 60,
  but sometimes 59.94 or 59, while RetroArch presents at 60.002 Hz:

  | probe | output | drops |
  | --- | --- | --- |
  | 59.94 | 59.94 | one frame dropped every ~17-20 s (the "partial" ~3.5/min) |
  | 59 | 59 | one dropped every second (the whole-window fault) |

- PS1's 1920×1080 window probes `1000k tbr`, no estimate, so its output
  falls back to `-framerate 60`. That is why PS1 never shows it.
- **It is a start-up guess, not load.** Every encoder restart (a live
  ladder transition, a recovery) re-probes, and so re-rolls the dice.

| evidence | what it shows |
| --- | --- |
| offline, 13 Snes9x windows (`offline.md`) | the only recorded value separating both faulty windows from all 11 clean ones: probed `tbr` 59 |
| offline, all 15 Snes9x encoder sessions in `native_video_alpha.log` | output rate = probed tbr in 15 / 15: 60 → 0 drops (10); 59.94 → 1 or 75 drops (3); 59 → 1,295 drops (2) |
| fresh sessions, per encoder segment (`segments.txt`) | 6 / 6 segments follow their probe: 60 → 0 drops/s (3); 59.94 → 0.051-0.057 drops/s (2); **59 → 59.03 fps, 0.947 drops/s** (1, a 19-s segment after a recovery restart) |
| RetroArch's verbose log | `Average monitor Hz: 60.002400 Hz` (2.97 % frame-time deviation): the window is fed at 60 |

**Context:**

- Task: `handoffs/E4-S5_SNES_CAPTURE_59FPS_TASK.md`, under
  `QUEUE_2026-10-10.md`.
- **Baseline: `7331184` plus the uncommitted E4-S1/S2 work**, untouched.
- Files: `e4_s5_2026-10-10/`.
- **Timeline (UTC):**

  | date | time | what |
  | --- | --- | --- |
  | 10-09 | 22:40 | the offline pass (read-only, during E4-S3) |
  | 10-10 | 04:03 | the change applied (after E4-S4's runs); **pre-registration hashed 04:03:18** (`1f3ec381…1b1c`) |
  | 10-10 | 04:03-04:46 | 3 × 10-min sessions, no flag |
  | 10-10 | 04:46-05:35 | 2 × 20-min with the flag |

## 1. The offline pass (§1)

`e4_s5_offline.py` → `offline.md` / `offline.json`.

- **Inputs:** 13 Snes9x windows (E3-A2 1, E3-S4 2, E4-S1 1, E4-S2 9) and
  3 PS1 windows for contrast.
- **Compared:** per-second capture and drops; the encoder session
  header (size, `tbr`, the window title); RetroArch's session log (the
  core's 60.0988 Hz, the audio rate, the video / GL size, the swap
  function, SET_GEOMETRY); what ran just before; the hour; the launch
  attempt.
- **Faulty by the task's classifier** (59.0 ± 0.05 with ~1 drop/s for
  ≥ 2 min): E4-S1's SNES and E4-S2's 400 %. 11 clean.
- **The reading rule** (a value that differs between every faulty window
  and every clean window names the cause): **only the x11grab input
  line**, its `tbr`, 59 vs 60 / 59.94. Everything else overlaps: the
  previous row (VOD vs PS1-STREAM), the hour, the launch attempt, the
  window size (897×672 in all), and every RetroArch value.

## 2. The fresh sessions (§2)

Three SNES-STREAM sessions of 10 min, no flag.

- **Extra instrumentation:**
  - `e4_s5_sidecar.py`: each encoder start's probe and output rate, and
    a 60-s `framemd5` of the window at 120 fps;
  - RetroArch at verbose level, through the counter override
    (`E1_COUNTER_EXTRA`, removed with it): 89 `[DEBUG]` lines.

| session | encoder starts: probe → output | capture fps / dup+drop per min | classifier | rendered; loss/min |
| --- | --- | --- | --- | --- |
| 1 | 59.94 → 59.94 | 59.93 / 3.61 | CLEAN (the 59.94 pattern) | 58.35; 607 |
| 2 | 60 → 60 | 59.99 / 0.10 | CLEAN | 59.23; 174 |
| 3 | 60 → 60; then three recovery restarts: **59 → 59** (19 s), 60 → 60 (25 s), 59.94 → 59.94 (237 s) | 59.89 / 3.02 | CLEAN | 55.13; **2,459** |

**The pre-registered statements:**

- **(i) "the fault appears in a session iff its probe is 59"** reads
  **False** as written: session 3's 59 probe lived only 19 s, under the
  classifier's 2 minutes.
  - Per encoder segment, the mechanism holds in all 6 (the table above).
  - The 59 segment output 59.03 fps with 0.947 drops/s.
- **(ii) "the window at ~60 distinct frames/s"** reads **False** as
  measured:
  - The `framemd5` count (R3c's method) tracks content change, and Super
    Mario World's attract mode has static stretches. Distinct frames per
    second ran 2-60, mean ~49, in every capture, faulty or clean alike.
  - Every capture's maximum is exactly 60. RetroArch's own measurement,
    60.0024 Hz, answers the question the statement asked.

## 3. The change and its runs (§3)

**The change:** `companion/native_stream.py`, behind
**`PRIVYHUB_SNES_CAPTURE_FIX=output_rate`** (absent = today; diff
`e4_s5_change.diff`).

- It adds an output `-r <profile fps>` (60) before `-an` in the x11grab
  encoder command.
- It applies to every x11grab session while the flag is set. The
  mechanism is the probe, not the core; only SNES ran.

| | flag run 1 | flag run 2 | bar |
| --- | --- | --- | --- |
| encoder starts (probe → output, `-r`) | 4 (three ladder / recovery restarts): 60 → 60 (60) each | 1: 60 → 60 (60) | — |
| capture fps (segment-aware) | 59.968 | 59.993 | 60.0 ± 0.1 ✓ ✓ |
| encoder dup+drop / min | 0.05 | 0.10 | ≤ 0.2 ✓ ✓ |
| RetroArch fps | 59.999 | 59.999 | ≥ 59.9 ✓ ✓ |
| host CPU % | 9.38 | 8.75 | 7.4 ± 2 ✓ ✓ |
| **rendered fps** | **57.99** | **59.21** | ≥ 59.5 **✗ ✗** |
| video loss/min; resyncs | 956 | 316 | (reported) |

**Verdict: REJECTED (rendered fps).**

- **The capture parts all hold:** `-r 60` was in every encoder's command,
  with no drop pattern.
- **But the fix was not exercised.** All five probes under the flag read
  60. That is chance: 8 of the 21 SNES probes before it (15 offline
  sessions, 6 fresh segments) were not 60, so 0 of 5 happens about one
  time in eleven. With a 60 probe, today's command behaves the same.
- **Rendered fps failed on the link.** It was 956 and 316 losses/min.
  The unflagged sessions in the same hour rendered 55.1-59.2.
- **What would settle it:** the same two runs on a clean link, plus a
  forced bad probe. For example, a test-only run that starts the encoder
  repeatedly until a 59 / 59.94 probe occurs, then checks that the output
  holds 60 with no drops. That is a proposal, not done.

## 4. KNOWN_ISSUES, the next step

- `docs/KNOWN_ISSUES.md` records the fault as **LOCATED**, with the open
  fix (above).
- **The next step proposed:** adopt-or-not is the user's call.
  - The change is one output option behind the flag, and is
    byte-identical in behaviour when the flag is absent.
  - It would need a clean-link verification or a forced-probe test.
  - It could be scoped to all x11grab sessions (the mechanism is
    general; PS1 never probes).

## 5. State at the end; files

- **Final state** (`runs_flag/final_state.json`, 05:34Z;
  `state_at_end.json`):
  - the four adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game; the PS1 files identical; **APK CONFIRMED**;
  - the counter override (with its verbose lines) removed.
- **The code stays in the tree**, dormant behind the flag, uncommitted.
- No sudo, no nft, the Opal untouched; nothing fetched; no data deleted.
  The window id was read from `/proc` and never written.
- **The sidecar's `input_size` field** caught the pixel-format code
  (`0x524742`), not the size. It is not used for anything; noted.
- **Files** (`e4_s5_2026-10-10/`):
  - `e4_s5_offline.py`, `offline.md`, `offline.json`,
    `offline_console.txt`;
  - `apply_e4_s5.py`, `predecessor_sha256.txt`,
    `predecessor_native_stream.py.txt`, `e4_s5_change.diff`,
    `change_sha256.txt`;
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`;
  - `run_e4_s5.sh`, `e4_s5_sidecar.py`;
  - `runs_sessions/` and `runs_flag/` (each with `sidecar.jsonl`,
    `manifest.sha256`, `check.txt` OK), their console logs;
  - `e4_s5_analysis.py`, `analysis_console.txt`, `e4_s5_table.md`,
    `e4_s5_verdict.json`, `validity.json`, `segments.txt`;
  - `state_at_end.json`, `redact_check.txt`.
- **Patches:** `patches/E4-S5_SNES_CAPTURE_OUTPUT_RATE_FLAG.md` (the
  companion change and the runner's `E1_COUNTER_EXTRA` hook).
- Git status: `logs/e4_s5_git_status.txt`.
