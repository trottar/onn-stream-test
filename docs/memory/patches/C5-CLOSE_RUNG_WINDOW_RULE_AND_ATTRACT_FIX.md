---
memory_schema: 1
as_of: 2026-10-05
baseline_commit: 4493e68
durable_memory_updated: true
---

# C5-CLOSE: the rung window skips non-PLAYING reports; the look helper's `--attract` fixed

## Purpose

Two changes from the user's calls of 2026-10-05, as C5 and Phase C close
(`handoffs/C5-CLOSE_PHASE_C_CLOSE_TASK.md`; record
`evidence/C5_CLOSE_2026-10-05.md`):

- **The rung window** counted clean reports while link-drop recovery held
  the game paused. A frozen picture streams clean, so S2b's window filled
  and qualified on a paused screen (448 entry decisions refused by the
  guards). The user's call: such reports do not count.
- **`tools/ps1_look.sh --attract`** launched the title but left the TV
  launcher without NOW PLAYING, and never tapped RESUME PLAYING (the
  user's first attempt, 2026-10-04).

**Nothing is adopted.** The rung flag stays off and is not adopted.

## Change

**The rung window** (`companion/adaptive_bitrate_live.py`, behind
`PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`):

- New `LivePolicy._rung_append(clean, ctx)`, used at the window's two
  appends (the evaluated report and the resync report). With the flag,
  a report whose context says `recovery_playing` is false is skipped
  (not appended) and counted in `rung_skipped_not_playing` (per session,
  reset with the window's other session state).
- Skip, not reset: the window keeps its pre-pause reports and resumes on
  PLAYING. Only an explicit false is skipped.
- `RUNG_WINDOW_RULE`; the status's `rung_1080p.window_rule` and
  `skipped_not_playing`; `holds_in_force.rung_skipped_not_playing`. All
  with the flag only.
- The docstring records the rule. Nothing else in the policy changed.

**The helper** (`tools/ps1_look.sh`):

- `--attract`: after the launch, wait for the game to be active, then
  `open_stream`: force-stop the app, wake, start `MainActivity`, wait
  `PS1_LOOK_OPEN_S` (7 s), find `now_playing_preview_host` in a
  `uiautomator dump`, tap its centre from its bounds (fallback 1008 298),
  confirm `NativeStreamActivity`; two attempts. If it fails, it prints the
  TV steps and waits for PLAYING as before.
- Teardown, when it opened the stream: BACK first; after the restore,
  force-stop and restart the launcher (no stale NOW PLAYING).
- Every printed line also goes, UTC-stamped, to
  `logs/games/ps1_look_helper.log` (`PS1_LOOK_LOG`).
- The header names the plain route as the default.

**Tests and tools:**

- `tools/test_adaptive_bitrate_live.py`: new class `C5CloseRungWindow`
  (6 tests).
- `tools/test_ps1_look_helper.py`: the adb stub models the launcher, the
  tap and the top activity; the `--attract` test rewritten; three new
  tests (no preview, a tap that does not open, the log); the log is
  redirected in every test.
- `tools/c5_close_replay.py` (new): the stop rule, flag on before/after,
  the S2b replay.

**Unchanged:** the shadow (`d66211b3…`), the entry threshold (415 of
450), the leave, the increase window, every trigger; the profile, the
drop-in, the APK, the client; the adopted PS1 `.opt` / `.cfg`.

## Verification

- `tools/test_adaptive_bitrate_live.py` **126 / 126**; shadow 21, nft
  harness 32, selector 14, source contract 7, look 13 pass;
  `test_c3_f1` 7/8 (its pre-existing error).
- Mutations **22 / 22** caught
  (`evidence/c5_close_2026-10-05/c5_close_mutation_check.sh`).
- Stop rule **PASS**: flag absent, 0 differences against `5005615` over
  448 series. Flag on vs `4493e68`: 5 series differ, all holding
  not-PLAYING reports.
- S2b replay: 451 entry decisions → 0; the window never qualifies during
  the pause.
- Injection check (TOP=1080p + INJECT=1, one 60-s hold): **PASSES**;
  teardown flags absent, APK `de072762…835e` confirmed.
- `tools/test_ps1_look_helper.py` **11 / 11**; one real
  `tools/ps1_look.sh 4x --attract` dry pass to PLAYING and back, ADOPTED
  STATE VERIFIED (the launcher-restart step was added after it and is
  fake-run covered).
- Hashes: `evidence/c5_close_2026-10-05/pre_patch_sha256.txt`,
  `post_patch_sha256.txt`; diff `code_patch.diff`.

## Rollback

`git checkout 4493e68 -- companion/adaptive_bitrate_live.py tools/ps1_look.sh tools/test_adaptive_bitrate_live.py tools/test_ps1_look_helper.py`,
then `systemctl --user restart privyhub-companion`. With the rung flag
absent (the default) the controller's behaviour is identical either way.
