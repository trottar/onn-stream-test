---
memory_schema: 1
as_of: 2026-11-09
status: HOME-11 DONE (session A; stage 1 2026-11-09 18:53-18:57Z unattended, stages 2-4 22:26-22:45Z with the user at the TV, the close 22:57Z-). APK 85220f99… installed with every property empty (seventeen); C43 MET, C40 MET, C41 MET, C42 MET → **85220f99… CONFIRMED**, the pin moved in the three places (tests green; `patches/HOME-11_APK_PIN.md` indexed). The user's Phase H answer: "Close H" → the H5 checkpoint (`H5_CHECKPOINT_2026-11-09.md`). Nothing adopted; nothing committed
---

# HOME-11: the bar fits, discs start on 1, the warning

Task: `handoffs/HOME-11_DISC_SAFE_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-09AA.md` §A. The directory is
`home11_2026-11-09/`: `stage1/`, `c43/`, `c40/`, `c41_c42/`, `close/`, `pin/`, `preregistration.md` and its `.sha256`,
`LABELS.txt`, `props17.sh`, `ldci_index.sh`, `drive_listing.py`, `redact_check.txt`, `manifest.sha256`. Times are UTC.
T-labels (`LABELS.txt`, HOME-10's): **T15** the one-disc PS1 title, **T17** the 4-disc set. No title, serial, game id
or path is written.

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- Before C43: "One disc game you mean normal game? Like that's such a confusing way to phrase it" (A's reply rephrased
  the step in plain words; the step unchanged).
- C43 (T15): "I'm doing a load" / "Touchpad does nothing, we already established that" / "Save load end" / "Stage 2".
- C40 (T17): "Saw those 4 and everything was on a screen" / "Stage 3".
- C41 / C42 (T17): "Disc 1" / "Pop up occured , disc 2 selected" / "Resumed without issue" / "No message second disc
  click" / "Stage 4".
- Phase H: **"Close H"**.

## Stage 1 (`stage1/STAGE1.md`)

- HEAD `2b5826ea` (queue AA `6885189c` and queue AB / B75 `2b5826ea` committed), the tree clean; `/tmp` 5.9 GB;
  eighteen lines, `--check` ok; `5f72af4b…` CONFIRMED on the onn; **the seventeen properties empty**; the two units.
- **The companion restart 18:54:51Z** (B74's host part live; no drop-in): eighteen lines, `--check` ok, the journal
  clean (33 lines, 0 error / warning), the keeper not restarted; "PlayStation (72)"; **T17's details `discs` 4** (the
  only 4-disc set); **T17's record's `image_index` 0**.
- **The install 18:56Z:** `5f72af4b…` preserved in `home11_previous/`; `queue_aa_built/` → `home11_installed/`,
  **`85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`**, the signer `455bde4e…` the same, `apksigner
  verify` OK; `adb install -r` Success; read back, paired, identity v2; the seventeen properties empty.
- Pre-registration hashed 18:57:13Z (`3dec65f9…ef4b`).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C43** C37's client half on this APK, T15 (`c43/C43.md`) | Started with **LOAD** instead of Start Fresh (the user's choice; recorded, the readings independent of it). "Touchpad does nothing" / "Save load end". `launch_ports` without `discs` / `start_disc` / `launched_disc`; no `PS1 start disc` line, no `[Disc]` line; 23 heartbeats, none with `discs`; the encoder **`-draw_mouse 0`** once before `-window_id` (read live) | **MET → B70's client half** |
| **C40** the paused bar on a set + C41's first half, T17 (`c40/C40.md`) | A first plain start (22:28:48Z, not asked: `start_disc 1`, `record kept`, 1/4; ~27 s) then **Extras → Start on disc… → Disc 4** (22:29:37Z): `launch_ports` **`discs 4`, `start_disc 4`, `launched_disc 4`**; **`PS1 start disc: 4 of 4 (record set)`**, RetroArch's **`Setting disc in tray: 4/4`**; the status `disc 4` of 4. "Saw those 4 and everything was on a screen" (the four buttons whole, END on the screen). After END the record's **`image_index` 3** — its mtime is the host's write at the launch; RetroArch did not rewrite it at this close (disclosed). The bar's "Disc 4 of 4" was not stated by the user (asked; not answered); the status read disc 4 | **MET → B73** |
| **C41** the set starts on disc 1, T17 (`c41_c42/C41_C42.md`) | Left on disc 4 (record 3). **`PS1 start disc: 1 of 4 (record set)`**, then RetroArch's **`Setting disc in tray: 1/4`** as the launch line (without B74: 4/4); `launch_ports` **`start_disc 1`, `launched_disc 1`**; heartbeats `disc 1`. The user: **"Disc 1"** | **MET → B74** |
| **C42** the warning, then a change during the intro, T17 (`c41_c42/C41_C42.md`) | "Pop up occured , disc 2 selected": the warning, "I understand", the chooser, disc 2. The exact text not quoted back by the user; **the installed APK carries it** (`apk_strings.txt`, read from the dex; disclosed). `disc_swap` **`ok true`, `from_disc 1`, `disc 2`, `steps 1`, `ms 953`, `launched_disc 1`**; RetroArch's `Ejected` / `Setting disc in tray: 2/4` / `Closed`, then **`PS1 disc swap: 1 -> 2`**; **the status paused** after the change until RESUME (22:44:08 → 22:44:17Z). "Resumed without issue" (recorded, not scored). **"No message second disc click"**. After END the record's `image_index` **1** (RetroArch's own save at the close) | **MET → B74** |

## What each cell decided

- **The CONFIRMED rule (CL-B7 §6):** C40, C41, C42 and C43 valid and met with every property empty (seventeen, read at
  the install and the close; no `setprop`) → **`85220f99…` CONFIRMED.** The pin moved in the three places
  (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; `pin/`), the tests
  green (`pin/tests.txt`), `patches/HOME-11_APK_PIN.md` indexed. `5f72af4b…` stays in `home11_previous/`.
- C40 → **B73 met** (the four-button bar fits). C41 / C42 → **B74 met** (a set starts on disc 1 unless picked; the
  warning once; the line after a change). C43 → **B70's client half met** on this APK (the host half `-draw_mouse 0`
  live as before).
- **HOME-10's C38 items closed:** the bar's width (C40); the black screen after an unprompted change — settled by B74 as
  the game's reaction and answered by the warning (C42; a change during the intro carried on); RetroArch restoring the
  last disc (C41). **Still open:** a real "insert disc N" prompt (no save near one).

## Phase H — the user's answer

**"Close H"**, read as "close Phase H" → the H5 checkpoint, `evidence/H5_CHECKPOINT_2026-11-09.md`.

## The close (`close/`)

Every property empty (seventeen, `properties_close.txt`); the two units; nothing running (no RetroArch, Dolphin, PCSX2,
encoder or AppImage helper); the drive's folders before = after (`drive_after.txt` = `stage1/drive_before.txt`);
`85220f99…` read back on the onn, paired, identity v2 (`client_close.json`); the keeper unchanged. Eighteen lines (the
drop-ins the same), `--check` ok, CONFIRMED on the new pin.

Left (not deleted): `PrivyHub/app/build/home11_previous/` and `home11_installed/` (the two APKs); `~/.cache/home11_tmp/`
(the watcher's raw log, the raw journal, the dex copies, the test runs' temp dir — off the repo, they carry paths).

Seen, not this session's: `_cowork_prompt_b.txt` modified and `handoffs/QUEUE_2026-11-09AC.md` new — another
session's; untouched.

Nothing adopted; nothing committed.
