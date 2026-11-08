# B52 — the PS2 load: MTVU off, the load after the game's ELF, "confirmed" = the picture moving (design, hashed before code)

Queue: `handoffs/QUEUE_2026-11-08S.md` §B52. HOME-5 C12'c: both PINE loads answered OK and PCSX2 logged `Loaded state
from slot 1.`, then ten `TLB Miss` lines at EE hardware-register addresses on each resume — "Load is just a black
screen". Baseline `65186c66`; built in `/tmp/b_q11s_b52`. **Inside `PRIVYHUB_PS2=1`; absent = today byte for byte.**

## 0. Settled (HOME-5's PCSX2 log excerpt and the hub's files, read in place; PCSX2 not started)

**S1. The fault: two causes, both removed.**
- **MTVU.** The hub's ini has `[EmuCore/Speedhacks] vuThread = true` (PCSX2's default, kept by B49's merge). PCSX2
  printed its own warning at both loads, `MTVU speedhack is enabled, saved states may not be stable`. The state's VU1
  thread section (`SaveStateBase::mtvuFreeze` is in the binary) is taken from a separate thread.
- **A load before the game's ELF.** HOME-5's relaunch log has **no `ELF Loading:` line at all**: the start handoff
  paused PCSX2 at 2.0 s, before the BIOS booted the game. Both loads went into a VM whose game had never started, and
  the TLB misses were identical at both (the same pcs and addresses), as from the same bad start. PCSX2 logs `ELF
  Loading: {}, Game CRC = …, EntryPoint = …` when the game boots (the binary's strings). PINE cannot say it: its 0x0C is
  `GetDiscSerial`, known from the disc's open during the BIOS (the binary's dispatch).
- **MTVU off, and its cost.** The hub's margin with MTVU on: the EE thread mean 28-31 % / max 62 %, VU1 18-22 % of a
  core, a core max 67 %, GPU ≤ 30 % (H3-P1 / H3-P2). MTVU off puts VU1 back on the EE thread. **Expected:** that thread's
  mean ~50 %, its peak toward ~85-100 % of one core in a heavy scene. So a heavy title (H3-P1's T2) may drop frames;
  the light ones should not. A measures it (`pidstat -t` beside H3-P2's).
- **No reason was found to keep MTVU** (it helps CPUs with few cores; the hub has 6 / 12).
- **HOME-5's save (made with MTVU on, before the ELF had booted twice over) is treated as unusable.** It stays on the
  hub (nothing deleted), and the user makes a new save at HOME-6. PCSX2 keeps the old file as `.p2s.backup` when slot 1
  is saved again.
- **Kept:** `BackupSavestate` (a restore path; B51's file wait already handles the new file); fast boot.

**S2. The load-at-boot case: picked — hold the load until the game's ELF is up.** At a LOAD, if this launch's PCSX2
log has no `ELF Loading:` line yet:
1. the companion resumes PCSX2 (the hotkey, PINE confirming running);
2. it waits ≤ **30 s** for the line (fast boot reaches it in a few seconds);
3. it pauses PCSX2 again;
4. then it loads.

Never seen → PS1-shaped error "The game is still starting; play a moment, then load again", the game left paused. The
in-game load (paused through Game State, the user's usual path) has the line already and goes straight on. Both paths
end in the same check (S3).

**S3. "Confirmed" = the game runs from the state.** After the PINE load (OK, and `Loaded state from slot N.` within
3 s as B51), the companion:
1. **resumes** PCSX2 (the hotkey, PINE status running);
2. **samples the PCSX2 window's picture** every 0.2 s for up to **5 s**. Each sample is one `x11grab` frame of the
   PID's window, scaled to 64×36 gray, hashed, with its mean. The window is used, not the encoder, because at a Game
   State load the stream is stopped;
3. stops at the first of:
   - **ok:** 3 distinct sample hashes, none equal to the pre-load picture's, not all near-black (mean > 20), PINE
     running, and no `TLB Miss` in PCSX2's log since the load;
   - **fault:** a `TLB Miss` line since the load;
   - **static:** 5 s with fewer than 3 distinct, or all black, or PINE not running;
4. **pauses** again.

The game is thus left paused, as PS1's load leaves it, having run the ~0.3-1 s the check took (disclosed). Answers:
- ok → the PS1 payload, `confirmed: true`, `verification: "picture"`;
- static / fault → `EmulatorError("The game did not resume from the save")`, PS1's shape (HTTP 503 `{"ok": false,
  "error": …}` on this API, as B51 stated), the game paused.

The game log: `PS2 load: slot N pine 0x0a ok; picture <ok|static|fault> <s>s`.

## 1. The code (inside the flag)

- `ps2_session.settings_for`: `[EmuCore/Speedhacks] vuThread = false`.
- `Session`:
  - `grab` (injectable: one window frame → bytes);
  - `picture_hash()`;
  - `log_path` (default `pcsx2_log_path(root)`; B53 points it at the per-launch file);
  - `elf_started()`;
  - `wait_elf(bound)`;
  - `check_picture(pre, log_offset, bound)` → (`ok` | `static` | `fault`, seconds).
- `EmulatorManager._pcsx2_load_state`: the PS1 preconditions, the hand-over, the ELF hold, the pre-load hash, the PINE
  load, the log line wait, `resume`, `check_picture`, `pause`, the answer.

## 2. Tests (`tests/ps2_session`, < 10 s, everything faked)

- **The picture:** moving → `confirmed`, `picture ok`; static → the error, the game paused; a `TLB Miss` line → `fault`
  → the error; all black → static.
- **The ELF hold:** no `ELF Loading:` → resume, the line appears, pause, then the load (`picture ok`); never → the error
  and paused.
- **The ini:** `vuThread = false`.
- **The request bytes** still `[6][0x0A][slot]`.
- B51's load tests move to the new meaning (`verification: "picture"`; disclosed).
- **Absent → today** (B49 / B50's absent tests).
