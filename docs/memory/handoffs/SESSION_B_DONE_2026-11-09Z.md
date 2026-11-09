# SESSION B — done, 2026-11-09 Z (QUEUE_2026-11-09Z: B70 the two pointers, B71 "Change disc", B72 the small readings; run 07:17-08:05Z)

- **Baseline:** `94c05e4a` (HOME-9+GC committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files
  tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no drop-in written;
  - no stream, no companion or keeper restart, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched;
  - **RetroArch and Dolphin not started**; their binaries were read only as archives (`7z`, `strings`);
  - nothing fetched, nothing written to the drive, nothing of A's touched.

## What was built (three diffs applied to the tree in order, uncommitted)

**B70, the two pointers** (`evidence/B70_POINTERS_2026-11-09.md`, patch `patches/B70_POINTERS.md`). Default on.
- **Host:** the capture gets **`x11grab -draw_mouse 0`**, so the hub's arrow is no longer in the picture.
  `PRIVYHUB_CAPTURE_POINTER=1` gives today's argv byte for byte.
- **Client:** in the stream activity the pads' touchpad and any mouse are swallowed: motion, scroll, clicks, and
  pointer-source keys (so a touchpad click can never act as Back). The onn's pointer gets the null icon and is
  **captured** at focus; the capture is what hides the touchpad's own touch-spot style. The remote's D-pad / OK and
  the pads' buttons and sticks are untouched. `debug.privyhub.pointer_hide=0` = today.
- **The DS4 / DS5 touchpad press** is the touchpad's own pointer click, not a pad button. It is swallowed with the
  rest and listed.
- Tests: host 4 ×3; client 9. Mutations: 2 / 2 host and 4 / 4 client caught.
- Disclosed: two existing suites that pin today's argv now read it under `=1`.

**B71, "Change disc"** (`evidence/B71_CHANGE_DISC_2026-11-09.md`, patch `patches/B71_CHANGE_DISC.md`). Default on.
- **Settled from RetroArch 1.22.2's own binary:**
  - the port has only `DISK_EJECT_TOGGLE` / `DISK_NEXT` / `DISK_PREV`, and no set-index command;
  - the disc index comes from RetroArch's own `[Disc] Setting disc in tray: k/n` lines (the label is never kept);
  - the launch's own line gives the starting disc.
- **Host `disc-swap`:**
  - on a multi-disc PS1 `.m3u` session only, and only while paused;
  - the sequence: eject, then NEXT / PREV step by step, each confirmed by its line, then close, 0.4 s apart. The pause
    is never touched;
  - a failure closes the tray again and answers the PS1 error;
  - the reply is PS1-shaped; the game log gets `PS1 disc swap: i -> j`; the `disc_swap` row is written;
  - `discs` / `disc` are on the status / launch response, `launch_ports` and every heartbeat row;
  - after a LOAD the disc reads unknown;
  - `PRIVYHUB_DISC_SWAP=0` = today.
- **Client:** **CHANGE DISC** in the paused bar (SAVE · LOAD · CHANGE DISC · END), shown only when `discs > 1`; a
  chooser "Disc 1 (in the tray)" … "Disc n"; then "Disc 2 of 4". `debug.privyhub.disc_change=0` = today.
- **A one-disc session is today's byte for byte.**
- Tests: host 21 ×3 on a fake RetroArch port; client 5. Mutations: 5 / 5 and 2 / 2 caught.

**B72, the small readings** (`evidence/B72_SMALL_READINGS_2026-11-09.md`, patch `patches/B72_SMALL_READINGS.md`).
- **(a)** The N64 card at the top, with the "Stabilizing" text pushed under it. Its own `shown_top` key, so it shows
  once more on the new APK. `n64_card_top=0` = B67's.
- **(b)** `fps (min)` clamped at 0, with the reset / hold-resume seconds excluded. On the HOME-9 evening, −1730 /
  −87.7 / −1659 now read 57.6 / 58.1 / 58.4.
- **(c)** B66's split on dolphin starts at the hold's `desync_pause`. C35's bar 4.5 / 0 now reads 0.0 / 1.
- **(d)** `gc_frames` classes a segment by its own median, with 20 a class and the VIs beside each segment. C34's
  224 → 39 hitches / 10 min. *Refined after a test finding (disclosed):* the runs are still cut on 30 / 60.
- **(e)** Dolphin's SDL is kept off the virtual pads (`SDL_JOYSTICK_BLACKLIST_DEVICES` /
  `SDL_GAMECONTROLLER_IGNORE_DEVICES` = `0x1209/0x5048`). `PRIVYHUB_GC_SDL_PADS=1` = today.
