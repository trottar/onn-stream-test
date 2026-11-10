# SESSION B — done, 2026-11-10 AF (QUEUE_2026-11-10AF: B87 the N64 cheat launch, B88 `ps2-patches` on POST + the client ↔ hub contract test, B89 the mapping picture redrawn; the APK; run 22:35-23:30Z)

- **Baseline:** `051bb4d0` (HOME-12R committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files
  tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no companion or keeper restart; no stream, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched; nothing fetched; nothing written to the drive; nothing of A's
    touched; nothing deleted;
  - **RetroArch was run by B, headless, for B87's reproduction only** — B61's form: the synthetic fixture ROM, made-up
    cheat files, temp folders under `~/.cache` (removed), the companion's display, no stream, no pad; nothing left
    running. The hub's real cheat files and HOME-12R's logs read in place for counts and order only.

## What was found and built (three diffs applied to the tree in order, uncommitted)

| Item | Found | Built | Switch | Tests | Mutations |
| --- | --- | --- | --- | --- | --- |
| **B87** | **The real cause, reproduced headless:** RetroArch names a game's cheat file after the content **with one more dot-suffix stripped** (`X v1.1.v64` → `X v1.cht`); the hub staged `X v1.1.cht`, so a title with a dot inside its name **never got its cheats — on every RetroArch system**; HOME-12R's T81 has one. **Also:** a cheat pulse sent before the N64 core runs is lost (the hub's first pulse at PLAYING: unanswered in every recorded run) | the file staged under RetroArch's name too; before any cheat command, a wait for RetroArch's cheat-file line and an answered pulse (≤ 10 s); a miss stops the game cleanly with "**cheats not ready — the game did not finish loading**" | `PRIVYHUB_CHEAT_READY=0` (3 / 3 byte-equal to HEAD) | 6 (a fake RetroArch on loopback; the 4 N64 cases fail on HEAD with the onn's exact message) | 6 / 7 (1 equivalent) |
| **B88** | the onn's Patches… → Save is a POST; the hub served `ps2-patches` on GET only (B80's / B83's tests called the handler, not the route) | `ps2-patches` on the POST route (the GET unchanged, byte for byte); **`tests/client_contract/`: all 46 hub calls in the client's source as data, a source check, and every call sent with the client's method through the companion's own HTTP server on loopback** | — (a new route) | 5 | 4 / 4 |
| **B89** | "a big poorly drawn controller" — B86's view was half its width tall, labels placed by point | one geometry (a plain original gamepad from arcs, one stroke width, a label box per control, no overlaps), **at most a fifth of the screen's height**; **rendered off the device** (`evidence/b89_2026-11-10/render/`: default, a bottom / right swap, a many-button remap; SVG + PNG) | `debug.privyhub.mapping_picture=0` (B86's gate) | 7 (+ B86's 7) | 5 / 5 (after one test case added) |

- **The contract, before / now:** HEAD's server serves 45 of the 46 calls (`ps2-patches` POST → "Unknown Games plugin
  POST action"); B88's serves 46 / 46. No other mismatch. The PS2 round trip: HEAD's Save 400 and nothing stored;
  B88's 200 and `details` reads `ws` back.
- **The tree checks:** HEAD + `b87.diff` + `b88.diff` + `b89.diff` = the work copy; reversed → HEAD (0 differences each
  way; `git diff --check` clean). **Host suites** on full exports of HEAD and HEAD + B87 + B88: 73 shared suites the same;
  `tests/b87_cheat_ready` (6) and `tests/client_contract` (5) new and green; failing in both: the same six `tools/`
  suites and `tests/input_hold_b8`'s time-dependent off-by-one (queue AE's note). JVM in the working copy 301 / 301.

**The APK `3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1`:**
- contents: B5 … + B74 + B80's client part + B84 + B86 + **B89** (B87 / B88 have no client part); B27 / B29 out;
- built offline (`--no-configuration-cache`) twice → the same bytes; the baseline rebuilds `c801caab…` byte for byte;
  the same signer (`455bde4e…`); JVM 290 / 290 in the APK tree;
