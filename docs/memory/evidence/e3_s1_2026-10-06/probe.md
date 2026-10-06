# E3-S1 probe — the grabber's spawn chain, its priority, its first 3 s (2026-10-06 03:16Z)

Measurement before the change. The stream idle, no game; the 1-s sampler with `--e2` on
(`probe/sampler/`), and `tools/e3_probe.py tree` polling the companion's descendants every ~76 ms
(`probe/tree.jsonl`, `probe/tree_summary.json`). One forced grab, `ComedyCentral.us@East`:
ok, 82 programmes, 5.3 s.

## The chain (not quite what E2 inferred)

E2 inferred companion → `npm` → `node`. The real chain has five processes per **source attempt**:

| order | process (comm / argv) | role | policy | nice | I/O class |
| --- | --- | --- | --- | --- | --- |
| 1 | `npm run grab --` (node running npm) | the companion's direct child | 0 (SCHED_OTHER) | 0 | none (best-effort default) |
| 2 | `sh -c …` | npm's script shell | 0 | 0 | none |
| 3 | `node … tsx grab.ts` | the tsx loader | 0 | 0 | none |
| 4 | `node --require preflight.cjs …` | **the grabber itself** (V8, multi-threaded) | 0 | 0 | none |

And **one forced refresh can run the chain more than once**: the plugin tries up to three source
sites in order and stops at the first with programmes. This channel's first site (`tvtv.us`)
returned 0 programmes after 1.96 s; the second (`tvpassport.com`) returned 82 after 2.78 s. So this
grab spawned the chain **twice**.

## CPU-seconds by process (`cpu_s` from `utime+stime`)

| attempt | process | start (s after the POST) | alive s | CPU-s, first 3 s of the grab | CPU-s total | peak RSS / PSS MB |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | npm | 0.45 | 1.86 | 0.08 | 0.08 | 66 / 36 |
| 1 | sh | 0.53 | 1.79 | 0 | 0 | 2 / 0.2 |
| 1 | node tsx | 0.53 | 1.79 | 0.04 | 0.04 | 56 / 29 |
| 1 | **node grabber** | 0.53 | 1.79 | **3.09** | **3.09** | **595 / 539** |
| 2 | npm | 2.39 | 2.87 | 0.08 | 0.08 | 66 / 53 |
| 2 | sh | 2.47 | 2.80 | 0 | 0 | 2 / 0.2 |
| 2 | node tsx | 2.47 | 2.80 | 0.05 | 0.06 | 57 / 29 |
| 2 | **node grabber** | 2.55 | 2.72 | 0.65 (its first 0.45 s) | **3.53** | **626 / 595** |

- **The first 3 s of the grab cost ~3.9 CPU-s, ~97 % of it in the node grabber.** That is ~1.3 cores
  on average and, per the 1-s sampler, **the busiest core at 97 %** in the second after the spawn
  (host mean 14-19 % of 12 CPUs during the body; the `epg` category at ~184 % of a core).
- The grabber's start-up is the cost: attempt 2's node used **3.29 of its 3.53 CPU-s before its
  first established TCP socket** (4.41 s after the POST, ~1.9 s after it started). Attempt 1 never
  showed a TCP socket at the probe's resolution.
- **As spawned today, every process in the tree is SCHED_OTHER, nice 0, default I/O class** — the
  same class as the stream's FEC relay thread (SCHED_OTHER in E2's thread table; the audio sender
  is SCHED_RR).

## Consequence for the change

The change applies to what is actually spawned: the companion's direct child (`npm`) is started
under `chrt -i 0` → `nice -n 19` → `ionice -c 3`. Each wrapper execs the next, so the pid is the
same and every descendant (sh, both node processes) inherits SCHED_IDLE, nice 19 and the idle I/O
class. **Smoke with the flag set** (`probe/smoke_flag_tree.jsonl`, `NBC.us@East`, 2 attempts, ok,
35 programmes): all eight processes of both attempts read policy 5 (SCHED_IDLE), nice 19, I/O
class idle. The drop-in was then removed, `daemon-reload`ed and the unit restarted: the environ is
`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` only. The smoke is not data.

Two notes for the record, not for this task:

- A forced refresh may spawn the chain 1-3 times (per source attempt), so "a grab" in the E1 rows
  is one-to-three Node start-ups; E3-S3 measures this.
- The guide metadata (`data/epg/metadata/guides.json`, 25.6 MB) has a 24-h TTL; it was fetched
  2026-10-05 ~06:20Z, so it re-downloads during one grab of tonight's first runs (as it did on
  any night). Today's behaviour; reported if visible.
