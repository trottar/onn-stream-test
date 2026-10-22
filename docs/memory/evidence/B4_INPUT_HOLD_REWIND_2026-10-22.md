---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: d4c9870 (B1-B3 committed there; companion/, tools/, tests/ clean at start; predecessors = HEAD's files)
---

# B4 — rewind on the hold's release (a blackout should cost the player nothing)

**Classification: BUILT behind `PRIVYHUB_INPUT_HOLD_REWIND=1` (read only with B2's `PRIVYHUB_INPUT_HOLD` set and
valid). Unit-tested against a fake core over real loopback UDP. Flag absent = B2 byte for byte:**
- the five changed modules' whole-module AST, with B4's items removed, = the predecessors';
- the generated RetroArch config's masked hash = the predecessor's;
- the tool's output = the predecessor's.

**NOT ADOPTED; no live run; nothing committed.** The CPU cost, the PSX question and the live proof are session A's
(BENCH-R2, §7).

Task `handoffs/B4_INPUT_HOLD_REWIND_TASK.md`, session B. The user's idea: "We have the emulator, why not just rewind
the game for however lost." Design `b4_2026-10-22/design_written_before_code.md`, sha256 `ca9cc18a…bdaf`, hashed
**04:25:28Z, before any B4 code**. Two corrections were found after the hash, by measurement and by the fake core
(§3, `design_corrections.md`).

## 0. The wait, and what the host carries

**The bench.** `privyhub-bench-r1` read `active` at the start.
- Reading, the design, the evidence extracts, the `/tmp/b_b4` copy and all the code and tests in the copy proceeded
  meanwhile.
- **Nothing under the tree's `companion/` was written until it read `inactive`** (04:35:45Z,
  `bench_check_before_write.txt`). Only `privyhub-companion` was listed then. It was not restarted.
- Disclosed: the unit was checked at each step of the work, minutes apart at times, not on a 60-s timer. The rule it
  serves held: no write while active.

**RetroArch: 1.22.2 (AppImage), no source and no docs on the host.** What follows is from the binary's strings
(`retroarch_binary_strings.txt`) and from the config the same binary saved with every key at its default
(`retroarch_saved_defaults.txt`):
- the command interface lists `REWIND` among its hotkey commands ("Rewinds current content while key is held").
- **It reads no frame counter.**
  - `GET_STATUS` is state + content.
  - `GET_CONFIG_PARAM`'s list has `active_replay` (`%lld %u %lld`), which is a frame only while a replay records or
    plays.
- Rewind keys: `rewind_enable` (default `false`), `rewind_granularity` (`1`), **`rewind_buffer_size` in bytes**
  (`20971520`), `audio_rewind_mute` (**default `false`**), `notification_show_fast_forward` (`true`: the indicator).
- It refuses rewind for a core without serialization, with threaded audio (Pulse here is not), or after a failed
  buffer allocation.

**Real savestates on disk** (RZIP header's uncompressed size; one per core fully decompressed = the header;
`savestate_sizes.json`):

| core | raw state |
| --- | ---: |
| snes9x | 823,536 B |
| bsnes | 284,304 B |
| **Beetle PSX HW** | **16,777,240 B (16 MiB), all 29 files** |

## 1. What was built

**The flag:**
- `PRIVYHUB_INPUT_HOLD_REWIND=1`, with the hold valid;
- `PRIVYHUB_INPUT_HOLD_REWIND_CAP` 5-120, default 30;
- set but not `1`, or the hold inactive: ignored, one `input_hold_rewind_config` row. An invalid cap is noted in
  the row and 30 is used.

**The launch config, flag on only** (one block appended to `privyhub-session.cfg`; a base that already sets a key is
left alone, after A7.3's duplicate lesson):

```
rewind_enable = "true"
rewind_granularity = "1"
rewind_buffer_size = "<ceil_MiB(raw state × (cap + 2))>"
audio_rewind_mute = "true"
```

- The arithmetic at cap 30: snes9x 823,536 × 32 → **26 MiB = 27,262,976**; bsnes 284,304 × 32 → **9 MiB =
  9,437,184**; Beetle PSX HW 16,777,240 × 32 → **513 MiB = 537,919,488**; a core with no state on disk → RetroArch's
  20 MiB.
- That is room for cap + 2 frames even with no delta compression. Cap 120 on PSX would be 1.9 GiB, on a 15-GB host.
- **`audio_rewind_mute` is a fourth key beyond the task's three, disclosed.** The task wrote "(muted)", and this
  RetroArch's default is not.
- **Hashes** (`config_hashes.txt`, the masked method, one synthetic project root):
  - predecessor, flag absent, `HOLD` only, `REWIND=yes`, `REWIND` without `HOLD`, `HOLD=0` + `REWIND=1`: **one hash
    `91afed62…`**;
  - flag on: + the block only, per core.

**The counter: the host's monotonic clock × 60 fps** (no core counter is readable, §0; the host's frame logs count
encoder frames, which run at 60 / s on a paused core, B2):
- **onset** = the receive loop's stamp of the last controller packet. B2's dispatcher `put` runs in the loop at
  detection and stamps it, as `put time − age_ms`, FIFO, one pop per hold event on every path. Resolution ~2.3 ms:
  the packet interval.
