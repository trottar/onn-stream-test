---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d (with G5-S3 uncommitted beside it, which this builds on)
---

# G5-S4 — the remote rung cap, a data saver, behind a flag

**Classification: BUILT behind `PRIVYHUB_REMOTE_RUNG_CAP=<kbps>`; proved in process
and by replay; NOT ADOPTED; unvalidated live; nothing committed.**

- **What it is:** the user's choice, never automatic.
- **When it is active:** only when the value is a rung of G5-S3's remote list
  and `PRIVYHUB_REMOTE_LADDER=1` is set. Otherwise the cap writes one row saying
  so, and does nothing else.
- **What it does, on a remote path:**
  - the ladder's target is clamped to the cap;
  - the stream moves down to the cap through the ladder's own gates;
  - an increase never goes above the cap;
  - every step below the cap is the ladder's own.
- **On the LAN:** nothing.
- **Flag absent:** byte for byte as today.
  - G5-S3's in-process proof re-run: PASS.
  - G5-S3's replay re-run: identical.
- **Replay:** over G4-S1's runs at 4000 and at 5000, each remote session ran
  about 60 s at 7000, then at the cap.
- **Data per hour at the cap:** given as arithmetic only (§3).

- Task: `handoffs/G5-S4_REMOTE_RUNG_CAP_TASK.md`, queue item 2, session B,
  unattended. **Baseline `1dab25d`**, with G5-S3 uncommitted (this builds on it).
  - `g5_s4_2026-10-17/predecessor_sha256.txt` equals G5-S3's `after_sha256.txt`
    for every file both touch.
- No companion restart, no stream, no game, no adb. Not touched:
  `~/.config/privyhub/`, the audit log, the drop-ins,
  `companion/session_identity.py`, `companion/overlay/`.

## 1. The design (written before the code)

`g5_s4_2026-10-17/design_written_before_code.md`, sha256 `0ef2f5c8…7a37`, hashed
at 00:37:47Z, before the first G5-S4 code edit.

**How the design reads the handoff (§0, disclosed).** The handoff says both "a
session starts at the cap or below" and "the cap never forces a step-down by
itself".

- **The problem:** every stream starts at 7000 (C1), and a data saver that never
  moves a clean link saves nothing.
- **The reading:** the cap moves the stream *down to the cap and never
  further*. Below the cap every step is the ladder's own, and the cap never
  lowers the floor (every valid cap is ≥ 4000).
- **The cost:** the move goes through every gate, the 60-s session guard
  included, so a session's first minute runs at 7000. That is about 86 MB at
  G4-S1's 11.42 Mbit/s.
- **Not done:** starting the encoder at the cap would change the stream start,
  not the ladder. Listed for the user.

**The rules:**

- **Valid values:** 4000 / 5000 / 5500 / 6000 / 7000.
- **Anything else** gives one `remote_cap_config` row with `active: false`,
  `reason: not_a_remote_rung`. A non-numeric value is recorded as
  `non-numeric`, never echoed.
- **Valid without G5-S3's flag:** one row, `reason: remote_ladder_flag_absent`.
- **Active:** one row, `active: true`, `cap_kbps`.
- **The clamp** (in `LivePolicy._decide`, after the target is chosen):
  - a decrease aimed above the cap goes to the cap;
  - an increase aimed above the cap is refused `remote_cap`;
  - anything at or below the cap is the ladder's own.
- **The move** (in `LiveController.observe`, after the feed): on a remote path
  with the stream above the cap, on an evaluated report where the ladder decided
  nothing, one ROUTINE decision (trigger `remote_cap`) through `_decide`, aimed
  at the cap. Its reason is `remote_cap`.

**Found while coding, disclosed.** Design §3 said a blocked increase would be
"logged once per run of identical refusals".

- **What happens instead:** the ladder resets its refusal key on every report
  that carries no evidence (`adaptive_bitrate_live.py`, the line after the
  FALLBACK/ROUTINE branch). So a blocked increase is written **every report**
  while the increase window is full: 278 rows in 400 clean reports in the unit
  scenario, 111 in G4-S1 run 1's replay.
