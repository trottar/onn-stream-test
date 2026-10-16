---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
---

# G5-S2 — the WAN adaptation rules, behind a flag

**Classification: BUILT behind `PRIVYHUB_WAN_ADAPTATION=1`; proved by
replay; NOT ADOPTED; nothing committed.** With the flag absent the ladder is
byte for byte as adopted:

- the four named runs' recorded decisions are reproduced exactly;
- HEAD's and the edited controller write identical rows.

With the flag present, the result is tabulated per rule, open loop, with
**no claim of improvement**. That is the live test's job. The live smoke
(LAN, 10 min, the flag on) and the first off-site run with it (G4-S2) are
**pending on the stream**.

- Task: `handoffs/G5-S2_WAN_ADAPTATION_RULES_TASK.md`, queue
  `QUEUE_2026-10-16C.md` item 1, session B, unattended. **Baseline
  `92e388e`.** The tree carried the user's uncommitted G-A1 / CL-B3 / G3-S3
  work, untouched (`g5_s2_2026-10-16/git_status_at_start.txt`).
- No companion restart, no stream, no game, no adb. Not touched:
  `~/.config/privyhub/`, the audit log, the drop-ins,
  `companion/session_identity.py` and `companion/overlay/`.

## 1. The design (written before the code)

`g5_s2_2026-10-16/design_written_before_code.md`, sha256 `683821f5…7d38`,
hashed at 18:50:47Z before the first G5-S2 code edit. In short:

- **The module:** `companion/wan_adaptation.py`. Its `WanRules` are pure.
  They classify with G5-S1's `classify_window` on the same client telemetry
  the ladder sees.
- **The hook:** one guarded build and one `if` in
  `LiveController.observe`.
- **At most one suggestion per report:** `hold`, `no_step_up`,
  `step_down` or `floor_4000`. It is applied only as a constraint:
  - a blocked increase is refused `wan_no_step_up`;
  - a forced one-rung decrease goes through the ladder's own `_decide`, so
    every existing gate applies: the hold-downs, the blackout, the guards
    (including the 60-s session age), the rate limit and the oscillation
    guard;
  - nothing else.
- **The rules:**
  - **R1:** `hold` for the 3-report blackout after a path event, then
    `no_step_up` until 90 reports after it.
  - **R2:** `latency-limited` or `starved` on 2 consecutive 5-report
    windows → one rung down.
  - **R3:** `capacity-limited` → one rung down, to 5000 on the LAN. At 5000
    on a remote path, after 60 reports of persistence (ROUTINE's down
    hold-down; no record set this number), `floor_4000`.
  - **R4:** "FEC switch: not implemented; the fixed 8+1 stays".
  - **R5:** an increase needs K consecutive `clean` windows, and a `lossy`
    window is not clean. K = 18 on the LAN (the ladder's 90 reports) and 36
    on a remote path.
- **Recording:** each suggestion is a `decisions.jsonl` row
  (`event: wan_suggestion`, `source: wan_rules`, the suggestion, the rule
  id, the window class, the path, `ladder_result`).

**Two findings while coding, disclosed:**

1. **The remote floor cannot be actuated.** The live actuator's validated
   ladder is 5000 / 5500 / 6000 / 7000
   (`LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS`), and it refuses other targets.
   `floor_4000` is therefore **recorded, never actuated**; no rule suggests
   below 4000. Actuating 720p/4000 needs an actuator change plus its own
   validation (C5-M3 screened the rung on transport only). Listed for the
   user.
2. **The ladder cannot tell a remote path from the LAN today.** The design
   said remote means "the native status's client address field, if
   present". The native status carries no client address (its keys were
   checked), and the ladder's context has none. So `path_class` defaults to
   LAN, and remote applies only when the context supplies `path_class` or
   `target_address`. Wiring that (the session's routing class from G3 →
   the ladder's context) needs the games plugin and is not session B's
   file. Listed as G5-S3. In the replay both readings are tabulated.

## 2. Verification

**Unit tests** (`tests_output.txt`):
`python3 -m unittest discover -s tests/wan_adaptation -v` → **23 OK**. By
rule:

- **the flag:** `1` only; the ladder's import is guarded (AST); the overlay
  block equals G3-S1's; the path class;
- **R1:** hold ×3, then `no_step_up` to 90 reports, then free; recovery and
  overlay changes count as events; never at the top rung;
- **R2:** one latency window is not enough and two are; `starved` (stale
  drops); not below the floor;
- **R3:** a step down; nothing at the LAN floor; the remote floor exactly
  at the persistence, recorded with target 4000 and never below it;
- **R4:** no FEC suggestion;
- **R5:** K = 18 LAN and 36 remote, exactly; `lossy` is not clean;
- **precedence:** a step down beats a hold;
- **with the real `LivePolicy`:**
  - no suggestion means events identical to the plain ladder;
  - an increase the plain ladder takes is blocked under R5
    (`wan_no_step_up`), and the instance wrapper is removed afterwards;
  - a forced step down 7000 → 6000 labelled `wan_rules`, then refused by
    the ladder's own hold-down;
  - the session-age guard applies;
  - one suggestion per tick;
  - never below 5000;
  - a new session resets the rules.

**One unit test caught a bug before the record, disclosed.** With under one
window of history, `tick` returned `none`, so R5 would not have blocked an
increase that early. The ladder cannot increase that early anyway (it needs
a 90-report window and 60 s). The rule now returns `no_step_up` (R5.1)
there.

**The regression suites** (`tests_regression.txt`):

| suite | result |
| --- | --- |
| `tests/overlay` (G1) | 17 OK |
| `tests/session_identity` (G3) | 80 OK |
| `tests/wan_telemetry` (G5-S1) | 18 OK |
| the ladder's own `tools/test_adaptive_bitrate_live.py` (with the hook present) | 126 OK |

**The replay** (`replay.py` → `replay_output.md`, `replay_tables.json`,
`replay_console.txt`). Each run's whole session is taken from the live log;
the run's `decisions.jsonl` starts mid-session, with a 46-report window
already held. Recovery's state per report comes from the recovery logs.

| run | reports | recorded decision / state events | flag absent: recorded decisions | flag absent: controller HEAD vs edited |
| --- | --- | --- | --- | --- |
| e4_s4b run3 (lossy) | 639 | 98 | **exact** | **identical** (738 rows) |
| e4_s4b run2 (cleanest) | 643 | 136 | **exact** | **identical** (780 rows) |
| cl_b3 run1 (today's best link) | 343 | 70 | **exact** | **identical** (414 rows) |
| e4_s4 E1-CONC_flag run1 (grab bursts; 2 transitions) | 636 | 99 | **exact** | **identical** (738 rows) |

What each column compares:

- **"Exact":** every recorded sample row's decision fields (disposition,
  clean, the window counts, state, reason, level, blackout, hold-downs,
  escalation) and every recorded decision / state / SSRC event are
  reproduced key for key.
- **The controller comparison:** HEAD's `adaptive_bitrate_live.py` (from
  git) and the edited one are driven through `observe` /
  `note_recovery_restart` with a synchronous actuator, a temporary log and
  the log's own clock. Rows are compared apart from `at_utc` and the
  actuation duration.
  - The first pass differed on run3 in one field (`restart_gaps_ms` 19 vs
    20). That was HEAD against HEAD too: `note_recovery_restart` reads the
    real monotonic clock.
  - The harness now gives both controllers the replayed clock. After that,
    all four were identical (disclosed).

