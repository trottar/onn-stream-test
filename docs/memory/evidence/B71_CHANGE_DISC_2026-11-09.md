---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 94c05e4a (B71 built in /tmp/b_q18z_work after B70; its diff against the after-B70 snapshot; applied to the tree second, uncommitted)
---

# B71 — "Change disc": the host's `disc-swap` action and the paused bar's CHANGE DISC entry

**Classification: SETTLED + BUILT**, host + client, both default on:
- the host: `PRIVYHUB_DISC_SWAP=0` = today;
- the client: `debug.privyhub.disc_change=0` = today.

A one-disc session is today's byte for byte, whatever the knobs.

**Tests:**
- host `tests/b71_disc_swap` 21 green ×3 (a fake RetroArch command port; no temp dir left);
- client `B71DiscChangeTest` 5, inside JVM 259 / 259 (working tree) and 248 / 248 (APK tree).

**Mutations: 5 / 5 host and 2 / 2 client caught.** **The APK `64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`**
(B5 … + B54 + B67 + B70 + B71 + B72 (a); B27 / B29 out) is pinned at `PrivyHub/app/build/queue_z_built/app-debug.apk`,
**NOT installed**; `5f72af4b…` stays CONFIRMED.

RetroArch was not started; nothing was fetched; nothing was written to the drive.

Design `b71_2026-11-09/design_written_before_code.md`, sha256 `aaa829c1…f07258dca`, hashed **07:28:36Z, before any B71
code**.

## 0. Settled (read-only)

- **RetroArch 1.22.2's own command table** (read from the AppImage's `usr/bin/retroarch` as an archive with
  `7z x -so … | strings`; nothing run):
  - the disk commands are `DISK_EJECT_TOGGLE`, `DISK_NEXT` and `DISK_PREV`. They take no argument and send no reply;
  - there is no set-index command and no index query;
  - `GET_STATUS` answers `PAUSED|PLAYING <system>,<content>,crc32=…`, with no disc.
- **The index comes from RetroArch's own log lines** (`--verbose`, stderr into the game log): `[Disc] Setting disc in
  tray: k/n[ - <label>]`, `Removed disk from tray.`, `Ejected / Closed virtual disc tray.` and the `Failed to …` forms.
  - A hub game log of a 4-disc set already shows the launch's own `Setting disc in tray: 1/4 - …` line. So the starting
    disc is read, and RetroArch's restore of the last used disc is honoured.
  - **Only the two numbers are read; the label is never kept or logged.**
- **The sequence** is the Quick Menu's, done while the core is paused: open the tray, select the disc, close the tray.
  Beetle PSX marks the disc changed on the insert, so a game waiting at its "insert disc" screen reads the lid cycle
  and the new disc when it runs again.
  - The game is **left paused**, and no `PAUSE_TOGGLE` is ever sent.
  - The commands are 0.4 s apart, each confirmed by its own line before the next is sent.
- **The onn learns from** `discs` / `disc` in `status()`. That one place carries them into the launch response, the
  `status` poll the banner reads, and every SAVE / LOAD / stop reply. They are also on `launch_ports` and on every
  heartbeat row of the session. Before B71 none of these said anything about discs.
- **What the TV shows:**
  - the paused bar: SAVE · LOAD · **CHANGE DISC** · END;
  - the chooser: "Disc 1 (in the tray)" … "Disc n";
  - the status line: "Changing to disc 2…", then **"Disc 2 of 4"**. The bar's state line carries "Disc 2 of 4"
    under PAUSED.
  - RetroArch's own notice ("Setting disc in tray …", which carries the core's label) may show over the picture for a
    moment after the resume. RetroArch's notifications are left as they are for every session (disclosed).

## 1. Built (`b71_2026-11-09/b71.diff`, 9 files; `companion/disc_swap.py` new)

1. **The session:**
   - `session_for(content, system)`: a PS1 `.m3u` with more than one disc line (blanks and `#` lines skipped) →
     `{"discs": n, "disc": 1}`. Anything else, or `PRIVYHUB_DISC_SWAP=0` → None.
   - It is set after the RetroArch Popen and reset at every launch and every session end.
   - `disc` is refreshed from the game log's newest `Setting disc in tray: k/n` (read incrementally).
