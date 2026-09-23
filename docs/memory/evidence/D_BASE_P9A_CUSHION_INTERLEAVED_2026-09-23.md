---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-P9a — 3/8 kept at the time, 12/17 ADOPTED by the user later on 2026-09-23 (D-BASE-T2 Part 0, decisions/D-BASE-P9_AUDIO_CUSHION.md); 12/17 passes starvation, residence and the underrun noise band in both B arms, and fails only the hole clause as coded (B3 -22.5 % against A4, which is itself +28 % above A3); audio loss TIME-DRIVEN, not the cushion's
---

# D-BASE-P9a — the 12/17 cushion against noise, interleaved

Task: `handoffs/D-BASE-P9A_TASK.md` (authorized by the user 2026-09-23).
Evidence: `d_base_p9a_2026-09-23/`, SHA-256 of every file in
`d_base_p9a_2026-09-23/p9a_sha256.txt`. **No code change**: the `P9`
setting and APK `a9355bb0…4a72` as installed. `p9_run.sh` copied
byte-for-byte from `d_base_p9_2026-09-23/`; `p9a_all.sh` runs the four arms
and restores; `p9a_analyze.py` (written and dry-run on `P9`'s reports
before the first arm finished) → `p9a_analysis.txt`, `p9a_summary.json`.

Every arm: cushion from the user manager's environment, companion
restarted through systemd, 8765 owned by the unit's MainPID,
`audio_cushion` and `any_override: false` confirmed at PLAYING, report
`queue_cushion_source` "host", sampler off, heartbeat default, **0 adb
client processes in every hold**, game stopped after. Adopted profile,
host headless, Opal path.

## Raw numbers first — the four arms in run order

| field | A3 3/8 | B2 12/17 | A4 3/8 | B3 12/17 |
| --- | ---: | ---: | ---: | ---: |
| PLAYING (UTC) | 07:53:43 | 08:14:54 | 08:36:06 | 08:57:18 |
| duration s | 1,207.0 | 1,207.1 | 1,207.2 | 1,207.9 |
| **`underruns`** (total) | **10** | **12** | **16** | **19** |
| `prolonged_starvation_events` | 833 | 15 | 931 | 4 |
| … per min | **41.41** | **0.75** | **46.27** | **0.20** |
| `concealed_underruns` | 5,201 | 158 | 6,087 | 49 |
| `smooth_latency_trims` | 5,203 | 127 | 6,090 | 28 |
| audio `lost_packets` | 442 | 1,151 | 1,417 | 1,676 |
| `concealed_loss_packets` | 424 | 1,117 | 1,381 | 1,651 |
| **`avg_queue_residence_ms`** | **30.85** | **68.45** | **30.34** | **64.14** |
| `max_queue_residence_ms` | 51 | 127 | 52 | 100 |
| `max_queue_depth` | 8 | 17 | 8 | 17 |
| `startup_wait_ms` | 2,211 | 2,139 | 2,037 | 2,175 |
| `first_write_elapsed_ms` | 2,306 | 2,222 | 2,121 | 2,244 |
| holes > 15 ms / ≥ 40 ms | 3,479 / 2,227 | 3,749 / 2,328 | **4,451** / 2,781 | 3,450 / 2,175 |
| rendered fps | 59.91 | 59.87 | 59.91 | 59.90 |
| spikes ≥ 20 ms / min | 31.9 | 34.8 | 33.1 | 29.7 |
| `max_output_gap_ms` | 157 | 203 | 214 | 329 |
| video lost / min | 9.5 | 21.9 | 9.4 | 17.0 |

Hole lengths (ms: count):

| arm | 15-20 | 20-30 | 30-40 | 40-50 | 50-60 | 60-70 | 70-100 | 100-200 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A3 | 331 | 416 | 505 | 251 | 1,775 | 193 | 6 | 2 |
| B2 | 459 | 420 | 542 | 304 | 1,851 | 164 | 5 | 4 |
| A4 | 512 | 500 | 658 | 396 | 2,203 | 178 | 4 | 0 |
| B3 | 413 | 385 | 477 | 272 | 1,747 | 152 | 4 | 0 |

**Every underrun placed in time.** The heartbeat carries the cumulative
`audio_underruns` every 2 s for the whole session (`R5`/`P7` field); an
event is a run of consecutive ticks with a non-zero delta, the share
before the first heartbeat and the tail after the last are events of their
own (`*`):

| arm | total | events (count @ s) |
| --- | ---: | --- |
| A3 | 10 | 3@7*, 1@64, 2@415, 1@494, 2@803, 1@1187 |
| B2 | 12 | 2@7*, 2@285, 1@554, 2@588, 1@887, 2@1026, 2@1165 |
| A4 | 16 | 1@7*, 2@88, 1@470, 2@506, 2@685, 2@795, 2@970, 2@996, 2@1163 |
| B3 | 19 | 1@46, 1@64, 2@116, 1@237, 2@566, 2@717, 2@803, 2@954, 3@966, 2@974, 1@1197 |

