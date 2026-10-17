---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G8-S3 (session A): the rate-cap cells of G8-S1 re-run live with G8-S2's start rung, on the LAN through the shim at `@post-fec` — the question G8-S1 §5 left open: can the client reach PLAYING, and does the ladder then settle under a cap, when the stream starts at the floor instead of 7000. Three cells, detached driver, ~45 min; Code launches, confirms the first cell, exits; the record is a later one-line task. Measurement only; nothing adopted; nothing committed
---

# G8-S3 — the cap cells with the start rung

Read first: `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §5 (the cap cells: starts at 8.25 Mbit/s, tail drop 27 / 45 %, 9–27 frames rendered, no PLAYING in 12 attempts) and §2c (the shim's counters), `G8_S2_START_RUNG_2026-10-17.md` (the flag; **the floor on the LAN is 5000** — 4000 exists only on a remote path with G5-S3, so 4000 cannot be started on the LAN; the in-process numbers: 5000 enters at ~6.1 Mbit/s, ~2 % drop under cap-6000, ~29 % under cap-4500), `G8_S1_LAUNCH_2026-10-16.md` and `g8_s1_driver.py` (the detached driver: copy its scaffolding again).

**What this can and cannot test on the LAN:** the start at 5000 under cap-6000 (the ~2 % case) — yes; the start at 4000 under cap-4500 — no, not on the LAN (that is G4-S2's, off-site, with `=cap`). `cap-4500` at 5000 is run once as the prediction check (expected `no_play`, ~29 % drop). B's record proposed "`=cap` under cap-4500" on the LAN — that would fall back to the floor 5000 because `path_class` is `lan`; it is not run.

## 1. Pre-registration (hashed before the first run)

- **Cells, in order** (each one E1-PS1-STREAM, `--e2`, `--window 600`, E2's warm-up, a 120-s gap; `e3_flag.conf` per cell, read back under load, removed at teardown with `flags_absent` true):
  1. `cap-6000@post-fec,seed=1`, `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_WAN_TELEMETRY=1` — rules off;
  2. the same with `PRIVYHUB_WAN_ADAPTATION=1` — rules on;
  3. `cap-4500@post-fec,seed=1`, `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_WAN_TELEMETRY=1` — rules off (the prediction check).
- **Validity:** as G8-S1 (the shim's profile applied by the count tolerances; `flags_absent` after). **PLAYING is the measured outcome, not a validity condition:** a cell that never reaches PLAYING is `no_play` and recorded with the same reading G8-S1 §5 used (the attempts, the client's last state, the shim's counters); not repeated beyond the suite's own attempts.
- **Written beforehand, from G8-S2's in-process table:** cells 1–2: the start enters at ~6.1 Mbit/s, ~2 % tail drop; whether the client reaches PLAYING at that drop is unknown — that is the measurement. Cell 3: ~29 % drop, `no_play` expected. If cells 1–2 reach PLAYING: the ladder's climb (first step at report 90, ~9 min to 7000 from 5000 on a clean link) will push the stream above the cap again — report what the ladder does then (its own capacity trigger; the rules in cell 2), the rung path, and whether the stream stays up for the window. That is the first measurement of "settling under a cap".
- **Gates (host):** RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, `flags_absent` after. **Everything link-side reported:** PLAYING reached (attempt, s), the start rung and its source from the first decisions row, the rung path, every acted transition with its reason, the rules' suggestions by rule id, post-FEC loss/min, FEC recovered / unrecoverable, rendered, stale, resyncs, the `wan` class and windows, the shim's counters (in / out / dropped_queue / queue_max), the client's pauses.
- **Comparisons:** each cell against its G8-S1 counterpart (cells 17, 18, 19: the same profile at a 7000 start); cell 1 vs cell 2 (rules off vs on), stated not judged.

## 2. The driver and Code's steps

- `g8_s3_2026-10-17/g8_s3_driver.py` from `g8_s1_driver.py`'s scaffolding (the cells table, the flag lines per cell, `no_play` as an outcome; the status file `~/privyhub_g8_s3/status.txt`, `history.csv`, `STOP`, the busy skip, cap **2026-10-18T00:00:00Z**); a 2-min `--dry`; the pre-registration hashed; the hashes of `start_rung.py`, `impairment.py`, `wan_adaptation.py`, `adaptive_bitrate_live.py`, `native_stream.py`, the suite and the driver in `tools_at_preregistration_sha256.txt`; launch under `systemd-run --user --unit=privyhub-g8-s3 --collect`; wait for cell 1's status line (≤ 15 min — a `no_play` cell takes ~3 min, a playing one ~14); `systemctl --user status` into the launch record; `evidence/G8_S3_LAUNCH_2026-10-17.md`, `logs/g8_s3_git_status.txt`, the redactor; **exit**. No session B runs tonight.
- The record: a later one-line task ("write G8-S3's record from the driver's files"), with the G8-S1 §5 reading for any `no_play` cell and the rung path for any playing one.

Precondition: seven lines, `--check` ok (adb to the onn), no `e3_flag.conf`, no game, one device paired, no `privyhub-g8-s1` / `-g8-s3` unit, the tree committed (HEAD named). No sudo, no nft, the Opal read-only, adb only to read state, no addresses or identifiers; nothing fetched, nothing deleted; nothing adopted; nothing committed.
