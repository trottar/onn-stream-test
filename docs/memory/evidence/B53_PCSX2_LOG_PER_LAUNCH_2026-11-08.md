---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 65186c66 (built on B52 in /tmp/b_q11s_b53; queue S's combined diff applied to the tree, uncommitted)
---

# B53 — PCSX2's log per launch, kept 30 days, copied by the keeper, counted by diag_read

**Classification: SETTLED + BUILT.**
- **Tests:** `tests/ps2_session` 79 green ×3; every host suite as the baseline copy; the touched suites from the tree
  OK.
- **Mutations:** 5 caught.
- **Proof:** absent / no PCSX2 log = today (`b53_2026-11-08/proof_flag_absent.md`).
- Not adopted; nothing committed.

Design `b53_2026-11-08/design_written_before_code.md`, sha256 `10a178cd…1e8c`, hashed **17:06:45Z, before any B53
code**.

## 1. Settled

- **PCSX2 2.8.2's own help text:** `-logfile <path>: Writes the application log to path instead of emulog.txt.` So the
  log is per launch from the CLI, with no copy at exit.
- **The drive messages it logs:** `Read Abort`, `CDVD read err, retrying…`, `SUB CHANNEL READ ERROR`, the `Read Bad
  Parameter` errors, `DVD Read when CD Error`. **There is no slow-read line, so "disc read waits" count only errors
  and retries** (disclosed).

## 2. Built

- **The launch:**
  - `-logfile <data/games/ps2/logs/<YYYYmmddTHHMMSSZ>-pcsx2.log>` before `--` (the UTC launch time only: no title or
    id);
  - B52's ELF / TLB checks read that file;
  - the game log gains `PS2 pcsx2-log: <name>`;
  - **30-day retention** at each launch (names older than 30 days removed; other files untouched).
- **The keeper:**
  - the second source `data/games/ps2/logs/`: each new log becomes a tail from its first byte, kept as
    `raw/ps2logs__<name>/`, redacted as the game logs; those present at the start count as seen;
  - `diag_keeper` resumes these tails across its restarts;
  - the copies are local diagnostics in `~/privyhub_diag/` and carry PCSX2's title / serial lines as RetroArch's game
    logs do; never in git or a record.
- **`diag_read`:**
  - reads the logs live and from keeper dirs;
  - a PS2 session's row gains `pcsx2_log` = `read_errors`, `invalid_binding`, `card_formatted`, `card_unformatted`,
    `tlb_miss`, `state_saved`, `state_loaded`, `elf`, counted from the previous session's end (or the launch) to this
    session's end;
  - the report gains `## PCSX2 logs (B53)` only when such a row exists.
- **Test hygiene:** `tests/ps2_session/_tmp_cleanup.py`, imported by each test module, removes that run's own temp dirs
  at exit (B52 §4: the leftovers that filled `/tmp`).

## 3. Tests

- the name from a fake launch time;
- `-logfile` before `--` (and absent without it);
- the retention (31 days removed, 29 kept, other names kept);
- the keeper copying a new log and not a pre-existing one; no folder = today's keeper;
- `diag_read`'s counts in the session window (a line after the session not counted), the Markdown section;
- no log and a PS1 session have no key.

## 4. Files

`b53_2026-11-08/`:
- the usual start files, the design + hashes, `predecessors/`;
- `b53.diff` (against B52), `queue_s_combined.diff` (B52 + B53 against the baseline, applied to the tree);
- `after_sha256.txt`, `proof_flag_absent.md`;
- `tests_ps2_session_x3.txt`, `tests_mutations.txt`, `tests_host_b52_b53.txt`, `tests_host_baseline.txt`,
  `tests_tree_after_apply.txt`;
- `units_before_apply.txt`, `applied_to_tree_at.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B53_PCSX2_LOG_PER_LAUNCH.md`.
