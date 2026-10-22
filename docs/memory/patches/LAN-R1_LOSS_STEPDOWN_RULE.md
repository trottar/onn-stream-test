---
memory_schema: 1
as_of: 2026-10-21
baseline_commit: 357ee73
---

# LAN-R1 — one rung down on sustained FEC-unrecoverable groups, behind `PRIVYHUB_LAN_LOSS_RULE=1`

**Result: BUILT behind a flag, proved by replay; NOT ADOPTED; no live run.** Applied in the working tree by session
B, 2026-10-21 (`handoffs/LAN-R1_LOSS_STEPDOWN_REPLAY_AND_DESIGN_TASK.md`). Record:
`evidence/LAN_R1_LOSS_STEPDOWN_2026-10-21.md`. Nothing committed. The live test is session A's.

- **The flag:** `PRIVYHUB_LAN_LOSS_RULE=1` (`1` only). Absent = today: the ladder does not import the module, and
  `observe()` is unchanged. The replay proves it: both evenings' recorded decisions exact, and HEAD's controller
  against the edited one identical row for row (2,256 / 1,510 rows).
- **The rule:**
  - When each of the newest 2 windows of 5 evaluated reports holds ≥ 4 FEC-unrecoverable groups
    (`telemetry.fec.unrecoverable_groups_delta`), it asks for one rung down through the ladder's own
    `_decide("ROUTINE", …)`, with every gate. The decision is labelled `lan_loss`.
  - Floor 5000. Re-climb by the existing increase rule.
  - One `lan_loss_rule` row per ask.
- **The files** (`evidence/lan_r1_2026-10-21/lan_r1.diff`; `predecessors/`):

  | file | predecessor sha256 (16) | after (16) |
  | --- | --- | --- |
  | `companion/adaptive_bitrate_live.py` | `4dbbb5400b7bb8bf` | `dffbacd24ab3829b` |
  | `companion/lan_loss_rule.py` | (new) | `7ce249c9185a3c84` |
  | `tests/lan_loss_rule/test_lan_loss_rule.py` | (new) | `95a42504b03185d9` |

- **Validation:**
  - `tests/lan_loss_rule` 21 OK;
  - the regression suites all OK, including `tools/test_adaptive_bitrate_live.py` 126 (one of them run from the
    tree, read-only, for its golden fixture);
  - `git diff --check` clean;
  - the replay with the rule on: Sunday 7000→6000 at 05:03:05Z, →5500 at 05:06:07, →5000 at 05:10:48. 0 asks in
    every clean window. Last night, 2 asks refused by the session-age guard.
- **Disclosed:**
  - T / K were chosen in sample, and the cell is an edge (T 3 K 2 has 6 false triggers, T 4 K 1 has 19).
  - The rule also steps down under random loss (G8-S1 loss-1: 5000 within 9-11 min), where a lower rate does not
    help.
- **Rollback (written, not applied):** copy `adaptive_bitrate_live.py` back from
  `evidence/lan_r1_2026-10-21/predecessors/`, and remove `companion/lan_loss_rule.py` and `tests/lan_loss_rule/`.
  With the flag absent nothing runs anyway.
