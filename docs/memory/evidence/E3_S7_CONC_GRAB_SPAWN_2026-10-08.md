---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: def1ad1
---

# E3-S7 — the grab's spawn share of the CONC loss

**Classification: REJECTED by the pre-registered bar.** Three clauses
fail in both paced CONC runs:

- **a**: loss/min is ≤ 100 but above 3 × the control;
- **c**: the aligned frame's 0-2 s mean is above 3 × the control's
  baseline;
- **d**: the guide cycle slowed to **12 refreshes per channel** (needs
  ≥ 20) and a **median grab of 14.8 / 15.1 s** (≤ 11.8).

Clauses b (fps, resyncs) and e (the guide serves) hold. The control is
comparable.

**What the change did to the stream, read beside the bar.** Against the
adopted state's CONC (E3-S6A), the paced grab cut the stream's loss from
1,312 to 67 / 60 packets/min. Rendered went from 57.6 to 59.8, resyncs
from 52 to 1 / 3, and the per-grab peak from ~27 to ~3.7 lost/s. That is
the largest CONC improvement in E3. The price is a guide cycle about
three times slower, which the bar does not allow.

- One change, behind `PRIVYHUB_EPG_GRAB_NET=paced` (`--delay=4000` to
  the grabber). **NOT ADOPTED**; nothing committed.
- **Task 1's flag (`PRIVYHUB_RECOVERY_TRIGGER`) was absent in every run.**
  E3-R1 was INCONCLUSIVE, so this task relied on the replacement rule.
  All three runs were valid.

**Context:**

- Task: `handoffs/E3-S7_CONC_GRAB_SPAWN_TASK.md`, item 2 of
  `handoffs/QUEUE_2026-10-08.md`.
- **Baseline commit: `def1ad1`.** It ran on the adopted state (live, the
  guide index, Snes9x).
