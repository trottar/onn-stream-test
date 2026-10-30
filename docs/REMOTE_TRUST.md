# PrivyHub remote trust (G0)

**Status: G0 written 2026-10-15 (G1-S1).** Every statement is either
quoted from `docs/ROADMAP.md` (marked **[ROADMAP §…]**) or marked
**[G1-S1 proposal]**; proposals become rules only when the user accepts
them. The source-address audit this rests on is
`docs/memory/evidence/g1_s1_2026-10-15/source_address_audit.md`.

## 1. The two topologies

**Home** [ROADMAP §G0]: *"The ordinary household router/Wi-Fi is upstream
connectivity, not part of the PrivyHub trust domain."*

```text
Internet / ordinary household upstream
              |
          home Opal
   PrivyHub trust/network domain
      |                   |
future Linux hub      local PrivyHub clients/devices
```

**Remote** [ROADMAP §G0]: *"The travel router owns uplink changes. Portable
clients should remain configured to the travel router's trusted LAN rather
than being reconfigured for each hotel/friend/work network."*

```text
remote uplink → travel GL-iNet-class router (portable trusted client LAN)
  → onn / future handheld → secure overlay → Linux hub on the home Opal domain
```

*"Remote access must never flatten or expose the ordinary household LAN."*
[ROADMAP §G0]

## 2. The threat model [G1-S1 proposal]

| who | trusted for | must never get |
| --- | --- | --- |
| **the visited network** (hotel, friend, work uplink) | nothing | any PrivyHub service: the travel router exposes no PrivyHub port to it (ROADMAP §G2: *"local client/router management remains possible without exposing PrivyHub services to the visited LAN"*) |
| **the household LAN** (the ordinary router's side) | upstream connectivity only | any PrivyHub service on the Opal side; a route into the overlay |
| **an overlay member without a paired PrivyHub identity** (anyone holding the travel router or the overlay key) | transport | application authority — *"Secure overlay membership is transport protection, not sufficient PrivyHub authorization."* [ROADMAP §G3] |
| **a request's source address** (any network) | routing evidence | identity, a media target or a controller target — *"Source/request address is routing evidence, not durable client identity."* [ROADMAP, trust boundary] |
| **a lost handheld / onn** | its paired identity, until revoked | anything after revocation; pairing-admin unless explicitly granted |

## 3. The fail-closed rules

- *"If identity, readiness, save integrity, import integrity, capture
  scope, or permission cannot be established, preserve the data/session
  rather than guessing."* [ROADMAP, Fail closed]
- *"Loss of overlay fails closed for remote PrivyHub access."* [ROADMAP §G2]
- *"Local operation remains authoritative and must continue to function when
  remote connectivity is absent."* [ROADMAP, Phase G]
- [G1-S1 proposal] **Overlay absent → remote access absent, local unchanged.**
  The overlay provider is off by default (`PRIVYHUB_OVERLAY_PROVIDER` absent
  = today); an unknown provider name selects no provider (state `absent`).
- [G1-S1 proposal] **Identity unknown → no session.** **Permission unknown
  → denied.** A presented credential that fails is refused; it never falls
  back to a weaker path.
- [G1-S1 proposal] **The overlay endpoint is opaque.** It is never written to
  a log, a record or a status document; the status shows `present` /
  `absent` and a short hash only.

## 4. The overlay provider boundary (G1)

*"Use a provider boundary instead of hard-coding one overlay product into
the PrivyHub session architecture."* *"Tailscale is the preferred first
implementation candidate, not the permanent architecture contract."*
[ROADMAP §G1] The contract (`companion/overlay/provider.py`) carries the
ROADMAP's list: connected/disconnected, direct vs relayed, reachable
endpoint (opaque), MTU/path constraint, peer/session readiness, and
diagnostics kept inside the provider. Providers: `none` (the default) and
`tailscale` (reads `tailscale status --json` / `netcheck` only if the binary
is installed; never installs, never runs `tailscale up`) [G1-S1].

## 5. The identity model (G3)

*"Phase G must separate: client identity, session identity, reachable
video/audio/controller endpoints, overlay/path state,
authorization/permissions."* *"Do not use source IP as durable client
identity."* [ROADMAP §G3] The host side is built behind
`PRIVYHUB_SESSION_IDENTITY=v2` (absent = today), not adopted; the design is
§1 of `docs/memory/evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md`.
Everything below is a **[G3-S1 proposal]**.

- **Routing evidence, not identity.** Each source is classed `local`
  (the hub), `lan` (the hub's own on-link subnet), `overlay` (the overlay's
  address space) or `unknown`; only the class is ever logged.
- **Client identity.** A device is paired once, on the home LAN, while a
  120-s window the hub opens is live, with a one-time code the hub shows.
  The hub stores its id, name, key and permissions — no address
  (`~/.config/privyhub/paired_devices.json`, 0600, outside git). Removing it
  revokes it.
- **Session identity.** A nonce-bound, signed setup (HMAC-SHA256 with the
  device key) issues an 8-h token; every call carries it. A failed token is
  refused and never falls back.
- **Declared endpoints.** The client declares where it receives media; the
  hub streams there, not to the request's source. The declared host must be
  in the source's routing class (LAN to LAN, overlay to overlay).
- **Authorization.** `games`, `tv`, `vod`, `pairing-admin`; a paired device
  gets the first three. A path whose permission is unknown is denied.
- **Legacy.** Today's client (no identity) is accepted only from the hub's
  LAN while `legacy_unpaired_lan` is on (the transition default), exactly as
  today, and audited; **never over the overlay**. The hub itself is always
  the operator. **Do not put a reverse proxy or `tailscale serve` in front of
  the companion**: it would make overlay requests look local.
- **Audit.** `logs/session_audit.jsonl`: every pairing, setup, token, refusal
  and denial, with the client id, the reason and the routing class — never
  an address, a key or a token.

## 6. The client's part of the identity model (G3-S2)

Built behind the client setting `identity_v2`, **default off = today's
requests, byte for byte**; not installed, not adopted (record:
`docs/memory/evidence/G3_S2_SESSION_IDENTITY_CLIENT_SIDE_2026-10-16.md`).
Every point below is a **[G3-S2 proposal]**.

- **The device secret** is 32 random bytes in app-private storage. It is
  never logged, and it is sent once, in the pairing request on the home LAN:
  the hub verifies HMACs, so it must hold the key. After pairing only HMACs
  travel.
- **Pairing** happens once, by hand: the hub opens a 2-minute window on its
  own loopback, and the user types the code into the client. The client
  keeps the device id and the permissions the hub returns. Only an explicit
  "Re-pair (new key)" replaces the secret.
- **The session:** the client signs the hub's nonce, declares the address it
  receives media on (the local end of its route to the hub) and its ports,
  and carries the token on every control call that needs a permission the
  hub granted. It refreshes the token before expiry.
- **Refusal:** the hub's reason code is shown. A token refusal gets one fresh
  setup and one retry; a refused setup fails closed, with a cooldown rather
  than a retry storm.
- **Without a pairing, or against a hub without the identity layer,** the
  client sends today's requests: the legacy LAN path.
- **Logging:** no client log line carries an address, the secret or a token.

## 7. WAN telemetry and adaptation (G5)

*"Do not hide a bad WAN path with ever-growing buffers."* [ROADMAP §G5]
**[G5-S1 proposal]** The remote path is judged by the same rows as the
home link (D-BASE's loss and stale rows, the live ladder's capacity and
queue / gap triggers), per 10-s window. The overlay's path state (direct /
relayed) and its transitions count as session events, not as identity.
Adaptation follows `docs/WAN_ADAPTATION_RULES.md`: session correctness
first, then latency, capacity, loss, and a slow recovery upward. No
adaptation decision ever changes a session's identity or its declared
endpoints.

