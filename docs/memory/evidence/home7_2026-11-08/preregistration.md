# HOME-7+N64: pre-registration (written and hashed after the install, before Stage 2, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08V.md` §A (the order, the stage-1 steps, the changed stage-6 reply, C19
shortened, C21-C23 — used exactly), `handoffs/SESSION_B_DONE_2026-11-08U.md` §A (C15-C18 and C20: rows, hub reads,
met, replies — used exactly), `handoffs/HOME-7_JOIN_PS2_N64_TASK.md`, `B54_…`, `B55_…`, `B57_…`, `B59_…`,
`CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md` §6.

**The candidate:** APK `9aa00ba2afe19a7f36b869454d7d5e683185dc97fc116cc6f8f75878bc5fe73f` (queue T: … + B46 + B47 +
B54 hold-to-join), `queue_t_built/` → `home7_installed/`, the signer `455bde4e…` the same; installed `adb install -r`
Success, read back, paired. **Predecessor (CONFIRMED):** `cfe0211c…a65f`, preserved in `home7_previous/`.
**The properties:** all eleven empty throughout (no `setprop` this sitting; hold-to-join on by default).
**The host:** sixteen adopted lines + the bench drop-in `b59-n64.conf` (`PRIVYHUB_N64=1`) = seventeen; `b56-import.conf`
removed at stage 1 (the list "PlayStation (80)", no "(OpenBIOS)"); queues T, U and V live from the restart; the N64
core `mupen64plus_next_libretro.so` fetched on the user's "go N64" (the nightly per-core zip; stable 1.22.2 lists no
per-core files), `n64_core_check --keys` bundled, 12 / 12 keys; "Nintendo 64 (13)" listed.

## The cells, in B's order (rows as B wrote them)

**C15 — hold-to-join, a two-player PS1 title (multitap off: `ports_set` `players 2`, `multitap false`).**
You should see "Hold any button to join"; the tap: no change; the hold: `P1` for 2 s, then "P1 joined — hold to add
Player 2"; controller 2's hold: `P2`, and the line goes; both controllers play. Hub reads: the start's `pad_slots` row
`join: "hold"`, `players_joined` 0; `change` rows `players_joined` 1, then 2, `label` P1 / P2, `claimed_by` prompt; the
heartbeats' `players_joined` 2; `updates_by_player` moving on slots 0 and 1; no `relaunch_ports` row; the launch's
`ports_set` `source` `join` (a stored count) else `metadata`. **Met:** the tap claimed nothing (no `players_joined` 1 row
before the hold) and both joined by a hold.

**C16 — a 1-player title.** P1 by the hold, then no line; controller 2's hold does nothing. Hub reads: the start
response `players` 1; `players_joined` stays 1; no slot-1 entry. **Met:** as read.

**C17 — the multitap at once (C15's title; a third controller's hold).** You should see the paused frame with "Setting
up 4 players…", then the game back where it was, `P3`, "P1, P2, P3 joined — hold to add Player 4". Hub reads:
`relaunch_ports` (`ok` true, `state` `loaded`, `steps_ms`, `total_ms`, `within_budget`); `ports_set` `source: relaunch`,
`players` 4; the relaunch's `PS1 multitap: port1`, `--device=1:1` … `4:1`; RetroArch's `[State] Loading`; the ready;
`players_joined` 3; `updates_by_player[2]` moving; the exit report's `relaunches`. **The time:** the row's start (its time
minus `total_ms`) to the ready, beside the user's count; budget 15 s. **Met:** the game resumed at the save point (the
user's line) with four ports.

**C18 — the PS2 hold's return through PINE (B55).** Recovery log: `state_saved` slot 9, core pcsx2, kind stall,
`ps2_states pine`; `input_release` `ps2_states pine`, `load_ms` < 450, `line` true; `ps2_states` `verdict ok`; `resumed
via client_ready_stall` (or `stall_end`). Game log: `PS2 state save: slot 9 pine 0x09 ok (stall)`, `PS2 state load: slot
9 pine 0x0a ok; <ms> ms`, `PS2 state load: slot 9 picture ok <s>s`. The time: the resume minus the client's return
(≤ 1.0 s). A `rewind_failed` "…(picture static|fault)" is the failure row. **Met:** the game where it was (the user's
line) and `verdict ok`. **Decides B55.**

