---
memory_schema: 1
as_of: 2026-09-15
---

# Linux wireless-ADB recovery probe parity

Classification: **DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**

## Trigger

During Phase D4 setup, the Linux companion itself was verified healthy:
process running, TCP 8765 listening, TCP 8000 listening, localhost `/status`
passing, and no active nftables/firewalld/ufw service. The onn nevertheless
reported the companion unavailable.

The existing privacy-safe `tools/probe_adb_wireless_recovery.py` then measured:

- ADB binary available from PATH;
- ADB 1.0.41;
- zero online/offline/unauthorized transports;
- zero `_adb-tls-connect._tcp` services;
- classification `ADB_TLS_CONNECT_SERVICE_NOT_DISCOVERED`.

This reproduces the already-known state where Wireless-debugging pairing may
remain intact while the onn disappears from both `adb devices` and ADB mDNS.

## Gap found

The v2 probe only audited discovery state. It did **not** execute the accepted
D-053 recovery sequence implemented by `tools/build_install_onn.ps1`, especially
its private cached-target recovery. That made the Linux diagnostic materially
less capable than the installer it was meant to audit.

D-053 remains authoritative:

1. private cached target;
2. already-online physical transport;
3. mDNS TLS-connect discovery;
4. reconnect offline transports;
5. one ADB-server restart plus bounded retry;
6. only then user Wireless-debugging Off/On, preserving pairing.

## Patch scope

`probe_adb_wireless_recovery.py` v3 is made host-neutral and aligned with D-053.
It adds the same bounded automatic recovery sequence and a Linux-private target
cache under XDG user state (or `~/.local/state` fallback). The cache may contain
a network-bearing target and therefore remains outside Git/shareable logs.

The probe continues to redact network endpoints, device serials, and mDNS
instance names from its report. It records only counts, safe recovery-stage
labels, and the non-sensitive recovery source classification.

No companion, media, game, transport, Android application, bitrate, FEC, or
router behavior is changed.

## Validation before delivery

Performed off-device:

- Python compilation of the replacement probe;
- probe `--self-test`;
- installer fixture validation against the exact predecessor Git blob;
- wrong-state rejection test;
- idempotent reinstall test;
- forced post-write rollback test;
- `git diff --check` fixture validation;
- ZIP integrity validation.

Runtime ADB recovery is **not yet validated** on the authoritative Linux host.
