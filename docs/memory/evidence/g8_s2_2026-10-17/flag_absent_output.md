# G8-S2 — flag absent, byte for byte (in process)

No `PRIVYHUB_*` variable in this process: True; `native_stream.START_RUNG` is None; HEAD from git; temp files `g8_s2_absent_*`, `g8_s2_stub_*` left in place.

## 1. The first-target handler (`_start_linux_locked`), HEAD vs today

| target class | argv -b:v / -maxrate / -bufsize | active kbps | stub calls | identical (argv, level, payload, calls, log) |
| --- | --- | --- | --- | --- |
| LAN | 7000k/7000k/7000k / 7000k/7000k/7000k | 7000 / 7000 | 8 / 8 | **yes** |
| overlay | 7000k/7000k/7000k / 7000k/7000k/7000k | 7000 / 7000 | 8 / 8 | **yes** |

## 2-3. The replays (unchanged code) over the sessions the ladder's log still holds

- the ladder's log (`logs/games/adaptive_bitrate_shadow.jsonl` + 3 archives, `LOG_KEEP = 3`) rotated at 2026-10-17T03:57Z during G8-S1's night; it now starts 2026-10-10T08:59Z.
- G5-S2's four runs: held 3 (e4_s4b run3 (lossy), e4_s4b run2 (cleanest), cl_b3 run1 (today's best link)); **rotated out: e4_s4 E1-CONC_flag run1 (grab bursts)** (no copy in the evidence tree). The replays run over the held ones.

**G5-S2's `replay.py`** (its `RUNS` restricted to the held sessions):

```
| e4_s4b run3 (lossy) | 639 | 98 | exact | identical (738 rows) |
| e4_s4b run2 (cleanest) | 643 | 136 | exact | identical (780 rows) |
| cl_b3 run1 (today's best link) | 343 | 70 | exact | identical (414 rows) |
```

- recorded decisions exact and HEAD's vs today's controller identical: **PASS**
- its WAN tables, entry for entry, equal G5-S2's recorded ones (6 entries): **yes**

**G5-S3's `replay.py`** (G5-S3 on, G8-S2 absent; its G5-S2 runs restricted the same way):

- exit 0; its tables, entry for entry, equal G5-S3's recorded ones (16 of 20 entries; the 4 missing are the rotated session's): **yes**
- `replay_output.md` equals the recorded one with the rotated session's rows removed: **yes**

## 4. In addition: HEAD's vs today's `LiveController` over every session the log holds

- sessions with >= 5 reports: 70; rows written: 23847; sessions differing: **0**

-> flag absent: **PASS**
