---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (+ B5-B7 / B1b uncommitted)
---

# LAN-R2 — `PRIVYHUB_LAN_LOSS_RULE=bidir`: step down when the link is bidirectionally bad

**Result: READ (no host signal tells Sunday's pre-burst loss from 1 % random loss); BUILT; replayed: 0 asks in
BENCH-R1 cells 1-4, every clean window and last night, Sunday 05:06:09Z; NOT ADOPTED; no live run.** Record:
`evidence/LAN_R2_LOSS_RULE_RETHOUGHT_2026-10-22.md`. Nothing committed.

- **The rule:** LAN-R1's two 10-s windows, each with ≥ 4 FEC-unrecoverable groups AND ≥ 2 uplink silences ≥ 400 ms
  (the host's own controller stream). One rung, floor 5000, every ladder gate. Labelled `lan_bidir`.
- **`=1`** is LAN-R1's, byte for byte; absent is today.
- **Files:**
  - `companion/lan_loss_rule.py` (the new class, the uplink ring, one guarded statement);
  - `companion/native_session_io.py` (a guarded note of each silence ≥ 250 ms);
  - `companion/plugins/games.py` (sets the ladder's `LAN_LOSS_RULE` for `bidir`; `adaptive_bitrate_live.py`
    untouched);
  - `tests/lan_loss_rule_bidir/` (new, 10).
- **Validation performed:**
  - the analysis and the search;
  - the replay through the real controller (flag absent exact on the evenings and cell 1);
  - the tests (+ LAN-R1's 21 unchanged, the regression set);
  - the AST proof (3 identical);
  - `git diff --check` clean;
  - the redact check.
- **Disclosed:**
  - the replay of cells 3-4 is not an exact reproduction (the harness under heavy loss);
  - G8-S1 `burst-50x20 off` steps twice under `bidir`: the room's uplink was flapping that quarter-hour.
