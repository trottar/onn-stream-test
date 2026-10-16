---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
durable_memory_updated: true
---

# G5-S2: the WAN adaptation rules, behind `PRIVYHUB_WAN_ADAPTATION=1`

## Purpose

`docs/WAN_ADAPTATION_RULES.md` R1-R5 as a guarded input to the live ladder,
proved by replay. Record: `evidence/G5_S2_WAN_ADAPTATION_RULES_2026-10-16.md`.

## Change

- **New** `companion/wan_adaptation.py`:
  - `WanRules` (pure): R1-R5 over G5-S1's window classes;
  - `WanAdaptation.feed`: the policy's `feed`, with the one suggestion
    applied as a constraint. A blocked increase is refused
    `wan_no_step_up`; a forced one-rung decrease goes through the ladder's
    own `_decide`. Each suggestion is a `wan_suggestion` row with
    `source: wan_rules`.
- **`companion/adaptive_bitrate_live.py`** (predecessor `49a814e3…`, after
  `58f247a5…`), two guarded places:
  - the module global `WAN_ADAPTATION`, built only when the flag is `1`,
    with the import inside the `if`;
  - one `if` in `LiveController.observe`. Absent, it calls
    `self._policy.feed(s, ctx)` exactly as before.

  `LivePolicy` is not edited.
- **New tests:** `tests/wan_adaptation/test_wan_adaptation.py` (23).
- **Docs:** `docs/WAN_ADAPTATION_RULES.md` (the title, the status, one G5-S2
  line per rule); ROADMAP §G5 (the G5-S2 paragraph).

## Validation

- `python3 -m unittest discover -s tests/wan_adaptation` → 23 OK.
- `tools/test_adaptive_bitrate_live.py` → 126 OK; `tests/overlay` 17,
  `tests/session_identity` 80 and `tests/wan_telemetry` 18, all OK.
- `evidence/g5_s2_2026-10-16/replay.py`, flag absent:
  - the four named runs' recorded decisions reproduced exactly;
  - HEAD's and the edited `LiveController` wrote identical rows.
- Flag present: tabulated, open loop, with no claim of improvement.

## Result

BUILT behind the flag; NOT ADOPTED; nothing committed. `PATCH_INDEX.md` was
not updated (not session B's file).
