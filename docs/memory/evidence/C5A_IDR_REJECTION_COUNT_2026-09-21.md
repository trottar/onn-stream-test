---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
status: COUNTERS SHIPPED; the pre-registered rule is still INDETERMINATE — D-BASE-R3b (2026-09-22) produced only 3 discontinuities and the slowest resync was 75 ms, so no resync came near the 250 ms threshold. See evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md. A clean link drop cannot test C5: the encoder restart emits an IDR in 40-75 ms.
---

# C5a — count the rejected IDRs

> **SUPERSEDED 2026-09-21 by `D-BASE-S2`: the C5 hypothesis is
> FALSIFIED.** A 3-hour session on a degrading link produced 94 natural
> sequence resyncs and fired these counters for the first time
> (`idr_aus_rejected_waiting_for_idr` 10). Of the seven retained resyncs
> over 250 ms, **six rejected zero IDRs, including the longest at
> 1,340 ms**, and one resync at **240 ms did reject an IDR** — impossible
> if a rejection costs a further GOP. The long tail tracks
> `dropped_non_idr_aus` (40-67 on the longest rows), i.e. waiting for an
> IDR to arrive at all on a lossy link, not discarding damaged ones. See
> `D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`. Everything below is the
> original record of the probe and of why it could not be decided then.

## Classification

**INDETERMINATE**, on both limbs of the pre-registered rule: **four
discontinuities were obtained against a floor of six, and none exceeded
250 ms** (the four ran 18-24 ms). The C5 hypothesis — that an ordinary
resync spends 195-332 ms because complete IDRs are rejected at the
completeness gate — is therefore **neither confirmed nor falsified**. The
counters stay in the tree for the corpus to accumulate, exactly as the task
directs.

The probe itself is sound and is **proven wired end-to-end** (control
session below). What failed is the *fault injection*, and the reason is
worth recording precisely, because it invalidates a premise the task
inherited.

## Why the SIGSTOP substitute produced no resync

The task specified the `D-BASE-R3` SIGSTOP substitute in short form —
0.3 s stall of the encoder at 30/60/90/120 s — on the strength of the R3a
record's "real sequence jumps (720 / 984 / 480 packets) after SIGCONT".
**That premise does not transfer to a short pulse.** A stopped encoder
*emits nothing*; it does not have packets dropped. RTP sequence numbers are
minted by the sender as it sends, so a paused encoder burns none, and on
SIGCONT the sequence continues contiguously from where it left off. The
stall is a gap in **time**, not in **sequence**. `RESYNC_FORWARD_GAP_PACKETS`
(128) is never approached, `shouldResyncForSequenceJump` never fires, and
there is no resync for the counters to count.

The R3a jumps came from a different mechanism: longer holds that tripped
recovery into a **C3.L1 encoder restart**, which spawns a new encoder with a
new SSRC and a fresh sequence base. That is an `ssrc_change`, not a
sequence jump, and it is the fast path.

The runtime data says the same thing directly. Across the three specified
sessions the link supplied genuine loss — 122, 51 and 228 packets — and
produced 12, 7 and 14 forward-gap events, but the **largest forward gap in
any of them was 47 packets** against the 128 threshold:

| run | duration | packets | lost | fwd-gap events | max fwd gap | seq resyncs | ssrc changes | discontinuities |
|---|---|---|---|---|---|---|---|---|
| R1 | 158.1 s | 131,311 | 122 | 12 | 27 | 0 | 0 | 0 |
| R2 | 158.2 s | 130,925 |  51 |  7 | 26 | 0 | 0 | 0 |
| R3 | 158.5 s | 131,228 | 228 | 14 | 47 | 0 | 0 | 0 |

`desync_pause` is absent from the recovery log for all three, as required —
the pulses stayed below `DESYNC_MS`, so recovery never paused the game. All
twelve pulses landed (logged with timestamps in the harness output); they
simply had no effect on the sequence.

## Session counters

All three specified sessions: `idr_aus_rejected_waiting_for_idr` 0,
`non_idr_aus_dropped_waiting_for_idr` 0, `packets_dropped_waiting_for_idr` 0.

These zeros are **expected and uninformative**, not evidence of anything.
`waitingForIdr` initialises `true` (RtpH264Receiver.kt:321), so the counters
could in principle fire at session start — but they cannot on this system:
the encoder starts *with* the client, so the first access unit the receiver
ever sees is the stream's opening IDR. `first_clean_idr_ms` was 577 / 577 /
607 ms, and nothing arrived before it. Outside startup, the counters are
reachable only through `beginStreamResync`, which needs the >= 128-packet
forward gap that never occurred.

## Control session — the instrumentation is wired

Because three zeros could mean "nothing to count" or "counter never
reached", one further session was run to separate those. **This is not one
of the three specified runs and is labelled CTRL throughout**; it replaces
the SIGSTOP pulse with the already-validated C3.L1 encoder-only restart
primitive (`POST /plugins/games/c3-actuator-continuity-cycle`) at the same
four marks. That is a deliberate step past the task's stated injection,
taken so the record would not rest on unexercised code, and it changes no
classification: an `ssrc_change` resync is the fast path by construction
and cannot test the > 250 ms limb.

