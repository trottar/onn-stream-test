---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
durable_memory_updated: true
---

# E3-S2: `malloc_trim(0)` after each forced EPG refresh, behind `PRIVYHUB_EPG_MALLOC_TRIM=1` (+ a memory probe hook, off)

## Purpose

E3's second item (`handoffs/E3-S2_COMPANION_GUIDE_RETENTION_TASK.md`,
record `evidence/E3_S2_COMPANION_GUIDE_RETENTION_2026-10-06.md`). The
probe found the companion's ~110 MB step to be the allocator's
high-water from the per-grab guide-metadata parse.

**NOT ADOPTED (REJECTED by the bar).**

## Change

`companion/plugins/epg.py`:

- `guide()` is a wrapper over the unchanged body, renamed `_guide()`.
  With `PRIVYHUB_EPG_MALLOC_TRIM=1`, a forced call runs
  `ctypes.CDLL("libc.so.6").malloc_trim(0)` in a `finally`. Absent: it
  returns `_guide()` directly.
- **The measurement hook:** `GET /plugins/epg/memprobe?op=start|snap|trim|gc`,
  served **only with `PRIVYHUB_MEM_PROBE=1`**. Otherwise the action is
  unknown, as today (HTTP 400). It reports tracemalloc's traced memory
  and top files, the `gc` objects by type, and `smaps_rollup`. It stays
  in the tree, off.

Tools: `tools/e3_guide_read.py` (the six channels' cached guide, the
programme total and the cache-file count).

## Validation

- `py_compile`.
- Probe and smoke (not data) with each flag set, then the drop-in
  removed.
- E1-META ×2 with the flag (see the record).

## Rollback

Unset the flags. To remove the code, revert `companion/plugins/epg.py`
to the E3-S1 state (`bde31e0a…ce6e`), or to `d9fdbdd`.
