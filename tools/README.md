# tools/

The hub's scripts. Run them from the repository root, for example `python3 tools/diag_check.py`. The descriptions come
from each file's docstring, or from its name and arguments where it has none.

The scripts fall into five groups:
- the **live tools**, used today;
- the **maintenance utilities**;
- **measurement scripts** from closed phases (each is named in its record and can be re-run);
- the **historical probes** (`probe_*`, `probes/`);
- **unit tests**.

## Live tools

**The adopted state and the suite:**
- `e1_suite.py`: the Phase E workload suite runner (frozen definition: `docs/memory/architecture/E1_WORKLOAD_SUITE.md`).
  It also holds the state:
  - `ADOPTED`, the fourteen adopted lines;
  - `EXPECT_APK`, the CONFIRMED APK pin;
  - the host preflight.

  Its modes are `--list`, `--check <dir>`, `--self-test` and `run …`.
- `e1_remote.py`: the suite's off-site row, `e1_suite.py run --remote …` (G4-P1).
- `e1_sampler.py`: the Phase E sampler set: a 1-s host sampler plus the workload's own telemetry.
- `e3_state.py`: the adopted state as one JSON line (`"ok"`, the preflight, `"apk": "CONFIRMED"`, the link-recovery
  stack).
- `capability_probe.py`: the capability probe v1 (E5). It reads the host and prints the seven capability classes as
  JSON.
- `host_resource_sampler.py`: the durable host resource sampler. The companion runs it for each stream session
  (D-BASE-T1).

**The diagnostics (B36):**
- `diag_keeper.py`: the always-on diagnostics keeper, read-only on the hub. It keeps redacted copies in
  `~/privyhub_diag/<YYYY-MM-DD>/` with 30-day retention, plus `sessions.jsonl`, `status.txt` and a `STOP` file.
- `privyhub-diag.service`: the keeper's systemd user unit.
- `diag_check.py`: six plain lines: adopted, apk, overlay, routing, band, diag-keeper.
- `diag_read.py`: the one-line read for a range (`today`, `"last night"`, `"YYYY-MM-DD HH:MM..HH:MM"` UTC, `trip`).
  It writes one Markdown file under `docs/memory/evidence/reads/`.
- `trip_check.py`, `trip_log_keeper.py`: the trip's check and log-keeper (B30). The trip keeper's unit ended on
  2026-11-01. The files stay because `diag_check.py` and `diag_keeper.py` reuse their redactor, tails and readers.

**Memory:**
- `check_memory_health.py`: the memory health check: the required files, the size limits, CURRENT.md's headings.

**Code:**
- `claude_settings_local.json`: the Code allow-list. It was committed with G4-W1 / G4-W2 (2026-10-18).

## Maintenance utilities

- `update_game_metadata.py`: updates the local game metadata and box-art cache from the Games catalog.
- `update_game_cheats.py`: updates the local game-cheat cache. It never activates cheats.
- `storage/configure_vod_storage.py`, `storage/enable_vod_appliance_mode.py`: the VOD storage setup.
- `recover_orphan_game_session.py`: recovers an orphaned game session through the local control API.
- `diagnostic_retention.py`: the bounded diagnostic retention (`--apply` to act).
- `privyhub_debug_bundle.py`: a redacted debug bundle (`--mode game-smear | latest | transport-history`).
- `privyhub_audio_history.py`: the audio history diagnostic.
- `collect_game_session_diagnostics.py`: collects a game session's diagnostics.
- `audit_repo_checkpoint.py`: audits checkpoint source tracking and repository hygiene.

## Measurement scripts from closed phases

Each one is named in its record under `docs/memory/evidence/`.

- **E3** (closed): `e3_probe.py` (read-only measurement probes), `e3_children_log.py` (the companion's reaped-children
  CPU), `e3_guide_read.py` ("the guide still serves"), `e3_table.py` (one comparison table over run summaries),
  `e3_redact_check.sh` (a redaction check over text files).