- pinned at `PrivyHub/app/build/queue_af_built/app-debug.apk`, **NOT installed** (`85220f99…` stays on the onn).

**Disclosed:** B87's 10-s bound is sized from the fixture (≤ 0.6 s), not a real title; B87's design said "9 of 10"
for the lost first pulse before the runs were tallied (the record has the counts); the contract test fakes what would
start a process or the stream and runs without session identity; B89's renders are the geometry through `java.awt`,
the device draws the same shapes with `Canvas`.

**One line for the user:** the N64 cheat failed because your game's file name has a dot in it and RetroArch looks for
the cheat list under a shorter name — the hub now gives it both names and waits until the game is really running before
switching cheats on; the PS2 "Patches…" Save now reaches the hub, and every button the app sends to the hub is now
checked automatically the same way the app sends it; the controller picture is redrawn, smaller (about a fifth of the
screen) — you can look at it now in `docs/memory/evidence/b89_2026-11-10/render/`.

## A — HOME-12, the third sitting (~20 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): **twenty** (HOME-12R's; queue AF adds none).
**T-labels:** HOME-12R's T81 (N64), T82 (PS2, with a widescreen patch), T85 (PS1); T86 (the user's own profile).

### The CONFIRMED rule, in two parts (pre-registered, hashed at stage 1)

- **(a) The APK** `3f21e2c6…` is **CONFIRMED on its own cells**: **C51**, **C52** and **C53** valid and met, with every
  property empty → the pin moves in the three places (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py`
  `ADOPTED_APK_SHA256` and its test; green; the patch notes indexed). Any of the three not met → `85220f99…`
  reinstalled from `home12t_previous/`, read back, paired, the user told why.
- **(b) Hub-side cells decide hub items only:** **C46** (the N64 cheat seen in-game) decides **B87**; met or not, it
  **does not roll the APK back**.

### Stage 1 — unattended

1. **Preconditions:** HEAD with **queue AF committed** and the tree clean — if B87-B89's files are uncommitted, stop
   with "YOU, now: commit queue AF first, then send the read line again"; `/tmp` ≥ 1 GB; eighteen `PRIVYHUB_` lines
   (queue AF adds none), `--check` ok; `85220f99…` CONFIRMED on the onn; only the two units.
2. **The companion restart (B87, B88 live):** `systemctl --user restart privyhub-companion`; eighteen lines,
   `--check` ok, the journal clean; the keeper not restarted.
3. **B88's read (no state changed):** `curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8765/plugins/games/ps2-patches`
   → **400** with "Missing game id" in the body (the route exists; before B88: "Unknown Games plugin POST action");
   and `python3 -m unittest discover -s tests/client_contract -v` → 5 OK (fixture trees only, no network).
4. **B87's read (counts only):** T81's content name holds a dot inside → **yes** (the staging will write two files at
   C46); `PRIVYHUB_CHEAT_READY` absent from the companion's environment (on by default).
5. **The install:** preserve `85220f99…` in `home12t_previous/`; copy `queue_af_built/app-debug.apk` to
   `home12t_installed/`; `adb install -r`; read back **`3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1`**,
   paired; **every property empty (twenty)**. adb for the install and state reads only; no setprop.
6. **Pre-register** C51, C52, C53, C46, hashed: the rows below, the validity rules, the two-part rule.
7. **Reply:** "YOU, now: on the PlayStation game I name (T85's words), press Launch on Companion → Extras → Cheats →
   New Cheat Session, tick one cheat I name, and press Start on your pad. Does it start, and does the cheat work? END.
   Send 'Stage 2'."

### C51 — the picker launches a PS1 cheat (T85; the APK's cell)

- **Hub:** the launch 200; RetroArch's log: the cheat-file line, the picked index on, `activation_verified` true.
- **Met:** the user's line (it starts, the cheat works).
- **Reply:** "YOU, now: on the PS2 game I name (T82's words): Launch on Companion → Extras → Patches…, tick Widescreen,
  Save. What does the line at the bottom say? Then Start Fresh: does the picture fill the TV from side to side? END.
  Send 'Stage 3'."

### C52 — PS2 Patches… → Widescreen → Save, and the picture fills the TV (T82; the APK's cell + B88)

- **You should see:** "Saved — used the next time this game starts"; the game in widescreen.
- **Hub:** `POST /plugins/games/ps2-patches?…ws=1 → 200` in the journal; `details`' `ps2_patches.on` holds `ws`; the game
  log `PS2 patches: ws=on …`; the game's settings file `EnableWideScreenPatches = true` (the key only).
- **Met:** the user's two lines (the saved message; the picture fills the TV).
- **Reply:** "YOU, now: open your own profile (Options → Input Profile → your profile → Edit Player 1 Mapping). Look at
  the controller picture at the top: is it a good size now, with the rows visible under it, and is it drawn well enough
  to read? Change nothing — press Cancel. Send 'Stage 4'."

### C53 — the mapping picture, smaller and redrawn (the APK's cell; B89)

- **You should see:** a small controller at the top (about a fifth of the screen), the rows below it; your profile's
  changed buttons in yellow.
- **Met:** the user's line: size and drawing acceptable. Nothing saved (the profile's bytes before = after).
- **Reply:** "YOU, now: last one — on the N64 game I name (T81's words): Extras → Cheats → New Cheat Session, tick the
  cheat I name, press Start. Does the game start with the cheat working? If the TV says 'cheats not ready', tell me.
  END."

### C46 — the N64 cheat seen in-game (T81; the hub's cell → B87 only)

- **Hub:** RetroArch's log: **`Load game-specific cheatfile`** present, then `Cheat #` lines, the picked index on;
  `activation_verified` true; the staged folder held two files (the stem's and RetroArch's name; counts only).
- **Met:** the user's line (the effect seen). **Not met → B87 not confirmed; the APK's verdict unchanged.** If the TV
  says "cheats not ready", record the log's order (the cheat-file line yes / no, the first answered pulse's time after
  PLAYING) for B.
