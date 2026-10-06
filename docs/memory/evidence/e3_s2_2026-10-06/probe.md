# E3-S2 probe — what holds the companion's ~110 MB step at the first grab (2026-10-06 04:57-04:59Z)

Measurement before the change. The stream idle, no game. The companion was restarted with
`PRIVYHUB_MEM_PROBE=1` (drop-in, probe only) so that the task's measurement hook
(`GET /plugins/epg/memprobe?op=start|snap|trim|gc`, `companion/plugins/epg.py`, served only with
that flag; it stays in the tree, off) answers. `mem_probe.sh` ran the sequence; `mem_probe.jsonl`
holds every reply. Two forced grabs of `NBC.us@East` (each ran two source attempts, ok, 37
programmes). tracemalloc started just before the first grab.

| point | traced (live Python) MB | traced peak MB | companion PSS MB | Pss_Anon MB |
| --- | --- | --- | --- | --- |
| before grab 1 (fresh restart) | 0.02 | 0.21 | 28.5 | 25.3 |
| after grab 1 | 0.33 | **146.9** | 137.5 | **134.3** |
| 60 s later | 0.34 | 146.9 | 137.5 | 134.3 |
| after grab 2 | 0.35 | 147.1 | 139.3 | 136.1 |
| after `malloc_trim(0)` | 0.35 | 147.1 | **32.9** | **29.7** |
| after `gc.collect()` (0 collected) | 0.28 | 147.1 | 32.1 | 28.9 |

- **The step**: +109.0 MB anon at the first grab (25.3 → 134.3), as E2 saw (+106-114).
- **Retention**: live Python allocations grew by **0.3 MB** = **0.3 %** of the step. The objects by
  type (`gc.get_objects`) are unchanged (dict 2,599, function 5,337, …). Nothing of the guide is kept.
- **Allocator high-water**: during the grab the companion's traced Python heap peaked at **147 MB**:
  the plugin parses the 25.6 MB `guides.json` metadata (`_fetch_guides_metadata`, `json.loads` of
  the whole file, every grab) and frees it on return. glibc keeps the freed heap. **`malloc_trim(0)`
  returned 106.4 MB = 98 % of the step** (anon 136.1 → 29.7).
- **Answer: allocator high-water** (≥ 50 % returned by `malloc_trim`; retention < 50 %). By the task's
  rule the change is `PRIVYHUB_EPG_MALLOC_TRIM=1`: `malloc_trim(0)` after each forced refresh, with
  `MALLOC_ARENA_MAX=2` in the unit's environment for the runs.
- Teardown: the drop-in removed, `daemon-reload`, restart; environ `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`
  only.

**The guide read before the runs** (`guide_read_before.json`, `tools/e3_guide_read.py`, 04:57Z): 6 of 6
channels serving, **341 programmes**, 56 cache files.

**Smoke with the change** (`smoke_flag.txt`, not data): flag + `MALLOC_ARENA_MAX=2`; companion PSS
27.8 → 28.5 → 29.1 MB over two forced grabs (anon 24.7 → 25.8). Drop-in removed after; environ back to
the live default only.
