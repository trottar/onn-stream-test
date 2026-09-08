# UDP transport investigation — game audio / prototype network

**Investigation date:** 2026-09-07
**Status:** Deferred after localization; resume on dedicated Linux infrastructure if reproduced.

## Executive summary

The native game-audio prototype suffered underruns even though process-specific WASAPI capture was healthy. A staged synthetic-UDP investigation demonstrated that the dominant burst/gap timing behavior is not primarily caused by process-audio callbacks, the Android audio queue, AudioTrack, or Android application receive scheduling.

Forward traffic remained tightly paced through Windows userspace and through the PktMon-visible Windows networking stack up to the **upper edge of the PC's USB Wi-Fi miniport**, yet arrived at the Android kernel in large bursts and gaps. Android-local UDP loopback did not reproduce the external-path pathology. Android's `WIFI_MODE_FULL_LOW_LATENCY` did not fix it.

A final full reverse-direction test then showed the same class of timing transformation from Android to Windows and an unusually large number of duplicate UDP deliveries before Windows userspace.

The shared unresolved region is therefore the physical/network-infrastructure path and endpoint radio/driver internals. The experiment does **not** identify one specific device as the cause.

Because the planned Linux infrastructure changes a major portion of this path anyway, further root-cause work on the disposable Windows/consumer-network prototype is deferred.

## Production audio baseline before isolation

Host:

- process-specific WASAPI loopback for the exact RetroArch PID;
- 48 kHz, stereo, PCM16;
- source callbacks overwhelmingly 480 frames / approximately 10 ms;
- each callback split into two 240-frame / 5 ms packets;
- callback-local pacing;
- nonblocking UDP.

Android:

- 5 ms packets;
- 8-packet / 40 ms hard queue capacity;
- 3-packet / 15 ms queue target;
- 100 ms startup prefill timeout;
- low-latency AudioTrack target around 960 frames;
- loss concealment/crossfade/stale trim.

Production logs showed receive bursts, long gaps, and underruns even though source callback timing was healthy. That motivated layer-by-layer transport isolation instead of additional receiver tuning.

Rejected application-side mitigations before transport localization included:

- host v0.23 `SelectWrite` retry logic, which did not recover WouldBlock behavior sufficiently;
- Android v0.12.3 grace behavior;
- Android v0.12.4 AudioTrack-head top-up behavior;
- Android v0.12.5 / v0.12.5.1 periodic notification clock/telemetry variants.

These were not retained in the production baseline because the later transport evidence showed that the dominant timing transformation was upstream of those receiver strategies.

## Layer-isolation results

### 1. Synthetic Windows -> Android probe

A standalone 1000-byte UDP probe sent one packet every 5 ms while the system was otherwise idle.

Windows sender timing was tightly centered around 5 ms, but Android userspace showed many arrivals separated by less than 2 ms and occasional very long gaps. Therefore production game/video load was not required to reproduce the symptom.

### 2. Android kernel receive timestamps

The Android receiver was changed to collect kernel `SO_TIMESTAMPNS` timestamps using `recvmsg()`.

Representative 10-second result:

- host: 2000/2000 sends, all sender intervals 4-6 ms;
- Android: 2000 unique packets plus 29 same-sender-stamp duplicates;
- kernel arrival max gap: approximately 212.8 ms;
- kernel intervals <2 ms: 507;
- kernel intervals >=20 ms: 59;
- application and kernel interval distributions were nearly identical.

Conclusion: the main transformation already existed **before Android userspace**. Android Kotlin receive scheduling, the application queue, and AudioTrack were not primary causes.

### 3. Android-local UDP loopback

The same style of sender/receiver measurement was run entirely inside Android over `127.0.0.1`.

Representative 10-second result:

- 2000/2000 unique arrivals;
- no duplicates or missing packets;
- sender-clean 4-6 ms -> kernel <2 ms transformations: 1;
- sender-clean 4-6 ms -> kernel >=20 ms transformations: 1;
- sender-vs-kernel interval delta p95 approximately 0.31 ms.

Conclusion: Android's local UDP/IP/socket path was healthy enough; the major external-path transformation required the real network/Wi-Fi path.

### 4. Android Wi-Fi low-latency lock

`WIFI_MODE_FULL_LOW_LATENCY` was held during a 20-second forward probe.

Result: no evidence of meaningful improvement. Kernel arrivals remained strongly bursty and gapped. The lock was therefore **not added to production**.

### 5. Windows PktMon boundary — forward direction

A 20-second forward probe captured all Windows networking components with PktMon.

The capture contained exactly 4000 unique PktMon packet groups with zero event/buffer loss. Each packet traversed the PktMon-visible Windows stack and ended at the upper edge of the actual USB Wi-Fi miniport.

Final miniport-upper-edge interval statistics:

