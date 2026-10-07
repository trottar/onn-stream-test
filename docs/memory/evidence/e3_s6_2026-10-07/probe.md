# E3-S6 probe — which half of a grab the live stream feels (2026-10-07 01:33-01:52Z)

Measurement before the change. The probe hook (`/plugins/epg/memprobe`, served only with `PRIVYHUB_MEM_PROBE=1`)
was extended by this task with `parse` (the guide-metadata parse alone, `_fetch_guides_metadata`, the result
discarded, no child), `prepare` (one channel's candidates, kept), `spawn` (the grabber child for the prepared
candidate, no parse, no cache write) and `cands` (a channel's candidates by today's parse and by the index):
`e3_s6_probe_hook.diff`. `e3_s6_probe.py` started a PS1 stream (E1-PS1-STREAM's launch) with the hook's flag
(drop-in, probe only) and the 1-s sampler (`--e2 --telemetry`, `probe_sampler/`), 60 s settle, 60 s quiet, then
**parse ×20, prepare ×1, spawn ×20, parse ×20**, each 15 s after the previous started (`probe_triggers.jsonl`),
then E1's teardown (environ the live default, APK CONFIRMED, PS1 files identical). The alignment is
`probe_aligned.json` (e2_analysis.py's heartbeat loss series and the busiest core, by offset from each trigger).

**The reading rule (the task's, written before):** an operation reproduces the peak if its mean lost packets/s
at offsets 0-2 s is ≥ 3 × the stream's baseline loss/s (the same window, seconds outside 0-10 s after any
trigger).

| mean over triggers, by s after the trigger | 0 | 1 | 2 | 3 | 4 | 5-10 | baseline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **parse ×40**: lost packets/s | 40.8 | **80.5** | 44.9 | 2.6 | 0.1 | 0.17-0.37 | **0.174** (311 s) |
| parse: busiest core % | 27.0 | 33.3 | 24.8 | 24.8 | 24.9 | 25.4-27.6 | 24.6 |
| **spawn ×20**: lost packets/s | 4.7 | 15.7 | 12.6 | 6.7 | 0.0 | 0.05-0.35 | 0.174 |
| spawn: busiest core % | 26.1 | 72.3 | **83.3** | 28.4 | 25.5 | 22.6-28.2 | 24.6 |

| op | mean loss/s at 0-2 s | × baseline | reproduces | wall / thread CPU per op (median) |
| --- | --- | --- | --- | --- |
| **parse** | **55.4** | **318** | **yes** | 0.417 s / 0.415 s (180,681 items) |
| spawn | 11.0 | 63 | yes | 2.85 s / 0.002 s in the companion |

- **The probe names `both`**, so the stream half of the bar is gated. The two are not alike, though.
- **The parse alone reproduces E1-CONC's peak, at its height and shape.** E1-CONC lost 56-65/s at +1 s;
  the parse alone lost 80.5/s at +1 s. That comes from 0.42 s of one Python thread's CPU, with the
  busiest core barely moving (33 %).
  - It holds the companion's GIL for ~0.4 s.
  - The stream's sender threads are Python threads in the same process.
- **The grabber child alone costs ~5 × less** (11 vs 55 packets/s at 0-2 s), although it drives a core to
  83 %. That is consistent with E3-S1: taking the child's CPU priority away did not move the peak.
- The companion's PSS after the parse triggers ranged 41-124 MB (the per-parse allocator high-water,
  E3-S2).

**The smoke with the change** (`smoke.sh`, `smoke.jsonl`, not data; `PRIVYHUB_EPG_GUIDE_INDEX=cached` +
the hook, stream idle):

- one forced refresh of each of the six suite channels, all ok (79 / 87 / 64 / 40 / 34 / 35 programmes);
- the first refresh built the index;
- PSS 27.7 → 59.2 MB after the build and the trim, then flat through the other five.
- **Clause (c)'s candidate dump: identical by both paths for all six channels** (4 / 1 / 1 / 1 / 3 / 4
  candidates).
- The index file `data/epg/metadata/guides_index.json` (runtime, ignored) is 3.27 MB.
- Drop-in removed after; environ the live default only.

**The index's cost** (`index_cost.py` → `index_cost.json`, outside the companion, the same packing):

- 13,555 channels;
- **3.7 MB in memory**, 3.1 MB on disk;
- built once in **0.95 s**, which includes the 0.34-s parse;
- reloaded from disk in **0.014 s**.
