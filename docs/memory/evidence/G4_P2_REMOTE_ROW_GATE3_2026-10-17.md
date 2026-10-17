---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d
---

# G4-P2 — the remote row's gate 3

**Classification: BUILT (harness only); tested; NOT RUN off-site; NOT ADOPTED;
nothing committed.** `tools/e1_remote.py` now records the host-side readings
G4-S1's gate 3 lacked, as the home row records them:

- RetroArch's FPS counter, through the home row's per-run override;
- the encoder's progress, through the sampler's `--e2` and `encoder.jsonl`;
- `retroarch_fps`, `capture_fps` and `dupdrop_per_min`, reported as the gates'
  clauses read them.

The home row is byte for byte as HEAD: `e1_suite.py` and `e1_sampler.py` were not
edited, which the file and masked AST hashes show. **G4-S1's gate 3 stays NOT
EVALUABLE from its files** (§2). G4-S2 is the first remote run with gate 3
readable.

- Task: `handoffs/G4-P2_REMOTE_ROW_GATE3_TASK.md`, queue item 3, session B,
  unattended. **Baseline `1dab25d`.** G5-S3 / G5-S4's uncommitted work sits
  beside it, in other files.
- The change was written and hashed before the code:
  `g4_p2_2026-10-17/change_written_before_code.md`, sha256 `00355fa4…61f2`,
  00:47:22Z.
- No stream, no game, no adb, no companion restart. No test touches the real
  companion or the real RetroArch config tree: the fake suite's override path is
  a temp directory.

## 1. The change (`tools/e1_remote.py`)

**What the home row does** (`e1_suite.run_once`, `e1_sampler`):

- it writes `COUNTER` (+ `E1_COUNTER_EXTRA`) to `TEKKEN["override"]` before the
  run, refuses if a file is there, and removes it at teardown;
- the sampler's `--title` writes RetroArch's title with "FPS / Frames" to
  `title.txt`;
- `--e2` adds `encoder.jsonl`;
- `key["retroarch"] = host["retroarch"]` (`frames_per_s`).

**How the gates read those files** (the E4-S5D / CL-B3 analyses):

- `retroarch_fps = key.retroarch.frames_per_s ≥ 59.9`;
- `capture_fps` (60 ± 0.1) and `dupdrop_per_min` (≤ 0.2) from E4-S5's `segcap`
  over the run directory's `encoder.jsonl`.

**The remote row now does the same:**

- **The same override.** Same path, same content, same `E1_COUNTER_EXTRA`, same
  refusal. It is written after the preflight and before the sampler.
- **The sampler** gets `--e2`; `encoder.jsonl` is kept in the run directory.
- **The summary's `key`:**
  - `retroarch`, the home row's own key;
  - `gate3` = `{retroarch_fps, retroarch_titles, capture_fps, dupdrop_per_min}`,
    computed as the clauses compute them. `segcap` is re-implemented in
    `e1_remote.py`, and a test asserts it equals E4-S5D's on a fixture with a
    counter reset and a 3-s hole.
- **Unchanged:** the endpoint class and hash, `path.jsonl`, the wait, the
  refusals, the rest of the teardown.

**Two things to know:**

- **The override is per game.** It applies only when the user starts the
  PS1-STREAM fixture, Tekken 3 (USA). A run of another title gets `titles: 0`
  and gate 3 reads `None`, visibly. One log line at the wait says so; the
  existing wait line is unchanged.
- **A deliberate difference from the home row.** The remote row removes the
  override **only if this run wrote it** (`counter_override: set`). The home
  row's `finally` unlinks the path unconditionally, so after refusing to
  overwrite an existing file it would delete that file. Not changed in
  `e1_suite.py`: not this task, and the home row stays byte for byte. Listed for
  the user.

**Not added:** the home row's cgroup poller (`--e2`'s `cgroup.jsonl`). The task
asks for the sampler's `--e2` and `encoder.jsonl` only.

## 2. Verification

**Tests** (`tests_output.txt`): `(cd tools && python3 -m unittest test_e1_remote -v)`
→ **20 OK**: the 13 existing and 7 new.

