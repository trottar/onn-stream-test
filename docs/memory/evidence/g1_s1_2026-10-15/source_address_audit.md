# G1-S1 — the source-address audit (G3's input; no change made by the audit)

Baseline `3107fb5`. Every line in `companion/` and in the Android client
(`PrivyHub/app/src/`) where a request's source address, or a peer address,
decides something. Line numbers are at the baseline (before G1-S1/G3-S1's
edits).

**Patterns searched** (`grep -rnE`, `*.py` under `companion/`, `*.kt` /
`*.java` under `PrivyHub/app/src/`):

```text
client_address|client_ip|clientIp|remote_addr|getpeername|X-Forwarded|x-forwarded|recvfrom|source\[0\]|peername|REMOTE_ADDR
```

plus, for the client, `native-stream-start|/plugins/games/launch|recovery-resume|InetAddress|getByName|DatagramSocket(`
(what the client sends at setup, and where it receives).

**Complete:** the pattern returns 80 lines in `companion/` (11 files) and 0
in the client; every one is listed below (consecutive pass-through lines
grouped). **Nothing unlisted.**

Categories (G3): **client identity**, **session identity**, **declared
endpoint**, **authorization**, **routing evidence only** (stays: logging and
diagnostics), **not a client source** (loopback / internal peers; stays).

## 1. Where the source enters (the HTTP layer)

| file:line | what it decides | today | G3 category |
| --- | --- | --- | --- |
| `companion/privyhub_service.py:1856` | the access-log line's first field | logging only (journal) | **routing evidence only** — stays; G3-S1 does not touch it (the journal is local; the audit log carries no address) |
| `companion/privyhub_service.py:2258` | passed to `adaptive_bitrate_live.handle_route` as `client_ip` | **authorization**: `inject` is loopback-only (`adaptive_bitrate_live.py:1162`) | **authorization** — a host-local tool permission; stays a loopback check (local is not remote) |
| `companion/privyhub_service.py:2371` | passed to `tv_state.handle_post_json_request` as `client_address` | nothing: discarded (`tv_state.py:817`, `del client_address`) | — (stays) |
| `companion/privyhub_service.py:2377` | passed to `games.handle_post_request` as `client_ip` | **the media target, the controller target and the controller filter, and a loopback permission** (§2) | **declared endpoint** + **authorization** |

`X-Forwarded-*`, `REMOTE_ADDR`, `getpeername`: **0 hits**. No proxy header is
read anywhere.

## 2. The games plugin (`companion/plugins/games.py`)

| file:line | what it decides | G3 category |
| --- | --- | --- |
| `:3272` | `handle_post_request(…, client_ip)` — the source for every games POST | (entry) |
| `:3329` | `launch`: `ensure_game_controller(client_ip)` → the controller's **allowed source** (`native_session_io.py:2533`) | **declared endpoint** (controller return source) |
| `:3405`, `:3426`, `:3447`, `:3468`, `:3489`, `:3510` | `c3-actuator-continuity-cycle`, `c3-fixed-bitrate-6000/5000/5500-cycle`, `c3-recovery-restart`, `c3-validated-bitrate-transition`: **refused unless the source is loopback** | **authorization** (host-local test tools; stays loopback) |
| `:3681` | `recovery-resume` → `_recovery_resume_fresh(client_ip)` → a relaunch with this source | **declared endpoint** |
| `:3699` | `recovery-copy` → `_recovery_copy_and_launch(…, client_ip)` | **declared endpoint** |
| `:3735` | `native-stream-start`: `NativeStreamManager.start(client_ip=…)` → **video, audio and controller targets** | **declared endpoint** (the central one) |
| `:3740` | remembered as `_recovery_start_args["client_ip"]` | **declared endpoint** (session state; must bind to the session, not the source) |
| `:218`, `:232` | D-BASE-R3a full restart reuses the remembered target | **declared endpoint** (follows `:3740`) |
| `:309`, `:314`, `:322`, `:328`, `:369`, `:378` | `_launch_for_recovery`, `_recovery_resume_fresh`, `_recovery_copy_and_launch` pass it to `handle_post_request("launch", …)` | pass-through → `:3329` |

## 3. The stream path (`native_stream.py`, `native_session_io.py`, `native_fec_relay.py`)

