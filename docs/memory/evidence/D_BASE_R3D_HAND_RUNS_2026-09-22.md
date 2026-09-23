---
memory_schema: 1
as_of: 2026-09-22
status: D-BASE-R3d — the user's hand runs classified. N05 PASS (run 2026-09-23 00:08 local), N15b PASS, E30 PASS → R3 + R3a RUNTIME VALIDATED for real loss (N05, N3, N15, N15b, N150 all PASS) and END_MS RUNTIME VALIDATED (one recording gap named). Documentation only; no nft, no code
---

# D-BASE-R3d — the owed R3b runs, run by hand

Task: `handoffs/D-BASE-R3D_TASK.md`. The user ran
`d_base_r3b_2026-09-21/r3b_run.sh` by hand on the evening of 2026-09-22
(local, UTC-4; the logs are UTC). Artifacts in
`d_base_r3b_2026-09-21/<LABEL>/`; manifest `SHA256SUMS.txt` regenerated
(48 files, `sha256sum -c` clean). Criteria:
`D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md` and the task. **No
`privyhub_fault` table was present** when checked (`sudo -n nft list
tables`).

## Classification

- **N05 — NOT RUN on 2026-09-22** *(superseded: re-run 2026-09-23 00:08, **PASS** — see "N05 — result" at the end)*. `N05/` was then **empty**: `r3b_run.sh`
  creates the directory first and exits before the fault when the stream
  cannot be opened. No `session_started` appears in the recovery log
  between 01:16 and 02:27 UTC, and nothing listened on 8765 until 22:27
  local (see the incident below). **So `R3` + `R3a` stay NOT runtime
  validated; N05 is the only run owed** (N3, N15, N150, N15b PASS).
- **N15b — PASS**, on the N15 criterion, numbers beside N15's below.
- **E30 — PASS on every behavioural criterion → `END_MS` RUNTIME
  VALIDATED.** One *recording* criterion is unmet: **the recovery file's
  SHA-256 was not captured** before the user discarded it (the harness
  does not hash it, and `save_state_probe.txt`, which held it, is reset
  at every launch — the next launch at 23:10 reset it). The file's
  existence is recorded (`gave_up_saved.state_file`, `save_available:
  true` at the end). Named here so it can be overruled.

## N15b — 15 s, repeat of N15 (raw first)

| | N15 (09-22 11:19) | **N15b (09-22 22:28)** |
| --- | --- | --- |
| measured fault (`t_off - t_on`) | 15.064 s | **15.069 s** |
| `desync_pause` (trigger, age) | +1.42 s (`client_output_silence`, 1,281 ms) | **+1.28 s** (`client_output_silence`, 1,147 ms) |
| `encoder_restart` | +5.61 s, `method: restart`, attempt 1 | **+5.51 s, `method: restart`, attempt 1** |
| restart result | `encoder_restarted` true, host RTP again at 1,171 ms | **true, host RTP again at 1,221 ms** — at ≈ +6.7 s, **while the fault had ~8 s left** |
| `resumed` | off **+3.77 s**, `recovering_ms` 17,512, restarts 1 | **off +3.60 s**, `recovering_ms` 17,482, restarts 1 |
| poll saw `PLAYING` | off +3.848 s | off +3.746 s |
| heartbeat `rx_packets` during fault | 25,646 → 25,646 (flat, 8 beats) | **25,665 → 25,665 (flat, 8 beats)** |
| max `last_output_age_ms` during | 14,601 | 14,436 |
| report `max_output_gap_ms` | 15,116 | **15,260** |
| `lost_packets` / in resyncs | 22 / 0 | 10 / 0 |
| `sequence_resyncs` / `ssrc_changes` | 1 / 1 | 1 / 1 |
| discontinuities | `ssrc_change` at 46,118 ms | `ssrc_change` at 46,239 ms |

Pause yes; the only restart is `method: restart` and it succeeded with
the fault still in place; resumed 3.60 s after the rule was deleted
(< 5 s). **PASS.** Loss reads 10 packets for a 15 s outage because the
restart's new SSRC hides it — `max_output_gap_ms` (15.26 s) is the honest
column, as `R3b` recorded.

## E30 — 150 s fault, rule kept for the whole post-wait (raw first)

Run: `./r3b_run.sh E30 output 48100,48101 150 1900 25 1`. `t_on`
02:31:30.124 UTC; **`t_off` empty** (`KEEP_RULE=1`); the rule was removed
by the script's exit trap at **≈ 03:10:10 UTC** (the run's last artifacts,
23:10:08-10 local), 38.7 min after `t_on`.

| event (recovery log) | UTC | from `t_on` |
| --- | --- | ---: |
| `session_started` | 02:31:04.218 | -25.9 s |
| `desync_pause` (`client_output_silence`, 1,235 ms) | 02:31:31.486 | +1.36 s |
| `encoder_restart` 1-5, all `method: restart`, backoff 5/10/20/30/30 s | 02:31:35.710 … 02:33:15.980 | +5.6 … +105.9 s |
| **`gave_up_saved`** → `PAUSED_SAVED`, restarts 5, `state_file …/Tekken 3 (USA).state.recovery` | **02:33:31.767** | +121.6 s |
| **`ended_after_link_loss`** → `ENDED` | **03:03:33.153** | +1,923.0 s |

- **`PAUSED_SAVED` → `ENDED` = 1,801.386 s** against `END_MS` 1,800,000
  ± 5 s — **PASS**, from the recovery-log timestamps.
- Heartbeat: 74 beats during the 150 s window, `rx_packets` flat at
  25,612, `last_output_age_ms` up to 148,879; flat after it too (the rule
  stayed).
