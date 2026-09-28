---
memory_schema: 1
as_of: 2026-09-25
status: D6-R1 DONE — the preserved synthetic UDP suite replayed on the post-B2 path (host wired → Opal → onn 5 GHz), topology gate PASS; forward 3 valid runs and reverse 3 valid runs (three first-pass runs ended by the onn's screensaver, retried once each, woken first); pre-registered signature (≥ 20 same-stamp duplicates, the suite's own analyzer threshold) in 0 of 3 runs in each direction → forward NOT REPRODUCED, reverse NOT REPRODUCED → roadmap D6 "specific to the old environment" (the pre-B2 runs had the host on its USB Wi-Fi adapter); duplication 0-4 per run against 2,371-2,626 (forward) and 476 (reverse) pre-B2; burst/gap transformation ~14-20× lower; loss 0-28 of 4,000; DEFERRED entry closed for the old signature
---

# D6-R1 — the deferred UDP suite, replayed on the production path

Task: `handoffs/D6-R1_UDP_SUITE_REPLAY_TASK.md` (weekend queue item 5,
authorized by the user 2026-09-24). Evidence: `d6_r1_2026-09-24/` (manifest
`sha256_manifest.txt`). The pre-registration was written at 21:28:03Z,
before any run (`d6_r1_preregistration.txt`).

**Scope.** Runtime only. The probes ran as preserved: no code change to
them or to anything else, and no companion, client or profile change. The
Opal was read-only (`ssh opal` reads only). The stream was inactive
throughout, and nothing overlapped (task 4's teardown ended at
00:09:48Z; the suite ran 00:12-00:35Z).

## 1. Topology gate: PASS (`d6_r1_topology_gate.{sh,txt}`)

The checks are B2's, and only labels and booleans were recorded:

- **Default route**: the host's one onboard wired interface (`eno1`),
  which is the only interface up. The host has no wireless interface and
  no tunnel.
