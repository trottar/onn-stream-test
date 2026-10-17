---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d
---

# G5-S3 — the remote ladder, behind a flag

**Classification: BUILT behind `PRIVYHUB_REMOTE_LADDER=1`; proved by replay and in
process; NOT ADOPTED; unvalidated live; nothing committed.** The flag closes
G5-S2's two gaps:

- the live ladder's context carries the session's routing class (`path_class`);
- on a remote path only, the ladder and its actuator can use 720p/4000. Nothing
  goes below 4000, and the LAN never uses it.

With the flag absent, everything is byte for byte as today:

- the actuator: HEAD vs edited, 200 of 200 cases identical;
- the games plugin's stream start: 3 of 3 identical;
- G5-S2's own replay, re-run: exact, identical, and its tables equal.

**With the flag present, no replayed run reaches 4000.** That includes G4-S1's
run 1 (§3): its 2,259 loss/min is **one report of 21,407 lost packets**, the
sequence jump after its 24.5-s recovery pause. It was not sustained loss.

- Task: `handoffs/G5-S3_REMOTE_LADDER_TASK.md`, queue `QUEUE_2026-10-17.md`
  item 1, session B, unattended. **Baseline `1dab25d`.**
- The tree's uncommitted files at the start were left untouched
  (`g5_s3_2026-10-17/git_status_at_start.txt`). Session A's G8-S1 resume files
  appeared during the session; none of them was touched.
- No companion restart by this session, no stream, no game, no adb. Not
  touched: `~/.config/privyhub/`, the audit log, the drop-ins,
  `companion/session_identity.py`, `companion/overlay/`.

## 1. The design (written before the code)

`g5_s3_2026-10-17/design_written_before_code.md`, sha256 `8ccc8267…acff2`,
hashed at 00:21:36Z, before the first G5-S3 code edit. In short:

- **The module:** `companion/remote_ladder.py`, one shared `RemoteLadder` per
  process. The class is `lan` by default (G5-S2's default).
- **The class:** set at every `native-stream-start` from the target the games
  plugin is handed, so a re-setup updates it. Only the class is kept, never the
  address.
- **The ladder:** with the flag and a `remote` class, the policy's ladder is
  `4000 / 5000 / 5500 / 6000 / 7000`, and the actuator's validated list gains
  4000. Otherwise both are today's, and 4000 is refused as today.
  - `LivePolicy` is not edited. The 4000 rung is reached by its own code: the
    one-rung `capacity_mild` step from 5000, and G5-S2's `floor_4000` through
    `_decide`.
  - `TARGET_KBPS` is unchanged, so a strict FALLBACK still names 5000.
- **The hooks:** each is a module global built only under the flag (the import
  inside the `if`) plus one `if` at the site:
  - the ladder's context builder `_ctx` and its `_write`;
  - the games plugin's `native-stream-start`;
  - the probe's `_run_c3_linux_bitrate_cycle` (the validated list as a local);
  - `wan_adaptation.feed` (`floor_4000` forced like `step_down`).
- **Recorded:**
  - `path_class` on every ladder row;
  - `remote_rung: true` on any decision or result row that moves to or from
    4000;
  - the result row also carries the decision's `reason` / `trigger` /
    `wan_rule`, matched by `decision_sequence`;
  - `floor_actuatable` on `floor_4000` suggestions.

**A correction to the handoff, written in the design §0 before the code:**

- **What the handoff assumed.** The games plugin does not hold G3's
  `routing_evidence` as a field.
- **What the plugin actually has.** Its `client_ip` with identity v2 on.
  That is `client_target`: the declared endpoint whose class matches the
  request's routing class (G3-S3's `endpoint-class-mismatch` rule).
- **So the class is G3's.** G3's own overlay test over that target equals the
  stream-start request's routing evidence. The design uses that.
  - The networks are built from integers.
  - A test asserts they equal `session_identity.OVERLAY_NETWORKS`.
  - A test asserts that G3's `RoutingClassifier` and this module agree on
    overlay, LAN, loopback, IPv4-mapped and unparsable inputs.
- **The alternative, not done.** Carrying the evidence as a field would need
  `session_identity.py` or the service's dispatch, which are not this
  session's files. Listed for the user.

## 2. Verification

**Unit tests** (`tests_output.txt`): `python3 -m unittest discover -s tests/remote_ladder -v` → **26 OK**.

- **The flag:**
  - only `1` turns it on;
  - this process has none;
  - the imports are guarded (AST, all three modules);
  - the games plugin has exactly one guarded reference;
  - a child interpreter with the real variable shares one instance across the
    ladder, the rules and the probe. With `0`, nothing is imported.
- **The class:**
  - G3's networks and classifier agree with this module;
  - the class is set at every start, and a re-setup over the LAN reads `lan`;
  - no address is kept;
  - the class never raises;
  - the games plugin's real `handle_post_request` sets it with the flag and does
    nothing without it.
