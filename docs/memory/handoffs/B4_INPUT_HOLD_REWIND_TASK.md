---
memory_schema: 1
as_of: 2026-10-22
status: TASK HANDOFF — B4 (session B, software only): on the hold's release, rewind the core by the frames it ran without input before the pause landed, so a blackout costs the player nothing — behind `PRIVYHUB_INPUT_HOLD_REWIND=1` (absent = B2's hold byte for byte). The CPU cost of per-frame rewind per core and the live proof are session A's (BENCH-R2). DO NOT edit anything under `companion/` while `privyhub-bench-r1` is active — its driver restarts the companion between cells and would load half-written code. Nothing adopted; nothing committed
---

# B4 — rewind on release

**The user's idea (2026-10-22):** "We have the emulator, why not just rewind the game for however lost." The hold (B2) lands ~H = 250 ms after the silence begins, so the core runs ~15 frames without the player; on release, rewind those frames and the player loses nothing. The blackout itself needs no rewind: the core was paused for it.

Read first: `B2_INPUT_HOLD_2026-10-22.md` (the hold inside recovery v2: `note_input_hold` → `_enter_recovery(trigger="input_hold")`, `EmulatorManager.pause()`; `note_input_release` → `EmulatorManager.resume()`, `held_ms`; the handover to v2 at 5.35 s; the rate limit; `tools/unattended_frames.py` and `unattended_frames_core_running`), `companion/input_hold.py`, `companion/games/link_drop_recovery.py`, `EmulatorManager` (how it speaks to RetroArch: the command interface we already use for `PAUSE_TOGGLE` / `SAVE_STATE` / `LOAD_STATE`; whether it can send `REWIND` and read a frame counter), the RetroArch config the companion writes per launch (`rewind_enable`, `rewind_granularity`, `rewind_buffer_size`; `D_BASE_R3C_…` for how the core's paused state behaves), `E4_S2_…` / `E4_CLOSEOUT` (the host CPU floor — rewind's cost lands on top of it), `BENCH_R1_LAUNCH_2026-10-22.md` and the bench's record when it lands (what the hold did live).

## 0. Wait for the bench

Before the first edit under `companion/`: `systemctl --user is-active privyhub-bench-r1` must read `inactive` / not found (poll every 60 s). Reading code, writing the design and the tests' skeletons may proceed meanwhile; nothing under `companion/` is written until the unit is gone.

## 1. The design (hashed before the code)

- **The flag:** `PRIVYHUB_INPUT_HOLD_REWIND=1`. It is read only when `PRIVYHUB_INPUT_HOLD` is set; absent = B2's hold byte for byte (AST-identical hooked functions, the hold's 19 tests unchanged). Invalid = ignored, one `input_hold_rewind_config` row.
- **RetroArch's rewind, only under the flag:** when the flag is set, the launch config carries `rewind_enable = true`, `rewind_granularity = 1`, and a buffer sized from the core's savestate size × the cap (state the arithmetic per core; Beetle PSX HW's state is large — say the size from a real savestate on disk). Flag absent = the config byte for byte as today (the masked-hash method on the generated config).
- **The frame count:** on `input_hold`, record the core's frame counter at the silence's onset and at the moment the pause is confirmed (`EmulatorManager.pause()` returns `PAUSED`). The onset count is the counter at the last controller packet; if RetroArch exposes no counter over the command interface, derive it from the host's own frame log (`native_frame_sizes.jsonl` is per second; the encoder's frame count in `encoder.jsonl` / the sampler is per sample) and say which source and its resolution. **`frames_to_rewind` = frames advanced between onset and the confirmed pause, capped at 30** (`PRIVYHUB_INPUT_HOLD_REWIND_CAP`, optional, 5-120; default 30).
- **On release (`note_input_release`), before `resume()`:** rewind by `frames_to_rewind`. The mechanism, from the code: `REWIND` on the command interface acts per frame while the core runs — so the sequence is unpause, hold `REWIND` for N frames with input masked, release, resume normal input; or, if the core honours rewind while paused, the simpler path. State which, from RetroArch's source or its documentation as present on the host (nothing fetched). The frame counter after must read onset ± 1; the actual rewind achieved is logged (`input_release`: `rewound_frames`, `requested_frames`, `counter_before`, `counter_after`). A rewind that cannot be confirmed within 2 frames' time is logged `rewind_failed` and the resume proceeds without it — **the hold never fails because the rewind did.**
- **Not rewound:** a release that hands over to v2's own `controller_silence` path (the 5.35-s case) — **unless** v2's resume can take the same rewind cheaply; say so and, if it is one guarded call, include it behind the same flag (then a 20-s outage also costs nothing; note it in the record as a second use).
- **Audio:** what RetroArch does to audio during rewind (muted), and what the stream sends in those ~15 frames — from code, stated.
- **The cost, to be measured by A, written here as the question:** host CPU with `rewind_enable` on, per core (snes9x, Beetle PSX HW), at idle play; whether Beetle PSX HW with the hardware renderer rewinds at all (if it refuses, the flag is SNES-only and says so in the record and the config).

## 2. The code, the tests

- `companion/input_hold.py` / `link_drop_recovery.py`: the onset counter, the pause counter, `frames_to_rewind`, the rewind call, the new log fields; the rewind lives inside the hold's own release, one owner, as B2's rule.
- The launch config generator: the three rewind keys under the flag only.
- **Tests with a fake core** (`tests/input_hold/`): the count from the two counters; the cap; the rewind requested on release and confirmed; `rewind_failed` → resume still happens; the flag absent → no counter reads, no rewind, no config keys (the hold's tests unchanged and green); the config generator's masked hash flag absent = predecessor; the v2 handover case per §1.
- `tools/unattended_frames.py`: a `--net` view that subtracts `rewound_frames` from the core-running count per episode, so A's record can show the net.

## 3. Record

`evidence/B4_INPUT_HOLD_REWIND_2026-10-22.md` + `b4_2026-10-22/` (the design + hash, the diff, the tests, the config hashes, `redact_check.txt`, `manifest.sha256`); `patches/B4_INPUT_HOLD_REWIND.md`; `docs/KNOWN_ISSUES.md` (the top item); `docs/ROADMAP.md` (one line); `logs/b4_git_status.txt`; `SESSION_B_STATUS.txt`; `SESSION_B_DONE_2026-10-22B.md` (ten lines, with **BENCH-R2 sketched**: the blackout cell with hold + rewind — net unattended frames per blackout expected ~0, `rewound_frames` ≈ `requested_frames`; plain E1 rows per core with `rewind_enable` on vs off for the CPU cost; the Beetle PSX HW question).

Rules: the `/tmp/b_*` copy holds `companion/`, `tools/`, `tests/` only; no stream, no companion restart, no adb, no sudo, no nft, the Opal read-only, no gradle; **nothing under `companion/` written while `privyhub-bench-r1` is active**; nothing of A's touched (`bench_r1_2026-10-22/`, its record); nothing fetched, nothing deleted; nothing adopted; nothing committed.
