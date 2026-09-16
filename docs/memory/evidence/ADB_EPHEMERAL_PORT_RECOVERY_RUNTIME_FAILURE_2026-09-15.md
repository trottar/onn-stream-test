---
memory_schema: 1
as_of: 2026-09-15
---

# Linux wireless-ADB ephemeral-port recovery runtime correction

## Status

**V4 DEVELOPMENT PROBE FAILED AT RUNTIME / V5 DEVELOPMENT PATCH PENDING**

## Authoritative runtime evidence

The v4 ephemeral-port recovery probe did not recover the paired onn automatically.
The user then issued a local `adb connect <private-host>:<current-port>` command
without sharing the network address. That command connected immediately.

This establishes:

- the existing Linux/onn ADB pairing remained valid;
- the onn host was reachable;
- the current wireless-ADB TCP endpoint was valid;
- the v4 failure was in PrivyHub endpoint bootstrap/discovery, not pairing or
  basic reachability.

After the manual connection, the onn reported no value for
`service.adb.tls.port`. Its kernel local ephemeral range was measured as
`32768-60999`. That range is representative-device runtime evidence only, not a
universal Android constant.

## V4 correction

V4 assumed a Linux private host cache already existed and otherwise had no safe
bootstrap source before attempting its single-host port refresh. It also scanned
a much broader TCP range than needed. Mark the v4 port-refresh implementation as
unsuccessful at runtime and do not promote it into `build_install_onn.ps1`.

## V5 development behavior

The follow-up diagnostic keeps production code unchanged and narrows recovery:

1. if ADB is already online, cache the successful endpoint host privately;
2. query `/proc/sys/net/ipv4/ip_local_port_range` from the connected onn and
   cache that range privately;
3. after a future stale endpoint, scan only the cached/measured ephemeral range
   on the one privately known onn host;
4. validate a candidate only through the existing paired ADB connection plus
   `get-state`;
5. refresh the private endpoint/host/range caches on success;
6. if automatic recovery still fails, prompt the local operator to repair/re-pair
   the Linux host and retry recovery once;
7. never emit the host, endpoint, pairing code, serial, or mDNS instance into
   shareable logs or durable memory.

The probe does not perform pairing itself and does not ask the user to paste a
network address into chat or a shareable diagnostic.
