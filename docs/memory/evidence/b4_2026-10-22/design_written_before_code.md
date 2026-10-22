# B4 — rewind on the hold's release: design (written and hashed before any B4 code)

Task `handoffs/B4_INPUT_HOLD_REWIND_TASK.md`, session B. Baseline HEAD d4c9870 (B1-B3 committed there; `companion/`,
`tools/`, `tests/` clean at start). Predecessors = HEAD's files (`predecessors/`).

## 0. What the host carries (nothing fetched)

- **RetroArch 1.22.2**, an AppImage (the binary's version string). **No RetroArch source and no docs on the host.**
  What follows is from the binary's own strings and from the config the same binary saved with every key at its
  default (`~/.config/retroarch/retroarch.cfg`, `config_save_on_exit = "true"`, written 2026-09-15). Read-only.
- **The command interface (NCI) of 1.22.2**, from the binary's command table:
  - the hotkey-style commands include `REWIND`, `PAUSE_TOGGLE`, `FRAMEADVANCE`, `FAST_FORWARD_HOLD`. `REWIND` is the
    hotkey whose help text reads "Rewinds current content while key is held. 'Rewind Support' must be enabled.";
  - the query commands are `VERSION`, `GET_STATUS`, `GET_CONFIG_PARAM`, `READ_CORE_RAM` / `READ_CORE_MEMORY` (+ write
    forms), `LOAD_STATE_SLOT`, `SAVE_STATE_SLOT`, `PLAY_REPLAY_SLOT`, `SEEK_REPLAY <frame number>`, `SAVE_FILES`,
    `LOAD_FILES`, ….
  - **No frame counter is readable.** `GET_STATUS` answers `PAUSED` / `PLAYING` / `CONTENTLESS` + the content (the
    companion parses it today). `GET_CONFIG_PARAM` takes a fixed list (`video_fullscreen`, the directories,
    `netplay_nickname`, `active_replay`). `active_replay` answers `%lld %u %lld`, which reads as replay id / flags /
    the replay's frame. That is only there while a replay records or plays. Recording a replay to get a counter is
    not acceptable (disk, states, input movie).
- **Rewind in 1.22.2:** the keys `rewind_enable`, `rewind_granularity`, `rewind_buffer_size`,
  `rewind_buffer_size_step`, `audio_rewind_mute` ("Automatically mute audio when using rewind");
  `notification_show_fast_forward` ("Display an on-screen indicator when fast-forward, slow-motion or rewind is
  active"). The refusals it can print are "Rewind unavailable because this core lacks serialized save state support",
  "Implementation uses threaded audio. Cannot use rewind.", "Failed to initialize rewind buffer…", "Reached end of
  rewind buffer.", and the hardcore-achievements one. The audio driver here is `pulse`, which is not threaded.
- **The defaults, as the binary saved them:** `rewind_enable = "false"`, `rewind_granularity = "1"`,
  `rewind_buffer_size = "20971520"`, which is **bytes**, not MB (20 MiB); `audio_rewind_mute = "false"`;
  `notification_show_fast_forward = "true"`; `video_font_enable = "true"`; `menu_enable_widgets = "true"`.
- **What the companion's launch config is:** `privyhub-session.cfg` = the persistent `data/games/retroarch/retroarch.cfg`
  (25 lines, **no rewind key**) + the input override + cheat / storage / `pause_nonactive` + the PS1 look. Every key
  it does not set is RetroArch's compiled default, so rewind is off today. A7.3 found that RetroArch ignored a
  duplicate assignment appended after the persistent one. The rewind keys are absent from the base, so appending
  them is the only assignment. The generator also refuses to append if the base ever carries one.
- **Real savestates on disk** (`data/games/retroarch/states/<core>/`, RZIP, header `#RZIPv\x01#` + chunk size +
  **total uncompressed size**; one file per core fully decompressed = the header's size):

  | core (states dir) | core file | files | raw state, bytes | on disk (compressed), max |
  | --- | --- | ---: | ---: | ---: |
  | Snes9x | `snes9x_libretro.so` | 4 | 823,432-823,536 | 122,804 |
  | bsnes | `bsnes_libretro.so` | 2 | 284,304 | 108,802 |
  | Beetle PSX HW | `mednafen_psx_hw_libretro.so` | 29 | **16,777,240** (16 MiB + 24, every file) | 1,975,196 |

## 1. The flag

- `PRIVYHUB_INPUT_HOLD_REWIND=1`. It is read **only when `PRIVYHUB_INPUT_HOLD` is set and valid** (B2's
  `input_hold.parse`).
- **Absent:** B2's hold byte for byte. Nothing imports the new module (`companion/hold_rewind.py`; not named
  `input_hold_*`, so B2's hook-shape test, which looks for `"import input_hold"`, still counts one). The hooked
  functions are AST-identical with the B4 statements removed. The hold's 19 tests are unchanged.
- **Set but not `1`:** ignored, one `input_hold_rewind_config` row (`ignored: true`, the reason).
- **`1` while the hold is not active** (its value invalid): ignored, one row, reason "the hold is not active". No
  config keys.
- `PRIVYHUB_INPUT_HOLD_REWIND_CAP`: optional, 5-120, default 30. An invalid value is ignored, so the cap is 30, and
  the config row says so.
- A valid setting writes its `input_hold_rewind_config` row once: cap, fps, method, mask.

## 2. RetroArch's rewind in the launch config (flag only)

When the flag is on (the hold valid, `REWIND=1`), the generator appends one block to `privyhub-session.cfg`:

```
# PrivyHub B4 input-hold rewind (PRIVYHUB_INPUT_HOLD_REWIND=1)
rewind_enable = "true"
rewind_granularity = "1"
rewind_buffer_size = "<bytes>"
audio_rewind_mute = "true"
```

- **`rewind_buffer_size`** is in bytes (RetroArch's own saved default is `20971520`). It is sized so that `cap + 2`
  states fit even with no delta compression at all (RetroArch stores per-frame deltas, so real capacity is larger):
  `ceil_MiB(raw_state × (cap + 2))`. At the default cap 30:
  - **snes9x:** 823,536 × 32 = 26,353,152 → **26 MiB = 27,262,976**;
  - **bsnes:** 284,304 × 32 = 9,097,728 → **9 MiB = 9,437,184**;
  - **Beetle PSX HW:** 16,777,240 × 32 = 536,871,680 → **513 MiB = 537,919,488**. At cap 120 that is 1.9 GiB. The
    host has 15 GB, ~11 GB available at start. The buffer fills as play goes on, so the resident cost rises toward
    this.
  - **A core with no state on disk** (fceumm, blastem, …): RetroArch's own 20 MiB (`20971520`).
- **`audio_rewind_mute = "true"` is a fourth key, beyond the task's three, disclosed.** The task wrote "(muted)", but
  this RetroArch's default is `false`. Without the key, RetroArch would play the rewind's audio. Muting it is what
  the task describes, so the flag pins it.
- **Not set:** `notification_show_fast_forward`. Its default `true` means RetroArch draws its rewind indicator in the
  window while rewinding, and the stream will carry it (§6). This is left for the user / A: one more key under the
  same flag hides it.
- **Flag absent:** the generated config is byte for byte today's. The masked-hash method: the generator is run from
  the predecessor and from B4's file on the same inputs, `network_cmd_port = "<n>"` masked (a random port per
  launch), sha256 of each; equal. With the flag on, the diff is the block above only.
- **Where it hooks:** the launch function sets `self._hold_rewind_core = core_path.name` (one guarded statement,
  after the PS1 look). `_prepare_retroarch_session_config` appends the block (one guarded statement, before the
  write). Both are guarded by a module-level `_hold_rewind is not None`, which is imported only with both flags set.

## 3. The frame counter: source and resolution

**There is no core frame counter on the NCI** (§0), and the host's own frame logs count encoder frames, not core
frames. `native_frame_sizes.jsonl` is per second. The encoder's count goes on at 60 / s on a paused core (B2,
measured). So neither shows the core stopping.

**The counter is the host's monotonic clock × the core's nominal 60 fps**, read at two moments:
- **the onset:** the receive loop's `time.monotonic()` of the last controller packet (`last_any_packet_at`, which is
  the detector's `_silence_start`).
  - B2's detector emits `("hold", age_ms)` at detection time `now`, so `onset = put_time − age_ms`.
  - The dispatcher's `put` runs synchronously in the loop at `now`. It stamps the put time into a FIFO.
  - The worker pops one stamp per `hold` event, in order, on every path, the user's-pause skip included. The stamps
    and the events cannot misalign.
  - Packets arrive every ~2.3 ms (≈ 430 / s), so the onset is within ~2.3 ms of the player's last input reaching
    the host.
- **the confirmed pause:** the dispatcher's `_paused_at`, B2's own `self._clock()` taken when `note_input_hold`
  returns True, i.e. `EmulatorManager.pause()` returned with `GET_STATUS PAUSED`.
  - `pause()` sends `PAUSE_TOGGLE` and then polls `GET_STATUS` in a loop with a 50-ms sleep after a miss. The first
    poll is normally answered in the same NCI poll as the toggle.
  - So the confirmation trails the real pause by **0-1 frame typically, ≤ ~4 frames** on a missed first poll.
- **`counter_before` = round((paused_at − onset) × 60)**: the frames the core advanced since the onset, counted from
  0 at the onset.
  - **Resolution: one frame.** It overcounts by 0-1 frame typically, ≤ ~4 worst case: the confirmation lag.
  - Nominal 60 against the cores' real 60.10 (SNES) / 59.94 (PSX) is < 0.05 frame over 20.
  - **Overcounting is the safe side.** A rewind past the onset returns the player to a moment they had controlled,
    and they replay ≤ ~4 frames they already played. Undercounting would leave frames run without them.
- **`frames_to_rewind` (`requested_frames`) = min(counter_before, cap)**, cap 30 by default. At H = 250: ≈ (250 +
  ≤ 50 detection + the pause round trip) ms ≈ 18-20 frames.

## 4. The rewind on release: the mechanism

**Which mechanism, and why:**
- **Whether 1.22.2 honours `REWIND` while paused cannot be settled from what the host carries.** There is no source.
  The binary's strings describe rewind only as "while key is held".
- So the code uses the path that holds either way, the task's first form: **unpause, hold `REWIND` for N frames
  with the player's input masked, release, resume.**
- If A finds that paused rewind works (§7 Q3), it is a smaller follow-up: the method is one constant.

**The NCI semantics this relies on** (RetroArch's documented hotkey model; the binary lists `REWIND` among the
hotkey commands):
- an NCI hotkey command is "pressed" for the frame whose poll reads it;
- holding the key = one datagram per frame;
- a frame that sees none runs forward.

**The sequence** (`hold_rewind.Rewinder.rewind`, called by the recovery before its resume; under
`EmulatorManager.lock`, the RLock `pause()` / `resume()` take, so no UI pause / resume can interleave; raw loopback
UDP to `emulator._network_cmd_port`, the port the companion wrote into the launch config):
1. **Preconditions** (any failing → no NCI command, a `rewind_failed` row with the reason, the resume proceeds):
   - a pending hold of this pause episode (key: the recovery's `_state_since` at the hold, unchanged by a handover,
     changed by any new pause);
   - `requested ≥ 1`;
   - the port is known;
   - the session config on disk carries `rewind_enable = "true"`: the running RetroArch was launched by this
     companion with the flag. This guards "the REWINDs are ignored and the core runs forward with no input".
2. **Mask the input:** the bridge's `masked()` reads True (expires by itself after 1.0 s whatever happens), and
   `controller._neutralize()` sets all four pads neutral. The receive loop skips `_apply_report` while masked: one
   guarded statement after B2's `on_packet`, behind a class attribute `_input_mask = None`.
3. `REWIND`, then `PAUSE_TOGGLE` in the same instant: the same NCI poll, so the frame that unpauses is already a
   rewind frame. If RetroArch reads the pause after the rewind bit, this is −1 step: within ±1.
4. `REWIND` every half frame (8.3 ms) until `(requested − 0.5) / 60` s have passed since step 3. Every frame's poll
   sees at least one, and two in one poll are one press.
5. **Confirm within 2 frames' time:** one `GET_STATUS` on the same socket, timeout **2 / 60 s = 33 ms**, one try.
   (`_retroarch_network_request` clamps timeouts to ≥ 50 ms, hence the raw socket.)
   - NCI datagrams on loopback are read in order in RetroArch's per-frame poll, so an answer means every `REWIND`
     before it was read.
   - It must say `PLAYING`, which means the toggle landed.
6. **Unmask** (`finally`, always), then B2's `resume_game()` exactly as today.
   - After a confirmed rewind it finds `PLAYING` and sends no toggle.
   - After a failed one it toggles if still paused.
   - **The hold never fails because the rewind did:** the rewinder never raises. Every exception becomes
     `rewind_failed`, and the resume follows in all cases.

**The rows:**
- **`input_release`** (a confirmed rewind): `requested_frames`, `rewound_frames`, `counter_before`, `counter_after`,
  `onset_to_pause_ms`, `rewind_ms`, `via` (`input_release` / `controller_return`), `method`
  (`unpaused_per_frame`), `cap`.
- **`rewind_failed`**: the same fields + `reason`.
- Then B2's `resumed via input_release` row, unchanged. `tools/unattended_frames.py --net` reads `rewound_frames`
  from the `input_release` rows.

**`rewound_frames` and `counter_after`, stated for what they are:**
- `rewound_frames = min(requested, round((t_last − t_first) × 60 + 0.5))`: the frames over which `REWIND` was held,
  by the same clock, ±1.
- `counter_after = counter_before − rewound_frames`, so 0 ± 1 = the onset.
- **These are the commands RetroArch acknowledged reading, on the clock counter. They are not an observed core
  position.** 1.22.2's NCI has no frame read-back (§0).
- **Not detectable over the NCI:**
  - a core that refuses rewind;
  - a buffer that failed to initialise;
  - a buffer exhausted.
  In all three the `REWIND`s are ignored and the core runs ~N frames forward with the player's input masked. That
  is the failure mode the session-config check (step 1) narrows and BENCH-R2 must look for (§7).

**The handover (v2's `controller_silence` at 5.35 s): rewound too, one guarded call.**
- The hold's pause is the pause v2 takes over: no second pause, and `_state_since` is unchanged. So the frames run
  without the player are still the hold's onset → pause frames, and the pending hold matches the episode.
- v2's resume is `_maybe_exit_controller_pause` → `self._resume_game()`. One guarded statement before that call
  runs the same rewind (`via: controller_return`).
- Then a 20-s outage also costs nothing. It is recorded as the second use.
- A v2 pause without a hold has no pending hold, so no rewind. The client's own gate (`note_stream_ready`) and the
  give-up save path are not rewound, and are untouched.

**One owner (B2's rule):** the rewind lives inside the recovery's own two resumes. The dispatcher only stamps and
records. Hooks:
- `input_hold.HoldDispatcher.put`: +1 guarded (the stamp);
- `.handle`: +2 guarded (pop the stamp; record the pending hold after `_paused_at`);
- `LinkDropRecovery.note_input_release` / `_maybe_exit_controller_pause`: +1 guarded each, the class attribute
  `_input_hold_rewind = None`;
- `native_session_io._receive_loop`: +1 guarded, the class attribute + setter;
- `plugins/games.py`: a guarded import + one guarded wire call;
- `emulator_manager`: a guarded import + 2 guarded statements.

Every guard tests a name that is `None` unless both flags are set.

## 5. Input masking: stated trade-off

The task asks for the rewind with input masked: the player's live input is not applied to frames being rewound
through. This costs something in the undetectable failure case (§4): a refused rewind becomes ~N frames run forward
with neutral input, not with the player's. Masking is one module constant (`MASK_INPUT`), on per the task. The mask
cannot outlive 1.0 s.

## 6. Audio and picture during the rewind (from code and config)

- **Audio:** RetroArch, with `audio_rewind_mute = "true"` (pinned under the flag, §2), mutes its output while
  rewinding. The companion's audio streamer captures RetroArch's own Pulse sink through that sink's
  `monitor_source_name` (`NativeAudioStreamer`, `native_session_io.py`), continuously. So for the ~N frames
  (~0.3 s) **the stream carries silence**, as it does during the hold's pause.
- **Picture:** the encoder captures the RetroArch window with `x11grab` at a fixed frame rate (`native_stream.py`).
  RetroArch draws each rewound frame, so **the stream sends the game stepping backward, ~N frames over ~N / 60 s**.
  With `notification_show_fast_forward` at its default `true`, RetroArch's rewind indicator is drawn too (§2).
  Then play continues from the onset.
- What the player sees, end to end: the picture frozen (the hold) → on the link's return, ~0.3 s of the game
  running backward → play from the moment the silence began, their input live again.

## 7. The cost and the open points: session A's questions (BENCH-R2)

- **Q1 (CPU):** host CPU at idle play with `rewind_enable` on vs off, per core (snes9x, Beetle PSX HW), on the plain
  E1 rows. Rewind at granularity 1 serializes the whole state every frame: snes9x ~0.8 MB × 60 / s, **Beetle PSX
  HW 16 MiB × 60 / s ≈ 1 GB / s** of serialize + delta. That lands on top of E4's host CPU floor.
- **Q2 (memory):** RetroArch's resident size over a 30-min session with the 513-MiB PSX buffer.
- **Q3 (paused rewind):** with the core paused, do `REWIND` datagrams step it back on 1.22.2? If yes, the method can
  drop the unpause.
- **Q4 (PSX HW):** does Beetle PSX HW with the hardware renderer rewind at all: the picture steps back, no
  "Rewind unavailable…" or "Failed to initialize rewind buffer" on screen or in the RetroArch log. **If it refuses,
  the flag is SNES-only.** The generator writes the block only for the cores A has seen rewind, and the record and
  config say so.
- **Q5 (the effect):** on the blackout cell, the frame after the rewind equals the onset's (the driver's view or a
  capture), since the NCI cannot read it back.

## 8. Tests (`tests/input_hold_rewind/`, a fake core; B2's 19 untouched)

**The fake core:** a loopback UDP server that behaves like 1.22.2's NCI at 60 fps:
- each frame it reads every pending datagram;
- `PAUSE_TOGGLE` toggles;
- `REWIND` presses rewind for that frame;
- `GET_STATUS` answers `GET_STATUS PLAYING|PAUSED …`;
- then, if playing, the counter goes −1 (rewinding, with history) or +1;
- options: ignore `REWIND` (a refusing core); stop answering (a dead NCI).

**The fake emulator:** `lock`, `_network_cmd_port`, `pause()` / `resume()` through `GET_STATUS` / `PAUSE_TOGGLE`.

The cases:
1. **the count:** `counter_before` from the two stamps (fake clock), and the FIFO alignment across a skipped hold;
2. **the cap:** 1 s onset → pause gives 30; cap env 10 gives 10; cap invalid gives 30 + a row; outside 5-120
   ignored;
3. **the rewind requested on release and confirmed:** the fake core's real counter after = its counter at the onset
   ± 1; the rows `input_release` (fields) then `resumed via input_release`; the mask was on during the rewind and is
   off after;
4. **`rewind_failed` → the resume still happens:** a dead NCI, a missing config key, no port. The resume is called
   every time, and the state is `PLAYING`;
5. **flag absent → nothing:**
   - with `_input_hold_rewind` None: no stamp, no counter read, no NCI datagram, B2's exact rows;
   - a fresh process with only `PRIVYHUB_INPUT_HOLD` imports no `hold_rewind` (plugins, emulator manager, session
     io);
   - with `REWIND=0` / `yes` one ignored row;
6. **the config:**
   - the generator's masked hash with the flag absent = the predecessor's;
   - with the flag on, the four keys once each, the bytes per core (snes9x / bsnes / PSX / unknown);
   - a base carrying a rewind key is refused;
7. **the handover:** hold → v2's `controller_silence` takes over → v2's controller-return exit rewinds once
   (`via controller_return`), then resumes. A v2 pause with no hold does not rewind;
8. **the hooks' shapes**, and the proof: the AST with the B4 statements removed = the predecessor, per function;
9. **`tools/unattended_frames.py --net`:**
   - per episode, core-running minus `rewound_frames`, floored at 0, with the excess shown as
     `rewound_beyond_threshold` (the rewind also returns the first 250 ms, which the measure does not count);
   - without `--net` the output is byte for byte the predecessor's, on synthetic logs and on UX-R2's preserved logs.

## 9. Rules held

The copy is `/tmp/b_b4`: `companion/`, `tools/`, `tests/` only. The rules:
- no stream, no companion restart, no adb, no gradle, no sudo, no nft;
- the Opal read-only;
- no addresses or identifiers;
- nothing of A's touched;
- nothing fetched, nothing deleted;
- nothing adopted;
- nothing committed.

**Nothing under `companion/` in the tree is written until `systemctl --user is-active privyhub-bench-r1` reads
inactive / not found** (polled every 60 s).