- **The context:**
  - without the flag the keys are as today;
  - with it, the class and the ladder follow the setup, including with the
    1080p rung;
  - G5-S2's `path_class(ctx)` reads `remote`.
- **The policy (the real `LivePolicy`):**
  - remote: 7000 → 6000 → 5500 → 5000 → 4000, then the hold-down and
    `at_floor` at 4000, never lower;
  - LAN (flag on, and flag absent): the floor stays 5000;
  - the strict trigger still names 5000;
  - the increase from 4000 goes to 5000.
- **The actuator** (C3-F1's fake manager, the real cycle):
  - remote: 5000 → 4000, recovery's restart at 4000, then 4000 → 5000;
  - the 4000 argv is the 5000 argv with only `-b:v / -maxrate / -bufsize`
    changed;
  - LAN and flag absent: 4000 is refused (`unsupported_validated_bitrate`), and
    a stream left at 4000 is not restarted or moved;
  - 3000 and 3500 are refused everywhere;
  - `NativeStreamManager.adaptive_level_transition(4000)` routes to the
    validated transition (`native_stream.py` unedited).
- **G5-S2's `floor_4000`:**
  - flag absent: recorded only, and the stream stays at 5000;
  - flag on, remote: one transition 5000 → 4000 labelled `wan_rules` /
    `R3.2`, through the gates;
  - flag on, LAN: no floor suggestion at all.
- **The rows** (the real `LiveController`):
  - every row carries `path_class`;
  - the 4000 transition and its `transition_done` carry `remote_rung` and the
    trigger;
  - on the LAN the flag adds only the class and the decision copy;
  - flag absent: no new key.

**Flag absent, byte for byte** (`flag_absent_proof.py` → `flag_absent_output.md`):

| what | how | result |
| --- | --- | --- |
| the actuator | HEAD's (from git) vs the edited `c3_linux_actuator_probe.py`, 4 entry points × 8 current levels × 8 targets (3000…12600, incl. 4000); payload, argv, exception, level after | **200 / 200 identical**; 40 cycles ran and the rest were refused identically; of the 46 cases touching 4000, **0 accepted** |
| the games plugin | HEAD's vs the edited `handle_post_request("native-stream-start")`, same stubs, plus `_adaptive_bitrate_context` | **3 / 3 identical** (started; game inactive; start fails) |
| the ladder | G5-S2's `replay.py`, unchanged, re-run (`g5_s2_replay_rerun/`) | four runs' recorded decisions **exact**; HEAD vs edited controller **identical** (738 / 780 / 414 / 738 rows); its WAN-rules tables **equal** to G5-S2's recorded ones |

**Regression** (`tests_regression.txt`):

- `tests/overlay` 17, `tests/session_identity` 80, `tests/wan_telemetry` 18,
  `tests/wan_adaptation` 23, `tests/remote_ladder` 26: all OK;
- `tools/test_adaptive_bitrate_live.py` 126 OK;
- `tools/test_c3_f1_recovery_restart.py` 7/8. The one error
  (`restart_encoder=(` not found in `games.py`) is **pre-existing at HEAD**, as
  recorded since C5-M5.

## 3. The replay, flag present (`replay.py` → `replay_output.md`, `replay_tables.json`)

**How it ran:**

- The edited `LiveController` ran in process, its globals set as the flag would
  set them, on the replayed clock.
- The actuator was the **real encoder-only cycle** on C3-F1's fake manager, so
  anything the probe refuses is refused here too.
- The stream sat at the level the controller chose.
- The reports are the recorded ones (open loop).

**G4-S1's sessions** came from the live log. Their `path_class` comes from the
routing evidence of the last `token_issued` before each session (G4-S1's
reduced audit):

- run 1: `remote`, two sessions;
- run 2: `remote` until the toggle, then `lan` after the 23:15:01Z LAN setup.

Flag absent, all six sessions' recorded decisions were reproduced exactly (§0 of
the output).

| run | path_class | rules off | rules on |
| --- | --- | --- | --- |
| G4-S1 run 1 | remote (as set up) | 7000 throughout; 4000 not reached | the same; **0 suggestions** |
| G4-S1 run 2 | remote, then lan | 7000 throughout | the same; 0 suggestions |
| e4_s4b run3 (lossy) | lan / read as remote | 7000 | 7000 → 6000 (`wan_rules`, R2.1); 4000 not reached |
| e4_s4b run2, cl_b3 run1 | lan / read as remote | 7000 | 7000 |
| E1-CONC_flag run1 | lan / read as remote | 7000 → 6000 `capacity_mild`, back to 7000 (as recorded) | 7000 → 6000; the increase blocked by R5 |

Checks over all 24 replays:

- every row carries `path_class`;
- nothing below 4000;
- never 4000 on a `lan` path;
- no `floor_4000` tick anywhere (no run reached 5000).

**Why G4-S1 did not move: what the files show.** This is not G5-S2's
assumption.