- **Precedent:** G5-S2's `wan_no_step_up` already behaves this way.
- **Consequences:** "every clamp in `decisions.jsonl`" holds literally. The cost
  is about one more row per report while capped on a clean link, roughly
  doubling the log's growth then.
- Not changed. The ladder's dedupe is not this task's.

## 2. Verification

**Unit tests** (`tests_output.txt`):
`python3 -m unittest discover -s tests/remote_cap -v` → **16 OK**.

- **The flag:**
  - absent or empty → none;
  - valid at each rung, spaces stripped;
  - invalid: 3000, 4500, 8000, 12600, `-4000`, `4000.0`, text, each with
    its row;
  - G5-S3 absent → inactive;
  - the guarded import (AST);
  - child interpreters with the real variables: none, cap only, both, and an
    invalid cap with G5-S3.
- **The effect** (the real `LivePolicy`, the order of the report path):
  - **the LAN:** unaffected;
  - **an inactive cap:** identical to no cap, both without G5-S3 and with an
    invalid value under G5-S3;
  - **on a clean remote link, at each cap 4000 / 5000 / 5500 / 6000:** one move
    7000 → cap (wish 7000, capped to the cap), after `guard` refusals for the
    first 60 s; the increase is blocked above the cap; the level stays at the
    cap;
  - **cap 7000:** no move;
  - **a 5000 cap with mild capacity from the start:**
    - the ladder's 6000 is clamped to 5000;
    - then the ladder's own 5000 → 4000;
    - then 4000 → 5000 allowed, never above 5000;
  - **a strict FALLBACK at 7000 under a 4000 cap:** clamped 5000 → 4000;
  - **G5-S2's `floor_4000` under a 5000 cap:** lands on 4000 (`wan_rules`,
    R3.2);
  - **a recovery full start back at 7000:** the move again.
