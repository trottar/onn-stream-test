---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
status: C5 COMPLETE, but its §2 second cost is **FALSIFIED** (2026-09-21, `D-BASE-S2`): six of seven natural resyncs over 250 ms rejected zero IDRs, one at 240 ms rejected one, and the long tail tracks `dropped_non_idr_aus`, i.e. waiting for an IDR to arrive on a lossy link. §5's bounded fallback is retired with it. Original status: COMPLETE — analysis only, no code changed, no build, no install. The §4 probe was built as `C5a` on 2026-09-21 and returned INDETERMINATE (no injection without root produces a sequence resync); see `../evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md`. §5's bounded fallback remains unauthorized.
---

# C5 — receiver resync and IDR-acceptance read

Battery item §C5. The question: `C3.L2a` and `C3.L3a` Part 1 measured
ordinary sequence resyncs at 195-332 ms against 18-65 ms for
actuator-driven IDRs. GOP is 15 frames at 60 fps, so an IDR arrives within
250 ms of any point — a 195-332 ms wait is either one full GOP every time,
or a wait for something other than the next IDR. **It is both, and the
corpus separates them.**

Line numbers are
`PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt` unless said
otherwise.

## 1. The resync path, step by step

**Trigger (630-698).** Every datagram is checked twice. A changed SSRC
calls `beginStreamResync(type = "ssrc_change", jumpPackets = 0)` (662). An
unchanged SSRC with a forward sequence jump of **>= 128 packets**
(`RESYNC_FORWARD_GAP_PACKETS`, 108-109; test at 832-859) calls it with
`type = "sequence_resync"` and the jump size (691). 128 packets is chosen
because an 8+1 XOR group cannot repair that much (108).

**`beginStreamResync` (862-959) discards everything and re-arms.** It
counts the resync, adds the jump to `lostPackets` and to
`lostPacketsInResyncs` (`D-BASE-R1`, 879-891), records the discontinuity
(893-899) and fires `onStreamDiscontinuity` (903). Then it resets the
receiver's whole reassembly state: `activeSsrc`, `orderedLastSequence = -1`
(911), `gapHoldStartedNs = 0`, **`heldPackets.clear()`,
`recentPackets.clear()`, `fecGroups.clear()`** (915-925), `lastSequence =
-1`, `currentTimestamp = -1`, the current access unit and its flags
(927-951), and finally **`waitingForIdr = true`** with
`resyncStartedNs = nowNs` (953-958).

Three consequences worth naming:

- **The access unit in flight at that moment is orphaned.** Its earlier
  packets are gone from `accessUnit`, and because `orderedLastSequence` is
  -1 the *next* packet to arrive is accepted unconditionally as the new
  frontier (`acceptOrderedPacket`, 1013-1026). Any packet of that AU still
  in flight arrives "behind the frontier" and is silently dropped (the
  comment at 1094-1096). So the wait never starts at a usable AU boundary;
  it starts at the next one.
- **FEC cannot repair across the boundary.** `recentPackets` and
  `fecGroups` are cleared, so parity that would have repaired a packet lost
  just before the resync is thrown away with it.
- **The decoder is neither flushed nor reconfigured.** `onStreamDiscontinuity`
  does exactly one thing on the client
  (`NativeStreamActivity.kt` 648-659): `decoder?.markCycleWindow(...)`,
  which only protects slow-event rows from eviction. `onParameterSets`
  (2526-2533) fires whenever SPS and PPS are both known, but the activity
  constructs `AvcLowLatencyDecoder` only `if (decoder == null)`
  (`NativeStreamActivity.kt` 604-615), so later parameter sets are ignored
  and MediaCodec is configured **once per session**. Nothing in the resync
  path touches the codec.

**The wait (2117-2181).** Reassembly continues normally; NAL payloads are
appended to `accessUnit` (2082-2112) and `observeParameterSet` records SPS
(7) and PPS (8) as they pass (2496-2521). On the RTP marker bit the
assembled AU is judged:

