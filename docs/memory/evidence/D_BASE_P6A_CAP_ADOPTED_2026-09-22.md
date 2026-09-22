---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P6a — the 90 KB frame cap is the profile default

## Classification

**RUNTIME VALIDATED.** Every pre-registered gate condition passed on the
first session, with no environment variable set.

| gate | required | measured |
| --- | --- | ---: |
| frames >= 80 packets | **0** | **0** |
| max frame bytes | <= 90,000 | **89,874** |
| video `lost_packets` | <= 600 | **249** |
| >= 80-packet bucket in the loss table | absent | **absent** |
| achieved bitrate | 6,900-7,050 kbps | **6,929.6** |
| rendered fps | >= 59.8 | **59.90** |
| sequence resyncs | 0 | **0** |
| onn socket drops | 0 | **0** |
| relay send errors | 0 | **0** |
| encoder CPU median | 26-28 % | **26.6 %** (26.1-27.4) |

The cap is now declared beside the other static stream parameters and the
argv carries it with nothing set in the environment. **The companion is
left running on it.**

## 1. The user's perceptual check

**The one cost the instruments cannot see was checked by the user, not by
this run.** On 2026-09-22, running the `A1` arm with
`encoder_overrides.any_override: true` and `max_frame_size_bytes: 90000`
confirmed from `native-stream-status`, the user played for about a minute
and reported: **no stutters, "could barely tell it was over the LAN."**

**That is a user-stated perceptual result, not instrument evidence, and it
is not upgraded here.** It is what made the adoption a decision the user
could take; everything else in this record is measurement.

## 2. What changed

**The cap moved from an environment override to a profile field.**

`NativeStreamProfile` gains `max_frame_size_bytes` (default **0**, meaning
uncapped), and the reference profile declares **90,000**. It sits beside
width, height, fps, bitrate, GOP, B-frames and FEC group size because it
belongs to the same class of fact: **it is a transport parameter wearing an
encoder's clothes.** The loss on this link is a per-frame micro-burst
meeting the wireless queue, the burst *is* the frame, and capping the frame
is what makes this profile deliverable over one wireless hop.

**Three source states, and the third is the one that needed new code.**

| environment | cap applied | argv | `max_frame_size_source` | `any_override` |
| --- | ---: | --- | --- | --- |
| unset | **90,000** (profile) | `-max_frame_size 90000` | `profile` | **false** |
| `=60000` | 60,000 | `-max_frame_size 60000` | the variable | true |
| **`=0`** | **uncapped** | **flag absent** | the variable | true |

`_env_int` could not express "explicitly zero" — it folded 0 and unset into
the same answer — so `_env_int_or_none` was added beside it. **`=0` is the
documented way to re-run the `D-BASE-P6` baseline for comparison**, and it
is proven below rather than asserted.

**`any_override` changed meaning, deliberately.** The profile being in
force is no longer an override. It is false when nothing but the profile
decides the argv; that is the "default is in force" reading from now on.
`default_max_frame_size_bytes` and `uncapped` were added so a status read
says which source won without inference.

**Scope held to one change.** `-bufsize` stays at 7000k and
`PRIVYHUB_ENC_BUFSIZE_K` is untouched and still default off (`P6` measured
it and it was **not** adopted — 3x the loss of the cap). No pacing, no FEC,
no client change, no other encoder flag. **The deferred Windows NVENC
builder ignores the field and logs one line saying so** rather than
inventing a translation it has no measurement behind.

## 3. The validation session

One 20-minute attract-mode session, zero input, **no `PRIVYHUB_ENC_*`
variable set** — `env | grep PRIVYHUB_ENC` printed nothing and the harness
recorded that it did.

**Confirmed before the hold, not after:**

- argv contains `-max_frame_size 90000`;
- `encoder_overrides.any_override` **false**;
- `default_max_frame_size_bytes` **90000**, `max_frame_size_source`
  **`profile`**, `uncapped` **false**;
- the launch line in `logs/games/native_video_alpha.log` carries
  `-max_frame_size 90000` (the last `encoder argv:` banner in the file,
  with none after it).

**Session V1:**

| | |
| --- | ---: |
| frames | 72,470 |
| packets p50 / p90 / p99 / max | 12 / 29 / 65 / **77** |
| bytes p50 / p90 / p99 / max | 13,312 / 33,792 / 76,800 / **89,874** |
| frames >= 40 / >= 80 packets | 2,565 / **0** |
| video packets / loss | 989,510 / **249** (0.0251 %, 12.4/min) |
| forward-gap events / max gap | 91 / **15 packets** |
| sequence resyncs | 0 |
| audio loss | 1,106 (0.4612 %) |
| fps / spike_20_ms per min | **59.90** / 25.9 |
| max output gap / max rx-to-decode | 141 ms / 96 ms |
| achieved bitrate (encoder log) | **6,929.6 kbps** |
| relay `rtp_bytes` / `send_errors` | 1,071,090,387 / **0** |
| onn socket drops | **0** |
| encoder CPU median | **26.6 %** |

