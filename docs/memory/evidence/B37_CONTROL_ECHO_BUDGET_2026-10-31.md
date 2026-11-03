---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8 (B37 is a read; nothing built, nothing committed)
---

# B37 — where the 125 ms go: the "control echo" is the client-health HTTP POST, not the control loop

**Classification: SETTLED (read) + DESIGNED, not built** (no part of the design is a one-liner).
- **The metric.** `latency.control_round_trip_ms` is the wall time of the client's 2-s health report: an HTTP
  POST over a new TCP connection to the hub's control API, timed around the hub's synchronous telemetry work. It does
  **not** measure the controller packets. They are UDP, one way, and nothing echoes them.
- **Where Friday's p50 127 ms sits** (inference from the LAN baseline, shown below):
  - **~35-40 ms is fixed:** the hub's handler, the per-request thread and the client's own steps. It is the same at
    home.
  - **~85-95 ms is two to three network round trips:** the TCP connect, the request and response, and perhaps a
    Nagle round. That puts the path's RTT at **R ≈ 28-47 ms**.
- **What the player feels.** A press reaches the hub in ~R/2 + the send tick, about **15-25 ms** one way against
  ~2 ms at home. That is about one frame later, not 1/8 s.
- **The p95 ~400 ms is the HTTP POST's tail** (+275-285 ms over its p50 in both off-site records). It is not a
  delay on the UDP presses. Its cause is not settled; three candidates are in §3.
- **Halving the number** is a measurement fix: D1 / D2 below. **Halving what the player feels off-site** is not
  available in software, because ~R of it is the path. D4 lists the few frames software can save.

