# E3-S3 probe — where each grab's CPU-seconds and memory go (2026-10-06 05:49Z)

Measurement before the change. The stream idle, no game; the 1-s sampler with `--e2` on (`probe/sampler/`),
`tools/e3_probe.py tree` every ~56 ms (`probe/tree.jsonl`, `probe/tree_summary.json`). Three forced grabs of
`CNBCUK.uk@SD` (one source attempt each, ok, 81 programmes). The first established TCP socket of a process
(`ss -tnp`, own processes) marks "the first network byte" at the probe's resolution.

| grab | (a) npm wrapper CPU-s | sh | tsx cli (node) CPU-s | (b) grabber node before its first TCP socket, CPU-s | (c) grabber node after it, CPU-s | total CPU-s | grabber start → first TCP s | grabber peak RSS / PSS MB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.08 | 0 | 0.07 | 3.36 | 0.17 | 3.68 | 2.01 | 625 / 594 |
| 2 | 0.08 | 0 | 0.06 | 3.23 | 0.20 | 3.57 | 1.97 | 626 / 595 |
| 3 | 0.09 | 0 | 0.07 | 3.41 | 0.19 | 3.76 | 2.01 | 627 / 596 |

(The tsx cli's CPU is counted with (b): it is node start-up before any network.)

- **(a) + (b) = 3.51 / 3.37 / 3.57 CPU-s of 3.68 / 3.57 / 3.76: 95 %.** That is above the task's 40 %, so
  **start-up is the cost** and the pre-registered change is `PRIVYHUB_EPG_DIRECT_NODE=1`: the companion
  invokes the grabber's node directly.
- **Where the start-up is, though:** npm and the tsx cli are only ~0.15 CPU-s (4 %) and ~95 MB PSS together.
  **~91 % is inside the grabber node itself**, ~2 s of compile/load at ~170 % of a core and ~600 MB before
  any network: tsx's TypeScript transform and the grabber's module load. Starting node directly keeps
  that. The task's rule is followed; the expectation is stated here, before the data.
- **Memory**: the grabber node's ~595 MB PSS is set before its first network byte; npm adds 35-62 and
  the tsx cli ~29 MB PSS.
- As before, the companion's own work per grab (the 25.6 MB metadata parse, E3-S2) is not in these
  numbers; it is the companion's CPU, not the child's.

**The change** (`../e3_s3_direct_node_change.diff`, `companion/plugins/epg.py`, the grab's argv only): with
`PRIVYHUB_EPG_DIRECT_NODE=1` the argv is `<toolchain node> --require <tsx>/dist/preflight.cjs --import
<tsx>/dist/loader.mjs scripts/commands/epg/grab.ts <the same grab arguments>`. That is exactly what the
tsx cli spawns (its own source: `--require preflight.cjs`, `--import loader.mjs`), in the same working
directory and with the same environment. Absent = `npm run grab`, byte for byte. E3-S1's priority prefix,
if set, still wraps it; it is absent here.

**Smoke with the flag** (`probe/smoke_flag_tree.jsonl`, `probe/smoke_flag_summary.json`; not data): two
grabs, ok, 81 programmes each. The tree is one process, the grabber node, at 3.38 / 3.54 CPU-s, with its first
TCP socket at ~2.4 s. The drop-in was removed and the environ is back to the live default only.

**The guide read before the runs** (`guide_read_before.json`): 6 channels serving, 342 programmes.
