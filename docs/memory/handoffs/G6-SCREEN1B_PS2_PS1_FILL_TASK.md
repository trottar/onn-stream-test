---
memory_schema: 1
as_of: 2026-11-20
status: TASK — session G6. G6-SCREEN1b: PS2 and PS1 fill the 4:3 handheld box. A handheld launch asks the hub to run PS2 without its widescreen patch (that launch only), and the tablet then crops PS2 to 4:3; PS1's slightly narrow picture is stretched to 4:3. One small, opt-in hub change plus a new tablet-only candidate; the run pre-registered and hashed before it. The onn's launches and code paths stay as they are; the onn keeps ca53df0d…. Nothing adopted; nothing committed by you; no restart by you.
---

# G6-SCREEN1b — PS2 and PS1 fill the 4:3 box

## Why

G6-SCREEN1 (`docs/memory/evidence/G6_SCREEN1_4X3_PICTURE_2026-11-20.md`, `g6_screen1_2026-11-20/crop_decision.txt`)
cropped only SNES and N64, by the rule "every game shown 4:3". PS2 failed because four titles launch with B80's
widescreen patch on; PS1 failed because Beetle PSX HW reports aspect 1.2190, not 1.3333 (876 x 720 in the stream).
For the user's PS2 game the picture would not have grown at all.

**The user's decisions, verbatim (2026-11-20):** "Those wide screen ps2 games are a patch that can be toggled off just
for handheld. PS1 should be stretched, it cant be by much"

So:
- **PS2:** a handheld launch runs with the widescreen patch **off**, for that launch only. Every PS2 game is then 4:3
  in handheld mode and the tablet crops it (960 x 720 of 1280 x 720).
- **PS1:** the tablet shows the content area (876 x 720, centred) stretched to fill the 4:3 box: about 9.6 % wider
  than true shape. The user accepts that.

G6-SCREEN1's pre-registered run is **superseded and will not be run**: record that in its evidence file (part 2: "not
run; superseded by G6-SCREEN1b"), with no verdict. Its pre-registration stays as hashed.

## Preflight (stop and say so if any fails)

- G6-SCREEN1 is committed: `git log` holds its commit and `git status --short` shows nothing of SCREEN1's.
- No game, gradle or other Claude Code session running. The user may be playing on the tablet; session B may be
  running a queue: if so, stop and say so.
- Outside 04:30–05:30Z and the 45 minutes before it.

## Part A — the hub: a handheld launch without the widescreen patch (opt-in)

1. **Find the path, read only first.** Where B80's PS2 patches are applied at launch: `PRIVYHUB_PS2_PATCHES`,
   `data/games/ps2/patch_toggles.json` (`"ws": true` for four titles), the `gamesettings/*.ini` files carrying
   `EnableWideScreenPatches = true`, and how the launcher reaches PCSX2. Write it down with file and line.
2. **The request.** The handheld client adds one field to its game start request saying it is a portrait handheld
   (name it to fit the existing request; for example `"display": "handheld"`). A request without it is handled exactly
   as today: **byte-for-byte the same launch for the onn and every other client**.
