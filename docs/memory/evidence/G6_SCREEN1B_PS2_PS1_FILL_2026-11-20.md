---
memory_schema: 1
as_of: 2026-11-20
status: RECORD — G6-SCREEN1b part 1 done: a handheld launch (`display=handheld`) runs PS2 without its widescreen patch for that launch only (opt-in hub change; every launch without the field identical); the tablet crops PS2 to 4:3 on the reply's `widescreen: false` and stretches PS1 to the 4:3 box; candidate adcb1222… tablet only; the run pre-registered. G6-SCREEN1's run superseded, not run. The onn keeps ca53df0d…. Nothing adopted; the companion not restarted.
---

# G6-SCREEN1b — PS2 and PS1 fill the 4:3 handheld box (part 1: hub change, client, build, pre-registration)

Task: `../handoffs/G6-SCREEN1B_PS2_PS1_FILL_TASK.md` (a byte-for-byte copy of the Cowork file). Patch note:
`../patches/G6_SCREEN1B_PS2_PS1_FILL.md`. Files: `g6_screen1b_2026-11-20/`. Follows `G6_SCREEN1_4X3_PICTURE_2026-11-20.md`.

**The user's decisions (verbatim, 2026-11-20):** "Those wide screen ps2 games are a patch that can be toggled off just
for handheld. PS1 should be stretched, it cant be by much"

