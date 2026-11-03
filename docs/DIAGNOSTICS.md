# Diagnostics: what runs, how to read it, and the transport probes

As of 2026-11-03. The current state (the fourteen adopted lines, the units, the APK) is in `docs/memory/CURRENT.md`.
This page replaces the 2026-09-07 inventory, which listed `.ps1` probe wrappers that no longer exist.

## 1. The diagnostics keeper: `privyhub-diag` (B36)

A user unit that runs all the time beside `privyhub-companion`. It copies the hub's logs, read-only, into a dated
folder outside the repo. It is B30's trip log keeper made permanent. Record:
`docs/memory/evidence/B36_DIAG_KEEPER_2026-10-31.md`. It has been running since HOME-1 (2026-11-03 UTC;
`docs/memory/evidence/HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md`).

- **Code:** `tools/diag_keeper.py`. It reuses `tools/trip_log_keeper.py`'s redactor, tails and readers, so that file
  must stay in the tree while the unit exists.
- **Unit file:** `tools/privyhub-diag.service` (`Restart=on-failure`, `Nice=10`, `WantedBy=default.target`). B's install
  command, run by the user at HOME-1:

  ```text
  mkdir -p ~/.config/systemd/user && cp tools/privyhub-diag.service ~/.config/systemd/user/ \
    && systemctl --user daemon-reload && systemctl --user enable --now privyhub-diag
  ```

- **What it copies:**
  - the stream logs in `logs/games/`, following rotation;
  - `wan_sessions`, `session_audit` and `impairment`;
  - each game log, new decoder reports and audio-timing files;
  - the companion's journal;
  - `logs/vod_client.jsonl` and `logs/vod_range.jsonl`.
- **Where:** `~/privyhub_diag/<YYYY-MM-DD>/` (the UTC date of the copy):
  - `raw/<log>/…` chunks, never overwritten;
  - `samples/{overlay,session,copies}.jsonl`;
  - `manifest.sha256`.

  At the root are `status.txt`, `sessions.jsonl`, `retention.jsonl` and `state.json`, the last holding each tail's
  position so that a unit restart resumes. A root inside the repo is refused.
- **Cadence:** a copy every 300 s and a sample every 60 s. It has no cap. It stops on a `STOP` file at the root or on
  `systemctl --user stop privyhub-diag`, with a final copy either way.
- **Redacted:** every chunk, sample and summary row goes through the keeper's redactor.
- **Retention, the one deletion it makes:** a day folder directly under the root, a real directory dated more than
  **30 days** before today, is removed whole. It checks at its start and at each UTC date change, and writes one row
  per removal to `retention.jsonl`.
- **`sessions.jsonl`:** one row per game session, written about 90 s after its `session_ended`. The row holds the
  length, the core and title, players and slot map, the path class, the rung history (with `in place`), loss, RTT,
  fps, the pauses, holds, stalls, rewinds and restarts with their causes, hitches, silences, underruns and RSSI. A
  summary that fails writes `{"error": <type>}`, and the keeper carries on.
- **Stop:** `systemctl --user stop privyhub-diag` (or the `STOP` file); `disable` as well to keep it from starting at
  login. The day folders stay on disk.

## 2. Reading it: `tools/diag_read.py "<range>"`

```text
python3 tools/diag_read.py "last night"
python3 tools/diag_read.py today
python3 tools/diag_read.py "2026-10-30 21:00..05:00"     # UTC; an end before the start is the next day
python3 tools/diag_read.py trip                         # the trip keeper's folder, its whole span
```

- **Sources:** by default, the `~/privyhub_diag` day folders that overlap the range. `--source` takes any keeper
  folder, `--live` reads `logs/` directly, and `--trip-dir` points at the trip keeper's folder. All are opened
  read-only.
