---
memory_schema: 1
as_of: 2026-11-11
status: TASK HANDOFF — HOME-12V, a short check (session A, hardware, attended ~5 min, plus an optional ~5 min for H7's first save state; ONE sitting at the TV, the user with the onn and the pads paired to the onn over Bluetooth as always; nothing asked on the hub; the stages move on the user's "Stage N"; every reply begins "YOU, now:"). Queue AH's APK `ca53df0d…` installed with every property empty (twenty). **The CONFIRMED rule in two parts, pre-registered:** (a) the APK on its own cell — C58 the changed buttons yellow in the mapping list as on the picture; (b) the hub cell C59 — an SNES cheat from the list that matches the game file, seen in-game — decides B90's SNES part only. Optional, on the user's word at the end: H7's first save state (no verdict, no change). Nothing adopted; nothing committed
---

# HOME-12V — the list's yellow, an SNES cheat from the matching list, and (optional) H7's first save state

Read first: `SESSION_B_DONE_2026-11-11AH.md` §"A — HOME-12V, a short check" (**the two-part rule, the stage-1 steps, the cells with their hub reads, "You should see" lines and replies are B's — use them exactly**, with the additions below), `B92_MAPPING_LIST_CHANGED_ROWS_2026-11-11.md` (the changed rows; the SNES bench; the `GET active-cheats` finding), `B93_H7_MINIGAME_PROOF_2026-11-11.md` (the proof tool; "What waits"), `HOME_12U_PARITY_2026-11-11.md` (T86, T87; C56's note; C57), `docs/ROADMAP.md` §H7 (the first step), `docs/memory/CURRENT.md`.

**The user's words that set this task (2026-11-11):** to session B — "H6 only has a few quick fixes so let's do that then into h7"; to Cowork, on HOME-12U's C56 — **"Letters were great."** (recorded here so C56's open note is closed: the user confirmed the picture reads from the couch; `218d9a82…`'s CONFIRMED stands on the user's word). **A writes both lines verbatim into this task's record.**

