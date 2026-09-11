---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.8 first package-removal result

Classification:
`B4_8_DEVICE_MOONLIGHT_REMOVAL_NOT_CONFIRMED`

Observed device action:
- PrivyHub present before removal: true;
- Moonlight present before removal: true;
- uninstall attempted: true;
- adb uninstall command success: true;
- PrivyHub present after removal: true;
- Moonlight present after removal: false;
- action nevertheless reported `PACKAGE_QUERY_FAILED`.

Diagnosis:
the action used `pm path` for presence checks. On this device, querying a
now-absent package returns a nonzero shell status. The code simultaneously
observed no package path and classified the command status as an error.

The uninstall result itself is therefore promising but not yet accepted as B4
completion. Re-verify with `pm list packages <filter>`, where absent output with
exit zero is a valid absence state. Do not issue another uninstall in the
verification step.