- **Output:** one new Markdown file under `docs/memory/evidence/reads/`, never overwriting one, and its path printed.
  It contains:
  - the per-session table and a per-10-min table;
  - every client restart with its cause (the client's trigger, paused and away ms, `surface_lost`, the silences and
    stalls in the 20 s before, the rung before and after);
  - every rewind, pause, hold and stall with its cause (B33's `why`);
  - the ladder steps with `in place`, the `pad_slots` rows and the VOD rows;
  - a ±60-s per-second view around each restart and stall. `--around HH:MM:SS` and `--around-saves` add more views.
- **Example:** HOME-1's read of the trip, `docs/memory/evidence/reads/diag_trip_20261103T004048Z.md`.

## 3. The quick check: `tools/diag_check.py`

It prints six redacted lines and changes nothing:

1. **adopted:** the adopted line count and `e1_suite`'s host check, with any failing field named;
2. **apk:** on the pin or not, read over adb, or "not read (adb off-LAN)";
3. **overlay:** connected, the path (direct / relayed / no-peer / none), online peers by count;
4. **routing:** the newest `token_issued`'s routing class and time;
5. **band:** 5 GHz or 2.4 GHz with the frequency, if adb reaches the onn;
6. **diag-keeper:** the keeper's `status.txt` line, and whether `privyhub-diag` is active.

A reader that fails prints `unknown (<why>)`. Lines 1-5 are `tools/trip_check.py`'s, which is kept unchanged.

## 4. The companion's own diagnostics

These are the companion's endpoints. Under session identity v2 (adopted line 7) a client needs the `diagnostics`
permission for most of them; a paired device gets it by default (`docs/REMOTE_TRUST.md` §8).

- **`GET /diagnostics/health`:** the live health snapshot.
- **`GET /diagnostics/stream-telemetry`:** the stream telemetry store, plus a `wan` object when the WAN telemetry is
  active (G5-S1).
- **`POST /diagnostics/self-test`** (`companion/diagnostics/self_test.py`, schema
  `privyhub_diagnostics_self_test_v1`): checks `storage_writability`, `adb_development` and `emulator_runtime`, each
  with a status, event code and summary.
- **`POST /diagnostics/bundle`, the support bundle** (`companion/diagnostics/support_bundle.py`):
  - it runs `tools/privyhub_debug_bundle.py --mode latest` and adds the health snapshot and a diagnostics context;
  - it returns the sanitized `SHARE_ME.zip`'s relative path, size and sha256;
  - the bundles go under `logs/debug_bundles/<stamp>_<mode>/` (`SHARE_ME.txt`, `manifest.json`, `SHARE_ME.zip`);
  - addresses and MACs are redacted, and the raw packet captures are excluded.
- **By hand:** `python3 tools/privyhub_debug_bundle.py --root . --mode {game-smear,latest,transport-history}
  [--since-utc …]`.
- **On the onn:** the client's Diagnostics screen (`DiagnosticsActivity`) has REFRESH (health), RUN SELF-TEST and
  COLLECT DIAGNOSTICS (the bundle).
- **Retention of `logs/`:** `tools/diagnostic_retention.py` builds a plan from `companion/diagnostics/retention.py`'s
  policy and prints it. With `--apply` and the policy's `--policy-sha256` it deletes per the plan. The policy covers
  `logs/transport_probe`, `logs/transport_reverse`, `logs/debug_bundles` and `logs/games/stream_log_archive`.

## 5. The UDP transport probes (the 2026-09 investigation)

These are synthetic probes, kept apart from production streaming, for testing a host or network path before
production audio or transport is changed. The investigation is
`docs/investigations/2026-09-07-udp-transport.md`.

**What exists:**
- `companion/diagnostics/udp_transport_probe.py`: `send` (a paced synthetic stream from the host) and `compare`
  (host against onn packet logs);
- `companion/diagnostics/udp_reverse_transport_probe.py`: `receive` (on the host), `compare` and `pktmon-presence`
  (the last for Windows PktMon summaries; Windows-era);
- the client activities `UdpTransportProbeActivity`, `UdpReverseTransportProbeActivity` and
  `UdpLoopbackProbeActivity` (onn-local loopback; no Python half).

**The `.ps1` wrappers** (`run_udp_transport_probe.ps1`, `run_udp_loopback_probe.ps1` and
`run_udp_reverse_transport_probe.ps1`) are not in the tree.

**Last run:** D6-R1 (2026-09-24, `docs/memory/evidence/D6_R1_UDP_SUITE_REPLAY_2026-09-24.md`). It replayed forward
and reverse on the Linux host (wired) → home router → onn (5 GHz) path, 3 valid runs each way, driven by its own runner
scripts (in the record's directory).
- The old duplication signature was not reproduced in either direction (0-4 same-stamp duplicates a run). It was
  classed as specific to the old environment.
- **Port note:** use free ports (D6-R1 used 48120 / 48122), because the companion's controller socket owns 48102.
- **Screensaver note:** wake the onn first; its screensaver ended three first-pass runs.

The paths tested:

```text
forward:  host sender -> host stack / NIC -> network / Wi-Fi -> Android kernel UDP arrival -> Android userspace
loopback: Android sender -> 127.0.0.1 UDP -> Android kernel timestamp -> Android receiver
reverse:  Android sender (nonblocking DatagramChannel, send-completion timing) -> Wi-Fi / network
          -> host NIC / stack -> host userspace receiver
```

### The Linux acceptance suite (kept as written)

- **Test A, Linux → onn, idle:**
  - 5-ms interval, ~1000-B datagrams, at least 20 s / 4000 packets;
  - sequence numbers and actual sender timestamps;
  - Android kernel receive timestamps;
  - dedupe by sequence for the intervals, and report duplicates separately.

  Record:
  - sender and kernel-receive interval p50 / p95 / p99 / max;
  - intervals < 2 ms and ≥ 20 ms;
  - loss, duplicates and reordering;
  - clean 4-6-ms sender intervals turned into < 2-ms or ≥ 20-ms arrivals.
- **Test B, onn → Linux, idle:** the reverse probe's semantics. Android's nonblocking send completion is the sender
  boundary. Timestamp Linux ingress and userspace receive separately. Report unique packets and duplicates
  independently.
- **Test C:** repeat A and B under native-stream load. **Not recorded as run.**
- **Test D:** the production audio path against the synthetic probe, before any queue or buffer policy change. **Not
  recorded as run.**

D6-R1 ran A and B's forward and reverse probes idle (above).

## Acceptance guidance

There is no product requirement that every packet arrive exactly every 5 ms over Wi-Fi. Some jitter is expected. What should trigger renewed root-cause investigation is behavior resembling the prototype pathology:

- large systematic transformation of clean sender intervals into sub-2 ms bursts and >=20 ms gaps;
- very high duplicate UDP delivery rates;
- long arrival stalls on an otherwise idle local network;
- divergence already visible at a kernel/NIC boundary before the application receiver.

Do not make the 2026 Windows prototype's measured duplicate/jitter rates into hard universal thresholds. Establish Linux baseline data first.

## Privacy when saving diagnostics

Sanitized summaries should avoid storing or committing:

- IP addresses;
- MAC addresses;
- Wi-Fi identifiers;
- device GUIDs;
- payload/media contents;
- local usernames or absolute private paths where unnecessary.

Raw captures belong under ignored diagnostic/log directories and should not be committed by default.

The keeper (§1), `diag_read` / `diag_check` (§2-§3) and the support bundle (§4) redact addresses before they write or
print. Their outputs still go under `~/privyhub_diag/` or `logs/`, outside git, except `diag_read`'s report, which is
written into `docs/memory/evidence/reads/` to be kept.
