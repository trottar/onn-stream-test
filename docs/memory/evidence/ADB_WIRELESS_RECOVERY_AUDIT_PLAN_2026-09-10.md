---
memory_schema: 1
as_of: 2026-09-10
---

# Wireless ADB recovery audit plan

Observed failure: Android APK build completed, then `tools/build_install_onn.ps1` failed at `[2/4] Finding physical ONN ADB target` because no online ADB transport was listed.

Historical source at checkpoint `25e9a14` performs a single `adb devices` query and aborts if the online-device list is empty. It does not inspect ADB server mDNS health, enumerate `_adb-tls-connect._tcp`, retry discovery, or reconnect a previously paired wireless target.

The diagnostic probe records only non-sensitive state: exact build-script SHA-256, line-numbered target-selection logic, ADB version, whether `server-status` is supported, mDNS enabled/backend fields when available, mDNS service-type counts, and device status counts. Device serials, mDNS instance names, hostnames, and network endpoints are never written to the log.

Expected next patch, if the audit confirms the hypothesis: bounded ADB-server/mDNS recovery and explicit connection to a discovered paired TLS-connect endpoint used only in memory, with output redacted and no persistent address storage.
