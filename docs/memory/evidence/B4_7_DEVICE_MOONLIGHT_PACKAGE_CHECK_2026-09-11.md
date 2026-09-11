---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.7 device Moonlight package verification

Classification:
`B4_7_DEVICE_MOONLIGHT_INSTALLED`

Validated:
- ADB available through `PrivyHub/local.properties`;
- physical target resolved privately;
- recovery source `cached-online`;
- no ADB connection attempt was required;
- `com.safeiot.privyhub` present on resolved target;
- `com.limelight` present on resolved target;
- no network address or device identifier was logged.

Conclusion:
remove only `com.limelight`, then verify:
- PrivyHub remains present;
- Moonlight is absent.
