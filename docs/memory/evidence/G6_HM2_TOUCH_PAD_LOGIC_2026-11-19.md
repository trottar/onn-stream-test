---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-HM2 DONE (bench). The touch pad's logic and its JVM tests; 346 / 346 JVM tests pass. No APK built or installed; the onn's code paths unchanged. Nothing adopted.
---

# G6-HM2 — the touch pad's bench logic (2026-11-19)

The user's "Proceed" (2026-11-19) after G6-HM1's design (`g6_hm1_2026-11-19/design_written_before_code.md`, sha256
`c38dbd82…`, hashed before any code) and their answers (`g6_hm1_2026-11-19/user_answers_2026-11-19.md`). Patch note:
`../patches/G6_HM2_TOUCH_PAD_LOGIC.md`. Plan: `../architecture/G6_HANDHELD_PLAN_2026-11-19.md`.

**Preflight (07:16Z).** No game, gradle or other session running. Session B's last step was done at 06:18Z, and
the tree held only G6-HM1's uncommitted docs (`g6_hm2_2026-11-19/git_status_at_start.txt`). Baseline `f52ce75b`.

## 1. What was written

| File | What |
|---|---|
| `streaming/HandheldInput.kt` (new) | `HandheldInput.isTouchscreen` (design §6); `HandheldGeometry.videoBoxHeight` = W·9/16 (§2); `TouchPadDevice : PadDevice`, key `01097c` (§5) |
| `streaming/TouchPadState.kt` (new) | finger ownership, 8-way D-pad by angle with a roll, one finger one button, enlarged hit areas, digital L2 / R2, the PS1 layout in fractions, the sender's fields as output, `stickY` stub for HM5 (§4) |
| `streaming/TouchPlayerRules.kt` (new) | `TouchP1Rule`: D2's 5 s from the gameplay release, again after every unpause, not after a self-restart, a countdown for the pad region (Q3 (b)/(i), Q4 (b)). `TouchTakeover`: a hold begun unjoined and kept 2 s takes P1 from the touch pad only (Q2 (d)) |
| `NativeControllerSender.kt` (+27, 0 deleted) | `writePlayerState(player, buttons, lx, ly, rx, ry, lt, rt)` under the existing lock (§3) |
| `PlayerPrompt.kt` (+39, 0 deleted) | `joinAsP1WithoutHold` (D2; uses the existing `join`) and `takeOverP1` (Q2 (d); only when P1's holder is the given key) |

**One reading disclosed (Q2 (d)).** On a 1-player title a real pad cannot join at 0.5 s, because the join closes
after P1. Its 2-s hold still takes P1 from the touch pad. This is the hold "that joins it, or that could not join",
so the user's rule also works where there is no P2. `onAOnePlayerTitleTheTwoSecondHoldTakesP1` tests it.

**A design detail made concrete.** The design's `joinWithoutHold` (lowest open slot) is written as
`joinAsP1WithoutHold`: P1 or nothing. Q1 (c) settles that the touch pad does not join behind a real P1.

## 2. Tests (`g6_hm2_2026-11-19/tests_jvm.txt`)

`gradlew --offline :app:testDebugUnitTest`, all classes: **346 tests, 0 failures, 0 errors, 0 skipped**. The 34 new
tests:
- `G6TouchPadStateTest`, 15: the design's test list 1–12 and the empty bottom tenth;
- `G6TouchSlotsTest`, 16: §5 and the user's answers;
- `G6SenderWriteTest`, 3: the real send loop over loopback; the PHI1 packet read back; `neutralize` clears; the loop
  never goes silent.

The existing tests pass unchanged, among them `B70PointerTest` 9, `PadSlotsTest` 7, `PlayerPromptTest` 15,
`VirtualRemoteNoSlotTest` 5, `HoldAndSlotsDefaultOnTest` 6 and `SurfaceHoldTest` 8.

`G6TouchSlotsTest.withoutTheTouchPadPresentARealPadWouldTakeP1` shows why hook H4 is needed. Without the touch pad
in the connected list, a real pad's hold takes P1.

## 3. The onn is unchanged (design §9, the checks that apply at HM2)

- sha256 before = after for `NativeStreamActivity.kt`, `PadSlots.kt`, `PointerGuard.kt`, `AndroidManifest.xml` and
  `MainActivity.kt` (`predecessor_sha256.txt`, `after_sha256.txt`).
- `git diff --numstat`: `NativeControllerSender.kt` 27 / 0, `PlayerPrompt.kt` 39 / 0: additions only (`numstat.txt`).
- No existing path calls the new code. It runs only when G6-HM3's handheld activity calls it.
- `git diff --check` is clean, and `git apply -R --check g6_hm2.diff` is OK.
- **Redaction:** clean on every new or changed file. `tools/e3_redact_check.sh` does not read `.kt`, so the Kotlin
  files were also run through its redactor directly. The first diff was flagged for the loopback literal in
  `G6SenderWriteTest`, which now uses `InetAddress.getLoopbackAddress()`. The suite was re-run after that change:
  346 / 346.
- **Not run: `assembleDebug`.** HM2 makes no APK. The test task compiled the main source, and leaving
  `build/outputs/apk/debug/app-debug.apk` untouched (dated 2026-10-18) avoids a new build output that could be
  mistaken for an installable one. The real assemble runs at G6-HM3, where the APK is the deliverable.

## 4. Files (`g6_hm2_2026-11-19/`)

`baseline_head.txt`, `git_status_at_start.txt`, `started_at.txt`, `predecessor_sha256.txt`, `after_sha256.txt`,
`new_files_sha256.txt`, `numstat.txt`, `g6_hm2.diff` (the two changed files and the six new ones),
`tests_jvm_console.txt` (empty: quiet mode, exit 0), `tests_jvm.txt`, `MANIFEST.sha256`.

## 5. Next

G6-HM3, on the user's word:
- the hooks H1–H4, H6, H7, H8 and H9 in `NativeStreamActivity`;
- `HandheldStreamActivity` with its own manifest entry, the layout and an inert pad view;
- the Settings choice in `MainActivity`;
- the real `assembleDebug`;
- a candidate APK sideloaded on the tablet only, read with the decoder-report cells (design §9).

`ca53df0d…` stays on the onn until a pre-registered confirmation there passes.