- **The gateway is the Opal**:
  - its OUI equals the OUI of the Opal's own interfaces, read over `ssh
    opal`;
  - the `opal` ssh alias is the default gateway;
  - it answers with a Dropbear SSH banner, an nginx HTTP server header and
    DNS on 53.
- **One subnet**: host and onn share one /24, and the onn's address is on
  its wireless interface.
- **adb** answers.
- **The internet** is reached via the default gateway on `eno1`.
- The stream and the game were inactive.

## 2. The runs

**Forward (host → onn).** The D082 runner's probe steps
(`tools/run_opal_bridge_boundary_probe.sh`):

- the onn's `UdpTransportProbeActivity` on port 48120 for 23 s, with
  `kernel_timestamp`, wifi lock `none` and priority `default`;
- 1 s later, `udp_transport_probe.py send`: 20 s at 5 ms, 4,000 packets of
  1,000 B;
- then the pull and `compare`.

**The runner's Opal steps were not run**: they use password ssh, `opkg
install tcpdump-mini` and a capture on `br-lan`, and the Opal is
read-only. So no router-boundary verdict exists for these runs.

**Reverse (onn → host).** The archived Windows runner's sequence with Test
B's parameters:

- `udp_reverse_transport_probe.py receive` for 25 s, expecting 4,000;
- 0.6 s later, the onn's `UdpReverseTransportProbeActivity`: 20 s,
  `urgent_audio`;
- then the pull and `compare`.

**Port 48122 instead of 48102** was used on both ends, as arguments, not
code: the companion's controller socket owns 48102, and nothing was stopped
for this.

**The runner** is `d6_r1_run.sh`, driven by `d6_r1_all.sh` and
`d6_r1_retry.sh`. Addresses live only in shell variables, and the outputs
were scrubbed of them.

**Three first-pass runs were invalid.** At ~00:20Z the onn entered its
screensaver (`mWakefulness=Dreaming`, screen-off timeout 600 s after the
last input at task 4's teardown). The dream took the foreground and ended
the probe activities:

- **fwd3**: the receiver ended after 0.74 s (10 of 4,000 arrived).
- **rev2 and rev3**: the sender stopped at 2,088 and 2,095 packets, and no
  summary was written.

Each was **retried once** (fwd3b, rev2b, rev3b), with the onn woken
(`KEYCODE_WAKEUP`, as `p9_run.sh` does) before every retry run. The
invalid runs stay in the evidence, marked.

- Forward runs started at 00:12:51, 00:17:51 and 00:27:03Z.
- Reverse runs started at 00:15:22, 00:29:37 and 00:34:34Z.
- **rev2b → rev3b were 4 min 57 s apart**, 3 s short of the task's ≥ 5
  min. That is recorded as a deviation.

## 3. Results beside the last pre-B2 runs (`d6_r1_analyze.py` → `d6_r1_analysis.txt`)

**Forward (host → onn):**

| run | sent | arrived | missing | same-stamp dup | conflicting dup | 4-6 ms → kernel < 2 ms | → ≥ 20 ms | kernel interval p95 / max ms | reordered |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| pre-B2 Test A (09-15 09:40) | 3,993 | 3,993 | 0 | **2,626** | 0 | 2,116 | 190 | 18.4 / 792.3 | 0 |
| pre-B2 D082 (09-15 14:12) | 3,661 | 3,661 | 0 | **2,371** | 0 | 2,064 | 159 | 12.0 / 551.1 | 0 |
| fwd1 | 4,000 | 3,988 | 12 | **0** | 0 | 153 | 2 | 8.0 / 25.0 | 0 |
| fwd2 | 4,000 | 3,972 | 28 | **0** | 0 | 152 | 9 | 8.0 / 27.7 | 0 |
| fwd3b | 4,000 | 3,997 | 3 | **0** | 0 | 100 | 4 | 8.0 / 30.0 | 0 |

**Reverse (onn → host):**

| run | sent | arrived | missing | same-stamp dup | conflicting dup | 4-6 ms → host < 2 ms | → ≥ 20 ms | host interval p95 / max ms | reordered |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| pre-B2 Test B (09-15 09:45) | 4,000 | 3,894 | 106 | **476** | 0 | 1,312 | 126 | 18.1 / 173.7 | 0 |
| rev1 | 4,000 | 3,998 | 2 | **3** | 0 | 100 | 6 | 6.2 / 93.4 | 0 |
| rev2b | 4,000 | 4,000 | 0 | **4** | 0 | 77 | 4 | 6.2 / 81.5 | 0 |
| rev3b | 4,000 | 4,000 | 0 | **1** | 0 | 52 | 1 | 6.2 / 35.4 | 0 |

**Host UDP counters** (`/proc/net/snmp`, each run): InErrors,
RcvbufErrors and SndbufErrors were all +0. Test B had RcvbufErrors +120,
and Test A had SndbufErrors +7.

**The onn's sender** (reverse): 4,000 of 4,000 sent, would-block 0, errors
0.

## 4. Classification (pre-registered)

| direction | runs with the signature (≥ 20 same-stamp duplicates) | reading |
| --- | --- | --- |
| forward | 0 of 3 (max 0) | **NOT REPRODUCED** |
| reverse | 0 of 3 (max 4) | **NOT REPRODUCED** |

**Roadmap D6: the pathology is specific to the old environment.** It is
not reproduced on the representative path.

**The old environment, stated from the raw evidence.** The 2026-09-15
suite runs had the host on its **USB Wi-Fi adapter** (Realtek RTL8822BU,
`rtw_8822bu`) into the Opal, with the onn on the Opal's 5 GHz. That adapter
logged LPS-exit firmware failures and a register timeout, and the host saw
thousands of UDP buffer errors (`2026-09-15.md`,
`investigations/D_LINUX_UDP_EGRESS_2026-09-15.md`).

- The handoff's and `DEFERRED.md`'s phrase "through the Windows PC" does
  not describe those suite runs. The PC was in the path for the
  in-session sessions from 2026-09-16 on.
- The post-B2 path differs from it by the host's link: wired, not USB
  Wi-Fi. This replay cannot say which part of the old path (the adapter,
  its driver, or a WLAN-to-WLAN hop through the Opal) produced the
  duplication. It says only that the path the product now uses does not.

**The burst/gap transformation fell too, though no threshold is applied**
(the suite defines none):

- 4-6 ms → < 2 ms: 100-153 forward and 52-100 reverse, against 2,064-2,116
  and 1,312 pre-B2.
- 4-6 ms → ≥ 20 ms: 2-9 against 159-190 forward, and 1-6 against 126
  reverse.
- The worst forward kernel interval was 25-30 ms, against 551-792 ms.

**What remains is small loss.** 3-28 of 4,000 forward and 0-2 reverse went
missing, with 0 reordered. This is the transport's ordinary single-packet
loss that 8+1 FEC and the audio redundancy cover (`C4-D1`, `P10`). It is
not the old signature.

## 5. The in-session view beside it (cited, not rerun)

On the same path under load:

- the close-out holds (2026-09-23) read post-FEC video loss 8.7 / 8.4 per
  minute, 0 resyncs;
- the `C3.L3a-S1` holds read the same order;
- tonight's `C3-L4-S1` holds read 7.7-9.2 per minute;
- `late_or_reordered_packets` is 0 across every adopted-build decoder
  report, and no duplication counter was raised.

Tonight's `CTRL-L1` holds read 14-24 per minute on video, on the same path
earlier in the evening. That is loss, not duplication.

## What remains

- The replay was idle only. The preserved suite has no with-load arm, so
  none was run. The in-session rows above are the with-load reference.
- No router-boundary capture was taken: the Opal stays read-only.
- The onn's 10-minute screensaver ends any diagnostic activity started
  more than 10 min after the last input. **A runner must wake the onn
  first.** Recorded for `TOOLS.md`.

## Files (`d6_r1_2026-09-24/`)

- **Setup**: `d6_r1_preregistration.txt` and
  `d6_r1_topology_gate.{sh,txt}`.
- **Runners**: `d6_r1_run.sh`, and `d6_r1_all.{sh,log}` and
  `d6_r1_retry.{sh,log}`.
- **Per run** (`fwd1`, `fwd2`, `fwd3` invalid, `fwd3b`, `rev1`, `rev2` and
  `rev3` invalid, `rev2b`, `rev3b`): the probes' own outputs, meaning
  `host_packets.csv`, `host_summary.json`, `android_*`,
  `combined_summary.{json,txt}` and the console outputs; plus
  `udp_before.txt` / `udp_after.txt` and `am_start.txt`.
- **Analysis**: `d6_r1_analyze.py` and `d6_r1_analysis.txt`.

`h2_prep_redact.py --check` reports 0 residual matches on every file. The
gate script's one public address literal is written `<public-ipv4>` in the
stored copy. The probes persist no address (`source_address_persisted` /
`target_address_persisted` false). No address, MAC, SSID or device
identifier appears in any file.
