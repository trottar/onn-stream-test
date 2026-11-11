# SESSION B — done, 2026-11-11 AH (H6's last quick fixes after HOME-12U: B92 the list's yellow; the SNES cheat and the GET polls settled; the APK)

- **Baseline:** `af063475` (HOME-12U committed); `git status --short` empty; only the companion and `privyhub-diag`.
- **The user's word:** "H6 only has a few quick fixes so let's do that then into h7".
- **Not done:** nothing committed, adopted or installed; no companion or keeper restart; no stream, no adb, no sudo,
  no nft; nothing fetched; nothing written to the drive; nothing deleted. RetroArch was run headless once (B61's form, a
  synthetic SNES ROM, made-up codes, temp folders) for the SNES code-form bench; nothing left running.

## What was found and built

| Item | Found | Built | Tests |
| --- | --- | --- | --- |
| **B92** the list's yellow (C56) | the picture lit changed controls; the list did not | changed rows yellow in the list (red rows still win); `debug.privyhub.mapping_picture=0` = today | 5 JVM ×3, 4 / 4 mutations, full JVM 312 / 312 |
| the SNES cheat's effect (C57) | **the hub applies every SNES code form its lists use** (raw `:` / `=`, Pro Action Replay; ROM and RAM; bench); the pick was an Action Replay ROM patch; the plain list matches the game file | — (a TV check with a cheat from the matching list) | the bench's 9 cases |
| `GET active-cheats` 400s | all from loopback: A's earlier watcher copies (HOME-12U's switched to POST at 05:47Z) | — (not a defect) | — |

**The APK `ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`** = `218d9a82…` (CONFIRMED) + B92; built
twice → the same bytes; the baseline rebuilds `218d9a82…` byte for byte; signer `455bde4e…`; JVM 301 / 301 in the APK
tree; pinned at `PrivyHub/app/build/queue_ah_built/app-debug.apk`, **NOT installed**.

**One line for the user:** the changed buttons are now yellow in the list too; the SNES cheat problem is not the hub —
it applies every kind of SNES code — so next time we try a cheat from the list that matches your copy of the game.

## A — HOME-12V, a short check (~5 min at the TV; the user's pads on the onn, nothing on the hub; every reply starts "YOU, now:")

**Properties:** twenty, read back empty at the start and the close. **T-labels:** HOME-12U's T86 (the user's own
profile's game), T87 (the SNES title).

### The two-part rule (pre-registered, hashed at stage 1)

- **(a) The APK** `ca53df0d…` is CONFIRMED on **C58** valid and met with every property empty → the pin moves in the three
  places (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; green; the
  patch note indexed). C58 not met → `218d9a82…` reinstalled from `home12v_previous/`, read back, paired, the user told why.
- **(b) The hub cell C59** decides B90's SNES part only; it does not roll the APK back.

### Stage 1 — unattended (outside 04:30-05:30Z; no game)

1. HEAD with queue AH committed and the tree clean (else "YOU, now: commit queue AH first, then send the read line
   again"); `/tmp` ≥ 1 GB; eighteen lines, `--check` ok; `218d9a82…` CONFIRMED read back; only the two units. No
   companion restart (queue AH has no host part).
2. **T87's pick:** in the cheat catalog (`POST cheat-catalog`, as the client), the source whose list name matches the
   game file (HOME-12U's third source) — a cheat with a RAM write whose effect is plain on screen (lives, health,
   invincibility); its section and position in the picker noted off the repo.
3. **The install:** `218d9a82…` preserved in `home12v_previous/`; `queue_ah_built/` → `home12v_installed/`; `adb install
   -r`; read back **`ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`**, paired; every property empty
   (twenty). adb for the install and state reads only.
4. Pre-register C58, C59 hashed. **Reply:** "YOU, now: open your own profile (Options → Input Profile → your profile →
   Edit Player 1 Mapping). The buttons you changed are yellow on the picture — are the same rows yellow in the list on
   the right too? Change nothing — press Back to close it. END. Send 'Stage 2'."

### C58 — the list's yellow (T86; the APK's cell; B92)

- **You should see:** the picture's yellow buttons, and the list's rows for those buttons yellow too.
- **Met:** the user's line (yes). The profile's bytes before = after.
- **Reply:** "YOU, now: one more — on the Super Nintendo game I name: Extras → Cheats → New Cheat Session, tick the cheat
  I name (it's in the list I name), press Start. Does the cheat work this time? END."

### C59 — an SNES cheat from the matching list (T87; the hub's cell → B90's SNES part)

- **Hub:** RetroArch's log: the cheat-file line from snes9x's folder, `Applying cheat changes.`; `activation_mode`
  "staged", `activation_verified` true; no `launch_orphaned`.
- **Met:** the user's line (the effect seen). **Not met** → record the code's shape (RAM / ROM; the form) only; B90's
  SNES part stays not confirmed; nothing else changes.
- **Reply (the close):** "YOU, now: that's all, thank you. I'll tidy up on the hub."

### The close

Every property empty (twenty); nothing running; no profile changed; the verdicts (a) C58 → the APK, (b) C59 → B90's SNES
part; `evidence/HOME_12V_<date>.md` + dir (T-labels; no title, id, serial, code name or path; a cheat's name never);
KNOWN_ISSUES insertions; ROADMAP §H6 lines; CURRENT.md; `logs/home12v_git_status.txt`; nothing committed.

## Files

`evidence/B92_MAPPING_LIST_CHANGED_ROWS_2026-11-11.md` + `b92_2026-11-11/`; `patches/B92_MAPPING_LIST_CHANGED_ROWS.md`
(not indexed); `PrivyHub/…/MappingPicture.kt`, `MainActivity.kt`, `B92ChangedRowsTest.kt`; `docs/KNOWN_ISSUES.md`,
`docs/ROADMAP.md` (insertions); `logs/b92_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`. Left: `/tmp/b_q21ah_apk`,
`_apko`; `~/.cache/b_q21ag_tmp/` (the builds, the bench).