3. **The launch.** For a PS2 launch with that field, the widescreen patch is off **for this launch only**:
   - nothing persistent changes: after a handheld launch, the next launch without the field has the patch on again,
     with the same files, bytes and settings as before the handheld launch (prove it in a test, and by sha256 of every
     settings file the launcher touches, before and after);
   - prefer a per-launch override (an argument, a temporary settings copy, or the launcher's own toggle) over editing
     the shared `gamesettings` files; if the only way is to write a file, it is restored before the launch returns, and
     a crash cannot leave it changed (say how);
   - every other patch (B80's other toggles) stays as it is;
   - the game log gets one line saying the widescreen patch is off for a handheld launch (no title).
4. **The reply.** The start reply tells the client what it launched, as one added field (for example
   `"widescreen": false` in the game session object). The client crops PS2 only when the reply says widescreen is off;
   an older hub, or a reply without the field, means no crop.
5. **Saves.** In-game memory-card saves are unaffected. Report what happens if a savestate made with the patch on
   (slot 1, HOME-6's load) is loaded in a handheld launch, and the reverse: read the code and PCSX2's patch timing; do
   not run a game to find out. If it can break a game, say so plainly and make no change for it in this task.
6. **Tests.** The companion's tests pass, plus new ones: the field absent → today's launch, identical; the field present
   with PS2 → patch off for that launch only, then on again; the field present with any other system → no change; the
   reply field.

## Part B — the tablet (tablet only)

1. The handheld activity sends the field in its start request (through a hook whose default sends nothing, like
   H1–H11). The onn's requests are unchanged.
2. **PS2:** crop to `160,0,960x720` when the reply says widescreen is off; otherwise as SCREEN1 (none).
3. **PS1:** show the content area `202,0,876x720` stretched to the full 1200 x 900 box. Derive 876 from the evidence
   (1.2190 x 720, C5-M4's measured 876 x 720), not from a guess, and pin it in a test. `video_crop` reads `"stretch"`
   for PS1.
4. SNES and N64 as in SCREEN1. Everything else as SCREEN1.
5. Tests pin: the request field sent only by the handheld path; PS2 crop only with the reply's field; the PS1 rect and
   stretch; every earlier test passes.

## Rules

- The onn's code paths stay as they are (the five checks again); the onn keeps `ca53df0d…`; the pins do not move.
- **The hub change is code only in this task: you do not restart the companion or any service.** Give the user the
  exact restart command for after the commit, and the check that it came back (the same check other sessions use).
- No adb, no install, no stream, no game run, nothing fetched. `tools/` untouched. Touch no other session's files and
  no other prompt file. `G6-WIFI1_SEAT_DROPOUTS_TASK.md` stays as it is.

## Steps

1. Part A, its tests and the before / after hashes of every settings file the PS2 launcher touches.
2. Part B and its tests.
3. **Build.** `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`; preserve the previous `build/outputs` APK
   first; the candidate goes to `PrivyHub/app/build/g6_screen1b_candidate/` plus `PrivyHub-handheld-preview-<sha8>.apk`.
4. **Checks.** The onn-unchanged checks, a companion check that a request without the field produces the identical
   launch (command line, environment, files), the diff, `git diff --check`, `git apply -R --check`, the redaction check.
5. **Pre-register the run, hashed before it:** `docs/memory/evidence/g6_screen1b_2026-11-20/preregistration.md`. Copy
   G6-SCREEN1's exactly, changing only:
   - the candidate's hash, and a precondition: the companion restarted on this commit before the run (the user's step);
   - **c10 for PS2:** `video_crop` `"4:3"`, `video_source_rect` `"160,0,960x720"`;
   - **one added cell, c11:** the PS2 game log's handheld line (patch off) is present for the session's launch;
   - **one added remark:** whether the bigger picture looks right. An optional PS1 session may be played; its
     `video_crop` `"stretch"` is a remark, not a cell.

   Hash it.
6. **Record:** `docs/memory/evidence/G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md` (part 1 now, part 2 after the run); a patch
   note and its `PATCH_INDEX.md` row; the plan's dated line and `CURRENT.md`'s G6 line; SCREEN1's "superseded" note;
   `logs/g6_screen1b_git_status.txt` (git-ignored; for the record only).

## Gates

- every JVM test and every companion test passes; BUILD SUCCESSFUL;
- the onn-unchanged checks pass, and the no-field launch is identical;
- the settings files' hashes are identical before and after a handheld launch in the test;
- `git diff --check` clean; the redaction check clean; `tools/check_memory_health.py` passes.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- part A: where the patch is applied, how the handheld launch turns it off, why nothing persists, the savestate answer;
- part B: the crops (PS2, PS1 stretch);
- the candidate's sha256; the tests; the onn checks; the no-field identity check;
- the pre-registration's sha256;
- the commit command in session B's style (commit the tree; `logs/` is git-ignored), then the companion restart
  command and its check, to run only when no game is playing;
- the user's steps exactly as pre-registered.