- Report `native_decoder_20260923_031009_782.json`: duration 2,350 s,
  `max_output_gap_ms` **2,319,190**, `lost_packets` 6, 0 resyncs, 0 SSRC
  changes, no discontinuities — the stream never came back, so nothing
  was counted as loss; the gap column carries the outage.
- **Graceful end** — RetroArch's own session log
  (`logs/games/20260922-223046-game_ps1_b0a5986638f61a11.log`, last
  written 23:03:32 local, the second of `ENDED`): `[SRAM] Saved
  successfully … (unchanged, skipping write)` (the `SAVE_FILES` effect),
  `Unloading game` / `Unloading core` / `Unloading core symbols`, core
  options and monitor saved — a full, clean shutdown. The companion's
  `frontend_close_result` line (returncode) is **not retained**: the
  control probe was reset by the 23:10 launch.
- **No orphan**: the same-title launch at 23:10:43 started a new
  RetroArch session log (a launch against a live session is a no-op), and
  now no RetroArch or ffmpeg runs and nothing listens on 48100-48102 or
  48110. `status_end.json`: `ENDED`, `save_available: true`, `saved_at`
  02:33:31Z, `last_error` null.
- **Prompt before launch, then Discard** — companion access log:
  `POST /plugins/games/recovery-discard` at **23:10:27**, then `POST
  /plugins/games/launch` at **23:10:43**. Discard is reachable only from
  the recovery prompt, so the prompt was shown, with no live session,
  before the launch. Afterwards the states directory holds no
  `.state.recovery` or `.png`, the index file is gone, and the 23:10
  session's RetroArch log has **no `[State] Loading` line** — a plain
  launch.
- Recovery file SHA-256: **not recorded** (see Classification).

## The incident — why 8765 was not listening

**Cause determined: a deliberate stop, not a crash.** The overnight
queue's `P8` teardown stopped the companion per `TOOLS.md` ("the
companion is stopped last"): `P8`'s harness restored companion 103827 at
21:17 local; the teardown then stopped it, started a short-lived one at
21:20 (`logs/companion_teardown_2026-09-22.log`) to re-check the launcher
banner, and stopped that too at ≈ 21:21 — and said so in its summary.
**Nothing listened on 8765 from ≈ 21:21 until the user's manual start at
22:27:16** (`logs/companion_manual_2026-09-22.log`, first request
22:27:22). So the handoff's "died between the end of N05 and the first
N15b attempt" is wrong in its first half: **N05 itself ran against no
companion**, which is why its directory is empty, and the first N15b
attempt failed the same way (`logs/n15b_fail_probe.txt`: empty status
curl, "Companion unreachable").

Looked at: the three companion logs of the evening (`companion_p8_restored`,
`companion_teardown` — both 0 bytes, consistent with SIGTERM before a
block-buffered flush — and `companion_manual`), the recovery log, the
decoder-session directory, `p8_all.sh`. **No 414 / `send_error` traceback
is involved** (N05 posted no report). The manual companion's log holds
three tracebacks, all `BrokenPipeError` on heartbeat replies at
22:31-22:33 — the client timing out during E30's outage; harmless. The
P8-started companion was not lost to a session ending; it was stopped on
purpose.

## Privacy

Client addresses in the companion logs were not copied; access-log lines
above are quoted without them. No MAC, SSID, endpoint or serial.

## N05 — result (run by the user 2026-09-23 00:08 local; closes the set)

The first N05 attempt (2026-09-22 ≈ 22:22 local) left an empty directory
— no companion; see the incident above. The user re-ran
`./r3b_run.sh N05 output 48100,48101 0.5 20 25` with the companion
listening; artifacts in `d_base_r3b_2026-09-21/N05/`.

Raw numbers:

- **Measured fault `t_off - t_on` = 0.556 s** (`t_on` 04:08:12.809 UTC).
- Recovery log for the run: `session_started` 04:07:47.747 (on -25.06 s),
  `session_ended` 04:08:37.166 (on +24.36 s) — **nothing between them**:
  no `desync_pause`, no restart. The state poll read `PLAYING 0` through
  the fault and after the clear (first post-clear poll `PLAYING` at
  +0.039 s).
- Report `native_decoder_20260923_040837_140.json` (56.9 s):
  **`max_output_gap_ms` 625**; `lost_packets` 445, of which
  `lost_packets_in_resyncs` 423; **`sequence_resyncs` 1**, `ssrc_changes`
  0, `largest_resync_jump_packets` 423; `forward_gap_events` 4 (max 8
  packets); `fec_recovered_packets` 2, `fec_unrecoverable_groups` 3;
  discontinuities: one `sequence_resync` at 33,882 ms, jump 423. Audio: 108
  lost, 42 underruns.
- Heartbeat across the hole: `rx_packets` 27,473 at on +0.12 s → 28,720 at
  +2.15 s (still climbing), `last_output_age_ms` 60 → 62 → 4; the loss
  counter steps 22 → 445 and `stream_resyncs` 0 → 1 in the same tick.

Against the criterion: no pause — **yes**; the receiver resynced on its
own (one sequence resync, no restart, no SSRC change) — **yes**;
`max_output_gap_ms` < 1,000 — **625, yes**; the report records the hole —
**yes** (423-packet resync, 445 lost). **N05 PASS.** A 0.556 s hole stays
under the 1 s `DESYNC_MS` with room: the longest output age seen was
625 ms.

## Classification, final

**`R3` + `R3a` — RUNTIME VALIDATED for real loss**: N05, N3, N15, N15b and
N150 all PASS on the production path. **`END_MS` — RUNTIME VALIDATED**
(E30, above).
