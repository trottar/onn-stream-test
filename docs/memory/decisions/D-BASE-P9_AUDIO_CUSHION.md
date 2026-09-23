---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 3e6cde5
status: DECIDED 2026-09-23 by the user (spend +45 ms); MEASURED (P9, P9a interleaved); 12 / 17 ADOPTED as the profile default by the user 2026-09-23 (D-BASE-T2 Part 0)
---

# Decision — the audio cushion is a declared setting; +45 ms measured

## The decision (the user's)

On 2026-09-23 the user decided to **spend the +45 ms of audio latency**
that `P7` priced, because `P7` and `P8` established the audio arrival
holes are the path's (p90 ≈ 60 ms, ~100/min ≥ 40 ms) and a deeper client
cushion is the only client lever. Asked before any session — the code
makes the **capacity**, not the target, set the running depth — the user
chose to measure **both 12 / 17 (+45 ms) and the handoff's 12 / 24**
against a fresh 3 / 8.

## What is now true in the code

`audio_queue_target_packets` / `audio_queue_capacity_packets` are fields
of `native_game_720p60_reference`, passed to the client in the
stream-start response (`audio_cushion`), overridable per session with
`PRIVYHUB_AUDIO_QUEUE_{TARGET,CAPACITY}_PACKETS`, reported in
`native-stream-status` and the decoder report. **Default: 12 / 17 since
2026-09-23 (adopted, below); 3 / 8 before.**

## The measured cost (`evidence/D_BASE_P9_AUDIO_CUSHION_2026-09-23.md`)

| | starvation/min | underruns | avg residence | Δ latency |
| --- | ---: | ---: | ---: | ---: |
| 3 / 8 | 42.4 | 20 | 30.7 ms | — |
| **12 / 17** | **0.8** | 25 | 66.7 ms | **+36.0 ms** |
| 12 / 24 | 0.1 | 16 | 102.4 ms | +71.7 ms |

## Why the default is 3 / 8

The handoff pre-registered: works if the drop is ≥ 80 %, `underruns` ≤
the baseline's and the residence rises 35-55 ms; **does not work if
underruns rise — revert the default, keep the setting.** 12 / 17 met the
first and third and missed the second (20 → 25, one 8-underrun event at
76 s). The rule was applied as written.

## Open for the user

- **Re-adopt 12 / 17** if the user judges 20 → 25 as noise (the counter
  did not track the cushion: 20 / 25 / 16 at 8 / 17 / 24) — a two-number
  edit in `companion/native_stream_profiles.py` and a systemd restart; or
  test it by ear first through the environment override (commands in the
  evidence record). **The listen is the user's words, never a gate.**
- 12 / 24 buys 0.7 more starvation events/min for +36 ms more. Not
  proposed.

## P9a — interleaved against noise (2026-09-23)

`evidence/D_BASE_P9A_CUSHION_INTERLEAVED_2026-09-23.md`. A3 / B2 / A4 /
B3 = 3/8, 12/17, 3/8, 12/17, 20 min each:

| | A3 | B2 | A4 | B3 |
| --- | ---: | ---: | ---: | ---: |
| starvation/min | 41.4 | **0.75** | 46.3 | **0.20** |
| avg residence ms | 30.9 | 68.5 | 30.3 | 64.1 |
| underruns | 10 | 12 | 16 | 19 |

- **12/17 costs +33.5-37.9 ms** (P9: +36.0) and removes 98-99.5 % of
  starvation episodes, three times out of three.
- **Its underruns are inside the 3/8 noise band** (4-20 across six 3/8
  sessions, events of 1-3). `P9`'s 20 → 25 was one 8-underrun event and
  did not replicate.
- **The rule as coded fails on one clause**: B3's holes are -22.5 %
  against A4 — but A4 is +28 % above A3 and every earlier 3/8 session, so
  the tolerance is broken by the baseline's own spread. Against the A mean
  every clause passes.
- **The user chose: keep 3 / 8, decide later.** Nothing changed.

To adopt: `audio_queue_target_packets=12`, `audio_queue_capacity_packets=17`
in `native_game_720p60_reference` (`companion/native_stream_profiles.py`
— the default lives in the companion, no rebuild), then
`systemctl --user restart privyhub-companion`; `audio_cushion.source`
reads `profile`.

## Adopted — 12 / 17 is the profile default (2026-09-23, `D-BASE-T2` Part 0)

**The user adopted 12 / 17.** Their standing decision was to spend the
+45 ms; `P9a` removed the underrun objection (inside the 3/8 band) and the
one failed clause was a hole check against a baseline arm that disagreed
with its sibling by 28 % — arrivals the cushion cannot move. **The
measured cost: +33.5 to +37.9 ms of audio queue residence** (three
sessions; 30.3-30.9 → 64.1-68.5 ms), for **-98 to -99.5 %** of
starvation episodes.

**The user's listen, verbatim, user-stated, not a gate:** *"No issues
from playing for a minute or two."*

In force: `native_game_720p60_reference` 12 / 17
(`companion/native_stream_profiles.py`), `audio_cushion.source`
`profile`, nothing in the environment; **no client build** — the default
is the companion's and reaches the client in the stream-start response.
Patch record `patches/D-BASE-T2_P0_AUDIO_CUSHION_ADOPTED.md`.

