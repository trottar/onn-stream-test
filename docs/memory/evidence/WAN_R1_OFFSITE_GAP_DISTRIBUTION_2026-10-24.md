---
memory_schema: 1
as_of: 2026-10-25
baseline_commit: 13ccff5
---

# WAN-R1 — what a WAN link's gaps look like (read-only)

**Classification: READ.**
- **On the DIRECT overlay path:** 113 min of streaming across all four off-site sessions (G4-S1 ×2, G4-S2, G4-S3,
  G4-S4), with **0 uplink silences ≥ 250 ms outside real drops** and 0 output gaps ≥ 400 ms. Neither the 400-ms save,
  H 950 nor the 400-ms stall would fire falsely there. The 5-GHz LAN (47 min, five windows) reads 1.27 silences / 10
  min.
- **The RELAYED path has no data in play:** 0.5 min in total. In every session the path read relayed only while the
  stream was idle or ending.
- **G4-S4's actual false holds: 0, as predicted.**
- **For B:**
  - on direct, the data sets no lower bound on H or the stall: any H ≥ 250 and any stall ≥ 200 keeps ≤ 1 false fire /
    10 min;
  - the binding numbers come from the LAN (H 550 each / 300 pooled; the stall 350);
  - relayed needs a session forced onto the relay.

Nothing changed, nothing run. Nothing adopted; nothing committed.

Task: `handoffs/WAN-R1_OFFSITE_GAP_DISTRIBUTION_TASK.md`, session A, run after G4-S4's record in the same turn. Every
number comes from `wan_r1_2026-10-24/`: `wan_r1_gaps.py` → `wan_r1_tables.json` / `wan_r1_tables.md`. The copies are
in `copies/`.

## 1. Method (in the script's header, written before the tables)