`tick_series` (first ~200 s only) agrees where it overlaps (A3 3@2.7 s,
1@62.6 s; B3 1@45.5, 1@62.7, 2@115.0 s). **Underruns come in events of 1-3
spread across the whole session, in both cushions;** the startup share is
1-3. `P9`-B's 8-underrun event at 78 s has no counterpart in any of these
four.

## The 3/8 noise band

Every 3/8 session on record with the default 2 s heartbeat (`P8`-C left
out: 10 s heartbeat):

| session | `P7` | `P8`-A | `P8`-B | `P9`-A2 | A3 | A4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| underrun total | 4 | 9 | 6 | 20 | 10 | 16 |
| largest single event | 2 | 2 | 2 | 3 | 3 | 2 |

**Band: min 4, median 9.5, max 20; largest single 3/8 event 3.** The
rule's allowance: max + one event = **23**.

## The pre-registered reading

Against the A mean (starvation 43.84/min, residence 30.60 ms, holes 3,965):

| clause | B2 | B3 |
| --- | --- | --- |
| starvation ≥ 80 % below | **98.3 %** ✓ | **99.5 %** ✓ |
| residence +30-55 ms | **+37.9** ✓ | **+33.5** ✓ |
| underruns ≤ 23 | **12** ✓ (inside the band) | **19** ✓ (inside the band) |
| holes within 20 % of the A arms | A3 +7.8 %, A4 -15.8 % ✓ | A3 -0.8 %, **A4 -22.5 % ✗** |

**As coded before the data ("each A arm"): KEEP 3/8, on the hole clause
alone.** Against the A mean the same clause reads B2 -5.4 %, B3 -13.0 %
and all four pass. **The failure is the baseline's, not B's**: A4's 4,451
holes are +28 % over A3 and above every earlier 3/8 session (3,200-3,524);
the within-A spread exceeds the 20 % tolerance by itself. Asked which
reading to apply, **the user chose to keep 3/8 and decide later** — the
profile default is unchanged, adoption is open.

**`P9`'s underrun objection does not replicate.** B2 12 and B3 19 sit
inside a 3/8 band of 4-20; the 20 → 25 that tripped `P9` was one event.

## Audio loss — TIME-DRIVEN, not the cushion's

Per-minute audio `lost_packets`, run order:

- A3 (442): 3 3 3 1 5 3 9 2 9 8 4 21 21 40 34 47 66 49 59 53
- B2 (1,151): 33 55 52 39 60 67 87 29 76 86 70 50 46 59 45 62 58 63 24 74
- A4 (1,417): 111 35 55 95 60 94 64 118 24 84 57 77 46 75 96 26 79 83 105 25
- B3 (1,676): 80 96 42 71 90 83 58 47 80 77 60 91 78 81 81 121 132 65 117 117

A4 ≥ A3 ✓, B3 ≥ B2 ✓, B not systematically above its neighbouring A (A4
1,417 > B2 1,151) → **time-driven** by the rule; not cushion-linked (B
does not exceed both A by ≥ 50 %). **It is streaming time, not the clock
and not the session:** `P9`'s run ended at ~78/min (07:14 UTC), and after
a ~40-minute idle gap A3 opened at **3/min** and climbed only from minute
12; later arms, started a minute after the previous one, open high. Loss
builds over **back-to-back streaming** and resets with idle time. For the
roadmap, not measured here: something that accumulates while streaming
(onn or host thermal, the AP) — the thermal-threshold work is next.

## Not in the rule, noted

- **Video loss/min was higher in both B arms** (21.9 / 17.0 against 9.5 /
  9.4). `P9` showed no such split (A2 12.1, B 13.3, B′ 11.0), and the
  audio queue sits after the network on the client; fps and spikes did
  not move. Five 12/17-or-deeper sessions against four 3/8: not a
  pattern the data supports, recorded so a later run can check it.
- `max_output_gap_ms` 329 in B3 (one gap); the others 157-214.
- `first_write_elapsed_ms` 2,121-2,306 in all four: the startup hold is
  untouched (the host's cushion still lands after the first PCM).

## The user's listen

Lip-sync or lag on the TV with 12/17 in force: **their words, recorded
as user-stated, never a gate.** Not yet given.

## State at the end

Profile default **3 / 8** (`audio_cushion.source` `profile`); companion
MainPID serving 8765 under systemd; **no `PRIVYHUB_*` in its environ or
the user manager's**; `any_override: false`; game inactive; launcher
banner cleared. No code changed.

## Privacy

Private addresses in the companion journals, reports and status files
replaced with `<IP_REDACTED>`; no MAC, SSID or device identifier in the
evidence.
