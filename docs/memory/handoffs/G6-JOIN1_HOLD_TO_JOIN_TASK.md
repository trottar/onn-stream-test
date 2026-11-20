---
memory_schema: 1
as_of: 2026-11-20
status: TASK — session G6. Part A runs G6-STICK1S (score G6-STICK1's run, read only) exactly as its task file says. Part B, G6-JOIN1: holding any touch control makes the touch pad P1 at once; the 5-second countdown stays as the fallback. A tablet-only candidate and its run pre-registered, hashed before it. No hub change, no restart. The onn keeps ca53df0d…. Nothing adopted; nothing committed by you.
---

# G6-STICK1 score + G6-JOIN1 — hold any touch button to be P1

The id is G6-JOIN1: G6-HM5 and G6-HM6 stay reserved as the plan says.

## Preflight (stop and say so if any fails)

- G6-STICK1 is committed (`git log`), and `git status --short` shows nothing of it.
- No game, gradle or other Claude Code session running; the user may be playing on the tablet.
- Outside 04:30–05:30Z and the 45 minutes before it.

## Part A — G6-STICK1S

Run `Claude outputs/G6_tablet/G6-STICK1S_SCORE_TASK.md` steps 1–6 exactly as written (read only; its own rules hold).
Its record is written before Part B starts.

## Part B — G6-JOIN1 (tablet only)

**The user's request, verbatim (2026-11-20):** "Before we run this, I also think I'd rather be able to hold any button
on virtual controller. We can still keep the 5 seconds but if I hold a virtual button that registers P1"

### B1. Read first (read only)

How P1 is chosen today in handheld mode, with files and lines: `TouchPlayerRules` (`p1Rule`, the 5-second countdown,
D2), `PlayerPrompt.joinAsP1WithoutHold` / `takeOverP1`, and how a **physical** pad joins by holding a button (its hold
time, what it shows, whether the held press reaches the game). Write it down.

### B2. The change

1. While P1 is free and the countdown is running, **holding any touch control** (a button, the D-pad, a shoulder, a
   stick, SELECT, START; not End) for the **same hold time a physical pad uses** makes the touch pad P1 at once and
   stops the countdown. The joining press does not reach the game, as with a physical pad's join hold.
2. Releasing before the hold time does nothing; the countdown goes on. The 5-second countdown, its text and its result
   are otherwise unchanged.
3. If P1 is already taken (a physical pad, or the countdown already finished), a touch hold does nothing new: today's
   behaviour.
4. The line under the buttons says how, during the countdown: for example "Hold any button to join · P1 in 5…" (keep it
   short; it must fit the same line).
5. End keeps working as today at all times.
6. Report: the handheld block gains `p1_join_via` (`"hold"` or `"timer"`) and `p1_join_hold_ms` (the hold time used);
   `p1_join_after_release_ms` stays as it is.
7. The onn, real controllers and every non-handheld path are untouched.

### Tests

They pin: a hold of the physical hold time on any touch control joins P1 at once with `p1_join_via` `"hold"`; a shorter
hold does not; no hold → the timer joins at 5 s as today with `"timer"`; the joining press is not sent; with P1 taken a
touch hold changes nothing; End during the countdown still ends. Every earlier test passes.

## Rules

- The onn's code paths stay as they are (the five checks again); the onn keeps `ca53df0d…`; the pins do not move.
- No hub, companion or PCSX2 change. No adb, no install, no stream, no restart, nothing fetched. `tools/` untouched.
- Touch no other session's files and no other prompt file. `G6-WIFI1_SEAT_DROPOUTS_TASK.md` stays as it is.

## Steps

1. Part A.
2. B1, then B2 and the tests.
3. **Build.** `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`; preserve the previous `build/outputs` APK
   first; the candidate goes to `PrivyHub/app/build/g6_join1_candidate/` plus `PrivyHub-handheld-preview-<sha8>.apk`.
4. **Checks.** The onn-unchanged checks, the diff, `git diff --check`, `git apply -R --check`, the redaction check.
5. **Pre-register the run, hashed before it:** `docs/memory/evidence/g6_join1_2026-11-20/preregistration.md`. Copy
   G6-STICK1's `preregistration_v2.md` exactly (conditions, cells c1–c13 and their bounds, the verdict rule, the steps,
   the remarks), changing only:
   - the candidate's hash;
   - **"Which session":** the first tablet PS2 handheld session after the hash time whose decoder report has
     `p1_join_via` (this candidate); older apps are noted and skipped;
   - **step 2 becomes:** "Start the PS2 game. When the line under the buttons shows the countdown, hold ✕ until it reads
     'Touch buttons: Player 1' (about N s: the physical hold time)";
   - **c5 becomes:** `touch_slot` 0; `p1_join_via` `"hold"`; `p1_join_after_release_ms` < 5000;
   - **one added remark:** whether holding to join feels right.

   Hash it.
6. **Record:** `docs/memory/evidence/G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md` (part 1 now, part 2 after the run); a patch
   note and its `PATCH_INDEX.md` row; the plan's dated lines and `CURRENT.md`'s G6 line;
   `logs/g6_join1_git_status.txt` (git-ignored; for the record only).

## Gates

- G6-STICK1S's record written, its cells as the files show them;
- every JVM test passes; BUILD SUCCESSFUL;
- the onn-unchanged checks pass; no file under `companion/`, `tools/` or `data/` changed;
- `git diff --check` clean; the redaction check clean; `tools/check_memory_health.py` passes;
- the pre-registration hashed before your last reply, with its hash and time written.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- Part A: the thirteen cells with values, the verdict, and the c4 comparison table;
- B1's reading (the physical hold time and what it does);
- the candidate's sha256; the tests; the onn checks;
- the pre-registration's sha256 and time;
- the commit command in session B's style (commit the tree; `logs/` is git-ignored);
- the user's steps exactly as pre-registered.
