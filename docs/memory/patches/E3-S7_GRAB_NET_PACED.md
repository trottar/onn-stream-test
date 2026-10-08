---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: def1ad1
durable_memory_updated: true
---

# E3-S7: the grabber paced (`PRIVYHUB_EPG_GRAB_NET=paced`, `--delay=4000`) + a no-network probe hook (`PRIVYHUB_EPG_GRAB_NONET=1`)

## Purpose

E3-S7 (`handoffs/E3-S7_CONC_GRAB_SPAWN_TASK.md`, record
`evidence/E3_S7_CONC_GRAB_SPAWN_2026-10-08.md`): the grabber child's
share of the CONC loss. The probe named both CPU and network; per the
task, the change is the network one.

**REJECTED by the bar** (loss and aligned-peak clauses above 3 × the
control; the guide cycle at 12 refreshes per channel, not ≥ 20). It cut
CONC's loss from ~1,300 to ~60 packets/min. NOT ADOPTED.

## Change

`companion/plugins/epg.py` `_grab_from_candidate`:

- **`PRIVYHUB_EPG_GRAB_NET=paced`**: `--delay=4000` appended to the
  grabber's arguments; `--maxConnections=1` already today's. Absent:
  today's arguments. Diff
  `evidence/e3_s7_2026-10-08/e3_s7_grab_net_paced.diff`.
- **`PRIVYHUB_EPG_GRAB_NONET=1`** (measurement only): the spawn is
  prefixed with `/usr/bin/unshare -rn`, so the child runs in its own
  user + network namespace with no route (unprivileged). Absent: today.
  Diff `evidence/e3_s7_2026-10-08/e3_s7_nonet_probe_hook.diff`.

## Validation

`py_compile`. The probe (arms A, B, C, with B and C replaced under the
validity rule) and the benchmark: see the record.

## Rollback

Both flags absent. To remove the code, reverse the two diffs.
