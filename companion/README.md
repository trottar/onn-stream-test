# companion/

The hub's server is the companion. It runs as the `privyhub-companion` systemd user unit, which starts
`python3 -u ./companion/privyhub_service.py` from the repository root. The descriptions below come from each module's
docstring, or from its name and classes where it has no docstring.

**The flag convention.** Most feature modules sit behind a `PRIVYHUB_*` environment line, and their docstrings say
"absent = today": with the line absent, nothing imports the module. The fourteen adopted lines each come from a drop-in
(see the repository [`README.md`](../README.md)). Every other flag is off unless a record says otherwise.

## The entry point and the core

- `privyhub_service.py`: the companion control service. It serves the control API (TCP 8765): `/status`, the plugins,
  the native-stream calls, `/diagnostics/health`, `/diagnostics/self-test`, `/diagnostics/bundle` and
  `/diagnostics/client-health`.
- `range_server.py`: a small HTTP media server with single-range byte requests (TCP 8000), for the app's Media3 /
  ExoPlayer VOD.
- `storage_presence.py`: non-blocking presence helpers for configured local removable storage.
- `config/sources.json`: the source catalog tree (the live / VOD categories and their sources).

## plugins/

- `games.py`: `GamesPlugin`, the games catalog and launch.
- `epg.py`: `EpgPlugin`, the EPG (guide), with the background guide warmer and deferred grabs.
- `iptv_org.py`: `IPTVOrgPlugin`, the IPTV channel catalog.
- `tv_state.py`: `TvStatePlugin`, the hub-authoritative, durable TV user-state store that the onn syncs with.

## games/

- `emulator_manager.py`: `EmulatorManager`, the managed RetroArch runtime (cores, launch, save / load).
- `config/emulators.json`: the emulator and core configuration.
- `metadata_importer.py`, `cheat_importer.py`: the local game metadata / art and cheat caches.
- `startup_reconcile.py`: the startup metadata reconcile (`run_startup_metadata_reconcile`) over the games catalog.
- `ps1_look.py`: the PS1 look per session, behind `PRIVYHUB_PS1_LOOK` (C5-M5B; not adopted).
- `link_drop_recovery.py`: the link-drop self-recovery state machine, host side (D-BASE-R3).
- `native_stream_heartbeat.py`: a host-side trace of a terminal client stall (D-BASE-R2).
- `decoder_session_log.py`: writes the client's decoder session report, with the host thermal reading.
- `decoder_report_http.py`: the decoder session report as a POST body (CL-B1).
- `host_resource_sampling.py`: runs `tools/host_resource_sampler.py` for each stream session (D-BASE-T1).
- `log_rotation.py`: bounded, append-only diagnostic logs (D-BASE-R4).

## The native stream

- `native_stream.py`: `NativeStreamManager`, the stream start / stop. On Linux it runs x11grab of the managed window
  and the `h264_vaapi` encoder.
- `native_stream_profiles.py`: the stream profiles: the adopted `native_game_720p60_reference` and the 1080p
  candidates (never the default).
- `native_fec_relay.py`: `NativeVideoFecRelay`, the 8+1 XOR FEC relay. It takes its input on loopback UDP 48110.
- `native_fec_rs.py`: the second parity of the `xor8_2` comparison arm (C4-M1).
- `native_session_io.py`: the audio streamer and the controller bridge (uinput), as `NativeSessionIO`.
- `native_host_telemetry.py`: the host process telemetry (its sampler class is `_WindowsProcessSampler`).
- `native_wgc_bridge.py`: the Windows Graphics Capture bridge (the preserved Windows reference path).
- `native_source_contract.py`: the generalized native source contract, as interfaces only (C6-D1). Nothing in
  production imports it.
