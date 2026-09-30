---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C3-L4-L2: the live increase rule (the user's blend), per-report samples, the `nft` harness

## Purpose

`C3-L4-L1`'s increase rule was 90 **consecutive** reports at fps ≥ 59,
queue 0 and gap ≤ 150. It never fired on a clean link, so a stepped-down
session stayed down (`evidence/C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`
§5). The user chose "the blend" on 2026-09-28. Task:
`handoffs/C3-L4-L2_INCREASE_RULE_AND_NFT_HARNESS_TASK.md` (queue
`QUEUE_2026-09-29.md` item 1). Record:
`evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md`.

## Change

- `companion/adaptive_bitrate_live.py` (`LivePolicy`):
  - A report is **clean** when fps ≥ 57, queue ≤ 1 and gap ≤ 150.
  - **The increase window**: the last 90 evaluated reports since the
    last SSRC change and its 3-report blackout. It starts empty after
    every change: the controller's own transition, recovery's restart,
    a full start, or a session start. Stale reports are skipped; a
    resync report enters the window as not clean.
  - **INCREASE**: one rung when the window is full and ≥ 85 of its 90
    are clean, and the hold-downs, guards, rate limit and oscillation
    guard allow it.
  - The constants are `INCREASE_*`. The status carries
    `policy.increase_window`, and the transition row carries
    `window_reports` and `clean_reports`.
  - Decreases, hold-downs, the blackout, the rate limit, the guards and
    the disable route are unchanged.
- `LiveController`: one `sample` row per client report in the existing
  log (`logs/games/adaptive_bitrate_shadow.jsonl`). The row carries:
  - time, session elapsed, fps, queue, gap, fresh;
  - clean, and the disposition (evaluated / blackout / resync / stale /
    non_distinct / dropped_actuating / ...);
  - the window count and its clean count;
  - state, reason, level, the blackout remaining and the hold-downs.
- `tools/test_adaptive_bitrate_live.py`: the two tests of L1's
  consecutive rule are replaced. Ten blend tests and one sample-row
  test are added. The rest is unchanged. 54 tests.
- `tools/c3_l4_l1_replay.py`: the header prints whichever increase rule
  the module carries, and it takes an optional output file name.
- **New** `tools/c3_l4_nft_night.py`: the user's `nft` night harness. It
  never runs `nft` or `sudo`; it prints the lines to paste.

**Not changed:**

- `companion/adaptive_bitrate.py` and its suite; the shadow keeps its own
  rule;
- the rest of the companion;
- the profile, the encoder, FEC and the client.

## Validation

- `py_compile` is clean.
- The live suite passes **54/54**. The shadow suite passes **21/21,
  unchanged** (`evidence/c3_l4_l2_2026-09-29/unit_tests.txt`).
- **Parity**: the shadow night through live is still **0 actions**.
- **Loss replays** under the blend (`c3_l4_l2_replays.txt`). The
  would-fire lists include increases. The most transitions in any 10
  minutes are 2 (proxy) and 3 (bound); **RATE_LIMITED 0**.
- **Flag-off smoke** after the restart: `mode off`, disable 200, inject
  403.
- **Session B2** and the **harness dry run**: in the record.

## Files

SHA-256 before and after: `evidence/c3_l4_l2_2026-09-29/pre_patch_sha256.txt`
and `post_patch_sha256.txt`. `module_patch.diff` is the diff of the live
module against L1.

## Rollback

Restore L1's `adaptive_bitrate_live.py`
(`evidence/c3_l4_l1_2026-09-28/adaptive_bitrate_live.py`) and its test
file, then restart the unit. With the flag unset, neither version builds
the live controller.
