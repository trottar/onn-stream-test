# SESSION B — done, 2026-11-08 W (QUEUE_2026-11-08W: B61, B62, B63, B64; run 22:50-23:25Z)

- **Baseline:** `6fcd2f23` (HOME-7 committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files
  tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed;
  - no stream, no companion or keeper restart, no adb, no sudo, no nft; no APK built (two client items listed);
  - nothing fetched, nothing written to the drive, nothing deleted.
- **RetroArch with the N64 core was started by B headless** (the hub's display, no stream, no pad), for B61's
  reproduction only:
  - six short runs (each ≤ 35 s) on a **synthetic fixture ROM**, with temp folders and no title;
  - the hub's real config was only read (a copy of its N64 `.opt`);
  - the first two crashed at startup because the shell had no `DISPLAY`; one of those ran outside the tool sandbox
    (disclosed in B61).
  - **T6's own reproduction needs the real title, so it is A's step** (HOME-8 stage 1).

## What was built (four diffs applied to the tree in order, uncommitted)

1. **B61, the N64 Home-hold freeze** (`evidence/B61_N64_HOLD_FREEZE_2026-11-08.md`; inside `PRIVYHUB_N64=1`):
   - **the cause:** RetroArch froze within ~2 frames of the hold's slot-9 save sent into a **running** N64 core. It
     then spun at 100 % inside the core and never answered again (no save logged). Every N64 save that worked was
     into a paused core;
   - **the fixture:** a running save does not hang a synthetic ROM, with or without a window capture, so the capture
     is not implicated;
   - **the fix:**
     - no state save is sent into a running N64 core (the hold's scratch skipped; its return a plain resume; the
       slot-0 capture pauses first);
     - a silent command port gets one `command_port_silent` row and a 10-s retry instead of the 46-row storm;
   - **the tests:** `tests/b61_n64_hold` 14 ×3; 5 mutations caught.
2. **B62, the N64 layout** (`evidence/B62_N64_MAPPING_2026-11-08.md`):
   - **the cause:** "half the buttons" = ○ and △, which do nothing in Mupen64Plus-Next's own layout (its input
     descriptors). The title's jump is a C-button, and presses did reach the host. Not a race, not a per-title quirk;
   - **the fix:**
     - a core remap written and verified at every N64 launch: ○ = C-right, △ = C-up, the right stick still all four
       (RetroArch logs `[Remap] Core-specific remap found`, read on the fixture);
     - a per-title `n64_layout` in the metadata;
     - the layout on the game's details line;
     - `n64_core_check.py --remap`;
   - **the tests:** `tests/b62_n64_mapping` 10 ×3; 4 mutations caught.
3. **B63, the PS1 multitap rule** (`evidence/B63_PS1_MULTITAP_CAPABILITY_2026-11-08.md`; **default-on**;
   `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` = today):
   - **the rule:** the multitap from a join or a pick only for a title the metadata calls multitap-capable (the five
     `port1` titles, or `ps1_multitap_capable: true`). Any other PS1 title stays at 2 ports;
   - **the echo:** `ports_set.multitap_available` false, so the onn shows its note and does not relaunch;
   - **the relaunch** is refused "This game supports 2 players";
   - **T1:** its host state (the `.opt` with the multitap on) is corrected at its next launch. The onn's stored 3 is
     capped by the host at every launch;
   - **the tests:** `tests/b63_ps1_multitap` 11 ×3; 4 mutations caught.
4. **B64, the stale pad rows** (`evidence/B64_STALE_PAD_ROWS_2026-11-08.md`): the first heartbeat after a start (the
   previous game's count, no claim) is tagged `stale: true`. `tests/b64_stale_pad_rows` 5 ×3; 3 mutations caught (one
   after an added test).
5. **Checks:**
   - every host suite in each snapshot reads as the baseline plus the new suites; the same six `tools/` tests fail in
     every copy;
   - 16 touched suites green in the tree;
   - the four diffs reverse-apply (64 → 61) to the baseline.

**For the next APK (listed, not built):**
- the N64 layout shown once at the first N64 launch;
- "This game supports 2 players" in place of "No multitap on this system — 2 players" when `ports_set.capable` is
  false;
- the onn's stored joined count capped at the title's capability;
- the pad-slot order at a new start (B64).

**One line for the user:**
- **N64 freeze:** the freeze came from PrivyHub's safety save when you press Home, so N64 now just pauses and resumes.
- **N64 buttons:** Triangle and Circle are now C-up and C-right, so you can jump with Triangle.
- **PS1 adapter:** a PS1 game only gets the 4-player adapter if it is known to support it, so player 2 keeps working
  on your two-player game.

## A — HOME-8 (~30 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (the eleven, read back empty at the start and the close), as HOME-7.

**Stage 1 (A alone; no game, no movie; outside 04:30-05:30Z):**
1. **Preconditions:**
   - `/tmp` ≥ 1 GB free;
   - **seventeen** `PRIVYHUB_` lines; `e3_state.py --check` ok;
   - **`9aa00ba2…` CONFIRMED, read back on the onn**;
   - the eleven properties empty; only the two units.
2. **The companion restart** (queue W's host code goes live: B61-B64). Seventeen lines read back, `--check` ok. No
   keeper restart.
3. **The N64 remap verified before any launch:** `python3 tools/n64_core_check.py --keys --remap` → `bundled`, 12 / 12
   keys, the remap `absent (the first N64 launch writes it)` or `matches`, `shadowed 0`, writable.
4. **T6's reproduction, unattended (B61's open part; the drive read-only; no stream, no pad; ≤ 60 s):**
   - `DISPLAY=:0 XAUTHORITY=<the companion's> python3 docs/memory/evidence/b61_2026-11-08/repro/b61_repro.py <repo>
     <a temp dir on the main disk> --content <T6's file on the drive>`. The script uses temp config / state / save
     folders and reads the title in place;
   - wait at T6's attract / menu ~20 s;
   - record each running save's ack and the longest silence, then the paused save's;
   - if it hangs: the `threads` row and the CPU, then SIGTERM / SIGKILL (the script does it).
   - **Recorded:** "running save hangs T6: yes / no" (no title).
5. **Pre-register** C24-C28, hashed.
6. **Reply:** "YOU, now: open Games → Nintendo 64 and open the game you played last time (the one where you couldn't
   jump). Before starting it, tell me what the 'Controller:' line in its details says. Then start it, hold ✕ on
   controller 1 and controller 2 to join, and try jumping with △ (Triangle). Send 'Stage 2' with whether it worked."

