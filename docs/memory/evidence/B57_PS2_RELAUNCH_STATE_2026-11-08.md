---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: d618a20a (B57 built in /tmp/b_q13u_b57 on the baseline; applied to the tree, uncommitted)
---

# B57 — the PS2 multitap relaunch through PINE (slot 7), and the `PrivyHub-Import/` ignore line

**Classification: SETTLED + BUILT** inside `PRIVYHUB_PS2=1` (every change is on a branch reached only in a PCSX2
session). A third pad holding in a PS2 game now brings the game back where it was, as PS1 does (B54's relaunch).
- **Tests:** `tests/relaunch_ports` **19** green ×3 (B54's 10 + B57's 9; B54's PS2 test moved to B57's meaning,
  disclosed); `tests/ps2_session` 93 green ×3, unchanged. Every host suite as the baseline copy.
- **Mutations:** 12, all caught on the first run (`b57_2026-11-08/tests_mutations.txt`).
- **Proof:** absent = today, PROVEN; PS1 untouched (`b57_2026-11-08/proof_flag_absent.md`).
- NOT ADOPTED (live with the adopted `PRIVYHUB_PS2=1` at the next companion restart: HOME-7 Stage 1); no live run;
  PCSX2 not started; no client change, no APK; nothing committed.

Design `b57_2026-11-08/design_written_before_code.md`, sha256 `1129c03d…cfb515845`, hashed **19:42:24Z, before any
B57 code**.

## 0. Settled

**B54's relaunch for PS1 (RetroArch):** pause → the relaunch save (SAVE_STATE_SLOT 0 copied to
`<stem>.state.relaunch`, verified; a failure = refused, nothing touched) → the encoder stopped → the core stopped →
the launch with the new ports → resume → a 1.0-s settle → the running-core load (`[State] Loading` required) → pause →
the encoder started on the new window → `relaunch_ports` (`state: loaded`) and `ports_set` (`source: relaunch`).

**Where PS2 diverged:** no save (`reason: ps2_no_relaunch_state`), so after the launch the title ran from its boot
(`state: restarted`).

**The slots** (PCSX2's own 1-10; PrivyHub's user slots 1-3): **9** B55's hold / stall scratch, **8** B55's give-up
save, **7 the relaunch** (new, `ps2_session.RELAUNCH_SLOT`). None collides. The file is PCSX2's `….07.p2s` (and its
`.backup`), overwritten at the title's next relaunch; no slot index is written, so the Game State list never shows it.

