---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: 969085f
durable_memory_updated: true
---

# E3-S7B: the paced grab's delay as a value, `PRIVYHUB_EPG_GRAB_DELAY_MS` (dormant)

## Purpose

E3-S7B (`handoffs/E3-S7B_GRAB_PACING_SHORT_TASK.md`, record
`evidence/E3_S7B_GRAB_PACING_SHORT_2026-10-08.md`). It runs E3-S7's
grab pacing at a shorter delay: 1,500 ms, chosen by the task's rule after
a spacing probe.

**REJECTED by E3-S7's bar** (loss, fps / resyncs, the aligned frame).
The guide cycle held this time. NOT ADOPTED.

## Change

- **`companion/plugins/epg.py`** `_grab_from_candidate`: with
  `PRIVYHUB_EPG_GRAB_NET=paced`, `--delay=<PRIVYHUB_EPG_GRAB_DELAY_MS>`
  is appended to the grabber's arguments.
  - The default is 4,000, S7's value, so S7's result stays reproducible;
    an unparsable value also gives 4,000.
  - Absent flag: today's arguments.
- Diff: `evidence/e3_s7b_2026-10-08/e3_s7b_grab_delay.diff`.

## Validation

- `py_compile`; `git diff --check`.
- The spacing probe saw `--delay=1000` / `1500` / `4000` on the child's
  command line.
- 3 suite runs (the record).

## Rollback

The flag is absent everywhere. To remove the code, reverse the diff;
`=paced` alone then means 4,000 again, as S7 left it.
