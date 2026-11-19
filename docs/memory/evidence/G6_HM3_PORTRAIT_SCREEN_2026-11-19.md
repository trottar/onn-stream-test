---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-HM3 part 1 DONE (code, build, pre-registration). Candidate APK 1d658a3f… for the tablet only; the tablet run (part 2) waits for the user. The onn keeps ca53df0d…. Nothing adopted.
---

# G6-HM3 — the portrait screen with an inert touch pad (2026-11-19)

The user's "Proceed" after G6-HM2 (`G6_HM2_TOUCH_PAD_LOGIC_2026-11-19.md`). Design (hashed before code):
`g6_hm1_2026-11-19/design_written_before_code.md` with `user_answers_2026-11-19.md`. Patch note:
`../patches/G6_HM3_PORTRAIT_SCREEN.md`.

**Preflight (12:30Z).** No game, gradle or other session running; the last stream ended 06:33Z. **HM1 and HM2 were
still uncommitted.** HM3 builds on that working tree (`git_status_at_start.txt`, `predecessor_sha256.txt`), and
`g6_hm3.diff` is relative to it.

## 1. What was written

| File | What |
|---|---|
| `NativeStreamActivity.kt` (+34, −9) | `open class`; the hooks H1–H9. The 9 replaced lines: the class line, the orientation value (H1), `setContentView(root)` (H2), the touch guard's line (H3), and the five `AndroidPadDevice.connected()` calls (H4, as `connectedPadDevices()`). Plus no-op calls to H5 (after the prompt's start response), H6 (at the gameplay release) and H7 (before the report is returned) |
| `HandheldStreamActivity.kt` (new) | the portrait activity: `HandheldLayout` (the box W × W·9/16 on top from the measured width, the pad region below), `TouchPadView` (draws `TouchPadState`'s layout, feeds it the fingers, releases on cancel / hide / detach, edge-gesture exclusion on API 29+), the status panel (Q1 (c)), the **End** button and Back swallowed (Q5 (c)), the `handheld` report block (H7). **`TOUCH_LIVE = false`:** the pad takes no slot and writes nothing (HM3 is the inert stage); the 5-s rule, the countdown, the takeover and the writes are wired behind it for G6-HM4 |
| `TouchPadState.kt` (+10) | `drawn()` for the view |
| `AndroidManifest.xml` (+6, 0 deleted) | `.streaming.HandheldStreamActivity`, `exported="false"`, `screenOrientation="portrait"`, after today's entry |
| `MainActivity.kt` (+34, −1) | "Handheld game screen (portrait, touch buttons)" in Settings, only with `FEATURE_TOUCHSCREEN`; stored in `privyhub_game_screen` / `mode`, default `tv`. The launch picks `HandheldStreamActivity` only when chosen on a touchscreen device. The one replaced line is the launch's activity class |

**Disclosed changes from the design and the answers:**
- **H5 is added as well as H6.** The answers file said "H6, not H5". But `TouchP1Rule` (G6-HM2) must know which
  starts clear the slots: a game's start and every unpause, not a self-restart. Only the start response tells it.
  H6 alone would also re-arm at a link recovery's release.
- **H4 is named `connectedPadDevices()`,** not `connectedPads()`, to avoid confusion with the sender's
  `connectedPads` property inside the `also` block at the sender's construction.
- **End is a tap.** If accidental presses happen at G6-HM4, a press-and-hold is the obvious change; it is not built.
- **Q1 (c) edge, left for G6-HM4:** after a real P1 releases its slot, the pad shows again but has no slot until the
  next start.

## 2. Build and tests

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL**. 346 / 346 JVM tests pass
  (`tests_jvm.txt`). The two compiler warnings are in existing lines (`MainActivity.kt:10106`,
  `NativeStreamActivity.kt:4229`) (`build_console.txt`).
- **The candidate:** `PrivyHub/app/build/g6_hm3_candidate/app-debug.apk`,
  sha256 `1d658a3fb96a3281816e1900af54c00479bff74d19fa4281281c0e186d9cf64e` (also copied as
  `PrivyHub-handheld-preview-1d658a3f.apk` for sending).
- The previous `build/outputs/apk/debug/app-debug.apk` (`043891e1…`, 2026-10-18) was copied first to
  `PrivyHub/app/build/g6_hm3_preserved_outputs/`.

## 3. The onn is unchanged (design §9; `onn_unchanged_checks.txt`)

1. The manifest's `NativeStreamActivity` element is byte for byte the same (sha256 `4d36c0bb…` before and after); the
   manifest diff deletes nothing.
2. The `NativeStreamActivity.kt` diff deletes 9 lines, each replaced as listed. Every hook's default body is the
   replaced expression (checked line by line by script).
3. `PadSlots.kt` and `PointerGuard.kt` are unchanged.
4. `PlayerPrompt.kt` and `NativeControllerSender.kt` are as G6-HM2 left them.
5. `MainActivity.kt`'s only deleted line is `NativeStreamActivity::class.java` in the launch. It is now the `else`
   of the choice, and the intent and its extras are unchanged.
6. Every existing JVM test passes, and the real `assembleDebug` ran.

The onn's run of this code and its confirmation are **not done**. `ca53df0d…` stays on the onn, and the pins are not
touched.

`git diff --check` is clean; `git apply -R --check g6_hm3.diff` is OK. The redactor is clean on the Kotlin files and
the records.

## 4. Part 2 — the tablet run (pending)

Pre-registered and hashed before the run: `g6_hm3_2026-11-19/preregistration.md`, sha256 `bcbeff14…`
(`preregistration.sha256`, `preregistration_hashed_at.txt`). It has seven cells read from the tablet's decoder report
and the user's steps. The result is added here after the run.
