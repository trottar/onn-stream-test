---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-R5 — the receiver's loss counters in the heartbeat

## Classification

**RUNTIME VALIDATED.** Every check passes. One 20-minute attract-mode
session, zero input: **597 heartbeats, all carrying all seven new counters**
under schema `privyhub_native_stream_heartbeat_v2`; **all seven loss
counters at the last heartbeat match the session report exactly**; and the
per-minute series **accounts for the report's `lost_packets` to the
packet** — 2,212 in the series + 6 before the first heartbeat + 0 after the
last = **2,218 = the report's 2,218**.

**The project now has a per-minute loss series for the first time**, and on
its first use it resolved what `D-BASE-P4` could only infer: **loss inside a
single session ran 0 to 303 packets per minute** while the radio moved 2 dB
and the link speed did not move at all.

## The change

Client heartbeat payload only, plus passthrough. Full detail in
`patches/D-BASE-R5_HEARTBEAT_LOSS_COUNTERS.md`. APK
`8d6004fd…26e1`, **hash-verified against the installed package on the
device** before the session was treated as evidence.

The seven fields are read from the **same `receiver.snapshot()` the
heartbeat already took** for `rx_packets`: `lost_packets`,
`lost_packets_in_resyncs`, `forward_gap_events`, `max_forward_gap_packets`,
`stream_resyncs` (sequence resyncs + SSRC changes), `fec_recovered_packets`,
`fec_unrecoverable_groups`. **Nothing new is sampled, counted or threaded.**

`native-stream-status` gained `loss_per_min_recent` — loss over the last
60 s of the current session, clocked on the client's own `elapsed_ms`.

## CHECK 1 — every heartbeat carries the new fields

**PASS.** 597 of 597, zero missing any field. One schema across the whole
session: `privyhub_native_stream_heartbeat_v2`.

Heartbeat cadence held: interval min 2,005 ms, median 2,009, **max
2,511** — no interval over 4 s, so **no heartbeat was dropped** and the
series has no holes.

## CHECK 2 — last heartbeat against the session report

**PASS on all seven loss counters, exactly.**

| field | last heartbeat | report | delta |
| --- | ---: | ---: | ---: |
| `lost_packets` | 2,218 | 2,218 | **0** |
| `lost_packets_in_resyncs` | 0 | 0 | **0** |
| `forward_gap_events` | 175 | 175 | **0** |
| `max_forward_gap_packets` | 48 | 48 | **0** |
| `stream_resyncs` | 0 | 0 | **0** |
| `fec_recovered_packets` | 94 | 94 | **0** |
| `fec_unrecoverable_groups` | 38 | 38 | **0** |
| `rx_packets` | 985,748 | 987,058 | 1,310 |

**`rx_packets` is the one that differs, and it should.** The last heartbeat
was posted at elapsed 1,205,252 ms and the report covers 1,206,893 ms, so
**1,641 ms of stream followed it** — about 1,310 packets at the observed
rate. That the *loss* counters match exactly across that same 1.6 s says
only that nothing was lost in it, which is consistent with minute 20's near
zero. The counters are cumulative and read from one snapshot, so this is
the expected end-of-session boundary, not a discrepancy.

## CHECK 3 — the series accounts for the report

**PASS, to the packet.**

```text
series sum 2212  +  first-heartbeat head 6  +  post-last tail 0  =  2218
report lost_packets                                              =  2218
```

The head is the loss before the first heartbeat (elapsed 7,114 ms, the
first tick after the session opened); the tail is loss after the last. Both
are named rather than absorbed, because a reader differencing the log alone
will land on 2,212 and should know why.

## CHECK 4 — the 20-minute loss series, with the radio beside it

The radio series is a post-session `WifiScoreReport` harvest (`D-BASE-P4`'s
method), which costs the run nothing.

| min | lost | gap events | rx | RSSI | txLink |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 4 | 2 | 44,979 | −66 | 260 |
| 1 | 9 | 4 | 49,131 | −66 | 260 |
| **2** | **159** | 11 | 47,592 | −66 | 228 |
| 3 | 5 | 2 | 50,307 | −66 | 260 |
| **4** | **230** | 11 | 48,969 | −67 | 260 |
| **5** | **161** | 10 | 49,086 | −66 | 260 |
| **6** | **303** | 34 | 49,663 | −66 | 260 |
| 7 | 0 | 0 | 47,392 | −67 | 260 |
| 8 | 78 | 10 | 49,152 | −65 | 260 |
| 9 | 72 | 4 | 49,827 | −66 | 260 |
| 10 | 128 | 10 | 49,163 | −66 | 260 |
| 11 | 152 | 9 | 49,221 | −65 | 260 |
| **12** | **203** | 12 | 49,193 | −66 | 260 |
| 13 | 2 | 1 | 49,162 | −65 | 260 |
| 14 | 146 | 11 | 47,260 | −66 | 260 |
| 15 | 0 | 0 | 50,009 | −66 | 260 |
| 16 | 87 | 7 | 49,255 | −65 | 260 |
| **17** | **228** | 17 | 49,263 | −65 | 260 |
| **18** | **236** | 15 | 49,206 | −65 | 260 |
| 19 | 7 | 2 | 49,090 | −65 | 260 |
| 20 | 2 | 1 | 3,276 | — | — |

