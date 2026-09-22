---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P4 — is it the air?

## Classification

**CHARACTERIZED for what this client can see, and the answer is no.** Across
seven sessions the loss rate swung **74x** — 1.4 to 105.0 packets per minute —
while the radio sat still: the association never changed, RSSI spanned **5 dB
in total** across 639 three-second samples with a median of **−66 dBm in every
single session**, link speed never correlated with anything, and **not one
scan of any kind was logged inside any session window.** Inside the 20-minute
session, at **n = 597** heartbeat ticks, the client's receive rate against
RSSI gives **rho = −0.022**, against Tx link speed **−0.001**, against Rx link
speed **−0.001**. Those are not small-sample nulls.

**But one half of the pre-registered test could not be run at all, and that
bounds the verdict.** This device exposes **no retry, failure, airtime or
channel-occupancy counter** — every one of them is a hardcoded zero or a
constant (see below). So **signal strength, association stability, link-rate
selection and background scanning are excluded as the cause. Interference and
airtime contention are not excluded — they are simply invisible from here**,
and a measurement of them needs the Opal side or a different client.

**The band gate passed: the onn is on 5 GHz**, so the cheapest possible fix
was not available and the rest of the run was valid.

## The gate, checked on the device and not taken on trust

`adb shell dumpsys wifi`, the `mWifiInfo` line, and confirmed identically in
all seven per-session snapshots:

| | |
| --- | --- |
| band / frequency | **5 GHz, 5180 MHz** |
| channel | **36** |
| channel width | **80 MHz** (`channelWidth = 2`; the field is a code, not MHz) |
| standard | **802.11ac** (`Wi-Fi standard: 5`) |
| supplicant state | `COMPLETED` in every sample, **never re-associated** |
| RSSI | −63 to −69 dBm across the whole run |
| Tx / Rx link speed | 117-390 / 29-351 Mbps |
| max supported Tx | **866 Mbps** |
| wifi score | 60, unchanging |

Worth noting even though it is not the cause: **the link negotiates 195-260
Mbps against an 866 Mbps ceiling**, which is what −66 dBm buys on 80 MHz. The
stream needs ~7 Mbps, so there is plenty of headroom, but the link is running
well down its rate table.

## What this onn does and does not report about its radio

**Live and usable:** RSSI, link quality, Tx and Rx link speed, `rx_pps`, the
supplicant state, and a timestamped scan log.

**Present as fields but never populated — recorded as absences, never read as
zeros:**

| field | source | value |
| --- | --- | --- |
| `tx_retry`, `tx_bad`, `bcnCnt` | `WifiScoreReport`, 3,600 rows | identically **0** |
| `total_tx_retries`, `total_tx_bad` | `WifiUsabilityStatsEntry`, 440 rows | identically **0** |
| discarded `nwid/crypt/frag/retry/misc`, `missed beacon` | `/proc/net/wireless`, every sample | identically **0** |
| `noise` | `/proc/net/wireless` | **−256** (driver reports none) |
| `total_radio_on/tx/rx_time_ms`, `total_scan_time_ms` | usability ring | **0** |
| `channel_utilization_ratio` | usability ring, 440 rows | **constant 15** |
| `total_cca_busy_freq_time_ms` | usability ring | **0** |

`iw` and `wpa_cli` are not present on this build.

**This is the finding that most constrains future work on the air.** Retries
and airtime are exactly where co-channel interference would show, and this
client cannot show them.

## Method

**No code change anywhere.** The sampler is a host-side script that reads the
onn over adb and the companion's own status endpoint; nothing was installed on
the onn and neither client nor companion was modified.

**Sampling cost was measured before anything was designed around it.** A full
`dumpsys wifi` costs **368-387 ms of onn CPU** — over the task's 300 ms bar,
and too expensive to run beside a 60 fps decode. So the expensive dump was
kept out of the sessions and the live round was built from cheap sources:
`cat /proc/net/wireless` plus `dumpsys wifiscanner`, together **77-87 ms
on-device** (median 193-209 ms wall per round including adb transport), every
**10 s** as originally specified.