- **(f)** A stall during a picture check waits for the verdict and does not re-save slot 9.
- **(g)** `state_reply` rows after SAVE / LOAD, with fixed keys and no path or title. `PRIVYHUB_STATE_REPLY_ROWS=0` =
  none.
- Tests: host 25 ×3; client 5. Mutations: 7 / 7 and 3 / 3 caught.

**Every host suite**, run on full exports of HEAD and of HEAD + B70-B72, reads the same apart from the three new suites.
The same two `tools/` tests fail in both. The touched suites are green in the tree. The diffs apply in order and
reverse back to HEAD; `git diff --check` is clean.

**The APK `64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`:**
- contents: B5 … + B54 + B67 + **B70 + B71 + B72 (a)**; B27 / B29 out;
- built offline with `--no-configuration-cache`, twice → the same bytes;
- the baseline rebuilds `5f72af4b…` byte for byte; the same signer;
- JVM 248 / 248 in the APK tree (259 / 259 in the working tree);
- pinned at `PrivyHub/app/build/queue_z_built/app-debug.apk`, **NOT installed**;
- B72 (a) is in it too: C39 reads that card (disclosed).

**One line for the user:**
- no arrow and no touchpad pointer in a game; the touchpad does nothing;
- two- and four-disc PlayStation games get CHANGE DISC in the Back menu;
- the N64 button card sits above the "Stabilizing" text;
- GameCube sees only its four pads;
- the hub's readings stop showing negative frame rates.

## A — HOME-10 (~25 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): **fifteen**. That is HOME-9's twelve plus
`debug.privyhub.pointer_hide`, `debug.privyhub.disc_change` and `debug.privyhub.n64_card_top`.

### Stage 1 — unattended (A alone; no game, no movie; outside 04:30-05:30Z)

1. **Preconditions:**
   - HEAD with queue Z committed and the tree clean. If B70-B72's files are uncommitted, stop with "YOU, now: commit
     queue Z first, then send the read line again";
   - `/tmp` ≥ 1 GB free;
   - **eighteen** `PRIVYHUB_` lines; `--check` ok;
   - `5f72af4b…` CONFIRMED, read back on the onn; the fifteen properties empty;
   - only the two units.