| elapsed | type | jump_packets | resync_to_idr_ms | rejected_idr_aus | dropped_non_idr_aus | au_complete |
|---|---|---|---|---|---|---|
| 36,460 ms | ssrc_change | 0 | 18 | 0 | 0 | true |
| 67,684 ms | ssrc_change | 0 | 22 | 0 | 0 | true |
| 98,849 ms | ssrc_change | 0 | 22 | 0 | 0 | true |
| 130,047 ms | ssrc_change | 0 | 24 | 0 | 0 | true |

The resync path executed four times, `beginStreamResync` /
`completeStreamResync` ran, and the two new per-row fields were emitted on
every row. The 18-24 ms sits inside C5's 18-65 ms actuator band, confirming
the corpus reading on independent runs. All four are <= 250 ms and all four
carry `rejected_idr_aus` 0 — **consistent with** the hypothesis' easy limb
(fast resyncs reject nothing), which is not the same as support for it.

## First natural resyncs, 2026-09-21 (from `D-BASE-P2b`)

The counters fired for the first time a few hours later, on a session run
for `D-BASE-P2b` and rejected by that task for an early discontinuity:

| elapsed | type | jump_packets | resync_to_idr_ms | rejected_idr_aus | dropped_non_idr_aus | au_complete |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 4,446 ms | sequence_resync | 302 | 98 | 0 | 11 | true |
| 29,291 ms | sequence_resync | 151 | 263 | 0 | 14 | true |

Two discontinuities, so the pre-registered rule still returns
**INDETERMINATE** (floor of six). The direction is against the hypothesis:
**the one resync over 250 ms rejected zero IDRs** and accepted a complete
IDR after discarding 14 non-IDR access units — the plain GOP wait, not a
rejected IDR. Four more discontinuities decide it. Record:
`D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`.

## What is still owed

A genuine sequence resync needs >= 128 consecutive packets to vanish *on
the wire*. Neither available injection produces that:

- **SIGSTOP of the encoder** — no packets sent, no sequence burned. Ruled
  out above, at any pulse length short of tripping a restart.
- **C3.L1 encoder restart** — `ssrc_change`, the fast path. Ruled out by
  construction.
- **nftables drop of a packet run** — the only injection that creates real
  loss, and it is the one the battery has wanted since `D-BASE-R3a`. It
  **still cannot run: no non-interactive root on this host.**

One untried host-side candidate, noted for whoever holds authorization and
**not attempted here**: SIGSTOP the *companion* rather than the encoder, so
the FEC relay stops forwarding while the encoder keeps producing into the
socket and the kernel drops datagrams off a full receive queue — genuine
loss, no root. It also stops the control server and the audio and
controller paths for the duration, so it needs its own risk read and its
own authorization before anyone runs it.

Until one of those lands, the counters accumulate against natural
discontinuities. The corpus supplies them at roughly the rate Group A
measured; C5's 195-332 ms population is real and recorded, so the question
is answerable as soon as a resync of that kind is captured with this build
installed.

## Provenance

Sessions 2026-09-21T00:57:55Z - 01:15:28Z, PS1 reference title, attract
mode, zero input, 150 s hold each, BACK to end, teardown between runs.
Build: `RtpH264Receiver.kt`
`8e314115ad8cd2f044807038b6ec1887fd674e5b6807d5f2fbdb0fb5b0846162`,
`NativeStreamActivity.kt`
`96f2168d4748a85fe31f5f30440f7e6e1903492a229d0a3c2fa3c4997fe5785e`,
APK `c3252ab5fda3e0986adc896ad2b2e856010ffc60484834b6a83422558270c718`.

Reports, the per-session and per-discontinuity CSVs, the recovery-log lines
and both harness scripts are under `evidence/c5a_2026-09-21/`, with
`c5a_sha256.txt`.

## Note on the first attempt at R2

The first R2 attempt aborted at the PLAYING gate. BACK ends the client
session but leaves the game **active and paused** on the host, so the
relaunch POST was a no-op and no native stream started. The harness now
issues `POST /plugins/games/stop` before each launch. R1 was unaffected (it
started from a clean host) and stands as recorded.

## Correction on cross-check (2026-09-21, from the raw R3a reports)

The paragraph above attributing the `D-BASE-R3a` jumps to encoder restarts
is wrong for two of them. `G3` (`native_decoder_20260920_205343_872.json`)
carries one discontinuity of type **`sequence_resync`, 720 packets**, with
`restarts` 0 in its recovery log — no restart, no SSRC change. `G15b`
carries an `ssrc_change` (the restart) *and then* two `sequence_resync`
rows of **984 and 480 packets**. So a 3 s or 15 s SIGSTOP does produce a
genuine sequence jump; a 0.3 s pulse does not. The reasoning that a stopped
encoder burns no sequence numbers is correct, so the jump must come from
what happens at SIGCONT — the likeliest mechanism is a resume burst that
overruns a receive buffer, which is the same burst-then-drop shape Group A
measured on the wire and is worth its own measurement. Two consequences:
(1) a long SIGSTOP is a no-root way to obtain sequence resyncs, but only
the *fast* kind (every one above resolved in 41-100 ms with `au_complete`
true, because the loss had already ended when the IDR arrived), so it
still cannot exercise the > 250 ms limb; (2) the nftables runs remain the
only injection that produces loss *while* the next IDR is in flight. The
INDETERMINATE classification stands.
