# tests/

The host-side unit tests, one directory per feature. They need no stream, no companion and no network: they use fakes,
temporary directories and the loopback, and nothing here runs `adb`. Run them from the repository root. The command is
the one in each test file's docstring:

```text
python3 -m unittest discover -s tests/<feature> -v
```

Each `test_*.py` file also ends in `unittest.main()`. More tests are in `tools/test_*.py` (see
[`../tools/README.md`](../tools/README.md)), and the app's Kotlin tests are in `PrivyHub/app/src/test/` (see
[`../PrivyHub/README.md`](../PrivyHub/README.md)).

The descriptions below come from each file's docstring. The tag is the item that built it (its record is under
`docs/memory/evidence/`).

## The adopted lines

- `audio_codec/`: the Opus audio path, host side (G4-W2; line 8).
- `overlay/`: the overlay provider boundary (G1-S1; line 6). Its `fixtures/` hold canned `tailscale` status and
  netcheck JSON.
- `session_identity/`: the session gate, the request handler and range-server replays, the hardening, and `sig_v` 3
  (G3-S1, G3-S3, CL-B4; line 7). `common.py` holds the helpers.
- `link_report/`: the client's Wi-Fi link report, host side (B3; line 9).
- `link_notice/`: the client's link notice, from the heartbeat (B14).
- `link_recovery/`: `PRIVYHUB_LINK_RECOVERY=1` = exactly the six stack lines (B20), and its config row (B21) (line 10).
- `restart_fast/`: a guarded restart's start answered before the old teardown (B22; line 11).
- `restart_fast_unlock/`: the ready at the new encoder's check (B24; line 12).
- `restart_fast_unlock_relay/`: nothing from the old encoder forwarded after the relay's stop (B26).
- `remote_umbrella/`: `PRIVYHUB_REMOTE=1`, the four WAN lines on a remote-class session only (B28; line 13).
- `step_in_place/`: a ladder step on the same stream; the explicit cap beside the umbrella (B32; line 14).
- `rewind_needs_loss/`: no rewind without loss (B33, live inside line 10).

## The link-recovery stack's parts

- `input_hold/`: the fast input hold (B2).
- `input_hold_rewind/`: the rewind on the hold's release (B4).
- `input_hold_b6/`: the hold's trigger, cap rule and resume (B6).
- `input_hold_b8/`: the hold / stall ownership at the link's return (B8).
- `stall_signal/`: the client's stall signal, through the real receive loop (B7).
- `rewind_cores/`: the hold's rewind for each core (B9).
- `stall_owner/`: the stall's resume inside the one owner (B12).
- `stall_resume_speed/`: the stall resume's speed, and the saves (B16).
- `guard_end/`: a guarded client restart ends the old session in the start request (B17).
- `session_end/`: no save and no hold once the session's end is known (B18).
- `link_recovery_wan/`: the hold and stall thresholds for each path class (B23; G-A6 shelved).

## The ladder and the remote path

- `start_rung/`: the start rung (G8-S2). `stub_manager.py` is a `NativeStreamManager` that runs for real against
  stubs; other suites reuse it.
- `remote_ladder/`: the remote ladder (G5-S3).
- `remote_cap/`: the remote rung cap (G5-S4).
- `wan_telemetry/`: the WAN telemetry classification (G5-S1).
- `wan_adaptation/`: the WAN adaptation rules, each rule with hand fixtures (G5-S2; not adopted).
- `lan_loss_rule/`, `lan_loss_rule_bidir/`: the LAN loss rule and its bidirectional form (LAN-R1, LAN-R2).
- `encoder_rc/`: the encoder's rate-control profile (G8-S4; not adopted).
- `keyframe_request/`: the client's keyframe request, host side (B10).

## Client rows, host side

- `surface_lost/`: the client's `surface_lost` row (B32).
- `pad_slots/`: the client's stable slot map (B34).
- `pad_slots_changes/`: `updates_by_player` counts only the changed slots (B38).

## VOD

- `vod_log/`: the range server's per-request log and the player's retry rows (B35).
- `vod_drop_test/`: the hub-side VOD drop for the bench (B40; per run, never adopted).

## The impairment shim

- `impairment/`: the impairment shim's parser and stages (G8-P1), and its blackout in both directions (B1).

## Diagnostics and the trip tools

- `diag_keeper/`: the diagnostics keeper on a fake log directory that rotates (B36).
- `diag_read/`: `diag_read` on a fake keeper directory (B36). `diag_fixture.py` is a fake evening.
- `diag_check/`: the diag check's six lines, from fakes (B36).
- `trip_check/`, `trip_log_keeper/`: the trip check and the trip's log-keeper (B30). The tools stay because the
  diagnostics reuse them.
