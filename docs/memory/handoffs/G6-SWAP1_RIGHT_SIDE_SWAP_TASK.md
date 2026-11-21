---
memory_schema: 1
as_of: 2026-11-21
status: TASK — session G6. Part A scores G6-JOIN1's run if not yet scored (G6-JOIN1S, read only). Part B, G6-SWAP1: the right stick and the face buttons trade places; every other control stays exactly where it is. A tablet-only candidate; its run pre-registered and hashed before it. No hub change, no restart. The onn keeps ca53df0d…. Nothing adopted; nothing committed by you.
---

# G6-JOIN1 score + G6-SWAP1 — face buttons up, right stick down

The id is G6-SWAP1: G6-HM5 and G6-HM6 stay reserved as the plan says.

## Preflight (stop and say so if any fails)

- G6-JOIN1 is committed (`git log`); `git status --short` shows nothing of it except, if G6-JOIN1S already ran and its
  record is not yet committed, that record.
- No game, gradle or other Claude Code session running; the user may be playing on the tablet.
- Outside 04:30–05:30Z and the 45 minutes before it.

## Part A — G6-JOIN1S (only if not done)

If `docs/memory/evidence/G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md` has no part 2 yet, run
`Claude outputs/G6_tablet/G6-JOIN1S_SCORE_TASK.md` steps 1–5 exactly as written (read only; its own rules hold). If it
already has part 2, say so and skip.

## Part B — G6-SWAP1 (tablet only)

**The user's request, verbatim (2026-11-21):** "After playing a while on the tablet I think ergonomically it would be
better to swap the right face and analogs everything else remains unchanged"

Context for the record: in G6-HM1b the user chose "right stick above the face buttons"; this reverses that choice, by
the user, after play. With it the right side matches the left (the D-pad above the left stick; the face buttons above
the right stick), as on a DualShock 2.

### B1. The change (`Ps2TouchLayout` / `layoutPs2`, reference 1200 x 1100)

1. **The face buttons' cluster** moves, as one unchanged diamond (same spacing, radii and hit scale), to centre on the
   right stick's present centre: **(900, 295)**. So △ (900, 205), ○ (990, 295), ✕ (900, 385), □ (810, 295).
2. **The right stick** (same radius, 0.875 throw, press area, DS2 mapping, ownership) moves to the face cluster's
   present centre: **(900, 805)**.
3. **Everything else stays exactly where it is**: the D-pad, the left stick, L3 (540, 815), **R3 (690, 565)**, L1, L2,
   R1, R2, SELECT, START, **End (1080, 70)**, the footer, the video box, the crop, the join rules, the stick mapping.
4. The side-edge gesture exclusions keep following the shoulders, as today.
5. Report: the handheld block gains `layout_version` (for example `"ps2-swap1"`), so a session on this candidate is
   recognised.

### B2. The geometry check

`docs/memory/evidence/g6_swap1_2026-11-21/layout_check_swap1.py` (from `layout_check_screen1.py`) and its output, on
the tablet's 1200 x 2000 screen, 94.5 px per cm:
1. every control other than the right stick and the four face buttons has the same on-screen centre as G6-JOIN1's
   within 1 px;
2. the four face buttons and the right stick are where B1 says, within 1 px;
3. no drawn shape overlaps another, and no press area overlaps another;
4. End's rectangle ≥ 0.5 cm from every press area (report each clearance in px and cm; the nearest is expected to be
   △ or ○);
5. the drawn sizes as before (≥ 1 cm smaller side for SELECT / START / End).
If any of these fails, stop before building and report the figures: do not move anything else to make it pass.

### Tests

They pin the new centres (the five moved controls) and that every other control's centre is unchanged; the stick and
face behaviour tests pass with the new places; `layout_version`. Every earlier test passes.

## Rules

- The onn's code paths stay as they are (the five checks again); the onn keeps `ca53df0d…`; the pins do not move.
- No hub, companion or PCSX2 change. No adb, no install, no stream, no restart, nothing fetched. `tools/` untouched.
- Touch no other session's files and no other prompt file. `G6-WIFI1_SEAT_DROPOUTS_TASK.md` stays as it is.

## Steps

1. Part A.
2. B1, B2 (it must pass) and the tests.
3. **Build.** `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`; preserve the previous `build/outputs` APK
   first; the candidate goes to `PrivyHub/app/build/g6_swap1_candidate/` plus `PrivyHub-handheld-preview-<sha8>.apk`.
4. **Checks.** The onn-unchanged checks, the diff, `git diff --check`, `git apply -R --check`, the redaction check.
5. **Pre-register the run, hashed before it:** `docs/memory/evidence/g6_swap1_2026-11-21/preregistration.md`. Copy
   G6-JOIN1's `preregistration.md` exactly (conditions, cells c1–c13 and their bounds, the verdict rule, the steps, the
   remarks), changing only:
   - the candidate's hash;
   - **"Which session":** the first tablet PS2 handheld session after the hash time whose decoder report has
     `layout_version` equal to this candidate's; older apps are noted and skipped;
   - **one added cell, c14:** `handheld.layout_version` equals this candidate's string;
   - **one added step**, at the start of step 3: "The face buttons are now top right and the right stick bottom right";
     and in the stick step, "push the **right** stick fully up and fully left too: last time it stopped short";
   - **one added remark:** whether the swap feels better, and whether anything on the right side is now hard to reach.

   Hash it.
6. **Record:** `docs/memory/evidence/G6_SWAP1_RIGHT_SIDE_SWAP_2026-11-21.md` (part 1 now, part 2 after the run); a
   patch note and its `PATCH_INDEX.md` row; the plan's dated lines (the user's reversal of HM1b's choice included) and
   `CURRENT.md`'s G6 line; `logs/g6_swap1_git_status.txt` (git-ignored; for the record only).

## Gates

- Part A done or skipped as above;
- B2's checks pass; every JVM test passes; BUILD SUCCESSFUL;
- the onn-unchanged checks pass; no file under `companion/`, `tools/` or `data/` changed;
- `git diff --check` clean; the redaction check clean; `tools/check_memory_health.py` passes;
- the pre-registration hashed before your last reply, with its hash and time written.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- Part A: its thirteen cells and verdict, or "already scored";
- B2's output (the moved centres and End's clearances in px and cm);
- the candidate's sha256; the tests; the onn checks;
- the pre-registration's sha256 and time;
- the commit command in session B's style (commit the tree; `logs/` is git-ignored);
- the user's steps exactly as pre-registered.
