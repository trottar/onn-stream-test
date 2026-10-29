# B30 — design, written before any code (QUEUE_2026-10-28K item 3): the trip's log-keeper and the trip check

Both are new tools; nothing existing changes. Flag absent = today, trivially: nothing runs unless A launches them.

## `tools/trip_log_keeper.py` (read-only; A launches it Thursday as `privyhub-trip-log`)

`python3 tools/trip_log_keeper.py --out docs/memory/evidence/trip_2026-10-30 --cap 2026-11-01T23:59Z [--start <UTC>]
[--copy-s 300] [--sample-s 60] [--once]`

- **The window:** it waits until `--start` (default: now), then runs until **the cap** (written to `cap_utc.txt` at
  launch, never changed) or **`<out>/STOP`** exists. At the end it makes one last copy and writes status `done (<why>)`.
- **Every `--copy-s` (300 s), G4-S4's list, incremental from the launch:**
  - the rotating logs in `logs/games/`: `adaptive_bitrate_shadow.jsonl`, `native_stream_heartbeat.log`,
    `native_stream_recovery.log`, `native_stream_ctrl_gaps.log`, `native_frame_sizes.jsonl`,
    `host_resource_samples.jsonl`, `native_pulseaudio.log`, `native_video_alpha.log`;
  - the hub's `logs/wan_sessions.jsonl` (B28's telemetry), `logs/session_audit.jsonl` (the audit rows) and
    `logs/impairment.jsonl` if present;
  - the new files in `logs/games/decoder_sessions/` and `logs/games/audio_timing/` (once each, after 10 s quiet);
  - the new game logs (`logs/games/*-game_*.log`);
  - the companion's journal (`journalctl --user -u privyhub-companion --since @t --until @now`).
- **By file and rotation, never overwriting:**
  - each step's new bytes of each log go into a **new chunk file**, `raw/<log>/<NNNNNN>_<UTC>.<ext>`. The ordinal
    grows; a name is never reused, and an existing file is never opened for writing.
  - Rotation: as G4-S4's `Tail`. The file's inode is followed; on a change, the old file's rest is read from
    `stream_log_archive/<log>.1..3` (the matching inode), then the new file from 0. A shorter file (truncated)
    restarts at 0.
  - Concatenating a log's chunks in ordinal order gives its bytes since the launch, redacted.
- **`manifest.sha256` grows:** one line appended per kept file, in `sha256sum` format, the hash of the file as
  written (redacted).
- **The redactor on every kept file before it is written:**
  - **secrets read in process, never printed:** the tailnet's name and DNS suffix, every node's DNS name, host name,
    tailnet addresses, current address and endpoints (`tailscale status --json`, re-read at every copy, so the
    friend's network's endpoints are caught as they appear); the host's own IPv4 addresses; the paired devices'
    ids and keys (`~/.config/privyhub/paired_devices.json`, read only);
  - **patterns:** any IPv4 literal but loopback / 0.0.0.0, an IPv6 literal, a MAC, `dev-<hex>` client ids, and hex
    runs of ≥ 32;
  - **each is replaced by a placeholder** (`<tailnet>`, `<node-name>`, `<tailnet-address>`, `<endpoint>`,
    `<host-address>`, `<device-id>`, `<key>`, `<ipv4>`, `<ipv6>`, `<mac>`, `<client-id>`, `<hex>`), counted per
    kind in the step's row. No value is ever printed.
- **Every `--sample-s` (60 s), into `samples/`:**
  - `overlay.jsonl`: the overlay state through the companion's own provider (`python3 -m companion.overlay --state
    --provider tailscale`): `connected`, `path`, `peer_ready`, `mtu`, `reason`; peers by count only;
  - `session.jsonl`: the games plugin's status (`GET /plugins/games/status` on the local control API): active,
    paused, the system's class (snes / ps1, never the title), `native_stream_active`, the recovery state if
    present;
  - both redacted as above.
- **`status.txt`:** one line: the phase, the last copy's time and bytes, the last sample, the cap, how to stop.
- **Survives the companion restarting:** it holds no file open between steps (each read opens, reads, closes by
  path), and an HTTP or subprocess failure is a row, not an exit.
- **It does nothing else:** no stream, no restart, no adb, no game, no setprop, no network change; nothing is
  deleted.
- **Tests** (`tests/trip_log_keeper/`, a fake log dir that rotates, fake secrets built from integers, fake
  samplers):
  - chunks concatenate to the bytes written, across a rotation and a truncation;
  - no file is rewritten (every kept file's hash stays as first written); the manifest grows and verifies;
  - a planted secret / pattern is replaced in the kept file and counted;
  - new decoder files are copied once;
  - STOP and the cap end it with a last copy; `--start` in the future waits;
  - a vanished then recreated log (a restart) is followed;
  - the samples hold no address.

## `tools/trip_check.py` (read-only; six plain lines, no identifiers)

1. `adopted: <N> lines; host check <ok|NOT ok> (<the failing fields, by name>)`. From `tools/e1_suite.py`'s
   `preflight()` host fields (`manager`, `environ` == `ADOPTED`, the drop-ins, no `e3_flag.conf`, no e4 file); adb is
   not a host field.
2. `apk: on the pin <short hash>` / `NOT on the pin` / `pin <short>, not read (adb off-LAN)`.
3. `overlay: connected <yes|no>, path <direct|relayed|no-peer|none>, peers <n>`.
4. `routing: newest token_issued <lan|overlay|…> at <UTC>` from `logs/session_audit.jsonl`.
5. `band: <5 GHz|2.4 GHz> (<MHz>)` if adb reaches the onn, else `band: adb off-LAN`.
6. `log-keeper: <status.txt's line>` or `log-keeper: not running (no status)`.

Each reader is a function taking its source (tests pass fakes). A failing reader prints `unknown (<why>)` on its line;
the six lines always print. Tests (`tests/trip_check/`): the six lines from fakes (LAN and remote cases, adb on and
off); no address, endpoint or id in the output when the fakes carry them.
