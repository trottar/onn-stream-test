# SESSION B — done, 2026-11-08 V (QUEUE_2026-11-08V: B59, B60; run 20:44-20:58Z)

- **Baseline:** `a8a505e5` (queue U committed).
- **Checked first:**
  - only the companion and `privyhub-diag` active;
  - `git status --short` showed only the two prompt files (`_cowork_prompt_b.txt` modified, the queue file new).
- **Not done:**
  - nothing committed, adopted or installed;
  - no stream, no companion or keeper restart, no adb, no sudo, no nft;
  - no emulator started; no APK built (no client change needed).
- **Nothing fetched** (no N64 core, no Dolphin), **nothing written to the drive, nothing deleted.**
  - The drive's N64 and GameCube folders were counted by extension and size only.
  - Dolphin's dependencies were read with `apt-cache` / `dpkg -s`; nothing was installed.

## What was built

1. **B59, N64 through RetroArch, behind `PRIVYHUB_N64=1`** (`evidence/B59_N64_LAUNCH_2026-11-08.md`; applied to the
   tree, uncommitted):
   - **the core:** Mupen64Plus-Next (GLideN64, native resolution). Not on the hub and not in the AppImage, so
     **fetch needed** (`tools/n64_core_check.py`, exit 3). ParaLLEl-N64 is kept by name only;
   - **the list:** the `n64` system in place from the drive's N64 folder (13 `.v64`). The folder is named by `N64_DIR=`
     in the gitignored paths file; the new `companion/inplace_library.py` generalises B49's listing;
   - **the ports:** four always (`--device=1..4:1`; `ports_set` 4, no multitap), so hold-to-join fills P1-P4 and
     **never shows "Setting up 4 players…"**;
   - **the pad:** the C-buttons on the right stick; A on south, B on west, Z on the left trigger. The `.opt` is merged
     at launch; the input file has no D-pad mirroring;
   - **the states:** RetroArch's save states and the recovery stack, as PS1's;
   - **the logs:** the game log `N64 launch: core=mupen64plus_next ports=4`; `diag_read` labels `n64`;
   - **the metric:** `tools/n64_frames.py` (the title's own frame rate and hitches, which the fixed-60 stream hides);
   - **the tests:** `tests/n64_session` 28 ×3; 7 mutations caught (M5 after a strengthened test); absent = today
     proven hunk by hunk.
2. **B60, the GameCube probe design** (`architecture/H2_P1_GAMECUBE_PROBE_DESIGN_2026-11-08.md`, no code):
   - **the emulator:** standalone Dolphin, not the unmaintained libretro core. The hub has no Dolphin and no Flatpak;
     Debian 13 offers 2503 with 10 of 44 dependencies missing. The rootless way is an upstream AppImage if published,
     else Debian's packages extracted into `runtime/`; `sudo apt install` is the user's own option;
   - **the parts table:**
     - the `nogui` / `-b` launch with `-u` on the hub;
     - the capture and the audio by PID;
     - evdev pads in `GCPadNew.ini`, with the GameCube layout;
     - the pause hotkey confirmed by the CPU thread's standing time, SIGSTOP as the fallback, SIGTERM to exit;
     - save states by hotkey, read back by mtime and the picture check;
     - four native ports;
   - **the files:** 27 `.rvz` on the drive, one small non-title `.bin`; the user dir on the hub; no BIOS needed;
   - **the run:** the metrics and the pass rows P0a-P7; the A run H2-P1.
3. **Checks:** every host suite on the baseline copy and the B59 copy, identical but for the new suite. The same six
   `tools/` tests fail in both. The seven touched suites are green in the tree. `redact_check` and `title_check` are
   clean.

**One line for the user (B59):** the N64 games will run on Mupen64Plus-Next, which has to be downloaded first (your
go); the N64's C-buttons are on the right stick (A on the A / Cross button, B on X / Square, Z on the left trigger).

**One line for the user (B60):** GameCube needs Dolphin, which is not on the hub. A can fetch it without changing the
system (your go), or you can install it with `sudo apt install dolphin-emu`.

## A — HOME-7+N64 (~60 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

Queue U's HOME-7 is carried forward (`SESSION_B_DONE_2026-11-08U.md`), with four changes:
- **the import flag** comes off at stage 1, not at the close;
- **N64 is added**: stage 1's bench drop-in, and the cells **C21-C23**;
- **C19 is shortened**;
- **the order:** C15, C16, C17, C18, C20, C19, then C21, C22, C23, then the close.

C15-C18 and C20 are **as queue U wrote them** (rows, hub reads, met, replies), with one reply changed (below).

**Stage 1 (A alone; no game, no movie; outside 04:30-05:30Z):**
1. **Preconditions:**
   - `/tmp` ≥ 1 GB free;
   - **seventeen** `PRIVYHUB_` lines: the sixteen adopted + `b56-import.conf`;
   - `cfe0211c…` CONFIRMED;
   - the eleven properties empty;
   - only the two units.
2. **The import flag off:** `b56-import.conf` removed. Nothing was placed (IMPORT-1), so no NEW tag is lost, and the
   list loses "(OpenBIOS)".
3. **The N64 core, only if the user has said yes** (ask before the sitting; **no go → skip steps 3-4, and C21-C23
   wait**):
   - fetch `mupen64plus_next_libretro.so` from the libretro buildbot (`stable/1.22.2/linux/x86_64/` if it lists
     per-core files, else `nightly/linux/x86_64/latest/mupen64plus_next_libretro.so.zip`) into
     `runtime/emulators/retroarch/cores-linux/`;
   - record the zip's and the `.so`'s sha256;
   - `python3 tools/n64_core_check.py --keys` → `"bundled"`, every key found (a missing key is recorded and is inert);
   - **nothing started.**
4. **The N64 folder and the bench flag:**
   - `N64_DIR=<the drive's N64 folder>` added to the gitignored paths file (never in a record);
   - the bench drop-in `b59-n64.conf` (`Environment=PRIVYHUB_N64=1`).
5. **The companion restart:**
   - queues T, U and V's host code goes live;
   - **seventeen** lines read back (the sixteen + `b59-n64.conf`), or sixteen with no go;
   - `--check` names the bench flag;
   - no keeper restart.
6. **The install, as queue U:**
   - preserve `cfe0211c…`;
   - copy `PrivyHub/app/build/queue_t_built/app-debug.apk` to `PrivyHub/app/build/home7_installed/`;
   - `adb install -r`; read back `9aa00ba2…`, paired;
   - **every property empty.**
7. **Pre-register** C15-C23, hashed.
8. **Reply:** queue U's Stage 1 reply.

**Stages 2-6 (C15, C16, C17, C18, C20): as queue U.**
- Stage 6's reply changes to: "YOU, now: Back and Stop the PS2 game. Open Games and tell me what the PlayStation entry
  is called. Scroll the PlayStation list and tell me how many entries you see for any game that has several discs (just
  the counts). Send 'Stage 7'."

**Stage 7 — C19, shortened (the list without the import flag):**
- **You should see / read:**
  - "PlayStation (<n>)", with no "(OpenBIOS)" (the flag removed at stage 1);
  - no " · NEW";
  - the multi-disc sets: **expected one entry per disc**, because the library holds no `.m3u`. The user's counts are
    recorded.
- **Met:** the name as above, and the counts recorded (a reading, not a pass).
- **Reply (no go: skip to the close):** "YOU, now: open Games → Nintendo 64. Tell me how many games it shows, then
  start the first one in the list (or one you pick, by its place in the list). When 'Hold any button to join' shows,
  hold A on controller 1 for about a second, then on controller 2. Play a minute, and tell me how the left stick, A, B,
  the right stick (the C-buttons) and the left trigger (Z) feel. Send 'Stage 8'."

**Stage 8 — C21, the first N64 title from the onn:**
- **You should see:**
  - "Nintendo 64 (13)";
  - the game starting;
  - P1 then P2 by the hold, with no "Setting up 4 players…" at any point;
  - both controllers driving their players (in a two-player title).
- **Hub reads:**
  - the game log's `N64 launch: core=mupen64plus_next ports=4` and `N64 core options: 12 keys (Mupen64Plus-Next)`;
  - the start payload's `n64_session` and `players_session.device_args` = `--device=1:1` … `4:1`;
  - `ports_set` players 4, `multitap` false, `multitap_available` false;
  - the `pad_slots` change rows `players_joined` 1, 2; **no `relaunch_ports` row**;
  - RetroArch's log: the core loaded, GLideN64 initialised (GL), no core error;
  - `native-stream-ready`.
- **Met:** the title played with two pads joined by the hold, and the user's line on the mapping. The mapping is a
  reading: what maps badly goes to B61.
- **Reply:** "YOU, now: in the game, press Back and choose SAVE (Game State 1). Play on for a minute so things change,
  then Back → LOAD (Game State 1). Tell me whether the game went back to where you saved. Send 'Stage 9'."

**Stage 9 — C22, a save and a load with the buttons (RetroArch's, as PS1):**
- **Hub reads:**
  - the save's answer ok and the slot's state file under `data/games/retroarch/states/` (**its size**: the recalled
    ~16-MB order);
  - the load's answer ok; RetroArch's `[State]` lines;
  - the resume.
- **Met:** the game back at the save point (the user's line).
- **Reply:** "YOU, now: play the N64 game for about 10 minutes with two controllers. Around halfway, press Home on the
  remote, count to 2 and go back to PrivyHub, then keep playing. At the end, tell me how smooth it felt and whether the
  game was where you left it after Home. Send 'Stage 10'."

**Stage 10 — C23, 10 min of play, the hitch rates:**
- **A captures, unattended,** a 120-s `showinfo` capture of the RetroArch window in the first minutes (`ffmpeg -f
  x11grab -framerate 60 -window_id <wid> -t 120 -i :0 -vf format=yuv420p,showinfo -f null -`; no encode; its CPU
  recorded) → `tools/n64_frames.py`: the internal rate, the distinct-fps median / min, the internal hitch rate.
- **Hub reads:**
  - `tools/diag_read.py` over the sitting: the N64 session's UX-R3 hitch seconds per 10 min, **beside C15 / C17's PS1
    sessions** of the same evening;
  - host CPU (`host_resource_samples`), Tctl;
  - **the Home hold:** `state_saved` slot 9 with `core mupen64plus_next_libretro.so`, then the release's load and
    `resumed` (the recovery stack, as PS1's).
- **Met:**
  - the hitch rate ≤ the PS1 session's + 2;
  - the hold resumed where it was (the user's line);
  - the internal rate and its hitch rate recorded (a reading).
- **Reply:** "YOU, now: that's all for the games — thank you. I'll tidy up on the hub. One question: should N64 stay on
  (yes / no)?"

**The close and the CONFIRMED rule (CL-B7 §6):**
- Every property empty.
- **`9aa00ba2…`:** CONFIRMED if C15, C16 and C17 are valid and met with every property empty; the pin moves
  (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test). Otherwise
  `cfe0211c…` goes back on.
- **What decides what:** C18 decides B55 and C20 decides B57 (inside the adopted `PRIVYHUB_PS2=1`). C19 is a reading.
- **The N64 reading** (what maps badly, the internal frame rate, the hitches, the state size):
  - → **B61**: the GameCube launch kind (B60's design) and any N64 fix;
  - → **G-A15**: `PRIVYHUB_N64=1` adopted **on the user's word only**. "Yes" → G-A15 at once (`b59-n64.conf`
    becomes the seventeenth adopted line, recorded as earlier adoptions); otherwise `b59-n64.conf` removed and
    sixteen lines read back.
- The record is `evidence/HOME_7_HOLD_TO_JOIN_N64_<date>.md` (no title, serial or path; titles as T1, T2…).

## A — H2-P1 (a later sitting; B60's §5)

Dolphin is fetched with the user's go. The run is unattended to the menu (P0a-P5); the streamed play waits for B61.

## Files

- **Records:**
  - `evidence/B59_N64_LAUNCH_2026-11-08.md` and its dir `b59_2026-11-08/`;
  - `architecture/H2_P1_GAMECUBE_PROBE_DESIGN_2026-11-08.md` (B60's record is the design itself).
- **Patch note:** `patches/B59_N64_LAUNCH.md`.
- **Docs, insertions only:**
  - `docs/KNOWN_ISSUES.md` (the queue V section);
  - `docs/ROADMAP.md`: §H0 IMPORT-2 deferred by the user, §H1 opened with B59, §H2 opened with the design.
- **Logs:** `logs/b59_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q14v_{base,b59,scratch}` (~27 MB); `~/.cache/b_q14v_tmp/` (~26 MB of the other
  host suites' temp).
- **To B next:**
  - HOME-7's findings (C20, the N64 mapping);
  - **B61**: the GameCube launch kind after H2-P1, plus any N64 fix;
  - the library's own multi-disc `.m3u` (the user's word first).
