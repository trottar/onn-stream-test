---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: dfa1626 (G-A2 committed; the tree carried only the user's prompt and this task file)
---

# CL-B6 — the A/B repeated after an onn power-cycle

**Classification: both runs VALID; every host gate HELD in both. The adopted state is unchanged** (the eight lines,
Opus adopted, no `e3_flag.conf`, `--check` ok). Measurement only; nothing committed.

- **The question:** was G-A2's single-run 78 underruns the codec, or the onn after a long evening?
  - The user power-cycled the onn; its uptime was 71 s at the precondition.
  - Two runs, 5 min apart: Opus as adopted first, then PCM by override (CL-B5's order reversed).
- **Run 1, Opus on a fresh onn: underruns 22** (13 in the heartbeat window), against G-A2's 78 / 50 and CL-B5
  B / L's 11 / 13.
  - **By the reading written beforehand:** run 1 is back near 11-13, so **G-A2's 78 reads as the onn's state after
    many sessions, not the codec.** Consistent-with, not proved.
  - The session count, 22, is 2 over D-BASE-P10's ≤ 20; the window count, 13, is under.
- **Run 2, PCM: underruns 11** (8 in the window). PCM was not high, so the evening's link and the onn were not
  bad either.
- **The decoder spikes still follow the codec,** on the same evening:
  - ≥ 20 ms: **Opus 104.7 / min against PCM 61.4** (CL-B5: 144.0 against 100.4);
  - ≥ 50 ms: 2.92 against 2.24 / min.
  - **The onn's CPU, read for the first time:** 150 s into each window the PrivyHub process used **107 % (Opus)
    against 85 % (PCM)** of one core, and the onn was 51.0 % against 46.0 % busy of its 4 cores.
  - The Opus decode costs the client ~0.2 core. That is the candidate for the spikes, still not proven, and it is
    now measured.
  - G-A2's ≥ 50-ms spikes (11.8 / min) did not recur: 2.9 here.
- **The wire, paired:** Opus against PCM on the LAN interface, **−2,916.3 kbit/s and −202.7 packets/s.**
- **The user's lines, verbatim:**
  - run 1 (Opus): no listen during it;
  - run 2 (PCM): "It sounds fine";
  - then "Both are fine" (for run 1, given after it had ended).

Task: `handoffs/CL-B6_AB_REPEAT_AFTER_RESTART_TASK.md`, session A. Pre-registration:
`cl_b6_2026-10-19/cl_b6_preregistration.txt`, sha256 `c9d48ab1…5169`, hashed at 02:33:31Z, before the first run,
with the reading written beforehand (§5 there).

## 0. Precondition (02:32Z)

`check_start.json`, `client_start.json`, `onn_reads.jsonl` `precondition`:
- the eight lines; `--check` ok, with adb to the onn (connected after the power-cycle; no hand step was needed this
  session);
- APK `043891e1…` CONFIRMED;
- no `e3_flag.conf`, no game;
- one device paired, `identity_v2` on;
- **the onn's uptime 71 s** (`adb shell uptime`: up 1 min);
- HEAD `dfa1626`; the tree carried the user's prompt and the task file, not touched.

## 1. One tool patch, before the runs (disclosed in the pre-registration)

**`tools/e1_suite.py`** (`e1_suite.diff`; predecessor in `predecessors/`):
- **The problem:** the post-restart check expected `sorted(ADOPTED + the run's drop-in)`. With Opus adopted, the PCM
  arm's drop-in `PRIVYHUB_AUDIO_CODEC=pcm` *replaces* the adopted `=opus` in the environ rather than adding a line,
  so the check could never hold and run 2 would have been refused.
- **The patch:** new `expected_environ()`. A run drop-in's `KEY=VAL` replaces the adopted line with the same `KEY`.
  With no shared `KEY`, the result is exactly the former rule.
- **Tests** (`tests.txt`): self-test cases added for both behaviours; `--self-test` OK; `test_e1_remote` and
  `test_c3_l4_nft_night` OK.
- Nothing else in the suite changed. **This is not another way of turning Opus off:** the PCM arm is the
  pre-registered `e3_flag.conf`, verified below.

## 2. The runs (one suite invocation; `runs/`, `runs_console.log`)

- **The plan:** `E1-PS1-STREAM:1:120,E1-PS1-STREAM:1:300:PRIVYHUB_AUDIO_CODEC=pcm`, window 600 s, `--e2`, the same
  PS1 title.
- **Run 1, Opus as adopted, no `e3_flag.conf`:**
  - PLAYING at 02:36:12Z (4.1 s); window 02:37:42-02:47:42Z.
  - `token_issued` at **`sig_v` 3 / opus** (02:35:57Z);
  - the companion's `opus 128 kbit/s, 10-ms frames` (02:36:05Z);
  - **320 heartbeats `opus`, 0 `pcm`** in the window;
  - the report's `codec: opus`.
- **Run 2, PCM by override:**
  - `e3_flag.conf` = `PRIVYHUB_AUDIO_CODEC=pcm`, restart.
  - **The environ read back showed `PRIVYHUB_AUDIO_CODEC=pcm` and no `=opus`** (`environ_run2.txt`: eight lines,
    the override in place of the adopted value).
  - **The companion's log: `ignored (codec 'pcm' is not opus); audio stays PCM`** (02:48:10Z;
    `companion_codec_line_run2.txt`).
  - PLAYING at 02:53:32Z (3.0 s); window 02:55:02-03:05:02Z.
  - **301 heartbeats `pcm`, 0 `opus`**; the report's `codec: pcm`.
  - The client still declared opus at setup (`sig_v` 3 / opus, 02:53:18Z), and the host ignored it, as designed.
- **Teardown:** the override removed, restart, `flags_absent` true. The environ was back to **the eight adopted
  lines with `=opus`** (`environ_end.txt`). `--check` ok (`check_end.json`).
- **Validity** (`validity.json`, `audit_runs.jsonl`, `journal_codec_lines.txt`): both OK.

## 3. The onn, over adb (state reads only; `cl_b6_onn_read.py`, `cl_b6_read_scheduler.py` → `onn_reads.jsonl`)

`top` was taken as the second of two 1-s iterations. CPU is in % of the onn's 4 cores (400 %); the PrivyHub column
is in % of one core.

| read | at (UTC) | uptime s | load 1 / 5 / 15 | onn busy % (user / sys / idle of 400) | PrivyHub % of a core / RES | thermal; cpu-thermal °C | MemAvailable |
| --- | --- | ---: | --- | --- | --- | --- | ---: |
| precondition | 02:32:47 | 104 | 9.57 / 4.34 / 1.61 | 10.5 (3 / 38 / 358) | 0.0 / 106M | 0; 56.5 | 777 MB |
| before run 1 | 02:33:48 | 166 | 3.26 / 3.50 / 1.50 | 5.5 (4 / 16 / 378) | 0.0 / 106M | 0; 54.3 | 774 MB |
| **run 1 (Opus) +150 s** | 02:40:12 | 549 | 3.61 / 3.16 / 1.94 | **51.0** (108 / 73 / 196) | **107.0** / 162M | 0; 63.8 | 668 MB |
| before run 2 | 02:48:14 | 1,031 | 3.22 / 3.39 / 2.58 | 4.2 (5 / 12 / 383) | 0.0 / 156M | 0; 62.6 | 678 MB |
| **run 2 (PCM) +150 s** | 02:57:32 | 1,589 | 2.72 / 2.28 / 2.18 | **46.0** (91 / 75 / 216) | **85.0** / 165M | 0; 63.8 | 610 MB |

These are single samples, one per window. The onn's CPU was not read in CL-B5 or G-A2, so there is no uptime / CPU
for those rows.

## 4. The table across the six runs (`cl_b6_analysis.py` → `cl_b6_verdict.json`, `cl_b6_analysis_console.txt`)

| | CL-B5 A pcm | CL-B5 B opus | CL-B5 L opus | G-A2 opus | **CL-B6 1 opus** | **CL-B6 2 pcm** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| when (UTC) | 10-18 23:31 | 10-18 23:48 | 10-19 00:18 | 01:53 | **02:37** | **02:55** |
| onn uptime at the window | n/r | n/r | n/r | n/r (5 sessions since 22:00Z) | **~7-17 min** | **~24-34 min** |
| RetroArch / capture / dup+drop (gates) | 59.999 / 59.998 / 0.1 | 59.999 / 59.998 / 0.1 | 59.999 / 59.999 / 0.1 | 59.999 / 59.999 / 0.1 | **59.999 / 59.997 / 0.1** ✓ | **59.999 / 59.998 / 0.1** ✓ |
| `flags_absent` after (gate) | true | true | true | true | **true** ✓ | **true** ✓ |
| **underruns** (session / window; ≤ 20 of interest) | 19 / 17 | 11 / 7 | 13 / 10 | 78 / 50 | **22 / 13** | **11 / 8** |
| net audio loss (ms; per min) | 135; 11.6 | 300; 25.8 | 280; 23.9 | 10; 0.9 | **10; 0.9** | **450; 38.7** |
| arrival holes > 15 ms / min | 829 | 935 | 916 | 865 | 846 | 780 |
| queue residence avg / max ms | 65.3 / 106 | 57.5 / 145 | 58.1 / 94 | 57.7 / 100 | 58.5 / 94 | 66.0 / 167 |
| decode queue depth max / wait max ms | — | 19 / 185.5 | 20 / 86.5 | 36 / 166.8 | **20 / 81.8** | — |
| decoder spikes ≥ 20 ms / min | 100.4 | 144.0 | 136.7 | 163.1 | **104.7** | **61.4** |
| decoder spikes ≥ 50 ms / min | 4.65 | 4.39 | 2.91 | 11.84 | **2.92** | **2.24** |
| max output gap (report) ms | 180 | 227 | 310 | 351 | 261 | 209 |
| host ctrl gaps > 1 s (max ms) | 0 (694) | 0 (981) | 1 (1,007) | 2 (1,234) | **0** (688) | **0** (552) |
| video loss / min | 19.9 | 25.2 | 48.5 | 24.2 | 12.9 | 51.0 |
| rendered fps | 59.88 | 59.85 | 59.85 | 59.69 | 59.92 | 59.83 |
| **eno1 tx kbit/s / packets/s** | 11,913.0 / 1,378.9 | 9,003.5 / 1,178.2 | 9,005.6 / 1,178.2 | 8,994.2 / 1,176.6 | **8,995.8 / 1,176.9** | **11,912.1 / 1,379.6** |
| host CPU %; companion / encoder % of a core | 10.29; 24.76 / 36.18 | 10.10; 21.25 / 36.76 | 11.07; 21.33 / 36.68 | 9.90; 21.05 / 36.30 | 10.28; 20.93 / 36.77 | 10.32; 24.38 / 36.53 |
| **the onn: busy % / PrivyHub % of a core (+150 s)** | n/r | n/r | n/r | n/r | **51.0 / 107** | **46.0 / 85** |

(n/r = not read.)

**Read plainly:**
1. **Underruns.** On a fresh onn, Opus read 22 / 13 and PCM 11 / 8. G-A2's 78 / 50 came after five sessions that
   evening.
   - With CL-B5's 11 and 13, three of four Opus runs sit at 11-22, and the outlier is the long-uptime one. The
     pre-registered reading applies: **consistent with the onn's state, not the codec.** Not proved: one restart,
     one run per arm.
   - The Opus session count is 2 over the ≤ 20 bar; the window count is under.
2. **The spikes are the codec's on the client.** Opus is over PCM on both evenings: +44 / min in CL-B5, +43 / min
   here.
   - The onn's PrivyHub process used ~0.22 core more under Opus at the same moment of each window.
   - This is a correlation from single samples, not a located cause. The ≥ 50-ms spikes are small in both arms
     (2.9 / 2.2 per min).
   - The item stays open, with its candidate now measured.
3. **The wire:** −2,916 kbit/s and −203 packets/s, the same saving as CL-B5 (−2,910 / −201) and G-A2.
4. **Net audio loss** is the path's: 10 ms (Opus) against 450 ms (PCM) on this evening, against CL-B5's 300 / 135.
   It does not follow the codec.

## 5. The user's lines (verbatim; nothing perceptual is a gate; `user_reports.tsv`)

| run | at (UTC) | the user's line |
| --- | --- | --- |
| 1 — Opus (adopted) | — | no line during run 1's window (02:37:42-02:47:42Z) |
| 2 — PCM (override) | 03:01:04Z (mid-window) | "It sounds fine" |
| both | 03:01:25Z (during run 2; for run 1, after it had ended) | "Both are fine" |

## 6. State at the end (03:06Z)

- **The eight adopted lines (Opus adopted); no `e3_flag.conf`; no game; APK `043891e1…` CONFIRMED; `--check` ok**
  (`check_end.json`, `environ_end.txt`). The adopted state is unchanged.
- One device paired (`client_end.json`).
- Nothing committed (`logs/cl_b6_git_status.txt`).

## 7. Files

**`cl_b6_2026-10-19/`:**
- the run's context: `baseline_head.txt`, `git_status_at_start.txt`, the pre-registration, its hash and the time
  it was hashed;
- the patch: `predecessors/e1_suite.py`, `predecessor_sha256.txt`, `e1_suite.diff`, `tests.txt`;
- the onn reads: `cl_b6_onn_read.py`, `cl_b6_read_scheduler.py`, `read_scheduler_console.log`, `onn_reads.jsonl`;
- the runs: `runs/` (run 1 = `E1-PS1-STREAM/run1`, run 2 = `E1-PS1-STREAM_flag/run1`, `suite.log`),
  `runs_console.log`, `audit_offset_before_run.txt`, `audit_runs.jsonl`, `journal_codec_lines.txt`,
  `environ_run2.txt`, `companion_codec_line_run2.txt`, `environ_end.txt`;
- the client reads and the checks: `client_*.json`, `check_*.json`;
- the user's lines: `user_reports.tsv`;
- the analysis: `cl_b6_analysis.py`, `cl_b6_analysis_console.txt`, `cl_b6_verdict.json`, `validity.json`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

No sudo (only `systemctl --user`, through the suite), no nft, the Opal untouched. adb was used only for state reads:
`uptime`, `/proc/uptime`, `top`, `dumpsys thermalservice`, `/proc/meminfo`, the client read. Nothing fetched,
nothing deleted.
