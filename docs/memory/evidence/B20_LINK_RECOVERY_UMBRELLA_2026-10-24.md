---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d (+ B17-B19; B20 uncommitted)
---

# B20 — `PRIVYHUB_LINK_RECOVERY=1`: one host line for the six-line stack; the adoption (G-A4, the tenth line) PREPARED as a patch only

**Classification: BUILT + PREPARED.**
- **Tests:** `tests/link_recovery`, 7 green: the umbrella alone = the six by hand in every module's own reader and in
  fresh processes; an explicit flag wins; absent → nothing read.
- **Proof:** AST identical with B20's items removed in `plugins/games.py`, `games/emulator_manager.py` and
  `tools/e3_state.py`: **PROVEN**.
- **G-A4:** `patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`, tested on a scratch copy; **nothing applied to the
  drop-in directory or the tree's adoption lists.**
- NOT ADOPTED; no live run; nothing committed.

Design `b20_2026-10-24/design_written_before_code.md`, sha256 `96bf9d9a…cfa20f2`, hashed **16:09:28Z, before any B20
code**.

## 1. Built (`b20.diff`)

**`companion/link_recovery.py` (new):**
- `STACK` is exactly `PRIVYHUB_INPUT_HOLD`, `_B6`, `_B8`, `_REWIND`, `PRIVYHUB_STALL_SIGNAL`,
  `PRIVYHUB_STALL_RESUME`, each `=1`.
- `implied(environ)` gives the ones **not present** (any explicit value wins, `0` included), and only when the umbrella
  reads exactly `1`.
- `apply(environ)` sets them (`setdefault`; idempotent) and returns `{umbrella, implied, explicit}`.
- `describe(lines)` is the readers' view.

**The hooks:**
- `plugins/games.py` and `games/emulator_manager.py`: before each module's first read of the six (both import-time
  readers; the second call adds nothing), `if (os.environ.get("PRIVYHUB_LINK_RECOVERY") or "").strip(): import
  link_recovery; apply(os.environ)`.
  - The wire-time readers get the same `os.environ` from the plugin.
  - The service's `/proc` environ still shows the drop-in as written (the umbrella). The six live in the process's own
    environment; children inherit them, unread.
- **The config read back:** one recovery-log row `link_recovery_config` (`umbrella`, `implied`, `explicit`) at the
  plugin's wire, before the six modules' own config rows.
- **The reader:** `tools/e3_state.py` (A's `--check` line) gains a `link_recovery` key (the six as they will act:
  `implied 1` / `explicit <v>`), **only when the service's environ carries the umbrella**. Absent, the output is
  today's.
  - **Not run here:** its preflight calls `adb devices`. The key's function (`describe`) is tested.

## 2. Tests (`tests_link_recovery.txt`)

- **every module's own reader** (`input_hold.parse`, `hold_tuning.enabled`, `hold_ownership.enabled`,
  `hold_rewind.parse`, `rewind_cores.mode`, `stall_signal.parse`, `stall_owner.enabled`): **the umbrella alone after
  `apply` = the six set by hand.** Nothing more than the six is added;
- **fresh processes:** `plugins/games.py` (loaded alone, constructing nothing) and `emulator_manager` import **the same
  stack modules and set the same six module globals** under the umbrella alone as under the six by hand
  (+ `link_recovery` itself);
- **an explicit flag wins:** with the umbrella + `PRIVYHUB_STALL_RESUME=0`, that part is off and the other five are on,
  equal to the same set by hand;
- the umbrella `0` / `yes` / empty / ` 2 ` implies nothing; `apply` is idempotent;
- **absent:** no stack module imported, every module global None, B4's launch-config import absent;
- `describe` of a `/proc`-style list.

## 3. G-A4, PREPARED (`patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`; `ga4_tools.diff`, `ga4_tests_before_after.txt`)

- **The drop-in content:** `link-recovery.conf`, `Environment=PRIVYHUB_LINK_RECOVERY=1`. NOT written.
- **The tools diff, made on `/tmp/b_q24g_scratch/ga4/after/tools`:**
  - `e1_suite.py`: `LINK_RECOVERY` in `ADOPTED` (**ten**), `drop_in_link_recovery` and its `ok` term;
  - `e3_state.py`'s docstring;
  - `e1_remote.py` / `test_e1_remote.py`'s comments. These are G-A3's four files.
  - **Not edited:** `d7_regression.py` / `c3_l4_nft_night.py`'s older three-name `ADOPTED_E3`, which G-A1 to G-A3
    never entered either.
- **Tested before / after on the scratch:**
  - `e1_suite --self-test` OK both;
  - `len(ADOPTED)` 9 → 10;
  - `test_e1_remote` 21 and `test_c3_l4_nft_night` 33 with the same one error / failure both sides (fixtures under
    `docs/`, absent from the copy);
  - **`git apply --check -p1` OK against the tree.**

## 4. For CL-B12 (A)

**Every host cell's drop-in carries `PRIVYHUB_LINK_RECOVERY=1` alone (no individual stack line). Expect:**
- `link_recovery_config` `implied` = the six, `explicit` {};
- then each module's own config row, as CL-B11 read them from the six by hand: `input_hold_config`,
  `input_hold_rewind_cores_config` (mode `state`), `stall_signal_config` (400), `input_hold_b8_config`,
  `stall_resume_config` (`fast_ready` / `save_from_signal` true);
- `e3_state.py` during a cell: `link_recovery.stack` all `implied 1`;
- at the teardown, nine lines and `flags_absent` as today.

## 5. Files

- **`b20_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b20.diff`, `proof_flag_absent.py` / `.md`, `tests_link_recovery.txt`;
  - `ga4_tools.diff`, `ga4_tests_before_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/link_recovery.py` (new), `companion/plugins/games.py`, `companion/games/emulator_manager.py`,
    `tools/e3_state.py`;
  - `tests/link_recovery/` (new);
  - `patches/B20_LINK_RECOVERY_UMBRELLA.md`, `patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`,
    `logs/b20_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed. No drop-in written.
