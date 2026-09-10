---
memory_schema: 1
as_of: 2026-09-10
---

# Persistent wireless ADB discovery failure

The corrected audit was run while the ONN still listed the PC as a paired
Wireless debugging host. ADB was available through `PrivyHub/local.properties`,
server version was 37.0.1, `mdns_enabled=true`, backend `LIBADBMDNS`, and there
were zero TLS-connect services and zero ADB transports. Restarting only the
PC-side ADB server did not change the result.

Conclusion: pairing is intact but the ONN can temporarily stop being
discoverable. The build/install tool must perform bounded recovery and may
privately cache the last successful target outside the repository. That target
may contain a network endpoint or mDNS instance name and is therefore never
printed or written to shareable logs/durable memory.

## Post-patch validation

After installing the recovery patch and rerunning the build/install workflow,
the audit returned `ADB_TARGET_ALREADY_ONLINE`. The updated build script no
longer uses the old immediate-fail path and now contains mDNS and reconnect
recovery. ADB discovered one TLS-connect service and one online transport, with
zero offline and unauthorized transports.

Status: **COMPLETE / runtime validated**.
