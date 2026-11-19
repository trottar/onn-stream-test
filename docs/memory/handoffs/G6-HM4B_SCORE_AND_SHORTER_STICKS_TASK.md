---
memory_schema: 1
as_of: 2026-11-19
status: TASK — session G6. Scores G6-HM4 part 2 as pre-registered with the user's remarks, then G6-HM4b: the sticks' throw about 12.5 % shorter, a new tablet-only candidate, and its run pre-registered. The onn keeps ca53df0d…. Nothing adopted; nothing committed.
---

# G6-HM4 score + G6-HM4b — shorter stick throw

## Part A — score G6-HM4 part 2 (read only)

1. Check that the pre-registration's sha256 is still `0fbaf9f2…`.
2. Pick the session by its "Which session" rule. Cowork's reading is session 19:29:34Z → 19:32:38Z and decoder report
   `logs/games/decoder_sessions/native_decoder_20261119_193238_516.json`; confirm it from the raw files.
3. Score c1–c8 exactly as written, each with its value. Cowork's preview, which you must confirm:
   - c1–c5 and c8 met (join 5007 ms; max output gap 173 ms);
   - **c6 NOT MET**: 14 of 16, with `SELECT` and `START` absent;
   - **c7 NOT MET**: the right stick reached up 0.379 and left 0.791; its down and right, and the left stick in all four
     directions, reached ≥ 0.9.

   The verdict follows the rule. The context figures: `touch_writes`, `takeovers`, `back_swallowed`, lost packets,
   resyncs.
4. **The user's remarks and answers, verbatim (2026-11-19):**
   - "Overall played pretty nice. I think the sticks might actually have too much give. When driving I really had to
     pull them pretty far for turning. Maybe like 10-15% smaller would be excellent."
   - Asked whether they pressed SELECT and START and pushed the right stick fully up and left: "I used the right stick
     naturally, but never clicked select and start thAt was an oversight".
   - Record that c6's miss and c7's miss were the run's steps not followed in full, by the user's own account, not a
     fault found in the code. Do not change the verdict for that: NOT MET stands as scored.
   - Do not ask the user for further remarks.

   Write part A into `docs/memory/evidence/G6_HM4_TOUCH_LIVE_2026-11-19.md` as part 2.

## Part B — G6-HM4b, the sticks' throw about 12.5 % shorter (code for the tablet only)

**The user's request:** sticks "10-15% smaller".

**Cowork's reading, the midpoint:** full deflection at **0.875 × today's radius**, so a turn needs 12.5 % less finger
travel.
- The drawn base ring shrinks to match, so what is seen matches what is felt.
- The dead zone stays 0.1 of the new radius, the clamp stays 1, and the sign rules are unchanged.
- The press (catch) area stays at today's size, so the sticks are no harder to land on.
- A finger keeps its stick until it lifts, as today.
- Re-run `layout_check_b.py`'s B2 numbers with the smaller rings. Nothing may newly overlap, and the sticks' drawn size
  is reported in cm. The amendment's 2.5 cm minimum was for the sticks' drawn size: if 0.875 × brings a stick under
  2.5 cm, report it and keep the 0.875 throw anyway. The user asked for it, and the press area still exceeds 2.5 cm.
  Say so plainly.

**Rules:**
- The onn's code paths stay as they are, shown as at G6-HM4 (`onn_unchanged_checks.txt`'s five checks again).
- No adb, no install, no stream, no service restart, nothing fetched. The companion and `tools/` are untouched; the
  onn keeps `ca53df0d…`; the pins do not move.
- Preflight: no game, gradle or other Claude Code session running, or stop and say so.
- Touch no other session's files.

**Steps:**

1. **The change and its tests.** A test pins full deflection at 0.875 × the old radius. The dead zone, the clamp and
   the sign tests are updated to the new radius. Every earlier test passes.
2. **Build.** `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`. The candidate goes to
   `PrivyHub/app/build/g6_hm4b_candidate/`, plus a copy named `PrivyHub-handheld-preview-<sha8>.apk`. Preserve the
   previous `build/outputs` APK first.
3. **The checks.** The onn-unchanged checks, the diff, `git diff --check`, `git apply -R --check`, and the redaction
   check.
4. **Pre-register the run, hashed before it:** `docs/memory/evidence/g6_hm4b_2026-11-19/preregistration.md`. Copy
   G6-HM4's pre-registration exactly (conditions, "Which session", cells c1–c8 and their bounds, the verdict rule,
   the remarks list), changing only:
   - the candidate's hash;
   - **the steps.** Make them harder to miss:
     - number all 16 controls one per line;
     - put **SELECT** and **START** as their own lines, with "the game may pause; tap START again to go on";
     - make the stick step read "push each stick to its edge and hold a moment: up, down, left, right, the left stick
       first, then the right";
   - **one added remark:** whether the shorter throw suits driving.

   Hash it.
5. **Record:**
   - `docs/memory/evidence/G6_HM4B_SHORTER_STICKS_2026-11-19.md`: part 1 now, part 2 after the run;
   - a patch note and its `PATCH_INDEX.md` row;
   - the plan's dated line and `CURRENT.md`'s G6 line;
   - `logs/g6_hm4b_git_status.txt`: this task's files only.

**Gates:**
- every JVM test passes;
- BUILD SUCCESSFUL;
- the onn-unchanged checks pass;
- `git diff --check` is clean;
- the redaction check is clean;
- `tools/check_memory_health.py` passes.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- part A's eight cells with their values and the verdict;
- the new radius and drawn sizes;
- the candidate's sha256;
- the tests;
- the onn checks;
- the pre-registration's sha256;
- the user's steps exactly as pre-registered.
