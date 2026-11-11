---
memory_schema: 1
as_of: 2026-11-11
status: HOME-12T DONE (session A; stage 1 2026-11-10 23:44-23:47Z unattended; the cells 23:48Z-00:03Z with the user at the TV; the close 00:03Z-). APK 3f21e2c6… installed with every property empty (twenty); C51 the picker's PS1 cheat MET, C52 PS2 Patches → Widescreen → Save MET (B88's POST 200), C53 the mapping picture NOT MET (better drawn, labels too small to read from the couch) → **3f21e2c6… NOT CONFIRMED; 85220f99… reinstalled**; C46 the N64 cheat NOT MET (the cheat file now loads, but the launch took ~107 s, past the onn's 60-s wait) → B87 not confirmed. Nothing adopted; nothing committed
---

# HOME-12T — HOME-12's third sitting: the app's own cells, and the N64 cheat

Task: `handoffs/HOME-12T_PARITY_THIRD_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-10AF.md` §"A — HOME-12,
the third sitting". The directory is `home12t_2026-11-10/`: `stage1/`, `c51/`, `c52/`, `c53/`, `c46/`, `close/`,
`preregistration.md` and its `.sha256`, `LABELS.txt`, `props20.sh`, `drive_listing.py`, `title_check.*`,
`redact_check.txt`, `manifest.sha256`. Times are UTC. **T-labels** (`LABELS.txt`): T81 N64, T82 PS2 (a widescreen
patch), T85 PS1, T86 the user's own profile's game. No title, serial, game id, code name or path is written; no cheat's
name.

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- C51: "Yes cheat works" / "Stage 2"; then "Ended without issue" (the PS1 game's end; the PS2 step not yet begun).
- C52: "Used the next time this game starts" / "Then I went back to the game to play and launch" / "It's widescreen" /
  "Stage 3".
- C53: "It looks much better although may be a little too small now, hard to read unless up close" / "Stage 4".
- C46: "I did a different cheat, it's stuck at launching"; after the close's reply: "Then failed from timeout".

## Stage 1 (`home12t_2026-11-10/stage1/STAGE1.md`)

HEAD `904d88fc` (queue AF `da2d580f` committed), the tree clean; `/tmp` 5.3 GB; eighteen lines, `--check` ok;
`85220f99…` CONFIRMED read back; the twenty properties empty; the two units. **The companion restart 23:44:52Z** (B87,
B88 live): eighteen lines, `--check` ok, the journal clean (32 lines, 0 error / warning), the keeper not restarted.
**B88's read:** POST `ps2-patches` on loopback with no id → 400 "Missing game id"; `tests/client_contract` 5 OK.
**B87's read:** T81's content name holds a dot inside → yes; `PRIVYHUB_CHEAT_READY` absent. **The install 23:46Z:**
`85220f99…` preserved in `home12t_previous/`; **`3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1`**
in `home12t_installed/`, the signer `455bde4e…` the same, `apksigner verify` OK, `adb install -r` Success, read back,
paired, identity v2; the twenty properties empty. Pre-registration hashed 23:47:17Z (`72ec6ceb…`).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C51** T85, the picker launches a PS1 cheat (`c51/`) | launch 200 (index 7); RetroArch `Load game-specific cheatfile`, the pick `on`, read back `on`; `activation_verified` true; ran 1 min 7 s; "Yes cheat works" | **MET** (B84 / B85 again) |
| **C52** T82, Patches… → Widescreen → Save (`c52/`) | **`POST ps2-patches?id=T82&ws=1…` → 200** from the onn; `details` `ps2_patches.on` `["ws"]`; the game log `PS2 patches: ws=on ni=off 60=off`; two PCSX2 game-settings files, `EnableWideScreenPatches = true`; "Used the next time this game starts", "It's widescreen" | **MET** (the APK's half: B80's client screen; the hub's half: **B88 met**) |
| **C53** the user's profile, the picture (`c53/`) | the profiles file's bytes before = after (two re-assignments of the stored profile, same bytes); "much better although may be a little too small now, hard to read unless up close" | **NOT MET** — the pre-registered size rule: labels not readable from the couch. The drawing answered (HOME-12R's "poorly drawn") |
| **C46** T81, the N64 cheat in-game (`c46/`) | the user picked another cheat (its list's "must be on" code with it); 2 staged files (B87's names); **`Load game-specific cheatfile` present** (HOME-12R: absent); the ready probe answered at the core's start; both picks `on` and read back; `activation_verified` true — **but the launch answered after ~107 s; the onn waits 60 s and had hung up** (the hub's 200 lost to a broken pipe); the onn "stuck at launching", the game left running paused; A stopped it via the hub's stop route | **NOT MET → B87 not confirmed** (the APK's verdict unchanged) |

## What it decided

- **(a) The APK:** C51 met, C52 met, **C53 not met** → **`3f21e2c6…` NOT CONFIRMED.** `85220f99…` reinstalled from
  `home12t_previous/` (00:04Z), read back, paired; every property empty (twenty, with each APK on). The pin stays;
  nothing indexed. The user told why in plain words.
- **(b) The hub:** **C46 not met → B87 not confirmed** (its two fixes worked on the real title — the file found, the
  wait passed — and the launch then outran the onn); **C52's hub half → B88 met** (the onn's real POST, stored, read
  back, applied).
- **The items:** B84 / B85 met again (C51); B80 met at the TV (C52) — on the unconfirmed APK; B88 met; **B89 half
  met** (the drawing yes, the size no); **B87 / B78 not met** (the launch's length).
- **For B (the next queue, two items):**
  1. **The N64 cheat launch's length:** the hub picks a cheat by stepping RetroArch's cheat index one answered pulse at
     a time round the whole list, for each enabled index and again to read back — ~2,000 steps on T81's 677 entries,
     ~107 s, past the onn's 60-s launch wait; every T81 pick enables two indexes (the "must be on" code). Needed: a
     selection that does not walk the list (e.g. the shorter direction, or the enabled state staged in the file
     RetroArch loads), measured on T81 under 60 s with margin; and when the onn hangs up mid-launch, the hub should not
     leave the game running unseen. Tested on the real N64 path.
  2. **The picture's size:** B89's cap (at most a fifth of the screen's height) makes the labels unreadable at a TV
     distance ("hard to read unless up close"); keep B89's drawing, larger — the labels readable from the couch with
     the rows still visible.

## The close (`home12t_2026-11-10/close/CLOSE.md`)

`85220f99…` on the onn, paired; every property empty (twenty); the two units; nothing running; the drive's folders
before = after; eighteen lines, the drop-ins the same; `--check` ok, CONFIRMED; no profile changed. The hub keeps queue
AF's host part live (B87, B88; committed by the user). T82's widescreen toggle stays saved (the user's own setting).

Left (not deleted): `PrivyHub/app/build/home12t_previous/`, `home12t_installed/`; `~/.cache/home12t_tmp/` (the
watcher's raw log, the catalog reads, the private reads — they carry titles and ids) and `~/home12_scripts/watch_t.py`.

Nothing adopted; nothing fetched; nothing written to the drive; nothing deleted; no sudo, nft or `setprop`; adb for the
install, the reinstall and state reads; one hub stop through its own route (the stuck N64 game); nothing committed.
