# SESSION B — done, 2026-11-08 P (QUEUE_2026-11-08P: B49; run 01:24-01:46Z; baseline f3f912c5, the tree clean. Only the companion + `privyhub-diag` active, checked first. Nothing committed, nothing adopted, nothing installed, nothing fetched, nothing deleted; no stream, no companion restart, no adb, no sudo, no nft; PCSX2 not started (no title, no BIOS read, no display); nothing written to the drive; `privyhub-diag` and `~/privyhub_diag/` untouched)

**What this queue rests on:**
- H3-P1: PCSX2 v2.8.2 at full speed with wide margins; the capture and the audio carry over by PID.
- P6 was not run, because the design put pads on the hub. **The user always plays on the TV through the onn, with the
  pads paired to the onn over Bluetooth.** That is the only attended form.

**B49 SETTLED + BUILT — the PS2 launch kind, behind `PRIVYHUB_PS2=1`** (host only; record
`evidence/B49_PS2_LAUNCH_KIND_2026-11-08.md`; applied to the tree, uncommitted):
- **The onn's list:** the onn renders the host's system nodes and has no hard-coded system set. So "PlayStation 2"
  appears with no APK change, its titles read-only from the drive's games folder: `.chd` / `.iso` / `.cue`, one per
  title, `.chd` preferred.
- **The launch:** PCSX2 launched like any title, with its ini written per launch:
  - Vulkan 1x on the AMD adapter, the overlay off, no update check, Discord off;
  - memory cards, save states and a BIOS copy (its NVRAM) on the hub;
  - PINE on;
  - the four virtual pads in the DualShock 2 layout through SDL, and the multitap from `players_chosen` at launch.
- **Pause / resume / exit:** pause and resume by PCSX2's hotkey when PINE confirms it, else SIGSTOP / SIGCONT; exit by
  SIGTERM, with SIGKILL after 5 s. The game log (no title) has timestamped `PS2 launch / pause / resume / exit` lines.
- **Save states off for PS2:** the hold's rewind, the slot-9 save, the stall resume's load and the link give-up save,
  each with a `ps2_mode` row.
- **The P2 metric:** `tools/ps2_p2_frames.py`, with black / static seconds out of the minimum and at most one beat
  repeat per second forgiven. A's bars: median ≥ 59, corrected minimum ≥ 55.
- **Tests and checks:** `tests/ps2_session` 35 ×3; 4 mutations caught; every host suite as the baseline; absent =
  today PROVEN.
- **Recalled, read back at H3-P2:**
  - PINE's status protocol (if it is wrong, every pause is a SIGSTOP, still correct);
  - PCSX2's SDL binding names and multitap pad numbering;
  - the pads' SDL order.

## A — H3-P2, the streamed PS2 session (the user at the TV with the onn; the pads paired to the onn as always; nothing on the hub)

**The APK for this run:** `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f` (CONFIRMED, on the onn),
**every property empty**.
- Two pads take slots by stable slots, with no chooser. The chooser is in `cfe0211c…`, which is **not installed**;
  HOME-4 comes later.
- So no `players_chosen` is sent, and a PS2 title starts with 2 ports and no multitap.

**Pre-register (hashed, before the drop-in):**
- the rows below;
- the order: the PS1 game first, then T1;
- the P2 capture's minute;
- the bars.

### Setup (A alone; no game and no movie running, read first; outside 04:30-05:30Z)

1. **Checks:**
   - fifteen lines; `e3_state.py --check` ok; `8ba4d996…` CONFIRMED; the eleven properties empty;
   - `runtime/h3_p1_paths.txt` present (gitignored, not read into any record);
   - `runtime/emulators/pcsx2/` holds the one AppImage;
   - the drive's two folders listed (names counted, not copied) with their mtimes.
2. **The bench drop-in:**
   ```
   printf '[Service]\nEnvironment=PRIVYHUB_PS2=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b49-ps2.conf
   systemctl --user daemon-reload && systemctl --user restart privyhub-companion
   ```
   Read back: sixteen `PRIVYHUB_` lines in the companion's environ, one of them `PRIVYHUB_PS2=1`; the journal clean.
3. **The hub-side samplers** (unattended, beside the stream for the whole run, as H3-P1): `mpstat -P ALL 1`,
   `pidstat -t -p <pid> 1` once PCSX2 runs, `iostat -x 1` on the drive, `sensors` and `gpu_busy_percent` at 1 Hz.

### The run (what the user does, and what the user should see)

1. **PS1 first, 10 min** (the M7 reference). On the onn, open Games → PlayStation → a two-player PS1 game you like,
   and play 10 minutes with your two pads as usual.
   - **You should see:** the game as always.
   - **A:** UX-R3's hitch seconds for those 10 minutes (the session's heartbeat / frame logs).
