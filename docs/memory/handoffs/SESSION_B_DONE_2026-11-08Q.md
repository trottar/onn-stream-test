# SESSION B — done, 2026-11-08 Q (QUEUE_2026-11-08Q: B50; run 03:30-03:53Z; baseline 85c51c91, the tree clean. Only the companion + `privyhub-diag` active, checked first. Nothing committed, adopted, installed, fetched or deleted; no stream, no companion restart, no adb, no sudo, no nft; PCSX2 not started (its binary read from the AppImage's squashfs in /tmp, nothing run); no BIOS read; nothing written to the drive; `privyhub-diag` and `~/privyhub_diag/` untouched)

**H3-P2 showed PS2 on the TV works** (the user: "ran surprisingly well", "It felt really good to play"). **B50 fixed its
defects, all inside `PRIVYHUB_PS2=1`** (record `evidence/B50_PS2_FIXES_2026-11-08.md`; applied to the tree,
uncommitted):
1. **The audio wait (A's in-run change): kept.** PCSX2's own log orders its start as the window → the audio stream
   (1.45 s) → the VM's init → PINE (1.54 s) → the pads. The sink-input is the earliest proof of the audio stream.
   - Narrowed: it runs on the session's injectable clock (so `tests/ps2_session` takes 1.6 s, not 91 s), polls every
     0.1 s, and the first pause now waits ≤ 1 s for PINE's first answer.
   - PINE and the wait are separated in tests, and B49's defect is reproduced in one.
2. **Memory cards:** the hub's cards were PCSX2's unformatted image (all `0xFF`). The companion now formats a slot's
   card when it is absent or all `0xFF`, never one holding data. The ECC is checked against PCSX2's own tables, and a
   checker reads the card back.
3. **Tears:** an immediate present (`VsyncEnable = false`) went to a fullscreen window that `xfwm4` unredirects. Now
   `VsyncEnable = true` with mailbox allowed: tear-free. Only if the driver gives FIFO does it cost up to ~17 ms.
4. **Bindings:** PCSX2 2.8.2 uses the SDL3 names, so Cross / Circle / Square / Triangle = `FaceSouth` / `FaceEast` /
   `FaceWest` / `FaceNorth`. All 24 DS2 bindings are in the accepted set, on Pad1-Pad4.
5. **The keeper:** PS2 sessions now read `system: ps2`, core `pcsx2` (the `-ps2.log` and the `ps2_session` row). The
   PS1 reference excludes them, and `diag_check` adds one line when the newest session is PS2.
6. **The P2 capture window:** `tools/ps2_p2_window.py plan|check`, at least 60 s after the last release and never
   within 90 s of a pause, with minute 3 as the fallback.
7. **Not built, open:** the drive read-ahead; PS2 save states through PINE (the user's question).

**Checks:** `tests/ps2_session` 55 ×3; 6 mutations caught; every host suite as the baseline; absent = today PROVEN. No
client change; no APK.

## A — HOME-4+ (ONE sitting at the TV, ~45 min; the user with the onn and two pads paired to the onn over Bluetooth as always; nothing asked on the hub; every reply to the user starts "YOU, now:"; the stages move only on the user's message "Stage N")

**The properties** (eleven, `debug.privyhub.*`, each read back empty at the start and the close): `restart_guard`,
`stall_signal`, `link_notice`, `link_report`, `loss_guard`, `wifi_lock`, `opus_decode`, `surface_hold`, `pad_slots`,
`vod_retry`, `player_prompt`.

**Stage 1 (A alone, unattended; outside 04:30-05:30Z; no game and no movie running, read first):**
1. **Checks:** fifteen lines; `e3_state.py --check` ok; `8ba4d996…` CONFIRMED; the eleven properties empty;
   `runtime/h3_p1_paths.txt` and the one AppImage present; the drive's two folders listed (counts, names not copied)
   with their mtimes; the hub's `data/games/ps2/memcards/Mcd001.ps2` / `Mcd002.ps2` sha256 recorded (all `0xFF` now).
2. **Pre-register** the rows below, hashed.
3. **The APK:**
   - preserve `8ba4d996…` (`PrivyHub/app/build/home3_installed/`);
   - copy `PrivyHub/app/build/queue_o_built/app-debug.apk` to `PrivyHub/app/build/home4_installed/` and `adb install
     -r` it;
   - read back `cfe0211ca36071901a8be3ea9f77855109cd957c3950903669997d6a0b10a65f`, paired, every property empty;
   - the chooser and the movie retry are on by default in this APK.
4. **The bench drop-ins and the restart:**
   ```
   printf '[Service]\nEnvironment=PRIVYHUB_PS2=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b49-ps2.conf
   printf '[Service]\nEnvironment=PRIVYHUB_VOD_DROP_TEST=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b47-vod-drop.conf
   systemctl --user daemon-reload && systemctl --user restart privyhub-companion
   ```
   Read back: seventeen `PRIVYHUB_` lines in the companion's environ (the fifteen + `PRIVYHUB_PS2=1` +
   `PRIVYHUB_VOD_DROP_TEST=1`); the journal clean. Queue O's, B49's and B50's host code is now live.
5. **The question, if the user has not answered it yet:** "PS2 always on? (`PRIVYHUB_PS2=1` as an adopted line, so the
   PlayStation 2 entry stays after tonight)".