**A names each game and cheat to the user in the reply only**; T-labels in every record (T86 the user's own profile's game, T87 the SNES title — HOME-12U's; **T88 the SNES game the user names for H7, if the optional step runs**). A cheat's name is never recorded.

**Additions to B's sketch (Cowork's, from reading B's files):**

1. **A stray RetroArch (stage 1, a read).** B92's bench results file ends with `retroarch_left: 1` while its record says none was left. At stage 1: the count of RetroArch processes with no game active. 0 → recorded. Not 0 → its start time and whether its command line points into B's temp bench folders (yes / no, no path written); if it is B's bench instance, stop it with a plain TERM and record that; if it is anything else, stop with "YOU, now:" and say what it is.
2. **C59's pick avoids what the bench did not cover.** B's bench showed the core holding raw `address:value`, raw `address=value` and Pro Action Replay codes (ROM and RAM). **Game Genie codes were not benched.** The cheat A names comes from the list whose name matches the game file, a RAM write with a plain effect on screen, in one of the benched forms; its form (RAM / ROM; which spelling) is recorded, never its name.
3. **`activation_verified` still reads RetroArch's flag** (B built no core check). So C59 is decided by the user's line alone; the hub reads are context.
4. **The `GET active-cheats` rows:** B found they came from A's own watcher on loopback, not the onn. This sitting's watcher uses POST only; the record states the count of `GET active-cheats` rows during the sitting (expected 0), which closes HOME-12U's "seen in passing".

**The stages by the user's message:** the read line = stage 1 (unattended); "Stage 2" = C58; then the user's line on the SNES cheat (C59); then A offers the optional H7 step; the user's "skip" or their lines; the close. **Every reply begins "YOU, now:" with what to press and what the TV shows, in the user's terms.**

## Stage 1 — unattended (~5 min; no game, no movie; **outside 04:30-05:30Z — if the read line arrives inside it, reply "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that" and change nothing**)

B §A stage 1 items 1-4 exactly: HEAD named — **queue AH committed; if B92 / B93's files are uncommitted, stop: "YOU, now: commit queue AH first, then send the read line again"**; `/tmp` ≥ 1 GB; eighteen `PRIVYHUB_` lines, `--check` ok, `218d9a82…` CONFIRMED read back, only the two units; **no companion restart** (queue AH has no host part — confirm from `git show --stat` that the commit touches nothing under `companion/`; if it does, stop and say so); **the stray-RetroArch read** (above); **T87's pick** (above: the matching list, a benched form, a RAM write with a plain effect; its section and position noted off the repo); the install (`218d9a82…` preserved in `home12v_previous/`; `queue_ah_built/` → `home12v_installed/`, sha256 **`ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`**, the signer the same, `adb install -r`, read back, paired, **every property empty — twenty**); the pre-registration hashed (C58, C59 as B's rows with the additions; the validity rules; the two-part rule; the optional step named as carrying no verdict). Exit with B's stage-1 reply.

## The cells — attended, B's cells in B's words

- **Stage 2 — C58** (the APK's cell; B92): the user's line — are the rows for the changed buttons yellow in the list, as on the picture; the profile's bytes before = after. Reply: B's (T87, the list and the cheat named: Extras → Cheats → New Cheat Session, tick it, Start; does the cheat work this time; END).
- **C59** on the user's line (the hub's cell → B90's SNES part only): RetroArch's log — the cheat-file line from snes9x's folder, `Applying cheat changes.`; `activation_mode` "staged", `activation_verified` true; the launch's seconds; no `launch_orphaned`; the code's form (RAM / ROM; the spelling); **the user's line decides** (the effect seen, or not). Not met → B90's SNES part stays not confirmed, nothing else changes. Reply: the optional step's offer (below).

## Optional — H7's first save state (the user's word; no verdict; nothing changes on the hub)

ROADMAP §H7's first step needs one SNES game, one save state just before a two-player contest, and who won. B93's tool is proved on a fixture only. After C59 A replies:

"YOU, now: that's the H6 check done. If you want to start PrivyParty's first proof tonight (about 5 minutes), tell me which Super Nintendo game you'd like as the first mini game — one where two players compete for a short time and the screen shows a score, lives or a winner. Or say 'skip' and we do it another day."

- **"skip"** → the close.
- **A game named** → T88 (the title in the reply only; off the repo in the private label map). Reply: "YOU, now: start that game with player 2 joined (hold to join as usual). Get to the moment just before a short head-to-head contest starts — both players ready, nothing scored yet. Press Home, then SAVE. Then play the contest once. When it ends, END the game and tell me who won and the score the screen showed."
- **Hub reads:** the save's 200 and the state file's existence, size and time (its location off the repo, never a path in the record); the game's system and core; players joined 2. The user's line (who won; the score) verbatim.
- Nothing is run with the tool in this task; the state is not copied or changed. The record's "For B / next" names what the real proof now has (a state, a known winner and score) and what it still lacks (the score's memory addresses — a search between the saved state and later moments, to be designed).

## The close — the two-part rule, the record (unattended)

- Every property empty (twenty); nothing running; the drive before = after; eighteen lines; `--check` ok; no profile changed.
- **(a) The APK:** C58 valid and met with every property empty → **`ca53df0d…` CONFIRMED**, the pin moved (the three places; tests green; B92's patch note indexed). Not met → `218d9a82…` reinstalled from `home12v_previous/`, read back, paired, the user told why in plain words. **(b) The hub:** C59 → B90's SNES part met or not.
- **The record** `evidence/HOME_12V_PARITY_<the UTC date of stage 1>.md` + dir (the cells' tables; the user's lines verbatim, with the two lines above; the stray-RetroArch read; the `GET active-cheats` count; C59's seconds and the code's form; the optional step's reads or "skipped"; the two verdicts; the APK on the onn named; T-labels; no title, serial, game id, code name, cheat name or path; `redact_check`); `KNOWN_ISSUES.md` (insertions only; HOME-12U's items closed where met); ROADMAP §H6 lines (what stays open: the PS2 disc change, a second source for PS2 / GameCube details and the art misses, the user's cheat files, `activation_verified` reading RetroArch's flag) and §H7's status line (the hub side begun on the user's word 2026-11-11: B93's tool; the first state, if made); `logs/home12v_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after).
- The reply: "YOU, now: commit" plus per cell met / not met in one line each, the two verdicts, whether the H7 state was made, and the eighteen lines.

No sudo, no nft, the Opal read-only, adb for the install and state reads, no `setprop` (every property stays empty); no addresses, titles, serials, game ids, code names or paths anywhere in git; nothing written to the drive; nothing fetched; nothing deleted; no `e3_flag.conf`; nothing adopted; nothing committed.
