---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 80f3fc4
---

# G8-S2 — the start rung, behind a flag

**Classification: BUILT behind `PRIVYHUB_START_RUNG=<floor|cap|kbps>`; proved in
process and by replay; NOT ADOPTED; unvalidated live; nothing committed.**

- **What it does:** a stream starts at the active list's floor, at G5-S4's cap, or at
  a named rung, instead of 7000. The ladder's own increase rule climbs from there.
- **Flag absent:** byte for byte as today.
  - The first-target handler is identical to HEAD.
  - G5-S2's and G5-S3's replays re-run identical over the sessions the ladder's log
    still holds. One of G5-S2's four sessions has rotated out (§2, disclosed).
  - HEAD's and today's controllers agree over 70 sessions.
- **The cap proof (in process, through the real FEC sender and the shim):**
  - **5000 under cap-6000 does not fit cleanly.** It enters at about 6.1 Mbit/s, and
    1.8-2.4 % is tail-dropped.
  - **4000 under cap-4500 is over that cap,** as written beforehand: it enters at
    about 4.65 Mbit/s, and 5.5-5.8 % is dropped.
  - No claim about PLAYING.

- Task: `handoffs/G8-S2_START_RUNG_TASK.md`, session B, unattended, after session A's
  LAN smoke had exited (`G5_S3_LAN_SMOKE_2026-10-17.md` present, no `e3_flag.conf`).
  **Baseline `80f3fc4`.**
  - A's uncommitted files were left as they were (`g8_s2_2026-10-17/git_status_at_start.txt`):
    its record and directory, its lines in ROADMAP §G5, `WAN_ADAPTATION_RULES.md` and
    `CURRENT.md`.
  - ROADMAP got one §G8 paragraph from B, in another section.
- No companion restart, no stream, no game, no adb. Not touched: `~/.config/privyhub/`,
  the audit log, the drop-ins, `companion/session_identity.py`, `companion/overlay/`.

## 1. The design (written before the code)

`g8_s2_2026-10-17/design_written_before_code.md`, sha256 `0bfd56ad…7063`, hashed at
16:35:42Z, before the first G8-S2 code edit.

**Where the first target is chosen (§0).** The ladder does not choose it. Every
`NativeStreamManager.start` does two things:

- `_stop_locked` resets `_active_bitrate_kbps` to the profile's 7000;
- `_start_linux_locked` builds the encoder argv at 7000 by default.

The ladder follows the stream: the session's reset, then the first report's
`level_sync`. So the hook sits at that one argv call.

**The flag:**

- **The active list.** It is decided per start from the start's own target.
  - G5-S3's remote list (4000-7000) applies when G5-S3's flag is in force and the
    target is overlay-class, under G5-S3's own `routing_evidence_of`. G5-S3's plugin
    hook runs only after the start, so the start classifies for itself.
  - Otherwise the ladder's validated 5000-7000 applies.
