# SESSION B — done, 2026-11-09 AA (QUEUE_2026-11-09AA: B73 the paused bar fits, B74 the disc change made safe; run 17:50-18:30Z)

- **Baseline:** `a5c51e37` (HOME-10 committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files
  tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no drop-in written;
  - no stream, no companion or keeper restart, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched;
  - **RetroArch and the core not started**. The core file was read as data only (`strings`), and so was the hub's one
    RetroArch disk index record (its `image_index`, and its path compared as a boolean, never printed);
  - nothing fetched, nothing written to the drive, nothing of A's touched, nothing deleted.

## What was built (two diffs applied to the tree in order, uncommitted)

**B73, the paused bar fits** (`evidence/B73_PAUSED_BAR_2026-11-09.md`, patch `patches/B73_PAUSED_BAR.md`). Client only,
default on.
- **Why END ran off:** B71's bar needed **1018 dp** on the onn's **960 dp** (1080p at density 2.0), so END spanned
  894-998 dp. The user's "~95 % off" puts the TV's visible edge at about **899 dp**.
- **Now, on a set:** **SAVE · LOAD · DISC · END**, 80 dp each with 6-dp gaps, the bar's end padding 80 dp. **END ends at
  880 dp.** The status text gets 232 dp, and still carries "Disc 2 of 4" under PAUSED, so the button reads "DISC" with
  the disc line beside it. There is no second row.
- **A one-disc bar is never touched.** `debug.privyhub.paused_bar_fit=0` = B71's bar.
- **The labels measured** at 26 px in a font wider than Roboto (upper bound): SAVE 70.4, LOAD 72.2, DISC 66.5, END
  62.6 dp, all ≤ 80. "CHANGE DISC" needs 132.
- Tests: 6 JVM. Mutations: 3 / 3 caught.

**B74, the disc change made safe** (`evidence/B74_DISC_CHANGE_SAFE_2026-11-09.md`, patch
`patches/B74_DISC_CHANGE_SAFE.md`). Host + client, default on.
- **Settled (1): the HOME-10 black screens were the game, not the sequence.**
  - The core is `Beetle PSX HW 0.9.44.1 82d8e05`; its state names (`DiscChanged`, `DiscStartupDelay`, `CD_TrayOpen`,
    `CD_SelectedDisc`) were read in the hub's own core file.
  - Its upstream source (recalled, not fetched) applies the open, the index and the close in the core's state at the
    call. At the close it latches the "lid was opened" bit and starts about 1 s of spin-up. **No frames are needed
    between**, and the in-between discs are never seen.
  - The same sequence carried on twice and went black three times, depending on where the game was: 1 → 4 (3 steps)
    carried on while 2 → 4 (2 steps) went black.
  - **The host sequence is unchanged; the running-core variant is not adopted.**
- **Settled (2): RetroArch restores the last disc** from its per-set disk index record (`saves/Beetle PSX HW/<set>.ldci`).
  **On the hub it already reads disc 1** (HOME-10's last change was 4 → 1), so C41 below first leaves the set on
  disc 4.
- **Host:**
  - a library launch of a set sets that record before RetroArch starts: **disc 1**, or the disc asked with `disc=j`.
    It is written only when it differs and is never deleted;
  - the game log gets `PS1 start disc: j of n (record …)`;
  - **`launched_disc`** (the launch's own first line) goes on `disc_swap` and `launch_ports`;
  - `discs` on a set's details;
  - B54's relaunch keeps RetroArch's restore;
  - **a one-disc game's launch call is today's exact kwargs**;
  - `PRIVYHUB_DISC_SWAP=0` = today.
- **Client:**
  - CHANGE DISC (DISC) first shows **"Change discs only when the game asks for the next one — changing at any other
    time can freeze the game"** with **"I understand"**, once per onn (remembered), then B71's chooser;
  - after a change: **"Disc j of n — if the game freezes, use LOAD or END"**;
  - **Extras → "Start on disc…"** in the launch dialog, for sets only;
  - `debug.privyhub.disc_safe=0` = B71's flow.
  - **Disclosed:** the queue's "in the Back menu" is read as the launch's menu. The paused bar has no room for a fifth
    button (B73), and a start from inside a game would throw the sitting away. The user may want it elsewhere.
- Tests: host 22 ×3 (a fake RetroArch boot reading the record, and B71's fake port); client 6.
- Mutations: host 8 of 9 caught (M5 is an equivalent mutant: the knob is checked twice), client 3 / 3.
- **Disclosed:** the first B74 passed `start_disc=1` on every launch and broke B54's three `players_session` tests,
  which pin the launch call. It was fixed to pass it for sets only, and every suite was re-run.

**Every host suite**, run on full exports of HEAD and of HEAD + B73 + B74, reads the same apart from the new suite. The
same six `tools/` suites fail in both: they read fixtures under `docs/` / `logs/`, which the copies do not hold. The
diffs apply in order and reverse back to HEAD; `git diff --check` is clean; the touched suites are green in the tree.

**The APK `85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`:**
- contents: B5 … + B54 + B67 + B70 + B71 + B72 (a) + **B73 + B74**; B27 / B29 out;
- built offline with `--no-configuration-cache`, twice → the same bytes;
- the baseline rebuilds `64d02f31…` byte for byte; the same signer;
- JVM 260 / 260 in the APK tree (271 / 271 in the working tree);
- pinned at `PrivyHub/app/build/queue_aa_built/app-debug.apk`, **NOT installed**;
- it carries B70's client half and B72 (a) again (both met at HOME-10 on `64d02f31…`).

**One line for the user:**
- the four buttons fit on the TV with a multi-disc game, END fully on screen;
- a game with several discs always starts on disc 1, unless you pick one under Extras → "Start on disc…";
- CHANGE DISC warns once that changing outside the game's own request can freeze it, and afterwards the TV says to use
  LOAD or END if it does;
- the black screens last time were the game reacting to a disc change it didn't ask for, as a real PlayStation would.

## A — HOME-11 (~20 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): **seventeen**. That is HOME-10's fifteen plus
`debug.privyhub.paused_bar_fit` and `debug.privyhub.disc_safe`.

**T-labels:** HOME-10's. T15 is the one-disc PS1 title; T17 is the 4-disc set.

### Stage 1 — unattended (A alone; no game, no movie; outside 04:30-05:30Z)

1. **Preconditions:**
   - HEAD with queue AA committed and the tree clean. If B73 / B74's files are uncommitted, stop with "YOU, now:
     commit queue AA first, then send the read line again";
   - `/tmp` ≥ 1 GB free;
   - **eighteen** `PRIVYHUB_` lines; `--check` ok;
   - `5f72af4b…` CONFIRMED, read back on the onn; the seventeen properties empty;
   - only the two units.
2. **The companion restart** (B74's host part live; no drop-in, nothing adopted): `systemctl --user restart
   privyhub-companion`. Then:
   - eighteen lines, `--check` ok, the journal clean, "PlayStation (72)";
   - **T17's details carry `discs` 4** (the control API's `details`, read on the hub);
   - **T17's record's `image_index`** is read as a number only (expected 0), never its path;
   - the keeper is not restarted.
3. **The install:**
   - preserve `5f72af4b…` in `home11_previous/`;
   - copy `PrivyHub/app/build/queue_aa_built/app-debug.apk` to `home11_installed/`;
   - `adb install -r`; read back **`85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`**, paired;
   - **every property empty (seventeen)**. adb is for the install and state reads only; no setprop.
4. **Pre-register** C40-C43, hashed: the rows below, the validity rules, the CONFIRMED rule, and what each cell
   decides.
5. **Reply:** "YOU, now: open Games → PlayStation and start the one-disc game you played last time (Launch on Companion
   → Start Fresh). When it plays, swipe and press the touchpad on purpose and tell me if any arrow or dot shows. Then
   press Back and tell me which buttons the bar shows. Then END. Send 'Stage 2'."

### C43 — C37's client half on this APK (T15, one disc)

- **You should see:** no arrow and no dots; the touchpad does nothing (no click, no Back); the Back bar reads **SAVE ·
  LOAD · END**, as before, with no DISC.
- **Hub:** `launch_ports` without `discs` / `start_disc`; no `PS1 start disc` line; the encoder still `-draw_mouse 0`.
- **Met:** the user's line. **A pointer seen** → to B (the onn's arrow or dots mean the client half).
- **Reply:** "YOU, now: open the PlayStation game with four discs → Launch on Companion → **Extras → Start on disc… →
  Disc 4**. When it plays, press Back. Tell me which buttons the bar shows, whether END is fully on the screen, and
  which disc it says. Then END. Send 'Stage 3'."

### C40 — the paused bar on a set (T17), and C41's first half (Start on disc 4)

- **You should see:**
  - the Extras list "Cheats", "Mods", **"Start on disc…"**, then "Disc 1" … "Disc 4";
  - the game starting from disc 4;
  - the bar **SAVE · LOAD · DISC · END, all four whole on the screen**, END not cut; under PAUSED, **"Disc 4 of 4"**.
- **Hub reads:**
  - `launch_ports`: `discs 4`, **`start_disc 4`**, **`launched_disc 4`**;
  - the game log: `PS1 start disc: 4 of 4 (record set)` and RetroArch's own `Setting disc in tray: 4/4`;
  - after END, the record's `image_index` **3** (RetroArch's own save at close; the number only).
- **Met (C40):** the user's line that all four buttons are on the screen and END is whole (a photo is welcome).
- **Reply:** "YOU, now: start the same four-disc game again the normal way (Launch on Companion → Start Fresh). When it
  plays, press Back and tell me which disc the bar says. Then RESUME, and once the intro movie has started press Back →
  DISC. Tell me what the screen says, press 'I understand', pick Disc 2, press RESUME, and tell me what the game does.
  Then press Back → DISC once more and tell me whether that message shows again (then Cancel). Then END. Send
  'Stage 4'."

### C41 — the set starts on disc 1 (T17, left on disc 4 by the stage above)

- **Hub reads:**
  - the game log: `PS1 start disc: 1 of 4 (record set)`, then RetroArch's own `Setting disc in tray: 1/4` as the launch
    line. **Without B74 it would read 4/4.**
  - `launch_ports`: `start_disc 1`, `launched_disc 1`; heartbeat rows `disc 1`.
- **You should see:** "Disc 1 of 4" on the bar.
- **Met:** the launch line 1/4 after a sitting that ended on disc 4; the bar's "Disc 1 of 4".

### C42 — the warning, then a change during the intro (T17, the same sitting)

- **You should see:**
  - the first DISC: "Change disc" with **"Change discs only when the game asks for the next one — changing at any other
    time can freeze the game"**, and the buttons "I understand" / "Cancel";
  - after "I understand": the chooser "Disc 1 (in the tray)", "Disc 2" …;
  - "Changing to disc 2…", then **"Disc 2 of 4 — if the game freezes, use LOAD or END"**;
  - after RESUME: the intro carrying on (as HOME-10's 1 → 2);
  - the second DISC: **straight to the chooser, no message**.
- **Hub reads:** the `disc_swap` row `ok true`, `from_disc 1`, `disc 2`, `steps 1`, **`launched_disc 1`**; `PS1 disc
  swap: 1 -> 2`; RetroArch's `Ejected` / `2/4` / `Closed`; the status still paused before RESUME.
- **Met:**
  - the message once with the exact text, then the chooser; the change `ok`; the line; no message the second time;
  - **the game's reaction is recorded, not scored.** Carrying on is expected, as at HOME-10. If it freezes, END
    (or LOAD) works, as the message says. B74 settled that a change outside the game's prompt is the game's
    business.
- **Reply (the close):** "YOU, now: that's all for the games, thank you. One question, no rush: PlayStation 2, N64 and
  GameCube are characterised and adopted, and every title stays listed. Do you want me to close Phase H ('close Phase
  H'), or keep it open for something first? I'll tidy up on the hub."

### The close

- **Every property empty** (seventeen); nothing running; the drive before = after.
- **The CONFIRMED rule for `85220f99…`:** C40, C41, C42 and C43 valid and met with every property empty →
  **`85220f99…` CONFIRMED**.
  - The pin moves in the three places: `tools/e1_suite.py` `EXPECT_APK`, and `tools/c3_l4_nft_night.py`
    `ADOPTED_APK_SHA256` and its test. The tests must be green and the patch note indexed.
  - Otherwise `5f72af4b…` is reinstalled from `home11_previous/`, read back and paired, and the user told why.
  - C41's host half (the launch line) is read from the hub whatever the APK.
- **The verdicts:** C40 → B73; C41 / C42 → B74; C43 → B70's client half.
- **The record:** `evidence/HOME_11_<date>.md` + dir: the cells, the user's lines verbatim, the rows, the record's
  `image_index` numbers, T-labels. No title, serial, game id or path.
- Then KNOWN_ISSUES insertions, the ROADMAP lines, CURRENT.md, `logs/home11_git_status.txt`, and nothing committed.

## A — the H5 checkpoint (sketched; only on the user's "close Phase H")

A writes `evidence/H5_CHECKPOINT_<date>.md`, reading each §H5 acceptance line from its own record (not from this
sketch):

| §H5 line | where it stands (to be read from) |
| --- | --- |
| content import pipeline validated | slice 1a run for real (IMPORT-1: 72 PS1, all duplicates, the drive untouched); slice 1b built (B58: plain folders, SNES / NES / Genesis, the journal); the `.m3u` sets applied (HOME-9). **NES / Genesis import deferred by the user** (IMPORT-2 not run) |
| no project-supplied ROM / ISO / BIOS | the user's drive; PS1 OpenBIOS (IMPORT-1); PS2 / GameCube / N64 as listed in place: A to cite each emulator's BIOS / firmware line from H1-H3's records |
| N64 / GameCube / PS2 characterised | H1 (G-A15, `PRIVYHUB_N64=1`), H2-P1 + HOME-9 (G-A16, `PRIVYHUB_GAMECUBE=1`), H3-P1 / P2 + HOME-6 (G-A14, `PRIVYHUB_PS2=1`): play, pause, save, load and recover from the onn |
| incremental resource costs vs Phase F | the probes' CPU / GPU margins (H2-P1, H3-P1, HOME-6's EE 42 % mean / 49 % max) beside Phase F's PS1 / SNES figures: A to tabulate |
| regression over the Phase G remote contract | A to state what was and was not re-run off-site with the extended systems |
| compatibility claims limited to tested evidence | H4's decision: every title offered, ENHANCED = PS2 + GameCube, **the caveat beside PS2: a heavy title's long play unread** |
| base Core hardware independent | no hardware change in Phase H |
| clean checkpoint / push | the user's commit of the checkpoint |

**What stays open, written in the checkpoint:**
- a heavy PS2 title's long play;
- the drive read-ahead (unbuilt; nothing in play has been put down to the drive, PS2-R1);
- NES / Genesis import deferred;
- **a real "insert disc N" prompt untested** (no save near one; B74's warning covers it);
- whatever HOME-11 leaves.

## Files

- **Records:** `evidence/B73_PAUSED_BAR_2026-11-09.md` and `evidence/B74_DISC_CHANGE_SAFE_2026-11-09.md`, each with its
  dir (the design + hash, the diff, tests, mutations, the proof, redact / title checks, the manifest). The APK's files
  are in `b74_2026-11-09/`.
- **Patch notes:** `patches/B73_PAUSED_BAR.md`, `…/B74_DISC_CHANGE_SAFE.md`.
- **Docs, insertions only:**
  - `docs/KNOWN_ISSUES.md`: the queue AA line and section;
  - `docs/ROADMAP.md`: §H0 B73 / B74, and §H4 the user's "Keep all games" recorded as the decision (every title on the
    drive offered; ENHANCED = PS2 + GameCube; the caveat beside PS2).
- **Logs:** `logs/b73_git_status.txt`, `logs/b74_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):**
  - `/tmp/b_q19aa_work`, `_base`, `_after_b73`, `_after_b74` (companion/, tools/, tests/, PrivyHub/ only), and
    `/tmp/b_q19aa_apk` / `_apko` (PrivyHub/ only), with their build outputs;
  - `~/.cache/b_q19aa_tmp/`: the test runs' outputs, the three APK builds, the first `b74.diff`, and the older host
    suites' own temp dirs. None of B73 / B74's suites leave a temp dir.
  - Disclosed: the host suites wrote a `logs/` dir into `_base` and `_after_b74` while running (`_after_b74` twice,
    once per run). All three were **moved** to `~/.cache/b_q19aa_tmp/hostrun_logs_from_*` (not deleted), so the copies
    hold only the four folders. The repo's own `logs/` is unchanged.
  - `~/.cache/b_q19aa_tmp/` also holds ~1,100 small temp dirs that the older host suites make and do not remove. They
    are left as they are, as in queue Z's.
