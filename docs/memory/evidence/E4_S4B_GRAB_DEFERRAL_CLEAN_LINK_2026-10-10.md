---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1..S5 work)
---

# E4-S4B — grab deferral, on a clean link

**Classification: INCONCLUSIVE (link).** No control in four was clean, so
no flagged run was made (pre-registration §1). E4-S4's verdict (REJECTED on
a, d) stands as recorded. Not adopted (nothing is); the flag is absent.

| control | window (UTC) | loss/min (gate < 10) | rendered (≥ 59.5) | resyncs (≤ 10) | host CPU | clean |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11:01-11:21 | 426 | 59.05 | 25 | 10.9 | no |
| 2 | 11:55-12:15 | **66** | 59.76 | 0 | 11.0 | no (loss) |
| 3 | 12:49-13:09 | 652 | 58.61 | 46 | 11.2 | no |
| 4 | 13:44-14:04 | 109 | 59.60 | 3 | 11.4 | no (loss) |

- **Host-side, every control was the same stream:**
  - RetroArch 59.999 in all four;
  - host CPU 10.9-11.4 % (E4-S1: 10.9);
  - the companion at 25.1-25.6 % of a core;
  - socket 19.9-21.1 W.
- Only the link moved. Controls 2 and 4 passed rendered and resyncs and
  failed on loss alone (66 and 109 against < 10).
- **The night's link** (every stream run of this queue, loss/min):

  | time (UTC) | run | loss/min |
  | --- | --- | --- |
  | 07:12 | E4-S3B control | 218 |
  | 08:51 | E4-S3B CONC at 1536M | 863 |
  | 09:16-10:31 | E4-S5B live SNES | 539 |
  | 10:36 | E4-S5B PS1 with the flag | 39 |
  | 11:01 | E4-S4B control 1 | 426 |
  | 11:55 | E4-S4B control 2 | 66 |
  | 12:49 | E4-S4B control 3 | 652 |
  | 13:44 | E4-S4B control 4 | 109 |

  - D-BASE's warm-state reference is 8.4.
  - No stream run of this queue met D-BASE's loss row, and neither did
    E4-S4's or E4-S5's earlier on 10-10 (the LINK item in
    `docs/KNOWN_ISSUES.md`).
- 4 runs, all valid, 0 replaced attempts; `--check` OK.

**Context:**

- Task: `handoffs/E4-S4B_GRAB_DEFERRAL_CLEAN_LINK_TASK.md`, under
  `QUEUE_2026-10-10B.md` (queue item 3).
- **Baseline: `7331184` plus the uncommitted E4-S1..S5 work**, untouched;
  E4-S3B's and E4-S5B's files and E4-S3B's runner patch beside it.
- Files: `e4_s4b_2026-10-10/`.
- **Timeline (UTC, 10-10):**

  | time | what |
  | --- | --- |
  | **10:57:05** | **pre-registration hashed** (`4623b401…5bea`) |
  | 10:57-11:21 | control 1 |
  | 11:21-11:51 | idle |
  | 11:51-12:15 | control 2 |
  | 12:15-12:45 | idle |
  | 12:45-13:10 | control 3 |
  | 13:10-13:40 | idle |
  | 13:40-14:04 | control 4 |
  | 14:04:37 | the gate closed: INCONCLUSIVE (link) |

## 1. What was pre-registered and what ran

- The clean-link gate (the only addition to E4-S4):
  - the control (E1-PS1-STREAM, no flag, 20 min) is clean if loss/min
    < 10 **and** rendered ≥ 59.5 **and** resyncs ≤ 10;
  - if it is not clean, idle 30 min and run it again, up to 4 controls;
  - if none is clean, the result is INCONCLUSIVE (link), with no flagged
    run.
- The four controls ran and none was clean.
- The flagged runs (CONC ×2 with the flag, CONC ×1 with the flag at
  `CPUQuota=150%`) did not run. Neither did the pre-run guide read (taken
  only after a clean control), and no `pre_guide.json` exists.
- **The flag was never set.** `e3_flag.conf` and `e4_constraint.conf` were
  absent throughout. Each control's teardown read `flags_absent` true.

## 2. If the user adopts it anyway (E4-S4 §3, unchanged; written, not applied)

**One line**, in its own drop-in beside the four:

- the file is
  `~/.config/systemd/user/privyhub-companion.service.d/epg-defer.conf`;
- its contents are `[Service]` / `Environment=PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`;
- then `daemon-reload` + restart;
- the state checks' `ADOPTED` list gains the name.

**Revert:** delete `epg-defer.conf`, `daemon-reload`, restart.

**The alpha spec with the deferral** (E4-S2 §5; memory from E4-S3B):

| | without the deferral (today) | with the deferral |
| --- | --- | --- |
| the stack's CPU-time floor | 400 % (CONC) | **150 %** (a stream; E4-S2's PS1-STREAM; E4-S4's CONC + flag at 150 %: 0 s throttled) |
| proposed CPU | ≥ 6 cores of this speed class | **4 cores of this speed class** |
| the stack's memory, swap off | **1.5G** (CONC: 1G OOM-kills, 1.5G holds at 1,166 MB peak; E4-S3B) | **1G** holds (the grab alone, META: 976 MB peak, 0 events; ~5 % headroom) |
| proposed memory | 1.5 GB for the stack; 8 GB system | 1.25 GB for the stack (~30 % over the grab's peak); 8 GB system |
| the guide | refreshed during play | refreshed when play stops: 6 channels in ~33-37 s (E4-S4) |

**What the deferral has shown so far:**

- E4-S4, on the host: 0 grabber processes and 0 grabs in every flagged
  window, a 6/6 drain with 0 failures, the guide serving, and 0 s
  throttled at 150 %.
- It has not shown stream quality on a clean link. E4-S4's link was lossy;
  tonight's never cleared the gate.
- Adopting on the host evidence, or waiting for a clean night, is the
  user's decision.

## 3. State at the end; files

- **Final state** (`state_at_end.json`, 14:05Z):
  - the four adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game; the PS1 files identical; **APK CONFIRMED**.
- No sudo, no nft, the Opal untouched; nothing fetched; no data deleted.
- E4-S4's analysis and pass-rule copy were copied into this directory
  (`e4_s4b_analysis.py`, `e4_s4b_passrule.py`) and not run in theirs.
- **Files** (`e4_s4b_2026-10-10/`):
  - `precondition.json`, `git_status_at_start.txt`,
    `tools_at_preregistration_sha256.txt`;
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`
    (`e4_s4b_preregistration.draft`, its unfilled draft);
  - `e4_s4b_run.py`, `run_console.log`, `runs_console.log`, `gate.json`
    (the four attempts);
  - `runs/` (4 controls, `manifest.sha256`, `check.txt` OK);
  - `e4_s4b_analysis.py` (its gate-only path → `e4_s4b_verdict.json`,
    `analysis_console.txt`), `e4_s4b_passrule.py` (unused: no flagged
    run), `e4_s4b_controls.py` → `controls.json`, `validity.json`,
    `e4_s4b_table.md`;
  - `state_at_end.json`, `redact_check.txt`.
- No tool changed: no patch record.
- Git status (cumulative): `logs/e4_s4b_git_status.txt`.
