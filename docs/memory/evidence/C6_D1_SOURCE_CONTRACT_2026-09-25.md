---
memory_schema: 1
as_of: 2026-09-25
status: C6-D1 DONE — generalized native source contract ESTABLISHED (architecture/NATIVE_SOURCE_CONTRACT.md) with an interface module imported by nothing in production (companion/native_source_contract.py, 7/7 tests: the games description validates, native_stream is never loaded); seam map of the games source; 14 cross-boundary findings, one a correctness defect (recovery's restart refuses after any ladder transition); migration list of 9 moves; C7 status table; no production file changed, no session, no restart
---

# C6-D1 — the generalized source contract

Task: `handoffs/C6-D1_SOURCE_ABSTRACTION_DESIGN_TASK.md` (weekend queue 2,
item 1, authorized by the user 2026-09-25). Architecture record:
`../architecture/NATIVE_SOURCE_CONTRACT.md`. Patch:
`../patches/C6-D1_SOURCE_CONTRACT.md`. Evidence: `c6_d1_2026-09-25/`
(`unit_tests.txt`, `new_files_sha256.txt`, `sha256_manifest.txt`).

**Scope.** Documentation plus two new files: the module and its test.

- No production file changed. No companion module imports the contract,
  and a test checks that.
- The module imports `adaptive_bitrate`, `native_fec_relay` and
  `native_stream_profiles` for their constants. None of them imports
  `native_stream`.
- There was no session and no restart.

## Seam map (the games source, line ranges of the working tree on 2026-09-24)

| stage | where, today | in → out |
| --- | --- | --- |
| **Capture** | `native_stream.py`: `_linux_display` 354-357 (only `DISPLAY`; the DP dummy plug is set up by the OS and the unit, not by code); `_find_linux_retroarch_window` 761-937 (xdotool, largest window ≥ 64×64); `_select_capture_target` 1177-1199 (2 s retry, never the whole desktop); x11grab is the **input of the encoder process itself** (`_build_linux_ffmpeg_command` 1395-1410). The "paused frame" is lifecycle order: `native-stream-start` pauses before starting (`plugins/games.py` 3639-3652) | emulator PID → window id |
| **Profile/encoder** | `native_stream_profiles.py` (163 lines): `NATIVE_GAME_720P60_REFERENCE` 138-163; env overrides `native_stream.py` 169-291 (`encoder_overrides`, `audio_cushion`, `audio_redundancy`); argv `_build_linux_ffmpeg_command` 1321-1450; start/stop 1537-1735 / 1498-1534; **bitrate actuator** `diagnostics/c3_linux_actuator_probe.py` `_run_c3_linux_bitrate_cycle` 443-821, entered via the manager's `diagnostic_*` methods 2266-2459 and the loopback plugin actions `games.py` 3341-3464 | profile → argv → RTP to loopback:48110 |
| **Transport/FEC** | `native_fec_relay.py` (1,412 lines): `PHF1` v1 header 19-31, `_handle_rtp` 526-588, `_emit_group_locked` 929-1005, `_send` 1310-1353; frame-size log 595-927; audio `native_session_io.py` `NativeAudioStreamer` 25-1560 (`PHA1`, redundancy 491-518); controller (reverse) `NativeControllerBridge` 1562-2565 | RTP → RTP + parity to the client; PCM datagrams; controller datagrams in |
| **Client feedback** | heartbeat `games.py` 3471-3570 + `games/native_stream_heartbeat.py` (v3 schema, fields 35-90); report `games/decoder_session_log.py` 49-159 (cap 48,000); client health `diagnostics/client_feedback.py`; telemetry `diagnostics/stream_telemetry.py` 104-262 (built at `privyhub_service.py` 2180-2186) | query/body → logs, snapshots |
| **Lifecycle** | `launch` `games.py` 3258-3339; `native-stream-start` 3628-3679 → `NativeStreamManager.start`; `native-stream-ready` 3681-3719; `native-stream-stop` 3721-3746; recovery `games/link_drop_recovery.py` 71-603, wired `games.py` 94-120 | |
| **Diagnostics** | `NativeStreamManager.status()` 478-646; plugin `native-stream-status` `games.py` 3044-3091 (adds recovery, adaptive_bitrate, last_heartbeat, loss_per_min_recent); Linux host sampling `games/host_resource_sampling.py`; `native_host_telemetry.py` and `process_audio/` are Windows-only | |
| **Adaptation** | `adaptive_bitrate.py` (shadow, reads `privyhub_stream_telemetry_v1`; hooked `privyhub_service.py` 2187-2196 and `games.py` 3050-3052). The actuator class exists only in the docs and in this module | telemetry → decisions (never acted) |

## Cross-boundary findings (C6's findings)

1. **`native_stream.py` owns everything.** Capture, encoder, transport,
   audio, controller and host diagnostics are all in one class: `__init__`
   96-111, `_start_linux_locked` 1537-1735. On Linux, capture and encoder
   are one FFmpeg process, so the capture seam is logical, not a process
   boundary.
2. **Profile values cross into audio and the client.** Redundancy is
   pushed into the audio streamer (1711-1716). The cushion is a client
   queue setting. The Windows path never applies redundancy, yet status
   reports it.
3. **Constants are copied, not shared:**
   - the ladder, in five places (`adaptive_bitrate.py` 57,
     `c3_linux_actuator_probe.py` 42, `c3_fixed_bitrate_probe.py` 17
     (Windows ladder), a literal allowlist at `games.py` 3444-3452, and a
     7000 guard at `native_stream.py` 2283);
   - the audio 5 ms packet and max offset 16;
   - relay port 48110 and `pkt_size=1200`, twice each;
   - the heartbeat field whitelist, twice.
4. **The relay's "frame cap" is not the encoder's cap.** `frames_over_cap`
   uses `PRIVYHUB_FRAME_BYTE_CAP` (relay 96, 818-826), not the profile's
   90,000, so it does not measure the adopted cap unless that variable is
   also set. Verified in source.
5. **`plugins/games.py` reaches into private fields** of the manager:
   `_native_stream._session_io.controller` (106-120).
6. **The bitrate actuator is implemented outside the encoder.**
   `c3_linux_actuator_probe.py` touches manager internals (`_process`,
   `_fec_relay`, `_active_bitrate_kbps`, `_build_linux_ffmpeg_command`, and
   more).
7. **Correctness defect.** Recovery's `restart_encoder` is the continuity
   *diagnostic* (`games.py` 99-102).
   - That diagnostic refuses unless the active bitrate is 7000
     (`native_stream.py` 2283-2287, `c3_linux_actuator_probe.py` 113-121,
     both verified). So **after any ladder transition, a recovery restart
     fails**.
   - A full start resets the bitrate to 7000 (1521, 1659-1662), silently
     undoing the level.
   - It does not bite today: no live controller exists and every session
     returns to 7000. **A live `C3.L4` must fix it first.**
   - **Fixed 2026-09-25 (`C3-F1`, WORKING)**: recovery's restart is now
     level-preserving at 5000-7000 (`C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`).
8. **Status reads change lifecycle.** `status()` reaps (478-482). The
   client-health route calls `native-stream-status` every 2 s, doing reap,
   thermal read, heartbeat tail, a 64 KB loss-window read and the shadow
   status in the request path.
9. **Status mixes layers.** Transport sender counters, the stream bitrate
   and the shadow's inputs are all read out of one combined dict.
10. **Host detail reaches the status.** It carries absolute paths
    (relay `log_path`, `host_telemetry.path`), the encoder argv (display,
    window id, DRM device) and the capture target (PID, title, class).
    None of these is a network address. The client address stays in
    private fields (`_recovery_start_args`, the relay's, audio's and the
    controller's `_client_ip`) and is exported by no status field.
11. **Exception text is copied as-is** into `audio.error` /
    `controller.error` (`native_session_io.py` 2615-2627). It is an
    address-leak risk if an OS error names one.
12. **Companion code puts `tools/` on `sys.path`.** `_host_thermal_c` is
    duplicated in `native_stream.py` 456-476 and `decoder_session_log.py`
    21-46.
13. **Some diagnostics assume Windows.** `health_model.py`
    `_component_capture` keys on `wgc_runtime_found`, and the Windows-only
    telemetry profiler is always in status.
14. **Transport counters double as lifecycle signals.** The relay's
    `rtp_packets` is the restart-resume signal, and the heartbeat's
    `last_output_age_ms` drives recovery.

The seam map was read by a read-only survey pass and spot-verified for
findings 4 and 7.

## The migration list

See the architecture record §"What the games source would have to move to
conform": 9 moves.

- 1 is large (split `NativeStreamManager`).
- 1 is medium (the actuator into the encoder stage).
- 7 are small.
- Move 3 (recovery's restart primitive) is a correctness item, and a
  precondition for any live `C3.L4`.

## Tests (`unit_tests.txt`): 7 / 7 OK

- the module never loads `native_stream`;
- nothing in `companion/` imports the contract;
- the games description validates, filled from `native_stream_profiles`,
  `native_fec_relay` and `adaptive_bitrate`: `video_only_restart`, ladder
  5000-7000, reference 7000, `xor8_1` wire v1 group 8;
- the constants are read, not copied;
- validation rejects duplicate wire versions, an identity-bearing
  diagnostics surface, and an actuator without a ladder;
- today's profile satisfies `SourceProfile`;
- the lifecycle states are present.

## C7 accounting

Appended to `docs/ROADMAP.md` §C7 and `docs/PROJECT_STATUS.md`.