Read-only throughout: no stream, no restart, no adb, no network probe. The trip keeper's directory was not read. The
rows came from `trip_r2_2026-10-31/copies/` (TRIP-R2's byte copies) and from older evidence dirs.

## 0. The numbers (`b37_2026-10-31/rtt_read.py` → `rtt_read_output.json`, `g4_s4_rtt_from_samples.json`)

| where | sessions / samples | p50 | p95 | source |
| --- | --- | --- | --- | --- |
| **Friday (trip), `remote-direct`, ~350 mi** | 35 sessions | **127** (per-session p50 111-149 in 33 / 35; kart 214; one 404 at a short session) | **~410** (per-session 388-453 in 28 / 35; to 1,107) | `wan_sessions.jsonl` (the `wan` block's `rtt_ms`, per session) |
| **G4-S4, broadband, direct** | 73 samples (60 s) | **58-68** | **331-342** (768 / 804 in the first minute) | `g4_s4_2026-10-24/samples/slow_60s.jsonl` (the running `wan` percentiles) |
| G4-S2 / G4-S3, hotspot | — | 119-138 | 160-780 | WAN-R1 §RTT (quoted, not re-read) |
| **the LAN at home, recent clean cells** (CL-B10 … CL-B16, G-A3 … G-A7, LINK-R1, 2026-10-23 … 29) | 12 records | **45-66** | 87-300 | e1_suite `telemetry.jsonl`, one sample per client report |
| the LAN, every e1_suite record (with shims) | 92,619 reports, 48 records | 46 (min 19; e-series 2026-10-05 … 15: 33-46) | 312 | the same |
| the hub → onn ICMP ping on the LAN | E4-S4C | 4.3-4.7 (median) | p99 274-499 | E4-S4C §2 (a −79 dBm room) |

- **G4-S4 is not Friday's path.** The two records use the same metric, but G4-S4's p50 is half of Friday's. Under
  the budget in §2 that makes G4-S4's path RTT R ≈ 6-15 ms, against Friday's ≈ 28-47 ms. Whatever the map distance,
  the paths are not the same RTT class (inference).
- **No record holds a WAN ICMP or WireGuard ping.** The overlay rows carry only the path (direct / relayed / no-peer),
  the peer count and the MTU (1280). So R on the WAN is estimated by subtraction. It is not measured.
- **The LAN p50 rose from 33-46 ms (2026-10-05 … 15) to 45-66 ms (2026-10-16 onwards).** This is not settled. It
  coincides with more synchronous work in the handler: G5-S1's WAN telemetry, the live ladder's `observe` and the
  link fields (inference).

## 1. What `control_round_trip_ms` is (the code)

**The client** (`PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`):
- **Every 2 s** (`CLIENT_HEALTH_INTERVAL_MS`, `:74`), `maybeSendClientHealth` (`:2786`) builds the
  `privyhub_client_health_v1` JSON. It then starts a thread `PrivyHub-Client-Health`.
- **That thread** takes `postStartedNs` (`:2946`). It then:
  - reads the Wi-Fi link (`linkSampler?.current()`, `:2956`, a `WifiManager.getConnectionInfo()` binder call at most
    once per its interval);
  - POSTs to `http://<hub>:8765/diagnostics/client-health` (`:2961`);
  - sets `clientHealthControlRoundTripMs = now − postStartedNs` (`:2965`).
- **The value goes out in the next report** (`:2857-2861`), 2 s later. So each report carries one snapshot of the
  previous POST.
- **`httpPostJson`** (`:4240-4310`): a new `HttpURLConnection` each time (connect / read timeout 1.5 s). It reads
  `responseCode`, closes the stream, and calls `connection.disconnect()` in `finally`. So **every POST pays a TCP
  connect**.

**The hub** (`companion/privyhub_service.py`):
- **The server:** `ThreadingHTTPServer` with `PrivyHubRequestHandler`. That means a thread per connection;
  `protocol_version` is not set (HTTP/1.0, close after each response); and Nagle stays on (`disable_nagle_algorithm`
  is not set).
- **The handler for `/diagnostics/client-health`** (`:2267-2336`) runs all of this **before** `_send_json(200, …)`:
  - `CLIENT_HEALTH_STORE.accept`;
  - `_native_stream_status()` (the games plugin's `native-stream-status`);
  - `STREAM_TELEMETRY_STORE.accept`;
  - the adaptive-bitrate controller's `observe` (with the live ladder, the call that decides);
  - `WAN_TELEMETRY.observe`.
- **`_send_json`** (`:1932-1970`) writes the headers (`end_headers()`) and then the body in a second write. Nagle is
  on, so the body may wait for the client's ACK of the headers.

**The controller path, for contrast:**
- **`NativeControllerSender.sendLoop`** (`NativeControllerSender.kt:584-700`) sends one 36-byte `PHI1` datagram per
  player each tick, then `Thread.sleep(8)` (~430 packets/s for 4 players). Each packet carries the client's own
  `System.nanoTime()/1000`.
- **The hub's `_receive_loop`** (`companion/native_session_io.py:2519-2600`) does `recvfrom` (50-ms timeout) and
  writes the uinput event in the same thread. There is no batching and no timer on the arrival path.
- **Nothing is sent back.** The stall (`PHS1`) and keyframe (`PHK1`) datagrams ride the same socket, client → hub
  only. The packet's timestamp is never read back.

**So:**
- **The "control echo" measures the diagnostics HTTP round trip.** That is ≥ 2 network RTTs (TCP connect, then
  request → response) plus the hub's handler, the per-request thread and the client's link read.
- **It is neither the control loop nor input → photon.** G8-S1 already found that the echo does not cross the shim's
  video path (G8-S1 §"delay-150").

## 2. The budget

| piece | in the echo? | in input → photon? | size (source; *inference* marked) |
| --- | --- | --- | --- |
| the pad's own report (Bluetooth HID) | no | yes | not in any record |
| the send tick (`sleep(8)`, 4 players) | no | yes | 0-~9 ms, avg ~4.5 (code) |
| uplink, one way (UDP over the overlay) | no | yes | ~R/2: **~14-24 ms Friday** (*inference*), ~2 ms LAN |
| the hub's receive → uinput | no | yes | the same thread as `recvfrom`, no batching; < 1 ms (*inference*) |
| the core's poll + the game's own lag | no | yes | avg ~8 ms to the next frame poll, + 1-3 frames per game (*not measured*) |
| capture (x11grab, 60 fps) + VAAPI encode + FEC | no | yes | *not measured* (≤ 1 frame for capture by construction) |
| downlink, one way | no | yes | ~R/2 |
| the FEC hold | no | when a group is open | per-session max 14.5 ms median, 47 max (Friday, 34 reports) |
| the client's receive → output | no | yes | 93.4 % < 20 ms, 6.0 % 20-40 ms (`rx_to_output_histogram_ms`, Friday); codec 17.5 ms median latest |
| the display (vsync + the TV) | no | yes | *not measured* |
| **TCP connect** (a new connection per POST) | **yes, 1 R** | no | code |
| **the request → the response** | **yes, 1 R** (+ up to 1 R if Nagle holds the body) | no | code |
| **the hub's handler before the reply** | **yes** | no | **not timed by any row** |
| the client's link read + thread inside the timer | yes | no | a binder call, ≤ a few ms (*inference*) |

**The fixed part F.**
- On the LAN, R ≈ 4.4 ms by ICMP. The echo's p50 is 45-66 ms on the recent cells (46 over everything).
- So **F ≈ 33-43 ms**: the handler, the thread and the client's steps, with k = 2-3 RTTs taken off.
- F is the floor that every home session already pays.

**Friday.**
- 127 − F = 84-94 ms = k·R, so **R ≈ 28-47 ms**.
- The player's extra input → photon against home is ≈ R − R_LAN, so **~24-43 ms** (both directions, about 1.5-2.5
  frames).
- The rung changes nothing on latency (*inference*).

**G4-S4:** 62 − F = 19-29 ms, so R ≈ 6-15 ms.

**The p95 tail.** It sits **+275-285 ms over p50 in both off-site records** (G4-S4 337 − 62; Friday 410 − 127). The
recent clean LAN cells run +40-200 ms. The cause is not settled. Candidates:
- **(a) a TCP retransmission** in a short-lived connection on the overlay. Linux's RTO floor is 200 ms, plus R.
- **(b) the onn's Wi-Fi power save.** The B5 lock is a property, and it was empty on the trip; B5 found no lock held
  by default. A DTIM-buffered downlink adds about 100-300 ms.
- **(c) a stalled handler**, from the GIL or a ladder decision on the same thread.
- **(a) and (c) cannot touch the UDP presses.** (b) delays only the downlink, that is the picture.
- **The trip's own rows bound the uplink:** the longest uplink silence in play that was not a teardown was 600 ms
  (TRIP-R2 §2), and controller packets arrived throughout.

**Correction to TRIP-R2 §2's "each press land about 1/8 s later than at home, and sometimes 0.4 s later".**
- The 1/8 s and the 0.4 s are the health POST's numbers.
- A press's one-way delay is ~R/2 + the tick, so **~15-25 ms Friday against ~2-6 ms at home** (*inference*).
- No row measures a press's delay. D3 would.

## 3. The design: what would halve it (not built — none is a one-liner)

- **D1 — a true control echo** (host `PRIVYHUB_CTRL_ECHO=1` + client `debug.privyhub.ctrl_echo=1`; absent = today).
  - **The hub:** in `_receive_loop`, right after the uinput write of every 32nd `PHI1` packet (~13/s), it sends a
    `PHE1` datagram back to the source: the packet's sequence, the client's µs timestamp and the hub's
    receive → send µs.
  - **The client:** it reads it on the sender's socket (a non-blocking receive in the tick) and keeps
    `control_echo_ms = now − client_us`. It reports p50 / p95 per report, beside today's key.
  - **Expected:** ≈ R + ≤ 1 tick, so ~30-50 ms Friday and ~5-10 ms at home. **The number halves or better**, because
    it then measures the right thing.
- **D2 — the health POST itself:**
  - the client starts the timer after the link read;
  - the hub replies before the telemetry work (send 200, then run the stores, the ladder and the telemetry on the
    same thread);
  - a kept-alive connection (HTTP/1.1 on both ends) drops the connect RTT.
  - **Expected:** ~R + a few ms. Today's 127 would read ~40-55.
  - It changes a key that records and the WAN class already use. So it would go behind a flag, and the old key would
    stay.
- **D3 — host only, works on today's APK** (`PRIVYHUB_UPLINK_DELAY=1`):
  - every `PHI1` already carries the client's µs clock;
  - (hub receive µs − client µs) − its running minimum over the session = **each packet's extra one-way uplink delay**.
    The clock offset cancels, and the drift is small over minutes;
  - per-10-s p50 / p95 / max go into the ctrl-gaps log.
  - **This answers "were presses late in flight?"** It separates the uplink from the HTTP tail (a) / (c).
- **D4 — what the player feels:**
  - **The network half is the path.** No software halves R.
  - **Send on the event:** an immediate datagram from `handleKeyEvent` / `handleMotionEvent` when the state changed,
    the tick kept. That saves an average ~4.5 ms, ≤ 9.
  - **RetroArch run-ahead 1 frame** per title where the core is cheap: −16.7 ms of the game's own lag, at a CPU cost.
    Not for the PS1 HW renderer without a measure.
  - **The B5 Wi-Fi lock by default:** if (b) is the tail, the picture's p95.
  - **Measure first:** D3 and an input → photon cell at home (a camera on the TV and a pad LED). Neither exists today.

**Order, if the user wants it:** D3 first (host only, no APK, it answers the question), then D1, then D4's
send-on-event. D2 matters only for the record's comparability.

## 4. The CAPABILITY_MODEL row (for the coordinator; §7 Network, after "the link recovery")

> | **the remote RTT budget** (2026-10-31, B37): the client's `latency.control_round_trip_ms` is **the 2-s health POST's HTTP round trip** (a new TCP connection + request/response + the hub's synchronous telemetry handler), not the control loop; the controller datagrams are one-way UDP with no echo; no host probe | **LAN: p50 45-66 ms, p95 87-300** (the recent clean cells; ICMP hub → onn ~4.4 ms): a fixed **~33-43 ms** is the handler and the stacks. **Off-site direct: p50 58-68 / p95 331-342 (G4-S4), p50 127 (111-149) / p95 ~410 (Friday, 35 sessions)**, so the path's RTT is R ≈ 6-15 / 28-47 ms (by subtraction; **no WAN ping in any record; E5-S2**). A press's one-way delay ≈ R/2 + the 8-ms tick (~15-25 ms Friday). Input → photon not measured; E5-S2 | none acts on it (G5-S1: reported, not classified); D1-D4 designed, not built (B37 §3) |

## 5. Files

- **`b37_2026-10-31/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `rtt_read.py` + `rtt_read_output.json` + `rtt_read_run_at.txt` (read-only, aggregates only);
  - `g4_s4_rtt_from_samples.json`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Nothing in `companion/` `tools/` `tests/` `PrivyHub/`**; no diff; no patch file.
- **Left in /tmp:** `/tmp/b_q31l_b37_scratch/` (`rtt.json`, a first-run copy).
- **The rules held:**
  - no stream, no restart, no adb, no network probe;
  - the trip keeper and `trip_2026-10-30/` untouched (TRIP-R2's copies read);
  - nothing fetched, deleted, adopted or committed;
  - no address or identifier.