- `process_audio/`: the Windows process-audio capture (C#, `PrivyHubProcessAudio.csproj`, `Program.cs`), part of the
  Windows reference.

## Adaptive bitrate and the remote lines

- `adaptive_bitrate.py`: the adaptive-bitrate policy engine (C3.L4-S1, shadow).
- `adaptive_bitrate_live.py`: the live mode, where the controller acts (line 1).
- `start_rung.py`: the rung a stream starts at, `PRIVYHUB_START_RUNG` (G8-S2).
- `remote_ladder.py`: the remote ladder, with the 4000 rung on a remote path (G5-S3).
- `remote_cap.py`: the remote rung cap, `PRIVYHUB_REMOTE_RUNG_CAP` (G5-S4).
- `remote_umbrella.py`: `PRIVYHUB_REMOTE=1`, the four WAN lines, each acting only on a remote-class session (B28, line
  13).
- `wan_telemetry.py`: the WAN-aware telemetry classification (G5-S1).
- `wan_adaptation.py`: the WAN adaptation rules R1-R5, `PRIVYHUB_WAN_ADAPTATION` (G5-S2; not adopted).
- `step_in_place.py`: `PRIVYHUB_STEP_IN_PLACE=1`, a ladder step on the same stream (B32, line 14).
- `lan_loss_rule.py`: one rung down on sustained FEC-unrecoverable groups, `PRIVYHUB_LAN_LOSS_RULE` (LAN-R1).
- `encoder_rc.py`: a named encoder rate-control profile, `PRIVYHUB_ENCODER_RC` (G8-S4; not adopted).

## Link recovery, restarts and the client's reports

- `link_recovery.py`: `PRIVYHUB_LINK_RECOVERY=1`, exactly the six stack lines (B20, line 10).
- `input_hold.py`: the fast input hold, which pauses the core on a controller silence (B2).
- `hold_tuning.py`: the hold's trigger, cap rule and resume (B6).
- `hold_ownership.py`: the hold / stall ownership at the link's return (B8).
- `hold_rewind.py`: rewinds the core on the hold's release (B4).
- `rewind_cores.py`: the hold's rewind for each core (B9).
- `rewind_needs_loss.py`: no rewind without loss (B33, live inside line 10; off with `PRIVYHUB_REWIND_NEEDS_LOSS=0`).
- `stall_signal.py`: the client's stall signal; a picture-only drop pauses the game (B7).
- `stall_owner.py`: the stall's resume, inside the one owner (B12).
- `link_recovery_wan.py`: the hold and stall thresholds for each path class, `PRIVYHUB_LINK_RECOVERY_WAN` (B23;
  G-A6 shelved).
- `restart_fast.py`: a guarded client restart, answered before the old teardown (B22, line 11).
- `restart_fast_unlock.py`: the ready at the new encoder's check, with the old audio stopped outside the lock (B24,
  line 12).
- `keyframe_request.py`: the client's keyframe request under loss, `PRIVYHUB_LOSS_GUARD` (B10; G-A8 prepared, not
  applied).
- `link_notice.py`: the client's link notice, as the host sees it (B14, on line 9).
- `surface_lost_row.py`: the client's `surface_lost` row (B32).
- `pad_slots.py`: the client's stable player-slot map, as the host sees it (B34).

## Audio, identity and the overlay

- `audio_codec.py`: the Opus audio path, host side, `PRIVYHUB_AUDIO_CODEC` (G4-W2, line 8).
- `session_identity.py`: session identity and authorization, host side: pairing, signed setup, tokens and the audit
  log (G3-S1, line 7).
- `overlay/`: the overlay provider boundary, `PRIVYHUB_OVERLAY_PROVIDER` (G1-S1, line 6). It contains:
  - `provider.py` (the contract);
  - `none.py` (always absent);
  - `tailscale.py` (reads `tailscale status --json` if the binary is installed; it never configures anything);
  - `__main__.py` (`python3 -m companion.overlay --state`, one read).

## VOD and test-only modules

- `vod_log.py`: the range server's per-request log and the player's retry rows, `PRIVYHUB_VOD_LOG=1` (B35, per run).
- `vod_drop_test.py`: a hub-side VOD connection drop for the bench, `PRIVYHUB_VOD_DROP_TEST=1` (B40, per run, never
  adopted).
- `impairment.py`: a user-space network-impairment shim on the loopback media hop, `PRIVYHUB_IMPAIRMENT` (G8-P1).

## diagnostics/

- `self_test.py`: the Diagnostics / Self-Test checks.
- `support_bundle.py`: the support bundle, with its redaction.
- `health_model.py`, `runtime_health.py`: the health snapshot and its model.
- `event_history.py`, `retention.py`: the diagnostic event history and the bounded retention policy.
- `client_feedback.py`: normalizes the client's feedback and link reports.
- `stream_telemetry.py`: the stream telemetry summary.
- `c3_actuator_probe.py`, `c3_fixed_bitrate_probe.py`, `c3_linux_actuator_probe.py`: the Phase C bitrate actuator
  probes. The live ladder uses the Linux actuator.
- `udp_transport_probe.py`, `udp_reverse_transport_probe.py`: the standalone UDP transport laboratory (UDP 48120 /
  48102). It is separate from the production stream.

The tests are in [`../tests/`](../tests/README.md) and `../tools/test_*.py`.
