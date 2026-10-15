# E4-S3B — a driver fault, fixed mid-task (bookkeeping only)

- **The fault.** `e4_s3b_ladder.py`'s `latest_summary()` looked for an
  unconstrained run in `runs/<row>_/`. The suite writes it to `runs/<row>/`.
  So the control (E1-PS1-STREAM, unconstrained) ran normally (07:08-07:32Z,
  PLAYING, its full 20-min window) but was recorded as "never ran", and
  `ladder.json`'s control loss was `None`. With it the 1G runs would have
  been judged without the pre-registered link clause.
- **What was done** (07:33-07:34Z, during step `mem:1G`'s idle gap):
  - The driver process alone was stopped (SIGTERM). The suite invocation it had
    started (CONC + META at 1G) ran on untouched.
  - The pre-fix driver is kept as `e4_s3b_ladder_as_preregistered.py`. Its
    sha256 is the one in the pre-registration.
  - The fix in `e4_s3b_ladder.py`:
    - `latest_summary()` reads `runs/<row>/` for an unconstrained run;
    - `repair-control` re-reads and re-judges the control's record;
    - `record <label>` judges and records a step the suite ran while the
      driver was stopped (`run_step`'s second half, `judge_step`).
  - `repair-control` ran at 07:34Z: control loss/min **218.23**, rendered
    59.48. That is INCONCLUSIVE on its own reading, and the link fails
    D-BASE's row.
  - The driver's 60-s constraint read-back for `mem:1G` continued from
    `readback_standin.py` (the same fields, tagged `source`) until the
    suite exited.
  - `record mem:1G` then ran, followed by `run` (resumed from `ladder.json`).
- **No pass rule, step, row, window or reading changed.** The judging code is
  the pre-registered one; only the file lookup and the step bookkeeping
  changed.
