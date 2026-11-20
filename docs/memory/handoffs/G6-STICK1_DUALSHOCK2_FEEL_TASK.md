---
memory_schema: 1
as_of: 2026-11-20
status: TASK — session G6. Part A scores G6-SCREEN1b's run as pre-registered (read only). Part B, G6-STICK1: the touch sticks made to feel like a real DualShock 2 end to end (diagonals reach full on both axes; full speed just before the ring's edge), a tablet-only candidate, and one pre-registered run that carries SCREEN1b's screen cells too. No hub change, no restart. The onn keeps ca53df0d…. Nothing adopted; nothing committed by you.
---

# G6-SCREEN1b score + G6-STICK1 — DualShock 2 stick feel

The id is G6-STICK1: G6-HM5 and G6-HM6 stay reserved as the plan says. Do not reuse or renumber them.

## Preflight (stop and say so if any fails)

- G6-SCREEN1b is committed (`git log`), and `git status --short` shows nothing of it.
- No game, gradle or other Claude Code session running; the user may be playing on the tablet; session B may be
  running a queue.
- Outside 04:30–05:30Z and the 45 minutes before it.

## Part A — score G6-SCREEN1b as pre-registered (read only)

1. Check `docs/memory/evidence/g6_screen1b_2026-11-20/preregistration.md` still hashes to `31a8832b…`.
2. Pick the session by its "Which session" rule, exactly. Cowork's reading, which you must confirm from the raw files:
   the first tablet PS2 handheld session after the hash time (08:05:31Z) that is not a false start is
   **08:11:58Z → 08:14:52Z**, decoder report `native_decoder_20261120_081452_382.json` (166 s, an End). It ran the
   **previous** app (`video_box` `1200x675`, no `video_crop` key) and the companion before its restart: the run's
   conditions were not in place.
3. Score every cell exactly as written, each with its value. Cowork's preview: c9, c10 and c11 **NOT MET** (box 1200x675;
   no crop field; no handheld line in that launch's game log), c6 NOT MET (5 of 16 controls). Score the rest as they
   fall. The verdict follows the rule: **NOT MET**. Record that the conditions were not met (wrong app, companion not
   yet restarted), by the user's own sequence, not a fault found in the code. Do not change the verdict for that.
4. **Context, not cells** (the user's free play after the restart, 2026-11-20): the four sessions 08:20:05Z → 08:46:09Z
   (`…082739_617`, `…082844_726`, `…083314_250`, `…084609_156`) each show `video_box` `1200x900`, `pad_region`
   `1200x1100`, `video_crop` `"4:3"`, `video_source_rect` `"160,0,960x720"`, and the 08:19:42Z launch's game log has
   `PS2 handheld: widescreen patch off for this launch only`. Confirm and record these figures as context only.
5. **The user's words, verbatim:**
   - "I played a long time last night. It ran super well. I think the analog could use a little fine tuning, but that's
     a small thing."
   - "Left analog movement on rotations would be too slow sometimes."
   - Asked whether to make the sticks behave like a real DualShock 2: "Yep, making feel like true dualshock 2 is a good
     idea"

   Write part A as part 2 of `docs/memory/evidence/G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md`. Do not ask the user for
   anything.

## Part B — G6-STICK1: DualShock 2 stick feel (tablet only)

**The problem, as Cowork reads it.** The touch stick clamps its output to a circle (`stickVector`, unit circle), so a
full push on a diagonal sends about 0.707 on each axis. A real DualShock 2 reaches (nearly) full on both axes at the
corners, and many PS2 games read the axes separately, so running diagonally or turning through the diagonals is slower
(known from PCSX2 users on circular-gated pads). A thumb circling the stick also tends to stay a little inside the ring.

### B1. Trace the whole chain first (read only)

Write down, with files and lines: touch point → `TouchPadState.stickDeflection` (dead zone 0.1, throw 0.875 × r,
unit-circle clamp) → the XUSB int16 in `NativeControllerSender` → the hub's uinput "PrivyHub Virtual Gamepad P1" →
PCSX2's DualShock 2 pad settings for that device as the hub launches it (`data/games/ps2/config/PCSX2/inis/PCSX2.ini`
and any per-game input profile): **`Deadzone`, `AxisScale` (PCSX2's analog sensitivity; its default is 1.33), and
anything else that shapes the sticks**. Compute today's end-to-end DualShock 2 value (0–255, centre 128 or as PCSX2
reports it) for: a cardinal push at 50 %, 75 %, 90 %, 100 % of the throw, and the same on a 45° diagonal. Put the table
in the record. If PCSX2 already scales the diagonal close to full, say so plainly and how much of the user's complaint
that leaves unexplained.

**Do not change PCSX2's settings or anything on the hub**: they are shared with real controllers and the onn.

### B2. The new mapping (the touch sticks only, both sticks)