6. **The reply:** "YOU, now: pick up both pads, open Games → PlayStation and start a two-player PS1 game, then send
   'Stage 2'." (Add the question if open.)

**Stage 2 — C7, the chooser at a start and an unpause** (a two-player PS1 title, multitap off; queue O's strings):
- **You should see, at the start:** bottom-centre `Players:  1  /  [2]  /  multitap (3-4)`.
  1. Pad A presses X: `Player 1 — press any button` (the pick claims nothing).
  2. Pad B presses X: `P1` for 2 s, then `Player 2 — press any button`.
  3. Pad A presses X: `P2`, and the line goes.
  4. Back on the remote, then the title's Resume: the chooser again with `[2]`. Pick, then claim P1 and P2 again.
- **Pass:**
  - the game is never paused by the chooser;
  - a `"event": "pad_slots"` `change` row after each pick, with `players_chosen` 2 and both slots `claimed_by:
    prompt`, `label` `P1` / `P2`; the heartbeats carry `players_chosen` 2;
  - each exit's report: `players_chosen` 2, `pad_claims`, `ports_set` (`players` 2, `source` `metadata`).
- **Reply:** "YOU, now: stay in the game for C9 and send 'Stage 3'."

**Stage 3 — C9, the held-Start release** (the same title, both pads claimed):
- **Do:** pad B presses Select, then Start, and holds both 2 s.
  - **You should see** `P1 released`, then `Player 1 — press any button`.
  - Keep Start held 3 s more, let go, then press Start again: `P1`.
- **Pass:** no `change` row with slot 0 `prompt` while Start was held; one after the fresh press.
- **Reply:** "YOU, now: Back, Stop this game, start a four-player PS1 game, and send 'Stage 4'."

**Stage 4 — C8, multitap** (a PS1 title that supports four players):
- **Do:**
  1. At the chooser, right twice → `[multitap (3-4)]`, pick. The line reads `Player 1 — press any button` and
     `Multitap from the next start` (unless the title's metadata already has the multitap on).
  2. Stop the game, then launch it again. The chooser shows `[multitap (3-4)]`; pick; pad B → P1, pad A → P2. P3 / P4
     stay open.
- **Pass (hub reads: these lines only, never a path or title):**
  - the game log's `PS1 multitap: port1`;
  - the Beetle `.opt` key `beetle_psx_hw_enable_multitap_port1 = "enabled"`;
  - RetroArch's `--device=1:<d>` … `--device=4:<d>`;
  - `ports_set` `players` 4, `multitap` true, `source` `launch`.
- **Reply:** "YOU, now: Back, Stop, then open the new 'PlayStation 2' entry, start any two-player PS2 game you like,
  and send 'Stage 5'."

**Stage 5 — C11, a two-player PS2 title** (the user's pick from the list):
- **You should see:**
  - the game's first picture within ~a few seconds (H3-P2: 2.5-2.7 s);
  - the chooser `Players:  1  /  [2]  /  multitap (3-4)`;
  - after the pick, `Player 1 — press any button` → pad B → `P1`, pad A → `P2`.
  - Then get both players into the game (a two-player mode): **pad 1 drives player 1, pad 2 drives player 2.**
  - Watch for tearing.
- **Pass:**
  - **the user's line:** both pads drive their players; any tearing;
  - **the PS2 game log:** `PS2 launch: pcsx2 players=2 multitap=false adapter=named`, `PS2 memcards:
    Mcd001.ps2=formatted Mcd002.ps2=formatted` (the first launch after B50), `PS2 audio: sink-input <s>s`,
    `PS2 pause: hotkey`;
  - **PCSX2's own log** (`data/games/ps2/config/PCSX2/logs/emulog.txt`, read in place): **no `Invalid binding:` line**;
    four `Opened gamepad` lines for `PrivyHub Virtual Gamepad`; `McdSlot 0 [File]: Mcd001.ps2 [8 MB, Formatted]`;
  - **the hub's ini:** `[Pad] MultitapPort1 = false`, `[Pad2] Cross = SDL-1/FaceSouth`, `[EmuCore/GS] VsyncEnable =
    true`;
  - **the rows:** `ports_set` `players` 2, `multitap` false; a `pad_slots` `change` row with `players_chosen` 2; the
    `ps2_session` row; `ps2_mode` on the heartbeats.
- **Reply:** "YOU, now: in this game, save to the memory card (the game's own save), and tell me when it says it saved;
  then send 'Stage 6'."

**Stage 6 — C12, a PS2 save on the hub's card:**
- **Do:** the user saves (the game confirms). Then Back, **Stop**, launch the same title again, and load the save.
- **You should see:** the save in the game's load list, and the game continue from it.
- **Pass:**
  - `Mcd001.ps2`'s sha256 differs from the post-format value, and `ps2_memcard.check` still reads it `formatted`
    (`python3 -c "import sys; sys.path.insert(0,'companion'); import ps2_memcard as m; print(m.check(open('data/games/ps2/memcards/Mcd001.ps2','rb').read())['formatted'])"`);
  - the relaunch carries `players_chosen=2`: the PS2 log `players=2 multitap=false`, the launch's `players_session`;
  - the drive's folders unchanged (listing + mtimes);
  - the user's line.
- **Reply:** "YOU, now: Back and Stop the game, start a movie you like, let it play, and send 'Stage 7' once it has
  played for a minute (don't press anything during it)."

**Stage 7 — C10, the movie with no property** (`vod_retry` empty; queue O's C10):
- **(a) The drop:** A runs `echo "drop 45" >> runtime/vod_drop_test.trigger` (from the repo root).
  - **You should see** "reconnecting…" in the corner, then the movie continue at the same place, **with
    "reconnecting…" gone**.
  - **Pass:** `vod_drop_injected` `dropped: 1`; `vod_error` (`reset`) → `vod_retry` × n → `vod_resumed`; no "Playback
    error". **Invalid** if `dropped: 0`: run again with `drop 60`.
- **(b) The restart:** with the movie playing ≥ 1 min more, A runs `systemctl --user restart privyhub-companion`.
  - **You should see** the movie pause briefly and resume by itself.
  - **Pass:** a `vod_range.jsonl` row with `closed: "shutdown"`; `401` → `token_refetched: true` → `vod_resumed`.
- **Reply:** "YOU, now: stop the movie and say 'Stage 8' — that is the end; nothing else for you."

**Stage 8 — the close (A alone, after the movie is stopped):**
- Remove `b47-vod-drop.conf`.
- **If the user said yes to "PS2 always on" — G-A14:**
  - `PRIVYHUB_PS2=1` becomes the **sixteenth** line in the applied form (as G-A13):
    - `tools/e1_suite.py` defines `PS2 = "PRIVYHUB_PS2=1"` (comment `G-A14 (adopted <date>, the user)`) in `ADOPTED`;
    - the preflight reads `drop_in_ps2` (`f"Environment={PS2}" in systemctl --user cat`) and requires it in `ok`;
    - `e3_state.py` / `e1_remote.py` / `test_e1_remote.py`: wording; `ADOPTED_E3` as it is;
    - the patch `patches/G-A14_PS2_ADOPTION.md`, its diff checked and applied, the tests green.
  - The drop-in `~/.config/systemd/user/privyhub-companion.service.d/ps2.conf` = `[Service]` /
    `Environment=PRIVYHUB_PS2=1`, then remove `b49-ps2.conf`.
  - `daemon-reload`, restart; **sixteen** lines read back; `--check` ok on sixteen.
- **Else:** remove `b49-ps2.conf`; `daemon-reload`, restart; **fifteen** lines; `--check` ok.
- Every teardown reads back the adopted count (fifteen, or sixteen after G-A14); every property empty; `flags_absent`.

**The CONFIRMED rule (CL-B7 §6):** if every cell that ran is valid and today's behaviours hold wherever a property was
`0` / `off` (B42 / B46 / B47's intended defaults aside), **`cfe0211ca36071901a8be3ea9f77855109cd957c3950903669997d6a0b10a65f`
is CONFIRMED** and the pin moves (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`
and its test). Otherwise `8ba4d996…` goes back on. C11 / C12 are PS2 cells: they bear on B50, not on the APK rule.

**The record:** `evidence/HOME_4_PLUS_<date>.md`, with titles as class + tag (PS2 titles `T`-labels), `redact_check`.

**The user's questions after:** PS2 save states through PINE (yes / no); the chooser for `single` titles (keep or skip);
a relaunch at the start when the pick changes the multitap.

## Files
- **Record:** `evidence/B50_PS2_FIXES_2026-11-08.md`; dir `b50_2026-11-08/`.
- **Patch file:** `patches/B50_PS2_FIXES.md` (no `PATCH_INDEX.md` row, as queues N-P).
- **Logs:** `logs/b50_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (a section), `docs/ROADMAP.md` (§H3).
- **Left in /tmp:** `b_q09q_base`, `b_q09q_b50`, `b_q09q_scratch/` (the AppImage's squashfs and the extracted
  `pcsx2-qt` read for the names and the ECC tables, the mutation copy, the regression outputs).