- The fake suite gains the override constants at a temp path. The existing tests
  need that, because the row now reads `E.TEKKEN` / `E.COUNTER`.
- **The 7 new tests:**
  - the override is written (it holds `COUNTER` while the sampler starts) and
    removed (`counter_override_removed: true`), with the per-game log line;
  - `E1_COUNTER_EXTRA` is appended as the home row appends it;
  - a refusal over an existing file leaves that file intact and reports no
    removal;
  - the sampler's argv ends `--telemetry --title --e2`;
  - `key.retroarch` and `key.gate3` are present, `None` without fixtures;
  - from fixtures (`title.txt` with the counter at 60 frames/s; `encoder.jsonl`
    with a dup, a reset and a hole): `retroarch_fps` 60.0, `capture_fps` 60.0,
    and `segcap` equal to E4-S5D's;
  - **a dry dispatch with `--remote` and no companion** (`mainpid` None) refuses
    as today with "refusing: --remote needs…", writes no output directory, and
    writes no override.
- Unchanged and passing: the dispatch is guarded (AST), and a dispatch without
  `--prereg` refuses.
- The `ResourceWarning` in the output is HEAD's own line (`open()` inside the
  sampler's `Popen` call), not this change.

**The home row, byte for byte** (`home_row_masked_hash.py` →
`home_row_masked_hash.txt`):

| file | file sha256, HEAD vs today | per-function masked AST hash |
| --- | --- | --- |
| `tools/e1_suite.py` | identical (`3dcc355d…`) | `main` (its `--remote` branch masked), `run_suite`, `run_once`, `preflight`, `stop_game`, `heartbeat_figures`, `telemetry_figures`, `poll_figures`, `decision_rows`: all identical |
| `tools/e1_sampler.py` | identical (`adc5d5ec…`) | `run`, `summarize`, `e2_extras`, `encoder_loop`, `title_loop`, `ra_fps`, `host_loop`: all identical |

## 3. What G4-S1 would have read (`g4_s1_gate3_read.py` → `g4_s1_gate3_read.json`)

| | run 1 | run 2 |
| --- | --- | --- |
| sampler mode (`sampler_meta.json`) | `--title`, **no `--e2`** | the same |
| `title.txt`: title lines / with the FPS counter | 20 / **0** | 76 / **0** |
| `encoder.jsonl` | **absent** | **absent** |
| host process CPU in `samples.jsonl` (window means, % of a core) | RetroArch 34.9, encoder 44.7, companion 24.5 (as G4-S1 reported) | RetroArch 37.1, encoder 42.8, companion 18.5 |
| the fixed row's reader (`e1_remote.gate3_figures`) over the run directory | `retroarch_fps` None (0 titles), `capture_fps` None, `dupdrop_per_min` None | the same |

- **What the samples do and do not hold.** `samples.jsonl` carries the host's
  process samples (CPU, RSS), so the encoder's and RetroArch's CPU are there.
  RetroArch's FPS counter and the encoder's frame / dup / drop counts are
  **not** in those files and cannot be recovered from them. The counter was
  never in the title, and the encoder's progress was never tailed.
- **So G4-S1's gate 3 stays NOT EVALUABLE.** This task does not rewrite G4-S1's
  record.
- **The next remote run (G4-S2)** is the first with gate 3 readable, provided
  the user plays the fixture.

## 4. Files; disclosures

- **`g4_p2_2026-10-17/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `change_written_before_code.md` / `.sha256`;
  - `g4_p2.diff`;
  - `tests_output.txt`;
  - `home_row_masked_hash.py` / `.txt`;
  - `g4_s1_gate3_read.py` / `.json`;
  - `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G4-P2_REMOTE_ROW_GATE3.md`.
- ROADMAP §G4: the G4-P2 line.
- `logs/g4_p2_git_status.txt`.
- Not written: `CURRENT.md`, `CURRENT_HANDOFF.md`, `KNOWN_ISSUES.md`,
  `PATCH_INDEX.md`.
- **Read only:** G4-S1's run directories.
- Nothing deleted, nothing fetched. No sudo, no nft, the Opal untouched. No
  address or identifier: the tests' addresses are built from integers, and the
  fixtures' times from an integer epoch.