- Files: `e3_s7_2026-10-08/`.
- Timeline (UTC, 2026-10-08):

  | time | what |
  | --- | --- |
  | 04:04 | preconditions held; the probe hook added (dormant) |
  | 04:04-04:30 | the probe, arms A, B, C; B and C invalid (recovery pauses) |
  | 04:30-04:47 | B_r1, C_r1 (valid) |
  | 04:47 | the change applied; the guide settled (no background refresh since the companion's start); pre-run read 6 / 343 |
  | **04:48:26** | **pre-registration hashed** (`5a936d96…dcf4`) |
  | 04:48-06:01:19 | the control, CONC paced ×2; all OK and valid |

## 1. The probe (`probe.md`, `probe_aligned.json`)

Three spawn-only arms, 20 triggers each at 15 s, one PS1-stream session
each, aligned as E3-S6 did:

- **A**: the child as today;
- **B**: the child at idle CPU / I/O priority (E3-S1's flag);
- **C**: the child in its own user + network namespace. This is the
  probe hook `PRIVYHUB_EPG_GRAB_NONET=1`, which prefixes the spawn with
  `/usr/bin/unshare -rn`: unprivileged, no route, loopback down. Its
  start-up runs as today and its fetch fails fast.

| session | valid | 0-2 s loss, lost pkt/s | baseline /s | busiest core at +1..+2 s |
| --- | --- | --- | --- | --- |
| A | yes | **39.8** | 1.6 | 77 % |
| B | **no** (`client_output_silence` 04:20:18Z) | 44.9 | 10.2 | 39-42 % |
| C | **no** (`controller_silence` 04:25:49Z, then saved) | 1.9 | 1.7 | 77-81 % (+2..+3) |
| B_r1 | yes | **3.6** | 1.5 | 38-40 % |
| C_r1 | yes | **3.1** | 2.0 | **79-86 %** |

- **The rule's reading: both** (B_r1 and C_r1 are each ≤ 25 % of A), so
  the change is the network one.
- **Read beside it:**
  - In C the CPU burst is fully there and the loss is not. CPU
    contention alone does not make the peak.
  - The arms are sequential sessions and A was not repeated: link drift
    is a confound. The invalid first B, on a lossy link, showed no
    reduction.

## 2. The change (`patches/E3-S7_GRAB_NET_PACED.md`)

- `companion/plugins/epg.py` `_grab_from_candidate`: with
  `PRIVYHUB_EPG_GRAB_NET=paced`, `--delay=4000` is appended to the
  grabber's arguments. `--maxConnections=1` is today's already. Absent:
  today's arguments. Diff `e3_s7_grab_net_paced.diff`.
- No metadata is downloaded inside the grab today; the child's source
  comes from the adopted index.
- **A correction to the pre-registration's reasoning.** It said the
  library's default 3-s delay already applies, making this "+1 s per
  request". The runs contradict that: the median grab went from 5.6-5.9 s
  (CONC, today) to 14.8 / 15.1 s. Today's grabs evidently do not sleep
  3 s per request; the mechanism is not determined here. The bar was
  judged as written; only that inference was wrong.

## 3. The runs and the bar

From `e3_s7_table.md`, `e3_s7_verdict.json` and `validity.json`
(`e3_s7_analysis.py`). Task 1's flag is absent in every column.

| | control (no flag) | CONC paced r1 | CONC paced r2 | E3-S6A CONC (today's grab) | E2 PS1-STREAM | E2 CONC r1 |
| --- | --- | --- | --- | --- | --- | --- |
| valid (no recovery pause) | yes | yes | yes | yes | yes | yes |
| host CPU % | 12.6 | 14.6 | 14.0 | 22.2 | 11.7 | 20.5 |
| rendered fps | 59.95 | **59.83** | **59.82** | 57.64 | 59.81 | 56.5 |
| video loss/min | 9.0 | **66.7** | **59.6** | 1,312 | 32.3 | 1,622 |
| resyncs; underruns | 0; 23 | 1; 12 | 3; 12 | 52; 11 | 0; 11 | 199; 448 |
| aligned loss 0 / +1 / +2 s (lost pkt/s) | — | 2.0 / 3.9 / 3.6 | 1.0 / 3.6 / 3.3 | 16.3 / 26.9 / 28.7 | — | 34 / 65 / 43 |
| grabs ok / failed, median s | — | **72** / 0, **14.8** | **72** / 0, **15.1** | 230 / 0, 5.6 | — | 208 / 0, 5.9 |
| refreshes per channel (each of 6) | — | **12** | **12** | ~38 | — | ~35 |
| EPG child CPU % / PSS MB | — | 28.7 / 596 | 28.4 / 594 | 85.1 / 486 | — | 79.2 / 484 |
| companion CPU % / PSS end MB | 25.6 / 37.7 | 25.1 / 46.7 | 25.2 / 48.6 | 26.5 / 47.0 | 24.3 / 40.2 | 33.1 / 158 |
| eno1 rx kB/s | 37.1 | 67.9 | 67.7 | 131.9 | 39.3 | 122.0 |
| socket W | 20.1 | 22.1 | 23.5 | 27.0 | 20.4 | 25.9 |

| clause | needed (both CONC runs) | got | holds |
| --- | --- | --- | --- |
| comparability | control 11.69 ± 2; 59.81 ± 0.5 | 12.63; 59.95 | yes |
| a. loss/min | ≤ 100 and ≤ 3 × 9.02 = 27.1 | 66.7 / 59.6 | **no** |
| b. rendered; resyncs | ≥ 59.5; ≤ 10 | 59.83 / 59.82; 1 / 3 | yes |
| c. aligned 0-2 s mean | ≤ 3 × 0.153 = 0.46 | 3.16 / 2.64 | **no** |
| d. grabs failed 0; each channel ≥ 20 refreshes; median ≤ 11.8 s | | 0; **12**; **14.8 / 15.1** | **no** |
| e. the guide serves | 6; 326-360 | 6; 340 | yes |

**Verdict: REJECTED** (a, c, d).

**Read beside the bar:**

- **The per-grab damage fell ~7×** (aligned peak ~3.7 vs ~27 lost/s).
  Grabs ran ~3× less often (72 vs 230), and together the stream's
  loss/min fell ~20×.
- The spacing between the requests matters, not only how many grabs run.
  That fits the probe's "network": a back-to-back burst of requests hurts
  far more than the same requests spread out.
- **What would be tried next (a new task, the user's call):** a shorter
  delay, e.g. 1-1.5 s. It would keep the cycle at ≥ 20 refreshes per
  channel and the median grab ≤ 11.8 s, and show how much of the gain
  survives. The grabber's per-request sleep could also be made explicit
  and measured, since today's effective value is not known.
- The paced child stays alive longer (~15 s), mostly idle: CPU 28.7 %,
  PSS ~595 MB. The host's CPU and socket power fall against E3-S6A's
  CONC (14.3 vs 22.2 %; 22.8 vs 27.0 W).

## 4. What the user would be adopting, and the revert

- **Not on the bar's terms.** If adopted anyway, it is one drop-in line,
  `Environment=PRIVYHUB_EPG_GRAB_NET=paced`. CONC would stream at
  ~60 loss/min and 59.8 fps, and each channel's guide would refresh ~3×
  less often during grab cycles. Ordinary background refreshes are rare,
  so that matters only for forced cycles like E1-CONC's.
- **Revert:** delete the line, `daemon-reload`, restart. Absent = today.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 06:01:19Z):
  - manager none; environ exactly live + the index + Snes9x;
  - no e3 drop-in; no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The probe hook and the flag are absent and dormant.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched,
  nothing deleted.
- **One slip, undone:** while checking the control's validity, I ran
  E3-A2's `e3_a2_validity.py` directly. That script writes its output
  into its own directory, so it rewrote the committed
  `e3_a2_2026-10-07/validity.json`. I restored the file from HEAD at
  once (`git checkout`); that directory is unchanged. This task's
  validity check is in its own `validity.json`.
- Files (`e3_s7_2026-10-08/`):
  - `precondition.json`, `e3_s7_nonet_probe_hook.diff`;
  - `e3_s7_probe.py`, `probe_{A,B,C,B_r1,C_r1}/`,
    `probe_triggers_*.jsonl`, `probe_run_*.json`, `probe_aligned.json`
    (and `probe_aligned_first_pass.json`), `probe.md`, the probe
    consoles;
  - `e3_s7_grab_net_paced.diff`;
  - `guide_read_before.json`, `epg_status_before.json`,
    `guide_read_after.json`;
  - the pre-registration and its `.sha256`;
  - `runs/` (3 runs; `manifest.sha256`, `--check` OK), `runs_console.log`;
  - `e3_s7_analysis.py`, `e3_s7_table.md/.json`, `aligned_ctl/`,
    `validity.json`, `e3_s7_verdict.json`, `redact_check.txt`.
- Git status: `logs/e3_s7_git_status.txt`.
