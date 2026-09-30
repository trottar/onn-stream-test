---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C3-L4-N2: the mild-capacity rule, the status-level fix, night 3's default

## Purpose

The user's `nft` night 2 (2026-09-29, `--only F1,F3`) scored WORKS UNDER
LOSS. But at 6000 under the cap the stream sat degraded for 3 min 56 s
and nothing fired:

- fps median 55.8, and under 50 on only 17 % of reports;
- ~60 lost packets per report;
- queue ≥ 1 on 1 of 115 reports.

The strict capacity rule needs fps < 50 on all 5 reports; the queue
ROUTINE needs queued frames. The user approved a milder rule on
2026-09-29: **"Go"**.

- Task: `handoffs/C3-L4-N2_NFT_NIGHT2_SCORE_AND_MILD_CAPACITY_TASK.md`.
- Records: `evidence/C3_L4_NFT_NIGHT2_2026-09-29.md` and
  `evidence/C3_L4_N2_MILD_CAPACITY_2026-09-29.md`.

## Change

**`companion/adaptive_bitrate_live.py`, LIVE only.** The shadow
(`adaptive_bitrate.py`) is byte-identical.

- **`capacity_mild`** (`LivePolicy._evidence`):
  - The rule: over the last 5 evaluated reports, fps < 57 on ≥ 4 and
    `lost_packets_delta` ≥ 50 on ≥ 3 → class ROUTINE, trigger / reason
    `capacity_mild`.
  - It is checked after the queue/gap FALLBACK and strict capacity, and
    before the queue ROUTINE.
  - Constants: `CAPACITY_MILD_*`.
- **`_decide`**: a `capacity_mild` ROUTINE targets the next rung below
  the level. At 5000 that is the floor, so it is refused `at_floor`.
  - All of ROUTINE's hold-downs (60 / 60), blackout, rate limit,
    oscillation guard, guards and L1's escalation deferral apply
    unchanged.
  - The queue ROUTINE's fixed 6000 target is unchanged.
- **`_transition`**: the reason is the trigger for `capacity_mild` (as
  for `capacity` and `recovery_escalation`).
- **The status gains `policy.capacity_mild`.**
- **`LiveController.session_ended()` clears `_stream_kbps`.** After BACK,
  the status `level` reads the policy's 7000, not the ended session's
  last stream bitrate. That staleness was night 2's check (i).

**`tools/c3_l4_nft_night.py`:**

- The default `--prereg` is night 3's
  (`evidence/c3_l4_n2_2026-09-29/c3_l4_nft_night3_preregistration.txt`).
  `PREREG_NIGHT2` keeps night 2's.
- The F1 EXPECT line names the mild step.
- `--only F1` in the usage.

## Tests

- `tools/test_adaptive_bitrate_live.py`: **102/102**.
  - 16 new: `MildCapacityTrigger` 15, `NightTwoShape` 1, and 1 wrapper.
  - 3 N1 tests narrowed to the strict rule, because their shapes now
    meet the mild bar (declared in the record).
  - Mutations caught: fps-of, loss (after a boundary test was added),
    target, precedence, the status clear.
- `tools/test_adaptive_bitrate_shadow.py` 21/21, and
  `tools/test_c3_l4_nft_night.py` 23/23.
- `tools/c3_l4_n2_replay.py` (new, from N1's): parity 0 actions; the stop
  rule PASS.

## Files

- `companion/adaptive_bitrate_live.py`; the diff is
  `evidence/c3_l4_n2_2026-09-29/module_patch.diff`.
- `tools/test_adaptive_bitrate_live.py`, `tools/c3_l4_nft_night.py`,
  `tools/test_c3_l4_nft_night.py`, `tools/c3_l4_n2_replay.py` (new).

Nothing adopted. Nothing committed. Flags unset and absent at the end.