2. **T1 from the onn's list.** Back to the Games menu. **You should see a new "PlayStation 2" entry** with the titles
   on the drive. Open it, then T1 (A tells you which title is T1 by its place in the list, not by name in any record).
   - **You should see:** "Launching…", then the game's first picture on the TV within about 1½ minutes (the PS2 boot
     logo, then the title), and both pads working (pad 1 = player 1, pad 2 = player 2).
   - **A:** the launch-to-first-frame time: from the onn's `launch` request to the stream's first decoded frame (the
     client report's first-frame time), and the game log's `PS2 launch: pcsx2 players=2 multitap=false
     adapter=named`.
3. **Pause and Resume once** (after a few minutes of play):
   - press **Back** on the remote: the picture stops and the onn shows the paused screen;
   - pick the title again, then **Resume**: the game continues where it stopped.
   - **You should see:** each within about 3 seconds, with nothing lost.
   - **A:**
     - the game log's `PS2 pause: hotkey|sigstop` and `PS2 resume: hotkey|sigcont` lines, timed against the recovery
       log's `session_ended` (the Back) and `session_started` (the Resume's release);
     - the `ps2_session` row at each start, and `ps2_mode` on the heartbeat rows.
4. **10 minutes of play with two pads** (in total, the pause included). **One line from you on how it felt** (smooth /
   stutters / unplayable, and anything about the controls).
   - **A:**
     - M7: UX-R3's hitch seconds for T1's 10 minutes, beside the PS1 session's;
     - M2-M6 from the samplers;
     - **P2:** one 60-s capture at minute 6-7 of T1, taken on the hub with no user step:
       `ffmpeg -f x11grab -framerate 60000/1001 -window_id <the PID's window> -t 60 -i $DISPLAY -vf format=yuv420p,showinfo -f null - 2> <scratch>/showinfo.txt`,
       then `python3 tools/ps2_p2_frames.py <scratch>/showinfo.txt`. That minute is marked in the hitch count (the
       capture's own load, disclosed). PCSX2's own counter is not read: its overlay is off for play.
5. **Exit:** Back, then **Stop** on the title.
   - **You should see:** the Games menu, nothing stuck.
   - **A:** the game log's `PS2 exit: sigterm <s>s`; no `AppRun` or FUSE helper left; the session's `session_ended`.
6. **T2, 10 min, only if you want the heavy title:** the same as steps 2-5 for T2, with one line on feel.

### The rows (P7, pre-registered)

| row | pass when |
| --- | --- |
| P7a the list | "PlayStation 2" on the onn with the drive's titles (count = the folder's distinct titles); the drive's folders unchanged (listing + mtimes) |
| P7b launch | the onn's launch → the first frame on the TV **≤ 90 s**; the game log `PS2 launch` line; `ps2_session` row |
| P7c pads | both pads drive players 1 and 2 (the user's line; PCSX2's log names the four `PrivyHub Virtual Gamepad` devices opened — their order recorded) |
| P7d pause / resume | Back → `PS2 pause` **≤ 3 s** after `session_ended`; Resume → `PS2 resume` **≤ 3 s** before or at `session_started`; the game continues (the user's line); the method recorded (`hotkey` or `sigstop`) |
| P7e hitches | T1's hitch seconds per 10 min **≤ the PS1 session's + 2** |
| P7f P2 | `ps2_p2_frames.py`: median **≥ 59**, corrected minimum **≥ 55** |
| P7g M2-M6 | as H3-P1's P3 / P4 / P5 bars, now in play with the stream (no core ≥ 90 % for 30 s, GPU median ≤ 80 %, Tctl ≤ 90 °C, frame-time p95 ≤ 20 ms, no read stall > 500 ms after 60 s) |
| P7h exit | `PS2 exit: sigterm …` (not `sigkill`); nothing of PCSX2 left; the next PS1 launch works |
| P7i feel | the user's line (recorded verbatim; not a pass / fail by A) |

**Invalid if:** a pad was not paired to the onn (re-pair on the onn, never on the hub), or the stream dropped to a
restart during the 10 minutes (rerun the 10 minutes).

### Close (A alone, after the user's "done")

- Remove `b49-ps2.conf`, `daemon-reload`, restart (no game, no movie). **Fifteen lines** read back; `--check` ok;
  `flags_absent`.
- The eleven properties empty; `8ba4d996…` still CONFIRMED; nothing written to the drive (listing + mtimes before =
  after).
- **The record:** `evidence/H3_P2_PS2_STREAMED_<date>.md`, with titles `T1` / `T2` only, and `redact_check`.
- **Then the user's questions:** turn `PRIVYHUB_PS2=1` into an adopted line (the sixteenth), or keep it bench-only;
  PS2 save states (the hold / stall / recovery through PINE) as a later item, yes or no.

**No stage asks the user for anything on the hub.** Every hub step (the drop-in, the samplers, the P2 capture, the
reads) is A's, unattended.

## Files

- **Record:** `evidence/B49_PS2_LAUNCH_KIND_2026-11-08.md`; dir `b49_2026-11-08/`.
- **Patch file:** `patches/B49_PS2_LAUNCH_KIND.md` (no `PATCH_INDEX.md` row, as queue N / O).
- **Logs:** `logs/b49_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (a section), `docs/ROADMAP.md` (§H3: H3-P1's run and B49).
- **Left in /tmp:** `b_q08p_base`, `b_q08p_b49`, `b_q08p_scratch/` (the edit scripts, the mutation copy, the
  regression outputs).
