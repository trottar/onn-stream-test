---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 75b2b6b
durable_memory_updated: true
---

# E3-A3B: recovery v2 re-adopted through `recovery.conf`; the adopted state's checks expect it (tools) + the drop-in (host, outside git)

## Purpose

E3-A3B (`handoffs/E3-A3B_RECOVERY_V2_READOPTION_TASK.md`, record
`evidence/E3_A3B_RECOVERY_V2_READOPTION_2026-10-09.md`) re-adopts E3-R2's
`PRIVYHUB_RECOVERY_TRIGGER=v2` on the user's "Adopt" and, after E3-A3's
revert, "Code application why not". **ADOPTION STANDS**: the bar judged
controller-trigger events only, and all four clauses held. The
companion's environ is now exactly four `PRIVYHUB_*` lines.

## Change

**Host (not in git):**
`~/.config/systemd/user/privyhub-companion.service.d/recovery.conf`
(`[Service]` / `Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`), written
04:50:43Z. A copy is in `evidence/e3_a3b_2026-10-09/`. `adaptive.conf`,
`epg-index.conf`, `snes-core.conf` and the unit file are untouched.

**Tools:** E3-A3's `evidence/e3_a3_2026-10-09/e3_a3_state_checks.diff`,
applied again (the same bytes:
`evidence/e3_a3b_2026-10-09/e3_a3b_state_checks_applied.diff`):

- `tools/e1_suite.py`: `RECOVERY` in `ADOPTED`, and the preflight checks
  the drop-in;
- `tools/d7_regression.py` and `tools/c3_l4_nft_night.py`: the name in
  `ADOPTED_E3`;
- `tools/e3_state.py`: its docstring;
- `tools/test_c3_l4_nft_night.py`: the adopted names, and the gap log
  alone refused.

## Validation

- `e1_suite.py --self-test` OK; `test_c3_l4_nft_night` 33/33;
  `e3_state.py` ok on four lines.
- Two verification runs passed preflight, teardown and the final state
  through these checks.

## Rollback

The kill switch is in `TOOLS.md` ("Recovery v2"): delete
`recovery.conf`, `daemon-reload`, restart, then `git apply -R` the diff.
