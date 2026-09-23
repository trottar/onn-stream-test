---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-P8 — CHARACTERIZED; the audio arrival holes are neither the heartbeat nor the adb socket sampler (pre-registered reading "neither"); the hole is the path's; nothing implemented
---

# D-BASE-P8 — the hole that comes "once every two seconds"

Task: `handoffs/D-BASE-P8_TASK.md`, second in
`handoffs/OVERNIGHT_2026-09-23_QUEUE.md` (authorized by the user
2026-09-22, unattended). Evidence: `d_base_p8_2026-09-22/`, SHA-256 of
every file in `d_base_p8_2026-09-22/p8_sha256.txt`. Patch record:
`patches/D-BASE-P8_AUDIO_HOLE_RING.md`. Host headless (H2), host wired to
the Opal, onn on the Opal's 5 GHz, adopted profile (`any_override:
false`, `-max_frame_size 90000` in every arm's argv).

## Classification

**CHARACTERIZED — "Neither".** In A and B only 6.6 % / 5.7 % of holes
start within 100 ms of a heartbeat send (uniform would be 5.0 %; the
heartbeat-caused rule needed ≥ 70 %). Removing the socket sampler changed
the hole rate by **-1 %** (sampler-caused needed ≥ -50 %); slowing the
heartbeat to 10 s changed it by **-11 %** (heartbeat-caused needed
≥ -60 %). Both within the 20 % "neither" band. **The hole belongs to the
path**; the AP's per-station scheduling is the remaining named candidate,
unmeasured.

## Raw numbers first

Three 20-minute attract-mode sessions of the PS1 reference title, zero
input, opened through RESUME PLAYING, BACK to end, companion restarted
per arm (`p8_run.sh`, derived from `P7`'s `p7_run.sh`; `p8_all.sh` runs
the three and restores the companion). Analysis `p8_analyze.py` →
`p8_analysis.txt`, `p8_summary.json`. Reports and heartbeat logs under
`runs/`.

| arm | heartbeat | socket sampler | duration | holes > 15 ms | /min | holes ≥ 40 ms /min | `prolonged_starvation_events` /min | adb client processes during hold |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| A | 2 s | **on** | 1,208 s | 3,200 | **158.9** | 101.5 | 35.0 | 138 — the sampler's own `cat /proc/net/udp{,6}` |
| B | 2 s | **off** | 1,207 s | 3,174 | **157.8** | 100.5 | 36.4 | **0** |
| C | **10 s** | off | 1,208 s | 2,842 | **141.2** | 93.6 | 33.8 | **0** |
| `P7` | 2 s | on | — | — | — | — | 32.5 | — |

Hole lengths (all arms alike; A shown): 15-20 ms 320, 20-30 383, 30-40
454, 40-50 292, **50-60 1,598 (50 %)**, 60-70 149, 70-100 3, 100-200 1.
The "55-60 ms hole" is the mode of a distribution, not a single event.

**Alignment with the heartbeat** — ms from the last heartbeat send start
to the hole's start, 50 ms bins (on-device histograms):

| arm | span | 0-50 | 50-100 | 100-150 | 150-200 | mean of other bins | 0-100 share | uniform |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 0-2,000 | 121 | 85 | 94 | 79 | 76.8 | **6.6 %** | 5.0 % |
| B | 0-2,000 | 95 | 81 | 84 | 75 | 76.8 | **5.7 %** | 5.0 % |
| C | 0-10,000 | 18 | 11 | 12 | 13 | 14.1 | **1.0 %** | 1.0 % |

Heartbeat in flight at the hole's start: A 146 of 3,200 (4.6 %), B 132 of
3,174, C 21 of 2,842.

The **client-health post** (the activity's other 2 s sender, found in the
code and tagged the same way) reads the same: A 6.6 %, B 5.6 %, **C 5.8 %**
— in C the health post stayed at 2 s while the heartbeat went to 10 s.
In A and B the two senders fire in the same tick, so their histograms are
near-identical and cannot be told apart there.

**One small effect, below every pre-registered threshold:** the first
50 ms bin after a send runs above the flat level — A 121 vs 76.8, B 95 vs
76.8, and in C **after the health post** 84 vs 68.8 but **not after the
heartbeat** (18 vs 14.1, within noise at that count). About **40 holes in
3,200 (≈ 1.3 %)** sit in that excess. A send costs the audio receive
path something within 50 ms, a little; it explains ~1 % of holes, not
the pattern.

**"Once every 2 s" was a reading of `P7`'s latched counter, not the
hole rate.** Holes ≥ 40 ms arrive at ~100/min (1.7/s); the counter
counts episodes (33.8-36.4/min here, P7 32.5).

## What went wrong first (recorded, not hidden)

1. **The first diagnostic build lost reports.** The decoder report is
   sent as a URL query (`POST …/decoder-session-log?report=…`); the
   companion's `http.server` refuses a request line over 65,536 bytes
   (**414**, then an `AttributeError` in `send_error` — a pre-existing
   companion bug). With a 4,000-row ring, ~3,000 holes per 20 minutes made
   arms A and C unsendable. Fixed in build v2: raw ring 300 rows plus
   on-device whole-session histograms; report ~40 KB encoded at any
   length. 5-minute check before the rerun: 791 holes, report landed.
2. **Arm B of the first run was disturbed by a concurrent R3b `E30` run**
   on the same host at 23:37 UTC (the host's adb monitor caught its
   `force-stop` / `am start` / `uiautomator dump /sdcard/r3bchk.xml`),
   which ended B's first session and injected a fault; and this task's
   harness in turn ended that session at 23:42 and restarted the
   companion for arm C — **so the user's E30 run should be treated as
   disturbed too.** The `privyhub_fault` table was gone when checked.
   First-run data kept as `runs_v1/` (not analysed beyond the note that
   its 263 s B segment also read flat: 7.0 % in 0-100 ms).
3. The rerun (all numbers above) had **no foreign adb traffic** in any
   hold (monitor: A only the sampler, B and C zero).

## The levers — the user's decision, none implemented

- **The deeper audio cushion**, `P7`'s measured **+45 ms** of latency, is
  still the only client lever that removes audible starvation from these
  holes.
- **Measure the AP's per-station scheduling** (power-save / DTIM /
  airtime on the Opal) — the remaining candidate; the Opal is read-only
  and `O1` found no sub-second airtime counter, so this needs a new
  instrument.
- The heartbeat and the socket sampler are **cleared**: no need to move
  the heartbeat off anything, and the sampler may keep running during
  audio measurements (it moved the rate by 1 %).

## State at the end

Companion restarted **without** `PRIVYHUB_HEARTBEAT_MS` (pid checked, the
variable absent from its environ), `status` read `active: false`; the
heartbeat default (2,000 ms) is in force with the variable unset. The
socket sampler is a harness script and is simply not running. **The P8
diagnostic build v2 stays installed** (APK `322022ef…8492`): it changes
no existing counter, adds `audio.arrival_holes` and bumps the report
schema to `_v2`.

## Privacy

The client address in the companion logs under `runs/`, `runs_v1/`,
`smoke/`, `smoke2/` was replaced with `<IP_REDACTED>`; no other address,
MAC, SSID or identifier in the evidence.