**Flag present, open loop** (later reports are the recorded ones). Rules
counted per tick. LAN, as recorded:

| run | ticks with a suggestion | by rule | ladder decisions changed | blocked increases | forced step-downs (taken / refused) | R5 let the rung back | remote floor would engage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| e4_s4b run3 (lossy) | 213 | R1.2 82, R2.1 6, R3.1 10, R5.1 115 | 1 | 34 | 1 / 1 | no | no |
| e4_s4b run2 (cleanest) | 0 | — | 0 | 0 | 0 / 0 | n/a (never below 7000) | no |
| cl_b3 run1 | 0 | — | 0 | 0 | 0 / 0 | n/a (never below 7000) | no |
| E1-CONC_flag run1 | 247 | R1.1 5, R1.2 86, R3.1 5, R5.1 151 | 1 | 1 | 0 / 1 | no | no |

The same inputs read as a remote path give the same table. The remote
reading did reach the rules (every row says `remote`), but it changed no
outcome:

- no run reached 5000, so the floor had nothing to do;
- R5 blocked every increase under both K = 18 and K = 36.

**What the table says, plainly:**

- On the two clean links the rules said nothing: at 7000 no block applies,
  and no window was capacity- or latency-limited.
- **run3:** the rules forced one step down, 7000 → 6000 at 890 s (R2.1 on
  the `starved` class, i.e. stale output drops; labelled `wan_rules`). One more was refused by a guard (recovery not PLAYING). The
  rules then blocked every increase for the rest of the run: run3 is
  `lossy` throughout, and a lossy window is not clean (R5.3). The recorded
  ladder stayed at 7000.
- **CONC:** the ladder's own `capacity_mild` took 7000 → 6000 at 605 s, as
  recorded, on the same tick as R3.1. The recorded increase back to 7000 at
  1096 s **was blocked** by R5, and the session stayed at 6000.
- **On the LAN, R5 is stricter than the ladder's own 85-of-90.** It needs 18
  consecutive clean windows, and a window with one dropped frame or a little
  loss is not clean. Whether that is right is for the live smoke to say, not
  this replay.

## 3. For the user

- **Live smoke (session A, pending on the stream):** add the drop-in
  `Environment=PRIVYHUB_WAN_ADAPTATION=1`, restart, run one 10-min LAN
  PS1-STREAM, read the `wan_suggestion` rows in the ladder's log, then
  remove the drop-in and restart. Then the first off-site run with it (G4-S2).
- **To decide:**
  - Actuating the remote floor 720p/4000 (an actuator change plus its own
    validation; today it is recorded only).
  - G5-S3: give the ladder the session's routing class, so "remote" is
    known live.
  - Whether R5's strictness on the LAN is wanted.

## 4. Files; disclosures

- **`g5_s2_2026-10-16/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `design_written_before_code.md` / `.sha256`;
  - `g5_s2.diff`: the ladder's hook, the rules document, G5-S2's ROADMAP
    hunk only, the new module and the tests;
  - `tests_output.txt`, `tests_regression.txt`;
  - `replay.py`, `replay_output.md`, `replay_tables.json`,
    `replay_console.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G5-S2_WAN_ADAPTATION_RULES.md`. Not written:
  `CURRENT.md`, `CURRENT_HANDOFF.md`, `KNOWN_ISSUES.md`, `PATCH_INDEX.md`.
- **Read only:** the live log (`logs/games/adaptive_bitrate_shadow.jsonl`
  and archives), the recovery logs, the run directories. The replay writes
  temp files only (`g5_s2_head_*`, `g5_s2_ctl_*` under the system temp
  directory; left in place). Nothing deleted, nothing fetched.
- No sudo, no nft, the Opal untouched. Git status:
  `logs/g5_s2_git_status.txt`.
