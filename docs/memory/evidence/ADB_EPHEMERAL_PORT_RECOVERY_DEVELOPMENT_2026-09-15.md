---
memory_schema: 1
as_of: 2026-09-15
---

# Linux wireless-ADB ephemeral-port recovery development evidence

## Status

**DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**

## Fresh evidence

The representative Linux host reproduced wireless-ADB non-discovery even though
Wireless debugging remained enabled and the onn still reported the host as
paired.

Measured results, with no network address copied into durable memory:

- Debian ADB: `1.0.41`, Platform Tools `34.0.5-debian`;
- normal ADB mDNS: zero `_adb-tls-connect._tcp` services;
- forced `libadbmdns` on 34.0.5: zero TLS-connect services;
- temporary Google Platform Tools `37.0.1-15733141`;
- ADB 37.0.1 `mdns_enabled: true`;
- ADB 37.0.1 `mdns_backend: LIBADBMDNS`;
- ADB 37.0.1 still observed zero TLS-connect services.

Therefore upgrading ADB or forcing the current mDNS backend is not sufficient in
this environment.

Windows history is important counter-evidence against treating the 2.4/5 GHz
radio split as a permanent discovery block. The same home Opal split previously
recovered the paired onn through D-053, including the validated
`cached-after-server-restart` branch.

## Architectural correction

ADB Wi-Fi pairing identity and the active connection endpoint are different
lifetimes. Pairing preserves host authorization, while Android's secure wireless
ADB TLS server listens on a randomly selected TCP port and is restarted when
Wireless debugging is restarted. A cached `IP:port` can therefore become stale
while pairing remains valid and the device address remains stable.

The v4 diagnostic extends D-053 without turning an IP address into a user-facing
contract:

1. try the cached endpoint normally;
2. derive/reuse the host address only from private state;
3. if the endpoint is stale, scan TCP ports on that **single privately identified
   host only**;
4. attempt ADB connection only to listening candidates;
5. accept a candidate only after the existing ADB pairing authenticates and
   `get-state` reports `device`;
6. refresh the private endpoint/host cache;
7. never place the host, port, serial, or mDNS instance in the shareable log.

The bounded scan covers TCP 1024-65535 on one identified host, uses short local
connect timeouts, and fails closed if more than 64 listening ports are observed.
It is not a LAN/subnet scanner.

The probe may also consume `PRIVYHUB_ONN_HOST` as a private local bootstrap hook
for future address-discovery integration. Its value is never emitted to the
shareable diagnostic or durable memory.

No production installer, companion, Android app, game, media, controller,
streaming, bitrate/FEC, or router behavior is changed by this development patch.
