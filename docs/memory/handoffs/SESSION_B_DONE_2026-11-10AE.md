# SESSION B — done, 2026-11-10 AE (QUEUE_2026-11-10AE: HOME-12's three requirements — B84 the cheat picker, B85 the cleaned lists, B86 the mapping picture; the APK; run 21:05-21:50Z)

- **Baseline:** `c514c543` (HOME-12 committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files tracked
  and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no companion or keeper restart; no stream, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched;
  - nothing fetched; no emulator started; nothing written to the drive; nothing of A's touched; nothing deleted;
  - **the hub's real cheat files read for counts and shapes only** (no code name, title or path in any record).

## What was built (three diffs applied to the tree in order, uncommitted)

| Item | What | Switch (`0` = today) | Tests ×3 | Mutations |
| --- | --- | --- | --- | --- |
| **B84** (client) | the cheat picker as PrivyHub's own screen: **"Launch Cheat Session · Cancel · n selected" fixed at the top** — **Left** from any row then OK, or the pad's **Start**; Back cancels; a **filter** row (OK → the keyboard; Right → "Selected only"); **sections** General / Player 1-4 / Other / Your files collapsed with counts; L1 / R1 / Channel ± page | `debug.privyhub.cheat_picker=0` | 11 (JVM) | 6 / 6 |
| **B85** (hub) | every system's cheat list cleaned in `cheat-catalog`: lone cartridge triggers hidden, "must be on" codes applied with any pick (not shown), "P1" → "Player 1", bare "P2" rows named from their cheat, "Part n" folded, repeats under the first as "variant n", identical ones folded; Dolphin's names tidied; your own files as they are; the launch expands picks to the real indexes. **Fixed on the way:** a heading row made the reader refuse a whole list (N64 8 of 18, SNES 1 of 13 failed on the onn) | `PRIVYHUB_CHEAT_CLEAN=0`; `raw=1` / `cheat_raw=1` | 8 (through the plugin) | 11 / 11 |
| **B86** (client) | the mapping editor: **a small controller picture drawn by the app** (a plain outline) with what each of your pad's controls sends now, changes highlighted; **rows in one set of letters — "Bottom (✕) → B"**; a legend; display only | `debug.privyhub.mapping_picture=0` | 7 (JVM) | 4 / 4 |

- **The hub's lists, before → after (counts only):** N64 7,562 → 6,561 (biggest 2,092 → 2,072), PS1 2,486 → 2,449,
  SNES 610 → 598. **HOME-12's C46 list: 677 → 588** (306 names + 282 variants; 84 triggers, 1 "must be on", 4
  duplicates hidden; sections General 135, Player 1 152, Player 2 131, Player 3 87, Player 4 83).
- **Absent:** B85 knob `0` / `raw=1` / `cheat_raw=1` byte-equal to HEAD on the same tree (5 / 5); the client switches
  `0` run today's code (the gates in the records).
- **The tree checks:** HEAD + `b84.diff` + `b85.diff` + `b86.diff` = the work copy; reversed → HEAD (0 differences each way;
  `git diff --check` clean; `b86_2026-11-10/diffs_apply_in_order.txt`).
  Host suites on full exports of HEAD and HEAD + B84 + B85: 73 each, the 72 others the same, `tests/art_systems` 112 → 120
  green; failing in both: the same six `tools/` suites as before, and `tests/input_hold_b8` (one off-by-one, 1347 vs
  1348 — it fails on HEAD's export alone and passed in queue AD's runs: pre-existing, time-dependent, listed for the next
  queue) — `b86_2026-11-10/tests_host_compare.txt`.

**The APK `c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`:**
- contents: B5 … + B74 + B80's client part + **B84 + B86**; B27 / B29 out (B85 has no client part);
- built offline (`--no-configuration-cache`), twice → the same bytes; the baseline rebuilds `de6682db…` byte for byte;
  the same signer (`455bde4e…`); JVM 283 / 283 in the APK tree (294 / 294 in the working copy);
- pinned at `PrivyHub/app/build/queue_ae_built/app-debug.apk`, **NOT installed** (`85220f99…` stays on the onn).

