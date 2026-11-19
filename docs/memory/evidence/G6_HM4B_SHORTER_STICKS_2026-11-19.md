---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-HM4b part 1 DONE. The sticks' throw 0.875 × G6-HM4's (the user's "10-15% smaller"); candidate APK 965d4f19… for the tablet only; 358 / 358 JVM tests; the run pre-registered (e9694ff0…). Part 2 waits for the user. The onn keeps ca53df0d…. Nothing adopted.
---

# G6-HM4b — the sticks' throw about 12.5 % shorter (part 1: code, build, pre-registration; 2026-11-19)

Task: `../handoffs/G6-HM4B_SCORE_AND_SHORTER_STICKS_TASK.md`. Patch note: `../patches/G6_HM4B_SHORTER_STICKS.md`.
G6-HM4's run, scored NOT MET (c6, c7), is in `G6_HM4_TOUCH_LIVE_2026-11-19.md` §4.

**The user's request (verbatim):** "I think the sticks might actually have too much give. When driving I really had to
pull them pretty far for turning. Maybe like 10-15% smaller would be excellent." Cowork's reading is the midpoint:
0.875.

**Preflight (20:15Z, `g6_hm4b_2026-11-19/preflight.txt`):**
- no game running;
- the gradle and Kotlin daemons idle, left by G6-HM4 part 1's build at ~19:07Z (no build running);
- three other Claude Code session processes idle (no children, transcripts last written 12+ h earlier); only this
  session active;
- baseline `43016a37`.

## 1. The change (`TouchPadState.kt`, +8 / −2: the stick constants only)

| | G6-HM4 | G6-HM4b |
|---|---|---|
| full deflection (= the drawn ring) | r 132 px | **r 115.5 px** (0.875 ×) |
| finger travel to full deflection | 15.0 mm | **13.1 mm** (at the panel's ~224 ppi) |
| drawn diameter | 2.79 cm (240 dpi) / 2.99 cm (224 ppi) | **2.44 cm** (240 dpi) / **2.62 cm** (224 ppi) |
| press (catch) area | r 158.4 px, Ø 3.35 / 3.59 cm | unchanged |
| dead zone, clamp, sign, a finger keeps its stick | 0.1 r, 1, up / right positive, until it lifts | unchanged (0.1 of the new r) |

**The 2.5 cm minimum, said plainly.** The amendment's 2.5 cm minimum was for the sticks' drawn size. At 0.875 × the
drawn ring is **2.44 cm** on the stricter 240-dpi measure, **under** the minimum (2.62 cm at the panel's own ~224 ppi).
**The 0.875 throw is kept anyway:** the user asked for it, and the press area, which is what a thumb must land on,
stays 3.35 cm.

**The layout re-check** (`layout_check_hm4b.py`, output `layout_check_hm4b_output.txt`): B2's numbers with the smaller
rings. All checks are OK across 120 press-area pairs, and nothing newly overlaps; the press areas are unchanged. The
sticks' drawn size under 2.5 cm is **reported**, not failed, as the task asks.

## 2. Tests and build (`tests_jvm.txt`, `build_console.txt`)

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL. 358 tests, 0 failures, 0 errors,
  0 skipped** (the run at 20:17Z).
- **New in `G6TouchPs2Test`:** `fullDeflectionAt0875OfTheOldRadius` checks:
  - full deflection at 115.5 px;
  - half the throw gives half;
  - G6-HM4's 80 % travel now gives about 91 %;
  - a touch 150 px out, outside the new ring, still lands on the stick.
- **Updated to the new radius** (as the task asks): the four-directions-and-sign test and the clamp / dead-zone test.
- **The minimum-size test** now pins the sticks' ring at 115.5 px and their press area ≥ 2.5 cm, instead of the drawn
  ring ≥ 2.5 cm (disclosed above).
- Every other test is unchanged and passes.
- **The candidate:** `PrivyHub/app/build/g6_hm4b_candidate/app-debug.apk`,
  sha256 `965d4f197213a639fd0277dbbd06f1db2b9c25f1899a5eaace879dabc83d66e5` (also `PrivyHub-handheld-preview-965d4f19.apk`).
  The previous `build/outputs` APK (`12bb09e7…`) was copied first to `PrivyHub/app/build/g6_hm4b_preserved_outputs/`.

## 3. The onn is unchanged (`onn_unchanged_checks.txt`)

1. The manifest's `NativeStreamActivity` element is byte for byte as before any G6 code (`4d36c0bb…`); G6-HM4b does
   not touch the manifest.
2. G6-HM4b does not touch `NativeStreamActivity.kt`; the 7 hook defaults are today's.
3. `PadSlots.kt` and `PointerGuard.kt` are unchanged since `f52ce75b`.
4. G6-HM4b does not touch `MainActivity.kt`; its G6 statement is still inside `useHandheldGameScreen()`.
5. `companion/` and `tools/` are untouched. The onn keeps `ca53df0d…`, and the pins are not moved.

The only code file changed is `TouchPadState.kt`. `git diff --check` is clean; `git apply -R --check g6_hm4b.diff`
is OK. The redactor is clean on the Kotlin files and the records.

## 4. Part 2 — the tablet run (pending)

Pre-registered and hashed before the run: `g6_hm4b_2026-11-19/preregistration.md`, sha256 `e9694ff0…`, at
2026-11-19T20:18:05Z. It is G6-HM4's pre-registration copied exactly, changing only the candidate, the steps (all 16
controls numbered one per line, SELECT and START on their own lines, the sticks pushed to the edge and held) and one
added remark (whether the shorter throw suits driving). The result is added here after the run.
