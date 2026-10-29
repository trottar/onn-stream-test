---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 42a2ab6 (B28 / B29 / B30 / B31 uncommitted beside it)
---

# B30 — the trip's log-keeper and the trip check: BUILT, tested on a fake rotating log dir, one read-only smoke run

**Classification: BUILT.**
- **The tools:** `tools/trip_log_keeper.py`, `tools/trip_check.py` (new; nothing existing changed).
- **Tests:** `tests/trip_log_keeper` 12 and `tests/trip_check` 8 green ×3; two mutations of the keeper caught.
- **One `--once` smoke run of the keeper** on the hub into /tmp, read-only; the real redactor left 0.
- **`trip_check.py` not run live:** it reads adb, which this session does not run. A runs it Thursday.
- Nothing launched, nothing adopted, nothing committed.

Design `b30_2026-10-28/design_written_before_code.md`, sha256 `94edd441…14ac`, hashed **03:20:32Z, before any B30
code**.

## 1. `tools/trip_log_keeper.py`

**A launches it Thursday as `privyhub-trip-log`:**

```
python3 tools/trip_log_keeper.py --out docs/memory/evidence/trip_2026-10-30 --cap 2026-11-01T23:59Z
```

- **The window:** from `--start` (default now) to **the cap** (written to `cap_utc.txt` at launch; a different cap
  already there is refused, never overwritten) or **`<out>/STOP`**. It makes a last copy, then
  `status.txt` reads `done (<why>)`.
- **Every 5 min (`--copy-s`), G4-S4's list:**
  - `logs/games/`'s ladder, heartbeat, recovery, control-gap, frame-size, host-sampler, audio and video logs;
  - the hub's `logs/wan_sessions.jsonl` (B28's telemetry), `session_audit.jsonl` (the audit rows) and
    `impairment.jsonl`;
  - every new game log (`*-game_*.log`) from its first byte;
  - the new files in `decoder_sessions/` and `audio_timing/`, once each, after 10 s quiet;
  - the companion's journal.
- **By file and rotation, never overwriting:**
  - each step's new bytes become a **new chunk** `raw/<log>/<NNNNNN>_<UTC><ext>`, created exclusively (`open(…, "x")`);
  - rotation is followed by inode into `stream_log_archive/<log>.1..3`, and a truncation restarts at 0;
  - **concatenating a log's chunks gives its bytes since the launch, redacted.**
- **`manifest.sha256` grows** by one line per kept file.
- **The redactor on everything kept** (secrets read in process, never printed; re-read every copy, so the friend's
  network's endpoints are caught as they appear):
  - the tailnet's name and suffix; every node's name, tailnet address, current address and endpoints;
  - the host's addresses; the paired devices' ids and keys;
  - any IPv4 (not loopback) / IPv6 / MAC / `dev-…` client id / hex run ≥ 32;
  - each replaced by a placeholder (`<tailnet>`, `<node-name>`, `<endpoint>`, `<ipv4>`, …), counted per kind in
    `samples/copies.jsonl`.
- **Every 60 s, into `samples/`:**
  - the overlay (connected, path, peer_ready, mtu, reason; **online peers by count**) through the companion's own
    provider;
  - the session (PLAYING / paused / idle, the system's class, never the title) from the local control API's games
    status;
  - both redacted.
- **It survives a companion restart:** it holds no file open between steps, and every failure is a row.
- **It does nothing else:** no stream, no restart, no adb, no game; nothing deleted.

## 2. `tools/trip_check.py`: six plain lines, no identifiers

```
adopted: 13 lines; host check ok
apk: on the pin 9719ea82…            | apk: pin 9719ea82…, not read (adb off-LAN)
overlay: connected yes, path direct, peers 1
routing: newest token_issued overlay at <UTC>
band: 5 GHz (5180 MHz)               | band: adb off-LAN
log-keeper: <status.txt's line>; unit active
```

- The host check is `e1_suite.preflight()`'s host fields (`manager`, `environ` == `ADOPTED`, every drop-in, no
  e3 / e4 file), with the failing ones named.
- The routing line is the newest `token_issued` in `logs/session_audit.jsonl`.
- A failing reader prints `unknown (<why>)`, and every line passes the keeper's redactor before it prints.
- **The pin it compares is whatever `tools/e1_suite.py` `EXPECT_APK` holds** (today `8b0fbb74…`; `9719ea82…` only if
  CL-B16 confirms it).

## 3. Tests (`tests_trip_tools.txt`, `tests_mutations.txt`, `keeper_smoke.txt`)

- **The keeper, 12** (temp dirs, a fake clock, fake samplers, secrets built from integers):
  - the chunks concatenate to exactly the bytes written since the launch, across a rotation into the archive and a
    truncation;
  - no kept file is ever rewritten; the manifest has one line per kept file, each verifying;
  - a planted tailnet name, endpoint, client id, IPv4, IPv6 and MAC are replaced and counted (loopback and a time
    kept);
  - decoder reports once each, after quiet (the last copy takes a fresh one);
  - a new game log from its first byte;
  - a log moved away then recreated (a restart) is followed, with no error;
  - the cap ends it with a last copy; STOP ends it; a future start waits; another cap is not overwritten;
  - the samples hold no address.
- **The check, 8:** each line from fakes (ok / NOT ok with names, the adb-off forms, the newest `token_issued` with
  the client id never printed, the band forms); six lines redacted on print; every source down → six `unknown` /
  off-LAN lines.
- **Mutations:**
  - one name per log, rewritten: 4 fail;
  - IPv4 kept: 2 fail.
- **The smoke run** (`--once`, the cap 15 min ahead, out `/tmp/b_q28k_scratch/keeper_smoke`):
  - exit 0; one sample (overlay `connected` true, path `no-peer`, the onn not on the overlay at home; session
    idle); the final copy (the journal's 17 B);
  - **the keeper's own redactor with the real secrets over every output file: 0 left.**

## 4. For A (Thursday)

- **The unit:**
  `systemd-run --user --unit privyhub-trip-log --property=WorkingDirectory=/home/privyhub/Projects/onn-stream-test python3 -B tools/trip_log_keeper.py --out docs/memory/evidence/trip_2026-10-30 --cap 2026-11-01T23:59Z`.
  Then `cat docs/memory/evidence/trip_2026-10-30/status.txt`.
- **Stop it early:** `touch docs/memory/evidence/trip_2026-10-30/STOP`.

## 5. Files

- **`b30_2026-10-28/`:** `baseline_head.txt`, `git_status_at_start.txt`, `started_at.txt`; the design + its hash;
  `b30.diff`, `proof_flag_absent.md`, `after_sha256.txt`; `tests_trip_tools.txt`, `tests_mutations.txt`,
  `keeper_smoke.txt`; `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** the two tools; `tests/trip_log_keeper/`, `tests/trip_check/`; `patches/B30_TRIP_LOG_KEEPER.md`;
  `logs/b30_git_status.txt`.
- **Left in /tmp:** `b_q28k_scratch/` (`b30_mut/`, `keeper_smoke/`, `keeper_smoke_check.txt`).
