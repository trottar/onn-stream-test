# SESSION B — done, 2026-11-08 R (QUEUE_2026-11-08R: B51; run 08:40-08:55Z; baseline c497a196, the tree clean. Only the companion + `privyhub-diag` active, checked first. Nothing committed, adopted, installed, fetched or deleted; no stream, no companion restart, no adb, no sudo, no nft; PCSX2 not started (its binary disassembled from the AppImage in /tmp, nothing run); no BIOS read; nothing written to the drive; `privyhub-diag` and `~/privyhub_diag/` untouched. Seen and left as it is: `b49-ps2.conf` in the drop-ins, the bench flag on at the user's decision)

**The requirement (HOME-4+ C12):** the user saves with PrivyHub's SAVE button on every system. For PS2 it answered
B49's refusal ("There is no save"; "Why are you changing it from ps1 and others"), so PS2 stays bench-only until SAVE
and LOAD work for it exactly as for PS1.

**B51 SETTLED + BUILT** (record `evidence/B51_PS2_SAVESTATES_PINE_2026-11-08.md`; applied to the tree, uncommitted;
live at the next restart):
- **PINE on 2.8.2, from its binary:**
  - save state `0x09`, load state `0x0A`, one slot byte;
  - the reply OK `0x00` / fail `0xFF`;
  - the OK means *queued*, so the save is checked by its file (`<serial> (<CRC>).0N.p2s` in
    `data/games/ps2/sstates/`) and the load by PCSX2's log (`Loaded state from slot N.`).
- **SAVE / LOAD for PS2 now answer exactly as PS1:**
  - the same JSON and the same PS1 slot index, so the onn shows the same `Saved Slot N - <date> - <size>`, the same
    Game State list, the same "Saved States";
  - PS1's messages, and PS1's rule that a load needs the game paused.
- **A failure** answers in PS1's error shape. **Over this API that is HTTP 503 for PS1 too** (every POST failure), so
  "never 503" and "PS1's shape" cannot both hold; B kept PS1's shape with real failure texts, never "not available".
  For the user to know.
- **Still off for PS2:** the hold's rewind / state load, the slot-9 save and the stall resume's load (not measurable
  without running PCSX2), the rewind (none in PCSX2), the link give-up save. So **C13 does not run.**
- **Checks:** `tests/ps2_session` 65 ×3 (a real PINE socket double), 6 mutations caught, every host suite as the
  baseline, absent = today PROVEN.
- **Docs only:** C10's off-check description and C9's row corrected (errata sections in B47 / B46's records, and
  `KNOWN_ISSUES`).

## A — HOME-5 (ONE short sitting at the TV, ~20 min; the user with the onn and two pads paired to the onn as always; nothing on the hub; every reply to the user starts "YOU, now:"; the stages move only on the user's "Stage N")

**Stage 1 (A alone, unattended; outside 04:30-05:30Z; no game and no movie running, read first):**
1. **Checks:** fifteen adopted lines (`e1_suite.ADOPTED`); `e3_state.py --check` ok; `cfe0211c…` CONFIRMED; the eleven
   `debug.privyhub.*` properties empty.
2. **The bench drop-in** `~/.config/systemd/user/privyhub-companion.service.d/b49-ps2.conf` (`[Service]` /
   `Environment=PRIVYHUB_PS2=1`): read back. It is present now, at the user's decision; write it if absent.
3. **The restart:** `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`. Read back
   **sixteen** `PRIVYHUB_` lines in the companion's environ (the fifteen + `PRIVYHUB_PS2=1`); the journal clean. B51's
   host code is now live.
4. **Before:** list `data/games/ps2/sstates/` (count and mtimes; names not copied, since they carry the serial); the
   drive's two folders (listing + mtimes).
5. **Pre-register** the rows below, hashed.
6. **The reply:** "YOU, now: open Games → PlayStation 2, start a PS2 game you like, play about a minute, then send
   'Stage 2'."

**Stage 2 — C12', SAVE** (PrivyHub's button, as on PS1):
- **Do:** Back to the game's screen, Game State → **Save → Slot 1** (the same button and slot as PS1).
- **You should see:** `Saving state slot 1...`, then **`Saved Slot 1 - <date and time> - <size>`**, exactly as PS1.
  No "Game State" error dialog.
- **Hub reads:**
  - the game log `PS2 save: slot 1 pine 0x09 ok; file complete <s>s` (**the measured write time**: record it; over
    5 s, note for B);
  - a new `….01.p2s` in `data/games/ps2/sstates/`, its mtime the save's time (the name not copied);
  - PCSX2's own log `Saved state to slot 1.` (read in place);
  - the PS1 index holds the title's slot 1 (`data/games/retroarch/privyhub_state_slots.json`, read in place; the key not
    copied);
  - the `ps2_session` row `savestates: "pine"`;
  - the drive unchanged.
