# SESSION B — done, 2026-11-11 AG (QUEUE_2026-11-11AG: B90 the cheat launch without walking the list + no game left running when the onn hangs up, B91 the mapping picture beside the rows; the APK; run 01:50-03:15Z)

- **Baseline:** `d1df1f86` (HOME-12T committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files
  tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no companion or keeper restart; no stream, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched; nothing fetched; nothing written to the drive; nothing of A's
    touched; nothing deleted (the `/tmp/b_q21ag_*` copies and `~/.cache/b_q21ag_tmp/` left);
  - **RetroArch was run by B, headless, for B90's measurement only** — B61's form: synthetic fixture ROMs (B61's N64
    loop, a SNES LoROM loop, a PS-X EXE loop), made-up cheat lists of 12 / 188 / 677 / 2,092 entries, temp folders under
    `~/.cache`, the companion's display, no stream, no pad; nothing left running (counted after each set: 0).

## What was found and built (two diffs applied to the tree, uncommitted)

| Item | Found | Built | Switch | Tests | Mutations |
| --- | --- | --- | --- | --- | --- |
| **B90** | **All three cores (Mupen64Plus-Next, snes9x, Beetle PSX HW) apply a loaded file's enabled cheats with no command** when `apply_cheats_after_load` is on — RetroArch logs `Applying cheat changes.`, the core's memory holds the values (off: neither). Today's walk ≈ 0.05 s per pulse: 677 entries / 2 picks = 1,807 pulses, 93 s; 2,092 / 4 = 10,045 pulses, 513 s. **Also: SNES cheats never load on the hub** (snes9x reads `Snes9x/`, the hub stages `bsnes/`) | only the session's cheats staged (renumbered, each enabled) + the apply-at-load line; verified from the apply line and ≤ 2k + 4 paced index pulses (no pause, no toggle); SNES under `Snes9x/`; **a launch whose client has hung up** (socket closed, ≥ 60 s, or the write fails) → the game stopped by the onn's own Stop path, one `launch_orphaned` row | `PRIVYHUB_CHEAT_STAGED=0` (5 / 5 byte-equal to HEAD through the real HTTP route) | 10, all through the companion's real HTTP server on loopback | 9 / 9 (after one test added) |
| **B91** | B89's labels were fitted to tiny boxes: **≈ 10.6 px** (a face button) **vs the rows' 34 px** at 1080p; one row in view under the picture | the picture **beside** the rows (left pane, outside the rows' scroll; the dialog 92 % of the screen), **every label at the rows' size (34 px = 17 sp)**, B89's drawing scaled to fill its side, labels placed without overlap (moved ones get a leader line); renders of the whole editor at 1920 × 1080 | `debug.privyhub.mapping_picture=0` (B86's gate) | 6 (+ B89's 7, B86's 7) | 7 / 7 |

- **Measured (staged, the hub's own code against the real RetroArch):** 36 / 36 runs verified on the three cores and
  four sizes, **≤ 1.13 s and ≤ 6 pulses each, 0.51 s on the 2,092-entry list with 4 picks** (target ≤ 15 s); 84 / 84
  core-memory reads hold the picks afterwards.
- **The number (B91):** the picture's label text 34 px beside the rows' 34 px (B89: ≈ 10.6 px).

**The APK `218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53`:**
- contents: B5 … + B74 + B80's client part + B84 + B86 + B89 + **B91** (B90 has no client part); B27 / B29 out;
- built offline (`--no-configuration-cache`) twice → the same bytes; the baseline rebuilds `3f21e2c6…` byte for byte;
  the same signer (`455bde4e…`); JVM 296 / 296 in the APK tree (307 / 307 in the working copy);
- pinned at `PrivyHub/app/build/queue_ag_built/app-debug.apk`, **NOT installed** (`85220f99…` stays on the onn).
- **Render files:** `docs/memory/evidence/b91_2026-11-11/render/default.png`, `swap_bottom_right.png`,
  `many_button_remap.png`.

**Disclosed:** the onn's density taken as the 1080p TV norm (2.0), not read on the device; the dialog's chrome and
row heights a model; the renders are java.awt's (DejaVu Sans), the device draws with its own font and widths; with
Android's font 1.3× larger *and* a deliberately wide width bound *and* all 24 controls labelled "START", 4 labels find
no place (left out, never overlapping — not a case at the default font); B87's suite now pins `PRIVYHUB_CHEAT_STAGED=0`
(one line) and four `tests/art_systems` cases that assert today's whole-file staging are pinned the same way; the
host-suite comparison also found B90's first service lines broke `tests/session_identity`'s handler replay (fixed: looked
up as B35's gate is); the hang-up check runs at the answer (a still-running launch is not aborted early).

**One line for the user:** the N64 cheat launch walked the whole cheat list one step at a time (about 100 seconds on
your game) — the hub now hands RetroArch only the cheats you picked, already switched on, and checks they took in
about a second; if the TV ever gives up waiting, the hub now stops the game instead of leaving it running; and the
controller picture now sits beside the list with its letters the same size as the list's — you can look at it now in
`docs/memory/evidence/b91_2026-11-11/render/`.

## A — HOME-12, the fourth sitting (~15 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): **twenty** (HOME-12T's; queue AG adds none).
**T-labels:** HOME-12T's T81 (N64), T82 (PS2, widescreen already saved), T85 (PS1); T86 (the user's own profile).

### The CONFIRMED rule, in two parts (pre-registered, hashed at stage 1)

- **(a) The APK** `218d9a82…` is **CONFIRMED on its own cells**: **C54**, **C55** and **C56** valid and met, with every
  property empty → the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py`
  `ADOPTED_APK_SHA256` and its test; green; the patch notes indexed). Any of the three not met → `85220f99…`
  reinstalled from `home12u_previous/`, read back, paired, the user told why.
- **(b) The hub's cell decides hub items only:** **C46** (the N64 cheat seen in-game within the onn's wait, the
  launch's seconds recorded) decides **B90 / B87**; met or not, it **does not roll the APK back**.

### Stage 1 — unattended

1. **Preconditions:** HEAD with **queue AG committed** and the tree clean — if B90 / B91's files are uncommitted, stop
   with "YOU, now: commit queue AG first, then send the read line again"; `/tmp` ≥ 1 GB; eighteen `PRIVYHUB_` lines
   (queue AG adds none), `--check` ok; `85220f99…` CONFIRMED on the onn; only the two units.
2. **The companion restart (B90 live):** `systemctl --user restart privyhub-companion`; eighteen lines, `--check` ok,
   the journal clean; the keeper not restarted.
3. **B90's read (no state changed):**
   - `PRIVYHUB_CHEAT_STAGED` absent from the companion's environment (on by default):
     `tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value privyhub-companion)/environ | grep -c '^PRIVYHUB_CHEAT_STAGED='` → **0**;
   - the fixture measurement's numbers, from the record (not re-run): staged ≤ 1.13 s / ≤ 6 pulses on every size;
     today's walk 93 s (677 / 2), 513 s (2,092 / 4); and
     `python3 -m unittest discover -s tests/b90_cheat_staged -v` → **10 OK** (fixture trees, loopback only);
   - **the staged file's shape on a dry call** (T81, the cheat C46 will name, by its index in the onn's list; reads the
     hub's catalog route and the cached file, writes nothing, launches nothing):
     `python3 -I -B docs/memory/evidence/b90_2026-11-11/scripts/staged_shape.py ~/Projects/onn-stream-test <T81's id> <the cheat's index>`
     → `staged_entries` = `real_indexes` (the pick + its "must be on" code: 2 for HOME-12T's pick), `enabled_true` =
     `staged_entries`, `enabled_false` 0, `pulses_bound` = 2k + 4. Record the counts only.
4. **The install:** preserve `85220f99…` in `home12u_previous/`; copy `queue_ag_built/app-debug.apk` to
   `home12u_installed/`; `adb install -r`; read back **`218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53`**,
   paired; **every property empty (twenty)**. adb for the install and state reads only; no setprop.
5. **Pre-register** C54, C55, C56, C46, hashed: the rows below, the validity rules, the two-part rule.
6. **Reply:** "YOU, now: on the PlayStation game I name (T85's words), press Launch on Companion → Extras → Cheats →
   New Cheat Session, tick one cheat I name, and press Start on your pad. Does it start, and does the cheat work? END.
   Send 'Stage 2'."

### C54 — the picker launches a PS1 cheat (T85; the APK's cell)

- **Hub:** the launch 200; RetroArch's log: the cheat-file line, then **`Applying cheat changes.`**; the session's
  `activation_mode` **"staged"**, `activation_verified` true, `activation_pulses` ≤ 2k + 4; no `launch_orphaned` row.
- **Met:** the user's line (it starts, the cheat works).
- **Reply:** "YOU, now: on the PS2 game I name (T82's words): Launch on Companion → Extras → Patches…. Is Widescreen
  already ticked? Press Save. What does the line at the bottom say? END. Send 'Stage 3'."

### C55 — Patches… opens and Save answers on the PS2 game (T82; the APK's cell)

- **You should see:** Widescreen already ticked (saved at HOME-12T); after Save: "Saved — used the next time this game
  starts".
- **Hub:** `POST /plugins/games/ps2-patches?…ws=1 → 200` in the journal; `details`' `ps2_patches.on` holds `ws`.
- **Met:** the user's two lines (ticked; the saved message). No game needs to start.
- **Reply:** "YOU, now: open your own profile (Options → Input Profile → your profile → Edit Player 1 Mapping). The
  controller picture is now on the left, the list on the right. From where you sit, can you read the letters on the
  picture without getting up? Change nothing — press Back to close it. Send 'Stage 4'."

### C56 — the mapping picture readable from the couch (the APK's cell; B91)

- **You should see:** the controller on the left half (about half the screen's width), its letters the same size as the
  list's words on the right; your profile's changed buttons in yellow; the list scrolls, the picture stays.
- **Met:** **the user's line: readable from the couch.** Nothing saved (the profile's bytes before = after).
- **Reply:** "YOU, now: last one — on the N64 game I name (T81's words): Extras → Cheats → New Cheat Session, tick the
  cheat I name, press Start. Does the game start with the cheat working, and about how long did 'Launching' show? END."

### C46 — the N64 cheat seen in-game within the onn's wait (T81; the hub's cell → B90 / B87 only)

- **Hub:** RetroArch's log: `Load game-specific cheatfile`, then `Applying cheat changes.`; `activation_mode` "staged",
  `activation_verified` true, `activation_pulses` ≤ 2k + 4; **the launch's seconds** (the request's arrival to its 200 in
  the journal / the game log) recorded — expected a few seconds, **well under 60**; **no `launch_orphaned` row**; the
  staged folder held 2 files (B87's names), each `staged_entries` long (counts only).
- **Met:** the user's line (the effect seen) and the 200 inside 60 s. **Not met → B90 not confirmed; the APK's verdict
  unchanged.** If a `launch_orphaned` row appears, record its reason and seconds, and confirm the status read showed no
  game.
- **Reply (the close):** "YOU, now: that's all, thank you. I'll tidy up on the hub."

### The close

- **Every property empty** (twenty); nothing running; the drive before = after; no profile changed.
- **The verdicts:** (a) C54 / C55 / C56 → the APK (`218d9a82…` CONFIRMED or `85220f99…` back); (b) C46 → B90 / B87.
- **The record:** `evidence/HOME_12U_<date>.md` + dir: the cells, the user's lines verbatim, T-labels, C46's seconds.
  No title, serial, game id, code name or path.
- Then KNOWN_ISSUES insertions, the ROADMAP §H6 lines, CURRENT.md, `logs/home12u_git_status.txt`; nothing committed.

## Files

- **Records:** `evidence/B90_CHEAT_STAGED_ENABLED_2026-11-11.md`, `B91_MAPPING_PICTURE_BESIDE_ROWS_2026-11-11.md`, each
  with its dir (the design + hash, the diff, the switch proof, tests, mutations, scripts, redact / title checks, the
  manifest); B90's `measure/` (the scripts, results, the table) and the host-suite comparison; B91's `render/` and the
  APK's files.
- **Patch notes:** `patches/B90_CHEAT_STAGED_ENABLED.md`, `B91_MAPPING_PICTURE_BESIDE_ROWS.md` (not indexed). **New:**
  `companion/launch_orphan.py`, `tests/b90_cheat_staged/`, `PrivyHub/…/streaming/MappingEditorLayout.kt`,
  `B91MappingBesideTest.kt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md` (§H6). **Logs:** `logs/b90_git_status.txt`,
  `logs/b91_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q21ag_base`, `_after_b90`, `_head_tests`, `_headpriv`, `_work`, `_apk`, `_apko`;
  `~/.cache/b_q21ag_tmp/` (the runs, the RetroArch extraction for its strings, the APK builds, the host suites' logs).