2. **`disc_swap(j)`** (manager lock):
   - **refused**, in the PS1 error shape:
     - no multi-disc session ("This game has one disc");
     - `j` outside 1..n;
     - not paused ("Pause the game to change disc");
     - not a RetroArch session;
   - the same disc → no command, `changed: false`;
   - else: eject (`Ejected` awaited ≤ 1.5 s), then steps (NEXT when the current is below the target or unknown, PREV
     when above; each step's `Setting … k/n` awaited; `Removed` counts as past the end; at most 2n steps), then close
     (`Closed` awaited);
   - then `GET_STATUS` must still read PAUSED;
   - **a failure after the tray opened closes the tray again** and answers "PrivyHub could not change the disc". The
     current disc is then the last one RetroArch reported.
3. **The reply** (PS1-shaped): `status()` + `action disc_swap`, `accepted`, `confirmed`, `control
   retroarch_network_disk_control`, `from_disc`, `disc`, `discs`, `changed`, `steps`.
4. **Logged:**
   - the game log: `PS1 disc swap: i -> j`, or `… failed: i -> j (<reason>)`;
   - the recovery row `disc_swap` with `from_disc`, `disc`, `discs`, `ok`, `changed`, `steps`, `ms` and the `reason`;
   - `launch_ports` and the heartbeat rows carry `discs` / `disc`;
   - no title, label or path anywhere.
5. **A LOAD on a multi-disc session sets the disc to unknown** (`disc: null`). A state may carry another disc, and no
   log line says which. The next swap finds the disc from its first step's line; the TV shows "4 discs" meanwhile.
6. **The action** `POST /plugins/games/disc-swap?disc=j`, under `PRIVYHUB_DISC_SWAP` (0 → today's unknown-action
   error).
7. **The client** (`DiscChange.kt` + `MainActivity`):
   - the button is visible only when the host says `discs > 1` and the property is on;
   - it is enabled only while paused (as SAVE / LOAD) and hidden wherever the bar's buttons are hidden;
   - the chooser is an AlertDialog list; the pick goes to the action on the network executor;
   - an error shows the "Change disc" dialog with the host's message (the host address masked, as the SAVE path does).

## 2. Tests and mutations

- **Host** (`tests_x3.txt`, `tests_mutations_host.txt`). The fake RetroArch is a real UDP port: it answers `GET_STATUS`
  and appends RetroArch's own lines, labels included, to the game log.
  - detection: the `.m3u` count; one disc / a `.cue` / N64 / unreadable / the knob → none;
  - the starting disc from the launch line (2), or 1 without a line;
  - the swaps 1 → 2, 1 → 3 (the 0.4-s spacing), 4 → 1 (PREV ×3), 2 → 4, unknown → 3 (NEXT stays at 4, then PREV),
    and `Removed` past the end → PREV;
  - the same disc → no command; the refusals; no step line → the tray closed again with the error; no eject line →
    nothing stepped blind;
  - the reply against the PS1 shape; the row; the label never in a PrivyHub line;
  - `status` keys only on a live multi-disc session; a LOAD → `disc: null`; the heartbeat writer;
    `launch_ports` with / without; the action, its row and the knob; every session end clears it.
  - Mutations caught: M1 no eject, M2 no close, M3 the pause toggled, M4 the one-disc guard removed, M5 the LOAD's
    unknown removed.
- **Client** (`tests_jvm.txt`, `tests_mutations_jvm.txt`):
  - the entry only with `discs > 1` (absent / 0 / 1 / the property off → none);
  - the labels with "(in the tray)" (unknown → none); "Disc 2 of 4" / "4 discs";
  - the reply parse (an out-of-range disc → unknown); the property.
  - Mutations caught: `>= 1`; the marker on the wrong disc.

## 3. The APK

- **The tree:** the after-B72 client sources (B70 + B71 + B72 (a) on B5 … B67) with `b29.diff` / `b27.diff` reversed
  on the client paths. That is queue X's composition, plus the three.
  - **B72 (a) is in it too** (the queue's list names B70 + B71). C39 reads that card on the new APK; disclosed.
- **Built:** `:app:assembleDebug --offline --rerun-tasks --no-configuration-cache`, **twice → the same bytes**
  `64d02f31…85dd` (9,714,892 B, 945 entries).
- **Reproducibility:** the baseline client (HEAD, B29 / B27 reversed) rebuilds **`5f72af4b…` byte for byte**. The only
  source difference is the 8 files in `apk_source_diff.txt`.
- **`apksigner verify`:** Verifies (v2), with the same signer certificate as `5f72af4b…`.
- **Not installed.** A build of this session (`c0cc6479…`) was superseded before any record: the same sources without
  B72 (a)'s `shown_top` key. It was never installed and was overwritten in `queue_z_built/`.

## 4. Files

`b71_2026-11-09/`:
- the start files; the design + its hash;
- `b71.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`;
- `tests_x3.txt`, `tests_in_the_tree.txt`, `tests_jvm.txt`, `tests_jvm_apk_copy.txt`, `tests_mutations_host.txt`,
  `tests_mutations_jvm.txt`;
- `apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`;
- `redact_check` / `title_check` (+ `.txt`), `manifest.sha256`.

Patch note: `patches/B71_CHANGE_DISC.md`.

**One line for the user:** on a two- or four-disc PlayStation game, Back now shows CHANGE DISC beside SAVE / LOAD /
END. Pick the disc and the bar says "Disc 2 of 4"; the game stays paused until you resume. A one-disc game looks as
before.