- **Reply:** "YOU, now: Back, Stop the game, start the same PS2 game again from the list, and send 'Stage 3' once it
  is on screen."

**Stage 3 — C12', LOAD after a relaunch:**
- **Do:** Back (the game paused), Game State → **Load → Slot 1**, then Resume.
- **You should see:** Slot 1 listed with the same date and size; `Loading state slot 1...`, then `Loaded Slot 1 - …`;
  after Resume, **the game continues from where you saved** (the gate: the user's line).
- **Hub reads:**
  - the game log `PS2 load: slot 1 pine 0x0a ok; confirmed` (or `visual` with `verification: visual_required`, the
    user's line deciding);
  - PCSX2's log `Loaded state from slot 1.`;
  - the response `confirmed` / `verification`;
  - the drive unchanged.
- **Reply:** "YOU, now: Back and Stop the game, and send 'Stage 4'; that is all for tonight."

**C13 (the hold's return through PINE): not run.** B51 kept the hold / stall state uses off (disclosed).

**Stage 4 — the close (A alone):**
- **G-A14 if C12' is met** (the save shown, `Saved Slot 1 …`, and the load continuing from it in the user's line):
  `PRIVYHUB_PS2=1` becomes the **sixteenth adopted line** in G-A13's applied form.
  - `tools/e1_suite.py` defines `PS2 = "PRIVYHUB_PS2=1"` (comment `G-A14 (adopted <date>, the user)`) in `ADOPTED`; the
    preflight reads `drop_in_ps2` (`f"Environment={PS2}"` in `systemctl --user cat privyhub-companion`) and requires it
    in `ok`.
  - `e3_state.py` / `e1_remote.py` / `test_e1_remote.py`: wording only; `ADOPTED_E3` as it is.
  - The patch `patches/G-A14_PS2_ADOPTION.md` with its diff (`git apply --check`, then applied); `e1_suite --self-test`,
    `test_e1_remote`, `test_c3_l4_nft_night` green.
  - The drop-in `privyhub-companion.service.d/ps2.conf` = `[Service]` / `Environment=PRIVYHUB_PS2=1`, then remove
    `b49-ps2.conf`.
  - `daemon-reload`, restart (no game, no movie); **sixteen** lines read back; `--check` ok on sixteen.
- **Else:** remove `b49-ps2.conf`; `daemon-reload`, restart; **fifteen** lines; `--check` ok. Tell the user which row
  failed (the save's answer, the file, or the load's continuation).
- **Every teardown:** the adopted count read back (sixteen after G-A14, else fifteen); the eleven properties empty;
  `flags_absent`.
- **The record:** `evidence/HOME_5_PS2_SAVE_<date>.md` (no title, serial or path), `redact_check`.

**The rows (pre-registered):**

| row | pass when |
| --- | --- |
| C12'a SAVE | HTTP 200; the onn `Saved Slot 1 - …`; the game log `PS2 save: slot 1 pine 0x09 ok; file complete <s>s` with s ≤ 10; a new / changed `.01.p2s` on the hub |
| C12'b the list | after Stop and relaunch, Slot 1 listed with the save's date and size |
| C12'c LOAD | HTTP 200; `Loaded Slot 1 - …`; `PS2 load: slot 1 pine 0x0a ok`; **the user: the game continues from the save** |
| C12'd the files | the state file under `data/games/ps2/sstates/` only; the drive's folders unchanged; `savestates: "pine"` on the `ps2_session` row |

**The user's open questions:** the chooser for `single` titles (keep or skip); a relaunch at the start when the pick
changes the multitap; and, after HOME-5, whether the hold / stall should use PINE states once the save's write time is
known.

## Files

- **Record:** `evidence/B51_PS2_SAVESTATES_PINE_2026-11-08.md`; dir `b51_2026-11-08/`.
- **Patch file:** `patches/B51_PS2_SAVESTATES_PINE.md`.
- **Logs:** `logs/b51_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md` (§H3), errata sections in
  `evidence/B46_PLAYER_CHOOSER_2026-11-07.md` and `evidence/B47_VOD_RETRY_DEFAULT_ON_2026-11-07.md`.
- **Left in /tmp:** `b_q10r_base`, `b_q10r_b51`, `b_q10r_scratch/` (the mutation copy, the regression outputs).
  PCSX2's extracted binary stays in `b_q09q_scratch/`.