| run | fresh reports in the window | lost (sum) | largest single report | when | without it |
| --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 | 282 | 21,463 | **21,407** (`waiting_for_idr` true, 1 forward gap) | 22:56:12.6Z, the first report after the 24.5-s controller-silence pause | **56 (6.0 / min)** |
| G4-S1 run 2 | 214 | 2,026 | 1,871 | 23:15:47.6Z, the first report of the LAN-set-up stream after the toggle | 155 (21.7 / min) |

- **The ladder's evidence windows.** In both runs' remote sessions the median
  fps was 59.8 and the median loss 0 per report. **No 5-report window** had
  ≥ 50 lost on ≥ 3 of 5, or fps < 57 on ≥ 4 of 5.
- **The big report did not count.** It was a resync (`waiting_for_idr`), which
  the ladder never takes as evidence.
- **So 4000 is not what was missing.** G4-S1 run 1's "2,259 post-FEC loss/min
  at 7000 while the ladder held 7000" is the window's mean, dominated by one
  resync jump. Neither the ladder nor G5-S2's rules had a decrease signal to
  act on.
- **Separate questions.** A remote session's data volume (G4-S1 §9: 5.1 GB/h at
  7000) is G5-S4's cap. The pause itself is a recovery question.
- Reported as read; G4-S1's record is not rewritten.

**No claim** that any run would have played better at another rung. Where 4000
is first seen is G4-S2's job.

## 4. For the user

- **Pending on the stream (session A):**
  - **The LAN smoke:** the drop-in `Environment=PRIVYHUB_REMOTE_LADDER=1`, a
    restart, one PS1-STREAM. Read: every ladder row's `path_class` is `lan`, and
    the ladder is unchanged. Then remove the drop-in and restart.
  - **Then G4-S2:** the first off-site run with G5-S3 (+ G5-S2) on, where 4000
    can first be seen.
- **To decide:**
  - Whether the gate should hand the plugin `routing_evidence` as a field
    (§1's alternative; `session_identity.py` / the service).
  - **G4-S1's loss reading (§3).** The off-site case for a lower rung is not
    shown by G4-S1's files. Whether a `lossy`-only remote window should step
    down at all is the R4 question G5-S2 left open (today: no).
  - 720p/4000 has passed transport only (C5-M3). Its live validation
    (picture, the actuator's cycle at 4000 on the real encoder) is G4-S2's.

## 5. Files; disclosures

- **`g5_s3_2026-10-17/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `design_written_before_code.md` / `.sha256`;
  - `g5_s3.diff`: the four hooks, the new module, the tests, the rules
    document's and ROADMAP's G5-S3 hunks;
  - `tests_output.txt`, `tests_regression.txt`;
  - `flag_absent_proof.py`, `flag_absent_output.md`, `g5_s2_replay_rerun/`;
  - `replay.py`, `replay_output.md`, `replay_tables.json`,
    `replay_console.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G5-S3_REMOTE_LADDER.md`.
- `docs/WAN_ADAPTATION_RULES.md`: the status line, and R3.2's and R5's G5-S3
  lines.
- ROADMAP §G5: the G5-S3 paragraph.
- `logs/g5_s3_git_status.txt`.
- Not written: `CURRENT.md`, `CURRENT_HANDOFF.md`, `KNOWN_ISSUES.md`,
  `PATCH_INDEX.md`.
- **Disclosed: the companion runs this code with the flag absent.** Session
  A's G8-S1 driver restarts the companion once per cell during this session.
  - Each restart loads the edited `adaptive_bitrate_live.py`, `plugins/games.py`
    and `wan_adaptation.py`, and the probe at its first transition. None of them
    carries the flag.
  - The live log after the edits shows the companion's rows with no
    `path_class` (inert, as proved).
  - The edits were made before the first restart that loaded them (the hooks at
    about 00:22-00:24Z; restarts seen at 00:25:37Z and later). Each file stayed
    importable throughout.
- **Disclosed: a side effect of this session's own testing.** Twice (a smoke
  import at about 00:24Z, and the first test run at about 00:25:14Z), importing
  the `plugins` package constructed every plugin in a test process.
  - `GamesPlugin()` then rewrote `logs/games/game_metadata_startup_reconcile.json`
    and `.txt` with `SKIPPED_CURRENT`: no metadata update invoked, nothing
    fetched.
  - The companion's own restarts rewrite that file, and it has since been
    rewritten by them.
  - No other plugin constructor writes. The test now loads `plugins/games.py`
    alone and constructs nothing.
- **Read only:** the live log (`logs/games/adaptive_bitrate_shadow.jsonl` and
  archives), the recovery logs, the run directories, `g4_s1_read.json`.
- Temp files are left in place under the system temp directory:
  `g5_s3_absent_*`, `g5_s3_replay_*`, `g5_s3_test_*`, `g5_s3_rows_*`, and G5-S2's
  `g5_s2_head_*` / `g5_s2_ctl_*` from its re-run.
- Nothing deleted, nothing fetched. No sudo, no nft, the Opal untouched. No
  address or identifier in any file: addresses in tests are built from
  integers, and the plugin comparison masks its target.