- **The values:**
  - `floor` → the lowest rung of the list;
  - `cap` → G5-S4's cap where G5-S4 applies (active, remote), else `floor`;
  - `<kbps>` → that rung if it is in the list; otherwise `floor`, logged once;
  - anything else → ignored (today's 7000), logged once.
- **The argv.** A rung below 7000 gets exactly the ladder's own transition argv for
  that rung (`-b:v / -maxrate / -bufsize`); a test asserts this. A chosen 7000 leaves
  the call unchanged.
- **Every start.** The flag applies to every `native_stream.start`, recovery's full
  start included. The ladder's escalation bookkeeping still labels a full start's
  level 7000. Not changed ("nothing else in the ladder"); listed.

**The record.** The start rung, its source, the request, the active list and the path
class go on the session's first `sample` row after each start.

- That needs a second guarded `if`, in `LiveController._write`, because the native
  stream does not write the ladder's log. It annotates only.
- A run's `decisions.jsonl`, as the suite extracts it (the window after the warm-up),
  will not hold that row. The ladder's log does.

**The climb (§3, arithmetic from the constants).** The first step comes at report 90,
then one every 93 reports:

| start | to 7000 |
| --- | --- |
| 5000 | 276 reports ≈ 9.2 min |
| 4000 | 369 reports ≈ 12.3 min |
| 4000 with G5-S2's R5 on | about 459 reports ≈ 15.3 min |

The unit test reproduces 90 / 183 / 276 (/ 369) exactly, in process.

**The wire arithmetic, written before the proof (§4).** The ratio is 8.25 / 7.0 ≈
1.179. The shim carries the video hop only (video + parity), so "and audio" does not
enter it.

| rung | ratio prediction |
| --- | --- |
| 7000 | 8.25 Mbit/s |
| 6000 | 7.07 |
| 5500 | 6.48 |
| 5000 | 5.89, under cap-6000 → drop ≈ 0 |
| 4000 | 4.71, **over cap-4500 by ≈ 4.8 % → drop ≈ 4.5 % ("about 4 %")** |

A second prediction came from C5-M3's measured 4.83 Mbit/s at 4000: drop ≈ 6.8 %. The
design said `cap-4500` was not expected to pass even at 4000.

## 2. Verification

**Unit tests** (`tests_output.txt`): `python3 -m unittest discover -s tests/start_rung -v`
→ **17 OK**.

- **The flag:**
  - parsing, with invalid values;
  - the guarded imports (AST, both files);
  - a child interpreter with the real variable shares one instance.
- **The choice:**
  - `floor` on the LAN / remote, with G5-S3 off and on;
  - `cap` with a G5-S4 cap, without one, on the LAN (remote-only), and invalid;
  - a value in and out of the list, never below 4000;
  - 12600 → floor;
  - invalid → 7000, logged once;
  - no address kept.
- **The start** (the real `_start_linux_locked` on a stubbed manager):
  - absent → 7000;
  - `floor` → 5000 argv, level and status;
  - a chosen 7000 or an invalid value → today's argv exactly;
  - the start argv equals the actuator's own transition argv at 4000 / 5000 / 6000;
  - a second start (as recovery's full start calls it) → the rung again.
- **The record and the climb** (the real `LiveController`):
  - one `start_rung` annotation, on the first sample row;
  - `level_sync` to the rung;
  - none when absent;
  - the climb's report numbers as computed.

**Flag absent** (`flag_absent_proof.py` → `flag_absent_output.md`):

| what | result |
| --- | --- |
| the first-target handler: HEAD's (git) vs today's `_start_linux_locked`, same stubs, LAN- and overlay-class targets; the argv, the level, the payload, every stub call, the log | **identical** (7000k / 7000k / 7000k, 8 calls, both) |
| G5-S2's `replay.py`, unchanged code, over the held sessions | recorded decisions **exact**, HEAD vs today's controller **identical** (738 / 780 / 414 rows); its tables equal entry for entry (6 entries) |
| G5-S3's `replay.py`, unchanged code, G5-S3 on | its tables equal entry for entry (16 of 20; the missing 4 are the rotated session's); `replay_output.md` equal, with that session's rows removed |
| in addition: HEAD's vs today's `LiveController` over every session in the ladder's log | **70 sessions, 23,847 rows, 0 differing** |

**Disclosed: the ladder's log rotated.** The companion's own retention
(`LOG_MAX_BYTES` 4 MB, `LOG_KEEP` 3) rotated the log at 2026-10-17T03:57Z, during
G8-S1's night.

- The oldest archive, 2026-10-10 before 08:59Z, is gone.
- It held G5-S2's fourth session (e4_s4 E1-CONC_flag run 1, from 02:52Z). No copy exists
  in the evidence tree.
- So "re-run identical" holds for the three held sessions. The added 70-session
  controller comparison covers the hook more widely than the lost session did.
- Future replays of that run are no longer possible from the logs.

**Regression** (`tests_regression.txt`):

- `tests/` overlay 17, session_identity 80, wan_telemetry 18, wan_adaptation 23,
  remote_ladder 26, remote_cap 16, impairment 14, start_rung 17: all OK;
- `tools/test_adaptive_bitrate_live.py` 126 OK;
- `tools/test_e1_remote.py` 20 OK;
- `tools/test_c3_f1_recovery_restart.py` 7/8, the error pre-existing at HEAD.

## 3. In process against the shim's cap profiles (`cap_proof.py` → `cap_proof_tables.md`, `cap_proof.json`)

**The setup** (G8-P1's proof, extended): the real `NativeVideoFecRelay`, at its
default pacing → the shim `@post-fec` → a capture playing the client. 30 s per case.

- **The shim** was given to the relay directly, with **no log file**. The
  environment route makes the relay pass the repo root and append to
  `logs/impairment.jsonl`.
- **Two kinds of source:**
  - (a) synthetic frames at r / 7000 × 14,615 B, 60 fps;
  - (b) **the real encoder's recorded stream starts** from the evidence tree:
    `c3_l4_nft_night3_2026-09-30/frames.jsonl` @ 13:15:23Z and
    `c3_l4_nft_night1_2026-09-29/frames.jsonl` @ 15:20:34Z.
- **What the recorded starts are.** Per-second aggregates (frames, payload bytes, the
  largest frame and its instant), re-timed into frames and scaled by r / 7000 (CBR),
  which is an assumption. No per-frame series exists in the tree.
- **What they show:** the real encoder is at its steady 876.9 kB/s from its first full
  second, with no burst above the rate.

| cap | start | shim in, steady (kbps) | predicted drop (§4) | tail-dropped, steady | FEC recovered / unrecoverable groups | lost after FEC /min | complete frames | G5-S1 windows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cap-6000 | 7000 | 8,253-8,321 | 27.3 % | 30.1-30.5 % | 0 / 133-146 | 12,629-12,975 | 0.7-3.1 % | capacity-limited |
| cap-6000 | 5000 | 6,103-6,137 | 0 % | **1.8-2.4 %** | 1-7 / 0-2 | 2-328 | 95.9-99.9 % | clean / lossy |
| cap-6000 | 4000 | 4,635-4,676 | 0 % | 0 % | 0 / 0 | 0 | 100 % | clean |
| cap-4500 | 7000 | 8,252-8,318 | 45.5 % | 47.6-47.9 % | 176-208 / 88-99 | 18,399-18,692 | 0.3-1.4 % | capacity-limited |
| cap-4500 | 5000 | 6,103-6,138 | 23.6 % | 28.9-29.9 % | 208-230 / 0-7 | 4,238-4,784 | 1.5-4.7 % | capacity-limited |
| cap-4500 | 4000 | 4,635-4,675 | 4.5 % (C5-M3: 6.8 %) | **5.5-5.8 %** | 129-191 / 0-2 | 646-731 | 82.1-85.8 % | lossy |

Each range runs over the three sources (synthetic and the two recorded starts).

**Read plainly:**

- **7000 reproduces G8-S1's cap cells:** the input is 8.25-8.32 Mbit/s and the drop is
  27-30 % / 45-48 %. G8-S1 measured 0.27-0.29 / 0.44-0.45.
- **The ratio under-predicts the lower rungs.** A parity packet goes per group of up to
  8, flushed at each frame end, so it does not shrink with the frame.
  - At 5000 the input is about 6.1 Mbit/s, not 5.89. Under cap-6000 a 1.8-2.4 % tail
    drop remains; 96-100 % of frames complete.
  - At 4000 it is about 4.65, between the ratio's 4.71 and C5-M3's 4.83.
- **4000 under cap-4500 drops 5.5-5.8 %.** That is post-FEC loss of about 650-730 /min,
  82-86 % complete frames, read `lossy`. The floor is above that cap: a finding about
  the rung list, as stated beforehand.
- **4000 under cap-6000 is clean.**
- **Whether a client reaches PLAYING** at a few percent of tail drop is the live
  test's (G8-S3). Nothing here claims it.

## 4. The replay at `floor` (`replay.py` → `replay_output.md`, `replay_tables.json`)

G5-S3's harness, the stream started at the floor at each session start, the
`StartRung` record checked on every session (PASS). Open loop on the reports recorded
at 7000.

| run | rules | start rungs | what the floor-started ladder did | at the run's first recorded acted transition |
| --- | --- | --- | --- | --- |
| G4-S1 run 1 (remote) | off | 4000, 4000 | 4000→5000 at 184 s; session 2: 4000→5000 at 502 s, 5000→5500 at 689 s | none recorded |
| G4-S1 run 1 | on | 4000, 4000 | held 4000, no transition (G5-S2's rules on; which rule blocked is not tabulated) | none recorded |
| G4-S1 run 2 (remote, then LAN) | off | 4000, then 5000 ×3 | 4000→5000 at 214 s | none recorded |
| G4-S1 run 2 | on | 4000, then 5000 ×3 | no transition | none recorded |
| G8-S1 cell 6 loss-5 (on) | on | 5000 | held 5000 | 00:33:38Z, recorded 7000→5000 `recovery_escalation`; the floor ladder was already at 5000 and refused FALLBACK / ROUTINE `at_floor` |
| G8-S1 cell 7 burst (off) | off | 5000 | held 5000 | 00:49:35Z, recorded 7000→6000 `capacity_mild`; the floor ladder was at 5000, ROUTINE refused `at_floor` |
| G8-S1 cell 12 delay-150 (on) | on | 5000 | held 5000 | 02:06:05Z, recorded 7000→6000 `wan_rules`; the floor ladder was at 5000, no decision within 4 s |

- No replayed run climbs back to 7000 within its window.
- In the three G8-S1 cells the recorded first action was a decrease, which a floor
  start would already have been below.
- No claim of improvement.

## 5. Proposed next (not run)

**G8-S3, session A's, about 1 h:**

- the four cap cells re-run with `PRIVYHUB_START_RUNG=floor`;
- once with `=cap` (G5-S3 + `PRIVYHUB_REMOTE_RUNG_CAP=4000`) under cap-4500;
- G8-S1's driver scaffolding.

**Expected from §3, not as a claim:**

- under cap-6000 the start enters at ~6.1 Mbit/s with ~2 % tail drop;
- under cap-4500, even 4000 carries ~5.5 %.

**What it answers:** whether the decoder starts under that, and whether a rung below
4000, or a parity scheme that scales, is the next question.

## 6. Files; disclosures

- **`g8_s2_2026-10-17/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`, `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - `design_written_before_code.md` / `.sha256`;
  - `g8_s2.diff`;
  - `tests_output.txt`, `tests_regression.txt`;
  - `flag_absent_proof.py`, `flag_absent_output.md`, `g5_s2_replay_rerun/`,
    `g5_s3_replay_rerun/`;
  - `cap_proof.py`, `cap_proof_tables.md`, `cap_proof.json`, `cap_proof_console.txt`;
  - `replay.py`, `replay_output.md`, `replay_tables.json`, `replay_console.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- `patches/G8-S2_START_RUNG.md`; ROADMAP §G8, the G8-S2 paragraph;
  `logs/g8_s2_git_status.txt`.
- Not written: `CURRENT.md`, `CURRENT_HANDOFF.md`, `KNOWN_ISSUES.md`, `PATCH_INDEX.md`.
- **Disclosed: `logs/impairment.jsonl` got 6 test lines.** At 16:53:5xZ the regression
  run of G8-P1's own `tests/impairment` appended them: profiles loss-5 / delay-50 /
  loss-1, t_s 1-4, 2,105 bytes.
  - That suite's relays pass the repo root to the shim. This is the suite's existing
    behaviour, not G8-S2's code.
  - The proof itself wrote nothing there.
  - The lines were not removed (nothing deleted). G8-S1's records use their own
    copies (`impairment_run1.jsonl`).
  - A later reader of the live file should skip them. The test's log path is listed
    for the user.
- **Disclosed: an errant command.** One command carried a stray `rm -rf /dev/null`.
  As a normal user it was refused by permissions; `/dev/null` is intact (checked), and
  nothing was deleted.
- **The companion is not restarted by B.** Its next restart loads these files with the
  flag absent: inert, as proved.
- Temp files are left under the system temp directory: `g8_s2_absent_*`,
  `g8_s2_stub_*`, `g8_s2_rows_*`, `g8_s2_replay_*`, and the re-runs' `g5_s2_*` /
  `g5_s3_*`.
- No sudo, no nft, the Opal untouched. Nothing fetched. No address or identifier:
  addresses are built from integers, and the handler comparison masks its target.
