---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: a56746e
durable_memory_updated: true
---

# E2-S1: the E2 instrumentation (`--e2`), the run plan, and the E1-VOD row

## Purpose

- E2 measures the whole system on the frozen suite, with finer
  instrumentation for the three contended findings
  (`handoffs/E2-S1_WHOLE_SYSTEM_MEASUREMENTS_TASK.md`; record
  `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md`).
- The VOD drive is attached, so the VOD row joins the suite by E1's rule.

**Measurement tools only. Nothing in the adopted system changed.**

## Change

**`tools/e1_sampler.py`:**

- `--e2`, which adds:
  - per-thread rows for the companion, RetroArch, the encoder and the EPG
    child (`threads.jsonl`: tid, % of a core, policy, syscall);
  - the encoder-log tail (`encoder.jsonl`);
  - tx drop counters: softnet, `tc -s qdisc` (read-only), interface
    `tx_dropped`.
- Always: rchar/wchar and `Pss_Anon` / `Pss_File` per category.
- In the summary: per-core p95, the busiest core's p95,
  `throttle_by_value`, the encoder's capture fps and dup/drop per minute,
  and the per-thread table.

**`tools/e1_suite.py`:**

- `--e2` and `--plan`.
- **The E1-VOD row**: launcher navigation, the resume dialog's
  "Start Over", RESTART, fullscreen, the progress ratio, the RESTART +
  STOP teardown, and a check that the mount is read-only.
- Stream rows: the decision-log slice and the decoder report's fields by
  path.
- The check covers only the runs present.
- `ABSENT` loses VOD.

## Validation

- Self-tests pass.
- The VOD smokes (not data) found and fixed two runner defects, both
  before the dry runs:
  - the mount check read the autofs layer;
  - the leftover resume dialog was not handled.
- The E2 smoke (not data) showed the relay-thread rule was ambiguous;
  amendment A1 was made before any run.
- **E1-VOD**: two 5-min dry runs, **REPEATABLE**.
- **E2**: 10 × 20-min runs, all OK, 0 missed samples, `--check` OK, flags
  absent, APK confirmed.

## Rollback

Revert the two tools to `a56746e`. The VOD row is then unavailable, and the
suite amendment would need its own revert.
