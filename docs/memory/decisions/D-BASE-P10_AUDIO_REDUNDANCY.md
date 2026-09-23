---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 3e6cde5
status: DECIDED 2026-09-23 by the user — audio redundancy 2 copies / offset 4 is the profile default
---

# Decision — send every audio datagram twice

## The decision (the user's)

**`audio_redundancy_copies = 2`, `audio_redundancy_offset_packets = 4`**
in `native_game_720p60_reference` (`companion/native_stream_profiles.py`),
in force with nothing in the environment. Taken by the user on
2026-09-23 on `D-BASE-P10`'s measurements.

## Why

`T2`/`T3`: from cold, audio loss steps to 30-90/min at a warm state and is
lost **between** the host's NIC and the onn's IP stack — neither end can
recover the same packet, and audio (unlike video) has no FEC. `P10`,
warm, interleaved (`evidence/D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md`):

| | off (A1, A2) | on (B1, B2) |
| --- | ---: | ---: |
| audio lost / min | 78.5, 77.5 | **2.8, 1.4** (−96.4 / −98.2 %) |
| recovered by the copy | — | 820, 772 |
| crossfades / min | 76.4, 77.4 | 3.8, 2.1 |
| audio on the wire | 1.60 Mbps | 3.21 Mbps |

The loss is single packets (98-99 % of gap events), so a 20 ms offset
covers it.

## The measured cost

**+1.60 Mbps** (on a 260 Mbps link); **no added latency** (residence
within ±6 ms of off — a copy fills a slot already queued); 0 send errors;
encoder CPU, fps, spikes unchanged.

## The rule, and why the user overrode its letter

The pre-registered reading failed **one** clause — video `fec_recovered`
outside the A range — **because it came in lower** (3.2, 3.6/min against
11.5, 5.0), with post-FEC video loss also lower (4.8, 3.0 against 16.1,
10.8). The clause guards against redundancy hurting video; it did not.
Whether it helps video is not settled by two pairs. The user adopted.

## The user's listen

Verbatim, user-stated, not a gate: *"sound good"* (2026-09-23, with 2 / 4
in force).

## Reversal

`audio_redundancy_copies=1` in the profile (or
`PRIVYHUB_AUDIO_REDUNDANCY_COPIES=1` for one session) and
`systemctl --user restart privyhub-companion`. The client follows the
response; an older companion without the field means off.
