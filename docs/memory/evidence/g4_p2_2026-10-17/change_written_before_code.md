# G4-P2 — the remote row's gate 3: the change (written before the code)

Baseline `1dab25d` (G5-S3 / G5-S4 uncommitted beside it, not in these files).
Task: `handoffs/G4-P2_REMOTE_ROW_GATE3_TASK.md`.

## What the home row does (read from `tools/e1_suite.py`, `tools/e1_sampler.py`)

- `run_once` writes the per-run counter override for the workload's game:
  `TEKKEN["override"]` (`<RetroArch config>/Beetle PSX HW/Tekken 3 (USA).cfg`) gets
  `COUNTER` (+ `E1_COUNTER_EXTRA` lines if set). It refuses if a file already sits
  there, and removes it at teardown (`counter_override_removed`). So RetroArch's
  title carries "FPS / Frames", which the sampler's `--title` writes to `title.txt`.
- With `--e2` the sampler also tails the encoder's progress into `encoder.jsonl`.
- The summary: `host = S.summarize(...)` holds `retroarch` (`frames_per_s` from
  the title counter) and, when `encoder.jsonl` exists, `encoder` (`capture_fps`,
  `dup_per_min`, `drop_per_min`); `key["retroarch"] = host["retroarch"]`.
- The gates' clauses (E4-S5D / CL-B3 analyses):
  - `retroarch_fps = key.retroarch.frames_per_s >= 59.9`;
  - `capture_fps` and `dupdrop_per_min` from E4-S5's `segcap` over the run
    directory's `encoder.jsonl` (60 ± 0.1; <= 0.2 / min).

## The change: `tools/e1_remote.py` only

1. Before the sampler starts: the same counter override, at the same path, with
   the same content, and the same refusal if a file is there. Teardown removes it on
   every exit path (`counter_override_removed`).
   - The override is per game: it applies when the user starts the PS1-STREAM
     fixture (Tekken 3).
   - One added log line says so at the wait. The existing wait line is
     unchanged.
2. The sampler is started with `--e2`, so `encoder.jsonl` is written in the run
   directory and kept. The home row's cgroup poller is not part of the task and
   is not added.
3. The summary: `key["retroarch"] = host.get("retroarch")` (the home row's key), and
   `key["gate3"] = {"retroarch_fps", "capture_fps", "dupdrop_per_min"}`. These are
   computed as the gate clauses compute them: `frames_per_s`, and E4-S5's
   `segcap`, re-implemented here verbatim in effect. A test asserts it equals
   E4-S5D's function on the same fixture.
4. Nothing else changes: the endpoint class / hash, `path.jsonl`, the wait, the
   teardown, the refusals.
   - `e1_suite.py` and `e1_sampler.py` are not edited, so the home row is byte
     for byte by construction.
   - Shown by whole-file hashes and a masked AST hash of the home row's
     functions (`main` with its guarded `--remote` branch masked; `run_once`,
     `run_suite`, the sampler's `run` / `summarize` / `e2_extras`), HEAD vs
     today.

## Tests

- The existing ones.
- Per new field: the override written and removed (a fake path); the refusal
  when a file sits there; `--e2` on the sampler's argv; `key.retroarch` and
  `key.gate3` from fixtures (`title.txt` with the counter, `encoder.jsonl`); gate 3
  `None` when the fixtures are absent.
- A dry dispatch with `--remote` and a fake companion without the flags refuses
  as today. No test reaches the real companion or the real RetroArch tree.

## §2 of the task

What G4-S1's run 1 / run 2 files hold for gate 3, stated from the files. G4-S1's
gate 3 stays NOT EVALUABLE, and its record is not rewritten.