**Preflight (06:44Z, `preflight.txt`):**
- G6-SCREEN1 committed (`27b3c937`); `git status` showed only the prompt file.
- No game process, no gradle running.
- The other two Claude Code sessions idle (no children; last activity 03:49Z, session B's queue BF done at 03:48Z).
- Outside 03:45–05:30Z.

## 1. Part A — the hub: a handheld launch without the widescreen patch (opt-in)

### 1.1 Where the patch is applied (read first)

- **The toggle record** `data/games/ps2/patch_toggles.json` (`ps2_patches.TOGGLES_FILE`): `"ws": true` for four
  titles. `PRIVYHUB_PS2_PATCHES` is unset, so B80 is on.
- **The launch path:**
  - `EmulatorManager.launch()` → `_launch_pcsx2()` (`companion/games/emulator_manager.py`);
  - its `_ps2_game_settings()` reads the record and writes `gamesettings/<CRC>.ini` and `<SERIAL>_<CRC>.ini`
    (`ps2_patches.game_ini_text` / `write_game_ini`) **at every launch of a title with a record**, before PCSX2 is
    spawned (`subprocess.Popen` of the AppImage with `-datapath data/games/ps2/config … -- <disc>`).
- **When PCSX2 reads it** (its own logs, `data/games/ps2/logs/*-pcsx2.log`):
  - `Loading game settings from '…/gamesettings/<SERIAL>_<CRC>.ini'` at `Disc changed`, about 1.0–1.6 s after
    start;
  - the patch is turned on only at `ELF Loading` (3–11 s) from what it read: `Enabled patch: Widescreen 16:9`, then
    `Patch: Setting aspect ratio to 1.7777777 by patch request`.
- **When the launch returns:** `_launch_pcsx2` returns only after PCSX2's window and its audio stream (~10–15 s).

### 1.2 How a handheld launch turns it off

- **The request:** `POST /plugins/games/launch?id=…&display=handheld`. The plugin passes `display="handheld"` to
  `launch()` only when the field is there; without it the call is today's (`no_field_identity_check.txt`).
- **The launch** (PS2 only; `display` is read only inside `launch()`'s PS2 branch):
  - for a title whose toggle has `ws` on, the two game settings files' exact bytes (or absence) go to a journal
    (`data/games/ps2/handheld_ws_journal.json`, base64);
  - the files are written with `EnableWideScreenPatches = false`, every other toggle (no-interlacing, 60 fps, B81's
    cheats) as it is;
  - PCSX2 starts and reads them at its disc;
  - before `_launch_pcsx2` returns (after the window and the audio), the journal is put back byte for byte and
    deleted. It is also put back on each failure path: the settings write refused, Popen failing, no window.
- **The game log** (no title, no serial):
  - `PS2 handheld: widescreen patch off for this launch only (the title's setting: on|off)`;
  - then `PS2 handheld: game settings put back (PCSX2 had read them: yes|not seen)`, which reads PCSX2's own
    log line.
- **Titles whose `ws` is already off, or have no record:** nothing extra is written; only the first line is logged.
- **The multitap relaunch** (`relaunch_ports.py`, the only mid-session PCSX2 relaunch) carries `display="handheld"`
  for a handheld session, so a 3–4-player relaunch stays without the patch. Any other session: today's call.
- **The reply:** `status()` (the stream start reply's `game_session`, and every status) adds `"widescreen": false`
  only while a handheld PS2 session runs; absent on every other session (today's payload).

### 1.3 Why nothing persists

- **The toggle record is never written** (the test compares its bytes).
- **The game settings files come back byte for byte** before the launch returns. Test: the files' sha256 before ==
  after, while what PCSX2 read at its spawn held `false`.
- **The next launch without the field** writes `EnableWideScreenPatches = true` again: identical to an earlier
  normal launch's bytes (tested).
- **A crash between the write and the put-back** leaves the journal. The next PS2 launch, handheld or not, puts it
  back before it writes or spawns anything (tested). The record would anyway make that launch rewrite the files from
  `patch_toggles.json`.
- **The one window when the files on disk are not their earlier bytes:** from a handheld launch's write to its
  put-back, about 10–15 s while PCSX2 starts. Nothing else reads them then.
- **The hub's real files, before:** `hub_gamesettings_sha256_before.txt`, 8 files, serials masked. Read only, not
  touched (no launch run).

### 1.4 Savestates (read from the code, PCSX2's logs and the patch files; no game run)

- **What the logs show:** in every widescreen launch, `Enabled patch: Widescreen 16:9` comes at the ELF and then
  HOME-6's slot-1 load (`Loaded state from slot 1`), with no patch line after the load. A load keeps the launch's
  patch set; it does not re-read the settings or re-apply the patch.
- **The four titles' widescreen sections** (PCSX2's bundle, read as the hub reads it; counts only):
  - one title: 15 once-at-boot lines (`patch=0`), no every-frame line;
  - one title: 138 once-at-boot and 6 every-frame lines (`patch=1`);
  - two titles: 8 every-frame lines each.
  - Each sets `gsaspectratio` (the 16:9 output).
- **A savestate made with the patch on, loaded in a handheld launch:** the state's memory holds the patched code and
  values, but the output stays 4:3 (no `gsaspectratio` request).
  - Expected: the picture **squeezed** (widescreen drawing shown at 4:3).
  - For once-only patches, until the game reloads that code, which may be the whole session.
- **The reverse, a handheld save loaded on the TV (patch on):** the once-only lines were applied at the ELF and then
  overwritten by the load; the output is still switched to 16:9.
  - Expected: the picture **stretched** for the two titles with once-only lines.
  - The every-frame lines come back at once.
- **Said plainly:**
  - **a save loaded across the two modes can show the wrong shape**, and HOME-6's Continue (slot 1 at launch) makes
    that likely the first time a TV game is continued on the tablet;
  - a crash or hang from mixed patched / unpatched code **cannot be ruled out** without running the game; none is in
    the logs;
  - memory-card saves are unaffected (no patch writes the cards).
- **No change made for it in this task.**

### 1.5 Tests (`tests_companion.txt`; `tests/g6_screen1b/test_g6s1b.py`, 12 tests)

- **New:**
  - the toggles with only `ws` off; the line;
  - the journal: bytes, an absent file, and no journal → nothing;
  - PCSX2's settings lines;
  - B49's launch rig:
    - with the field, ws on: `false` at the spawn, the files' sha256 equal before / after, the record untouched,
      `widescreen: false` in status and the reply, both log lines, no serial;
    - the next launch without the field: `true`, the earlier bytes, no `widescreen`;
    - without the field: today's;
    - with the field, ws off or no record: nothing new written;
    - a crash-left journal put back by the next launch;
  - `display` read only in `launch()`'s PS2 branch, so other systems are unchanged;
  - the plugin passes the field only when sent (`display=tv` ignored);
  - the multitap relaunch carries it only for a handheld session, otherwise today's call.
- **Every companion suite** (`tests_companion.txt`, 06:51–07:54Z): 103 suites, 97 OK, 6 not. Each was rerun in the tree
  and in a clean export of `27b3c937` (`tests_companion_failures_vs_head.txt`):
  - **`b74_disc_safe`: caused by this change, fixed.** Its test pins the text `emulator.launch(game,
    players_chosen=ports)` in `relaunch_ports.py`; the first version passed `**hh`. `relaunch_ports.py` now keeps
    today's exact calls for every non-handheld relaunch, and only a handheld PS2 relaunch calls
    `launch(…, display="handheld")`, in the `_previous` fallback too. The test file is session B's and is unchanged.
    Rerun (`tests_relaunch_rerun.txt`, 08:11Z, TMPDIR outside the repo): `b74_disc_safe` 22 OK, `relaunch_ports`
    19 OK, `b63_ps1_multitap` 11 OK, `gamecube_session` 54 OK, `g6_screen1b` 12 OK. The fallback check: handheld →
    both calls carry `display="handheld"`; not handheld → `{"players_chosen": 4}` then `{"players_chosen": 2}`.
  - **`b71_disc_swap`: already failing** on the committed code (a source count, 8 ≠ 6, on lines this change does not
    touch). Unchanged after the fix.
  - **`input_hold_b8`: already failing**: the same test fails on the committed code.
  - **`diag_keeper`: this session's test setup.** The keeper refuses a folder inside the repo, and the run's TMPDIR
    was under `runtime/`. With TMPDIR outside the repo: 13 OK.
  - **`h7_minigame_proof`, `h7_rule_search`: transient.** Both pass on rerun in the tree (13 and 52 OK).
  - The no-field identity check was rerun after the fix: **ALL IDENTICAL**. The diff, `after_sha256.txt` and the
    manifest were regenerated; the pre-registration (`31a8832b…`) and the APK are unchanged.

## 2. Part B — the tablet

- **The request:** MainActivity's one launch request gets `HandheldGeometry.launchSuffix(useHandheldGameScreen())`:
  `&display=handheld` with the handheld screen chosen, `""` otherwise (the onn: no touchscreen, no choice, so
  today's URL).
  - **Disclosed:** the task asked for this through a stream-screen hook. The stream screen never sends the launch:
    MainActivity's `POST /plugins/games/launch` starts the game, and the stream screen's `/native-stream/start` comes
    after it. So the field is on MainActivity's launch URL, behind `useHandheldGameScreen()`, as the handheld
    screen's own choice is (onn check 4).
- **The reply:** hook **H12** `onGameWidescreen` (no-op default; one call after H10) passes `game_session.widescreen`
  (null without it).
- **PS2:** cropped `160,0,960x720` (SCREEN1's centre 4:3) **only when the reply says `widescreen: false`**. No field
  (an older hub, or a session launched on the TV and resumed on the tablet) → `"none"` as SCREEN1.
- **PS1: stretched.** The content is `202,0,876x720`:
  - derived from C5-M4's measured picture in the adopted 1920 × 1080 window (x 302–1617, 1316 px), scaled to the
    stream (x 201.3–1078.7), whole pixels inside (202–1077);
  - the core's 1.2190 × 720 = 877.7 agrees within 2 px.
  - The surface is 1753 × 900 at x −276, so the content fills 1200 × 900: **9.6 % wider than its true shape.**
  - `video_crop` `"stretch"`.
  - A game's own black bands above and below (Tekken-like 224-line games: about 24 stream px each) stay in the
    stretched picture.
- **SNES and N64** as SCREEN1. Every other system `"none"`. The 16:9 fallback box: `"none"` for all.
- **The paused picture** (H11) is the box's share of the surface for any fill, stored at 360 × 270.
- **JVM tests** (`tests_jvm.txt`): **370 tests, 0 failures** (SCREEN1: 365).
  - New `G6Screen1bTest` (5): the fill per system and reply; PS2's rectangle; PS1's 202 / 876 from the evidence and
    the 1.219 check; the stretch's surface and the 9.6 %; the request field only via `useHandheldGameScreen()`.
  - Every earlier test unchanged and passing.

## 3. Build and the candidate

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL** (06:53Z).
- **Candidate:** `PrivyHub/app/build/g6_screen1b_candidate/app-debug.apk`, sha256
  **`adcb1222a9049e9a3871c049439b257edb29793f46bd299daba42c4a9b935bfb`** (also `PrivyHub-handheld-preview-adcb1222.apk`).
- SCREEN1's `e4263fd9…` was copied first to `PrivyHub/app/build/g6_screen1b_preserved_outputs/`.

## 4. Checks

- **The onn unchanged** (`onn_unchanged_checks.txt`, by `onn_checks_screen1b.py`, against `27b3c937`):
  1. the manifest's element `4d36c0bb…` as pre-G6;
  2. `NativeStreamActivity`: 4 lines added, 0 removed, **hook defaults today's 10 / 10**;
  3. `PadSlots.kt` and `PointerGuard.kt` unchanged since pre-G6;
  4. MainActivity: only the launch URL's added term `launchSuffix(useHandheldGameScreen())`;
  5. `tools/` untouched; `companion/` only the four files of part A.
  - The onn keeps `ca53df0d…`; the pins are not moved.
- **The no-field launch is identical** (`no_field_identity_check.txt`, by `no_field_identity_check.py`):
  - the committed companion (`git archive HEAD`, read only) against the working tree, on the same made-up fixture,
    for a title with ws on, all off, and no record;
  - **identical:** command line, full environment, cwd / session, the settings files at the spawn, every file left
    (bytes, memory cards included), `status()` (no `widescreen`), the reply's keys;
  - the plugin's launch call identical for ps2, ps1, snes, n64, nes, genesis, gamecube and party.
- **The diff:** `git diff --check` clean; `git apply -R --check g6_screen1b.diff` OK.
- **The redaction check:** `redaction_check.txt`.
- **No restart by this session.** The companion still runs the committed code until the user restarts it (§6).

## 5. The run, pre-registered (`preregistration.md`)

sha256 **`31a8832b7e513536b7503848fd20dcfd439aff88319635b7fe59f16b97aaf43a`**, hashed at **2026-11-20T08:05:31Z**.
- G6-SCREEN1's, copied exactly, changing only:
  - the candidate's hash;
  - a condition: the companion restarted on this commit first;
  - c10 for PS2: `"4:3"`, `"160,0,960x720"`;
  - c11: the session's PS2 game log holds `PS2 handheld: widescreen patch off for this launch only`;
  - one remark: an optional PS1 session, `video_crop` `"stretch"`, not a cell.
- **Every companion suite's result** is in `tests_companion.txt`; the pre-registration was hashed after it finished.

## 6. The user's companion restart (after the commit, only when no game is playing)

The commands are in the session's final reply and in `../patches/G6_SCREEN1B_PS2_PS1_FILL.md`.

## 7. Part 2 — the run (after it)

Not run yet.
