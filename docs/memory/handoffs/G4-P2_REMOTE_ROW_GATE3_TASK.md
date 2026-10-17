---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G4-P2 (session B, unattended): the remote row (`tools/e1_remote.py`) records the host-side readings G4-S1's gate 3 needs — RetroArch's FPS counter and the encoder's progress — as the home row does; and reads what G4-S1's run 1 would have shown, from its files where possible. Harness only; no stream
---

# G4-P2 — the remote row's gate 3

Read first: `G4_S1_…` §2 ("Why gate 3 is not evaluable": the title log without the FPS counter; the sampler started without `--e2`; no `encoder.jsonl`), `tools/e1_suite.py` (the home row: the per-run counter override for RetroArch's title, the `--e2` sampler, `encoder.jsonl` and `capture_fps` / `dupdrop_per_min`), `G4_P1_…` §1 (the remote row's steps).

## 1. The change (a patch to `tools/e1_remote.py`, inert for the home row)

- The remote row writes the same per-run RetroArch counter override the home row writes, so `title.txt` carries "FPS / Frames"; starts the sampler with `--e2`; keeps `encoder.jsonl`; and reports `retroarch_fps`, `capture_fps`, `dupdrop_per_min` in the run's summary under the same keys as the home row — so the gates' clauses read unchanged.
- Nothing else in the remote row changes (the endpoint class and hash, `path.jsonl`, the wait, the teardown as G4-P1 built them). The home row (`e1_suite.py` without `--remote`) is byte for byte as today — the dispatch is already guarded; show the masked-hash comparison of its code path.
- Tests: the remote row's existing tests plus one per new field (fixtures); a dry dispatch with `--remote` and no companion must refuse as today.

## 2. What G4-S1 would have read (from its files, stated as far as they allow)

- Run 1 and run 2's `samples.jsonl` carry the host's process samples: say whether the encoder's and RetroArch's CPU are there (the record reports them), and that the FPS counter and the encoder's frame counts are **not** recoverable from those files — so gate 3 for G4-S1 stays NOT EVALUABLE; this task does not rewrite that record.
- The next remote run (G4-S2) is the first with gate 3 readable.

## 3. The record

`evidence/G4_P2_REMOTE_ROW_GATE3_2026-10-17.md` + `g4_p2_2026-10-17/` (the diff, the test output, the masked-hash comparison, `redact_check.txt`, `manifest.sha256`); `patches/G4-P2_…md`; ROADMAP §G4 (a line: "remote row records gate 3 from G4-S2"); `logs/g4_p2_git_status.txt`. Then `SESSION_B_DONE_2026-10-17.md` (ten lines: the three tasks, their records, what is pending on the stream).