**The device keeps its own radio series, which is finer and free.**
`dumpsys wifi` carries a `WifiScoreReport` CSV of **3,600 rows at ~3 s
covering about three hours**, append-only and wall-clock stamped. Harvesting
it *after* each session recovers the whole session at 3 s resolution having
cost the run nothing — better than the 20 s thinning the task offered as the
fallback. `dumpsys wifiscanner` (67 ms) is likewise an append-only scan log
and was harvested the same way. Device local time is **UTC−4**; the offset is
read from the device and applied.

**Every stored line is redacted**: MACs, BSSIDs, quoted SSIDs and IPv4
addresses become `<redacted>` before anything is written. Band, channel,
width and counters are kept.

**Sessions.** Six attract-mode sessions of the PS1 reference title, 120 s
each, zero input, per `TOOLS.md`, BACK to end, companion restarted and the
game stopped between each; then **one 20-minute session** with identical
sampling. The sampler ran **30 s before and 30 s after** every session.
Nothing was rejected — all seven completed and produced reports, and none
carried a discontinuity. The `D-BASE-P3` pacing knob was confirmed **0** at
the start of every session.

Scripts, samples, harvests, heartbeat slices and reports are in
`d_base_p4_2026-09-21/` with SHA-256s in `p4_sha256.txt`.

## Per session: loss beside the radio

Loss is the decoder report's own `lost_packets`, which is authoritative.

| run | dur s | lost | loss/min | fwd gaps | pkt/gap | max gap | disc | spk20/min | fps | RSSI med | min | max | tx med | rx med | missed beacon | scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| S1 | 127 | 14 | 6.6 | 2 | 7.00 | 12 | 0 | 42.6 | 59.71 | −66 | −67 | −64 | 195 | 117 | 0 | **0** |
| S2 | 127 | 52 | 24.6 | 14 | 3.71 | 8 | 0 | 50.1 | 59.67 | −66 | −67 | −64 | 260 | 117 | 0 | **0** |
| S3 | 127 | 3 | **1.4** | 1 | 3.00 | 3 | 0 | 47.3 | 59.72 | −66 | −67 | −65 | 260 | 117 | 0 | **0** |
| S4 | 130 | 50 | 23.1 | 10 | 5.00 | 21 | 0 | 62.4 | 59.56 | −66 | −67 | −65 | 260 | 117 | 0 | **0** |
| S5 | 130 | 13 | 6.0 | 2 | 6.50 | 8 | 0 | 40.6 | 59.74 | −66 | −68 | −65 | 260 | 117 | 0 | **0** |
| S6 | 127 | 33 | 15.6 | 6 | 5.50 | 8 | 0 | 48.7 | 59.70 | −67 | −69 | −65 | 234 | 117 | 0 | **0** |
| **L20** | **1208** | **2114** | **105.0** | **142** | **14.89** | **53** | 0 | 45.9 | 59.76 | −66 | −67 | −65 | 260 | 117 | 0 | **0** |

**The 20-minute session is the striking row.** Its loss rate is **4x the
worst two-minute session and 75x the best**, and its bursts are far bigger —
**14.89 packets per gap against 3.0-7.0** — while its radio readings are
indistinguishable from every other session's. Whatever drives the loss
produces **larger bursts over a longer observation**, and a two-minute window
frequently misses it entirely. That is a better account of `D-BASE-P3`'s
1.8-35.2 control-arm swing than anything about the air: the loss is
**episodic, and short sessions sample it badly.**

## Correlation

**Across sessions**, loss/min against the radio (n = 7):

| | rho |
| --- | ---: |
| median RSSI | **+0.000** |
| worst RSSI | +0.267 |
| median level (`/proc/net/wireless`) | **+0.000** |
| median link quality | +0.786 |
| median Tx link speed | +0.178 |
| worst Tx link speed | +0.182 |

The one figure over the 0.5 threshold, link quality at **+0.786**, is
**discounted and not read as support for the air**: n = 7 (the 5 % critical
value is ~0.79, so it is borderline at best), link quality on this driver is a
monotone rescaling of the RSSI that reads **+0.000**, and **the sign is
backwards** — it says *better* link quality goes with *more* loss.

**Inside the 20-minute session**, the client's own per-tick receive rate
against the 3 s radio ring, **n = 597**:

| | rho |
| --- | ---: |
| receive rate vs RSSI | **−0.022** |
| receive rate vs Tx link speed | **−0.001** |
| receive rate vs Rx link speed | **−0.001** |

