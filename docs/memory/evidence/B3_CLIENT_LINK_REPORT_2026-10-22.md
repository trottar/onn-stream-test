---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: aa884a3 (B1 / B2 edits in the tree, uncommitted; plugins/games.py's predecessor here is B2's file)
---

# B3 — the client's Wi-Fi link quality in its reports, recorded by the host

**Classification: BUILT behind `debug.privyhub.link_report=1` (client) and `PRIVYHUB_LINK_REPORT=1` (host); flag
absent = today (no new key; the host parsers AST-identical); tests green; the debug APK built offline and pinned,
`e4d02354…7903`, NOT INSTALLED; nothing adopted; nothing committed.**

Queue `handoffs/QUEUE_2026-10-22B.md` item B3, session B. Design `b3_2026-10-22/design_written_before_code.md`, sha256
`0321f7fc…ef50`, hashed **00:57:51Z, before any B3 code edit**.

## 1. The client (`PrivyHub/`)

**The flag:** system property `debug.privyhub.link_report=1` (CL-B7P's convention; a reboot clears it).
- It is read once, lazily, by reflection, on the first report thread that asks. A failure means off.
- **Absent = no Wi-Fi read and no new key in either report.** The PCM / Opus paths and their tests are untouched.

**New `streaming/LinkReport.kt`** (105 lines):
- `LinkReportFlag`.
- `LinkSample.of(rssi, tx, rx, frequency, standard)` keeps only valid values: RSSI −126..−1 (−127 is the API's
  invalid value), speeds > 0, frequency > 0, standard > 0.
- `query()` gives the heartbeat keys: `&link_rssi_dbm=…&link_tx_mbps=…&link_rx_mbps=…&link_frequency_mhz=…`
  `&link_wifi_standard=…`.
- `fields()` gives the JSON object's keys.
- **`LinkSampler`:** at most one Wi-Fi read per second, whoever asks; the last reading in between.
- `readWifi(context)`: `WifiManager.getConnectionInfo()`.
  - `rssi`; `txLinkSpeedMbps` / `rxLinkSpeedMbps` (API 29+; below, `linkSpeed` as tx); `frequency`; `wifiStandard`
    (API 30+).
  - Any exception means no sample.
  - **No SSID, BSSID, MAC or address is read or sent.**

**`NativeStreamActivity.kt`** (+11 / −1):
- one lazy `linkSampler` (null unless the flag);
- in the existing **`PrivyHub-Stall-Heartbeat`** thread, the URL gains `linkSampler?.current()?.query()`;
- in the existing **`PrivyHub-Client-Health`** thread, the JSON gains `link`.

Both threads post every 2 s, and the sampler keeps it to ≤ 1 read / s. **Never on the receive path.**

**Permissions (stated; recalled from the platform, not verified on the onn here):**
- `ACCESS_WIFI_STATE` is already declared. It is a normal permission, granted at install, with **no prompt**.
- `getConnectionInfo()` gives RSSI, link speeds, frequency and standard with it. Location permission gates only
  SSID / BSSID, which B3 does not touch.
- **No manifest change.** A debug build cannot bypass a runtime permission, and none is needed.
- If the onn redacts RSSI anyway (reading −127), the key is absent, and CL-B8 records that.
- The call is deprecated from API 31. Its successor (`NetworkCapabilities` transport info) needs
  `ACCESS_NETWORK_STATE`, which is not declared, so the declared set is kept.

## 2. The host, behind `PRIVYHUB_LINK_REPORT=1`

| where | change (one guarded statement each, plus a guarded flag) | absent |
| --- | --- | --- |
| `diagnostics/client_feedback.py`, `normalize_client_health` | a `link` object → `_normalize_link`: tolerant (never rejects the report); keeps `rssi_dbm` −126..−1, `tx_mbps` / `rx_mbps` / `frequency_mhz` 1..100000, `wifi_standard` 1..32; drops anything else | `link` ignored as any unknown key |
| `diagnostics/stream_telemetry.py`, `accept` | the ladder's telemetry gains `link: {rssi, tx_mbps, rx_mbps, frequency_mhz, band 2.4 / 5 / 6, wifi_standard}` | no `link` |
| `games/native_stream_heartbeat.py` | `LINK_FIELDS` (the five `link_*`), recorded in the heartbeat log row | `None`, nothing recorded |
| `plugins/games.py`, the heartbeat handler | the five `link_*` query keys parsed as ints | ignored as today |

**The ladder reads nothing new:** `adaptive_bitrate._sample` is unchanged, and a test checks it.

## 3. Proof

**Flag absent, host** (`proof_flag_absent.py` → `proof_flag_absent.md`): each function's AST with B3's guarded
statements removed, against the predecessor.

| file | function | |
| --- | --- | --- |
| `client_feedback.py` | `normalize_client_health` | **identical** (new: `_normalize_link`) |
| `stream_telemetry.py` | `accept` | **identical** (new: `_link_telemetry`) |
| `native_stream_heartbeat.py` | `append_native_stream_heartbeat` | **identical** |
| `plugins/games.py` | `handle_post_request` | **identical** |

**`tests/link_report`: 9 OK** (`tests_link_report.txt`). Each case runs in a fresh process with the flag set or
absent:
- **absent:** a report with `link` normalizes identically to one without; there is no `link.*` and no heartbeat
  field;
- **on:** the link object is accepted; a bad one (−127, a string, a bool, 99, an `ssid` key, a list) drops its fields
  and keeps the report; `link.*` is mapped with its band; the heartbeat row is recorded;
- the ladder's `_sample` reads no `link`;
- the guards' shape.

**The regression set, in the copy (B1-B3 in place), all OK** (`tests_regression.txt`):
- impairment 29, input_hold 18, the recovery suite 17;
- overlay 17, session_identity 88, audio_codec 20, encoder_rc 16, wan_adaptation 23, **wan_telemetry 18 (the
  handler's byte-for-byte test)**, remote_ladder 26, remote_cap 16, start_rung 17, lan_loss_rule 21;
- adaptive_bitrate_shadow 21, native_source_contract 7, c5_m1 14;
- adaptive_bitrate_live 126 and **CL-B1's decoder report 4** (their docs fixtures, from the tree read-only), fec_xor8_2
  9.

C3-F1's 1 error is pre-existing.

**The APK** (`build_console.txt`, `tests_apk.txt`, `apk_sha256.txt`):
- `sh ./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug` in `/tmp/b_q22/PrivyHub`. Only the
  companion service was active. **BUILD SUCCESSFUL, 38 s.**
- **78 / 78** unit tests: 72 existing, unchanged, plus the new `LinkReportTest` with 6 (the flag table, the property
  absent on the JVM, validity, the query keys, once a second on a fake clock, a failing read).
- One compiler warning, pre-existing (`onBackPressed`).

| APK | sha256 | bytes | state |
| --- | --- | ---: | --- |
| **B3 candidate** | **`e4d02354df4237629bbdf84623605eb6d059184cb3f1efcbd249c59f82c37903`** | 9,604,874 | built offline, **NOT installed** |
| CONFIRMED on the onn (CL-B7) | `93d29b4a38d224fddbcf261dab72b40f1290f009b7dc506d60eb3104071e1624` | — | — |

The signer is the same as the tree's build output (apksigner; digests compared, not printed), so `adb install -r`
keeps the data and the pairing.

## 4. CL-B8 (session A, later; sketched)

1. Preserve `93d29b4a…` and install `e4d02354…` (`adb install -r`); read it back and check the pairing.
2. Set `adb shell setprop debug.privyhub.link_report 1` and read it back with `getprop`.
3. Add the host drop-in `Environment=PRIVYHUB_LINK_REPORT=1` and restart.
4. Run one LAN PS1 window of 10 min.
5. **Read:** the heartbeat log's `link_*`; `/diagnostics/stream-telemetry`'s `link.*`; whether RSSI is present or
   redacted (absent key = −127); the band.
6. Remove the drop-in and restart. **Absent = the reports as today**, checked by a heartbeat row without `link_*`.

Then the instrumented evening in the user's room, with the link beside the loss.

## 5. Files

**`b3_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ `predecessor_note.txt`),
  `predecessor_sha256.txt`, `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `b3.diff`, `diffstat.txt`;
- `proof_flag_absent.py`, `proof_flag_absent.md`;
- `tests_link_report.txt`, `tests_regression.txt`;
- `build_started_at.txt`, `build_console.txt`, `tests_apk.txt`, `apk_sha256.txt`, `sdk_listing.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:**
- `PrivyHub/app/src/main/java/streaming/LinkReport.kt` (new), `NativeStreamActivity.kt`,
  `PrivyHub/app/src/test/java/streaming/LinkReportTest.kt` (new);
- `companion/diagnostics/client_feedback.py`, `stream_telemetry.py`, `companion/games/native_stream_heartbeat.py`,
  `companion/plugins/games.py`;
- `tests/link_report/test_link_report.py` (new);
- `patches/B3_CLIENT_LINK_REPORT.md`;
- `logs/b3_git_status.txt`.

No stream, no companion restart, **no adb**, no sudo, no nft, the Opal untouched, nothing fetched (gradle
`--offline`), nothing deleted, nothing installed. Nothing of A's touched.
