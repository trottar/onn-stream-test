---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
durable_memory_updated: true
---

# E3-S3: the EPG grabber's node started directly, behind `PRIVYHUB_EPG_DIRECT_NODE=1`

## Purpose

E3's third item (`handoffs/E3-S3_GRABBER_COST_TASK.md`, record
`evidence/E3_S3_GRABBER_COST_2026-10-06.md`).

**NOT ADOPTED (REJECTED by the bar).**

## Change

**`companion/plugins/epg.py`, `_grab_from_candidate`** (the argv only,
+12 lines):

- With the flag, the argv is `<toolchain node>/node --require
  <epg>/node_modules/tsx/dist/preflight.cjs --import
  file://…/tsx/dist/loader.mjs scripts/commands/epg/grab.ts` plus the
  same grab arguments (`args[4:]` of the npm form).
- Same cwd and environment. E3-S1's priority prefix, if set, still wraps
  it.
- Absent = `npm run grab --`, byte for byte.

**Tools:** `tools/e3_children_log.py`, the companion's reaped-children
CPU every 5 s (exact for the grabber chain).

## Validation

- `py_compile`.
- A smoke with the flag (not data): one process, same programme count;
  then the drop-in removed.
- E1-META ×2 (see the record).

## Rollback

Unset the flag. To remove the code, revert the block in
`_grab_from_candidate`.
