---
memory_schema: 1
as_of: 2026-09-24
baseline_commit: 4e82298
durable_memory_updated: true
---

# C3-L3A-P2R3 — `--aggregate` pools only pre-registered rerun sessions

## Purpose

Make the `C3.L3a` pooling rule explicit — v2 state and the pre-registered
config, every other file listed as skipped with its reason — and move the
2026-09-20 run files out of the pool, so a smoke run or a re-scored older
session can never enter the rerun's pooled table. Task:
`handoffs/C3-L3A-P2R3_TASK.md`, authorized by the user 2026-09-24. Record:
`evidence/C3_L3A_P2R3_POOLING_RULE_2026-09-24.md`.

**Tools and documentation only.** No companion, client, profile, route or
environment change; no session run.

## Expected predecessor

`4e82298` plus the uncommitted `C3-L3A-P2R1` / `P2R2` working tree (probe
SHA-256 `b1e69245…719c`).

## Changed scope

| file | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `tools/probe_c3_l3a_gameplay_acceptance.py` | `b1e69245a2c70d00d27f18027d7124bd951b6768822e1269336baa6c2769719c` | `f574c2563e0b5f45578f51677177c294effc55d245c4a7befddaa0dabe903641` |

Also in `evidence/c3_l3a_p2r3_2026-09-24/{pre,post}_patch_sha256.txt`.

- `PREREGISTERED_CONFIG` (traversals 10, dwell 55 / 90 s, W 5.0 s, ramp gap
  4.0 s, park 45 s); the CLI defaults read from it.
- `pool_decision()` — the reasons a finalized run may not be pooled
  (analysis schema, state schema, each differing config field).
- `aggregate()` — pools only runs with no reasons; lists POOLED / SKIPPED
  with reasons in the report (`=== POOL ===`), on stdout and in the JSON
  (`files`, `pool_rule`); an empty pool writes the report and exits 0;
  `--pool-all` pools v2-analysis runs regardless, with " - POOL-ALL
  OVERRIDE" in the title and a WARNING line directly under the header.
- Run path: a blank line before the rating anchors and after the rating
  answer (teed-log readability); prompt and anchor text byte-identical.

Moved (byte for byte): `logs/streaming/c3_l3a_runs/20260920_010023.{json,txt}`
→ `evidence/c3_l3a_p2r1_2026-09-23/refinalized_p2r2/`.

Memory: `docs/KNOWN_ISSUES.md` (controller `lost_packets` under play, open),
`CURRENT.md`, `TOOLS.md`, `2026-09-24.md`, `investigations/ACTIVE.md`;
generated `patches/PATCH_INDEX.md`.

## Validation performed

- `py_compile`;
- `--aggregate` on the empty pool: 0 / 0 / 0, exit 0, stated in the report;
- temporary copies of the smoke and 2026-09-20 runs: default pools neither,
  skips both with the expected reasons; `--pool-all` pools both with the
  warning; copies removed, pool empty;
- `--plan` 8 / 10 identical to P2R1's output;
- smoke `--finalize` JSON byte-identical to P2R2's `after_fix/` (text:
  `Generated:` only);
- inputs' SHA-256 unchanged; `tools/check_memory_health.py` healthy; LF,
  trailing newline.

**Not exercised:** the run-path newlines (interactive; no session).

## Negative results

- `--pool-all`'s warning cannot sit inside the header block without
  changing `manual_checkout.Report` (out of scope; the block is
  load-bearing), so it is in the title and the first body line.
- The task named one newline; a second (after the answer) was needed for
  the stated result.

## Result

INSTALLED SUCCESSFULLY (tools, documentation). `C3.L4` stays BLOCKED.
