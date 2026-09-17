# D-128 — Guide-style category presentation

**Date:** 2026-09-17

**Type:** Android presentation-only change

**Status:** rev4 development patch / runtime validation pending

Rev1 compile result: `ROLLED BACK` after Kotlin reported conflicting `formatTvGuideTime(Long)` overloads. Rev2 corrected that transform but the delivery command could terminate the interactive shell. Rev3 passed the Android build, then `tools/check_memory_health.py` rejected the generated `CURRENT.md` because two required headings were missing; it rolled back. Rev4 keeps the same predecessor checkpoint, corrected transform, shell-safe delivery procedure, and adds exact CURRENT-heading validation to installer self-test.

## Production file

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`

## Behavior

The existing shared TV row renderer now displays cached current and next
programme time ranges. The existing D-127 incorrect-guide mark still suppresses
trusted guide content.

## Build gate

Installer runs:

`sh ./gradlew :app:assembleDebug --no-daemon`

and restores exact predecessor bytes if validation/build fails.

## Runtime probe

`tools/probes/d128_guide_style_ui_probe.py`

Target:

`D128_GUIDE_STYLE_FAVORITES_RUNTIME_VALIDATED`
