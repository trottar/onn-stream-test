---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B1.10 forward-retention blocker result

Fresh classification:

`B1_RETENTION_BLOCKER_CONTEXT_CAPTURED`

Forward runtime history:
- total: 322.048 MiB;
- limit: 256.000 MiB;
- existing eligible deletion: 8.870 MiB;
- projected under B1.9 policy: 313.178 MiB;
- blocked by protected evidence: true.

Protected footprint:
- 43 files / 313.178 MiB;
- 35 files / 259.808 MiB protected only by summary extension;
- 8 newest files / 53.370 MiB.

The dominant blocker is five old `pktmon_full.txt` packet-capture text dumps,
each roughly 51.8–51.9 MiB, protected solely because `.txt` is globally treated
as a summary extension. A sixth newest `pktmon_full.txt` remains protected by
the newest-minimum rule.

Conclusion:

Do not remove `.txt` protection globally. Add one explicit raw-name override for
`pktmon_full.txt`. Keep newest-minimum protection first, so the newest packet
capture remains preserved. Keep summary/failure protections for all other text
evidence. Re-run retention as dry-run before any apply.
