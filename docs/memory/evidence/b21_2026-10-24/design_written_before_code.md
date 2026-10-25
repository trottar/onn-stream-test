# B21 — the `link_recovery_config` row: design, written before any B21 code

Baseline HEAD 13ccff5 (G-A4 adopted: the service carries `PRIVYHUB_LINK_RECOVERY=1`). Queue:
`handoffs/QUEUE_2026-10-24H.md` §B21. The row's fault: CL-B12 §1 / §5 row 1.

## 0. What happens today (read from the code)

- `plugins/games.py` line 13 imports `games.emulator_manager` **before** its own B20 block (lines 29-34). So the
  process's **first** `apply(os.environ)` is `emulator_manager.py:21-23`'s. It sets the six into `os.environ` and
  returns `implied` the six / `explicit` {}. Nobody keeps that result.
- `plugins/games.py:32-34`'s `apply` is already the second: it finds the six present and returns `implied` [] /
  `explicit` the six. Its result is discarded too.
- At the plugin's wire, `plugins/games.py:200-201` logs a **third** `apply(os.environ)`. That is what CL-B12 read:
  `implied` [] / `explicit` {the six: "1"}.
- Behaviour is right (the environ held only the umbrella; `e3_state.py` read `implied 1` for all six). Only the row is
  wrong: it reports what a re-application finds, not what the umbrella did.

## 1. The design

**`companion/link_recovery.py`:**
- A module global `_FIRST = None`. `apply()` keeps a copy of its result in `_FIRST` **the first time it is called in
  the process** (whichever import site comes first; both import the same top-level `link_recovery` module). Later
  calls behave as today (setdefault, idempotent, same return) and do not change `_FIRST`.
- New `config_row(environ)`: what the row logs, built with **no `apply`** (the environment is not written):
  - `umbrella`, `implied`, `explicit`: the first `apply`'s result, i.e. what the umbrella did at import;
  - `at`: `"import"`;
  - `reapply`: the sorted keys a re-application would add **now** (`implied(environ)`, a read). Under the service this
    is `[]`, "nothing new". If it is ever not empty (an environment changed after import, which nothing in the
    companion does), the row says so instead of hiding it;
  - if no `apply` ran in the process (cannot happen under the plugin, whose import ran one), `at` is `"none"` and the
    three fields are computed from `environ` the way the first `apply` would have (`implied` = the keys not present,
    `explicit` = the ones present). Stated for completeness; tested.

**`companion/plugins/games.py:200-201`:** the second `apply` is **removed** from the log line; the row is
`self._recovery._log("link_recovery_config", **_link_recovery.config_row(os.environ))`. The block stays under
`if _link_recovery is not None:`, so absent nothing changes.

**The import-time `apply` calls are unchanged** (both sites; the first one sets the six before any reader, as B20).

**The expected rows:**
- the service's umbrella alone: `umbrella` true, `implied` the six, `explicit` {}, `at` `import`, `reapply` [];
- the umbrella + one explicit line (e.g. `PRIVYHUB_STALL_RESUME=0`): `implied` the other five, `explicit`
  {`PRIVYHUB_STALL_RESUME`: `"0"`}, `reapply` [];
- the umbrella + the six by hand: `implied` [], `explicit` the six (that is then true);
- the umbrella not `1` (e.g. `0`): `umbrella` false, `implied` [], `explicit` whatever of the six is present;
- absent: `link_recovery` not imported, **no row**.

## 2. Absent = today, byte for byte

- `link_recovery` is imported only under the umbrella (unchanged).
- `plugins/games.py`: the one changed statement is inside `if _link_recovery is not None:`. Proof: the whole module's
  AST with B20's items removed (B20's own stripper: `_link_recovery = None` and each `if` whose test starts with
  `(os.environ.get('PRIVYHUB_LINK_RECOVERY')` or `_link_recovery is not None`) equals the predecessor's with the same
  items removed. And with the umbrella **present**, the AST differs from the predecessor's only in that one call
  (`apply` → `config_row`), shown in the proof.
- `companion/link_recovery.py`: `apply`'s return value and its effect on `environ` unchanged (B20's 7 tests, unedited,
  plus a test comparing `apply`'s returns and environ before / after with the predecessor module loaded beside it).

## 3. Tests (`tests/link_recovery/test_config_row.py`, new; B20's file unedited)

- **fresh processes, the import order of the service** (`plugins/games.py` loaded alone, which imports
  `emulator_manager` first, constructing nothing), then `m._link_recovery.config_row(os.environ)`:
  - the umbrella alone → `implied` the six, `explicit` {}, `at` `import`, `reapply` [];
  - the umbrella + `PRIVYHUB_STALL_RESUME=0` → `implied` the five, `explicit` that one;
  - absent → `_link_recovery` is None (no row can be logged) and `link_recovery` not in `sys.modules`;
- **the row line itself:** the `if _link_recovery is not None:` block of `GamesPlugin.__init__` is taken from the
  module's AST and run against a fake `self._recovery` (a list-appending `_log`) in a fresh process under the umbrella:
  one `link_recovery_config` row with the fields above; `os.environ` unchanged by it;
- in process: `_FIRST` is set once (a second / third `apply` leaves it); `config_row` writes nothing to `environ`;
  `at` `none` when no `apply` ran; `apply`'s returns equal the predecessor module's for the same inputs;
- `tests/link_recovery` (B20's 7 + these) green; every `tests/` suite green in the copy.

## 4. Files

`companion/link_recovery.py`, `companion/plugins/games.py` (one line), `tests/link_recovery/test_config_row.py` (new).
Record `evidence/B21_LINK_RECOVERY_CONFIG_LOG_2026-10-24.md` + `b21_2026-10-24/`; `patches/B21_LINK_RECOVERY_CONFIG_LOG.md`.
Host-side only: no APK. Not adopted beyond what G-A4 already carries: the companion is **not restarted** (the rule), so
the running service keeps the old row until the user's next restart; CL-B13 reads the new row after one.
