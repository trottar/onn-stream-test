# SESSION B — done, 2026-11-08 S (QUEUE_2026-11-08S: B52, B53; run 16:48-17:40Z; baseline 65186c66, the tree clean; HOME-5 and PS2-R1 committed. Only the companion + `privyhub-diag` active, checked first. Nothing committed or adopted; no stream, no companion or keeper restart, no adb; PCSX2 not started; nothing written to the drive; the bench flag `b49-ps2.conf` left as the user set it. **Deleted, with the user's go:** B's own old `/tmp/b_q*` work copies. **Not deleted (refused by the auto-mode classifier):** 6.9 GiB of B's test leftovers in `/tmp` — for the user)

## What was built (applied to the tree as `evidence/b53_2026-11-08/queue_s_combined.diff`, uncommitted)

1. **B52, the PS2 load** (`evidence/B52_PS2_LOAD_2026-11-08.md`):
   - **two causes found, both removed:**
     - MTVU on (PCSX2's own warning: "saved states may not be stable") → `vuThread = false` per launch;
     - HOME-5's loads went into a VM whose game had never booted (no `ELF Loading:` line; the start handoff paused PCSX2
       at 2 s) → a LOAD is held until the game's ELF is up, running PCSX2 to it when needed;
   - **"confirmed" now means the game runs from the state:** after the load, PrivyHub resumes PCSX2 and samples its
     window, and needs the picture moving (3 distinct frames, not the pre-load one, not black), PINE running, and no
     `TLB Miss`; then it pauses again. Otherwise the answer is PS1's error shape: "The game did not resume from the
     save", the game paused;
   - the game log: `PS2 load: slot N pine 0x0a ok; picture <ok|static|fault> <s>s`;
   - **HOME-5's save is unusable** (made with MTVU on). It is kept on the hub; the user makes a new one;
   - **MTVU off costs CPU:** expected an EE-thread peak toward ~85-100 % of a core in a heavy title; A measures it.