- **confirmed pause** = B2's `_paused_at` (`EmulatorManager.pause()` returned `PAUSED`).
- **`counter_before` = round((pause − onset) × 60) − 4.** The 4 is measured (§3).
- **`requested_frames` = min(counter_before, cap).** At H = 250: ~17-18 frames in the fake.

**On release, before B2's resume** (`hold_rewind.Rewinder.rewind`, called from the recovery's own release, one
owner), under `EmulatorManager.lock`, over raw loopback UDP to the companion's own command port:
1. preconditions:
   - a pending hold of this pause episode (keyed by the recovery's `_state_since`; a stale one is dropped);
   - a port;
   - the session config on disk carrying `rewind_enable = "true"`;
2. mask the player's input (the receive loop applies no report while `masked()`, which expires by itself after
   1 s) and neutralize the pads;
3. `REWIND` + `PAUSE_TOGGLE` together, then `REWIND` every half frame for N frames;
4. **one `GET_STATUS` within 2 frames (33 ms)**, which must read `PLAYING`;
5. unmask (always);
6. B2's `resume()` as today. After a confirmed rewind it finds `PLAYING` and sends nothing.

**The mechanism, and why:** *unpaused, per-frame `REWIND`*. Whether 1.22.2 honours `REWIND` while paused is not
decidable from what the host carries, so the code uses the path that holds either way (A's Q3).

**The rows:**
- `input_release`: `requested_frames`, `rewound_frames`, `counter_before`, `counter_after`, `onset_to_pause_ms`,
  `pause_confirm_lag_frames`, `rewind_ms`, `via`, `method`, `cap`;
- **`rewind_failed`**: the same + `reason`;
- then B2's `resumed via input_release`, unchanged.

**The hold never fails because the rewind did:** the rewinder never raises, and the resume follows in every case
(tested ×4).

**`rewound_frames` / `counter_after` are what they are.** They are the `REWIND`s RetroArch acknowledged reading (the
`GET_STATUS` behind them answered), on the clock counter. They are not a read-back of the core: 1.22.2 has none.
**Not detectable over the NCI:** a core that refuses rewind, or a buffer that failed or ran out. Then the `REWIND`s
are ignored and the core runs ~N frames forward with the input masked: the cost doubles for that blackout. The
session-config check narrows this, and A's Q4/Q5 decide it.

**The handover, rewound too (one guarded call):**
- v2's 5.35-s `controller_silence` takes the hold's pause over. There is no second pause and `_state_since` is
  unchanged, so v2's controller-return exit (`_maybe_exit_controller_pause`) runs the same rewind before its
  `_resume_game()`, `via: controller_return`.
- **Then a 20-s outage also costs nothing: the second use.**
- A v2 pause without a hold is not rewound, and neither is the client's own gate or the give-up save.

**`tools/unattended_frames.py --net`:**
- per episode, core running − the episode's `rewound_frames` (the `input_release` rows; the latest episode starting
  before the row and ending ≤ 30 s before it), floored at 0;
- the excess is `rewound_beyond_threshold`: the rewind also returns the first 250 ms, which the measure does not
  count;
- **without `--net` the output is the predecessor's byte for byte** (`unattended_noflag_equal.txt`, UX-R2's
  preserved logs: sha256 `3c9dde9b…` both);
- on UX-R2 with `--net`: 563.8 = 563.8 (no rewinds there).

**Hooks** (`b4.diff`, `diffstat.txt`: +106 / −2 in six files, plus `companion/hold_rewind.py` 311 lines, new):
- `input_hold.py` +9: three guarded statements, in `put` and `handle`;
- `games/link_drop_recovery.py` +11: a class attribute, one guarded statement in each of the two resumes;
- `native_session_io.py` +10: a class attribute, `set_input_mask`, one guarded statement in `_receive_loop`;
- `plugins/games.py` +9: a guarded import, one guarded wire call;
- `games/emulator_manager.py` +15: a guarded import, one guarded statement each in `launch` and
  `_prepare_retroarch_session_config`;
- `tools/unattended_frames.py` +54 / −2.

