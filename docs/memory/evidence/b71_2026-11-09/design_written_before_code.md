# B71 — "Change disc": the design (written before any B71 code)

Baseline HEAD `94c05e4a`; built in `/tmp/b_q18z_work` after B70 (B70's files are not touched here). B68's `.m3u`s
are applied on the hub ("PlayStation (72)"): six sets (five of 2 discs, one of 4) start at disc 1 and cannot change
disc from the TV.

## 0. Settled (read-only; nothing run, nothing fetched)

- **RetroArch 1.22.2's network commands** (the AppImage's `usr/bin/retroarch` read as an archive with `7z x -so … |
  strings`; its own command table): the disk commands are **`DISK_EJECT_TOGGLE`, `DISK_NEXT`, `DISK_PREV`** — no
  argument, no reply. There is **no set-index and no disk-index query** over the port (`GET_STATUS` answers `GET_STATUS
  PAUSED|PLAYING <system>,<content>,crc32=…`, no disc). The help strings: eject toggle = "If virtual disc tray is
  closed, opens it and removes the loaded disc. Otherwise, inserts currently selected disc and closes the tray"; next /
  prev = "Increments / Decrements the currently selected disc index and does delayed insert if virtual disc tray is
  closed".
- **The index is read from RetroArch's log** (`--verbose`, stderr into the game log, unbuffered): `[Disc] %s` with
  `Setting disc in tray: %u/%u` (then ` - <label>` when the core names the disc), `Removed disk from tray.`,
  `Ejected virtual disc tray.`, `Closed virtual disc tray.` and the `Failed to …` forms. A real game log of the hub
  already holds `[INFO] [Disc] Setting disc in tray: 1/4 - …` at a `.m3u` launch, so **the launch's own line gives the
  starting disc** (RetroArch restores the last used disc of a content by its disk index file, so a set can start at
  disc 2). **The label is never read, kept or logged** (only the two numbers).
- **The sequence a game expects:** the one RetroArch's own Quick Menu does while the core is paused (the menu is
  open): **open the tray, select the disc, close the tray**. Beetle PSX marks the disc changed on the insert and
  reports the lid as opened at the game's next status read, so a game waiting at "insert disc 2" sees the lid cycle
  and reads the new disc when it runs again. The game is therefore **left paused as it was**; the commands are spaced
  (0.4 s) so each runs in its own pass of RetroArch's loop and is confirmed by its own log line before the next.
- **How the onn learns:** today neither the launch response, `status`, the heartbeat nor `launch_ports` says
  anything about discs → added (§1.2).
- **What the TV shows:** the paused game's bar (SAVE / LOAD / END) gains **CHANGE DISC**; the chooser lists
  "Disc 1" … "Disc n" with "(in the tray)" beside the current one; after the swap the status line reads
  **"Disc 2 of 4"**, and the bar's state line carries "Disc 2 of 4" while the session lasts. RetroArch's own notice
  ("Setting disc in tray …") may show briefly over the picture after the resume: RetroArch's default notifications are
  left as they are (not changed for every session); disclosed.

## 1. Host (`companion/disc_swap.py` new; `games/emulator_manager.py`; `plugins/games.py`;
`games/native_stream_heartbeat.py`) — default on, `PRIVYHUB_DISC_SWAP=0` = today

1. **A multi-disc session:** a RetroArch PS1 launch whose content is an `.m3u` with **n > 1** disc lines (non-empty,
   not `#`) → `emulator._disc_session = {"discs": n, "disc": i}`; `i` from the newest `Setting disc in tray: i/n`
   line in this launch's log (read incrementally from the launch's offset), else 1. **Any other launch (one disc, a
   `.cue` / `.chd`, any other system or kind, the knob `0`): `None`, and nothing below happens — every response and
   row byte for byte today's.**
