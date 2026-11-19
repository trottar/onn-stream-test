---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-S1 MET (2026-11-19). The CONFIRMED APK unchanged on the Galaxy Tab S6 Lite (SM-P610). Written by DOCS-G6 (docs only) from Cowork's notes, every value re-read from the raw logs. Nothing adopted.
---

# G6-S1 — the tablet's first install (2026-11-19)

The first step of the tablet handheld track (`docs/ROADMAP.md` §G6; the plan is
`../architecture/G6_HANDHELD_PLAN_2026-11-19.md`). The user's brief calls it T1; it is recorded as **G6-S1**
(`T1`–`T3` are D-BASE findings). The brief is `../handoffs/G6_TABLET_PROJECT_HANDOFF_2026-11-19.md`.

**Labels.** "Verified" = read in the hub's logs or the source. "The user" = the user's own words; nothing perceptual
is a cell. Times are UTC.

## Sources

| What | Where |
|---|---|
| Cowork's notes (verbatim copy) | `g6_s1_2026-11-19/G6_TABLET_PLAN_2026-11-19_cowork_notes.md` |
| `logs/session_audit.jsonl`, 03:52Z–04:28Z (10 rows, device ids cut to 4 hex, `token_ref` removed) | `g6_s1_2026-11-19/session_audit_0352_0428Z_redacted.jsonl` |
| `logs/games/native_stream_recovery.log`, sessions 8, 9, 10 (17 rows) | `g6_s1_2026-11-19/native_stream_recovery_sessions_8_10.jsonl` |
| The three decoder reports' summary fields, each with its raw file's bytes and sha256 | `g6_s1_2026-11-19/decoder_report_summaries.json` |
| The manifest | `g6_s1_2026-11-19/MANIFEST.sha256` |

## 1. The install

