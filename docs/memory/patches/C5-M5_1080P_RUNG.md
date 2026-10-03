---
memory_schema: 1
as_of: 2026-10-03
baseline_commit: 5005615
durable_memory_updated: true
---

# C5-M5: the 1080p rung on the live ladder, behind its flag

## Purpose

The user's reading of 2026-10-01: Phase C's adaptive machinery exists so
that a higher rung becomes usable, and 1080p had never been a rung. This
patch builds it as C5-M4 §4 designed it, **off by default** and **not
adopted**.

- Task: `handoffs/C5-M5_1080P_RUNG_TASK.md`.
- Pre-registration: `evidence/c5_m5_2026-10-03/c5_m5_preregistration.txt`.
- Record: `evidence/C5_M5_1080P_RUNG_2026-10-03.md`.

## Change

**The actuator: a level can carry a size.**

`companion/diagnostics/c3_linux_actuator_probe.py`:

- `LINUX_RUNG_LEVELS = {12600: (1920, 1080)}`.
- `_run_c3_linux_bitrate_cycle(..., level_transition=True)` is the C3.L3a
  encoder-only restart, with the argv's scale/pad rebuilt at the target
  level's size. 1920×1080 is the rung; every 720p level gets the
  profile's 1280×720. `manager._active_width` / `_active_height` follow
  the level, as `_active_bitrate_kbps` does, and are restored on failure.
- Recovery's same-level restart (C3-F1) accepts the rung and rebuilds it
  at 1920×1080.
- The validated 720p list, the C3.L3 / C3.L3a paths and the loopback
  `c3-validated-bitrate-transition` route are **unchanged**. The route
  cannot reach the rung.
- New entry point: `run_c3_linux_level_transition`, schema
  `privyhub_c5_m5_level_transition_v1`. The payload carries
  `from_size` / `target_size`.

`companion/native_stream.py`:

- `_build_linux_ffmpeg_command(..., width=None, height=None)`. Absent, the
  argv is byte for byte what it was: `golden_after_unset` matches.
  1920×1080 at 12,600 gives exactly C5-M2's c3-arm golden argv.
- `_active_width` / `_active_height`: the profile's at every start and
  stop. `native-stream-status` `width` / `height` report the active level.
- `adaptive_level_transition(kbps)`, the live controller's actuator:
  - between two 720p levels it is
    `diagnostic_c3_validated_bitrate_transition`, unchanged;
  - to or from the rung it runs the sized path.
- `encoder_command` in the status is still set at a full start only, as
  before. No restart updates it.

`companion/plugins/games.py`: the live controller binds
`adaptive_level_transition` (one line).

**The policy** (`companion/adaptive_bitrate_live.py`):

- `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p` (`top_from_env`; exact,
  case-insensitive) gives `LivePolicy(top_1080p=True)`. The ladder
  becomes 5000 / 5500 / 6000 / 7000 / **12600**, with `level_size()`
  returning 1280×720 for every 720p level and 1920×1080 for 12600.
  - **Absent**: the ladder is the closed controller's, and no row or
    status field changes.
- **Entry** `increase_1080p` (class INCREASE): at 7000 only, when the rung
  window is full and ≥ 435 of its 450 reports are clean.
  - The rung window is the blend's rules, 450 long, and restarts at
    every SSRC change. Clean is the blend's: fps ≥ 57, queue ≤ 1, gap
    ≤ 150.
  - Every gate applies.
- **Leave**: the existing triggers and mapping.
  - The mild bar goes one rung down, to 7000 at 720p.
  - Strict capacity and the queue/gap FALLBACK go to 5000; the queue/gap
    ROUTINE goes to 6000. The backstop is as before.
  - The hold-downs are as before: a decrease waits 60 reports after the
    entry.
- **Re-entry hold-down**: 10 min after any leave (`rung_reentry_hold`).
- **Rung oscillation**: a leave, an entry and a leave in one session. The
  second leave is carried out, then HOLD (`oscillation_rung`) for the
  session.
- Rows with the flag carry `from_size` / `to_size` and `rung_leave`. The
  status carries `rung_1080p` and `level_size`, and `controller_start`
  carries `top`.
- **Test-only injection** (`PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1`):
  - `class=SIZE&size=1080p|720p` is §1's raw sized transition; no rule
    decides it;
  - `class=INCREASE_1080P` is the policy's entry decision, with the window
    replaced by the injection;
  - `class=CAPACITY_MILD` is a synthetic mild bar.
- `would_act` counting tolerates a new class key.

**Unchanged:** the shadow `companion/adaptive_bitrate.py` (sha256
`d66211b3…`) and its suite; the drop-in; the profile; the APK; the
client.

## Tests

- `tools/test_adaptive_bitrate_live.py`: **119 / 119**, the previous 102
  plus 17 new (`C5M5Rung`, `C5M5Actuator`).
  - **Entry:** fires at 435 of 450 and not at 434; only from 7000; never
    without the flag (not even a refusal row); the window restarts after
    an SSRC change.
  - **Leave:** the first mild bar goes to 7000 / 1280×720, after the
    60-report hold; strict goes to 5000.
  - **Re-entry, oscillation and injection:** the 10-min re-entry
    hold-down; leave-entry-leave → HOLD, cleared at the session's end;
    the injected entry and mild bar.
  - **Sizes and status:** sizes on every level; the status and the start
    row carry the rung only with the flag.
  - **Actuator:** up, recovery at the rung and down against C3-F1's fake
    manager; the c3 route refuses the rung; the rung argv equals the c3
    golden, and the 720p argv equals `golden_after_unset`.
- Mutations: **10 of 10 caught**
  (`evidence/c5_m5_2026-10-03/mutation_check.txt`). The first run caught
  8 of 10, and two tests were strengthened (`mutation_check_first_run.txt`).
- Shadow suite 21 / 21. Harness `test_c3_l4_nft_night.py` 32 / 32.
  Selector 14, source contract 7.
- `test_c3_f1_recovery_restart.py` 7 of 8: one ERROR that **predates this
  patch** (a source-text search for `restart_encoder=(` that the games
  plugin no longer contains).
- **The stop rule** (`tools/c5_m5_replay.py`):
  - with the flag absent, the patched policy against the closed
    controller's (loaded from git at `5005615`): **0 differences**;
  - 377 series, 128,530 reports, 65,058 events.

## Files

- `companion/adaptive_bitrate_live.py`, `companion/native_stream.py`,
  `companion/diagnostics/c3_linux_actuator_probe.py`,
  `companion/plugins/games.py`.
- `tools/test_adaptive_bitrate_live.py`, `tools/c5_m5_replay.py` (new).
- Evidence: `evidence/c5_m5_2026-10-03/` (`companion_patch.diff`,
  `pre_patch_sha256.txt`, `post_patch_sha256.txt`).
