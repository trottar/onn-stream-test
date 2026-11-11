---
memory_schema: 1
as_of: 2026-11-11
status: HOME-12U DONE (session A; stage 1 2026-11-11 05:29:50-05:33:35Z unattended — a first read line at 04:54Z stopped inside 04:30-05:30Z after reads only; the cells 05:45Z-06:09Z with the user at the TV; the close 06:09Z-). APK 218d9a82… installed with every property empty (twenty); C54 the picker's PS1 cheat MET, C55 PS2 Patches… ticked + Save MET, C56 the mapping picture MET (readable; the user's new requirement: changed rows yellow in the list too) → **218d9a82… CONFIRMED, the pin moved**; C46 the N64 cheat MET in ~2 s (HOME-12T ~107 s) → B90 / B87 met; C57 the SNES cheat NOT MET (staged and loaded, the effect not seen) → B90's SNES part not confirmed. Nothing adopted; nothing committed
---

# HOME-12U — HOME-12's fourth sitting: the picture beside the rows, and the cheat launch in seconds

Task: `handoffs/HOME-12U_PARITY_FOURTH_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-11AG.md` §"A — HOME-12,
the fourth sitting" (with the handoff's two additions: C57 and the 60-second read). The directory is
`home12u_2026-11-11/`: `stage1/`, `c54/`, `c55/`, `c56/`, `c46/`, `c57/`, `close/`, `pin/`, `preregistration.md` and its
`.sha256`, `LABELS.txt`, `props20.sh`, `drive_listing.py`, `launch_seconds.py`, `title_check.*`, `redact_check.txt`,
`manifest.sha256`. Times are UTC. **T-labels** (`LABELS.txt`): T81 N64, T82 PS2 (widescreen saved), T85 PS1, T86 the
user's own profile's game, **T87 an SNES title** (new). No title, serial, game id, code name or path; no cheat's name.

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt." (twice: 04:54Z, stopped at the window;
  05:29:50Z).
- C54: "Yes and yes" / "Stage 2".
- C55: "Yes" / "Yes" / "Stage 3".
- C56: "Looks almost perfect. Only thing is the buttons that are changed are yellow on the controller image but also in
  the list they should be" / "Stage 4".
- C46: "Game started and cheats worked great. No issues".
- C57: "I was able to select cheat and everything launched but I don't think the cheat applied, I was not invincible".

## Stage 1 (`home12u_2026-11-11/stage1/STAGE1.md`)

HEAD `81ccd731` (queue AG committed), the tree clean; `/tmp` 5.1 GB; eighteen lines, `--check` ok; `85220f99…`
CONFIRMED read back; the twenty properties empty; the two units. **The first read line (04:54Z) was inside
04:30-05:30Z** → stopped after reads only (`stage1/WINDOW_STOP.md`); the second at 05:29:50Z, its first state change at
05:30:01Z. **The companion restart** (B90 live): eighteen lines, `--check` ok, the journal clean (31 lines, 0 error /
warning), the keeper not restarted. **B90's read:** `PRIVYHUB_CHEAT_STAGED=` count 0; `tests/b90_cheat_staged` 10 OK;
the dry call (T81, the cheat C46 named): `real_indexes` 2 = `staged_entries` 2, `enabled_true` 2, `enabled_false` 0,
`pulses_bound` 8. **The 60-second rule's read** (launches without cheats, the journal's 200 against each game log's
opening; a lower bound by under a second):

| system | launches | median | longest | ≥ 45 s | ≥ 60 s |
| --- | --- | --- | --- | --- | --- |
| PS1 | 494 | 1 s | 2 s | 0 | 0 |
| SNES | 73 | 1 s | 2 s | 0 | 0 |
| N64 | 10 | 2 s | 2 s | 0 | 0 |
| PS2 | 23 | 2 s | 3 s | 0 | 0 |
| GameCube | 5 | 3 s | 4 s | 0 | 0 |

