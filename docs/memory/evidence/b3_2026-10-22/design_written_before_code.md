# B3 design — the client's Wi-Fi link quality in its reports (written before any B3 code edit, hashed; session B, 2026-10-22)

## The client (`PrivyHub/`), behind `debug.privyhub.link_report=1`

**The flag:** an Android system property, CL-B7P's convention (`debug.` so `adb shell setprop` may set it; a reboot
clears it).
- `1` = on; absent / anything else = today.
- It is read once, lazily, by reflection on `android.os.SystemProperties.get`. Any failure = off.
- **Absent = no new key** in either report, and no Wi-Fi read at all.

**New `streaming/LinkReport.kt`**, mostly pure for the JVM tests:
- `LinkReportFlag.parse(value)` / `fromSystem()`.
- `LinkSample(rssiDbm, txMbps, rxMbps, frequencyMhz, wifiStandard)`, each nullable:
  - `LinkSample.of(...)` applies validity: RSSI in −126..−1 (−127 is the API's invalid value), speeds > 0,
    frequency > 0, standard > 0 (0 = unknown);
  - `query()` = `&link_rssi_dbm=…&link_tx_mbps=…&link_rx_mbps=…&link_frequency_mhz=…&link_wifi_standard=…`, the
    valid ones only;
  - `fields()` = the same as name → value pairs, for the JSON object.
- **`LinkSampler(read, clock, minIntervalNs = 1 s)`:** `current()` returns the cached sample and re-reads only when
  it is ≥ 1 s old (synchronized). **At most one Wi-Fi read per second**, whoever asks.
- `readWifi(context)`:
  - `WifiManager.getConnectionInfo()` (`ACCESS_WIFI_STATE`): `rssi`; `txLinkSpeedMbps` / `rxLinkSpeedMbps` (API 29+;
    below 29, `linkSpeed` as tx); `frequency`; `wifiStandard` (API 30+);
  - any exception → null (no keys).
  - **No SSID, BSSID, MAC or IP is read or sent.**

**Where it is read (never the receive path):**
- **The heartbeat:** inside the existing `PrivyHub-Stall-Heartbeat` thread, the URL gains
  `linkSampler?.current()?.query()`.
- **The client-health report:** inside the existing `PrivyHub-Client-Health` thread, the JSON gains a `link` object
  from `fields()`.
- Both threads already exist and post every 2 s. The sampler makes it at most one read a second between them.
- `NativeStreamActivity`: one lazy `linkSampler` field (null unless the flag) and the two one-line additions. The PCM /
  Opus audio paths and their tests are untouched.

**Permissions (stated; recalled from the platform, not verified on the onn here; CL-B8 reads it):**
- `ACCESS_WIFI_STATE` is already in the manifest. It is a normal permission, granted at install, with no prompt.
- `getConnectionInfo()` with it returns RSSI, link speeds, frequency and standard. **Location permission gates only
  the location-sensitive fields (SSID / BSSID)**, which B3 does not use.
- So **no manifest change and no prompt.** A debug build cannot bypass a runtime permission, and none is needed.
- If the onn redacts RSSI anyway (it would read −127), the key is simply absent, and CL-B8 says so.
- The call is deprecated from API 31 (its successor is the `NetworkCapabilities` transport info, which needs
  `ACCESS_NETWORK_STATE`, not declared). B3 keeps the declared permission set and uses the deprecated call. It still
  answers.

## The host, behind `PRIVYHUB_LINK_REPORT=1` (absent = the parsers byte for byte)

1. **`companion/diagnostics/client_feedback.py`:**
   - a module-level flag `_LINK_REPORT` (guarded);
   - in `normalize_client_health`, one guarded statement before the return: a `link` object, when present, is
     normalized by the new `_normalize_link`. That function is tolerant: it never raises (a bad link object never
     rejects the report). It keeps `rssi_dbm` (int −126..−1), `tx_mbps` / `rx_mbps` (int 1..100000),
     `frequency_mhz` (int 1..100000) and `wifi_standard` (int 1..32), and drops anything else.
   - Absent: the `link` key is ignored, exactly as any unknown key is today.
2. **`companion/diagnostics/stream_telemetry.py`:** a module-level flag, and one guarded statement before the snapshot
   is stored. The ladder's telemetry gains
   `link: {rssi, tx_mbps, rx_mbps, frequency_mhz, band, wifi_standard}`, with band `2.4` / `5` / `6` from the
   frequency. **The ladder reads nothing new** (`adaptive_bitrate._sample` is unchanged).
3. **The heartbeat log:**
   - `games/native_stream_heartbeat.py` gains a guarded module-level `LINK_FIELDS`, and one guarded loop in
     `append_native_stream_heartbeat`;
   - `plugins/games.py`'s heartbeat handler gains a guarded import of it, and one guarded loop that parses the five
     `link_*` query keys as ints.
   - Absent: unknown query keys are ignored, as today.

## Proof

- **Flag absent:**
  - the hooked functions' AST with the guarded statements removed equals the predecessors': `normalize_client_health`,
    `StreamTelemetryStore.accept`, `append_native_stream_heartbeat`, the heartbeat handler (B2's file);
  - a normalized report with a `link` object equals one without it;
  - the existing suites green (wan_telemetry's handler byte-for-byte test included).
- **Flag on:** the link object accepted and mapped, a bad link object dropped and the report kept, and the heartbeat
  keys recorded.
- **The client:** a `LinkReportTest` JVM test for the flag table, the validity rules, the query string and the
  sampler's once-a-second limit (fake clock). The existing tests unchanged and green.
- **The APK:** built offline (`./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug`) in the `/tmp`
  copy, only when no `privyhub-*` unit but the companion is active. Pinned in the record. **NOT installed.**
- **CL-B8 (session A), sketched:** install, `setprop debug.privyhub.link_report 1`, the host drop-in
  `PRIVYHUB_LINK_REPORT=1`, one LAN window; read `link.*` in the telemetry and the heartbeat log.