2. **What says it:** `status()` (so the launch response, every SAVE / LOAD / stop reply and the `status` poll the
   onn's banner reads) gains `discs: n, disc: i` (`disc: null` when unknown, §1.4) only when `_disc_session` is set;
   `launch_ports` gains `discs` / `disc`; **every heartbeat row** of the session gains `discs` / `disc` (as B69's
   `gc_mode`: the plugin sets them, the heartbeat writer copies them when present).
3. **The action `POST /plugins/games/disc-swap?disc=j`** → `emulator.disc_swap(j)`:
   - refused (an `EmulatorError`, the PS1 path's error shape) when: no multi-disc session; `j` not in 1..n; the game
     not paused (the bar's buttons are paused-only; "Pause the game to change disc"); not a RetroArch session;
   - `j` == the known current disc → no command; the reply with `changed: false`;
   - else, under the manager's lock: the log offset; **`DISK_EJECT_TOGGLE`** → wait ≤ 1.5 s for `Ejected virtual disc
     tray`; 0.4 s; then **steps**: `DISK_NEXT` when the current is unknown or below `j`, `DISK_PREV` when above, each
     waiting ≤ 1.5 s for its `Setting disc in tray: k/n` (k becomes the current; `Removed disk from tray` = past the
     end) with 0.4 s between, at most 2n steps, until k == j; 0.4 s; **`DISK_EJECT_TOGGLE`** → wait for `Closed virtual
     disc tray`. The game's pause is never touched (no `PAUSE_TOGGLE`); `GET_STATUS` read after → still `PAUSED`
     (else the error);
   - a failure after the tray opened (no step line, k never reaches `j`, a `Failed to …` line) → the tray closed again
     (one `DISK_EJECT_TOGGLE`, its line awaited) and the error "PrivyHub could not change the disc"; the current disc
     is then the last one RetroArch reported;
   - **the reply in the PS1 shape:** `status()` + `action: "disc_swap"`, `accepted: true`, `confirmed: true`,
     `control: "retroarch_network_disk_control"`, `from_disc: i`, `disc: j`, `discs: n`, `changed`, `steps`;
   - **the game log:** `PS1 disc swap: i -> j` (`? -> j` when the start was unknown), and on a failure `PS1 disc swap
     failed: i -> j (<reason>)`; **the recovery row** `disc_swap` with `from_disc`, `disc`, `discs`, `ok`, `steps`,
     `ms` (and `reason` on a failure). No title, label or path anywhere.
4. **A LOAD on a multi-disc session:** a state saved on another disc puts that disc back in the core (the core's own
   state), with no log line → after a successful LOAD the current disc becomes **unknown** (`disc: null`); the next
   swap finds it by its first step's line. Honest rather than a stale number.
5. **The knob:** `PRIVYHUB_DISC_SWAP=0` → `_disc_session` never set and the `disc-swap` action today's unknown-action
   error. Read at each launch.
6. **Tests (`tests/b71_disc_swap`, a fake RetroArch command port: a UDP socket on 127.0.0.1 in a thread that answers
   `GET_STATUS` and, for each disk command, appends RetroArch's own log line to a fake game log):** the `.m3u` count
   (comments / blanks skipped; 1 disc → none); the starting disc from a launch line (and 1 without); the sequence for
   1 → 2, 2 → 4, 4 → 1 and unknown → 3 (the commands in order, the 0.4-s spacing seen by the fake's clock, the pause
   never toggled, the log line, the row); the same disc → no command; refusals (running, out of range, no session);
   a fake that never logs a step → the tray closed again and the error; `Removed disk from tray` past the end → PREV;
   the reply's shape against the PS1 SAVE reply's keys; `status()` / `launch_ports` / heartbeat rows with and without
   a multi-disc session (a one-disc session and the knob `0`: byte for byte the baseline's); a LOAD → `disc: null`; no
   label / title / path in the game log line or the row. Temp dirs removed.

## 2. Client (`MainActivity.kt`; `streaming/DiscChange.kt` new) — default on, `debug.privyhub.disc_change=0` = today

- **`DiscChange`** (pure): `fromValues(discs: Int?, disc: Int?)` → a state or null (null unless discs > 1);
  `showEntry(enabled, state)`; `choices(state)` → the labels "Disc 1" … "Disc n" with " (in the tray)" on the known
  current one; `statusLine(state)` → "Disc i of n" (or "n discs" when unknown); `query(j)` → `disc=j`; `parseReply`
  from the reply's numbers; `PROPERTY`, `parse`, `fromSystem` as B54 / B67's.
- **`MainActivity`:** the `status` poll and the launch response read `discs` / `disc` (absent → null → today); a
  **CHANGE DISC** button in the paused bar beside SAVE / LOAD / END (same style, a wider label), **visible only when
  `discs > 1`** and the property on, enabled only when paused (as SAVE / LOAD), hidden wherever the bar's buttons are
  hidden; its chooser is an `AlertDialog` list; the pick → `POST …/disc-swap?disc=j` on the network executor →
  "Changing to disc j…" then "Disc j of n" (status line) and the bar's state line; an error → the "Change disc"
  dialog with the host's message (the host address masked as the SAVE path does). The paused frame and the session are
  not touched; RESUME afterwards is today's.
- **JVM tests (`B71DiscChangeTest`):** the entry shown only with `discs > 1` (absent / 0 / 1 → hidden; the property
  off → hidden); the labels and the current marker (unknown → none); "Disc 2 of 4"; the reply parse; the property.
- Off (`=0`): no button is ever made visible, nothing is parsed, no request is made — today's bar.

## 3. Mutations, files

- Host: the eject before the steps removed; the close after the steps removed; the pause toggled; the
  one-disc guard removed (a `.cue` session gains keys); the LOAD's unknown removed. Client: `discs > 1` → `>= 1`; the
  current marker on the wrong disc.
- Record `evidence/B71_CHANGE_DISC_2026-11-09.md` + `b71_2026-11-09/`; `patches/B71_CHANGE_DISC.md`. The client part
  goes into the queue's APK.
