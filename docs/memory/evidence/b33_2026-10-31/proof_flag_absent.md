# B33 — absent = today byte for byte: PROVEN

**What "absent" is here.** The rule rides the adopted `PRIVYHUB_LINK_RECOVERY=1` (design §3). Today's behaviour is
kept in three states: no umbrella and no `PRIVYHUB_REWIND_NEEDS_LOSS` line (every B9 / B12 / B16 suite, which set the
individual lines); the umbrella with `PRIVYHUB_REWIND_NEEDS_LOSS=0` (the rollback); a junk value with no umbrella.

1. **Behaviour, row for row** (`proof_flag_absent.py`, output `proof_flag_absent_output.txt`): one scripted set —
   two heartbeats through the recovery's real `note_heartbeat`, a 450-ms stall with 0 loss (B7 + B12, `stall_end`), a
   2-s silence and a 0.93-s silence (B2's hold, B9's state path) — run in fresh processes against
   `/tmp/b_q31l_base` (HEAD 1904fe8) and the B33 copy. Rows equal with every time-valued field masked, the fake core's
   loads equal (`[True]` in every case), in all three states: **EQUAL / EQUAL / EQUAL → PROVEN.** For contrast the
   new tree with the umbrella alone writes `why` on each release (the two heartbeats there are both in the window, so
   the first has no predecessor: `no_heartbeat` → the load; stated as the rule's start-of-session limit).
2. **Nothing imported:** `test_not_imported_without_it` — a fresh process wiring B9's rig with no line has no
   `rewind_needs_loss` in `sys.modules`; `test_zero_absent_and_junk_alone_wire_nothing` — no rule, no
   `rewind_needs_loss_config` row for `=0` under the umbrella, absent, junk alone.
3. **The code off-path:** `Cores.no_loss` and `LinkDropRecovery._rewind_needs_loss` are class attributes `None`; the
   two added branches are each one `is not None` test (`b33.diff`); `rewind_cores.wire`'s guard reads the two lines
   and imports only when on.
4. **The suites:** B4 / B7 / B8 / B9 / B12 / B16 / B18 / B20 / B21 suites unedited; every `tests/` suite the same as
   the queue-L baseline plus `tests/rewind_needs_loss` 14 OK (`tests_regression_after.txt` vs
   `tests_regression_baseline.txt`; the four `tools/` tests fail in a copy as at every baseline).
