---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 7331184 (E4-S1..S5C uncommitted; this task's files beside them)
---

# E4-S5D — the SNES capture fix, ADOPTED

**Classification: ADOPTED; CONFIRMED on its host-side gates** (every gate of both runs held; `e4_s5d_verdict.json`: CONFIRMED).
The user decided this on 2026-10-15, on E4-S5, S5B and S5C. **The
companion now sets its encoder's output rate to the profile's 60 fps**
(`-r 60`). It no longer uses x11grab's probed input rate.

- The adoption is the drop-in `snes-capture.conf`, which sets
  `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`.
- It is the fifth adopted line.
- No code changed. The flag's code is E4-S5's.

Task: `handoffs/E4-S5D_SNES_CAPTURE_FIX_ADOPTION_TASK.md`, session A item 1
of `QUEUE_2026-10-15.md`. Files: `e4_s5d_2026-10-15/`.

## 1. The adoption

- **Precondition** (`precondition.json`, 20:55Z): the four-line adopted state. No flag, no
  constraint, no game, no RetroArch, no encoder. PS1 files identical; APK
  CONFIRMED.
- **Pre-registration** written and hashed before the drop-in
  (`e4_s5d_preregistration.txt`, `.sha256`, `preregistration_hashed_at.txt`).
- **The drop-in**:
  `~/.config/systemd/user/privyhub-companion.service.d/snes-capture.conf`.
  Its text is in `snes-capture.conf.txt`:

  ```
  [Service]
  Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate
  ```

  Then `systemctl --user daemon-reload` and a restart. MainPID serves
  8765 (`restart.json`).
- **The environment read back** (`env_before.txt` / `env_after.txt`):
  four `PRIVYHUB_*` lines before, then **five**: live, cached,
  `RECOVERY_TRIGGER=v2`, `SNES_CAPTURE_FIX=output_rate`,
  `SNES_CORE=snes9x`.
- **The state checks:** the `ADOPTED` list lives in `tools/e1_suite.py`.
  `tools/e3_state.py` imports it.
  - `ADOPTED` gains `SNES_CAPTURE`.
  - The preflight gains `drop_in_snes_capture` and requires it.
  - `e3_state.py`'s docstring names the five lines.
  - The diff is `e1_suite_adoption.diff`; the predecessor is kept as
    `predecessor_e1_suite.py.txt`.
  - `tools_at_preregistration_sha256.txt` hashes the tools before the
    change, `tools_after_adoption_sha256.txt` after it.
  - `e3_state.py` passes on the new state (`check_after_adoption.json`,
    `ok: true`, five lines).
- **The revert:**
  1. Delete `snes-capture.conf`.
  2. `systemctl --user daemon-reload`.
  3. `systemctl --user restart privyhub-companion`.
  4. Take the `SNES_CAPTURE` line out of `ADOPTED` and the preflight
     (`predecessor_e1_suite.py.txt`).

  The kill switch is the drop-in's absence.

## 2. The confirmation runs (`tools/e1_suite.py --e2`, sidecar-free, gap 120 s)

| run | capture fps | dup+drop /min | encoder starts: input tbr → output fps (-r) | RetroArch | host CPU % | rendered* | loss/min* | resyncs* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SNES-STREAM, 20 min (21:01-21:21Z) | **59.964** | **0.05** | 60 → 60 (-r 60); 60 → 60 (-r 60) | **59.999** | **7.81** (band 7.4 ± 2) | 57.73 | 1,006 | 54 |
| PS1-STREAM, 10 min (21:26-21:36Z) | **59.942** | **0.10** | 1000k → 60 (-r 60) | 59.999 | 12.38 (not gated) | 53.33 | 3,349 | 108 |

\* The link: reported, not gated.

- **SNES gates, all hold:**
  - `-r 60` was in the encoder's argv at both encoder starts (launch
    attempt 2, so two starts).
  - Capture was 60.0 ± 0.1.
  - Dup+drop was ≤ 0.2/min.
  - RetroArch was ≥ 59.9.
  - Host CPU was within E1's band of E4-S1's 7.4 %.
- **PS1 gates:** capture 60.0 ± 0.1 and dup+drop ≤ 0.2/min both hold. PS1's window gets no estimate (`1000k tbr`), so it falls back to `-framerate 60`; the `-r 60` changes nothing for it, as E4-S5B showed.
- **What this run does and does not show:**
  - Both SNES encoder starts probed **60** tonight, so the fix was not
    exercised on a bad probe in this run.
  - The run shows that the adopted state streams SNES at 60 with no drops
    and no host cost.
  - That the fix removes the drops on a bad probe is E4-S5C's evidence:
    4 / 4 bad probes, 0 drops, in the companion's sink mode.
- **The link:** loss 1,006/min, rendered 57.7, a 15.6-s max output gap.
  The bad link of 10-09/10 continues tonight. Host-side the run was clean
  (socket 15.9 W).

Files: `runs/` (`E1-SNES-STREAM/run1/`, `E1-PS1-STREAM/run1/`,
`manifest.sha256`, `check.txt`), `e4_s5d_analysis.py` (E4-S5's
segment-aware `segcap`; tbr and `-r` from `native_video_alpha.log` from the
byte offset in `alpha_log_offset_snes.txt`), `e4_s5d_table.md`,
`e4_s5d_verdict.json`, `validity.json`, `redact_check.txt`,
`git_status_at_start.txt`.

## 3. State at the end

**The five-line adopted state** (`state_at_end.json`). No flag, no
constraint, no game. PS1 files identical. APK CONFIRMED. The watch
(E4-S4D) runs on this state. Nothing committed: the user commits tonight,
everything since `7331184`.
