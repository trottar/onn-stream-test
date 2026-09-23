---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-P10 — audio redundancy (2 copies, 4 ticks apart) cut warm-state audio loss 96.4 / 98.2 % at +1.6 Mbps; the pre-registered reading failed ONE clause on the favourable side (B's video FEC recoveries below the A range; video loss also lower); the user ADOPTED 2 / 4 as the profile default
---

# D-BASE-P10 — send audio twice

Task: `handoffs/D-BASE-P10_TASK.md` (authorized by the user 2026-09-23).
Evidence: `d_base_p10_2026-09-23/`, SHA-256 of every file in
`d_base_p10_2026-09-23/p10_sha256.txt`. Patch:
`patches/D-BASE-P10_AUDIO_REDUNDANCY.md`. Decision:
`decisions/D-BASE-P10_AUDIO_REDUNDANCY.md`.

## The change, in one paragraph

Profile `audio_redundancy_copies` (1 | 2) / `_offset_packets` (default
4), env overrides, `native-stream-status.audio_redundancy`; the Linux
sender sends packet *n* then the stored copy of *n − 4* in the same 5 ms
tick (same sequence, timestamp, payload); the client de-duplicates by
sequence first (64-slot window), and a late copy fills its concealment
slot in place (`recovered_by_duplicate`) or is dropped (`late_unplaced`).
**Found on the way:** the old receive loop, given any late packet, reset
`expectedSequence` backwards and queued it out of order at the tail —
fixed here; never exercised on this path (no reordering on record). APK
`f31b1c18…8ae7`, device hash equal. Smoke (60 s, copies 2): 4 one-packet
gaps, all 4 recovered by their copies, 0 lost.

## Sessions

PS1 reference title, zero input, adopted profile (`any_override: false`,
`-max_frame_size 90000`), **12/17 from the profile**, redundancy per arm
from the user manager's environment, companion restarted through systemd
per arm, `p9_run.sh` and `T2`'s `t2_sample.py` (10 s, whole run) copied
byte-for-byte; sampler off; **0 foreign adb in every hold** (only the
thermal sampler's).

| hold | copies | PLAYING (UTC) | onn cpu at start → mean in hold |
| --- | ---: | --- | --- |
| W (12 min, not scored) | 1 | 19:44:35 | 55.4 → — |
| W1 (5 min, extension) | 1 | 19:57:46 | 65.6 → — |
| W2 (5 min, extension) | 1 | 20:04:03 | 66.2 → — |
| **A1** | 1 | 20:10:13 | 63.7 → **67.3** |
| **B1** | 2 | 20:21:24 | 64.2 → **67.8** |
| **A2** | 1 | 20:32:35 | 64.7 → **67.8** |
| **B2** | 2 | 20:43:47 | 65.5 → **68.1** |

**The ≥ 67 °C-at-start condition was not met as measured, and W was
extended twice (the script's limit).** The reading at each start is taken
~40 s after the previous hold ends — the onn cools 2-3 °C across the
restart and launch — and every scored hold **averaged 67.3-68.1 °C**; the
A holds' loss rate (**78/min**, `T2`'s warm level, against ~3/min cold)
confirms the warm state held.

## Raw numbers first

| field | A1 off | B1 **on** | A2 off | B2 **on** |
| --- | ---: | ---: | ---: | ---: |
| duration s | 606.9 | 606.2 | 607.0 | 607.5 |
| **audio `lost_packets`** | **794** | **28** | **784** | **14** |
| … per min | **78.49** | **2.77** | **77.49** | **1.38** |
| `sequence_gap_packets` (raw, before recovery) | 794 | 848 | 784 | 786 |
| `recovered_by_duplicate` | 0 | **820** | 0 | **772** |
| `late_unplaced` (copy too late) | 0 | 14 | 0 | 6 |
| `duplicates_dropped` | 0 | 119,215 | 0 | 119,501 |
| `crossfaded_packets` | 773 | **38** | 783 | **21** |
| `concealed_loss_packets` | 771 | 28 | 784 | 14 |
| `underruns` | 3 | 0 | 12 | 13 |
| `prolonged_starvation_events` | 3 | 3 | 2 | 1 |
| `avg_queue_residence_ms` | 58.74 | 56.85 | 66.50 | 62.16 |
| `max_queue_residence_ms` | 83 | 93 | 91 | 89 |
| `P8` holes > 15 ms | 1,627 | 1,924 | 1,717 | 1,895 |
| sender originals / duplicates | 121,131 / 0 | 121,013 / 121,009 | 121,125 / 0 | 121,253 / 121,249 |
| sender send errors (orig / dup) | 0 / — | 0 / 0 | 0 / — | 0 / 0 |
| **audio on the wire** | **1.60 Mbps** | **3.21 Mbps** | 1.60 | 3.21 |
| encoder CPU % | 28.9 | 26.3 | 25.9 | 25.6 |
| rendered fps | 59.88 | 59.94 | 59.91 | 59.93 |
| spikes ≥ 20 ms / min | 32.3 | 31.3 | 33.6 | 35.8 |
| `max_output_gap_ms` | 168 | 128 | 105 | 141 |
| video lost / min | 16.1 | 4.8 | 10.8 | 3.0 |
| video `fec_recovered` / min | 11.47 | 3.17 | 5.04 | 3.56 |

Sequence-gap histogram (gap events at first arrival, before recovery):

| hold | 1 | 2 | 3 | 4-7 | 8+ |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 755 | 7 | 0 | 0 | 1 |
| B1 | 822 | 13 | 0 | 0 | 0 |
| A2 | 754 | 15 | 0 | 0 | 0 |
| B2 | 770 | 8 | 0 | 0 | 0 |

**The warm-state loss is single packets**: 98-99 % of gap events are one
packet, the rest two, one 8+ event in 3,145. A 20 ms copy offset clears
bursts that short with room to spare; the residual (28 / 14) is copies
lost too or arriving after their slot was played (`late_unplaced` 14 / 6).

## The pre-registered reading

Against the A mean (lost 77.99/min, crossfaded 76.90/min, residence
62.62 ms, holes 1,672); terms the handoff left loose were fixed in
`p10_analyze.py`'s docstring before the data:

| clause | B1 | B2 |
| --- | --- | --- |
| loss/min ≥ 80 % below A | **96.4 %** ✓ | **98.2 %** ✓ |
| crossfades fall in step (≥ 70 % of the loss reduction) | ✓ | ✓ |
| raw loss like A (0.5-1.5x) — the path lost as much | 83.9/min ✓ | 77.6/min ✓ |
| underruns ≤ 20 | 0 ✓ | 13 ✓ |
| residence within ±10 ms | −5.8 ✓ | −0.5 ✓ |
| holes within 20 % | +15.1 % ✓ | +13.3 % ✓ |
| fps in the A range | ✓ | ✓ |
| spikes in the A range | ✓ | ✓ |
| **video `fec_recovered` in the A range** (4.2-12.3 incl. ±10 %) | **3.17 ✗ (below)** | **3.56 ✗ (below)** |

**As written: DOES NOT WORK — one clause, on the favourable side.** The
video clause exists to catch redundancy *hurting* video (more traffic on
the same hop); B's FEC recoveries and post-FEC video loss both came in
**lower** than A's. Whether redundancy helps video or that is noise is not
settled by two pairs (A1/A2 themselves differ 2.3x in FEC recoveries);
nothing suggests it harms it. **Asked, the user adopted 2 / 4.**

## Adopted — the cost, measured

`native_game_720p60_reference`: `audio_redundancy_copies` **2**,
`audio_redundancy_offset_packets` **4**; companion restarted through
systemd: `audio_redundancy` 2 / 4 source `profile`, cushion 12/17
`profile`, 0 `PRIVYHUB_*`, `any_override: false`. **No client build** —
the default is the companion's. **Cost: +1.60 Mbps** on the wire (audio
1.60 → 3.21 Mbps against a 260 Mbps link), 0 send errors on either copy,
encoder CPU unchanged (25.6-28.9 %), audio latency unchanged (residence
within ±6 ms — the copy only fills a slot already in the queue).

The user's listen with redundancy on — their words, never a gate: not yet
given.

## State at the end

Companion under systemd, MainPID owns 8765, 12/17 and 2/4 from the
profile, 0 `PRIVYHUB_*` in its environ or the manager's, game inactive,
banner cleared, thermal sampler stopped, **no live `.state.recovery`**
(searched outside the evidence tree). Nothing on the Opal touched.

## Privacy

Private addresses in the companion journals / reports / status replaced
with `<IP_REDACTED>`; no MAC; `h2_prep_redact.py --check` passes on the
thermal jsonl.