**The twenty numbers:** 4, 9, 159, 5, 230, 161, 303, 0, 78, 72, 128, 152,
203, 2, 146, 0, 87, 228, 236, 7 (and 2 for the partial minute 20).

Median **87/min**, minimum **0**, maximum **303**. **Burst minutes at or
above twice the median: 4, 6, 12, 17, 18.** Minute 6 is the worst — 303
packets across **34 forward-gap events**.

**And the radio does not move with any of it.** RSSI spans **−65 to −67**
across the whole session, and `txLinkSpeed` reads **260 in twenty of the
twenty-one minutes** (228 in minute 2). Minute 6 lost 303 packets at RSSI
−66 / 260 Mbps; minute 15 lost **zero** at RSSI −66 / 260 Mbps. **The same
radio reading covers the best and the worst minute of the session.**

This is `D-BASE-P4`'s conclusion reproduced at sixty times the resolution
and with a direct loss measurement rather than an inferred one: **the air,
as this client can see it, does not explain the loss** — and the loss is
**episodic within a single session**, not merely between sessions.

## CHECK 5 — did the heartbeat get more expensive?

| | before | after |
| --- | ---: | ---: |
| heartbeat line | **276 bytes** | **465 bytes** median (449-468) |
| `spike_20_ms` / min | — | **51.5** |
| rendered fps | — | **59.70** |
| `max_output_gap_ms` | — | 343 |
| discontinuities | — | 0 |

**51.5 spikes/min sits inside `D-BASE-P4`'s seven-session range of
40.6-62.4**, and fps is at the top of the observed band. The payload grew
69 % and **nothing the client reports about its own timing moved.**

## The heartbeat log rotated mid-session — and rotation is now proven

**`KNOWN_ISSUES` has carried "rotation has never run against real traffic"
since `D-BASE-R4`. It has now run.** The log crossed 4 MiB at **22:09:38,
about 17.9 minutes into this session**, and rotated to
`stream_log_archive/native_stream_heartbeat.log.1` (4,194,628 bytes).

**It lost nothing:**

| | |
| --- | --- |
| archive last | seq **534**, elapsed 1,072,687 ms |
| fresh log first | seq **535**, elapsed 1,074,694 ms |
| sequence step | **1** — no line lost |
| elapsed step | **2,007 ms** — exactly one heartbeat interval |

**R5 is what brought it forward.** At 465 bytes a line and ~30 lines a
minute the log now grows **~819 KB/h**, so it fills 4 MiB in **~5.0 hours**
of continuous streaming against the **~453 KB/h and ~9 hours** on record
before this change. That figure in `KNOWN_ISSUES` is now stale and is
corrected there.

**One harness lesson, worth more than the run.** The session harness sliced
the heartbeat log by line offset taken before the session — and rotation
made the file *shorter* than that offset, so the slice came back **empty**.
The 597 heartbeats were recovered by reading the archive and the fresh log
together and filtering on a rising `elapsed_ms`. **Any tool that slices this
log by offset is wrong across a rotation**; filter on the session's
`elapsed_ms` run instead. `TOOLS.md` now says so.

## `loss_per_min_recent`, live

Sampled six times during the session, without waiting for a report:

| session elapsed | window | lost | **loss/min** | gap events |
| ---: | ---: | ---: | ---: | ---: |
| 176 s | 60.3 s | 159 | **158.2** | 11 |
| 347 s | 60.3 s | 206 | **205.0** | 10 |
| 518 s | 60.3 s | 76 | **75.7** | 9 |
| 689 s | 60.3 s | 126 | **125.5** | 9 |
| 860 s | 60.3 s | 24 | **23.9** | 3 |
| 1,031 s | 60.2 s | 87 | **86.7** | 7 |

Each window closed on 31 heartbeats and 60.2-60.3 s, so the 60 s target is
being hit. The values track the per-minute series and show the same
episodic swing — **24 to 205 per minute, on one link, inside twenty
minutes.**

## Offline checks, run before the build

`loss_per_min_recent` against synthetic logs: **60.0/min over a 60.0 s
window** for 2 lost per 2 s tick; window **confined to the current session**
when `elapsed_ms` restarts at zero; **None, not 0**, for a client sending no
loss fields and for a log holding one heartbeat; and
`latest_native_stream_heartbeat` still reads v1-shaped records.

## A correction to `TOOLS.md`

The Android build line said "from the repository root: `sh ./gradlew …`".
**The wrapper is in `PrivyHub/`**, and running it from the root fails with
`sh: 0: cannot open ./gradlew: No such file` — which cost this task a build
before it was noticed. Corrected, with the warm build time (~16 s) and the
step of hashing the built APK against `pm path` on the device.