**C20 — the PS2 multitap relaunch (B57).** You should see "Setting up 4 players…", then the game back where it was (not
at its start screen), `P3`. Hub reads: `relaunch_ports` `ok` true, `state: loaded`, `kind: pcsx2`, `slot` 7, `ps2_states:
pine`, `steps_ms`, `total_ms`, `within_budget`; `ports_set` `source: relaunch`, `players` 4, `multitap` true; the game log
`PS2 relaunch save: slot 7 pine 0x09 ok; file complete <s>s`, `PS2 exit: sigterm <s>s`, `PS2 relaunch load: slot 7 pine
0x0a ok; picture ok <s>s`; the relaunch's PCSX2 log `ELF Loading:` before `Loaded state from slot 7.`, 0 `TLB Miss`; the
merged ini `[Pad] MultitapPort1 = true`; the ready; `players_joined` 3; slots 8 / 9 untouched; no new Game State slot.
The time beside the user's count; budget 15 s, expected ~9.5-13 s. **Met:** the game resumed where it was (the user's
line) with four ports and `state: loaded`. **Not met, to B:** `state: restarted` with its `reason`. Also read: the exit
report's `relaunches.last.ok` beside the host row's. **Decides B57.**

**C19 — the list without the import flag (shortened).** "PlayStation (<n>)" with no "(OpenBIOS)"; no " · NEW"; the
multi-disc sets: expected one entry per disc (the library holds no `.m3u`); the user's counts recorded. **Met:** the
name as above, and the counts recorded (**a reading**).

**C21 — the first N64 title from the onn.** You should see "Nintendo 64 (13)"; the game starting; P1 then P2 by the
hold, with no "Setting up 4 players…"; both controllers driving their players (in a two-player title). Hub reads:
`N64 launch: core=mupen64plus_next ports=4`, `N64 core options: 12 keys (Mupen64Plus-Next)`; the start payload's
`n64_session` and `players_session.device_args` = `--device=1:1` … `4:1`; `ports_set` players 4, `multitap` false,
`multitap_available` false; `pad_slots` change rows `players_joined` 1, 2; no `relaunch_ports` row; RetroArch's log the
core loaded, GLideN64 initialised (GL), no core error; `native-stream-ready`. **Met:** the title played with two pads
joined by the hold, and the user's line on the mapping (**the mapping a reading → B61**).

**C22 — a save and a load with the buttons (RetroArch's).** Hub reads: the save's answer ok and the slot's state file
under `data/games/retroarch/states/` (its size); the load's answer ok; RetroArch's `[State]` lines; the resume. **Met:**
the game back at the save point (the user's line).

**C23 — 10 min of play, the hitch rates.** A 120-s `showinfo` capture of the RetroArch window → `tools/n64_frames.py`
(the internal rate, the distinct-fps median / min, the internal hitch rate); `diag_read` over the sitting (the N64
session's hitch seconds per 10 min beside C15 / C17's PS1 sessions); host CPU, Tctl; the Home hold's `state_saved` slot
9 with `core mupen64plus_next_libretro.so`, the release's load, `resumed`. **Met:** the hitch rate ≤ the PS1 session's
+ 2; the hold resumed where it was (the user's line); the internal rate and its hitch rate recorded (a reading).

## Validity

- The eleven properties empty throughout; seventeen lines; 5 GHz; the user's actions as described; the user's lines
  are the gate on anything on screen; a row's absence is itself the reading. A step the user could not do, or that
  left the app, is invalid, not failed.

## The CONFIRMED rule (CL-B7 §6) and what decides what

- **C15, C16 and C17 valid and met with every property empty → `9aa00ba2…` CONFIRMED**, the pin moved
  (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; tests green; the
  patch note indexed). **Otherwise** `cfe0211c…` reinstalled from `home7_previous/`, read back, paired, the user told why.
- **C18 → B55's verdict; C20 → B57's** (inside the adopted `PRIVYHUB_PS2=1`); **C19 a reading**; **C21-C23 the N64
  reading** (→ B61) and **G-A15 on the user's word only**: the stage-10 question "should N64 stay on (yes / no)?" — "yes"
  → `PRIVYHUB_N64=1` the seventeenth adopted line in G-A13's applied form; otherwise `b59-n64.conf` removed, sixteen
  lines.

Nothing else adopted; nothing committed.
