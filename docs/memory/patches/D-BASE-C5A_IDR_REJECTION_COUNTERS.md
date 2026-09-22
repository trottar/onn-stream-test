---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# C5a — IDR-rejection counters at the completeness gate

## Purpose

`C5` read the resync path and found that the completeness check runs
**before** the IDR check (`RtpH264Receiver.kt:2154`), so an access unit that
arrives corrupt while `waitingForIdr` is discarded without anyone asking
whether it was an IDR. If those AUs are IDRs, each rejection costs the
resync a further GOP, which would explain ordinary resyncs measuring
195-332 ms against 18-65 ms for actuator-driven ones. Nothing in the report
could show it. These are that record's §4 probe: counters only, so the
corpus can answer the question the next time a real resync occurs.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt`:
  `41c0db2097290f8cea894279c692fb5412cfa449619612954861266b36977b54`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `51dab63f996fd8dd85e72f137e59553ad58aa9366fc5cb0c48d0704ff637f551`

## Changed scope

**`RtpH264Receiver.kt`**
-> `8e314115ad8cd2f044807038b6ec1887fd674e5b6807d5f2fbdb0fb5b0846162`.
Two session counters, `idrAusRejectedWaitingForIdr` and
`nonIdrAusDroppedWaitingForIdr`, incremented in the marker block's corrupt
branch — the branch that **already** drops every AU it sees, so the added
`containsNalType(frame, 5)` inspection is for counting only. Two matching
per-episode counters reset in `beginStreamResync` and carried into
`FirstIdrAfterDiscontinuity` as `rejectedIdrAus` / `droppedNonIdrAus`.
The non-corrupt branch's existing non-IDR drop also increments the second
counter, so the two together account for every AU discarded while waiting.

**`NativeStreamActivity.kt`**
-> `96f2168d4748a85fe31f5f30440f7e6e1903492a229d0a3c2fa3c4997fe5785e`.
`video.idr_aus_rejected_waiting_for_idr`,
`video.non_idr_aus_dropped_waiting_for_idr`, and `rejected_idr_aus` /
`dropped_non_idr_aus` on each `first_idr_after_discontinuity` row.

APK: `c3252ab5fda3e0986adc896ad2b2e856010ffc60484834b6a83422558270c718`.

**Unchanged — the receiver's output does not differ by one byte.** Which
AUs are delivered, `RESYNC_FORWARD_GAP_PACKETS`, `beginStreamResync` /
`completeStreamResync` behaviour, the FU-A reassembly path, SPS/PPS
handling, the decoder, the companion, every streaming constant. The new
inspection runs only while `waitingForIdr`, so the steady-state path is
untouched.

## Validation performed

- `git diff --check` clean; real `sh ./gradlew :app:assembleDebug
  --no-daemon`; `adb install -r`; companion restarted with 8765 checked
  free (D-068);
- three 150 s sessions per the task's SIGSTOP substitute, plus one
  control session using the C3.L1 encoder-only restart;
- teardown per `TOOLS.md`: game stopped, banner confirmed clear, companion
  stopped, no process in state `T`, no listener on 8765 / 48100-48102 /
  48110.

## Result

**INDETERMINATE.** Record:
`evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md`.

The counters are correct and **proven wired end-to-end** — the control
session drove the resync path four times and every
`first_idr_after_discontinuity` row carried the two new fields. What failed
is the fault injection. A 0.3 s SIGSTOP of the encoder produces **no
sequence gap at all**: a stopped encoder emits nothing, so it burns no RTP
sequence numbers and the sequence resumes contiguous. The task's premise —
R3a's 720/984/480-packet jumps — came from encoder *restarts* (new SSRC),
not from short stalls. Across the three sessions the largest forward gap
was **47 packets** against the 128-packet threshold, so
`shouldResyncForSequenceJump` never fired and there was nothing to count.

The four induced discontinuities all resynced in 18-24 ms with zero
rejected IDRs — consistent with the hypothesis' `<= 250 ms` limb, unable to
test its `> 250 ms` limb. Four is below the pre-registered floor of six and
none exceeded 250 ms, so the rule returns INDETERMINATE on both counts.

The counters stay in the tree to accumulate against natural resyncs, as the
task directs. The bounded fallback is **not** implemented; it remains a
separate decision.

**Untested:** the `rejectedIdrAus` path itself has never incremented — no
corrupt AU has been seen while waiting. It is reachable only through a real
>= 128-packet loss run, which needs the nftables injection that still
cannot run without non-interactive root.
