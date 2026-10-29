# B28 — design, written before any code (QUEUE_2026-10-28K item 1): `PRIVYHUB_REMOTE=1`

## Settled first: each of the four lines on a LAN session today (the code, G4-S4's rows)

1. **`PRIVYHUB_START_RUNG=floor`** (`start_rung.py`, read at import by `native_stream` and `adaptive_bitrate_live`).
   - At each start, `choose(target)` picks the active list: the remote list (4000-7000) only when the ladder line is
     on and the target passes G3's overlay test; **otherwise the LAN list (5000, 5500, 6000, 7000)**.
   - `floor` takes the list's lowest rung. **So on a LAN session the four lines start the stream at 5000, not
     7000.** That changes the LAN: the encoder's first argv is the 5000 rung, and the first sample row carries
     `start_rung`.
   - G4-S4 never showed it: every session under the four was over the overlay (5 / 5 `start_rung` floor 4000,
     remote). The LAN sessions it calls "7000" ran without the lines.
2. **`PRIVYHUB_REMOTE_LADDER=1`** (`remote_ladder.py`; read by `adaptive_bitrate_live` and the actuator probe).
   - On a LAN class the ladder is `base` (no 4000) and the actuator adds nothing, so the moves are today's.
   - **But every ladder row gains `path_class`, and the context gains `path_class`** (`annotate` / `apply`). The
     rows are not byte-identical.
   - The class is set after the start (`note_stream_start`, `games.py`), from the overlay test only.
3. **`PRIVYHUB_REMOTE_RUNG_CAP=7000`** (`remote_cap.py`). On a LAN class `applies()` is false, so there is no clamp
   and no move.
   - **It writes one `remote_cap_config` row at the controller's start** (once per process: G4-S4 has it at both
     relaunches).
   - At 7000 (the top rung) it never clamps on a remote path either: G4-S4 shows 0 clamps.
4. **`PRIVYHUB_WAN_TELEMETRY=1`** (`wan_telemetry.py`, built at import by `privyhub_service`).
   - It observes every client report (classification only, it never acts) and writes one `logs/wan_sessions.jsonl`
     row per session.
   - It adds `wan` to `/status` while a stream reports, and `"wan": …` (null when stale) to
     `/diagnostics/stream-telemetry`.
   - **On a LAN session that is extra rows and fields; nothing acts.** The cost is a small per-report CPU cost, a
     file append per session, and one `tailscale status` read per overlay status call (cached 10 s).

So the four as written are **not** LAN-neutral: START_RUNG moves the LAN start to 5000, and the other three add rows
and fields.

## The design

**`PRIVYHUB_REMOTE=1`** (`== "1"`; anything else = absent) implies exactly the four, each **acting only when the
session's class is remote.** A LAN-class session runs byte for byte as today.

- **Imported only with the line** (`plugins/games.py`, a guarded import as B23's). Absent = today: nothing imported,
  nothing read.
- **No environment change.** The umbrella does not set the four lines. The modules therefore build nothing at import,
  and today's hooks (`if X is not None:` on module globals, read at each call) stay as they are. That covers the
  start rung in `native_stream` / `restart_fast*`, the ladder / cap / start rung in `adaptive_bitrate_live`, the
  actuator probe, and the service's telemetry.
- **The umbrella's own objects:** `RemoteLadder()`, `RemoteCap("7000", ladder)`, `StartRung("floor")`, and a
  `WanTelemetry` built at the first remote session from the service's `PROJECT_ROOT` / `OVERLAY_STATUS`. The service
  is found as the loaded module that holds `CONTROLLER`, `STREAM_TELEMETRY_STORE`, `PROJECT_ROOT` and
  `WAN_TELEMETRY`; if it is not found, the telemetry is "unavailable" in the row.
- **Per session, at `native-stream-start`, before the start** (beside B23's call), `note_stream_start(client_ip)`:
  - **the class:** `link_recovery_wan`'s overlay test (`_default_is_overlay`; G3's, via G5-S3). Not overlay →
    **`lan`**. Overlay → **remote**, the sub-class from the provider's path (`_default_overlay_path`), read on a
    daemon thread as B23's: `remote-direct` / `remote-relayed` / `remote-unknown` (no-peer, none, unread, or not
    read yet);
  - **remote (any sub-class):** each implied line's object goes into its module global: `REMOTE_LADDER` in
    `adaptive_bitrate_live` and the actuator probe (imported if not yet), `REMOTE_CAP`, and `START_RUNG` in
    `adaptive_bitrate_live` and `native_stream`. The service's `WAN_TELEMETRY` gets the umbrella's instance.
    - The cap's `remote_cap_config` row is written once into the ladder log at the first remote session, as at
      the controller's start under G4-S4.
    - `/status`'s `wan` comes from a wrapper the umbrella installs once at the first remote session. The service
      installs its own only when the line is set at import; the umbrella's adds `wan` only while the global is set
      and fresh.
    - The ladder's own `note_stream_start` (`games.py`, after the start, already guarded on the global) then sets
      its class, as under G4-S4. **These are exactly the four as G4-S4 ran them.**
  - **lan:** each implied line's global is set back to **None** (today's code path, byte for byte).
    - If a remote session left the ladder's policy holding 4000, the policy's ladder is put back to its base (4000
      removed), which is what today's ladder holds.
    - The telemetry's open remote session is closed (its `wan_sessions.jsonl` row written now rather than at the
      next remote report).
