---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: f52ce75b
---

# G6-HM2 — the touch pad's bench logic and its JVM tests (client source, no APK)

**Result:** `evidence/G6_HM2_TOUCH_PAD_LOGIC_2026-11-19.md`. Design (hashed before this code):
`evidence/g6_hm1_2026-11-19/design_written_before_code.md` (`c38dbd82…`) with `user_answers_2026-11-19.md`.

- **New files (pure Kotlin):** `PrivyHub/app/src/main/java/streaming/HandheldInput.kt` (`HandheldInput`,
  `HandheldGeometry`, `TouchPadDevice`), `TouchPadState.kt`, `TouchPlayerRules.kt` (`TouchP1Rule`, `TouchTakeover`);
  tests `PrivyHub/app/src/test/java/streaming/G6TouchPadStateTest.kt`, `G6TouchSlotsTest.kt`, `G6SenderWriteTest.kt`.
- **Changed, additions only (0 lines deleted):** `NativeControllerSender.kt` +27 (`writePlayerState`),
  `PlayerPrompt.kt` +39 (`joinAsP1WithoutHold`, `takeOverP1`).
- **Not changed (sha256 equal):** `NativeStreamActivity.kt`, `PadSlots.kt`, `PointerGuard.kt`, `AndroidManifest.xml`,
  `MainActivity.kt`.
- **Switch:** none needed. No existing path calls any of the new code; the handheld activity that will call it is
  G6-HM3. The onn's behaviour is unchanged by construction.
- **Rollback:** `git apply -R docs/memory/evidence/g6_hm2_2026-11-19/g6_hm2.diff` (checked with `--check`).