- **C3-L4** (closed): `c3_l4_nft_night.py` (the `nft` fault-injection night, started by the user), `c3_l4_fake_sudo.py`
  (test only, a fake `sudo` for it), and the offline replays `c3_l4_l1_replay.py`, `c3_l4_n1_replay.py`,
  `c3_l4_n2_replay.py`.
- **C5** (closed): the offline replays `c5_m5_replay.py`, `c5_m5b_replay.py` and `c5_close_replay.py`; `ps1_look.sh`
  (the PS1 look on the TV, one command per look).
- **D7:** `d7_regression.py`, the native Linux regression, scripted where it can be.
- **CL-B7:** `cl_b7_onn_threads.py`, where the app's CPU goes, per thread, on the onn (adb state reads).
- **ML-R1:** `hitch_predictor.py`, the hitch early-warning scorer (pure Python).
- **B2:** `unattended_frames.py`, host frames emitted while no controller packet had arrived for >= 250 ms.
- **D-BASE router-boundary captures:**
  - `analyze_*_bridge_boundary_pcap.py`, `analyze_*_dual_boundary_pcap.py`, `analyze_*_netdev_counter_probe.py`;
  - `run_*_bridge_boundary_probe.sh`, `run_*_dual_boundary_probe.sh`, `run_*_acceleration_off_dual_boundary_probe.sh`,
    `run_*_netdev_counter_probe.sh`.

## Historical probes

These are one-off probes from Phases A, B, C and D. Each is named in its own record. None is part of today's running
system.

- **`probe_*.py`, 62 files**, grouped by prefix:
  - `probe_a4_*` (3), Windows A4 audio;
  - `probe_a8_*` (9), input profiles;
  - `probe_adb_*` (1);
  - `probe_b1_*` (15), diagnostics, health and retention;
  - `probe_b3_*` (2), `probe_b4_*` (10), `probe_b5_*` (1), `probe_b6_*` (1): the legacy-stack removal and the clean
    native baseline;
  - `probe_c1_*` (1), `probe_c2_*` (1), `probe_c3_*` (6): the stream parameters, telemetry and actuators;
  - `probe_four_player_*` (3), `probe_phase_a_*` (4), `probe_ps1_multitap_*` (5): the controller and Phase A
    regressions.
- **`probes/`, 40 files:** the `d075`–`d136` Linux-migration probes (audio, controllers, the RetroArch runtime,
  companion startup, VOD, storage, EPG, TV-state sync, the guide UI and latency).
- `manual_checkout.py`: the shared prompt / answer helpers for the manual checkout probes.
- `remove_b4_8_device_moonlight_package.py`: the one-off legacy-package removal (B4.8).
- `a4_audio_mute_probe/`, `a4_audio_float_attenuation_probe/`: empty directories, on disk only (Windows A4).

## Unit tests

There are eleven `test_*.py` files. Each runs as `python3 -m unittest tools/test_<name>.py -v`, the command in its
docstring; the two `test_ps1_look*` files end in `unittest.main()` and run directly too.

- `test_adaptive_bitrate_live.py`, `test_adaptive_bitrate_shadow.py`: the live and shadow bitrate policies (C3-L4).
- `test_c3_f1_recovery_restart.py`: recovery's encoder restart at any ladder level (C3-F1).
- `test_c3_l4_nft_night.py`: the nft night harness's allow-list, parser and fake sudo.
- `test_c5_m1_profile_selector.py`: the 1080p60 candidate profile and `PRIVYHUB_NATIVE_PROFILE_ID`.
- `test_cl_b1_decoder_report_body.py`: the decoder report as a POST body.
- `test_e1_remote.py`: the suite's `--remote` row.
- `test_fec_xor8_2.py`: the `xor8_2` codec pair.
- `test_native_source_contract.py`: the native source contract module.
- `test_ps1_look.py`, `test_ps1_look_helper.py`: the PS1 look and its helper script (with stubs on PATH).

The per-feature host tests are in [`../tests/`](../tests/README.md).
