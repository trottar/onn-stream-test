# B61 — design, written before any B61 code (the N64 Home-hold freeze)

Queue: `handoffs/QUEUE_2026-11-08W.md` §B61. Baseline `6fcd2f23` (HOME-7 committed). Built in `/tmp/b_q15w_work`
(companion/, tools/, tests/, PrivyHub/ only), inside `PRIVYHUB_N64=1` (adopted, G-A15). No title, serial or path here:
T6 is HOME-7's label.

## 0. Settled

**The sequence at the loss** (C23; read in place: the recovery log, RetroArch's per-launch command log
`logs/games/retroarch_control_probe.txt`, T6's game log, the host samples, A's capture
`data/games/ps2/probe/home7/n64_showinfo.txt`):

| UTC | what |
| --- | --- |
| 22:33:19.6-22:33:23.6 | the earlier Back: `PAUSE_TOGGLE` → `PAUSED`; a `SAVE_STATE_SLOT 0` **into the paused core**, answered; RetroArch logs `[State] Saving state … save task COMPLETED` |
| 22:33:32.1 | the resume → `PLAYING`; the last answered command of the session |
| 22:35:28.2 | the Home press (the stall onset) |
| ≈22:35:29.39 | the stall's scratch **`SAVE_STATE_SLOT 9` into the running core** (onset + 1272 ms; the row is logged at 29.485, after its 100-ms ack wait) |
| **22:35:29.42** | **the last distinct frame of A's capture** (+108.035 s); every later second has 0 distinct frames |
| 22:35:29.9 → 22:36:42 | every `GET_STATUS` times out (3 tries each); 46 `stall_resume_failed` (~1.4 s apart); `SAVE_FILES` and `QUIT` unanswered at the stop; RetroArch killed by SIGTERM (`returncode 1`, `forced`) |

- **RetroArch never processed the slot-9 save.** Its log has no `[State] Saving state …state9` line, though a PS1
  session's slot-9 save logs one. The log ends at the paused save's lines (the trailing `plugin_start_gfx` is the
  core's buffered stdout, flushed at exit; it ends T5's clean logs too). There is no `Unloading game`.
- **RetroArch spun:** its CPU went from 20.2 % (22:35:26) to 92.1 % and then 100.0 % of a core (22:35:56, 22:36:26).
  This is not a deadlock: the main thread was busy inside the core, so the frontend never polled its command port
  again.
- **The picture stopped within ~2 frames of the running save,** and 1.2 s after the Home press. So the press itself
  (the pads neutralised) did not stop the game.
