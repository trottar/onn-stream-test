# B6 — the hold's trigger from the data, the rewind cap, the cap rule, the resume: design (hashed before any B6 code)

Queue `handoffs/QUEUE_2026-10-22C.md` item B6, session B. Baseline HEAD 144e5c7 (`companion/` clean). Predecessors:
`input_hold.py`, `hold_rewind.py`, `games/link_drop_recovery.py`, `plugins/games.py` (HEAD).

## 1. The distribution (`gap_distribution.md` / `.json`, `cap_windows.json`; computed before this design)

- **Clean sessions, chosen before computing** (the queue's list):
  - BENCH-R1 cell 1 (`loss-1`, uplink unimpaired) and cell 8 (`none`);
  - UX-R2's evening less the death (04:54:50-05:05Z), the user's two pauses and 10 s at every session edge.
  The CL-B5/6/7 windows have no control-gap log (the log exists only since E3-R2).
- **Gaps ≥ H per 10 min** (cell 1 / cell 8 / UX-R2):
  - 250: 9.84 / 16.1 / 3.54;
  - 500: 0.89 / 2.68 / 0.27;
  - 800: 0 / 2.68 / 0;
  - 900: 0 / 1.79 / 0;
  - **950: 0 / 0.89 / 0**;
  - 1500: 0 / 0 / 0.
  Cell 8's tail (gaps of 800-1,336 ms on an idle, unimpaired LAN) sets it.
- **H = 950 ms:** the smallest value on a 50-ms grid with ≤ 1 gap ≥ H per 10 min on **each** clean session, the
  queue's rule read per session.
  - Pooled over the three, the rule would give 500 ms, which leaves cell 8 at 2.68 false holds / 10 min. The queue
    expected ~500-600. The per-session reading is the one the queue's purpose needs: cell 8 is the session whose
    false holds failed BENCH-R1.
- **What 950 catches:**
  - **the death's five gaps (967 / 546 / 442 / 350 / 342): 1, the 967**, held ~17 ms before it ends; with B4's rewind,
    the 967 ms is returned whole. The other 4 run unheld.
  - Sunday:
    - the step 04:56-05:05: 0 of 34;
    - 05:06: 3 of 51 (3.4 of 24.4 s silent);
    - 05:10-05:11: 3 of 48 (3.9 of 21.1 s);
    - 05:20-05:21: 4 of 79 (6.8 of 37.5 s).
  - Every 4-s blackout (BENCH-R1 cells 5-6), at 0.95 s.
- **Stated plainly: on this LAN, length alone cannot tell the room's idle silences from the death's.** The idle LAN
  makes 800-1,336-ms silences, and the death's gaps are 342-967 ms.
  - The remaining levers are B5 (if the Wi-Fi lock removes the idle tail, H can come down: re-run
    `gap_distribution.py` on BENCH-R2's lock cell) and B7 (the client's own stall evidence).
  - 950 is what the data on file gives under the queue's rule. It is a setting, not a fixed constant.

## 2. The flag

**`PRIVYHUB_INPUT_HOLD_B6=1`**, read only when `PRIVYHUB_INPUT_HOLD` is set and valid (B2's `parse`).
- **Why a new flag:** "`1` / `on` maps to the chosen H" and "B2 / B4's tests unchanged" cannot both hold on B2's flag
  alone. B2's test pins `parse("1") == 250`.
  - So `PRIVYHUB_INPUT_HOLD` keeps its grammar and B2's meaning. With `_B6=1`, `1` / `on` mean 950. Numbers stay
    numbers (`PRIVYHUB_INPUT_HOLD=250` is still 250).
- **Absent = B2 + B4 byte for byte.** A new module `companion/hold_tuning.py` is imported only under both. The guarded
  statements are removed by the proof.
- Set but not `1`: ignored, one `input_hold_b6_config` row. The hold not active: nothing.

## 3. The four changes (all under `_B6=1`)

1. **H:** `1` / `on` → **950** (`hold_tuning.H_DEFAULT_MS`; the detector's threshold is set by B6's wire after B2's).
2. **The rewind cap default** (B4's `PRIVYHUB_INPUT_HOLD_REWIND_CAP` absent): **max(30, round(H / 16.7) + 5)**, ≤ 120.
   - **At 950: 57 + 5 = 62.** B4's counter at H = 950 is ≈ (950 + ≤ 50 detection + ~80 pause confirm) / 16.7 − 4 ≈
     61, so 62 covers it. At 250 it gives 30, B4's own.
   - An explicit `_CAP` still wins.
   - B4's launch-config buffer uses the same cap: snes9x 823,536 × 64 → **51 MiB**; Beetle PSX HW 16,777,240 × 64 →
     **1,025 MiB**. For A's memory question.
3. **The cap rule:** B2 counts every hold in a rolling 60 s (6, then no hold until the window passes). B6 counts
   **only holds released by input** (the release found the pause still the hold's own), and at 6 in 60 s
   **disarms for 10 s**, not until the window expires. One `input_hold_cap` row per disarm, `rule: b6`.
   - **From the data, why keep it at all:**
     - at H = 950 no session on file reaches 6 in 60 s. The most is 5, cell 5's bad room; Sunday 4; every clean
       session ≤ 1. So on file it never binds.
     - At 250 it bound 13-229 times per session. That is how it disarmed cell 6's b3.
     - It stays as a guard against an unseen flapping link, where each pause + rewind could cost more than it
       saves.
   - Handed-over holds (a real outage that v2 or the client took over) never count.
4. **The resume.**
   - **Why 2-4 s late in cells 5-7, from code:**
     - those pauses were all `client_output_silence`. The bench let the client's desync POST through.
     - Their exit is the **client's gate**: the client re-enters its stabilization gate after ≥ 1 s of output
       silence.
     - The gate shows a **full-screen black overlay** ("Reconnecting… The game is paused until the stream
       returns", `NativeStreamActivity.updateStabilizationOverlay`, a MATCH_PARENT black `TextView`).
     - The gate needs `RECOVERY_CLEAN_TICKS = 3` clean 500-ms metrics ticks (fps ≥ 45, output gap ≤ 120 ms,
       decode ≤ 150 ms) before it POSTs `native-stream-ready`, ≥ 1.5 s after frames return, typically 2-2.5 s.
     - **It is not v2's stability wait.** A host-side resume before the client's gate would run the game under a
       black screen: that is the problem cell 7 showed, moved.
   - **So B6's rule, one owner (the recovery):**
     - **(R1) A hold handed over to v2's `controller_silence`** (an uplink-only outage; the client's output is
       fresh, or it would have been a client trigger):
       - the hold's own release event (the first controller packet back), today ignored there, arms `hold_return`;
       - the recovery's monitor (every 250 ms) resumes as soon as **a heartbeat received after the return shows
         the client's output fresh** (0 ≤ `last_output_age_ms` ≤ 300), "within one report";
       - B4's rewind runs first if wired;
       - `resumed via hold_return`.
       This pre-empts v2's exit, which needs two checks 250 ms apart and then a heartbeat after them. v2's exit
       stays as the fallback; whichever fires first wins under the recovery's lock.
     - **(R2) A hold handed over to a client trigger** (`client_*`): **left to the client's gate**, for the reason
       above. The fix is client-side and belongs to B7: the client says when it shows gameplay again.
     - **(R3) A client `native-stream-ready` that arrives after a hold-originated resume** (`input_release` or
       `hold_return`), while `PLAYING`, within 20 s (the client's gate times out at 15 s):
       - read as that recovery's end: `recovered: true`, one `client_ready_after_hold` row;
       - **not as a new session.**
       - Today `note_gameplay_released` → `session_started()` would log a session start and reset the ladder
         (`_adaptive_bitrate_session_ended`, 7000 with no history).
     - **A latent B2 interaction, disclosed:** a hold released by the first packet back while the client sits in
       its gate (a ≥ 1-s output silence, e.g. a real `@both` drop where the desync POST cannot get out) runs the
       game behind the client's black overlay until its gate passes. Then, without R3, the ready restarts the
       session. B6 fixes the second; the first needs B7.

## 4. Hooks (each one guarded statement; the proof strips them)

- **`input_hold.InputHoldDetector`:** a class attribute `tuning = None`. In `on_quiet`, one guarded statement:
  `if self.tuning is not None: return self.tuning.on_quiet(self, now, last_any_packet_at)`. B6's version: B2's logic
  with the B6 cap.
- **`link_drop_recovery.LinkDropRecovery`:** a class attribute `_input_hold_b6 = None`, and:
  - `note_input_hold`: before its final read, `note_hold` (the episode key = `_state_since` when the hold's pause
    stands);
  - `note_input_release`: at its top, `note_release(self)`. It counts a true release (the reason still
    `input_hold`), arms R1 (the reason `controller_silence` and the episode the hold's), and marks R3's window;
  - `note_gameplay_released`: at its top, `if … and ready_after_hold(self): return {…recovered…}` (R3);
  - `_tick`, in `PAUSED_RECOVERING` before v2's exit: `if … and maybe_resume(self, now): return` (R1).
- **`hold_rewind`:**
  - `wire`: the cap default as above, when `_B6` is on and `_CAP` is absent;
  - `config_block`: the same default for the buffer.
  Both are one guarded statement, reading the environ given.
- **`plugins/games.py`:** a guarded module-level import, and one guarded wire call after B4's.

## 5. Tests (`tests/input_hold_b6/`; B2's 19 and B4's 22 unchanged and green)

1. **The flag:** with `_B6`, `1` / `on` → 950 and `250` → 250; without it B2's table. Ignored values give a row.
2. **The rewind cap default:**
   - 950 → 62, 250 → 30, an explicit `_CAP` wins;
   - the config block's buffer at 62 (snes9x 51 MiB, PSX 1,025 MiB);
   - with `_B6` absent, B4's bytes.
3. **The cap:**
   - 6 released holds in 60 s disarm for 10 s, then it re-arms;
   - handed-over holds never count;
   - one row per disarm.
4. **R1:**
   - a hold, then `controller_silence` takes over, then the packets return (the release event), then a heartbeat
     after the return with fresh output: `resumed via hold_return` within one tick, the rewind called first;
   - no heartbeat, or a stale one (before the return), or output not fresh: no resume;
   - v2's exit still works if it comes first;
   - a v2 pause that was never a hold: nothing.
5. **R2:** a hold handed to `client_output_silence`: the release does not resume, and the client's ready still does.
6. **R3:**
   - a ready within 20 s of an `input_release` resume: `recovered`, no `session_started`, one row;
   - after 20 s, or with the state not `PLAYING`: today's path.
7. **Flag absent:** a fresh process with the hold only imports no `hold_tuning`. The AST proof per changed module.
8. **The detector with B6** on a fake clock: a 950 threshold, 900 nothing, 960 a hold.
