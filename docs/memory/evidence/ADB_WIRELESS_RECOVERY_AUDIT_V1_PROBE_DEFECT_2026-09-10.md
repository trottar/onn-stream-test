---
memory_schema: 1
as_of: 2026-09-10
---

# ADB wireless recovery audit v1 probe defect

The first wireless-ADB recovery audit installed successfully but its Python probe
failed before producing a diagnostic log:

`RuntimeError: ADB could not be found using the same sources as build_install_onn.ps1`

This did not establish that ADB was absent. Immediately beforehand,
`tools/build_install_onn.ps1` had already found and invoked ADB successfully,
then failed later because no online ONN transport was present.

Root cause in the diagnostic probe: the `sdk.dir` parser used double-escaped
regular expressions, so a normal `PrivyHub/local.properties` line was never
recognized. The corrected v2 probe removes regex from `sdk.dir` parsing and
tests the escaped Windows local.properties form explicitly.

No ADB pairing, project production source, or Android device state was changed
by the failed v1 probe.