2. **The companion restart** (queue Z's host items live; no drop-in, nothing adopted): `systemctl --user restart
   privyhub-companion`. Then: eighteen lines, `--check` ok, the journal clean, "PlayStation (72)", "GameCube (27)".
   The keeper is not restarted.
3. **The install:**
   - preserve `5f72af4b…` in `home10_previous/`;
   - copy `PrivyHub/app/build/queue_z_built/app-debug.apk` to `home10_installed/`;
   - `adb install -r`; read back **`64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`**, paired;
   - **every property empty (fifteen)**. adb is for the install and state reads only; no setprop.
4. **Pre-register** C37-C39, hashed: the rows below, the validity rules, the CONFIRMED rule, and what each cell
   decides.
5. **Reply:** "YOU, now: open Games → Nintendo 64 and start any game. Before you press anything, tell me where the
   button card is: above the 'Stabilizing game…' text, or over it (a photo is welcome). Then press any button, join,
   play a few seconds and swipe and press the touchpad on purpose. Tell me if any arrow or dot shows. Send 'Stage 2'."

### C39 — the N64 card (first, at the first N64 start on the new APK)

- **You should see:** the card "A = ✕, B = □, C-buttons = right stick …" at the top of the screen, and the
  "Stabilizing game…" text with its resolution / FPS line **under it, not through it**. It goes at the first press.
- **Hub:** `launch_ports` (system n64, `layout face_c`).
- **Valid:** the first N64 start after the install, every property empty.
- **Met:** the user's line (or photo): the card is not over the details line. (The card shows once on this APK, by its
  own `shown_top` key.)

### C37 — no pointer in a game (N64 now; then PS1 and GameCube)

- **A, before each game's stream:** put the hub's X pointer over the game window on purpose: `xdotool mousemove` to the
  middle of the screen, read back by `xdotool getmouselocation` inside the window. This is what made HOME-9's "Linux
  one" visible.
- **Hub reads:**
  - the encoder's command line (`pgrep -a ffmpeg`) carries **`-draw_mouse 0`**;
  - nothing else in it moves (the same as HOME-9's, apart from the pair).
- **You should see:** no arrow and no touch dots, before or after the touchpad is swiped and pressed. The touchpad press
  does nothing: no click, no Back, no menu. The remote and the pads work as before.
- **Valid:** every property empty; the hub's pointer read inside the window.
- **Met:** the user's line, per game, for N64, PS1 and GameCube. **A pointer seen** → to B, with which one (the hub's
  arrow means the host half; the onn's arrow or dots mean the client half).
- **Reply after N64:** "YOU, now: Back and Stop. Start a one-disc PlayStation game and do the same: swipe and press the
  touchpad, tell me if anything shows. Then press Back and tell me which buttons the bar shows. Send 'Stage 3'."

### Stage 3 — PS1 (C37's PS1 line; C38's one-disc check)

- **You should see:** no pointer; the Back bar reads **SAVE · LOAD · END**, with **no CHANGE DISC**.
- **Hub:** the status poll has no `discs` key; `launch_ports` has no `discs`.
- **Reply:** "YOU, now: Stop. Start any GameCube game, join with two controllers, swipe and press the touchpad, and tell
  me if anything shows. Then Back and Stop. Send 'Stage 4'."

### Stage 4 — GameCube (C37's GameCube line; B72 (e))

- **Hub reads:**
  - Dolphin's per-launch log: `Added device: evdev/0/PrivyHub Virtual Gamepad P1` … `P4`, and **no `SDL/` device**;
  - `GC pads: P1=evdev/0 …` with no MISMATCH; the launch's environment carries the two SDL hints (B72 (e)).
- **Met:** the user's no-pointer line; only the evdev four in Dolphin's log.
- **Reply:** "YOU, now: Start the PlayStation game with four discs (or any of the two-disc ones). When it plays, press
  Back. Tell me what the bar shows and which disc it says. Then choose CHANGE DISC → Disc 2, press RESUME, and tell me
  what the game does. Then Back → CHANGE DISC → Disc 1 → RESUME, and tell me whether it carries on. If you have a save
  near the spot where the game asks for disc 2, load that in the game first and do the change when it asks. Send
  'Stage 5'."

### C38 — "Change disc" on a multi-disc PS1 title

- **Hub reads:**
  - the launch's own `[Disc] Setting disc in tray: i/n` in the game log (the starting disc; RetroArch may restore the
    last one used);
  - `launch_ports` `discs n` / `disc i`; heartbeat rows with `discs` / `disc`;
  - per change: the `disc_swap` row (`ok true`, `from_disc`, `disc`, `steps`, `ms`), the game log `PS1 disc swap: i ->
    j`, RetroArch's `Ejected …`, `Setting disc in tray: j/n` and `Closed …` lines, and the `GET_STATUS` after it still
    PAUSED;
  - `state_reply` rows for any SAVE / LOAD of the sitting (B72 (g)).
- **You should see:**
  - the bar SAVE · LOAD · **CHANGE DISC** · END, and "Disc 1 of 4" (or "of 2") under PAUSED;
  - the chooser "Disc 1 (in the tray)", "Disc 2" …;
  - "Changing to disc 2…", then "Disc 2 of 4";
  - after RESUME the game reads disc 2. That might be its own "wrong disc" message, it carrying on, or, at a real
    disc prompt, the prompt satisfied;
  - after the change back, the game carries on.
  - RetroArch's own short notice ("Setting disc in tray …") may show for a moment after the resume; it is listed, not a
    fault.
- **Valid:** every property empty; the swaps made from the paused bar.
- **Met:**
  - the entry is present here and absent on Stage 3's one-disc game;
  - both changes have `ok true`, and the game's state is unchanged (still paused) until RESUME;
  - the user's line that the game took the disc. At a real prompt: the prompt satisfied.
  - A `could not change the disc` reply → to B, with the rows.
- **Reply (the close):** "YOU, now: that's all for the games, thank you. One question for later, no rush: for the
  'selected PS2 / GameCube' tier, do you want every title offered (my suggestion), only the ones you've played and
  kept, or something else? I'll tidy up on the hub."

### The close

- **Every property empty** (fifteen); nothing running; the drive before = after.
- **The CONFIRMED rule for `64d02f31…`:** C37 (the client's half), C38 and C39 valid and met with every property empty
  → **`64d02f31…` CONFIRMED**.
  - The pin moves in the three places: `tools/e1_suite.py` `EXPECT_APK`, and `tools/c3_l4_nft_night.py`
    `ADOPTED_APK_SHA256` and its test. The tests must be green and the patch note indexed.
  - Otherwise `5f72af4b…` is reinstalled from `home10_previous/`, read back and paired, and the user told why.
  - C37's host half (`-draw_mouse 0`) is read from the hub whatever the APK.
- **The verdicts:** C37 → B70, C38 → B71, C39 → B72 (a); Stage 4's Dolphin log → B72 (e).
- **H4:** record the user's answer on the tiers (`docs/ROADMAP.md` §H4 holds the four readings and B's suggestion).
  What comes next is theirs to name.
- **The record:** `evidence/HOME_10_<date>.md` + dir: the cells, the user's lines verbatim, the rows, T-labels. No
  title, serial, game id or path.
- Then KNOWN_ISSUES insertions, the ROADMAP lines, CURRENT.md, `logs/home10_git_status.txt`, and nothing committed.

## Files

- **Records:** `evidence/B70_POINTERS_2026-11-09.md`, `evidence/B71_CHANGE_DISC_2026-11-09.md` and
  `evidence/B72_SMALL_READINGS_2026-11-09.md`, each with its dir (the design + hash, the diff, tests, mutations, the
  proof, redact / title checks, the manifest).
- **Patch notes:** `patches/B70_POINTERS.md`, `…/B71_CHANGE_DISC.md`, `…/B72_SMALL_READINGS.md`.
- **Docs, insertions only:**
  - `docs/KNOWN_ISSUES.md`: the queue Z line and section;
  - `docs/ROADMAP.md`: §H0 B71, §H2 B70 / B72, §H4 the tiers note for the user's decision.
- **Logs:** `logs/b70_git_status.txt`, `logs/b71_git_status.txt`, `logs/b72_git_status.txt`;
  `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):**
  - `/tmp/b_q18z_work`, `_base`, `_after_b70` / `_b71` / `_b72` (companion/, tools/, tests/, PrivyHub/ only), and
    `/tmp/b_q18z_apk` / `_apko` (PrivyHub/ only), with their build outputs;
  - `~/.cache/b_q18z_tmp/`: the older suites' own temp dirs from the host runs. None are from B70-B72's suites, which
    remove their own.
  - Disclosed: one of the host suites writes `logs/impairment.jsonl` into the copy it runs in. Those two `logs/` dirs
    in the scratch copies were removed, so the copies hold only the four folders. The repo's own
    `logs/impairment.jsonl` is unchanged.
  - My scratch strings of the two binaries (`/dev/shm`) were removed at the end.