None near 60 s — nothing for B. **T87:** 4 SNES titles hold cached cheat lists; one chosen. **The install 05:32Z:**
`85220f99…` preserved in `home12u_previous/`; **`218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53`** in
`home12u_installed/`, the signer `455bde4e…` the same, `apksigner verify` OK, `adb install -r` Success, read back,
paired; the twenty properties empty. Pre-registration hashed 05:33:35Z (`cf829053…`).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C54** T85, PS1 cheat via the picker (`c54/`) | launch 200 in **~1 s**; RetroArch: the cheat file, then `Applying cheat changes.` at load; the one staged entry `on`; `activation_verified` true; `activation_mode` / `pulses` not read live (the status route lacks them; read from the log: ≤ 2 pulses ≤ 6); no `launch_orphaned`; "Yes and yes" | **MET** |
| **C55** T82, Patches… (`c55/`) | Widescreen ticked on opening; **`POST ps2-patches?…ws=1` → 200**; `ps2_patches.on` `ws`; no game; "Yes" / "Yes" | **MET** |
| **C56** the user's profile, the picture (`c56/`) | the profiles file's bytes the same (the editor's Back rewrote it unchanged); "Looks almost perfect" — the one point the list's colour | **MET** (readable; A's reading told to the user; the list's yellow → B) |
| **C46** T81, N64 cheat (`c46/`) | the user's own pick (k = 2); launch 200 in **~2 s** (HOME-12T ~107 s); the stream started; `Load game-specific cheatfile` → `Applying cheat changes.`; **`activation_mode` "staged", `activation_pulses` 2 ≤ 8, `activation_verified` true**; 2 staged files × 2 entries, both enabled; no `launch_orphaned`; "Game started and cheats worked great. No issues" | **MET → B90 met; B87 met** |
| **C57** T87, SNES cheat (`c57/`) | the cheat named (k = 1); launch 200 in **~2 s**; the file staged in **snes9x's own folder** and loaded (`Load game-specific cheatfile`, `Applying cheat changes.`, `Cheat #0: on`); `activation_mode` "staged", `activation_pulses` 1, `activation_verified` true; "I don't think the cheat applied, I was not invincible" | **NOT MET → B90's SNES part not confirmed** |

## What it decided

- **(a) The APK:** C54, C55, C56 valid and met with every property empty (twenty) → **`218d9a82…` CONFIRMED.** The pin
  moved in the three places (`home12u_2026-11-11/pin/`; tests green: e1 self-test, `test_c3_l4_nft_night` 33,
  `test_e1_remote` 21, `tests/client_contract` 5); `patches/HOME-12U_APK_PIN.md` and B80 / B84 / B86 / B89 / B91
  indexed. On the onn: `218d9a82…`.
- **(b) The hub:** C46 met → **B90 met, B87 met** (the N64 cheat launch in ~2 s on the real title); C57 not met → **B90's
  SNES part not confirmed** (the staging and load worked; the effect did not show).
- **HOME-12's three requirements** (the picker's Launch at the top, the cleaned list, the controller picture) are now
  on the CONFIRMED app; B80's Patches… screen too.
- **For B (the next queue):**
  1. **The list's yellow (the user's requirement, C56):** changed buttons yellow in the mapping list too, not only on
     the picture.
  2. **The SNES cheat's effect (C57):** RetroArch reads the staged file and reports the cheat on, but the effect was
     not seen. The picked code (the first source) is a ROM-address `address:value` line; settle on the bench whether
     snes9x's libretro core takes that form or the code itself fails — the same cheat from the title's other sources,
     and a RAM-write code with a visible value. `activation_verified` reads RetroArch's state, not the core's.
  3. **Small, seen in passing:** the cheat session's `activation_mode` / `activation_pulses` are not on the status
     route (only on `POST active-cheats`); the onn polls `GET active-cheats` during a game and gets 400 every second
     (the action is POST-only) — harmless here; the contract test passes it.

## The close (`home12u_2026-11-11/close/CLOSE.md`)

`218d9a82…` on the onn, paired, CONFIRMED on the new pin; every property empty (twenty); the two units; nothing
running; the drive's folders before = after; eighteen lines, the drop-ins the same; `--check` ok; no profile changed;
no `launch_orphaned` row. The hub keeps queue AG's host part live (B90; committed by the user).

Left (not deleted): `PrivyHub/app/build/home12u_previous/`, `home12u_installed/`; `~/.cache/home12u_tmp/` (the watcher's
raw log, the private label map, the catalog reads — they carry titles and ids) and `~/home12_scripts/watch_u.py`,
`launch_seconds.py`.

Nothing adopted; nothing fetched; nothing written to the drive; nothing deleted; no sudo, nft or `setprop`; adb for the
install and state reads; nothing committed.
