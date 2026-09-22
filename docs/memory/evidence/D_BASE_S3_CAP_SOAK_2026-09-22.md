---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-S3 — three hours on the adopted 90 KB cap

Session 2026-09-22 06:38-09:38 UTC. 180 minutes, attract mode, zero input,
**no `PRIVYHUB_ENC_*` variable set**.

## Classification

**SOAK VALIDATED**, on all five criteria, with **one finding that the task
said would outrank the rest and that is reported first**.

| criterion | required | measured |
| --- | --- | ---: |
| every minute zero >= 80-packet frames | 0 | **0 of 180 minutes** |
| session loss per minute | <= 30 | **5.4** |
| sequence resyncs | 0 | **0** (and 0 SSRC changes) |
| rotation loses data | none | **0 discontinuities across 2 rotations of each log** |
| thermals plateau as `T1` found | plateau | **they plateau** |

## 1. The finding: the driver's cap is soft by ~0.01 %

**Two frames in 180 minutes exceeded 90,000 bytes — by 11 and 9 bytes**
(90,011 at minute 120, 90,009 at minute 163). Every other minute of the
session was at or under the cap, and the session maximum was 90,011.

**This is a property of the VAAPI driver, not of the adoption**, and it was
already visible in `D-BASE-P6`: the `A2` arm set 60,000 and measured a
60,092-byte frame, 92 over. The cap is honoured to within about **0.02 %**
and is approximate rather than absolute.

**It does not touch the mechanism.** A 90,011-byte frame is **~76
packets**; the population the cap exists to remove is **>= 80 packets**,
and the session's maximum was **77 packets** with **zero** frames at 80 or
above in any minute. An 11-byte overshoot cannot reintroduce a burst that
needs roughly 3,000 more bytes to reach the threshold.

**What it means for how the cap should be described:** `max_frame_size` is
a **target the driver aims at**, not a hard ceiling, and any future check
should allow a small tolerance rather than test `<= 90000` exactly. The
adoption stands.

## 2. The cap held, and the loss fell further

| | |
| --- | ---: |
| video packets / loss | 8,888,555 / **977** (0.0110 %) |
| **loss per minute** | **5.4** |
| per-minute loss: min / median / max | 0 / 4.0 / 37 |
| forward-gap events / **max forward gap** | 369 / **27 packets** |
| sequence resyncs / SSRC changes | **0 / 0** |
| max packets per frame | **77** |
| max frame bytes | 90,011 (see §1) |
| frames >= 80 packets | **0** |
| fps | **59.96** |
| `spike_20_ms` per minute | 26.7 |
| max output gap / max rx-to-decode | 162 ms / 117 ms |
| achieved bitrate | **6,928.7 kbps** |
| onn socket drops | **0** |
| audio loss | 8,543 of 2,152,427 (0.3969 %) |
| audio underruns (session) | 129 |
| `prolonged_starvation_events` | 5,759 (**32.0/min**) |

**5.4 losses a minute over three hours is lower than any 20-minute capped
session** — `A1` 15.4, `A1r2` 20.3, `P6a`'s `V1` 12.4. Over the same first
20 minutes `S3` lost **163** against those sessions' 308, 408 and 249,
i.e. **0.40-0.65x**. Against the uncapped baselines (2,690-2,896 per 20
minutes) the three-hour rate is **roughly 25x lower**.

**Hour by hour: 380 / 340 / 253.** Worst/best ratio **1.50x**, below the
2.0 drift flag and below the ±15 % spread `P6` saw between its baselines
in the sense that matters — **the trend is downward, not noise upward**,
and the frame distribution is identical throughout.

## 3. What the residual tracks: nothing

The pre-registered question. On **1,080 ten-second windows** and **180
one-minute windows**, Spearman of loss against every candidate:

| series | rho, 10 s (n=1,080) | rho, per minute (n=180) |
| --- | ---: | ---: |
| max packets per frame | −0.025 | +0.041 |
| max frame bytes | −0.027 | +0.045 |
| frames >= 40 packets | −0.014 | −0.011 |
| mean packets per frame | +0.024 | +0.028 |
| frames in the window | +0.037 | +0.031 |
| client rx packets | +0.013 | +0.026 |
| Opal channel utilization | — | **+0.073** |

**Every one is under 0.08.** The pre-registration set |rho| < 0.3 on all
series as "the residual is a floor", and this is an order of magnitude
inside it.

The bucketed table says the same thing in the other direction — **flat**,
where uncapped it rose 14-fold into the `>= 80` bucket:

| bucket (largest frame in the window) | windows | loss/window |
| --- | ---: | ---: |
| < 40 packets | 152 | **0.80** |
| 40-59 | 306 | **1.05** |
| 60-79 | 622 | **0.85** |
| **>= 80** | **0** | — |

**Reading: the residual is a floor.** It does not rise monotonically
across the remaining buckets, it does not track frame size at either
resolution, and it does not track the air. **The loss column is closed at
this level.** A tighter cap is not a live lever — `P6` already showed 60 KB
ties on loss, and this shows why: there is no frame-size signal left in the
residual to remove.