- **`remote-unknown` counts as remote for the start rung.** The rung is chosen at the encoder's spawn, before the
  provider's path can be read (`tailscale status` runs on a thread and takes ~0.1-1 s).
  - The overlay address already says the onn is not on the hub's LAN, and the floor (4000) is the safe start on an
    unknown WAN path.
  - The ladder climbs from it by its own rule. In G4-S4 that was one rung every ~3 min 07 s, so a new session spends
    ~12-15 min below 7000.
  - That cost is stated, not changed. Relayed and no-peer get the same four (G4-S4's `path_class` remote covers any
    overlay address).
- **An explicit individual line wins** (present in the environment, any value): that line's module keeps its own
  object (or None) for every class, as today with that line. The umbrella never touches its global, and the row says
  `explicit`. The umbrella's cap uses the ladder in force: the umbrella's, or the explicit one, or none, in which case
  it is inactive with G5-S4's own reason.
- **One `remote_config` row per session** (the recovery log, beside `link_recovery_config`): `class`, the four with
  `in_force` true / false (`implied` or `explicit …`), and `why`. LAN rows are written at the start; remote rows after
  the path read.
- **The config row at the plugin's start:** `remote_umbrella_config` (the four, implied / explicit; the cap's
  config; the telemetry's availability).

## Tests (`tests/remote_umbrella/`, new; a fake path class, fake service, no live process)

1. **The fake class LAN:** every reader as today:
   - the start rung's encoder kwargs `{}` (7000); no `start_rung` on the first sample row;
   - ladder rows without `path_class`; the context without `path_class`; the actuator's levels;
   - no `remote_cap_config` row; telemetry not observed, no `wan_sessions` row, no `wan` in `/status` or
     stream-telemetry;
   - the same reader outputs as a process with no umbrella (the globals None).
2. **Remote** (direct, relayed, unknown):
   - start rung 4000 `floor` with the remote list; ladder rows `path_class` remote, the policy's ladder with 4000;
   - the actuator's `(4000,)`; the cap active at 7000 with its config row once;
   - telemetry observed and `wan` in `/status`; the row's class.
3. **Remote → LAN → remote in one process:** the LAN session is today's (globals None, the policy's ladder base);
   the remote session after it is G4-S4's again.
4. **An explicit line wins:** e.g. `PRIVYHUB_START_RUNG=5000` present → the umbrella leaves the start rung's global
   alone in both classes; `0` / junk on the ladder → no ladder from the umbrella; the cap is then inactive.
5. **Absent / `0` / junk `PRIVYHUB_REMOTE`:** nothing imported (fresh processes).
6. **The replay:**
   - G4-S4's 13 sessions (`copies/…/adaptive_bitrate_shadow.jsonl` and the record's sessions table, all over the
     overlay) through the start-rung and ladder readers at the old (the four explicit) and the new (the umbrella,
     remote class): the same start rung, list and ladder per session;
   - the home LAN sessions (CL-B15's / G-A7's, class lan): the old gives 5000 (§1), the new 7000 = today.
7. Every suite under `tests/` green.

**Proof:** `plugins/games.py`'s AST, with B28's guarded items removed, equals HEAD's. `start_rung`, `remote_ladder`,
`remote_cap`, `wan_telemetry`, `link_recovery_wan`, `adaptive_bitrate_live`, `native_stream` and `privyhub_service`
are byte-identical to HEAD.

**G-A9 PREPARED** in G-A7's applied form: `REMOTE = "PRIVYHUB_REMOTE=1"`, `ADOPTED` to thirteen, `drop_in_remote`, the
wording, `remote.conf`. Nothing applied.
