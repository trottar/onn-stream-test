# B20 — one umbrella flag for the stack: design, written before any B20 code

Baseline HEAD 7f3f71d + B17 + B18 + B19 (uncommitted). Queue: `handoffs/QUEUE_2026-10-24G.md` §B20. Pattern for the
adoption: `patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md` (B13).

## 0. Where the six are read today

- **At import, from `os.environ`:**
  - `plugins/games.py` (each module's import gate: `INPUT_HOLD`, `INPUT_HOLD_REWIND`, `INPUT_HOLD_B6`, `STALL_SIGNAL`,
    `INPUT_HOLD_B8`, `STALL_RESUME`);
  - `games/emulator_manager.py` (`INPUT_HOLD` and `INPUT_HOLD_REWIND`: B4's launch-config import).
- **At wire time,** from the `environ` the plugin passes (`os.environ`): each module's `parse` / `enabled` / `mode`,
  and `hold_rewind` / `rewind_cores`' own reads of `_B6` / `_B8`.
- **The emulator's launch config** (`apply_session_config(…, os.environ)`).

So the one place every reader sees is the process environment, read at import and after.

## 1. The design

New `companion/link_recovery.py`:
- `FLAG_ENV = "PRIVYHUB_LINK_RECOVERY"`.
- `STACK` = exactly `PRIVYHUB_INPUT_HOLD`, `PRIVYHUB_INPUT_HOLD_B6`, `PRIVYHUB_INPUT_HOLD_B8`,
  `PRIVYHUB_INPUT_HOLD_REWIND`, `PRIVYHUB_STALL_SIGNAL`, `PRIVYHUB_STALL_RESUME`, each `=1`.
- `implied(environ)` → the keys of `STACK` **not present** in `environ`, when the umbrella reads exactly `1`; else `{}`.
  **An explicit individual flag wins:** any value present, `0` included, is left alone. A bench turns one part off
  with `…=0`, which each module already reads as "ignored", that is off.
- `apply(environ)` sets the implied keys into `environ` (`setdefault`). It is idempotent, and returns
  `{implied, explicit}`.
- `describe(lines)` for the readers: from a `KEY=VAL` list (the service's `/proc/<pid>/environ`), the six as they will
  act (implied / explicit value).

The hooks (absent = nothing imported, nothing read):
- **`plugins/games.py` and `games/emulator_manager.py`, before their first flag read:**
  `if (os.environ.get("PRIVYHUB_LINK_RECOVERY") or "").strip(): import link_recovery; link_recovery.apply(os.environ)`.
  Both call it (the import order between them is not relied on); the second call adds nothing.
- **One recovery-log row at the plugin's wire:** `link_recovery_config` with `implied` / `explicit`, the config read
  back beside each module's own config row.
- **The reader: `tools/e3_state.py`** (A's `--check` line) gains a `link_recovery` key **only when the service's
  environ carries the umbrella**: `describe` of it. Absent → the output is byte for byte today's.
- **The service's `/proc` environ keeps showing the drop-in as written** (the umbrella line). The six live in the
  process's own `os.environ`; child processes inherit them, unread.

**Adoption PREPARED only** (`patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`):
- the drop-in content (`link-recovery.conf`: `Environment=PRIVYHUB_LINK_RECOVERY=1`);
- `tools/e1_suite.py`: `LINK_RECOVERY` in `ADOPTED` (**ten**), the preflight's `drop_in_link_recovery` and its `ok`
  term;
- `e3_state.py`'s docstring (ten), `e1_remote.py` / `test_e1_remote.py`'s comments, and every other nine-counting
  reader found by a search;
- **made and tested on a scratch copy** (`e1_suite --self-test`, the tools' tests before / after, `git apply --check`
  against the tree). **Nothing applied to the drop-in directory or the tree's adoption lists.**

## 2. Tests

`tests/link_recovery/`:
- **the umbrella alone = the six by hand, in every reader:** for each module's own parse (`input_hold.parse`,
  `hold_tuning`'s / `hold_ownership`'s / `stall_owner.enabled`, `hold_rewind.parse`, `rewind_cores.mode`,
  `stall_signal.parse`) the result under `{umbrella}` after `apply` equals the result under the six set by hand;
- **in fresh processes,** the set of stack modules `plugins/games.py` and `emulator_manager.py` import is equal under
  the umbrella alone and under the six by hand;
- **an explicit flag wins:** the umbrella + `PRIVYHUB_STALL_RESUME=0` → that module off, the other five on;
- **the umbrella not `1`** (`0`, junk) → nothing implied;
- **absent → nothing read:** `link_recovery` not imported, no stack module imported;
- `describe` of a `/proc`-style list.

The regression: every suite under `tests/` from the copy. The AST proofs for the two hooks and the reader.

## 3. Files

Record `evidence/B20_LINK_RECOVERY_UMBRELLA_2026-10-24.md` + `b20_2026-10-24/`;
`patches/B20_LINK_RECOVERY_UMBRELLA.md`, `patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`;
`logs/b20_git_status.txt`.
