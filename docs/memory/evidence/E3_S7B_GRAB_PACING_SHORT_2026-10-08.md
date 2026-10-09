---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: 969085f
---

# E3-S7B — the grab's network pacing, shorter

**Classification: REJECTED by the pre-registered bar** (E3-S7's,
unchanged). Clauses a, b and c fail in both paced CONC runs. Clause d
now holds, and so do e and comparability.

| clause | result in both CONC runs | holds |
| --- | --- | --- |
| a. loss/min | 309 / 346 | **no** |
| b. rendered fps; resyncs | 59.33 / 59.32; 13 / 14 | **no** |
| c. aligned 0-2 s mean | 7.6 / 11.7 against a limit of 1.0 | **no** |
| d. the guide cycle | 20-21 refreshes per channel; median grab 10.0 s | yes |
| e. the guide serves | 6 channels, 316 programmes | yes |

**The finding, read beside the bar:** 1,500 ms keeps the guide cycle but
not the gain.

- Tonight's own CONC runs with today's unpaced grab (E3-R2's, §4) lost
  518 / 284 per min. That is in the same range as 1,500's 309 / 346.
- Per grab, the damage did not fall:
  - today's grab tonight: ~48 / ~26 lost packets per grab;
  - 1,500: ~49 / ~55;
  - S7's 4,000 (another night): ~18.5 / ~16.6.
- Spacing the request groups 2.1 s apart did not soften each grab, and
  4+ s did. So **the gain S7 saw needs the long spacing**, and the long
  spacing is what breaks the guide cycle.

**The probe also answered S7's open question:** today's grab sends its
request groups back to back (0.26-0.36 s apart). The library's 3-s
default delay is not in effect.

- One change, behind `PRIVYHUB_EPG_GRAB_NET=paced` with the delay from
  `PRIVYHUB_EPG_GRAB_DELAY_MS` (default 4,000, S7's value), run at
  **1,500** by the task's rule. **NOT ADOPTED**; nothing committed.
- **Task 1's flag (`PRIVYHUB_RECOVERY_TRIGGER`) was absent in every
  run.** E3-R2 was REJECTED, so by the queue's exception this task relied
  on E3-A2's replacement rule. All three runs were valid.

**Context:**

- Task: `handoffs/E3-S7B_GRAB_PACING_SHORT_TASK.md`, item 2 of
  `handoffs/QUEUE_2026-10-08B.md`.
- **Baseline commit: `969085f`.** It ran on the adopted state (live, the
  guide index, Snes9x).
- Files: `e3_s7b_2026-10-08/`.
- Timeline (UTC, 2026-10-08):

  | time | what |
  | --- | --- |
  | 15:04 | preconditions held; the change applied (dormant) |
  | 15:04-15:07 | the spacing probe, first pass (its child detector flawed, §1) |
  | 15:08-15:11 | the spacing probe, second pass |
  | 15:11:30 | pre-run guide read: 6 channels, 321 programmes; no background refresh since the start |
  | **15:12:09** | **pre-registration hashed** (`b71df09e…20a1`) |
  | 15:12-16:25:40 | the control, CONC paced 1,500 ×2; all OK and valid |
  | 16:26:59 | post-run guide read: 6, 316 |

## 1. The probe: the spacing itself (`spacing_table.md/.json`, `spacing/`)

**Set-up:**

- The stream was idle: no game, no session.
- One forced grab of CNBCUK.uk@SD (site mytelly.co.uk) per setting.
- `eno1` bytes were sampled every 100 ms.
- The child's `--delay` was read from its own command line.

**The first pass (`spacing_first_pass/`) is not used for spacing.** Its
child detector (`pgrep -f` on the grabber's path) also matched the tool
shell running the probe, so the child looked alive for the whole sampling
period. Its companion-side request wall times are sound and appear below.
The second pass counts only the grabber's npm / sh / node processes.

| setting | `--delay` on the child | request wall s (pass 1 / 2) | child wall s | request groups | start-to-start s | quiet between s |
| --- | --- | --- | --- | --- | --- | --- |
| today | none | 2.98 / 7.97 | 7.82 | 3 | 0.36, 0.36 | 0.26, 0.26 |
| 1,000 | `--delay=1000` | 4.95 / 4.94 | 4.73 | 2 | 1.55 | 1.21 |
| 1,500 | `--delay=1500` | 6.07 / 5.97 | 5.80 | 2 | 2.14 | 1.81 |
| 4,000 | `--delay=4000` | 10.99 / 10.94 | 10.78 | 4 | 2.26, 0.47, 1.90 | 1.92, 0.26, 1.80 |

**How the grabber paces:**

- It sleeps the delay before each `grab(channel, day)` call. `GRAB_DAYS`
  is 2.
- The site's own requests inside one call (mytelly: form, regions,
  schedule, listing) still go back to back.
- So a "request group" is not a single HTTP request. Idle, each second of
  delay adds ~2 s per grab.
- Today's start-up time varies (2.98 / 7.97 s).

**The choice, stated in the pre-registration before the runs:** the
projected CONC median was ~7.9 s at 1,000 and ~9.1 s at 1,500. Both stay
≤ 11.8 s with margin, so the task's preference applies: **1,500**. The
refreshes clause was named as near its edge (~21 per channel projected).
It landed at 20-21.

## 2. The change (`patches/E3-S7B_GRAB_DELAY_VALUE.md`)

`companion/plugins/epg.py` `_grab_from_candidate`: with
`PRIVYHUB_EPG_GRAB_NET=paced`, the grabber gets
`--delay=<PRIVYHUB_EPG_GRAB_DELAY_MS>`.

- The default is 4,000, so S7's result stays reproducible; a value that
  doesn't parse also gives 4,000.
- Absent flag: today, byte for byte.
- Diff: `e3_s7b_grab_delay.diff`.

## 3. The runs and the bar

From `e3_s7b_table.md`, `e3_s7b_verdict.json`, `validity.json`, the
analysis script `e3_s7b_analysis.py`, and `loss_vs_cycle.md`.
**Task 1's flag is absent in every column of this task.**

| | control (no flag) | CONC 1,500 r1 | CONC 1,500 r2 | S7 CONC 4,000 r1 / r2 | E3-S6A CONC (today's grab) | E2 PS1-STREAM |
| --- | --- | --- | --- | --- | --- | --- |
| valid (no recovery pause) | yes | yes | yes | yes / yes | yes | yes |
| host CPU % | 10.9 | 17.3 | 16.7 | 14.6 / 14.0 | 22.2 | 11.7 |
| rendered fps | 59.91 | **59.33** | **59.32** | 59.83 / 59.82 | 57.64 | 59.81 |
| video loss/min | 20.0 | **309** | **346** | 66.7 / 59.6 | 1,312 | 32.3 |
| resyncs; underruns | 0; 13 | 13; 9 | 14; 27 | 1; 12 / 3; 12 | 52; 11 | 0; 11 |
| aligned loss 0 / +1 / +2 s (lost pkt/s) | — | 4.6 / 7.6 / 10.5 | 4.6 / 14.3 / 16.3 | 2.0 / 3.9 / 3.6; 1.0 / 3.6 / 3.3 | 16.3 / 26.9 / 28.7 | — |
| grabs ok / failed, median s | — | 126 / 0, 10.0 | 125 / 0, 10.0 | 72 / 0, 14.8 / 15.1 | 230 / 0, 5.6 | — |
| refreshes per channel | — | 21 ×6 | 20-21 | 12 | ~38 | — |
| EPG child CPU % / PSS MB | — | 46.8 / 559 | 46.9 / 559 | 28.7 / 596 | 85.1 / 486 | — |
| companion CPU % / PSS MB | 25.1 / 38.3 | 26.0 / 46.6 | 25.9 / 47.0 | 25.1 / 45.3 | 26.5 / 45.8 | 24.3 / 38.1 |
| eno1 rx kB/s | 36.9 | 89.6 | 89.3 | 67.9 / 67.7 | 131.9 | 39.3 |
| socket W | 20.3 | 24.2 | 23.8 | 22.1 / 23.5 | 27.0 | 20.4 |

| clause | needed (both CONC runs) | got | holds |
| --- | --- | --- | --- |
| comparability | control 11.69 ± 2; 59.81 ± 0.5 | 10.89; 59.91 | yes |
| a. loss/min | ≤ 100 and ≤ 3 × 19.99 = 60.0 | 308.8 / 346.3 | **no** |
| b. rendered; resyncs | ≥ 59.5; ≤ 10 | 59.33 / 59.32; 13 / 14 | **no** |
| c. aligned 0-2 s mean | ≤ 3 × 0.333 = 1.00 | 7.56 / 11.74 | **no** |
| d. grabs failed 0; each channel ≥ 20; median ≤ 11.8 s | | 0; 21 / 20 (min); 10.0 / 10.0 | yes |
| e. the guide serves | 6; 305-337 | 6; 316 | yes |

**Verdict: REJECTED** (a, b, c).

## 4. Loss vs cycle speed, so the user can choose a point

| CONC run | delay | night | loss/min | rendered fps | resyncs | grabs | refreshes per channel | median grab s | lost packets per grab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E3-S6A | today (~0) | 10-07 | 1,312 | 57.64 | 52 | 230 | ~38 | 5.6 | ~114 |
| **E3-R2 CONC r1** (v2 flag, never fired) | today (~0) | **tonight** | 518 | 58.97 | 25 | 217 | ~36 | 5.4 | ~48 |
| **E3-R2 CONC r2** (same) | today (~0) | **tonight** | 284 | 59.42 | 9 | 220 | ~37 | 5.5 | ~26 |
| **E3-S7B r1** | 1,500 | tonight | 309 | 59.33 | 13 | 126 | 21 | 10.0 | ~49 |
| **E3-S7B r2** | 1,500 | tonight | 346 | 59.32 | 14 | 125 | 20.8 | 10.0 | ~55 |
| E3-S7 r1 | 4,000 | 10-08 early | 66.7 | 59.83 | 1 | 72 | 12 | 14.8 | ~18.5 |
| E3-S7 r2 | 4,000 | 10-08 early | 59.6 | 59.82 | 3 | 72 | 12 | 15.1 | ~16.6 |

Lost packets per grab = loss/min × 20 / grabs, a rough figure.

The aligned 0-2 s mean of tonight's unpaced runs, against this task's
control, is 10.6 / 6.3 (`e3_s7b_aligned_r2_conc.py`,
`aligned_r2_conc.json`; reported only). At 1,500 it was 7.6 / 11.7.
**The same range.**

**Reading:**

- Between 0 and 1,500 ms, the spacing does not change what one grab
  costs the stream. The CONC loss/min falls only in step with how often
  grabs run.
- 4,000 ms cut the cost per grab by ~3×, and the guide cycle by ~3× too.
- The link differs night to night: E3-S6A's unpaced CONC lost 1,312/min,
  tonight's 284-518. Only same-night rows compare cleanly, and 4,000 has
  none.

**What the user can choose from:**

1. **Leave CONC as it is.** The guide index is adopted; the per-grab
   peak stays.
2. **4,000 with a looser cycle bar.** About 12 refreshes per channel in
   a forced 20-min cycle; ordinary background refreshes are rare.
3. **A different lever.** The per-grab cost follows the request burst
   inside one grab (S7's probe: network, not CPU). Fewer requests per
   grab (`GRAB_DAYS` 1), or pacing inside the site's own request queue,
   are untested.

## 5. The one-line adoption and its revert (if the user chose it anyway; not on the bar's terms)

Two lines in a drop-in, e.g. `epg-pacing.conf` beside the others:

```ini
[Service]
Environment=PRIVYHUB_EPG_GRAB_NET=paced
Environment=PRIVYHUB_EPG_GRAB_DELAY_MS=1500
```

**Revert:** delete the file, `daemon-reload`, restart. Absent = today.
An adoption would also need its names in `ADOPTED` / `ADOPTED_E3` (the
state checks).

## 6. State at the end; files

- **Final state** (`runs/final_state.json`, 16:25:40Z):
  - manager none; environ exactly live + the index + Snes9x;
  - no e3 drop-in; no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- Both flags absent; the code is dormant.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched beyond
  the companion's own guide grabs; nothing deleted. No other task's
  script was run (E3-S7's analysis was copied and adapted here; E3-R2's
  runs were read in place).
- Files (`e3_s7b_2026-10-08/`):
  - `precondition.json`, `predecessor_sha256.txt`, `e3_s7b_grab_delay.diff`;
  - `e3_s7b_spacing_probe.py`, `spacing/`, `spacing_table.md/.json`,
    `spacing_console.log`, and the first pass
    (`spacing_first_pass/`, `spacing_table_first_pass.*`,
    `spacing_console_first_pass.log`);
  - `epg_status_before.json`, `guide_read_before.json`,
    `guide_read_after.json`;
  - the pre-registration and its `.sha256`;
  - `runs/` (3 runs; `manifest.sha256`, `check.txt` OK), `runs_console.log`;
  - `e3_s7b_analysis.py`, `analysis_console.txt`, `e3_s7b_table.md/.json`,
    `aligned_ctl/`, `validity.json`, `e3_s7b_verdict.json`,
    `loss_vs_cycle.md`;
  - `e3_s7b_aligned_r2_conc.py`, `aligned_r2_conc_view/`,
    `aligned_r2_conc.json`;
  - `redact_check.txt`.
- Git status: `logs/e3_s7b_git_status.txt`.