**Stage 2 — C24, T6's buttons:**
- **Hub reads:**
  - the game log `N64 remap: face_c (players 1-4, 8 binds) verified`;
  - RetroArch's `[Remap] Core-specific remap found`;
  - `n64_core_check.py --remap` → `matches`;
  - the payload's `n64_session.layout` `face_c`;
  - `updates_by_player` moving for P1 / P2.
- **You should see:** the details line "A = ⨉, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2"
  (glyphs drawn, or boxes: record which); △ / ○ jump for both players.
- **Met:** the user's line, jump on △ (and ○) for each player. **Not met → B:** the remap's two analog values (or the
  descriptor reading).
- **Reply:** "YOU, now: keep playing a few seconds, then press Home on the remote, count to 2 and go back to PrivyHub.
  Tell me whether the game came back and whether you can play again. Send 'Stage 3'."

**Stage 3 — C25, the N64 Home hold:**
- **Hub reads:**
  - at the loss: `state_save_skipped` `reason "n64: no save into a running core"`, `core mupen64plus_next_libretro.so`
    (no `state_save_failed`);
  - `desync_pause` with no `pause_error`;
  - at the return: `rewind_skipped` `"n64: plain resume (no state)"`, then `resumed`;
  - **no `command_port_silent`**, no `stall_resume_failed`;
  - RetroArch's CPU as before the press.