Receive rate held **821 packets/s median** (min 678, max 982; p05 738,
p95 890) with per-minute medians between **802 and 830 across all twenty
minutes**. Thirty ticks (5.0 %) fell more than 10 % below median; **every one
of them sits at RSSI −65 or −66**, the same as the rest of the session. **Not
one dip carries a worse radio reading.**

## Scans

**Zero.** Not one `start scan`, `addSingleScanRequest` or `singleScanResults`
was logged inside any of the seven session windows. The only scans in the log
all came from `com.android.tv.settings` at 14:05 local, before the run.
Background scanning has a 30 s base period configured but is not firing, and
`isScanningAlwaysEnabled` is false. **The classic client-side scan-stall cause
is not occurring here, so there is nothing to disable.**

## Why there is no per-minute loss series

It was attempted and it does not survive its own noise, so none is presented.
`loss(window) = Δ(relay rtp sent) − Δ(client rx received)` uses two real
counters, but the client's is only visible through the 2 s heartbeat and must
be interpolated against an ~830 packet/s stream. Measured over the seven
sessions: **noise sd 86 packets per 10 s window against a median true signal
of 3.0 packets** — a **29x** ratio, and individual windows come out
**negative**, which a loss count cannot be. Session totals reconcile (sums of
5 / 173 / 220 against reported 14 / 52 / 50), so the method is sound in
aggregate and useless per window. Full working in `p4_counter_noise.txt`.

**Getting finer would need a per-tick loss counter in the client, which this
task explicitly forbade changing.** That is the single instrument that would
most improve any future run on this question.

## Against the pre-registration

- **Implicated if loss tracks retry/failure deltas** — **could not be
  tested.** No retry or failure counter exists on this device.
- **Implicated if loss tracks RSSI dips (|rho| ≥ 0.5 and worse radio in the
  top-quartile loss minutes)** — **no.** rho −0.022 at n = 597 and +0.000
  across sessions; the worst receive-rate ticks carry ordinary RSSI.
- **Implicated if scan events sit inside the loss bursts** — **no.** There
  were no scan events at all.
- **Not the explanation if radio readings are flat and scan-free while loss
  swings 10x** — **this is what happened**, and by a wider margin than the
  clause asks: flat to 5 dB, scan-free, loss swinging **74x**.

**So: the air, in every respect this client can measure, is not the
explanation.** The honest qualifier is that "every respect this client can
measure" excludes interference and airtime entirely.

## Levers, and they are the user's to choose

None of these is code. Listed with what the measurements say about each:

- **Band** — already 5 GHz. **No lever here**, and this was the cheapest one.
- **Background scanning on the onn** — already not firing during sessions.
  **Nothing to disable.**
- **Channel** — the Opal is on **channel 36**, the bottom of UNII-1 and a
  common default, so neighbours are likelier there. Moving it to UNII-3
  (149-165) is one router setting. **This is the one lever the data neither
  supports nor rules out**, because the interference counters that would
  settle it do not exist on this client.
- **Channel width** — 80 MHz spans channels 36-48, so it is exposed to
  anything in that whole block. Dropping to 40 or 20 MHz cuts that exposure
  and raises per-subcarrier SNR, at a throughput ceiling the stream does not
  need (7 Mbps against 866). **A cheap experiment, again on the Opal.**
- **Placement** — RSSI −66 dBm holds the link at 195-260 Mbps against an
  866 Mbps ceiling. Improving it would buy rate headroom. **The data does not
  say it would buy less loss**, since loss does not track RSSI.

**Choosing among these is a product decision, not a measurement outcome.**
The measurement's own recommendation is different: **instrument the Opal side
or use a client that reports retries**, because this one cannot answer the
question that remains.

## What this does not establish

- **Nothing about interference, airtime contention or CCA.** Those counters
  are absent, and a flat RSSI does not exclude a busy channel.
- **Nothing about the Opal's own behaviour.** D080-D083 already showed its
  standard capture points go blind during confirmed traffic; this run added
  no router-side visibility and was not supposed to.
- **No per-minute loss series**, for the reason above.
- **Seven sessions.** The episodic reading of the loss — bigger bursts over
  longer windows — rests on one 20-minute session against six short ones and
  would want repeating before it is leaned on.