The target is **end to end**, what the PS2 game receives, after PCSX2's own scale:

1. **Dead zone:** 0.1 of the throw, as today.
2. **Full speed just before the edge:** past the dead zone the magnitude ramps linearly and reaches full at **0.9 of the
   throw**; the outer tenth is full.
3. **Diagonals reach full on both axes**, like a DualShock 2: map the circle to the square (scale the vector by
   1 / max(|cos θ|, |sin θ|)), so a full push at 45° gives full on x and on y; a cardinal push is unchanged.
4. **Compensate for PCSX2's scale on the client**, so the end-to-end result is exactly 1–3 and does not saturate early
   (for example, if PCSX2 multiplies by 1.33, the client sends the target divided by 1.33). If compensation cannot give
   the target (rounding, clamping), get as close as possible and report the residual.
5. The throw (0.875), the drawn ring, the press area, ownership until lift and the sign rules all stay as they are.
6. Real controllers, the onn and every non-touch path are untouched: the mapping lives in the touch pad's path only.

### B3. What the report records (new keys in the handheld block, per stick)

- `stick_out_max`: the largest sent value per axis direction, as now, plus `stick_diag_max`: the largest
  min(|x|, |y|) sent (in sent units and as the computed end-to-end fraction);
- `stick_edge_frac`: the fraction of owned time at magnitude ≥ 0.9 of the throw;
- `stick_mag_hist`: a 10-bin histogram of owned-time magnitude (0–1 of the throw);
- `stick_mapping`: a short version string (for example `"ds2-square-0.9-c1.33"`).

### Tests

They pin: the dead zone; full at 0.9 of the throw; a 45° full push → full on both axes end to end; cardinal values
unchanged in direction and monotonic; the compensation for the PCSX2 scale found in B1; no output beyond full; the new
report keys. Every earlier test passes.

## Rules

- The onn's code paths stay as they are (the five checks again); the onn keeps `ca53df0d…`; the pins do not move.
- No hub, companion or PCSX2 change. No adb, no install, no stream, no restart, nothing fetched. `tools/` untouched.
- Touch no other session's files and no other prompt file. `G6-WIFI1_SEAT_DROPOUTS_TASK.md` stays as it is.

## Steps

1. Part A.
2. B1's trace and table, then B2, B3 and the tests.
3. **Build.** `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`; preserve the previous `build/outputs` APK
   first; the candidate goes to `PrivyHub/app/build/g6_stick1_candidate/` plus `PrivyHub-handheld-preview-<sha8>.apk`.
4. **Checks.** The onn-unchanged checks, the diff, `git diff --check`, `git apply -R --check`, the redaction check.
5. **Pre-register the run, hashed before it:** `docs/memory/evidence/g6_stick1_2026-11-20/preregistration.md`. Copy
   G6-SCREEN1b's exactly (conditions, "Which session", cells c1–c11 with their bounds, the verdict rule, the steps,
   the remarks), changing only:
   - the candidate's hash, and the condition that the companion already runs G6-SCREEN1b's commit (no restart needed;
     check it from the running unit's start time against the commit time, read only);
   - **"Which session" made safer:** the first tablet PS2 handheld session after the hash time **whose decoder report
     shows this candidate's `stick_mapping`**; sessions on an older app are noted and skipped;
   - **c6:** all 16 controls, as before;
   - **one added step**, after the stick step: "Push the left stick into each diagonal corner and hold a moment
     (up-left, up-right, down-right, down-left); then circle it slowly twice, and then the right stick the same";
   - **added cells:** c12, each stick's `stick_diag_max` end to end ≥ 0.95 of full; c13, `stick_mapping` equals this
     candidate's string;
   - **added remarks** (not cells): whether turning through the diagonals now feels right; whether it feels like a
     DualShock 2; anything too twitchy.

   Hash it.
6. **Record:** `docs/memory/evidence/G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md` (part 1 now, part 2 after the run); a
   patch note and its `PATCH_INDEX.md` row; the plan's dated lines and `CURRENT.md`'s G6 line;
   `logs/g6_stick1_git_status.txt` (git-ignored; for the record only).

## Gates

- every JVM test passes; BUILD SUCCESSFUL;
- the onn-unchanged checks pass; no file under `companion/`, `tools/` or `data/` changed;
- `git diff --check` clean; the redaction check clean; `tools/check_memory_health.py` passes;
- the pre-registration hashed before your last reply, with its hash and time written.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- part A's cells with their values and the verdict, and the context figures;
- B1's table (today vs new, cardinal and diagonal, end to end) and PCSX2's stick settings found;
- the candidate's sha256; the tests; the onn checks;
- the pre-registration's sha256 and time;
- the commit command in session B's style (commit the tree; `logs/` is git-ignored);
- the user's steps exactly as pre-registered.