- **Met:** the game back and playable (the user's line), the rows above. **Not met → B:** a `command_port_silent`
  (with its process reading), or a freeze; record stage 1's reproduction beside it.
- **Reply:** "YOU, now: Back and Stop. Open Games → PlayStation and start the two-player game whose player 2 stopped
  working last time. Join with controllers 1 and 2, then hold ✕ on a third controller. Tell me what the TV says, and
  whether player 2 works. Send 'Stage 4'."

**Stage 4 — C26, T1 with three pads:**
- **Hub reads:**
  - the start's `ports_set`: players 2, `multitap` false, `multitap_available` false, `capable` false, `capped_from` 4
    (the onn's stored count 3);
  - the game log `PS1 multitap: off` and `PS1 ports capped: 4 -> 2 (not multitap-capable)`;
  - T1's per-content `.opt` multitap disabled after the launch (B63's migration, recorded);
  - `--device` 1-2;
  - **no `relaunch_ports` row** at the third hold.
- **You should see:** the note "No multitap on this system — 2 players" (today's words; "This game supports 2 players"
  is a client item), no "Setting up 4 players…", and player 2 working.
- **Met:** player 2 works and no relaunch.
- **Reply:** "YOU, now: Back and Stop. Start one of the four-player PlayStation games (one that worked with 4 players
  before). Join with controllers 1 and 2, then hold ✕ on a third controller. Tell me whether the game restarts with 3
  players and whether players 1, 2 and 3 all work. Send 'Stage 5'."

**Stage 5 — C27, a multitap-capable PS1 title:**
- **Hub reads:**
  - its metadata `ps1_multitap: port1`; the start's `capable` true;
  - either B54's `relaunch_ports` (`ok`, `state loaded`) or, with a stored count ≥ 3, the multitap from the start;
  - `PS1 multitap: port1`; `--device` 1-4; P3 joined.
- **Met:** players 1-3 working (the user's line).
- **Reply:** "YOU, now: Back and Stop. Start an N64 game you like and play about 10 minutes with two controllers
  (pressing Home once in the middle is fine). Then tell me how it felt. Send 'Stage 6'."

**Stage 6 — C28, 10 min of N64:**
- **A reads, with no capture running** (no x11grab this time):
  - `tools/diag_read.py` over the sitting: the N64 session's UX-R3 hitch seconds per 10 min, beside a PS1 session of
    the same evening (C26's or C27's);
  - host CPU, Tctl;
  - any Home hold as in C25.
- **Met:** the hitch rate ≤ the PS1 session's + 2, no freeze, and the user's line.
- **Reply:** "YOU, now: that's all — thank you. I'll tidy up on the hub."

**The close:** every property empty; the two units; nothing running; the drive as it was. The record is
`evidence/HOME_8_N64_FIXES_<date>.md` (no title, serial or path; titles as T-labels).

**What each cell decides (nothing to adopt: all inside adopted flags or the default host path):**
- C24 → B62 met, or the remap values to B;
- C25 (+ stage 1's reproduction) → B61 met; the reproduction says whether the trigger is per title;
- C26 → B63 met on an incapable title (and the migration recorded);
- C27 → B63 keeps the capable titles' relaunch;
- C28 → H1's N64 hitch reading without the capture;
- B64 is read on every start (the seq-1 row `stale: true`).
- A not-met goes to B; the knob `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` is the user's way back for B63 if they want it.

## Files

- **Records:** `evidence/B61_N64_HOLD_FREEZE_2026-11-08.md`, `B62_N64_MAPPING_2026-11-08.md`,
  `B63_PS1_MULTITAP_CAPABILITY_2026-11-08.md`, `B64_STALE_PAD_ROWS_2026-11-08.md`, with the dirs
  `b61_2026-11-08/` … `b64_2026-11-08/`.
- **Patch notes:** `patches/B61_N64_HOLD_FREEZE.md`, `B62_N64_MAPPING.md`, `B63_PS1_MULTITAP_CAPABILITY.md`,
  `B64_STALE_PAD_ROWS.md`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the queue W section), `docs/ROADMAP.md` (§H1 the fixes, §D4 the
  multitap rule).
- **Logs:** `logs/b61_git_status.txt` … `logs/b64_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q15w_*` (~81 MB); `~/.cache/b_q15w_tmp/` (~76 MB).
- **To B next:**
  - HOME-8's findings: T6's reproduction (the core's part), and the remap's values if C24 is not met;
  - the APK items above;
  - the multi-disc `.m3u` (the user's word);
  - the GameCube launch kind after H2-P1.