**Disclosed (details in the records):**
- **B84's jump key is Left** (Up still moves one row inside the list); Launch is ≤ 2 presses from any row, Start is one.
- **The Android views** (the picker's dialog, the picture) are not exercised by the JVM tests — the project has no
  Robolectric and nothing may be fetched. **C49 and C50 are their checks.**
- **B85: "must be on" codes are applied on the lists' own say-so** (no core documentation on the hub settles whether
  the cores need them). **The biggest N64 lists stay long** — their repeats are real cheats for other targets; the
  picker's sections and filter are the answer. B85's split rule changed from its design to the hub's real "Part n"
  shape; addendum 1 (heading rows) hashed before its fix.
- B86's glyphs are PlayStation's, by position.

**One line for the user:** the cheat list now opens with Launch at the top (press Left from anywhere, or Start on your
pad), split into General and Player 1-4 sections you open one at a time, with a search line; the hub hides the
cheat-cartridge leftovers, switches on "must be on" codes for you and says "Player 1" instead of "P1" — and a few N64
games whose cheat lists didn't open at all now do. The input-profile editor shows a little controller with what each
button does, and reads "Bottom (✕) → B" so the normal layout no longer looks swapped.

## A — HOME-12 resumed (~30 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): **twenty** = HOME-12's eighteen +
`debug.privyhub.cheat_picker` + `debug.privyhub.mapping_picture`. **T-labels:** HOME-12's T81 (N64), T82 (PS2), T83
(GameCube); a PS1 title with a cheat list chosen by A from the hub's data → **T85**.

### Stage 1 — unattended

1. **Preconditions:** HEAD with **queue AE committed** and the tree clean — if B84-B86's files are uncommitted, stop
   with "YOU, now: commit queue AE first, then send the read line again"; `/tmp` ≥ 1 GB; eighteen `PRIVYHUB_` lines
   (queue AE adds none), `--check` ok; `85220f99…` CONFIRMED on the onn; only the two units.
2. **The companion restart (B85 live):** `systemctl --user restart privyhub-companion`; eighteen lines, `--check` ok,
   the journal clean; the keeper not restarted. **Read (counts only):** `cheat-catalog` for T81 →
   `sources[0].clean` true, `raw_count` 677, `shown_count` 588, `hidden` {trigger 84, enabler 1, duplicate 4}, the
   entries' groups General 135 / Player 1 152 / Player 2 131 / Player 3 87 / Player 4 83; with `&raw=1` → 677
   entries and no `clean` key.
3. **The install:** preserve `85220f99…` in `home12r_previous/`; copy `queue_ae_built/app-debug.apk` to
   `home12r_installed/`; `adb install -r`; read back **`c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`**,
   paired; **every property empty (twenty)**. adb for the install and state reads only; no setprop.
4. **Pre-register** C49, C46, C47, C48, C50 and the PS1 check, hashed: the rows below, the validity rules, the
   CONFIRMED rule.
5. **Reply:** "YOU, now: on the N64 game I name (T81's words), press Launch on Companion → Extras → Cheats → New Cheat
   Session. Tell me: is 'Launch Cheat Session' at the top? Read me the section names and the numbers next to them.
   Then go to the filter line at the top, press OK, type a word from a cheat you'd like (like 'lives' or 'health'),
   tick one with OK, and press Left then OK (or Start on your pad) to launch it. Is this list usable now? Send
   'Stage 2'."

### C49 — the cheat picker on T81

- **You should see:** "Launch Cheat Session · Cancel · 0 selected" at the top; "General (135)", "Player 1 (152)",
  "Player 2 (131)", "Player 3 (87)", "Player 4 (83)" (closed); the filter narrows; one tick → "1 selected"; Left → OK
  launches.
