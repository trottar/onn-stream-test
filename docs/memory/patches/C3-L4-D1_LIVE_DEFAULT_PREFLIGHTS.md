---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: 4e45a4f
durable_memory_updated: true
---

# C3-L4-D1: the harness preflights for live-by-default

## Purpose

The user authorized live adaptive bitrate as the default on 2026-09-30:
"do the loss row look first and then the live default".

- It is made by a systemd drop-in for the user unit:
  `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`,
  containing `Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`. The unit
  file is unchanged.
- The companion's environ therefore carries that one `PRIVYHUB_*` name.
- The checks in `tools/` assumed "no `PRIVYHUB_*`" or "mode off at
  teardown". They would refuse every run, or tear the default down to
  off.
- Task: `handoffs/LINK-L1_LOSS_ROW_LOOK_AND_LIVE_DEFAULT_TASK.md`, Part B.
- Records: `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md` and
  `evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`.

## Change

**`tools/c3_l4_nft_night.py`** (the user's `nft` night harness):

- `DEFAULT_LIVE`, `env_baseline_refusal(manager, environ)` and
  `baseline_mode(environ)`:
  - the user manager must carry **no** `PRIVYHUB_*` (no `set-environment`
    residue);
  - the companion's environ may carry **only** `DEFAULT_LIVE`; any other
    name or value is refused.
- **Preflight** records the baseline: the environ, and the mode it
  implies (live with the drop-in, off without it). The status mode must
  match it.
- **Setup**: when live is the default, no `set-environment` is used
  (`live_on` row `by_default: true`). Without the drop-in it sets the
  mode as before (`flag_set`).
- **Teardown**: `unset-environment` still runs, but it only clears
  manager residue; the drop-in is never touched. The clean check is
  manager none, environ equal to the baseline, and mode equal to the
  baseline. **It no longer expects `off`.**
- **`finish()`** tears down when setup ran (`entered`), not only when the
  harness set the flag itself. With the drop-in it never sets the flag,
  so the old condition would have skipped the teardown.
- The summary gains `baseline_mode` and `baseline_environ`.

**`tools/d7_regression.py`**, the boot row: the companion's environ may
carry only `DEFAULT_LIVE`, and the user manager must carry no
`PRIVYHUB_*`. The evidence fields are renamed accordingly.

**Not edited:** the evidence copies of older scripts (the C5, CL-B1, L1,
L2, S1 and N-night `*_night.sh` / `*_run.sh`, and the L2 copies of the
nft harness). They are history (`TOOLS.md`).

## Tests

- `tools/test_c3_l4_nft_night.py`: **32/32**. That is the 24 existing
  tests plus 8 in `LiveDefault`:
  - the name;
  - the accepted baselines;
  - manager residue refused;
  - other names and values refused;
  - `finish()` tears down when live came from the drop-in, and not
    before setup;
  - the teardown no longer expects off;
  - d7's boot-row rule.
- **Mutations caught (4/4)**, `evidence/c3_l4_d1_2026-10-01/mutation_check.txt`:
  - `finish()` keyed on `flag_set` again;
  - manager residue allowed;
  - any environ name allowed;
  - the teardown expecting off.
- **Fake-sudo runs** on the default-live companion
  (`evidence/c3_l4_d1_2026-10-01/d1_fake_tests.sh`, `d1_check.py`):
  - **FULL** (F1, F2, F3, K; `--fast`): exit 0, **D1 PASS**;
  - **ABORT** (`--only F1`, exception at F1's cap): exit 4, **D1 PASS**;
  - both ended with the manager empty, the environ exactly the one name,
    and the mode live.
- `tools/test_adaptive_bitrate_live.py` and
  `tools/test_adaptive_bitrate_shadow.py`: 123/123, unchanged.

## Files

- `tools/c3_l4_nft_night.py`
- `tools/d7_regression.py`
- `tools/test_c3_l4_nft_night.py`
- Diff: `evidence/c3_l4_d1_2026-10-01/tools_patch.diff`.