2. **B53, PCSX2's log per launch** (`evidence/B53_PCSX2_LOG_PER_LAUNCH_2026-11-08.md`):
   - the log is `-logfile data/games/ps2/logs/<UTC launch>-pcsx2.log` (2.8.2's own option), kept 30 days;
   - the keeper copies it;
   - `diag_read` counts per PS2 session: read errors, bindings, cards, TLB misses, saves / loads, the ELF line;
   - **plus test hygiene:** the PS2 tests now remove their own temp dirs.
3. **Checks:** `tests/ps2_session` 79 ×3; 11 mutations caught across both items; every host suite as the baseline;
   absent = today PROVEN for both.

**`/tmp` (for the user):**
- The hub's 7.5-GB RAM `/tmp` filled with **B's own test leftovers**: ~6.9 GiB in 3,905 directories, from B49-B52's
  `tests/ps2_session` runs (the list: `evidence/b52_2026-11-08/tmp_test_leftovers.txt`).
- B removed its old work copies with your go. The classifier refused removing these, so they are still there:
  **40 MB free.**
- **Free them** (delete the listed dirs, or reboot the hub, which empties `/tmp`) **before HOME-6**: the companion and
  PCSX2 need some `/tmp`.

## A — HOME-6 (ONE short sitting at the TV, ~15 min; the user with the onn and the pads paired to the onn; nothing on the hub; every reply "YOU, now:"; stages on the user's "Stage N")

**Stage 1 (A alone, unattended; no game, no movie; outside 04:30-05:30Z):**
1. **`/tmp`:** at least 1 GB free (if not, stop and tell the user: B's test leftovers above).
2. **Checks:** fifteen adopted lines plus the bench flag (sixteen `PRIVYHUB_` lines in the environ); `e3_state.py
   --check` ok; `cfe0211c…` CONFIRMED; the eleven `debug.privyhub.*` properties empty.
3. **The restarts:**
   - `systemctl --user restart privyhub-companion` (B52 / B53 live), sixteen lines read back;
   - **`systemctl --user restart privyhub-diag`** (B50's PS2 label and B53's copy live).
4. **The state file:** HOME-5's slot-1 `.p2s` is kept on the hub and unusable (MTVU on). The user's save at Stage 2
   replaces it (PCSX2 keeps it as `.p2s.backup`).
5. **Pre-register** the rows, hashed.
6. **Reply:** "YOU, now: open Games → PlayStation 2, start a PS2 game, play about a minute, then Back → Game State →
   Save → Slot 1, and send 'Stage 2'."

**Stage 2 — C12'' (SAVE, Stop, relaunch, LOAD):**
- **You should see:**
  1. `Saved Slot 1 - <date> - <size>` (as HOME-5);
  2. then Back, **Stop**, start the same game again, Back → Game State → **Load → Slot 1**: `Loading state slot 1...`,
     then `Loaded Slot 1 - …` (a few seconds: PrivyHub lets the game boot, then checks the picture);
  3. then **Resume → the game continues from where you saved** (the gate).
- **Hub reads:**
  - the game log `PS2 save: slot 1 pine 0x09 ok; file complete <s>s`, `PS2 pcsx2-log: <name>`, and **`PS2 load: slot 1
    pine 0x0a ok; picture ok <s>s`**;
  - the per-launch PCSX2 log present, with `ELF Loading:` before the load, `Loaded state from slot 1.`, and **0 `TLB
    Miss` after it**;
  - after the Resume, the encoder's frame sizes varying (`native_frame_sizes.jsonl`);
  - **the CPU with MTVU off:** `pidstat -t -p <PCSX2 pid> 1` over a minute of play, the EE thread beside H3-P2's (mean
    28-31 %, max 62 %);
  - the drive unchanged.
- **Reply:** "YOU, now: play a little, then Back → Game State → Load → Slot 1 → Resume once more, and send 'Stage 3'."

**Stage 3 — C14 (the in-game load, the common case):**
- **You should see:** `Loaded Slot 1 - …`, then after Resume the game back at the save.
- **Hub reads:** a second `picture ok`, 0 `TLB Miss` after it.
- **Reply:** "YOU, now: Back and Stop the game, and send 'Stage 4' — that's all."

**Stage 4 — the close (A alone):**
- **If C12'' and C14 are met — G-A14:** `PRIVYHUB_PS2=1` becomes the **sixteenth adopted line** in G-A13's applied form.
  - `tools/e1_suite.py`: `PS2 = "PRIVYHUB_PS2=1"` in `ADOPTED`, `drop_in_ps2` required in the preflight's `ok`;
    `e3_state.py` / `e1_remote.py` / `test_e1_remote.py` wording; the patch `patches/G-A14_PS2_ADOPTION.md`; the tests
    green.
  - Write `privyhub-companion.service.d/ps2.conf` (`[Service]` / `Environment=PRIVYHUB_PS2=1`), remove `b49-ps2.conf`,
    `daemon-reload`, restart; **sixteen** adopted lines read back; `--check` ok on sixteen.
- **Else:** the bench flag stays as it is. Name the failed row (the load's picture, a `TLB Miss`, the user's line).
- **Every teardown:** the count read back; the eleven properties empty.
- **The keeper:** its first copy since the restart read back (`sessions.jsonl`'s PS2 rows labelled `system: ps2`,
  `raw/ps2logs__*` present).
- **The record:** `evidence/HOME_6_PS2_LOAD_<date>.md`, with no title, serial or path.

**Then the user's three questions:**
1. PS2 hold / stall through states (the save took 0.5 s)?
2. A 1-player game: chooser or skip?
3. A multitap pick: relaunch at once or at the next start?

## Files

- **Records:** `evidence/B52_PS2_LOAD_2026-11-08.md`, `evidence/B53_PCSX2_LOG_PER_LAUNCH_2026-11-08.md`; dirs
  `b52_2026-11-08/`, `b53_2026-11-08/`.
- **Patch files:** `patches/B52_PS2_LOAD.md`, `patches/B53_PCSX2_LOG_PER_LAUNCH.md`.
- **Logs:** `logs/b52_` / `b53_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md` §H3.
- **Left:**
  - `/tmp/b_q11s_base`, `b_q11s_b52`, `b_q11s_b53`, `b_q11s_scratch/` (with the half-written `mut52`), `b_q09q_scratch/`
    (PCSX2's extracted binary), `b_q07o_scratch/` / `b_q08p_scratch/` (B's scripts);
  - `~/.cache/b_q11s_tmp/` (this queue's test temp on the main disk, with `mut53`).
