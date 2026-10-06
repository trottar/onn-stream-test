---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
---

# E3-S2 — the companion's memory after a grab: `malloc_trim` after each forced refresh

**Classification:**

- **REJECTED by the pre-registered bar**, on clause (a) alone. The
  companion's PSS at the window's end was 155.3 / 155.7 MB against the
  ≤ 60 MB bar.
- The other four clauses hold.
- One change behind `PRIVYHUB_EPG_MALLOC_TRIM=1`, with
  `MALLOC_ARENA_MAX=2` for the runs. **NOT ADOPTED; nothing committed.**
  The flag is absent at the end; E2's final state is restored.

**Context:**

- Task: `handoffs/E3-S2_COMPANION_GUIDE_RETENTION_TASK.md`, queue item 2.
- Baseline commit: `d9fdbdd`.
- Files: `e3_s2_2026-10-06/`.
- E3-S1's flag is absent: nothing compounds. Its code and this task's
  probe hook stay in the tree, dormant.
- Timeline (UTC, 2026-10-06):

  | time | what |
  | --- | --- |
  | 04:57 | preconditions held (`precondition.json`); the guide read before |
  | 04:57-04:59 | the probe |
  | 05:00 | the change and a smoke (not data) |
  | **05:00:46** | **pre-registration hashed** (`3b13d060…4d61`) |
  | 05:00:51-05:47:14 | E1-META ×2 with the flag, both OK first time |

## 1. The probe (`probe.md`): allocator high-water, not retention

| point | live Python MB (tracemalloc) | companion Pss_Anon MB |
| --- | --- | --- |
| before the first grab | 0.02 | 25.3 |
| after it (and 60 s later) | 0.33 | **134.3** |
| after a second grab | 0.35 | 136.1 |
| after `malloc_trim(0)` | 0.35 | **29.7** |

- **The step is +109 MB.** Live Python objects hold 0.3 % of it.
  `malloc_trim` returns **98 %**.
- **Where it comes from:** every forced refresh parses the whole 25.6 MB
  guide-metadata file (`_fetch_guides_metadata`, `json.loads`). That is a
  **147 MB** traced peak. The list is freed when the refresh returns, and
  glibc keeps the heap.
- By the task's rule the change is `PRIVYHUB_EPG_MALLOC_TRIM=1`.

## 2. The change (`patches/E3-S2_EPG_MALLOC_TRIM.md`)

- `companion/plugins/epg.py`: `guide()` is now a wrapper over the
  unchanged body, renamed `_guide()`.
- With the flag, a forced `guide()` calls `malloc_trim(0)` as it returns
  (a `finally`).
- The runs' drop-in also carried `MALLOC_ARENA_MAX=2`.
- Absent = today's call path; the wrapper returns `_guide()` directly.
- The measurement hook (`/plugins/epg/memprobe`, served only with
  `PRIVYHUB_MEM_PROBE=1`) stays in the tree, off.
- Diff: `e3_s2_malloc_trim_change.diff`; the full diff against
  `d9fdbdd` is `e3_s2_epg_full_vs_d9fdbdd.diff`.

## 3. The runs and the bar

From `e3_s2_table.md`; the verdict is in `e3_s2_verdict.json`.

| | META r1 (flag) | META r2 (flag) | E2 META |
| --- | --- | --- | --- |
| companion PSS first → last of the window MB | 153.8 → **155.3** | 151.8 → **155.7** | 133.7 → 161.0 |
| companion anon first → last MB | 152.0 → 153.5 | 149.9 → 153.9 | 131.8 → 159.1 |
| companion PSS min / median / max in the window MB | 137 / 155 / 249 | 135 / 156 / 241 | — |
| last-15-min growth % (keeps growing > 5) | 1.7 | 1.9 | **22.0** |
| grabs ok / failed, median s | 233 / 0, 5.2 | 239 / 0, 5.2 | 228 / 0, 5.2 |
| host CPU mean % | 10.2 | 10.4 | 9.8 |
| companion CPU % | 7.7 | 8.0 | 7.6 |
| EPG child CPU % / PSS MB; peak per grab median | 71 / 483; 648 | 73 / 476; 648 | 67 / 486; 651 |

| clause | needed | got | holds |
| --- | --- | --- | --- |
| a. PSS at the window's end | ≤ 60 MB, both runs | 155.3 / 155.7 | **no** |
| b. not "keeps growing" | ≤ 5 %, both | 1.7 / 1.9 | yes |
| c. grabs | failed 0, ok ≥ 205, median ≤ 6.8 s | 233/0, 5.2; 239/0, 5.2 | yes |
| d. the guide serves | 6 channels; 341 ± 5 % | 6; 342 | yes |
| e. host CPU | 9.8 ± 2 | 10.2 / 10.4 | yes |

**Verdict: REJECTED.**

**Why the trim did not lower the row:**

- In E1-META the grabs run back to back.
- **The 147 MB metadata list is live for the whole of each grab**, not
  only during the parse. The plugin holds it while the node grabber runs
  (the candidate loop keeps the list in scope).
- So in this row the ~150 MB is live memory for ~99 % of the window:
  - the trim frees it for the milliseconds between one refresh's return
    and the next request's parse;
  - the 1-s sampler never saw the companion below 135 MB in either window.
- The probe's classification was right for the time after a grab, but
  not for a continuous grab cycle. That was not foreseeable from the
  probe's two isolated grabs.

**What the change did do (reported, not gated):**

- The PSS no longer ratchets: it plateaued at ~155 MB against E2's 161
  and +22 %.
- Outside the cycle, a single grab followed by the trim leaves the
  companion at ~29-30 MB (the probe and the smoke). In ordinary use grabs
  are occasional, so the companion would sit near its pre-grab size
  between them. **This is not what the bar measured**, and it does not
  change the verdict.

**A sharper hypothesis for later, not tested:** the per-grab work is the
25.6 MB metadata parse. It runs in the companion's own Python process
for every grab:

- 147 MB live during each grab;
- CPU and the GIL at each grab's start.

A cached, slim channel → source index (parsed once per metadata TTL)
would address this row's PSS. **It may also be E3-S1's unexplained loss
peak at +1 s:** the companion's stream threads are Python threads in the
same process. This is a new, untested hypothesis for the user's E3 list.

## 4. What the user would be adopting, and the revert

- **Adoption, if wanted despite the verdict:** two lines in the unit's
  drop-in, `Environment=PRIVYHUB_EPG_MALLOC_TRIM=1` and
  `Environment=MALLOC_ARENA_MAX=2`. Not recommended on the bar's
  evidence.
- **Revert:** delete the lines, `daemon-reload`, restart.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 05:47:14Z):
  - manager `PRIVYHUB_*` none;
  - environ exactly the live default;
  - the e3 drop-in absent; `MALLOC_ARENA_MAX` absent (teardown check);
  - no game; the PS1 files identical; **APK CONFIRMED**.
- No `nft`, no `sudo`, the Opal untouched.
- Files (`e3_s2_2026-10-06/`):
  - `precondition.json`, `probe.md`, `mem_probe.sh`, `mem_probe.jsonl`,
    `smoke_flag.txt`;
  - `guide_read_before.json` / `guide_read_after.json`;
  - the pre-registration and its `.sha256`; the two diffs;
  - `runs/` (2 runs, `manifest.sha256`, `--check` OK);
  - `e3_s2_table.md/.json`, `e3_s2_verdict.json`, `redact_check.txt`.
- Git status: `logs/e3_s2_git_status.txt`.
