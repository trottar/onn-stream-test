---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-R1 — resync loss counter, runtime confirmed on the onn

## Classification

**COMPLETE / RUNTIME VALIDATED.** `CURRENT.md` Next Action 1 (as of the
evening of 2026-09-20) performed in full: the `D-BASE-R1` APK is installed
on the onn, one ordinary session of the PS1 reference title ran for
127.5 s with no input, and the session report carries
`video.lost_packets_in_resyncs` with `lost_packets` counting the resync
jumps. Next Action 2 was **not** started.

Raw report: `logs/games/decoder_sessions/native_decoder_20260920_145024_777.json`
(SHA-256 `08c4836783f91413097e960961c7a9bbd6217380dfbfc536570110f009dd4fff`,
13,587 bytes), copied to
`group_a_2026-09-20/d_base_r1_runtime_native_decoder_20260920_145024_777.json`.

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 14:4x | ADB | already connected to the onn over wireless debugging (`adb devices` showed the device); no recovery needed |
| 14:44:48 | `adb install -r PrivyHub/app/build/outputs/apk/debug/app-debug.apk` | `Success`; APK SHA-256 `812bea87…1876`, the hash in the patch record; `lastUpdateTime` moved from 2026-09-19 00:31:59 to 2026-09-20 10:44:48 (device local). The install ended the old app process by itself; **no force-stop was issued at any point** |
| 14:45:2x | `python3 ./companion/privyhub_service.py` (detached, host shell) | listening on 8765; idle status `active: false` |
| 14:45:37 | `POST /plugins/games/launch?id=<Tekken 3 (USA) game id>` from the host shell | RetroArch (managed nightly AppImage, Beetle PSX HW 0.9.44.1) up in ~3 s; `active: true, paused: true` |
| 14:46:12 | `adb shell am start -n com.safeiot.privyhub/.streaming.NativeStreamActivity …` | **refused** — see "Deviation" |
| 14:47:1x | `adb shell am start -n com.safeiot.privyhub/.MainActivity` | launcher up, "NOW PLAYING Tekken 3 (USA) PAUSED" with the RESUME PLAYING preview |
| 14:48:16 | `adb shell input tap` on the RESUME PLAYING preview | `NativeStreamActivity` on top by 14:48:20; stream `active/ready`, FEC, audio and controller all active |
| 14:48:23 | game unpaused by the client's `native-stream-ready` | attract demo running; **no input from here until BACK** (120 s) |
| 14:50:23 | `adb shell input keyevent KEYCODE_BACK` | `MainActivity` on top by 14:50:26; app process kept alive |
| 14:50:24.777 | client `POST /plugins/games/decoder-session-log` | report written by the companion; `duration_ms` 127,497 |
| 14:51 | `POST /plugins/games/stop`, then SIGTERM to the companion | game `active: false`; no RetroArch, ffmpeg, FEC relay, process-audio or companion process left; no listener on 8765 or 48100-48102 |

No input reached the game during the demo: `controller.motion_events` 0 in
the report, and the only device input after the stream opened was the
single BACK key.

## The counter, confirmed

| field | value |
| --- | ---: |
| `video.lost_packets` | 695 |
| `video.lost_packets_in_resyncs` | **493** (field present) |
| `video.robust_missing_packets` | 202 |
| `video.sequence_resyncs` | 3 |
| `stream_discontinuities[].jump_packets` | 129 + 182 + 182 = **493** |

- `lost_packets_in_resyncs` equals the sum of the three resync jumps
  exactly, so the jump is credited once per resync and nowhere else.
- `lost_packets` − `lost_packets_in_resyncs` = 202 = `robust_missing_packets`:
  the gap-counted loss is unchanged by the patch. Under the pre-fix rule
  this session would have reported `lost_packets` **202**; it reports
  **695**, so `lost_packets` >= the pre-fix reading as required.
- The A2 re-score script (`group_a_2026-09-20/a2_rescore_decoder_sessions.py`)
  run over the corpus after this session scores it `v_lost_pm` 327.07 and
  `loss_corrected_pm` 327.07 — identical, as the with-field rule requires.
  (The scored table under `group_a_2026-09-20/` was left as the frozen
  Group A artifact, 148 rows; this run's 149-row table was not committed.)

The **transport column of the target table can now be read** from any report
that carries the field. Every report on disk before this one is pre-fix and
still needs the correction rule.

## The session itself (one session, not a distribution)

127.5 s at 7000 kbps, `low_latency_enabled: false`, epoch `C_post_L2b`,
scored by the A2 script:

| metric | target | this session |
| --- | --- | ---: |
| receive->output spikes >= 20 ms / min | < 200 | 2,258 |
| rendered fps | >= 59.5 | 56.27 (received-AU 59.19) |
| max output gap | <= 100 ms | 639 |
| stale output drops / min | < 20 | 169.9 |
| lost packets / min | < 10 | 327.1 |
| audio underruns / min | < 5 | 120.9 (257 in session) |

Nothing here changes the picture from the Group A record; it is one more
session in the same distribution. Two things are worth keeping:

- **The 639 ms worst gap is the outage + IDR-wait shape again.** The third
  `sequence_resync` fired at `elapsed_ms` 124,572 (jump 182); its first IDR
  arrived 492 ms later at 125,064; the slow event at 125,088 shows
  `rx_to_decode_ms` 649 / `output_gap_ms` 639 with `codec_in_flight` 5. The
  second and third resyncs were 686 ms apart with identical 182-packet
  jumps. `packets_dropped_waiting_for_idr` 377.
- **Steady state without resyncs** (0-60 s) had no slow event >= 50 ms until
  the first resync at 60,552 ms; the retained slow events cluster after
  110 s. Consistent with A2: the tail is transport, the 20-60 ms body is
  the decode path.

## Deviation from the instruction as written

`am start -n com.safeiot.privyhub/.streaming.NativeStreamActivity` **cannot
open the stream from a host shell.** The activity is `android:exported="false"`
(`AndroidManifest.xml`); on this Android 14 build the shell user gets
`SecurityException: Permission Denial … not exported from uid 10115`, and
`run-as com.safeiot.privyhub am start …` (and the `cmd activity` form) exit
255 silently under the `runas_app` SELinux domain. The exported entry point
is `MainActivity`, whose RESUME PLAYING preview calls the same
`openNativeGameStream()` the launcher uses, with the companion host from the
client's saved settings and the active session's title. That is the path
used above; the stream session that resulted is an ordinary client-launched
session in every field the report carries. Recorded in `TOOLS.md`.

A second, minor difference: the game was launched by a host-shell `POST` to
`/plugins/games/launch`, so the launch route's controller preflight bound
the persistent controller to the loopback address first. `native-stream-start`
from the onn rebinds it (`ensure_started` restarts on a client-address
change, `native_session_io.py`), and the status poll showed the controller
active alongside FEC and audio before the demo began. No input was sent, so
nothing depended on it.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied report. The companion host is referred to as
"the client's saved settings".
