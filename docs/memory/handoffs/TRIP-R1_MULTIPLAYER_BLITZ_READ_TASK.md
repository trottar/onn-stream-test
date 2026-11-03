---
memory_schema: 1
as_of: 2026-10-31
status: TASK HANDOFF — TRIP-R1 (session A, READ-ONLY, now, while the user is away at the friend's and may be playing: copies only, no restart, no drop-in, no setprop, no adb (off-LAN), the log-keeper `privyhub-trip-log` untouched). The user: single-player over the trip "ran incredible"; two-player NFL Blitz (PS1) "had a bit of issues". The user's hypothesis: the DualShock is the problem in multiplayer. Find the Blitz session(s), compare them with the single-player sessions on the same link, and say which side the trouble is on — the link, the host, the emulator's pad setup, or the controller's own path — from the rows, with what each side's evidence can and cannot show. Nothing changed; nothing committed
---

# TRIP-R1 — two-player NFL Blitz at the friend's

Read first: `CTRL_L1_CONTROLLER_LOSS_LOCATION_2026-09-24.md` (**the client sends players 0-3 back to back every tick, 36 bytes each, whatever the pad count — so a second pad does not change the uplink rate; the host counts `updates_by_player` and one global sequence**), `FOUR_PLAYER_RETROARCH_PORTS_RUNTIME_2026-09-10.md`, `FOUR_PLAYER_ANDROID_ASSIGNMENT_RUNTIME_2026-09-10.md`, `FOUR_PLAYER_BASE_SLOT_RUNTIME_2026-09-10.md`, `PS1_MULTITAP_*` (D087 / D088: the multitap and the per-port device type for Beetle PSX), `G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` §2-§3 (the per-session method; the start rung and the climb), `UX_R3_…` §1 (the hitch reader), `B30_TRIP_LOG_KEEPER_2026-10-28.md` (where the keeper's copies are: `evidence/trip_2026-10-30/raw/` by file and rotation, `samples/`), `TRIP_PREP_2026-10-29.md` (the state in force: thirteen lines, APK `fcd924c2…`, the guard off).

## 0. Preserve, then what was in force

- Read from `evidence/trip_2026-10-30/raw/` (the keeper's copies — **never written to, never moved; its manifest is its own**) plus the live logs for anything newer than the last copy; assemble into `evidence/trip_r1_2026-10-31/copies/` with `manifest.sha256`. If the user is playing right now, read the live files once and say so.
- In force: thirteen lines; the APK `fcd924c2…` (the guard off, the stall signal and the restart guard on by default); `PRIVYHUB_REMOTE=1` acting (class remote-direct or relayed — state which, per session); the ladder's rung history.

## 1. The sessions

- **Every client session of the trip** (the heartbeats' `elapsed_ms` resets; the companion's request log for the launches — the title stays in the record only as its class and a short tag like "Blitz" / "single-player title A"; no full title if it names a person): start, length, core, **the number of players sending state** (`updates_by_player` > 0 per player; the pad count seen by the host), the overlay path, the rung history, post-/pre-FEC loss, RTT, rendered, resyncs, pauses, holds, stall rows, hitch seconds and silences per 10 min, underruns.
- **The Blitz session(s)** identified by the launch row and by ≥ 2 players sending state. If the user's message names a time, use it; else list the candidates.

## 2. Single vs two-player, on the same link

A table, the two-player session(s) against the single-player sessions nearest in time: the link columns (loss, RTT, path, rung, silences, hitch s), the host columns (the encoder's rate, the host CPU, RetroArch's fps and dup+drop, the capture fps), **the controller columns** (per player: `updates_by_player` per minute, the control gaps ≥ 100 / ≥ 250 ms with their player, the global `lost_packets` rate, the host → onn control-return rate), the client columns (rendered fps, output gaps, underruns, `link_notice`). **The question:** does anything move when the second player appears that does not move with the link? State it from the columns.

## 3. The emulator's pad setup for this title

- From the tree and the host's RetroArch config as it stands (read-only): the Beetle PSX **device type per port** (standard pad / DualShock / analog) and the **multitap** setting per port (D087 / D088), the port mapping the host applies for 2 players (the base slot, the Android assignment, the RetroArch ports), and whether the core's **analog mode / the DualShock's "Analog" toggle** is relevant to a 1998 title (NFL Blitz on PS1 predates DualShock-aware input in many titles: a port set to DualShock with analog on can read as no digital input, or as a different pad, in such games — state what the core options say and what the game's known behaviour is, from the config and the core's documentation in the tree, without fetching).
- **What the logs can and cannot say about the pad:** the host sees each player's state updates and their gaps; it cannot see what the pad itself did or whether RetroArch read the port as digital or analog. Say so plainly.

## 4. The reading, and the on-site A/B

- **One of four, with the evidence for each:** (a) the link (two-player no worse than single on the link columns → not the link); (b) the host (CPU, encoder or RetroArch rows moving with the second player); (c) the emulator's pad setup (the port's device type / multitap / analog mode); (d) the controller's own path (one player's updates arriving at a different rate or with gaps the other does not have — the DualShock hypothesis, as far as the host can see it).
- **For the user, three things they can do at the friend's, each 3-5 minutes, no Code needed:** (1) the same two pads, roles swapped (P1 ↔ P2): does the problem follow the pad or the port?; (2) on the DualShock, press its **Analog** button so the light is off, then play: does it change?; (3) two-player in a different PS1 title (one they played single-player fine): the problem with Blitz only, or with two players? The record says what to tell Code afterwards ("A/B done: <which changed it>") so the next read can place it.
- `evidence/TRIP_R1_MULTIPLAYER_BLITZ_2026-10-31.md` + `trip_r1_2026-10-31/` (the copies, the tables, `redact_check.txt`, `manifest.sha256`); `docs/KNOWN_ISSUES.md` (one line); `logs/trip_r1_git_status.txt`; `CURRENT.md` Next Action (the user's commit after the trip; the A/B; the Blitz pad setup as a B item if (c)). Exit. The reply begins **"YOU, now:"** with the three A/B steps in plain words, then the verdict in two sentences.

No sudo, no nft, the Opal read-only, **no adb (the onn is off-LAN), no restart, no drop-in, no setprop, no run, no game launched, the log-keeper and its files untouched**; copies only; no addresses, names or identifiers (the friend's network and the tailnet as placeholders; titles as tags); nothing fetched, deleted or moved; nothing adopted; nothing committed.