- **Reply (the close):** "YOU, now: that's all, thank you. I'll tidy up on the hub."

### The close

- **Every property empty** (twenty); nothing running; the drive before = after; no profile changed.
- **The verdicts:** (a) C51 / C52 / C53 → the APK (`3f21e2c6…` CONFIRMED or `85220f99…` back); (b) C46 → B87; C52's hub
  half → B88.
- **The record:** `evidence/HOME_12T_<date>.md` + dir: the cells, the user's lines verbatim, T-labels. No title, serial,
  game id, code name or path.
- Then KNOWN_ISSUES insertions, the ROADMAP §H6 lines, CURRENT.md, `logs/home12t_git_status.txt`; nothing committed.

## Files

- **Records:** `evidence/B87_N64_CHEAT_LAUNCH_2026-11-10.md`, `B88_PS2_PATCHES_ROUTE_AND_CONTRACT_2026-11-10.md`,
  `B89_MAPPING_PICTURE_REDRAWN_2026-11-10.md`, each with its dir (the design + hash, the diff, the switch proof, tests,
  mutations, scripts, redact / title checks, the manifest); B87's `repro/`; B88's `served_before_now.md`; B89's
  `render/` and the APK's files; the host-suite comparison and the tree checks in `b89_2026-11-10/`.
- **Patch notes:** `patches/B87_N64_CHEAT_LAUNCH.md`, `B88_PS2_PATCHES_ROUTE_AND_CONTRACT.md`,
  `B89_MAPPING_PICTURE_REDRAWN.md` (not indexed). **New test dirs:** `tests/b87_cheat_ready/`, `tests/client_contract/`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md` (§H6). **Logs:** `logs/b87_git_status.txt`,
  `b88_…`, `b89_…`; `handoffs/SESSION_B_STATUS.txt` (the queue line; the checklist's rule sharpened).
- **Left (not deleted):** `/tmp/b_q20af_base`, `_after_b87`, `_after_b88`, `_work`, `_apk`, `_apko` (companion/, tools/,
  tests/, PrivyHub/ and their build outputs); `~/.cache/b_q20af_tmp/` (the runs' outputs, the APK builds, the host
  suites' `logs/`, the older suites' own temp dirs).
