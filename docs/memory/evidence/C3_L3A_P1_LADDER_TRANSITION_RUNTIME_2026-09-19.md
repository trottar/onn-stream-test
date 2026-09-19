---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: e347ed6b7055ef78d9620fe8970fb231c22c0820
---

# C3.L3a Part 1 — chained ladder transitions, runtime validated

## Classification

**COMPLETE / RUNTIME VALIDATED**

Six chained encoder-only transitions in one session, both directions, ending
at the 7000 kbps reference. Host side and client side both confirm it.

Sources:

- `logs/streaming/c3_l3a_p1_ladder_walk.txt` — per-transition companion
  responses and the before/after stream status;
- `logs/games/native_video_alpha.log` — the six
  `C3.L3a Linux validated-ladder transition probe:` begin/active pairs;
- `logs/games/decoder_sessions/native_decoder_20260919_181328_360.json` —
  the client's view of the same six transitions.

## The walk

```
7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000
```

The first transition fired during an aborted run whose HTTP response was lost
to a broken pipe in the operator's shell pipeline; the host log records it
completing, and the next transition's `from_bitrate_kbps` of 6000 confirms the
state it left behind. The remaining five are fully captured.

A redundant `-> 6000` issued while already at 6000 was rejected with
`bitrate_transition_noop` before any modification. That is one of the three
Windows error strings the Linux port reuses, and it is now runtime-confirmed
rather than argued from source.

## Host side

Every transition returned `ok`, schema
`privyhub_c3_validated_bitrate_transition_v1`, mode
`validated_ladder_actuator_probe`.

| transition | spawn_ms | first_rtp_resume_ms | rtp_silence_ms | host_verified_ms |
| --- | ---: | ---: | ---: | ---: |
| 6000 -> 5500 | 265.78 | 428.20 | 162.42 | 1180.64 |
| 5500 -> 5000 | 265.59 | 427.53 | 161.95 | 1180.29 |
| 5000 -> 5500 | 265.50 | 417.88 | 152.38 | 1171.81 |
| 5500 -> 6000 | 265.60 | 417.68 | 152.08 | 1170.67 |
| 6000 -> 7000 | 265.95 | 417.68 | 151.73 | 1171.08 |

Lifecycle, all five: `fec.send_errors_delta` 0, `audio.send_errors_delta` 0,
`controller.bad_packets_delta` 0; FEC, audio and controller each reported
active before, mid-cycle and after. `capture_restarted` false,
`encoder_restarted` true — the correct Linux single-process shape.

`from_bitrate_kbps` chains exactly: each equals the previous target. Status
after the walk: active, ready, `bitrate_kbps` 7000, `reference_bitrate_kbps`
7000, FEC running with zero send errors, audio active with zero send errors,
controller active with zero bad packets.

Spawn time spread across five restarts is **0.45 ms**.

## Client side

`native_decoder_20260919_181328_360.json`, 306,273 ms session:
`ssrc_changes` **6**, matching the six transitions one for one.

All six discontinuities are typed `ssrc_change` with `jump_packets: 0` — no
sequence disruption accompanied any of them.

| `elapsed_ms` | first IDR at | `resync_to_idr_ms` | AU complete | FEC repaired | unrecoverable group |
| ---: | ---: | ---: | --- | --- | --- |
| 169,935 | 169,959 | 24 | true | false | false |
| 266,137 | 266,162 | 24 | true | false | false |
| 273,331 | 273,349 | **18** | true | false | false |
| 280,541 | 280,607 | **65** | true | false | false |
| 287,698 | 287,727 | 29 | true | false | false |
| 294,880 | 294,910 | 30 | true | false | false |

Inter-transition spacing for the five chained ones: 7,194 / 7,210 / 7,157 /
7,182 ms, matching the scripted 6 s dwell plus the ~1.2 s cycle. The
96,202 ms gap before the second is the debugging pause between the aborted
run and the successful one.

## What this adds beyond Part 1's acceptance

**The `C3.L2a` result is no longer a single sample.** That answer — the
actuator's first IDR is accepted promptly, complete and unrepaired — rested on
one cycle at 27 ms. These six transitions land at 18-65 ms, mean ~32 ms, every
one complete and unrepaired. Seven observations now, across both directions
and four bitrate levels, against 195/210/332/202/205 ms for the ordinary
sequence resyncs on record.

**Upward transitions and 7000-as-target work.** Neither had ever run on Linux;
both were impossible before this patch. Nothing distinguishes them from
downward transitions in any measured field.

**Chained transitions resume faster than from-reference cycles.**
`first_rtp_resume_ms` here is 417.7-428.2 ms against `C3.L3`'s 519.4 / 667.1 /
517.5 ms. Recorded as an observation; one sequence, not a finding.

Within this walk the two downward transitions resumed at ~427.9 ms and the
three upward at ~417.8 ms. **Direction is confounded with ordering** — the two
downward ones were also the first two executed — so this is not evidence of a
direction effect. `C3.L3a` Part 2 randomizes shape order and can separate it.

## Session-level context, and what it does not show

The walk session's `decoder_max_output_gap_ms` was 440 ms over 306 s. It also
recorded six ordinary `sequence_resyncs` alongside the six `ssrc_change`
events, and this record does **not** establish which produced the 440 ms gap —
the slow-event rows were not correlated against the discontinuity list here.

What the surrounding sessions do show is that the transitions are not the
dominant stall source on this host today:

| session | duration | transitions | `max_output_gap_ms` | `lost_packets` |
| --- | ---: | ---: | ---: | ---: |
| 18:06:50 | 100.5 s | **0** | 588 | 1,115 |
| 18:13:28 (the walk) | 306.3 s | **6** | **440** | 2,462 |
| 18:19:26 | 89.1 s | **0** | 620 | 1,089 |

The session containing six transitions had a **lower** worst-case gap than
both sessions containing none. That is not proof transitions are free; it is
direct evidence that ambient conditions dominate them at present.

**The host is in a worse transport state today than during `C3.L3`.** Loss
runs 1,089-2,462 packets per session with 0-5 unrecoverable FEC groups, and a
14:51 session with no actuator activity at all recorded a 1,271 ms gap.
`C3.L3` yesterday ranged 2-425 lost packets and 219-584 ms gaps. Any `C3.L3a`
Part 2 run taken under today's conditions should record that, and gap figures
should not be compared across the two days.

## What is not established

- Which event produced the walk session's 440 ms gap.
- Whether transition direction affects resume time. Confounded with ordering
  here.
- Anything perceptual. No one judged the picture and no marks were taken.
  This is Part 1 — the mechanism — and it does **not** advance the `C3.L4`
  gate, which `C3.L3a` Part 2 performs.
- Two of the three reused guards.
  `validated_transition_requires_validated_start` and
  `unsupported_validated_bitrate` are unreachable over HTTP by construction,
  because the route allowlist and the Linux ladder are now the same set. They
  remain source-verified only.

## Privacy

No network addresses appear in this record.