- **Uplink silences:** the host's control-gap log (every client → host silence ≥ 250 ms), as B6.
  - Per 10 min over streaming seconds, with **10 s excluded at every session start / end** (start-up, teardown, the
    user's exits).
  - **A gap ≥ 3 s is a real drop** (G4-S4's rule) and is listed apart. The thresholds act on the rest:
    - the silence save at ~400 ms;
    - **the hold at H 950** (B6).
- **Output gaps:** the client's decoder report, which feeds **the 400-ms stall** (B9: a downlink-only gap pauses the
  core ~400 ms after the client's last frame).
  - The per-event list (`slow_events_ge_50_ms` + `slow_events_top_gap`) is placed by the report's own clock, counted
    only in live seconds.
  - The whole-session counts (spikes ≥ 20 / ≥ 50, stalls sent at 150) are prorated by live seconds. **A report whose
    live coverage is < 80 % of its duration keeps its events but not its counts**: a client "reconnecting" after its
    stream ended (G4-S3 §5, G4-S4 session 12) is not play.
  - No report's ≥ 50-ms list overflowed in play, except LINK-R1's one report (full, the older rows dropped).
- **Streaming seconds:**
  - **G4-S4 and the LAN windows:** seconds with frames on the host (1 s).
  - **G4-S1..S3:** their frame-size logs rotated out, so the 10-s status polls with the stream active are used. That
    is a coarser clock, disclosed.
- **The path class:**
  - G4-S1..S3 from `path.jsonl` (every 10 s);
  - G4-S4 from the driver's 60-s samples ("not sampled" beyond 60 s: sessions 1-2, 6, 13);
  - the LAN windows "lan".
  - `no-peer` is G4-S1 run 2 after the hotspot toggle: the stream was not on the overlay. Shown, not a WAN class.
- **The thresholds for B (computed, not changed):** per class, the smallest value on a 50-ms grid with ≤ 1 non-drop
  event ≥ it per 10 min.
  - on each session of the class, and pooled;
  - H from the uplink silences (250-2,950);
  - the stall from the output gaps (150-2,000).
- **Copies:**
  - G4-S1..S3's control-gap and recovery rows, and their client reports, were copied read-only from the hub's logs
    into `copies/s1r1`, `s1r2`, `s2r1`, `s3r1`. Their evidence dirs never held them.
  - The LAN windows' reports were copied into `copies/lan_*`.
  - G4-S4 and the LAN logs were read in place from their evidence dirs.

## 2. The tables (per session and class; `wan_r1_tables.md`)

| session | class | streaming min | silences ≥ 250 / 10 min | ≥ 400 / 10 | ≥ 950 / 10 | p50 / p90 / p99 ms | real drops (≥ 3 s) | output ≥ 50 / 80 / 200 per min | output ≥ 400 / 10 | spikes ≥ 20 / 50 per min |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | --- |
| G4-S1 run 1 (7000, PCM, hotspot) | direct | 10.5 | **0** | 0 | 0 | — | 25,301 | 27.4 / 3.4 / 0.1 | 0 | (tail) |
| G4-S1 run 1 | relayed | 0.3 | 0 | 0 | 0 | — | — | 0 / 0 / 0 | 0 | — |
| G4-S1 run 2 (7000, PCM, hotspot) | direct | 4.8 | **0** | 0 | 0 | — | — | 19.2 / 1.7 / 0 | 0 | 110.2 / 8.5 |
| G4-S1 run 2, after the toggle | *no-peer* | 3.0 | *120.0* | *33.3* | *0* | *329 / 509 / 662* | — | *207 / 40.7 / 1.3* | *0* | — |
| G4-S2 run 1 (4000, PCM, hotspot) | direct | 6.3 | **0** | 0 | 0 | — | — | 17.7 / 0.8 / 0 | 0 | 80.9 / 6.7 |
| G4-S2 run 1 | relayed | 0.2 | 0 | 0 | 0 | — | — | 150 / 8.6 / 4.3 | 0 | — |
| G4-S3 (4000, Opus, hotspot) | direct | 9.9 | **0** | 0 | 0 | — | — | 9.5 / 0.7 / 0 | 0 | 44.5 / 5.3 |
| **G4-S4 (Opus, friend's broadband)** | **direct** | **81.5** | **0** | 0 | 0 | — | 12,517 (Home) | 16.3 / 1.2 / 0.06 | 0 | 106.4 / 4.2 |
| G4-S4 | not sampled | 14.6 | 0 | 0 | 0 | — | — | 27.0 / 2.0 / 0 | 0 | 219.5 / 22.7 (start-ups) |
| LINK-R1 | lan (5 GHz) | 11.2 | 0 | 0 | 0 | — | — | 90.1 / 6.2 / 0 | 0 | 59.7 / 3.1 |
| G-A3 | lan | 11.2 | 0 | 0 | 0 | — | — | 81.7 / 6.4 / 0 | 0 | 55.0 / 1.4 |
| CL-B10 cell 1 | lan | 3.7 | 0 | 0 | 0 | — | 6,068 | 106 / 4.6 / 0 (0.2 report min) | 0 | (tail) |
| CL-B11 cell 1 | lan | 10.8 | **5.58** | 2.79 | 0 | 261 / 564 / 564 | 16,919 | 109 / 13.8 / 1.0 | 0 | 189.9 / 13.2 |
| CL-B12 cell 1 | lan | 10.2 | 0 | 0 | 0 | — | 25,815, 15,459 (Home) | 102 / 9.4 / 0.2 | **1.0** (820 ms) | 163.7 / 15.8 |

- **The longest non-drop silences:**
  - on direct, none ≥ 250 ms in 113 min;
  - on the LAN, CL-B11 cell 1's six (250-564 ms);
  - off the overlay (G4-S1 run 2 after the toggle), 36 in 3 min, up to 662 ms.
- **The longest output gaps in play:**
  - direct 337 ms (G4-S1 run 1) and 232 ms (G4-S4);
  - LAN 820 ms (CL-B12 cell 1) and 353 ms (CL-B11 cell 1).
- **The real drops on direct:**
  - G4-S1 run 1's 25.3-s controller-silence pause, which coincided with a direct → relayed → direct change (G4-S1 §6);
  - G4-S4's Home press (12.5 s). Its other Home (9.8 s) fell inside the 10-s session edge.
- **RTT** (the client's control echo, running p50 / p95):
  - **G4-S2 / G4-S3 on the hotspot: p50 119-138, p95 160-780 ms;**
  - **G4-S4 on broadband: p50 58-68, p95 331-342 ms** (768 in the first minute);
  - G4-S1: not in its files.
- **Rungs:** G4-S1 7000 fixed; G4-S2 and G4-S3 4000. G4-S3's 7000 is the status poll at the restarts (G4-S3 §8).
  G4-S4 4000 → 7000 (G4_S4 §3).
- **Uplink against downlink:** loss on the overlay is downlink. G4-S1 run 1 lost 2,259 packets / min post-FEC with 0
  uplink silences ≥ 250 ms; its output gaps stayed under 400 ms.

## 3. Pooled by class, and where the thresholds sit

| class | sessions | streaming min | silences ≥ 250 / 10 | would **save** (≥ 400) / 10 | would **hold** (≥ 950) / 10 | would **stall** (output ≥ 400) / 10 | H for ≤ 1 / 10 (each / pooled) | stall for ≤ 1 / 10 (each / pooled) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| **direct (WAN)** | 5 | **113.0** | **0.0** | **0.0** | **0.0** | **0.0** | **250 / 250** | **200 / 200** |
| relayed (WAN) | 2 | 0.5 | — | — | — | — | not answerable | not answerable |
| not sampled (G4-S4) | 1 | 14.6 | 0.0 | 0.0 | 0.0 | 0.0 | 250 / 250 | 150 / 150 |
| *no-peer (off the overlay)* | 1 | 3.0 | *120.0* | *33.3* | *0.0* | *0.0* | *700 / 700* | *250 / 250* |
| **lan (5 GHz)** | 5 | **47.1** | **1.27** | **0.64** | **0.0** | **0.23** | **550 / 300** | **350 / 350** |

- **Where a WAN path's silences sit against H 950 and the 400-ms stall:**
  - **direct:** none of the 113 min reaches 250 ms. With 0 events, the 95 % bound on silences ≥ 250 ms is
    < ~0.27 / 10 min, and likewise on false saves, holds and stalls. 0 output gaps ≥ 400 ms were seen; ≥ 200 ms at
    0-0.1 / min.
  - **The overlay's direct path was quieter on the uplink than the 5-GHz LAN.** The LAN's silences come from one
    window (CL-B11 cell 1, 5.6 / 10 min).
  - **relayed:** the off-site sessions spent 0.5 min streaming on the relay, all of it at a session's start or end. A
    relayed distribution does not exist yet.
- **G4-S4's false holds beside the prediction:**
  - **Predicted:** from G4-S1..S3's direct minutes (31.5 min, 0 silences ≥ 950 outside drops), ~0 per 10 min, bounded
    < ~1 / 10 min by that short span.
  - **Actual: 0 false holds in 100.1 min of play** (81.5 min direct by sample, 14.6 not sampled). The only holds were
    the two Home presses.
  - **The prediction held; the bound is now < ~0.3 / 10 min on direct.**
- **The numbers for B's design (not changed here):**
  - **H on a WAN direct path:** any value ≥ 250 ms keeps ≤ 1 false hold / 10 min on the data. H 950 has ≥ 700 ms of
    margin over everything seen; the LAN binds it first (550 each / 300 pooled).
  - **The stall on a WAN direct path:** ≥ 200 ms keeps ≤ 1 false stall / 10 min. The adopted 400 has margin; the LAN
    binds it first (350).
  - **Relayed:** not answerable from the files. **The first WAN question for B stays open for this class:** a session
    held on the relay (Tailscale can be told to avoid the direct path), or a lucky one, is needed before H or the
    stall can be set per path class.
  - **Off the overlay** (the toggle's aftermath, like 2.4 GHz): H 700, stall 250. This is the flapping regime, not a
    WAN path.

## 4. Limits

- **Direct is 113 min** from three hotspot sessions (31.5 min) and one broadband evening (81.5 min). One provider each,
  one evening each.
- **G4-S1..S3's streaming seconds come from 10-s polls.** A gap inside a poll interval is counted, but the denominator
  is coarser.
- **The client reports place events by their own clock**, without a heartbeat elapsed-map for G4-S1..S3 (rotated out).
- **The LAN column is five 5-GHz windows,** not the evenings (UX-R1/R2 are B6's).
- **The 10-s session edges exclude start-up silences.** G4-S4's first 15 s after each start had no hitch seconds
  (G4_S4 §7), so nothing large is hidden there.

## 5. Files

`wan_r1_2026-10-24/`:
- `wan_r1_gaps.py`;
- `wan_r1_tables.json`, `wan_r1_tables.md`;
- `copies/` (`s1r1`, `s1r2`, `s2r1`, `s3r1`: control gaps, recovery rows, client reports; `lan_*`: client reports);
- `redact_check.txt`, `manifest.sha256`.

`logs/wan_r1_git_status.txt`.

No sudo, no nft, the Opal untouched, no adb (WAN-R1 used none; G4-S4's record used it for `--check` and the band). No
run, no restart. No address or identifier. Nothing fetched, deleted or moved (copies only); nothing adopted; nothing
committed.