**What the residual is instead**, stated as the open question rather than
guessed: 977 packets over 8.89 million is **0.011 %**, spread thinly with
no per-window structure. Nothing in these instruments distinguishes the
windows that lost from the windows that did not.

## 4. Rotation: clean, twice, in both logs

The first multi-hour test of the `D-BASE-P6` frame-size log.

| log | rotations | live at end | archived |
| --- | ---: | ---: | --- |
| `native_frame_sizes.jsonl` | **2** | 949,864 B | 4,194,673 + 4,194,460 B |
| `native_stream_heartbeat.log` | **2** | 1,904,014 B | 4,194,497 + 4,194,628 B |

**The frame-size series has 0 discontinuities across 10,801 seconds** —
every one-second bucket is present, including the two seconds in which a
rotation happened. The heartbeat slice holds **5,382 lines** with intervals
**2,001-2,031 ms**, no gap. **Neither rotation lost a row.**

## 5. Thermals and resources

**Thermals plateau, as `T1` found.** Medians by third of the session:

| | first | second | third | range |
| --- | ---: | ---: | ---: | --- |
| `k10temp` Tctl | 53 °C | 54 | 55 | 41-57 |
| `amdgpu` edge | 43 °C | 43 | 44 | 33-46 |
| `amdgpu` power | 18 W | 18 | 19 | 11-25 |
| encoder CPU | 27 % | 27 | 27 | 26-28 |

The rise is the warm-up in the first minutes; from there it is flat. The
onn reported thermal status **0 (NONE)** throughout, as `T1` established it
always does.

**RetroArch memory: `S2`'s finding does NOT fully reproduce, and that is
worth saying rather than smoothing.**

| | `S3` (this run) | `S2` (2026-09-21) |
| --- | ---: | ---: |
| RSS total over 3 h | 157,396 → 301,004 kB = **+140.2 MB** | +119.9 MB |
| of which **anonymous** | 67,284 → 102,400 kB = **+34.3 MB** | **+6.2 MB** |
| of which file-backed | +105.9 MB (75.5 %) | +113.6 MB (95 %) |

**The growth is still majority file-backed**, so "warm-up, not a leak"
survives in its main claim. But the anonymous component grew **five and a
half times what `S2` measured**, and its per-third medians (73,076 →
85,320 → 97,464 kB) were **still rising at the end rather than levelling**.
That is a difference between two three-hour sessions on different paths and
different builds, not a demonstrated leak — **but it does not reproduce
`S2`'s clean result and should not be cited as if it did.** Companion RSS
+4.7 MB and encoder RSS +0.3 MB are both flat.

## 6. The Opal, sampled through the soak

543 rounds at 20 s, read-only, reachable on the first `BatchMode` try.
**Channel utilization mean 6.82 %** — the same ~93 % idle channel `O1`
measured — with a range of 0.0-56.6 %. **The 56.6 % excursion did not move
the loss**: utilization against per-minute loss gives rho **+0.073**.
Somebody else's traffic came and went and the stream did not notice.

## 7. Comparison arms

| | loss/min | spikes/min | starvation/min | forward gaps |
| --- | ---: | ---: | ---: | ---: |
| **`S3`** (capped, Opal path, 3 h) | **5.4** | 26.7 | 32.0 | 369 |
| `S2` (uncapped, PC path, 3 h) | ~115 | ~95 | 75.9 | — |
| `A1` / `A1r2` (capped, 20 min) | 15.4 / 20.3 | 34.9 / 33.3 | — | 105 / 119 |
| `V1` (capped, 20 min, adopted) | 12.4 | 25.9 | — | 91 |

Per-minute Pearson between `S3`'s first 20 minutes and the other capped
sessions is **+0.09 to +0.16** — i.e. **nothing**, which is the same result
`P6a` found and for the same reason: **with the tail removed there is no
content-lock left to reproduce.**

## 8. Method and privacy

Instruments: heartbeat v2, `native_frame_sizes.jsonl`, the `P5` onn socket
sampler at 2 s (5,432 rounds), the `T1` host sampler, and the `O1` Opal
sampler at 20 s. **Confirmed before the hold**: argv carried
`-max_frame_size 90000`, `encoder_overrides.any_override` **false**, and
`env | grep PRIVYHUB_ENC` printed nothing — all three recorded by the
harness.

The heartbeat was sliced **by timestamp**, never by byte offset, which is
what made the two rotations invisible to the analysis.

No address, MAC, SSID or device identifier appears here or in any stored
artifact; the Opal rounds are redacted at source by `o1_redact.py`.

Artifacts under `evidence/d_base_s3_2026-09-22/` with SHA-256s in
`s3_sha256.txt`: `s3_run.sh`, `s3_analyze.py`, `frames_S3.jsonl`,
`heartbeat_S3.jsonl`, `socket_S3.jsonl`, `air_S3.jsonl`,
`opal_inventory.txt`, `report_S3.json`, `status_S3.json`,
`armcheck_S3.json`, `encoder_cmd_S3.txt`, `index.txt`, `analysis_s3.txt`,
`s3_windows.json`, `host_summary.txt`.

**No code change.** The profile is exactly as `P6a` left it.