```
2117  if (marker) {
2118      if (!currentCorrupt && accessUnit.size() > 0) {
2119          val frame = accessUnit.toByteArray()
2120          val isIdr = containsNalType(frame, 5)
2127          if (waitingForIdr && !isIdr) {          -> dropped, counted
2137          } else { if (waitingForIdr && isIdr) completeStreamResync(...) }
2165      } else {                                    -> dropped, counted
```

**Two gates, not one.** An AU is delivered only if it is **complete**
(`!currentCorrupt`, 2118) *and*, while `waitingForIdr`, **contains NAL type
5** (2120, 2127). `currentCorrupt` is set by any sequence gap inside the AU
(`sequenceGap` at 2031-2041, carried into `currentCorrupt` at 2069-2070).
So **an IDR that lost a single packet fails the first gate and is discarded
whole** (2165-2166), `waitingForIdr` stays true, and the receiver waits for
the *next* IDR — a further GOP.

**Completion (2245-2337).** `completeStreamResync` clears `waitingForIdr`,
sets `resyncToIdrMs` from `resyncStartedNs`, updates
`maxResyncToIdrMs`, and appends a `FirstIdrAfterDiscontinuity` row with
`au_complete`, `au_fec_recovered` and `au_fec_unrecoverable_group`. The AU
is then delivered to the decoder in the same pass (2151-2159).

**Where the 195-332 ms can go**, in order:

| segment | bound | owner |
| --- | --- | --- |
| orphaned in-flight AU | up to one frame time, ~16.7 ms | the frontier reset (911-925) |
| wait to the next IDR | 0-250 ms, GOP 15 at 60 fps | the encoder's GOP |
| **each rejected IDR** | **+250 ms each, unbounded** | the completeness gate (2118) |
| decode of the accepted IDR | not included | — |

**The figure contains no decoder time at all.** Everything dropped while
`waitingForIdr` is dropped before `onAccessUnit` is called, so those frames
never reach `AvcLowLatencyDecoder` and cannot be stale-dropped. Question
2(c) is answered by construction: **the resync time cannot include frames
the decoder produced and threw away.**

## 2. Why 18-65 ms for an actuator IDR and 195-332 ms for a resync

**(a) It is not waiting for parameter sets.** The encoder repeats SPS and
PPS with every IDR on this build, and the evidence is already on disk. The
A1-live on-wire capture (10 s of the production command,
`evidence/group_a_2026-09-20/a1_a3_live_summary.json`) counted
**nal_unit_type 5 = 40, type 7 = 41, type 8 = 41**, against 560 type-1 and
600 type-6. Forty IDRs, forty-one SPS and forty-one PPS — one pair per IDR
plus the stream header. The hypothesis that an ordinary resync waits for
parameter sets that only arrive with the next *actuator* restart is
**falsified**, and with it the "bounded by nothing" worry. (The command
itself, `companion/native_stream.py` 1112-1150, sets `-g 15`, `-bf 0`,
`h264_vaapi`, `-f rtp`; it carries no `-bsf:v dump_extra` and no explicit
repeat-headers flag, so the repetition comes from the VAAPI encoder's own
output — which is why it had to be confirmed on the wire rather than read
off the command line.)

**(b) A complete IDR arriving before the receiver re-arms is not
discarded.** `beginStreamResync` runs synchronously inside the datagram
path (662, 691) *before* the triggering packet is handed to
`acceptOrderedPacket` (738-741), and `waitingForIdr` is set inside it. With
`orderedLastSequence` at -1 the next packet is taken unconditionally. There
is no window where the receiver is "not yet armed". The loss is the other
way round: the remainder of the orphaned AU is discarded, as above.

**(c) Not stale drops.** See §1: the wait is entirely upstream of the
decoder.

**So the difference is what the two events deliver.** An actuator restart
kills and respawns the encoder: the replacement opens with parameter sets
and an IDR as its very first output, and the SSRC change is observed on
that same first packet — the receiver re-arms and the IDR is already there.
An ordinary resync re-arms mid-GOP and must wait for the encoder's next
scheduled IDR, **and survive it intact**.

