---
memory_schema: 1
as_of: 2026-09-10
---

# Wireless ADB recovery runtime validation

Classification: **RUNTIME VALIDATED**

The post-patch ADB recovery audit returned `ADB_TARGET_ALREADY_ONLINE`.

Measured post-patch state:
- patched `tools/build_install_onn.ps1` SHA-256:
  `646d7c62b7d2972d1cbb3db88f6c25fcf3588ef36ff2e253dd662a03e50e6e5d`;
- old immediate no-online-device failure path absent;
- ADB mDNS recovery path present;
- ADB reconnect path present;
- ADB binary resolved from `PrivyHub/local.properties`;
- ADB 1.0.41 / server 37.0.1;
- `mdns_enabled=true`, backend `LIBADBMDNS`;
- one TLS-connect service discovered;
- one online device transport;
- zero offline transports;
- zero unauthorized transports.

Conclusion: the persistent build/install recovery patch successfully restored the paired
ONN to an online ADB state and the tooling investigation is closed unless the failure
reproduces despite the new cached-target/recovery path.

Next Phase A gate: CTR Multitap On runtime validation.