**The budget** (B54's 15 s from the join to play):

| step | expected |
| --- | --- |
| pause (hotkey) | ~0.1-0.2 s |
| **save: PINE 0x09 slot 7 + B52's file-complete check** | **~0.5 s** (HOME-5 / HOME-6) |
| stream stop; stop (SIGTERM) | ~0.2 s; ~1 s (bound 7 s) |
| **the launch (`MultitapPort1` per the count) + the hold to the ELF** | **~6-9 s** (H3-P2; HOME-6: `ELF Loading:` at t 4.68) |
| **load: PINE 0x0A slot 7 + `Loaded state from slot 7.`** | **≤ 0.31 s** (HOME-6) |
| **B52's picture check** | ~0.6 s (0.9 s from the load to a confirmed picture) |
| pause; stream start | ~0.1 s; ~0.8 s |

**Expected total ~9.5-13 s, inside 15 s**, with less margin than PS1's ~6-10 s (the boot dominates). The fake-timed
run in the tests (save 0.25 s, launch 2.0 s, the ELF at 6.0 s of running, stream start 0.8 s) totals **9.45 s**. The
worst bounds (window 30 s, sink-input 45 s, ELF 30 s, picture 5 s) can pass 15 s: `within_budget: false` is then
recorded and the game still comes back (the budget is read, not enforced, as B54).

**The client's wait (no client change, disclosed):** the onn reads the relaunch's answer with a 30-s timeout (B54's
`RELAUNCH_READ_TIMEOUT_MS`). The normal PS2 path (~9.5-13 s) fits; the clean relaunch after a static / faulted picture
boots twice (~20 s fake-timed: 16.05 s in the tests) and can come near it; past it the client takes the answer as
failed (`ok` false in its `relaunches`) while the host finishes and the game runs. If C20 shows this, the client's
timeout is a client change (an APK), not made here.

## 1. Built (`b57_2026-11-08/b57.diff`: `b57_code.diff` + `b57_gitignore.diff`; 6 files)

- **`ps2_session.py`:** `RELAUNCH_SLOT = 7`.
- **`emulator_manager.py`:**
  - `save_relaunch_state`, PCSX2 branch (B54's refusal) → **`_pcsx2_save_relaunch_state`**: `ensure_pine_pause`, PINE
    0x09 slot 7, **B52's file-complete check** (`wait_state_file`: new, size steady over two polls, a whole zip). The
    game log: `PS2 relaunch save: slot 7 pine 0x09 ok; file complete <s>s` (or `fail` / `no answer` / `file not
    complete`). Returns `state_path`, `slot` 7, `ps2_states: "pine"`. No index.
  - `load_recovery_state_running(source=…)`, PCSX2 branch: no source → B55's call exactly; a source → B55's running
    load with slot 7 (the source must be this session's `.07.p2s`, else refused before PINE). **The ELF hold** (B52's
    pre-check) → PINE 0x0A slot 7 → `Loaded state from slot 7.` → **B52's picture check** → left running; log `PS2
    relaunch load: slot 7 pine 0x0a ok; picture <verdict> <s>s`. A static / faulted picture raises with `ps2_picture`
    set.
- **`relaunch_ports.py`, `kind == "pcsx2"`:**
  - **save** (slot 7). **A failure is not a refusal on PS2:** the relaunch goes on and the title restarts without the
    state (today's behaviour), `reason: ps2_relaunch_save_failed`, `save_error`;
  - stream stop → **stop** (SIGTERM) → **launch** with `players_chosen` = the new count (`MultitapPort1`), B54's
    previous-ports fallback and ended path unchanged (moved into one helper, `launch_ports`);
  - with a state: **resume → load** (the ELF hold inside; **no 1.0-s settle on PS2**) → `state: loaded`;
  - **the load fails:** a static / faulted picture (the state loaded, the game did not run from it) → the title once
    more, clean (`stop_clean`, `launch_clean`) → `state: restarted`, `reason: ps2_relaunch_picture_static|fault`;
    otherwise (the ELF not up in 30 s, PINE failing) the game is its fresh boot already → `state: restarted`,
    `reason: ps2_relaunch_load_failed`, no second launch;
  - pause → stream start → the rows: `relaunch_ports` (`ok`, `state`, `kind: pcsx2`, `slot` 7, `ps2_states: pine`,
    `steps_ms`, `total_ms`, `within_budget`, `reason` when restarted) and `ports_set` (`source: relaunch`); the
    response's `relaunch` adds `reason` (only PS2 sets it).
  - **Never a dead session:** every failure lands on a running title, except both launches failing (B54's ended path,
    unchanged).
- **`.gitignore`:** `PrivyHub-Import/` (a hand-copied stick folder anywhere in the repo). `data/import/` was already
  ignored by `data/`. `git check-ignore -v` in the tree: both, plus `tools/PrivyHub-Import/…`, `data/import/journal.json`
  and a `games/ps1/.import-*` part (`b57_2026-11-08/git_check_ignore.txt`).

## 2. Tests (`tests/relaunch_ports/test_b57.py`, 9; B51's PINE socket double and B52's fake window / log on the real `EmulatorManager`)

- **The full sequence** (`launch` faked as a new PCSX2 whose per-launch log gains `ELF Loading:` after 6 s of running):
  the calls in order — pause, save, stream stop, stop, launch(4), resume, load(the `.07.p2s`), pause, stream start;
  PINE `[6][0x09][7]` then `[6][0x0A][7]` and nothing else (**slots 8 / 9 untouched**: only the `.07.p2s` exists);
  SIGTERM sent; the launch's `[Pad]` `MultitapPort1 true`; `state: loaded`, `kind: pcsx2`, `landed_ports` 4; no
  `settle`; the load step ≥ 5.5 s (it held for the boot); `ports_set` 4 / multitap / `relaunch`; the row's `slot` 7,
  `ps2_states` pine, `players_joined` 3, `within_budget`; both game-log lines; the game paused for the client's gate;
  **no slot index** (the Game State list unchanged).
- **A save failure** (PINE fail; no answer; the file never complete) → no refusal, `restarted`,
  `ps2_relaunch_save_failed`, no load sent, no resume.
- **A static picture** → `stop_clean` + `launch_clean` (4 ports again), `restarted`, `ps2_relaunch_picture_static`,
  the session active; **a TLB Miss** → `ps2_relaunch_picture_fault`.
- **The ELF never up** → `restarted`, `ps2_relaunch_load_failed`, no load, no second launch, `within_budget: false`
  recorded.
- **Unchanged:** the source-less running load is B55's slot 8 (its log line); a foreign source is refused before PINE;
  absent (`_ps2` None): no launch kind, and the relaunch save is B54's own path.
- **PS1 untouched:** B54's RetroArch tests unchanged and green (the order with the 1.0-s settle, the 7600-ms total, the
  refusals, the fallbacks).

## 3. For A (HOME-7 C20, `SESSION_B_DONE_2026-11-08U.md`)

A third pad holds in a PS2 game → "Setting up 4 players…" → the game back where it was; the `relaunch_ports` row
`state: loaded`, `kind: pcsx2`, `slot` 7, `steps_ms` (save ~500, launch + load ~6000-9000), `total_ms` against 15 s; the
game log's `PS2 relaunch save: slot 7 …` / `PS2 relaunch load: slot 7 … picture ok`; PCSX2's own `Loaded state from
slot 7.` after `ELF Loading:`.

## 4. Files

`b57_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `b57.diff` (= `b57_code.diff` + `b57_gitignore.diff`; `git apply --check` OK on the baseline), `applied_to_tree_at.txt`;
- `proof_flag_absent.md`, `git_check_ignore.txt`, `diff_check.txt` (both diffs reverse-apply on the tree);
- `tests_x3.txt`, `tests_in_the_tree.txt`, `tests_host_baseline.txt`, `tests_host_b57.txt`, `tests_mutations.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B57_PS2_RELAUNCH_STATE.md`.