- **Hub:** the launch's `cheat_indexes` (the count) and the session's enabled indexes (count: the pick + 1 "must be
  on"); the staged file under `cheat_runtime/Mupen64Plus-Next/`; RetroArch's cheat toggles checked (PS1's check).
- **Met:** the user's line says usable; the sections read out match the counts; the launch reached in a few presses.
- **Reply:** "YOU, now: in the game, does the cheat you picked work (for example, lives stay the same)? END. Send
  'Stage 3'."

### C46 — that N64 cheat seen in-game

- **Met:** the user's line (the visible effect). The cheat's name is not recorded (a label only).
- **Reply:** "YOU, now: on the GameCube game I name (T83's words): Extras → Cheats → New Cheat Session, tick the one I
  name, Launch (Left then OK). Does it work? END. Send 'Stage 4'."

### C47 — a GameCube cheat from the picker, seen

- **Hub:** `GC cheats: 1 enabled` in the game log; the user dir's `GameSettings/<id>.ini` written (section names only);
  `Dolphin.ini` `EnableCheats = True` for that launch.
- **Met:** the user's line.
- **Reply:** "YOU, now: on the PS2 game I name (T82's words): Launch on Companion → Extras → Patches…, tick Widescreen,
  Save, then Start Fresh. Does the picture fill the TV from side to side? END. Send 'Stage 5'."

### C48 — PS2 widescreen on T82 (B80; the APK's own cell from queue AC)

- **Hub:** the details' `ps2_patches`; `PS2 patches: ws=on …` in the game log; the game's settings file
  `EnableWideScreenPatches = true` (the key only).
- **Met:** the user's line (the picture fills the TV).
- **Reply:** "YOU, now: pick any game, press Options → Input Profile → Create New Profile, call it Test, then Edit
  Player 1 Mapping. Look at the little controller at the top: does it show B on your bottom button and A on your right
  one, and do the rows read 'Bottom (✕) → B'? Now change one button (for example, make your Bottom send A) and watch
  the picture: does that button change and light up? Is this clearer than before? Then Cancel, and delete the Test
  profile (Options → Input Profile → Test → Delete). Send 'Stage 6'."

### C50 — the mapping editor's picture

- **You should see:** the outline; Bottom B, Right A, Left Y, Top X; rows "Bottom (✕) → B" …; one change highlighted
  on the picture at once.
- **Hub:** after the delete, `input_profiles.json` holds no "Test" profile (the count of profiles as at stage 1).
- **Met:** the user's line says clearer; the profile deleted.
- **Reply:** "YOU, now: last one — on the PlayStation game I name (T85's words): Extras → Cheats → New Cheat Session.
  Is the list there, tidy, with Launch at the top? Tick one cheat I name and launch it. Does it work? END."

### The PS1 check (T85) — the confirmed path not broken

- **Hub:** `cheat-catalog` for T85 `clean` true; the launch's enabled indexes; RetroArch's toggles checked.
- **Met:** the list opens; the cheat works (the user's line).
- **Reply (the close):** "YOU, now: that's all, thank you. I'll tidy up on the hub."

### The close

- **Every property empty** (twenty); nothing running; the drive before = after; no game carries the Test profile.
- **The CONFIRMED rule for `c801caab…`:** C49, C46, C47, C48, C50 valid and met, and the PS1 check met, with every
  property empty → **`c801caab…` CONFIRMED**; the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; green; the patch notes indexed). Otherwise `85220f99…`
  is reinstalled from `home12r_previous/`, read back, paired, and the user told why in plain words.
- **The verdicts:** C49 → B84 (+ B85 on N64); C46 → B78; C47 → B79; C48 → B80; C50 → B86; the PS1 check → B85 on the
  confirmed path.
- **The record:** `evidence/HOME_12R_<date>.md` + dir: the cells, the user's lines verbatim, T-labels. No title,
  serial, game id, code name or path.
- Then KNOWN_ISSUES insertions, the ROADMAP §H6 lines, CURRENT.md, `logs/home12r_git_status.txt`; nothing committed.

## Files

- **Records:** `evidence/B84_CHEAT_PICKER_2026-11-10.md`, `B85_CHEAT_LIST_CLEAN_2026-11-10.md`,
  `B86_MAPPING_PICTURE_2026-11-10.md`, each with its dir (the design + hash, the diff, the switch proof, tests ×3,
  mutations, scripts, redact / title checks, the manifest); B85's settle and the hub's before / after counts; the APK's
  files, the host-suite comparison and the tree checks in `b86_2026-11-10/`.
- **Patch notes:** `patches/B84_CHEAT_PICKER.md`, `B85_CHEAT_LIST_CLEAN.md`, `B86_MAPPING_PICTURE.md` (not indexed).
- **Docs, insertions only:** `docs/CHEATS.md` (the picker in plain words), `docs/KNOWN_ISSUES.md` (the queue AE line and
  section), `docs/ROADMAP.md` (§H6, the queue AE paragraph). **Logs:** `logs/b84_git_status.txt`, `b85_…`, `b86_…`;
  `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q20ae_base`, `_after_b84`, `_after_b85`, `_work`, `_apk`, `_apko`, `_split`
  (companion/, tools/, tests/, PrivyHub/ and their build outputs); `~/.cache/b_q20ae_tmp/` (the runs' outputs, the three
  APK builds, the host suites' `logs/`, the older suites' own temp dirs). B84-B86's own tests leave no temp dir.
