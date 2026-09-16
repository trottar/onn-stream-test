# ADB endpoint debug runtime request — 2026-09-15

## Status

Development diagnostic / runtime evidence pending.

## Authoritative runtime observation

The v5 automatic wireless-ADB recovery diagnostic did not recover the onn.
Manual local `adb connect <private-host>:<current-port>` still connects without
issue, so pairing and basic TCP reachability remain valid. The unresolved defect
is therefore inside PrivyHub's endpoint selection/discovery path.

## Diagnostic change

Add an explicit `--debug-endpoints` mode to
`tools/probe_adb_wireless_recovery.py`. This mode prints literal endpoint data to
the local terminal only:

- cached target value;
- resolved private host and source;
- selected scan range;
- open TCP candidates found on that one host;
- every `adb connect` endpoint attempted;
- connect return code and `get-state` PASS/FAIL for that endpoint.

The normal shareable log remains address/endpoint redacted. Do not copy literal
endpoint-debug output into durable memory or shareable diagnostics.

## Scope

No Android, companion, emulator, streaming, router, or production installer code
changes are part of this diagnostic.
