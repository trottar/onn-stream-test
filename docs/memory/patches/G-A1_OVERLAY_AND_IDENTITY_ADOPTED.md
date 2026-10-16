---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
---

# G-A1 — the state tools' adopted list: seven lines (the overlay provider, session identity v2)

**Result: APPLIED** (session A, 2026-10-16, `handoffs/G-A1_ADOPTION_AND_CL-B3_TASK.md`; the adoptions are the user's,
"yes to all three").

- **What:** `tools/e1_suite.py` `ADOPTED` gains `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`OVERLAY`) and
  `PRIVYHUB_SESSION_IDENTITY=v2` (`IDENTITY`); `preflight()` checks their drop-ins (`drop_in_overlay`,
  `drop_in_identity`) as it checks the five. `tools/e3_state.py` reads that list (it imports `e1_suite`), so the
  task's "e3_state.py's ADOPTED list" is this edit; its docstring now says seven.

  | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- |
  | `tools/e1_suite.py` | `3def90ce25edd220` | `c1afa74184e1cbb1` | two constants + `ADOPTED` (+ two comment lines); two preflight keys and the `ok` clause |
  | `tools/e3_state.py` | `37700863be01c5a4` | `e1bf678c2530ff3e` | the docstring only |

  CL-B3's hash edit (`patches/CL-B3_HARDENED_APK_HASH.md`) followed on `tools/e1_suite.py`; its predecessor is
  this patch's after.
- **Diff:** `evidence/g_a1_2026-10-16/g_a1_state_tools.diff`; predecessors in `evidence/g_a1_2026-10-16/predecessors/`.
- **Validation:** `py_compile` ok; `tools/test_e1_remote.py` 13 / 13; `git diff --check` clean; `tools/e3_state.py`
  ok on the seven lines, both new drop-in keys true, APK CONFIRMED (`check_after.json`).
- **Not edited:** `tools/c3_l4_nft_night.py` `ADOPTED_E3` and `tools/d7_regression.py` (still four lines, as
  CURRENT.md has recorded since E4-S5D; not run here).
- **Revert (written, not applied):** delete `overlay.conf` and / or `session-identity.conf` from
  `~/.config/systemd/user/privyhub-companion.service.d/`, `systemctl --user daemon-reload`, restart the companion;
  copy the predecessors back (or take the name(s) out of `ADOPTED` and the matching preflight key).
- Record: `evidence/G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`.