- **The APK:** `ca53df0d…` (CONFIRMED, HOME-12V; `PrivyHub/app/build/home12v_installed/app-debug.apk`), unchanged.
- **Sideloaded** as a file on the tablet. **No adb anywhere:** the tablet was never connected to the hub's adb
  (why: the plan's conflict rules).
- The manifest's `android.software.leanback required="true"` did not stop the sideload (the user: it installed).
- Identity v2 was off at first (the legacy LAN path), as a fresh install starts.
- **Network:** the home 5 GHz network, not the travel router's.

## 2. What worked (the user)

"Everything works so far": install, launch, the connection to the companion, the catalog, touch navigation, and a
movie (VOD) played.

## 3. The two refused game tries (verified)

Two T88 tries, both on the unpaired legacy LAN path.

| | Try 1 (session 8) | Try 2 (session 9) |
|---|---|---|
| audit `legacy_setup`, `/plugins/games/launch` | 03:52:15Z | 04:09:52Z |
| audit `legacy_setup`, `/plugins/games/native-stream-start` | 03:52:18Z | 04:09:54Z |
| recovery `launch_ports` / `remote_config` (class `lan`) | 03:52:17.5Z / 03:52:18.1Z | 04:09:54.0Z / 04:09:54.6Z |
| `session_started` | **none** | **none** |
| `session_end_bye` `client_frame` | **0** (03:52:42.0Z) | **0** (04:10:13.6Z) |
| decoder report | `…_035242_129.json` | `…_041013_681.json` |
| `duration_ms` | 23950 | 19015 |
| video packets / frames | 0 / 0 | 0 / 0 |
| `first_clean_idr_ms` | −1 | −1 |
| audio codec | `none` | `none` |
| controller `packets_sent` / `send_errors` | 8928 / 0 | 6924 / 0 |

Both reports carry `host_metadata_complete: false` and the same `host_metadata_error`:

> audio codec opus is required by this host (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup

**Why (verified against `docs/REMOTE_TRUST.md` §9):** adopted line 8 (G-A2, `PRIVYHUB_AUDIO_CODEC=opus`) fails
closed for a client that did not declare Opus, and a client with `identity_v2` off runs no `/session/setup`, so it
never declares it. The refusal is the host's rule working, **not a fault in the APK; no code fix.** The controller
uplink reached the hub (6924 and 8928 packets, no send errors), so the tablet ↔ hub path itself works.

## 4. The pairing (verified)

| Time | Audit event | Device |
|---|---|---|
| 04:26:05Z | `pairing_open`, `window_s` 120 | (hub) |
| 04:26:33Z | `pairing_ok` | `dev-c320…` |
| 04:27:08Z | `pairing_refused`, `pairing-closed` | — |
| 04:27:15Z | `pairing_open`, `window_s` 120 | (hub) |
| 04:27:32Z | `pairing_ok` | `dev-954a…` |
| 04:27:43Z | `token_issued`, `audio_codecs: opus`, `sig_v` 3, `overlay_declared: true` | `dev-954a…` |

Two windows, two `pairing_ok`. Then "Use paired identity (identity v2)" on the tablet; the token was issued with Opus
declared. Both pairings carry `games,tv,vod,diagnostics`.

## 5. Session 10: the game stream (verified)

T88, the paired tablet. No onn session ran in the window: sessions 8–10 are the tablet's (the onn's tokens were
issued 2026-11-18T20:46:24Z and 2026-11-19T05:30:17Z, none between).

**Recovery log:** `launch_ports` 04:27:49.9Z (ps1, RetroArch); `remote_config` class `lan` 04:27:50.6Z;
`session_started` 04:27:54.6Z; `link_notice_shown` 04:28:01.6Z; `session_end_bye` 04:28:18.1Z (`client_frame` 1635);
`session_ended` 04:28:18.2Z. About 23.5 s PLAYING (the user: "it just ran fine"); not the 3-min hold.

**Decoder report `native_decoder_20261119_042818_218.json`** (`duration_ms` 27546, profiler 0.12.3):

| Field | Value |
|---|---|
| decoder | `OMX.Exynos.avc.dec`, `hardware_accelerated` true, `low_latency_enabled` true |
| video frames | 1641 (`decoder.queued_frames` 1641, `rendered_frames` 1634) |
| `recent_fps` | 59.4 |
| `video.lost_packets` / `video.dropped_frames` | 0 / 0 |
| `decoder.dropped_frames` | **6** (all `queue_overflow_drops`) |
| FEC | 8+1 (`fec_group_size` 8, 3354 groups, 3354 parity packets), `fec_recovered_packets` 1, `fec_unrecoverable_groups` 0 |
| encoder | 7000 kbps, GOP 15; `idr_frames` 110, `max_frames_between_idr` 14 |
| first clean IDR | 370 ms |
| first video output | 401 ms (`audio.first_video_output_elapsed_ms`) |
| receive → decode | 23 ms latest, 55 ms max (`decoder.latest_rx_to_decode_ms` / `max_rx_to_decode_ms`) |
| largest output gap | 136 ms |
| audio | Opus (`c2.android.opus.decoder`), 2670 packets, 0 lost, 0 underruns, 14 concealed; first write 1152 ms |
| controller | `packets_sent` 10624, 0 send errors |

**The link notice:** one `link_notice_shown`, reason `rssi_weak`: 5180 MHz, −73 dBm, tx 65 Mb/s (heartbeat 6).

## 6. Verdict

**G6-S1: MET** (the user's step T1): the CONFIRMED APK unchanged installs, launches, shows the catalog, takes touch,
connects, and, once paired, streams T88 on the tablet's hardware AVC decoder. The 3-min hold, the fuller 720p60
numbers and the battery move to G6-S3 / G6-S5.

**Settled by this record** (`../MEMORY.md`): since G-A2 an unpaired legacy-LAN client can browse and play VOD but
cannot start a game stream; a new client is paired first.

## 7. Open

- **The stale first tablet pairing `dev-c320…`** is in the hub's paired-device store beside the onn and the tablet
  (`dev-954a…`): three devices. Its removal is a hub change that **waits for the user's word**. No hub check counts the
  paired devices (`e3_state.py`, `e1_suite.py`, `c3_l4_nft_night.py`, per Cowork's notes).

## 8. Numbers re-read that differ from the notes

- The notes' "0 dropped" is `video.dropped_frames`. The decoder dropped **6** frames (`decoder.dropped_frames`, all
  `queue_overflow_drops`): 1641 queued, 1634 rendered. Recorded here; no verdict changes.
- The notes give the controller uplink as 6924 packets (try 2). Try 1's report reads 8928. Both are recorded.
- Every other value in the notes matched the raw files.

Outside this record: the audit shows `dev-954a…` again at 06:30:16Z and the recovery log a session 11 (ps2) at
06:30Z. They are not read here.
