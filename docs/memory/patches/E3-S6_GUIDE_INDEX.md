---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: bf2120c
durable_memory_updated: true
---

# E3-S6: a cached slim guide index, behind `PRIVYHUB_EPG_GUIDE_INDEX=cached` (+ the probe hook's grab-half ops)

## Purpose

E3-S6 (`handoffs/E3-S6_GUIDE_INDEX_TASK.md`, record
`evidence/E3_S6_GUIDE_INDEX_2026-10-07.md`): the per-grab parse of the
25.6 MB guide metadata in the companion's process.

**MEMORY ACCEPTED, STREAM REJECTED. NOT ADOPTED (the user's decision).**

## Change

**`companion/plugins/epg.py`:**

- **`_guide` (inside `_grab_lock`):** with the flag, `candidates =
  self._candidate_mappings(channel_id, self._guide_index_rows(channel_id))`.
  Absent: today's `_fetch_guides_metadata()` + `_candidate_mappings`.
- **`_guide_index_rows`** (new):
  - the index keyed by the metadata file's size + `mtime_ns`, valid within
    the file's 24-h TTL;
  - in-process (`self._guide_index`), then the saved
    `data/epg/metadata/guides_index.json`;
  - otherwise built from today's `_fetch_guides_metadata()`: per
    canonical channel the rows' six fields, packed with `\x1f` / `\x1e`;
    saved atomically; then `gc.collect()` + `malloc_trim(0)` once;
  - it returns the channel's rows as dicts, so `_candidate_mappings` is
    unchanged.
- **The probe hook** (`PRIVYHUB_MEM_PROBE=1` only): `memprobe` gains
  `op=parse | prepare | spawn | cands` (`_grab_half_probe`).

## Validation

- `py_compile`.
- The smoke: identical candidates by both paths for the six suite
  channels.
- The probe; the benchmark (see the record).

## Rollback

Unset the flag; optionally delete `data/epg/metadata/guides_index.json`.
To remove the code, revert the `_guide` branch, `_guide_index_rows` /
`_guide_index_file` / `_GUIDE_INDEX_FIELDS`, and `_grab_half_probe`.