- p50: approximately 4.9998 ms;
- p95: approximately 5.4066 ms;
- p99: approximately 5.4867 ms;
- intervals <2 ms: 1;
- intervals >=20 ms: 1;
- Windows stack transit, first appearance -> miniport upper edge: about 22 microseconds average, about 30.5 microseconds p99, under 42 microseconds max.

Android kernel in the same run:

- p50: approximately 3.999 ms;
- p95: approximately 12.9 ms;
- p99: approximately 26.1 ms;
- intervals <2 ms: about 900;
- intervals >=20 ms: about 91;
- max gap: approximately 154.8 ms.

Important qualification: PktMon observed the **miniport upper edge**, not actual RF transmission. A USB Wi-Fi driver's internal send queue, USB lower edge/device firmware, and radio behavior remain downstream of that timestamp.

Conclusion: the pervasive forward distortion did not occur in Windows userspace or the PktMon-visible Windows networking stack. It appeared somewhere after the miniport upper-edge observation and before Android kernel receive timestamping.

### 6. Reverse Android -> Windows probe

The final reverse diagnostic used an Android nonblocking `DatagramChannel` sender and Windows receiver with PktMon.

Full valid 20-second result:

- planned attempts: 4000;
- Android successful sends: 4000;
- Android WouldBlock: 0;
- Android send errors: 0;
- Windows unique arrivals: 4000;
- Windows duplicate arrivals: **1409**;
- total Windows/PktMon arrivals: **5409**;
- duplicate conflicting sender stamps: 0;
- PktMon Rx packet groups: **5409**;
- PktMon events lost: 0;
- PktMon buffers lost: 0.

Timing, using Android send-completion as the sender boundary:

| Metric | Android send completion | Windows unique receive |
| --- | ---: | ---: |
| p50 interval | ~4.99 ms | ~4.92 ms |
| p95 | ~5.50 ms | ~13.66 ms |
| p99 | ~6.23 ms | ~22.97 ms |
| max | ~47.09 ms | ~102.45 ms |
| intervals <2 ms | 128 | 808 |
| intervals >=20 ms | 13 | 63 |

Among Android send-completion intervals that were 4-6 ms:

- 661 became Windows receive intervals <2 ms;
- 49 became Windows receive intervals >=20 ms.

Conclusion: the reverse path also transformed otherwise well-paced sends. The 1409 same-stamp duplicate arrivals were already present as separate PktMon receive packet groups before Windows userspace, so the Python receiver did not manufacture them.

The approximate 35% extra duplicate-arrival count is not treated as a normal Wi-Fi property or a product requirement. Its origin remains unresolved.

## What is ruled out as the primary cause

The investigation provides strong evidence against these being the dominant source of the observed prototype pathology:

- process-specific audio capture callback timing;
- packet splitting logic itself;
- ordinary Windows userspace sender pacing in the synthetic test;
- the PktMon-visible Windows IP/networking stack in the forward direction;
- Android application receive scheduling;
- Android audio queue/AudioTrack behavior;
- Android local UDP loopback/IP/socket path;
- lack of Android `WIFI_MODE_FULL_LOW_LATENCY`.

None of these statements means those layers can never contribute latency. They mean they do not explain the large external-path transformation measured here.

## What remains unresolved

Potential locations/interactions still include:

- Windows USB Wi-Fi miniport internal queues below the PktMon upper edge;
- USB bus / adapter firmware / radio behavior;
- household upstream Wi-Fi/AP/mesh behavior;
- GL-iNet routing, bridging, NAT, offload, AP, or firmware behavior;
- RF scheduling/retransmission interactions;
- onn Wi-Fi firmware/driver/radio behavior;
- interactions among multiple consumer-network components rather than one faulty component.

A router-side dual-boundary packet capture would be the next localization step on the existing test environment, but that work is deliberately deferred.

## Decision

Stop root-cause work on the current disposable Windows/network prototype.

Do **not**:

- enlarge the production Android jitter buffer merely to mask this environment;
- add the Android Wi-Fi low-latency lock based on these results;
- change the stable video pipeline in response to the audio investigation;
- switch transport protocols solely because of this one environment;
- describe the 1409 duplicates as definitively "wire duplicates" without a lower-layer capture.

Do:

- preserve the stable production baseline;
- preserve and track the diagnostic sources/runners;
- document the evidence;
- replay the synthetic transport suite on the dedicated Linux infrastructure before tuning production audio.

## Resume criteria

Resume this investigation if any of the following occur:

1. Linux -> onn synthetic UDP again shows large burst/gap transformation from a clean sender boundary.
2. onn -> Linux again shows large burst/gap transformation or excessive duplicate delivery.
3. production audio on the Linux infrastructure underruns while the synthetic probe reproduces the same network behavior.
4. the project intentionally begins validating the current consumer-network topology as a supported deployment configuration.

If the Linux infrastructure is clean, classify this investigation as a Prototype-1 environment pathology and retain it only as regression history.
