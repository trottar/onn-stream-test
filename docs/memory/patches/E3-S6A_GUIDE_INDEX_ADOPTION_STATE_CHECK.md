---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: ccee2f5
durable_memory_updated: true
---

# E3-S6A: the adopted state's check expects the guide index (tools only) + the adoption drop-in (host, outside git)

## Purpose

E3-S6A (`handoffs/E3-S6A_GUIDE_INDEX_ADOPTION_TASK.md`, record
`evidence/E3_S6A_GUIDE_INDEX_ADOPTION_2026-10-07.md`) adopts E3-S6's
cached guide index (the user, 2026-10-07: "1. Adopt"). From here on the
companion's environ is exactly two `PRIVYHUB_*` lines, and every
precondition and teardown check must expect both.

## Change

**On the host (not in git):**
`~/.config/systemd/user/privyhub-companion.service.d/epg-index.conf`
(copy: `evidence/e3_s6a_2026-10-07/epg-index.conf`):

```ini
[Service]
Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached
```

`adaptive.conf` and the unit file are untouched.

**`tools/e1_suite.py`** (diff: `evidence/e3_s6a_2026-10-07/e3_s6a_state_check.diff`):

- `INDEX = "PRIVYHUB_EPG_GUIDE_INDEX=cached"`, `ADOPTED = sorted([LIVE, INDEX])`.
- `preflight()`: the environ must equal `ADOPTED`; a new
  `drop_in_index` check (the unit's `systemctl --user cat` lists the line).
- `teardown_flags()` (`flags_absent`), `run_once()` (the expected environ
  after a run's restart) and `run_suite()`'s final state: `ADOPTED`
  instead of `[LIVE]`.
- `tools/e3_state.py` reads through `preflight()`; only its docstring changed.

**Not changed** (they still accept only the live default and would refuse
the adopted environ): `tools/d7_regression.py`'s boot row and
`tools/c3_l4_nft_night.py`'s preflight. Neither is used by Phase E; both
need the same one-name extension before their next use.

## Validation

- `e1_suite.py --self-test` OK; `e3_state.py` `ok: true` on the adopted
  state (04:16:03Z).
- E3-S6A's three verification runs passed preflight, teardown and the
  final state through this check.

## Rollback

With the adoption's kill switch (`TOOLS.md`): delete `epg-index.conf`,
`daemon-reload`, restart; then revert `e3_s6a_state_check.diff` (the
check would otherwise refuse the one-line environ).