- **The rows** (the real `LiveController`):
  - the config row exactly once;
  - the move's transition row carries `source / wish_kbps / capped_kbps /
    cap_kbps / path_class / reason`, and its `transition_done` carries the
    decision;
  - inactive caps: their one row and nothing else;
  - the LAN: no clamp.

**Flag absent, byte for byte** (`flag_absent_output.md`):

- **G5-S3's `flag_absent_proof.py` re-run** with the cap code present
  (`g5_s3_proof_rerun/`):
  - the actuator: 200 / 200 identical;
  - the games plugin: 3 / 3 identical;
  - G5-S2's replay: exact, HEAD vs the edited controller identical, and the
    WAN tables equal.
  - → PASS.
- **G5-S3's `replay.py` re-run** with G5-S3 on and the cap absent
  (`g5_s3_replay_rerun/`): `replay_tables.json` equal (20 entries) and
  `replay_output.md` byte-identical.

**Regression** (`tests_regression.txt`):

- `tests/overlay` 17, `tests/session_identity` 80, `tests/wan_telemetry` 18,
  `tests/wan_adaptation` 23, `tests/remote_ladder` 26 (after the `annotate`
  change), `tests/remote_cap` 16: all OK;
- `tools/test_adaptive_bitrate_live.py` 126 OK;
- `tools/test_c3_f1_recovery_restart.py` 7/8, the pre-existing error.

## 3. The replay (`replay.py` → `replay_output.md`, `replay_tables.json`)

G5-S3's harness, with the controller also carrying a `RemoteCap` that shares the
`RemoteLadder`. The sessions and their setup class are G5-S3's: run 1 remote;
run 2 remote, then the LAN setup. Open loop on the reports, recorded at 7000.

| run | cap | reports on the remote path at 7000 / cap | the move | blocked increases (rules off / on) | the LAN part |
| --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 | 4000 | 30 / 298 (91 % at the cap) | session 1 at 61 s; session 2 (after the recovery pause's reset) at its first evaluated report, 323 s elapsed | 111 / 0 | — |
| G4-S1 run 1 | 5000 | 30 / 298 | the same | 111 / 0 | — |
| G4-S1 run 2 | 4000 | 28 / 124 (82 %) | at 61 s | 32 / 0 | 105 reports, all at 7000 (no effect) |
| G4-S1 run 2 | 5000 | 28 / 124 | at 61 s | 32 / 0 | the same |

- No other transition happened.
- **The rules-on column reads 0** because G5-S2's R5 refuses those increases
  first (`wan_no_step_up`).
- Checks:
  - every move is on a remote path;
  - no remote transition goes above the cap;
  - the LAN stays at 7000.
  - → PASS.

**The data per hour, as arithmetic (not a result).** GB/h = Mbit/s × 0.45.

| level | wire rate | source | GB/h | overlay, scaled ×(11.42/8.60) | GB/h | overlay, +2.82 | GB/h |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7000 | 8.60 Mbit/s | C5-M3 measured | 3.87 | 11.42 (G4-S1 measured) | **5.14** | 11.42 | 5.14 |
| 5000 | 6.20 | **L1 estimate; no wire measurement exists** | 2.79 | 8.23 | 3.70 | 9.02 | 4.06 |
| 4000 | 5.02 | C5-M3 measured | 2.26 | 6.67 | 3.00 | 7.84 | 3.53 |

- **Two arithmetic bases for the overlay at a lower rung.** The overlay's extra
  over C5-M3's wire figure (audio, control, the overlay's own overhead) is
  either proportional or constant. No record measures which.
- **Each run's replayed mix**, time-weighted with the first minute at 7000
  included:
  - run 1 at 4000: 2.41 / 3.20 / 3.68 GB/h by the three bases;
  - run 1 at 5000: 2.89 / 3.84 / 4.16;
  - run 2's remote part at 4000: 2.56 / 3.39 / 3.82;
  - run 2's remote part at 5000: 2.99 / 3.97 / 4.26.
- **What a capped stream would actually send** is for the first off-site run
  with the cap (G4-S2) to measure. **The picture at the cap is the user's
  judgement**, not a record's.

## 4. For the user

- **Pending on the stream:** the first off-site run with
  `PRIVYHUB_REMOTE_LADDER=1` and `PRIVYHUB_REMOTE_RUNG_CAP=4000` (drop-ins,
  then a restart).
  - Read: the ladder log's `remote_cap_config` row (`active: true`), the move's
    row about a minute in, and the overlay interface's tx.
  - You judge the picture.
- **To decide:**
  - Whether a session should start at the cap (an encoder-start change, §1)
    rather than move to it after the first minute.
  - Whether the per-report `remote_cap` / `wan_no_step_up` refusal rows should
    be deduplicated (§1).
  - The client-side setting (G3's Settings dialog) is session A's APK work, not
    built.

## 5. Files; disclosures

- **`g5_s4_2026-10-17/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `design_written_before_code.md` / `.sha256`;
  - `g5_s4.diff`: the cap's hooks (this task's lines of
    `adaptive_bitrate_live.py`, shown against G5-S3's after), `annotate`'s
    change, the new module and tests, the rules line and the ROADMAP paragraph;
  - `tests_output.txt`, `tests_regression.txt`;
  - `flag_absent_output.md`, `g5_s3_proof_rerun/`, `g5_s3_replay_rerun/`;
  - `replay.py`, `replay_output.md`, `replay_tables.json`,
    `replay_console.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G5-S4_REMOTE_RUNG_CAP.md`.
- `docs/WAN_ADAPTATION_RULES.md`: the G5-S4 line under R3.
- ROADMAP §G5: the G5-S4 paragraph.
- `logs/g5_s4_git_status.txt`.
- Not written: `CURRENT.md`, `CURRENT_HANDOFF.md`, `KNOWN_ISSUES.md`,
  `PATCH_INDEX.md`.
- The companion keeps running on the edited files across session A's G8-S1
  restarts, with neither flag; inert, as proved.
- Temp files under the system temp directory are left in place:
  `g5_s4_replay_*`, `g5_s4_rows_*`, and the re-runs' `g5_s3_*` / `g5_s2_*`.
- Nothing deleted, nothing fetched. No sudo, no nft, the Opal untouched. No
  address or identifier anywhere.
