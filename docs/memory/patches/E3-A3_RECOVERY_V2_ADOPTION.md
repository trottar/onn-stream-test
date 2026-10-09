---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 75b2b6b
durable_memory_updated: true
---

# E3-A3: recovery v2 adopted through `recovery.conf`, then reverted by the verification bar (state checks added and reversed; drop-in on the host, outside git)

## Purpose

E3-A3 (`handoffs/E3-A3_RECOVERY_V2_ADOPTION_TASK.md`, record
`evidence/E3_A3_RECOVERY_V2_ADOPTION_2026-10-09.md`) adopts E3-R2's
`PRIVYHUB_RECOVERY_TRIGGER=v2` on the user's "Adopt" (2026-10-09), after
the user's nft check passed.

**ADOPTION REVERTED** by the verification bar's clause (ii): no valid
run in either row after two replacements. All six windows were voided by
the client's own output-silence pauses on a poor link. v2 fired no
controller pause and no save. **The tree carries no change from this
task.**

## Change (adoption, 00:33Z) and revert (03:02:24Z)

- **Host (not in git):**
  `~/.config/systemd/user/privyhub-companion.service.d/recovery.conf`
  (`[Service]` / `Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`). Written,
  then removed at the revert; a copy is in
  `evidence/e3_a3_2026-10-09/recovery.conf`.
- **Tools** (`evidence/e3_a3_2026-10-09/e3_a3_state_checks.diff`,
  applied, then reversed with `git apply -R`):
  - `tools/e1_suite.py`: `RECOVERY` in `ADOPTED`, and the preflight's
    `drop_in_recovery`;
  - `tools/d7_regression.py` and `tools/c3_l4_nft_night.py`: the name in
    `ADOPTED_E3`;
  - `tools/e3_state.py`: its docstring;
  - `tools/test_c3_l4_nft_night.py`: the adopted names, and the gap log
    alone refused.

## Validation

- Adopted: self-test OK, `test_c3_l4_nft_night` 33/33, `e3_state.py` ok
  on four lines.
- Reverted: the five files byte-identical to their predecessors
  (`state_checks_predecessor_sha256.txt`); self-test OK, 33/33,
  `e3_state.py` ok on three lines.

## Re-adoption (the user's call)

Write the drop-in again (the record §5), then `git apply` the diff.
