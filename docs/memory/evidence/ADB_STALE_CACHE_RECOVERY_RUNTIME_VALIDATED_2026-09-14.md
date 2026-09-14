---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 47d3cf54220146c1d727e2a0491111f6d7dea6c9
---

# Stale cached wireless-ADB recovery runtime validation

## Result

**RUNTIME VALIDATED**

The 2026-09-14 build/install attempt exercised the stale cached-target branch
that D-054 had not previously covered.

Observed console result:

- Android build succeeded;
- step `[2/4]` recovered the physical onn using
  `cached-after-server-restart`;
- the physical onn model responded;
- APK installation returned `Success`;
- PrivyHub launch returned `Done.`;
- the earlier terminating `NativeCommandError` did not recur.

No network-bearing target value is reproduced here.

## Post-recovery sanitized audit

The existing privacy-minimized audit reported:

- `ADB_TARGET_ALREADY_ONLINE`;
- mDNS enabled;
- one TLS-connect service;
- one online transport;
- zero offline transports;
- zero unauthorized transports;
- network addresses logged: none;
- device serials/instance names logged: none.

## Diagnostic limitation

The audit also printed false for its old literal-source checks that looked for
direct `adb mdns services` and `adb reconnect` text. Those commands now flow
through `Invoke-AdbRecoveryCommand`; therefore the literal-source booleans are
stale heuristics and not evidence that recovery disappeared.

Raw runtime behavior is authoritative.

## Durable rule

D-053 remains the accepted architecture. Exploratory recovery calls fail soft;
final recovered-device validation, APK install and application launch fail hard.
Private cached target data remains outside the repository and is never copied
into durable memory.