## 8. Hardening: the media token and the permission set (G3-S3)

Built behind the same flags (the host's `PRIVYHUB_SESSION_IDENTITY=v2`, the
client's `identity_v2`; absent / off = today), not installed, not adopted
(record: `docs/memory/evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`).
Every point below is a **[G3-S3 proposal]**.

- **The permission set.** `games`, `tv`, `vod`, `diagnostics`,
  `pairing-admin`. A paired device gets the first four. `diagnostics` (the
  user's own device reporting its health: `/status`, `/diagnostics/*`) is
  **on by default** and listed in the pairing record (`permissions_v` 2), so it
  can be revoked by removing it from the record's list (no restart). A record
  paired before G3-S3 has no `permissions_v` and is granted `diagnostics`
  implicitly; to revoke it there, list the permissions without it and add
  `"permissions_v": 2`. TV-sync and EPG need `tv`, the range server `vod`.
- **The signed endpoints.** The setup signs the video port, the audio port
  and, when the client holds one, its overlay interface address
  (`privyhub-session-setup-v2`). The stream-start ports must equal the signed
  ones (`endpoint-port-mismatch`, audited). The hub streams to the declared
  address whose class matches the request's: the overlay address off-site,
  the LAN address at home.
- **The media token.** Issued with every session token, bound to the
  device, expiring and revoked with the session; for a player that cannot
  send headers, as `?media_token=`. It is never logged: the audit records only
  `media_token_used`, and the range server's own log masks its value. The
  client's player sends the header (Media3 can), only to the hub's own media
  endpoint, never to a third-party stream.
- **The range server over the overlay** answers only with the session token
  or the media token; it asks the companion on loopback, which decides and
  audits (refusals each time, the first accepted use of a token once). On the
  LAN without a token it serves as today (legacy). A presented token that
  fails is refused, never falls back. The companion unreachable: refused
  (`identity-unavailable`).
- **Status.** The hub's session status document lists the permission set
  and, per live session, its permissions and whether a media token is live
  (a boolean, never the value).
- **The hub host.** Off-site the client reaches the hub by a name the user
  types ("Hub host", e.g. the hub's tailnet name), overriding the companion
  host while `identity_v2` is on; the client never logs it (a hash if needed).

## 9. The audio codec (G4-W2; adopted G-A2, 2026-10-19)

- **Adopted:** `PRIVYHUB_AUDIO_CODEC=opus` (128 kbit/s, 10-ms frames) through the drop-in
  `~/.config/systemd/user/privyhub-companion.service.d/audio-codec.conf`, the eighth adopted line. The audio is
  then ~326 kbit/s on the wire instead of PCM 2/4's ~3,213 (G4-W1, CL-B5: −2.9 Mbit/s, ~1.3 GB/h).
- **The declaration is signed.** The client declares `audio_codecs: ["opus"]` in `/session/setup` under `sig_v` 3
  (CL-B4), so an on-path party cannot add or strip it without failing the signature. `token_issued` records it.
- **Fails closed.** A client that did not declare Opus (any APK before CL-B4, or a client with `identity_v2` off,
  which runs no setup) is **refused at stream start, with the reason**: "audio codec opus is required by this host
  (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup". Nothing is stopped or spawned
  first (G4-W2 §3). Such a client never gets Opus datagrams that it would drop as silence.
- **Turning Opus off (back to PCM 2/4):**
  1. Delete `audio-codec.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Take `AUDIO_CODEC` out of `tools/e1_suite.py` `ADOPTED`.

  An Opus-capable client then gets PCM, as before.

## 10. The client's link report (adopted G-A3, 2026-10-23)

- **Adopted:** `PRIVYHUB_LINK_REPORT=1` through the drop-in
  `~/.config/systemd/user/privyhub-companion.service.d/link-report.conf`, the **ninth adopted line**.
  - The host records the client's Wi-Fi link fields in each heartbeat row: RSSI, tx / rx link Mbps, frequency,
    Wi-Fi standard (B3).
  - **Diagnostics only:** no stream, recovery or ladder behaviour reads them.
- **What leaves the onn:** five numbers per heartbeat, as extra query keys of the heartbeat it already sends. No SSID,
  BSSID, MAC or address. The client reads `WifiManager.getConnectionInfo()` at most once a second, and no permission was
  added.
- **The client side:**
  - `da09e154…` (B13) sends the fields by default, and `debug.privyhub.link_report=0` turns that off.
  - Earlier APKs send them only with the property set to `1`. A reboot clears the property.
- **Turning it off:**
  1. Delete `link-report.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Take `LINK_REPORT` out of `tools/e1_suite.py` `ADOPTED`.

  The host then ignores the fields. The client may still send them.

## 11. The link-recovery stack (adopted G-A4, 2026-10-24)

- **Adopted:** `PRIVYHUB_LINK_RECOVERY=1` through the drop-in
  `~/.config/systemd/user/privyhub-companion.service.d/link-recovery.conf`, the **tenth adopted line**.
  - One line implies six (B20): `PRIVYHUB_INPUT_HOLD`, `_B6`, `_B8`, `PRIVYHUB_INPUT_HOLD_REWIND`,
    `PRIVYHUB_STALL_SIGNAL`, `PRIVYHUB_STALL_RESUME`, each `=1`. An explicit individual line still wins (`…=0` turns
    one part off).
  - **What it does:** on a real stall the host holds the game's input, saves a state ~0.4 s in, and at the return loads
    it and resumes on the client's ready (CL-B12: 108-349 ms after the return). One save per real stall, none at a
    session's end (the client's bye).
- **What leaves the onn:** the client's stall signal and its ready after a hold (B7 / B16), on the stream it already
  runs. No address or identifier.
- **The client side:** `20e3e339…` (B19) has the stall signal and the restart guard on by default.
  `adb shell setprop debug.privyhub.stall_signal 0` / `adb shell setprop debug.privyhub.restart_guard 0` turn them off.
  A reboot clears the properties.
- **Turning it off (host):**
  1. Delete `link-recovery.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Take `LINK_RECOVERY` out of `tools/e1_suite.py` `ADOPTED` (reverse
     `docs/memory/evidence/g_a4_2026-10-24/g_a4_applied.diff`).

  The host then holds and saves nothing on a stall. The client may still send its signal; no host module acts on it.

## 12. The fast restart (adopted G-A5, 2026-10-26)

- **Adopted:** `PRIVYHUB_RESTART_FAST=1` through the drop-in
  `~/.config/systemd/user/privyhub-companion.service.d/restart-fast.conf`, the **eleventh adopted line**.
  - **What it does (B22):** at a guarded restart (a Home return, `guard_end=1`) the host answers the start at once and
    tears the old stream down on a worker. The client releases at the new stream's first fresh frame. CL-B13: the
    picture back 1.7-2.0 s at three Home returns of four (3.1 s at one), against 6.7-7.5 s without.
  - It acts on no other start.
- **What leaves the onn:** nothing new. The response carries a `restart_fast` key; the client's report carries
  `restart_fast_*` timings. No address or identifier.
- **The client side:** `6bddafc0…` arms its half only on the host's key, inside `restart_guard`
  (`adb shell setprop debug.privyhub.restart_guard 0` turns both off).
- **Turning it off (host):**
  1. Delete `restart-fast.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Take `RESTART_FAST` out of `tools/e1_suite.py` `ADOPTED` (reverse
     `docs/memory/evidence/g_a5_2026-10-26/g_a5_applied.diff`).

  The APK then behaves as CL-B13 cell 2 (the start answered after the old teardown).
- **Not adopted:** `PRIVYHUB_LINK_RECOVERY_WAN` (G-A6, shelved 2026-10-26; built, off).

## 13. The fast restart unlocked (adopted G-A7, 2026-10-27)

- **Adopted:** `PRIVYHUB_RESTART_FAST_UNLOCK=1` through the drop-in
  `~/.config/systemd/user/privyhub-companion.service.d/restart-fast-unlock.conf`, the **twelfth adopted line**.
  - **What it does (B24):** inside the fast restart (§12), at a guarded restart the old audio's stop starts first, the
    relay stops, and the old encoder is SIGTERMed (SIGKILL after 100 ms). The new encoder is checked, and the lock is
    released there: the ready answers. The old audio's stop finishes after it, outside the lock (its capture SIGKILLed
    if still alive at 300 ms), and then the new audio starts. CL-B14: the picture back 1.15-1.86 s at four Home returns,
    against 1.74-3.12 s with §12 alone.
  - It acts only where §12 acts (a guarded start), and only with `PRIVYHUB_RESTART_FAST=1` also set.
- **What leaves the onn:** nothing new. The recovery log carries `restart_fast_unlock_config`,
  `restart_fast_audio_stop` and `restart_fast_audio` (timings and return codes). No address or identifier.
- **The client side:** no change (the APK `fcd924c2…` is the same with or without it).
- **Turning it off (host):**
  1. Delete `restart-fast-unlock.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Take `RESTART_FAST_UNLOCK` out of `tools/e1_suite.py` `ADOPTED` (reverse
     `docs/memory/evidence/g_a7_2026-10-27/g_a7_applied.diff`).

  The host then runs §12's worker (CL-B13 cell 1: the ready waits on the old audio's stop inside the lock).

## 14. The WAN lines on a remote session (adopted G-A9, 2026-10-29)

- **Adopted:** `PRIVYHUB_REMOTE=1` through the drop-in
  `~/.config/systemd/user/privyhub-companion.service.d/remote.conf`, the **thirteenth adopted line** (the user's "Yes",
  2026-10-29, after CL-B16).
  - **What it does (B28):** at each stream start the host reads the session's class from the onn's address (G3's overlay
    test), then the overlay's path. On an overlay address (direct / relayed / unknown) it turns on G4-S4's four:
    - the remote ladder;
    - the start rung `floor` (4000);
    - the remote cap 7000;
    - the WAN telemetry.
  - **On the LAN none of the four acts:** today's code path, 7000 from the start (CL-B16 cell 1, TRIP-PREP's window).
  - **The cost away:** every new session, a Home return too, starts at 4000 and climbs ~3 min a rung, ~12-15 min to
    7000, longer after a link stall (CL-B16 cell 2: 5500 after 13.6 min).
- **What leaves the onn:** nothing new. The host's recovery log carries `remote_umbrella_config` and one `remote_config`
  per session (the class and the four lines in force); on a remote session the ladder rows carry `path_class`,
  `logs/wan_sessions.jsonl` gets rows and `/status` a `wan` object. No address or identifier.
- **The client side:** no change.
- **Turning it off (host):**
  1. Delete `remote.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion` (outside 04:30-05:30Z while
     `privyhub-link-n1` runs).
  3. Take `REMOTE` out of `tools/e1_suite.py` `ADOPTED` (reverse
     `docs/memory/evidence/trip_prep_2026-10-29/g_a9_applied.diff`).

  Remote sessions then start at 7000 with no remote ladder, as on the twelve lines.
- **The loss guard for the trip:** out. The onn runs CL-B14's `fcd924c2…`, which has no guard default. The guard's
  return after the trip is a B item (CL-B16 S1: its holds still draw stall pauses).
