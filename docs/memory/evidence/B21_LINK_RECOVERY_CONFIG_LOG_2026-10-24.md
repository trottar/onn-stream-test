---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 13ccff5 (G-A4 adopted; B21 uncommitted)
---

# B21 — the `link_recovery_config` row now reports the import-time `apply()`: `implied` the six, `explicit` {}

**Classification: BUILT** (inside `PRIVYHUB_LINK_RECOVERY=1`; absent = today).
- **Tests:** `tests/link_recovery` **16 green** (B20's 7 unedited + 9 new in `test_config_row.py`). Every `tests/`
  suite green in the copy. One `tests/session_identity` failure, a timestamp one second apart, passed 5 / 5 re-runs
  (disclosed, §2).
- **Proof:** `plugins/games.py`'s AST with B20's items removed = the predecessor's. Present, the only difference is
  the row's call (`apply` → `config_row`). **PROVEN.**
- **The predecessor reproduces CL-B12's row exactly.** A fresh process in the service's import order under the
  umbrella alone gives `implied` [] / `explicit` the six; B21 gives `implied` the six / `explicit` {} / `at` `import` /
  `reapply` [].
- NOT restarted (the rule): the running companion keeps the old row until the user's next restart. No live run.
  Nothing committed.

Design `b21_2026-10-24/design_written_before_code.md`, sha256 `6e101829…6d3cf8b2a3`, hashed **17:45:36Z
(2026-10-25), before any B21 code**.

## 0. Settled from the code

- `plugins/games.py` imports `games.emulator_manager` (line 13) **before** its own B20 block (lines 29-34). So the
  process's **first** `apply` is `emulator_manager.py:21-23`'s. It set the six and returned `implied` the six; nothing
  kept the result.
- `plugins/games.py:34`'s `apply` was already the second (it found the six present). The wire's row
  (`plugins/games.py:201`) logged a **third**, which reported them as explicit. That is CL-B12's reading.
- Behaviour was the umbrella's throughout: the environ held the umbrella line only.

## 1. Built (`b21.diff`)

- **`companion/link_recovery.py`:**
  - `_FIRST` keeps a copy of the process's first `apply` result, whichever import site makes the call (both import the
    same top-level module). `apply`'s return and its effect on the environment are unchanged (tested against the
    predecessor's function).
  - New **`config_row(environ)`**, which writes nothing. It returns:
    - the first `apply`'s `umbrella` / `implied` / `explicit`;
    - `at` `import`;
    - `reapply`: the keys a re-application would add **now** (a read). `[]` means nothing new. If anything ever changed
      the environment after import, the row would name it.
  - With no `apply` in the process, `at` is `none` and the fields are what a first `apply` would report. This cannot
    happen under the plugin; it is tested anyway.
- **`plugins/games.py:200-202`:** the second `apply` is **removed** from the row. The row is
  `self._recovery._log("link_recovery_config", **_link_recovery.config_row(os.environ))`, still under
  `if _link_recovery is not None:`.
- **The rows CL-B13 should read after the next restart:**

  | service environ | `link_recovery_config` |
  | --- | --- |
  | `PRIVYHUB_LINK_RECOVERY=1` alone (G-A4's drop-in) | `umbrella` true, `implied` the six, `explicit` {}, `at` `import`, `reapply` [] |
  | + `PRIVYHUB_STALL_RESUME=0` | `implied` the other five, `explicit` {`PRIVYHUB_STALL_RESUME`: `"0"`}, `reapply` [] |
  | + the six by hand | `implied` [], `explicit` the six |
  | the umbrella not `1` | `umbrella` false, `implied` [], `explicit` {} |
  | absent | **no row** (`link_recovery` not imported) |

## 2. Tests (`tests_link_recovery.txt`, `tests_regression_*.txt`, `tests_session_identity_rerun.txt`)

- **Fresh processes, the service's import order** (`plugins/games.py` loaded alone, constructing nothing):
  - the umbrella alone → the row above. **The row line itself**, `GamesPlugin.__init__`'s
    `if _link_recovery is not None:` block taken from the AST, run against a fake recovery log → **one**
    `link_recovery_config` row with those fields, and `os.environ` unchanged by it. The block calls `config_row`, never
    `apply`;
  - an explicit `PRIVYHUB_STALL_RESUME=0` → `explicit` that one, `implied` the five;
  - the six by hand → `explicit` the six;
  - the umbrella `0` → nothing implied, the six absent from the environment;
  - **absent → `_link_recovery` None, `link_recovery` not imported: no row.**
- **In process:**
  - `_FIRST` is kept once (a 2nd and 3rd `apply` return `implied` [], and the row still reads the six);
  - `config_row` writes nothing (`at` `none`);
  - `reapply` names a key removed after import;
  - `apply`'s returns and environ effects = the 13ccff5 function's, over six starting environments × 3 calls.
- **Every suite** (`tests_regression_after_b21.txt`, against `tests_regression_queue_h_baseline.txt`):
  - all `tests/` suites OK. **Disclosed:** `tests/session_identity`'s `test_flag_absent_and_legacy` failed once. Its
    two lists differ only in a request-log timestamp one second apart (`…:47:46` / `…:47:47`), a second boundary
    crossed during the test. It passed 5 / 5 re-runs, and B21 touches nothing that suite uses;
  - the four `tools/` tests fail in the copy as at the baseline (their fixtures are under `docs/`, absent from the
    copy).

## 3. Files

- **`b21_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b21.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_link_recovery.txt`, `tests_regression_queue_h_baseline.txt`, `tests_regression_after_b21.txt`,
    `tests_session_identity_rerun.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `companion/link_recovery.py`, `companion/plugins/games.py`, `tests/link_recovery/test_config_row.py`
  (new); `patches/B21_LINK_RECOVERY_CONFIG_LOG.md`; `logs/b21_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
