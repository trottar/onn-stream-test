---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (companion/ clean; predecessors = HEAD's files)
---

# B6 — the hold's trigger from the data: H = 950, B4's cap to match, the cap rule, the resume

**Classification: the distribution READ; BUILT behind `PRIVYHUB_INPUT_HOLD_B6=1` (with the hold); 16 new tests; B2's
19 and B4's 22 unchanged and green; flag absent = B2 + B4 (whole-module AST identical, 4 files); NOT ADOPTED; no
live run; nothing committed.** Design `b6_2026-10-22/design_written_before_code.md`, sha256 `b7de4f95…640e`, hashed
**05:36:38Z, before any B6 code**. It came after the distribution was computed, as the queue orders.

## 1. The distribution (`gap_distribution.md` / `.json`, `cap_windows.json`)

**The clean sessions, chosen before computing** (the queue's list):
- BENCH-R1 cell 1 (`loss-1`: the shim drops downlink only) and cell 8 (`none`);
- UX-R2's evening, less the death, the user's two pauses and 10 s at every session edge.

The CL-B5/6/7 windows have no control-gap log: the log exists only since E3-R2.

| uplink silences ≥ 250 ms, per 10 min | ≥ 250 | ≥ 500 | ≥ 800 | ≥ 950 | longest ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| cell 1 | 9.84 | 0.89 | 0 | 0 | 517 |
| **cell 8** | **16.1** | 2.68 | 2.68 | **0.89** | **1,336** |
| UX-R2 clean | 3.54 | 0.27 | 0 | 0 | 669 |
| *shown only:* cells 2 / 3 / 4 | 19.6 / 36.6 / 70.5 | | | | 989 / 647 / 1,429 |
| *shown only:* cell 5's room (outside its blackouts) | **128.4** | | | | 1,742 |
| *shown only:* Sunday (UX-R1) | 51.0 | | | | 3,232 |

**H = 950 ms:** the smallest value (50-ms grid) with ≤ 1 gap ≥ H per 10 min on **each** clean session.
- **The queue expected ~500-600. Pooled over the three, the rule gives 500, but that leaves cell 8 at 2.68 false holds
  / 10 min.** Cell 8 is the session whose false holds failed BENCH-R1, so the per-session reading is applied.
- **What 950 catches:**
  - the death's five gaps (967 / 546 / 442 / 350 / 342): **1 (the 967)**;
  - Sunday:
    - the step 04:56-05:05: 0 of 34;
    - 05:06: 3 of 51 (3.4 of 24.4 s silent);
    - 05:10-05:11: 3 of 48 (3.9 of 21.1 s);
    - 05:20-05:21: 4 of 79 (6.8 of 37.5 s);
  - every 4-s blackout.
- **Read plainly: on this LAN a silence's length cannot tell the room from the death.** The idle, unimpaired LAN makes
  800-1,336-ms silences, and the death's are 342-967. 950 avoids false holds and catches long outages, but
  it does not catch the death's short gaps.
- **The levers left:**
  - **B5:** if the Wi-Fi lock removes the idle tail, H can come down. Re-run `gap_distribution.py` with BENCH-R2's
    lock cell added.
  - **B7:** the client's own evidence.

## 2. What was built (`b6.diff`: +36 in four files; `companion/hold_tuning.py` new, 201 lines)

**`PRIVYHUB_INPUT_HOLD_B6=1`** (read only with the hold valid; set but not `1` gives one ignored row). **A new flag,
because B2's test pins `PRIVYHUB_INPUT_HOLD=1` → 250**, and the queue keeps B2 / B4's tests unchanged. Under it:

1. **`1` / `on` → 950.** Numbers stay numbers (`250` is still 250).
2. **B4's rewind cap default** (no `_CAP` given): max(30, round(H / 16.7) + 5) ≤ 120. **At 950 that is 62.**
   - The launch-config buffer follows: snes9x **51 MiB**, Beetle PSX HW **1,025 MiB** (cap + 2 raw states).
   - An explicit `_CAP` wins.
3. **The cap rule:** only **holds released by input** count. 6 in 60 s **disarm the hold for 10 s**, with one
   `input_hold_cap` row, `rule: b6`.
   - **Kept as a guard, from the data:** at H = 950 no session on file reaches 6 in 60 s (the most is 5, cell 5's bad
     room; Sunday 4; the clean ≤ 1). At 250 it bound in every window of a flapping minute (cells 5-6, UX-R1-R2), and
     that is how it disarmed cell 6's b3. Handed-over holds never count.
4. **The resume.**
   - **Why 2-4 s late in cells 5-7, from code:**
     - those pauses were `client_output_silence` (the bench let the desync POST through).
     - Their exit is **the client's gate**: 3 clean 500-ms metrics ticks before `native-stream-ready`, behind a
       **full-screen black overlay** ("Reconnecting… The game is paused until the stream returns").
     - **It is not v2's stability wait.** A host-side resume before that gate would run the game under a black
       screen.
   - **So:**
     - **(R1)** a hold that v2's **`controller_silence`** took over (an uplink-only outage, with the client's output
       fresh):
       - the hold's release event (the first packet back) arms `hold_return`;
       - the monitor resumes at the **first heartbeat after the return that shows output fresh** (≤ 300 ms),
         within one report. B4's rewind runs first, then `resumed via hold_return`.
       - v2's exit stays as the fallback; the first to fire wins.
     - **(R2)** a hold that a **client trigger** took over: **left to the client's gate.** The fix is the client's
       (B7).
     - **(R3)** a client `native-stream-ready` within 20 s of a hold-originated resume, while `PLAYING`: read as that
       recovery's end (`recovered: true`, one `client_ready_after_hold` row), **not a new session.**
       - **Today it would log `session_started` and reset the ladder to 7000 with no history.**
       - **That is a latent B2 interaction, disclosed:** a hold released by the first packet back while the client
         is in its gate (any output silence ≥ 1 s, e.g. a real `@both` drop) runs the game behind the client's
         black overlay until the gate passes, then restarts the session. B6 fixes the restart. The blind running
         needs B7.

**One owner:** the recovery calls B6 from its own methods:
- `note_input_hold`, `note_input_release` (top), `note_gameplay_released` (top): one guarded statement each;
- `_tick`, before v2's exit: one guarded statement;
- the detector's `on_quiet`: one guarded statement, B2's logic with B6's cap;
- `hold_rewind.config_block`: the buffer;
- the plugin: a guarded import and a wire after B4's.

**Against the design, disclosed:**
- B4's rewinder cap is set in `hold_tuning.wire`, not by a hook in `hold_rewind.wire`. That is one hook fewer.
- The design's §1 typo, "04:54:50-05:05Z", is 04:54:50-04:55:05Z (the script uses the latter).

## 3. Tests (`tests_input_hold_b6.txt`, `tests_regression.txt`)

**`tests/input_hold_b6`: 16 OK** (from the tree):
- the flag table and H (`1` / `on` → 950, numbers kept; B2's parse untouched);
- the wire (H on the detector, B4's cap 62, the row);
- the rewind cap (62 / 30 / 120 / an explicit cap / B6 absent);
- the buffer per core (51 / 1,025 MiB; B4's bytes without B6);
- the detector at 950 (900 nothing, 960 a hold);
- the cap (6 released disarm 10 s and re-arm; 8 handed-over holds count 0);
- R1 (no heartbeat / a stale one / output not fresh: no resume; a fresh one after the return gives `hold_return`
  through `_tick`, the rewind first);
- v2's exit still first when it comes first;
- a v2 pause that was never a hold: nothing;
- R2;
- R3 (once; the window expires at 20 s);
- without B6, B2's exact rows (the ready is a `session_started`, as today);
- flag absent (a fresh process imports no `hold_tuning`);
- the hook shapes.

**B2's `tests/input_hold` 19 OK and B4's `tests/input_hold_rewind` 22 OK, both files unchanged vs HEAD.**

**The regression set in the copy:** all OK (impairment 29, recovery 17, overlay 17, session_identity 88, audio_codec 20,
encoder_rc 16, wan_adaptation 23, wan_telemetry 18, remote_ladder 26, remote_cap 16, start_rung 17, lan_loss_rule
21, link_report 9, shadow 21, source contract 7, c5_m1 14, ps1_look 13 + 11). adaptive_bitrate_live is 126 from the
tree. C3-F1's 1 error is pre-existing.

**Flag absent** (`proof_flag_absent.py` → `.md`): **all four modules identical** with B6's items removed.

## 4. For BENCH-R2 (session A)

- **The blackout cell:** `PRIVYHUB_IMPAIRMENT=blackout-4s@both,every=120s,seed=1` with B1b's gate (§B1b),
  `PRIVYHUB_INPUT_HOLD=1`, `PRIVYHUB_INPUT_HOLD_B6=1`, `PRIVYHUB_INPUT_HOLD_REWIND=1`.
  - Expected per blackout:
    - one hold at ~0.95-1.0 s;
    - one `input_release` at the return with `rewound_frames` ≈ 60-62;
    - net unattended ≈ 0 (`--net`).
  - **Then the client's black overlay for ~1.5-2.5 s with the game running** (the latent interaction above) and a
    `client_ready_after_hold` row (not a `session_started`). B7's stall signal is what closes that window.
- **`none` + everything on:** false holds per 10 min (expected ≤ 1 at 950 on this room; cell 8 read 0.89 at ≥ 950).
- **Re-run `gap_distribution.py`** with the B5 lock cell, to see whether H can come down.

## 5. Files

**`b6_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
- `gap_distribution.py`, `gap_distribution.json`, `gap_distribution.md`, `cap_windows.py`, `cap_windows.json`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `b6.diff`, `diffstat.txt`;
- `proof_flag_absent.py`, `proof_flag_absent.md`;
- `tests_input_hold_b6.txt`, `tests_regression.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:** `companion/hold_tuning.py` (new), `companion/input_hold.py`, `companion/hold_rewind.py`,
`companion/games/link_drop_recovery.py`, `companion/plugins/games.py`, `tests/input_hold_b6/test_input_hold_b6.py`
(new); `patches/B6_INPUT_HOLD_TRIGGER.md`; `logs/b6_git_status.txt`.

The rules held:
- no stream, no companion restart, no adb, no sudo, no nft;
- the Opal untouched;
- nothing fetched, nothing deleted;
- nothing of A's touched (its logs read only).

## 6. Correction (found during LAN-R2, the same session): the CL-B5/6/7 windows do have control gaps

- **§1 said "the CL-B5/6/7 windows have no control-gap log". That was wrong.**
  - Only the evidence copies were searched. The live `logs/games/native_stream_ctrl_gaps.log*` (read-only) cover
    2026-10-10 → 2026-10-22, those windows included.
- `gap_distribution_cl.py` → `gap_distribution_cl.md` / `.json` adds the eight CL windows as clean sessions
  (600 s each) and re-applies B6's rule.
- **The result: H stays 950.**
  - At ≥ 950 the CL windows hold 0-1 each per 10 min. At ≥ 900 cell 8 still has 1.79.
  - **The idle room of 10-18/19 made 59-81 uplink silences ≥ 250 ms per 10 min** (CL-B5 / CL-B6), more than cell 8's
    16. B2's 250 would have held 6-8 times a minute there.