The module is named `hold_rewind` so that B2's hook-shape test (which counts `"import input_hold"`) is untouched.

## 2. Audio and picture during the rewind (from code and config)

- **Audio:** muted by `audio_rewind_mute = "true"`. The companion's audio streamer captures RetroArch's Pulse sink
  through its `monitor_source_name` continuously, so **the stream carries silence for those ~N frames (~0.3 s)**, as
  during the pause.
- **Picture:** `x11grab` captures the RetroArch window at a fixed rate, so **the stream sends the game stepping
  backward ~N frames over ~N / 60 s**. RetroArch's rewind indicator shows too (`notification_show_fast_forward`
  default `true`, not set here; one more key hides it, for the user / A). Then play resumes from the onset.
- End to end: frozen (the hold) → on the link's return, ~0.3 s running backward → play from the moment the silence
  began, input live.

## 3. Corrections found after the design's hash (`design_corrections.md`)

1. **The confirmed pause trails the real pause by ~4 frames, not "0-1".** Measured on the host from the companion's
   own command log (`pause_confirm_lag.py` → `pause_confirm_lag.json`, read-only):
   - **in 39 of 39 toggles the first `GET_STATUS` after `PAUSE_TOGGLE` (+13-19 ms) answers the old state**, and the
     next (+70-83 ms, after `pause()`'s 50-ms sleep) the new one;
   - pauses: 61.0-66.8 ms between them = **3.66-4.01 frames**.
   - Counting to the confirmation, as the design and the task's "the difference" literally say, would rewind ~3-4
     frames past the onset.
2. **The frame that reads the toggle runs no core frame** (the pause), which the fake core showed: with 3
   subtracted, the rewind landed 2 before the onset, deterministically.
   - **`PAUSE_CONFIRM_LAG_FRAMES = 4` = floor(3.66 + 1)** is subtracted and logged on every row.
   - The fake now lands 1 frame before the onset in every trial: ±1. If the real toggle's frame does run, it lands
     0-1 frame after. ±1 either way.
   - A deviation from "the difference", disclosed. It is the difference corrected by a measured, constant lag.

## 4. Tests (`tests_input_hold_rewind.txt`, `tests_input_hold.txt`, `tests_regression.txt`)

**`tests/input_hold_rewind`: 22 OK** (from the tree; 4 runs in the copy after the fix, all OK). The **fake core** is a
loopback UDP server behaving as measured:
- 60 fps;
- every pending datagram read once per frame;
- `GET_STATUS` answered with the state before that frame's hotkeys;
- `PAUSE_TOGGLE` / `REWIND` as frame hotkeys;
- the counter −1 when rewinding, +1 when playing.

The **fake emulator** pauses and resumes it as `EmulatorManager` does. The recovery is the real `LinkDropRecovery`;
the dispatcher is B2's.

The cases:
- **the count:**
  - from the two stamps;
  - the FIFO aligned across a skipped hold;
- **the cap:**
  - the parse table;
  - a 0.6-s silence with cap 10: requested 10, rewound 10 ± 1;
- **the confirmed rewind:**
  - rows `desync_pause → input_release → resumed`, all fields;
  - `counter_after` 0 ± 1;
  - **the fake core's own counter back at the onset's ± 1**;
  - masked on every datagram, unmasked after;
  - the core playing;
- **`rewind_failed` → the resume still happens** in four ways:
  - `GET_STATUS` unanswered within 2 frames;
  - a session config without `rewind_enable` (and no `REWIND` sent);
  - no port;
  - the transport raising.
  The rows are `desync_pause → rewind_failed → resumed` and the core is playing in every case;
- **flag absent:**
  - B2's exact rows and calls, no `REWIND` seen;
  - the parse / wire table (ignored rows);
  - a fresh process with `HOLD` alone, or nothing, imports no `hold_rewind`; with both flags, it does;
- **the config:**
  - the masked hash, flag absent, = the predecessor's; flag on = + the block;
  - the four keys once each, with the bytes per core (snes9x, bsnes, PSX, unknown) and at cap 10;
  - a base with a rewind key is left alone;
- **the handover:**
  - hold → v2 takes over → the hold's release does nothing → v2's exit rewinds once (`via controller_return`, the
    fake's counter at the onset ± 1);
  - a v2 pause with no hold is not rewound;
  - a stale pending hold is not used by a later pause;
- **the hooks' shapes;**
- **`--net`:**
  - the per-episode net and excess;
  - without `--net`, the CLI = the predecessor's.

**B2's `tests/input_hold`: 19 OK, the file unchanged (no diff vs HEAD).**

**The regression set in the copy, all OK:**
- impairment 29, **recovery (E3-R2's) 17**;
- overlay 17, session_identity 88, audio_codec 20, encoder_rc 16, wan_adaptation 23, wan_telemetry 18,
  remote_ladder 26, remote_cap 16, start_rung 17, lan_loss_rule 21, link_report 9;
- adaptive_bitrate_shadow 21, native_source_contract 7, c5_m1 14, **ps1_look 13, ps1_look_helper 11** (added:
  `emulator_manager` changed);
- adaptive_bitrate_live 126 from the tree.

C3-F1's 1 error is pre-existing (the same as B1's / B2's).

**Flag absent** (`proof_flag_absent.py` → `proof_flag_absent.md`): **all five changed modules: identical.**

## 5. Disclosed

- **The fourth config key** (§1).
- **The lag subtraction** (§3).
- **The mask's trade-off:** masking is what the task asks, but in the undetectable "rewind refused" case it makes the
  forward-run frames neutral rather than the player's. `MASK_INPUT` is one constant.
- **The rewinder uses `EmulatorManager`'s private attributes:** `lock`, `_network_cmd_port`, and a raw socket,
  because the class's request clamps timeouts to ≥ 50 ms and logs every datagram.
- **A `py_compile` check wrote a gitignored `companion/__pycache__/hold_rewind.cpython-313.pyc`** (`-B` does not stop
  an explicit `py_compile`). Left in place: nothing deleted.
- **The execution budget** in `AGENTS.md` (10 reads / 15 commands / one deliverable) was exceeded. The prompt asked
  for the whole task as one run.
- **The bench's record had not landed;** A's directories were not read.

## 6. Files

**`b4_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`, `design_corrections.md`;
- `bench_check_before_write.txt`;
- `retroarch_binary_strings.txt`, `retroarch_saved_defaults.txt`, `rzip_sizes.py`, `savestate_sizes.json`,
  `pause_confirm_lag.py`, `pause_confirm_lag.json`;
- `b4.diff`, `diffstat.txt`;
- `proof_flag_absent.py`, `proof_flag_absent.md`;
- `config_hashes.py`, `config_hashes.txt`;
- `unattended_noflag_equal.txt`, `unattended_ux_r2_net.json`;
- `tests_input_hold_rewind.txt`, `tests_input_hold.txt`, `tests_regression.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:**
- `companion/hold_rewind.py` (new), `companion/input_hold.py`, `companion/games/link_drop_recovery.py`,
  `companion/native_session_io.py`, `companion/plugins/games.py`, `companion/games/emulator_manager.py`;
- `tools/unattended_frames.py`, `tests/input_hold_rewind/test_hold_rewind.py` (new);
- `patches/B4_INPUT_HOLD_REWIND.md`, `logs/b4_git_status.txt`.

The rules held:
- no stream, no companion restart, no adb, no gradle, no sudo, no nft;
- the Opal untouched;
- nothing fetched, nothing deleted;
- nothing of A's touched;
- nothing adopted;
- nothing committed.

The copy is `/tmp/b_b4` (`companion/`, `tools/`, `tests/`; `tests/recovery_ext` there only).

## 7. BENCH-R2 (session A): the questions this cannot answer

- **The blackout cell, hold + rewind:** `PRIVYHUB_IMPAIRMENT=blackout-4s@both,every=120s,seed=1` +
  `PRIVYHUB_INPUT_HOLD=250` + `PRIVYHUB_INPUT_HOLD_REWIND=1`, snes9x.
  - Expected per blackout:
    - one `desync_pause input_hold`;
    - one `input_release` with `rewound_frames` ≈ `requested_frames` (~17-20);
    - no `rewind_failed`;
    - `tools/unattended_frames.py --logs logs/games --span <window> --net` → **net unattended ≈ 0** per blackout.
  - **Q5:** the frame after the rewind is the onset's (the driver's view or a capture: the NCI cannot read it back).
- **Q1, CPU:** plain E1 rows per core (snes9x, Beetle PSX HW) with `rewind_enable` on vs off at idle play. Rewind at
  granularity 1 serializes the whole state each frame, which is ~1 GB / s on PSX (16 MiB × 60). It lands on E4's host
  floor.
- **Q2, memory:** RetroArch's resident size over 30 min with the 513-MiB PSX buffer.
- **Q3:** does 1.22.2 step back on `REWIND` while paused? If yes, a smaller method: no unpause.
- **Q4:** **does Beetle PSX HW with the hardware renderer rewind at all** (picture steps back; no "Rewind
  unavailable…" / "Failed to initialize rewind buffer")? If not, the flag is SNES-only: one table edit, said in
  the record and the config.