- **Every N64 save that worked was into a paused core:** T6's slot 0 at 22:33:23, and T5's SAVE / LOAD (C22, from the
  onn's paused menu). T6's was the only save ever sent into a running N64 core, and it is the one that hung.

**The reproduction (B, headless, the hub's display, no stream, no pad, no title):**
- **The fixture** is a synthetic ROM: a header plus a VI loop that flips the framebuffer origin each vertical
  interrupt. It runs on the hub's RetroArch and core, with temp config / state / save / XDG folders and a read-only
  copy of the hub's `.opt`.
- **The sequence:** 3 s of `GET_STATUS` at 4 Hz, three running `SAVE_STATE_SLOT 9` with 4 s of polling after each,
  then a paused save.
- **Result:** every running save was acknowledged in 13-24 ms, with no silence longer than one poll (0.27 s); the
  paused save likewise. **With an x11grab capture of the window running: the same.** So A's capture is not
  implicated, and a running save does not hang the core as such.
- **The first fixture is the evidence of the mechanism:** a ROM that never swaps a frame left the main thread at
  100 % inside the core, with the command port silent for 25 s. RetroArch polls its commands only between
  `retro_run`s, so a core that does not come back silences the port, exactly as T6's did.
- **T6's hang needs the real title's state** (the fixture draws nothing). The reproduction with T6 is **A's step**:
  HOME-8 stage 1, unattended, T6 at its menu, a running `SAVE_STATE_SLOT 9` and then a paused one, the port polled at
  4 Hz. B loads no real title.
- **The core's mechanism is not identified.** A candidate, recalled and not proven: GLideN64's frame-buffer copy to
  RDRAM, which a title with frame-buffer work has pending in a running core and a paused core has flushed.

## 1. The fix: option 3 — no state save into a running N64 core; the hold's return a plain resume

**Why not the others:**
- **(1) an asynchronous save with a longer N64 budget:** the save never ran and the core never returned in 70 s. A
  longer budget changes nothing, and running the save on another thread does not stop the frontend's main loop
  spinning inside the core.
- **(2) a `GET_STATUS` poll tolerant of the gap:** the port never came back. Tolerance would only delay the same
  frozen game.
- **(3) removes the one operation that preceded the hang,** never part of a working N64 save. **The cost, disclosed:**
  an N64 hold or stall no longer rewinds to the onset. The return resumes where the game was paused, so the
  0.4-1.3 s the player did not see are lost (PS1 / SNES / PS2 keep their rewind).

**Built (inside `PRIVYHUB_N64=1`: every hook keys on `EmulatorManager._n64_core`, set only by an N64 launch):**
1. **`EmulatorManager._n64_core`:** the core file name on an N64 launch; None otherwise (the class default, reset with
   the process).
2. **`rewind_cores.Cores.save`:** an N64 session sends no scratch save, for either the silence or the stall kind. One
   row `state_save_skipped`, `reason: "n64: no save into a running core"`, `core`, `kind`; `saves_skipped_n64`
   counts them.
3. **`rewind_cores.Cores.release`:** an N64 session's release is `rewind_skipped`, `reason: "n64: plain resume (no
   state)"`. The stall / hold then resumes through today's `resume()` (`GET_STATUS`, `PAUSE_TOGGLE`, `PLAYING`).
4. **`EmulatorManager._capture_slot0_state`** (the user's SAVE, the recovery save; defence in depth, since both are
   reached from a paused core today):
   - an N64 session whose `GET_STATUS` reads `PLAYING` is paused first (`PAUSE_TOGGLE`, wait `PAUSED`), saved, then
     resumed;
   - a probe row `n64_paused_for_save`;
   - a core that will not pause → the save refused ("N64: the core did not pause for the save"), never sent running.
5. **The storm bound** (`stall_signal.StallSignal.resume`, N64 only, through the hold's rewinder `rw.emulator`):
   - after **3** consecutive resume failures whose error says "did not respond", one row `command_port_silent`:
     `fails`, `since_ms`, `via`, `retroarch_state` (the process's `/proc` state letter and its CPU % over 0.2 s,
     best effort: spinning vs stopped);
   - then **one resume try every 10 s** instead of every ~1.4 s. The skipped calls return at once, with no row and no
     rewind call; each later try that fails logs one `stall_resume_failed` with `backoff_s: 10` and `skipped: <n>`;
   - a success resets it, and the `resumed` row carries `after_silent_fails`;
   - **the fallback is today's plain resume, retried, never a state:** a port that answers again resumes the game.
     If it never answers (a hung core), the game stays where it froze until the user's Stop. The rows now say so
     once, instead of 46 times.

**Never a frozen game:** with (2)-(4) no N64 path sends a save into a running core, the only trigger seen. (5)
bounds what remains.

**Absent = today:**
- without the flag no N64 launch happens, so `_n64_core` stays None and every new branch is skipped;
- **PS1 / SNES / PS2 sessions: byte for byte** (their saves, releases, captures and the 1.4-s resume retries
  unchanged).

## 2. Tests (`tests/b61_n64_hold/`; fakes only; temp dirs removed at exit)

- **`Cores.save`:** an N64 emulator → no datagram sent, the `state_save_skipped` row, the counter; a PS1 emulator →
  `SAVE_STATE_SLOT 9` sent as today (a fake command port).
- **`Cores.release`:** N64 → `rewind_skipped` "n64: plain resume", no `PAUSE_TOGGLE` / `LOAD_STATE_SLOT` sent; PS1
  with a matching save → today's load sequence.
- **`_capture_slot0_state`** (fake network): N64 `PLAYING` → `PAUSE_TOGGLE`, the save, the resume, in that order; N64
  already `PAUSED` → no toggles; N64 not pausing → refused, no save sent; PS1 `PLAYING` → today's (no toggle).
- **The bound:**
  - a fake recovery / resume that times out: N64 → three tries ~1.4 s apart, then one `command_port_silent`, then
    tries only every 10 s (a fake clock), each logged with `backoff_s`. Over 60 s: ≤ 3 + 6 tries instead of ~43;
  - a late-answering port (the 5th try succeeds) → `resumed` with `after_silent_fails`;
  - PS1 → every try made, every failure logged (today);
  - no rewinder → today.
- **Absent:** `_n64_core` None on a fresh manager; a SNES / PS1 launch through B59's fake RetroArch tree leaves it
  None; the four paths as today.
- **Mutations** (each expected caught): the save skip removed; the release skip removed; the capture's pause removed;
  the bound's count 3 → 1000; the back-off applied to PS1.

## 3. For A (HOME-8)

- **Stage 1:** T6's reproduction (above), unattended, recorded.
- **C25:** the Home hold → `state_save_skipped` (n64) at the onset, `rewind_skipped` "n64: plain resume", `resumed`;
  the game where it was paused, never frozen. A `command_port_silent` row is a not-met → to B, with T6's
  reproduction.