## 3. The corpus

All decoder reports since 2026-09-16, sessions >= 15 s. Script:
`evidence/c5_2026-09-20/c5_resync_idr_distribution.py` (a copy of the
Group A loader shape, extended; **the Group A script is unmodified**).
Result: `evidence/c5_2026-09-20/c5_resync_idr_result.json`.

Selection: 177 sessions, of which **100 carry the per-discontinuity lists**
(they exist only from the `C3.L2b` build onward), giving **167
discontinuities**, 151 of them with a recorded first IDR. Twenty-three
older sessions have resyncs but only a whole-session
`max_resync_to_idr_ms`, which cannot be attributed to one resync and is
reported separately in the JSON.

`resync_to_idr_ms`, by discontinuity type:

| type | n | p50 | p90 | max | min | mean | > 250 ms | > 500 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sequence_resync` | 104 | **204.5** | **484.2** | **2,555** | 20 | 294.8 | **32** | **10** |
| `ssrc_change` (actuator) | 47 | **27.0** | 45.2 | 76 | 15 | 30.5 | **0** | 0 |

The `ssrc_change` column reproduces `C3.L2a` E2 and `C3.L3a` Part 1 on a
much larger sample: 47 actuator IDRs, none over 76 ms, none over one GOP.

**The shape of the `sequence_resync` column is the finding.** Bucketed by
whole GOPs:

| bucket | count |
| --- | ---: |
| 0-250 ms | **72** (69.2 %) |
| 250-500 ms | 22 |
| 500-750 ms | 3 |
| 750-1,000 ms | 2 |
| 1,250-1,500 ms | 2 |
| 1,500-1,750 ms | 1 |
| 2,250-2,500 ms | 1 |
| 2,500-2,750 ms | 1 |

**If the receiver simply took the next in-GOP IDR, no value could exceed
250 ms.** Thirty-two do — 31 % — and ten exceed two GOPs, out to 2,555 ms,
about ten GOPs. Each step of ~250 ms is one IDR the receiver saw and
rejected.

Supporting numbers from the same rows:

- **`au_complete` is `true` for all 151 accepted first-IDRs**, and false
  for none. The gate admits only complete AUs, so the one finally accepted
  is always complete — it says nothing about how many were rejected first,
  which is exactly what is not instrumented.
- **FEC rescued the accepted IDR once in 104 sequence resyncs** (three
  times across all 151 discontinuities). XOR 8+1 repairs one loss per group
  of eight; Group A measured loss as bursty at a median of 14 packets per
  gap event, which spans two groups and is unrecoverable.
- **Bigger jumps recover faster.** Median wait is **100 ms** for jumps
  >= 256 packets (n = 21) and **210 ms** for smaller jumps (n = 83). A very
  large jump is a long outage that has *ended*, so the stream resumes clean
  and the next IDR survives; a smaller jump is more often ongoing burst
  loss that keeps damaging IDRs. Consistent with the hypothesis below, and
  the opposite of what "bigger break, longer recovery" would predict.
- **Frame size makes the IDR the biggest target.** Across the same corpus,
  15,327,863 packets carried 1,097,971 access units — a mean of **13.96
  packets per frame** at `pkt_size=1200`. An IDR is several times a P-frame,
  so it is the AU most likely to be hit by a 14-packet burst. This is an
  inference from the mean, not a per-frame-type measurement; the receiver
  does not record packets-per-AU by type.

**resync-to-first-render is not instrumented.** The nearest proxy — the
first retained slow-event row at or after each discontinuity — reads p50
278 ms but p90 49,821 ms and max 330,481 ms, because a retained row exists
only when some later frame happened to be slow enough to record. It is a
lower bound on nothing useful and **should not be quoted as a render
latency**; it is in the JSON only so the next reader does not recompute it
and believe it.

## 4. One hypothesis and one probe

**Hypothesis.** *The base cost of an ordinary resync is one GOP — up to
250 ms — because the receiver must wait for the encoder's next scheduled
IDR, and it has no way to ask for one. On top of that, roughly a third of
resyncs pay one or more extra GOPs because the completeness gate at line
2118 discards an IDR access unit that lost any packet, and the burst loss
that caused the resync is often still going.* The 195-332 ms range in the
earlier records is the middle of that distribution; its p50 is 204.5 ms and
its tail reaches 2,555 ms.

**Probe.** *Count the rejections.* Two counters in the receiver, exported
in the session report: **IDR access units discarded while `waitingForIdr`
because `currentCorrupt` was true**, and **non-IDR access units discarded
while `waitingForIdr`** — the latter is the unavoidable GOP wait, the
former is the extra cost. Optionally record the per-discontinuity rejected
count alongside `resync_to_idr_ms` in `first_idr_after_discontinuity`.

The hypothesis is **confirmed** if resyncs over 250 ms carry >= 1 rejected
IDR and those at or under 250 ms carry 0; it is **falsified** if resyncs
over 250 ms show zero rejected IDRs, which would mean the encoder is not
emitting IDRs on the expected 15-frame cadence during loss and the search
moves to the host.

`packetsDroppedWaitingForIdr` already exists but counts *packets* and does
not distinguish an IDR AU from a P AU, so it cannot answer this.

**Not the host-side `ffprobe` of SPS/PPS repetition.** That question is
already answered by A1-live (§2a) and would spend the probe budget
confirming something the evidence on disk has settled.

**Not implemented. It needs authorization** — it touches the receiver,
which is on the do-not-disturb list.

## 5. What a fix would touch, and what it must not

**The minimal change is a bounded fallback on the completeness gate**, not
a new mechanism: after N rejected IDRs, or after a deadline of one further
GOP, accept the next IDR access unit *even if incomplete* and let the
decoder conceal it. That converts an unbounded tail (2,555 ms observed)
into a bounded one at roughly 250-500 ms, and touches one condition at
line 2118 plus a counter and a deadline.

Two alternatives, both worse:

- **Ask the encoder for an IDR on resync.** There is no control channel:
  the encoder is an external FFmpeg CLI with `-nostdin` and no control
  socket (`C3.L0`, durable). The only way to force an IDR is an encoder
  restart — which is the `C3.L1` actuator, whose IDR *is* accepted in 27 ms
  — but that is a production behaviour change, it interacts with
  `D-BASE-R3`'s restart logic and backoff, and it would make every burst of
  loss trigger an encoder restart. Not minimal.
- **Shorten the GOP.** A streaming constant, out of scope by standing rule,
  and it would cost bitrate everywhere to help a minority of resyncs.

**What it must not touch:** the FEC wire format and the 8+1 group
semantics; the ordering and hold path (`acceptOrderedPacket`,
`drainHeldContiguous`, `flushGapIfExpired`); `RESYNC_FORWARD_GAP_PACKETS`;
the decoder configuration and the stale-drop policy; and the discontinuity
and first-IDR reporting, which several records now depend on.

**Runtime evidence needed to accept it**, in order:

1. The probe of §4 first, so the change is aimed at a measured cause rather
   than at this reading.
2. Then, on a build with the bounded fallback: `resync_to_idr_ms` p90 and
   max across a comparable number of resyncs — the claim is that the tail
   beyond one GOP disappears — with `max_output_gap_ms` not regressing and
   `stale_output_drops` not rising.
3. **A perceptual check, which the numbers cannot substitute for.**
   Accepting a damaged IDR trades a longer freeze for a visibly corrupt
   picture that persists until the next clean IDR. `C3.L2c` is the standing
   proof that a timing statistic and a perceptual verdict can point in
   opposite directions, and this change is squarely in that territory.

## Scope

Analysis only. **No production code was changed, nothing was built, nothing
was installed, and no session was run.** The only file added outside this
record is the read-only script and its JSON result under
`evidence/c5_2026-09-20/`.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the generated JSON.
