---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C3-L4-N1: the capacity trigger, the recovery-escalation backstop, `--only`

## Purpose

The user's first `nft` night (2026-09-29) found that under a capacity cap
the live controller never stepped down.

- The client dropped frames rather than queueing them (queue 0-1), and
  lost ~250 packets per report.
- The queue/gap FALLBACK met its bar only inside freezes, which recovery
  already owned.
- Recovery restarted the encoder at 7000 nine times in F1 (C3-F1,
  level-preserving).

The user approved two rules on 2026-09-29: **"Yes, add both"**.

- Task: `handoffs/C3-L4-N1_NFT_NIGHT1_SCORE_AND_CAPACITY_TRIGGER_TASK.md`
  (queue `QUEUE_2026-09-29B.md`, task 1).
- Records: `evidence/C3_L4_NFT_NIGHT1_2026-09-29.md` and
  `evidence/C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`.

## Change

`companion/adaptive_bitrate_live.py`, **LIVE only**. `adaptive_bitrate.py`
(the shadow) is byte-identical.

- **Capacity trigger** (`LivePolicy._evidence`):
  - The rule: FALLBACK when, over the last 5 evaluated reports, fps is
    `< 50` on all 5 and `lost_packets_delta` is `≥ 50` on `≥ 3` of 5.
  - Precedence: the shadow's queue/gap FALLBACK first, then capacity,
    then ROUTINE.
  - The window holds only evaluated reports, so a stale, blackout or
    resync report never counts. A missing delta does not count toward
    the 3.
  - Constants: `CAPACITY_FPS_BELOW`, `CAPACITY_LOSS_AT_LEAST`,
    `CAPACITY_LOSS_OF`.
  - The decision goes through `_decide("FALLBACK")` unchanged: hold-downs,
    the at-floor check, guards, rate limit, oscillation guard and the
    5000 target.
  - Its rows carry `trigger: capacity`, and the transition's reason is
    `capacity`.
- **Recovery-escalation backstop:**
  - `note_ssrc_change(source, clock_ms)` records one recovery
    `encoder_restart` with the level it ran at: the held level for a
    restart, 7000 for a full start. When two fall at one level within
    180 s, it arms one escalation (`escalation_armed` row).
  - An escalation's refusal row is always written: it is not folded into
    a run of capacity `at_floor` refusals. The replay found that defect,
    and it was fixed before the fake-sudo runs; the silent hold ran the
    module without the fix (sha256 `3e312681…`; final `7c326e6e…`).
  - At the first evaluated report with `recovery_playing` true (the
    blackout has already passed by construction), the controller makes
    **one** `_decide("FALLBACK")` with trigger and reason
    `recovery_escalation`. At 5000 that is a logged `at_floor` refusal.
  - The escalation is consumed whatever the outcome, and the restart
    list is cleared, so re-arming needs two new restarts.
  - While recovery is not PLAYING it waits; it is not spent on the
    guard.
  - Constants: `ESCALATION_RESTARTS 2`, `ESCALATION_WINDOW_MS 180000`.
    The state is cleared by `end_session()`.
- **Wrapper:**
  - `LiveController.note_recovery_restart` passes the monotonic clock.
    It is called once per recovery restart by the games plugin
    (unchanged), after the restart returned and released the stream
    lock.
  - The `sample` row gains `escalation_armed`.
  - The status `policy` gains `capacity_trigger` and
    `recovery_escalation` (rule, restarts in the window, the armed
    escalation).
  - Transition, refused and `last_action` rows gain `trigger` / `reason`.
- **Recovery is unchanged** (`link_drop_recovery.py`, `games.py`: no
  edit).
  - C3-F1 stays level-preserving. The controller moves the level, and
    recovery never does.
  - Serialization is L1's: the actuator takes the stream lock and
    re-reads recovery's state under it.
- `tools/c3_l4_nft_night.py`:
  - `--only F1,F3` takes any subset of F1, F2, F3, K and always runs it
    in that order. An unknown, empty or repeated name is refused by the
    argument parser before anything runs. `--sessions` is kept as a
    hidden alias.
  - The default pre-registration is night 2's. `PREREG_NIGHT1` keeps
    night 1's selectable.
  - `did()` records each decision's reason and trigger, the count of
    decisions by trigger, and the `escalation_armed` rows.
  - The printed EXPECT lines name the capacity trigger.
  - The preflight, setup, teardown, allow-list and every always-clear
    path are unchanged.

## Tests

- `tools/test_adaptive_bitrate_live.py`: **85/85**.
  - 54 carried from L2. `telemetry()` gains a `lost` argument (default 0).
  - 31 new: `CapacityTrigger` 14, `RecoveryEscalation` 14,
    `NightOneShape` 1, and 2 wrapper tests.
- **Mutations** (restored after): each was caught.
  - loss-of 3 → 2: 2 failures;
  - window 180 → 182 s: 1 failure;
  - no recovery-PLAYING wait: 2 failures.
- `tools/test_adaptive_bitrate_shadow.py`: 21/21, unchanged.
- `tools/test_c3_l4_nft_night.py`: **23/23** (18 + 5 `OnlySubset`).
- `tools/c3_l4_n1_replay.py` (new): parity 0 actions; the stop rule
  PASS (see the record).

## Files

- `companion/adaptive_bitrate_live.py` (the diff is in
  `evidence/c3_l4_n1_2026-09-29/module_patch.diff`).
- `tools/test_adaptive_bitrate_live.py`, `tools/c3_l4_nft_night.py`,
  `tools/test_c3_l4_nft_night.py`.
- `tools/c3_l4_n1_replay.py` (new).
- `evidence/c3_l4_n1_2026-09-29/`.

## Runtime

- The silent live hold, and the fake-sudo `--only F1,F3` runs.
- Night 2 is the user's.
- Results are in `evidence/C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`.

Nothing adopted. Nothing committed. Flags unset and absent at the end.