| file:line | what it decides | G3 category |
| --- | --- | --- |
| `native_stream.py:481-484` | `ensure_game_controller`: validates, starts the controller for this source | **declared endpoint** |
| `native_stream.py:690-704` | `_validated_ipv4`: IPv4 only, not unspecified / multicast | (validation; stays — a declared endpoint passes it too) |
| `native_stream.py:1258` | `_build_ffmpeg_command(client_ip, …)` — ffmpeg sends to the **loopback FEC relay** (`rtp://` on loopback, `:1297` / `:1419`), not to the client | pass-through |
| `native_stream.py:1597`, `:1713`, `:1778`, `:1796-1801`, `:1822`, `:2182`, `:2190`, `:2301` | `start` → FEC relay start, Linux / Windows start, session I/O start | pass-through → the targets below |
| `native_fec_relay.py:250`, `:288` | `self._client = (client_ip, port)`: **the video target** (every RTP + FEC datagram) | **declared endpoint** (video) |
| `native_fec_relay.py:527` | `recvfrom` on the relay's loopback input; the address is discarded | **not a client source** |
| `native_session_io.py:94`, `:436`, `:439`, `:511`, `:538`, `:865`, `:880`, `:917`, `:1184`, `:1194`, `:1264`, `:1311-1312`, `:1601` | the audio sender's target (`sendto(client_ip, AUDIO_PORT)`; Windows helper `--client-ip`) | **declared endpoint** (audio) |
| `native_session_io.py:1650`, `:2018`, `:2026`, `:2028`, `:2034`, `:2075`, `:2690` | the controller receiver's expected client; restart if it changes | **declared endpoint** (controller return source) |
| `native_session_io.py:2479`, `:2533` | `recvfrom`; **a controller packet from any other source is dropped** (`_rejected_packets`) | **declared endpoint** — today the filter doubles as the controller's only authorization; under G3 the session token authorizes, and the declared source only routes |
| `native_session_io.py:2711`, `:2716`, `:2724`, `:2732`, `:2738` | `ensure_controller` / `start`: pass-through | pass-through |

## 4. Not a client source (stays)

| file:line | what |
| --- | --- |
| `games/emulator_manager.py:5922` (and `:5924` `source[0]`) | the RetroArch command socket's reply: accepted only from RetroArch's loopback command host and port |
| `plugins/tv_state.py:814`, `:817` | the parameter, discarded |
| `adaptive_bitrate_live.py:1145`, `:1162` | the loopback check (§1) |
| `diagnostics/c3_actuator_probe.py:327`, `diagnostics/c3_fixed_bitrate_probe.py:398` | local probes that call the plugin with a loopback client |
| `diagnostics/udp_reverse_transport_probe.py:148` | the UDP probe's receiver; the source is discarded |

## 5. The client (`PrivyHub/app/src/`)

- **What it sends at setup:** `POST /plugins/games/launch?id=…` (`MainActivity.kt:12004`)
  and `POST /plugins/games/native-stream-start?port=<VIDEO_PORT>`
  (`streaming/NativeStreamActivity.kt:719`); `recovery-resume` (`MainActivity.kt:12393`).
  **No device identity, no session identity, no declared address** — only
  the video port. Everything else the host takes from the request's source.
- **Where it receives:** `RtpH264Receiver.kt:573` and
  `NativeAudioReceiver.kt:1002` bind fixed local ports (`DatagramSocket(port)`);
  `NativeControllerSender.kt:579-587` sends to the host from an ephemeral
  port, so the host's controller filter is address-only.
- 0 hits for the address patterns: the client reads no peer address.

## 6. What G3 must move (summary)

1. **The media target** (video via the FEC relay, audio, controller return
   source) — from the source address to a **declared endpoint** bound to
   an authenticated **session** (`games.py:3735`, `:3740`, `:3329`,
   `:3681`, `:3699`).
2. **The controller's authorization** — today the source filter
   (`native_session_io.py:2533`); under G3 the session authorizes, the
   declared source routes.
3. **Client identity** — none exists today: every caller on the network is
   the client. G3 adds it.
4. **Stays:** the loopback-only test tools (authorization of host-local
   callers), the access log (routing evidence), the internal peers.