Loss conditional on the window's largest frame — the `>= 80` bucket that
carried 93-95 % of the uncapped loss **does not exist**:

| bucket | windows | loss | loss/window |
| --- | ---: | ---: | ---: |
| < 40 packets | 16 | 50 | 3.12 |
| 40-59 | 35 | 78 | 2.23 |
| 60-79 | 69 | 121 | 1.75 |
| **>= 80** | **0** | — | — |

## 4. Against the P6 arms

| session | cap source | loss | total vs V1 |
| --- | --- | ---: | ---: |
| **V1** (this run) | **profile** | **249** | — |
| A1 | env override | 308 | 0.81x |
| A1r2 | env override | 408 | 0.61x |
| A0 | uncapped | 2,690 | **0.09x** |
| A0r2 | uncapped | 2,896 | **0.09x** |

**V1 sits at the good end of the capped band and an order of magnitude
below both uncapped baselines.** The three capped sessions span 249-408
against 2,690-2,896 uncapped.

**Per-minute Pearson against the capped arms is near zero or negative**
(A1 −0.291, A1r2 −0.064) and it is *also* negative against the uncapped
ones (A0 −0.546, A0r2 −0.456). That is worth stating plainly because it
reads oddly at first: **the content-lock was a property of the tail.** `O1`
found the loss reproduced at Pearson 0.964 session to session because the
attract loop replayed the same large frames in the same minutes. With the
tail capped there are no large frames to replay, the residual 249 packets
are not content-driven, and there is nothing left for the series to lock
onto. **Removing the cause removed the correlation, which is what should
happen.**

## 5. The uncapped path still runs

One 60 s check with **`PRIVYHUB_ENC_MAX_FRAME_SIZE=0`**:

| | |
| --- | --- |
| argv contains `-max_frame_size` | **no** — the flag is absent |
| `uncapped` | **true** |
| `max_frame_size_source` | `PRIVYHUB_ENC_MAX_FRAME_SIZE` |
| `any_override` | **true** |
| `default_max_frame_size_bytes` | still reported as 90000 |
| frames in 60 s | 4,052 |
| **max frame bytes** | **90,438** — above the cap, so the cap is genuinely absent |

**A useful detail fell out of it.** 90,438 bytes is about **76-79
packets**, because a large frame's packets run close to the 1,188-byte
payload maximum rather than the 1,066-byte session mean. That is why the
90,000-byte cap lands just under the 80-packet threshold and why every
capped session reports `max_packets` 77 and `frames_ge_80` 0. **The byte
cap and the packet threshold agree by arithmetic, not by coincidence.**

The no-variable environment was restored afterwards and the companion
restarted on it, confirmed by a final status read: `any_override` **false**,
source **`profile`**, `uncapped` **false**.

## 6. Tests

`d_base_p6a_2026-09-22/test_profile_cap.py`, 10 groups, no socket and no
thread: the profile declares the cap and carries it in `to_dict`; unset
gives the profile's cap with `any_override` **false**; a set value wins and
is an override; **`=0` gives an uncapped argv with the flag absent**; the
uncapped argv differs from the capped one by **exactly the two flag
tokens**; malformed and negative values fall back to the profile without
raising; the `-bufsize` knob is unchanged; a profile with the cap at 0
emits no flag; and a negative profile value is rejected at construction.
**All pass.** The `P5` and `P6` relay test suites still pass unchanged.

## 7. What this does not claim

- **The picture cost is still not instrument-measured.** `h264_vaapi`
  exposes no achieved QP here (`q=-0.0`) and this host's encoder has no
  `slices` or intra-refresh. §1 is a user report, one minute long, and is
  the whole of the perceptual evidence.
- **60 KB and VBV are measured alternatives, not rejected ones.** `P6`
  found 60 KB ties on loss with more constraint, and VBV loses 3x more
  while smoothing the bitrate most. Either remains available.
- **The Windows-era UDP pathology is untouched.** This cap is a Linux-host
  encoder setting; the Windows path is deferred and is not claimed fixed.
- **Adoption is not a claim that the target table is met.** `max output
  gap` still misses its target and `prolonged_starvation_events` is still
  unexplained.

## 8. Artifacts

Under `evidence/d_base_p6a_2026-09-22/`, SHA-256s in `p6a_sha256.txt`:
`p6a_run.sh`, `test_profile_cap.py`; per session `frames_*.jsonl`,
`heartbeat_*.jsonl`, `socket_*.jsonl`, `report_*.json`, `status_*.json`
(per-second ring stripped — it is `frames_*.jsonl`), `armcheck_*.json`
(the pre-hold status read) and `encoder_cmd_*.txt` (the two argv lines);
plus `index.txt`, `analysis_v1.txt`, `host_summary.txt`, `p6a_arms.json`.

Patch: `patches/D-BASE-P6A_FRAME_CAP_PROFILE_DEFAULT.md`.
Decision: `decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

## 9. Privacy

No address, MAC, SSID or device identifier in this record or any stored
artifact. The argv files carry the loopback destination and the local
render node, both constants of the code.
