---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 0eb115d9 (HOME-6 + the user's commit of the prompt / queue files; the code as 68386b32; B54 built in /tmp/b_q12t_b54, applied to the tree with queue T's combined diff, uncommitted)
---

# B54 — hold-to-join replaces the chooser; a third pad brings the multitap at once

**Classification: SETTLED + BUILT.** Client on by default (`debug.privyhub.player_prompt` absent / empty / junk = hold-to-join;
`0` / `off` = none, as the CONFIRMED build). Host keyed on the client's `players_joined` and the new
`native-stream-relaunch-ports` request (no key = today).
- **Tests:**
  - JVM `PlayerPromptTest` 15 (B46's 15 replaced: the chooser is gone, disclosed); the whole JVM suite **228 / 228**;
  - host `tests/players_session` 19 (B46's 13 + 6) and `tests/relaunch_ports` 10 (new), both green ×3;
  - every host suite as the baseline copy (the same six `tools/` tests fail in every copy, identically).
- **Mutations:** 11 caught (6 JVM, 5 host), none survived (`b54_2026-11-08/mut54_jvm.txt`, `mut54_host.txt`).
- **Proof:** `0` (client) and no request (host) = the CONFIRMED build's / today's behaviour, hunk by hunk
  (`b54_2026-11-08/proof_flag_off.md`).
- In queue T's APK (§5), NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b54_2026-11-08/design_written_before_code.md`, sha256 `13bccfbb…78c8`, hashed **18:12:24Z, before any B54
code**. Precondition: only the companion and `privyhub-diag` active; HOME-6 committed (`68386b32`; the user then
committed the prompt / queue files as `0eb115d9`); the tree clean but for the prompt files.

## 0. Settled

- **The hold: 500 ms**, from the pad's first down of a face button (A / B / X / Y) or Start. The prompt ticks every
  50 ms while a pad is holding, so a join lands **500-550 ms** after the press. Key repeats never start a hold; an up
  before 500 ms is a tap.
- **A tap from a pad that has not joined does nothing.** That pad has no player, so there is no port to send it to
  (B46 did the same for a pad beyond the pick).
  - A joined pad's taps reach the game as today.
  - **The joining hold itself is not sent to the game**: a Start held half a second would otherwise pause the game,
    or act in it, at the moment of joining.
  - This is how B54 reads "the press is passed to the game as today" (disclosed).
- **The launch's ports come from `players_joined`** (the onn keeps the title's highest joined count in a new private
  preference):
  - 1 or 2 → two ports; 3 or 4 → the multitap;
  - B46's plan for 1 (port 2 off) is not used, so that a second pad never costs a relaunch (disclosed);
  - B46's `players_chosen` is still accepted exactly as B46.
- **The relaunch at once.** The companion stops the core and launches the same title with the new ports.
  - The encoder is restarted on the new window (it captures the core's own window). The controller session stays up.
  - **On the TV: the paused frame**, under the gate's overlay "**Setting up 4 players…**" / "The game restarts with 4
    controller ports and comes back where it was". The decoder keeps the last frame, as in the link recovery's gate.
  - **PS1 (every RetroArch core): a state round trip.** A relaunch save (SAVE_STATE_SLOT 0 copied to
    `<stem>.state.relaunch`; the user's slots and the recovery save untouched) is loaded into the relaunched core
    while it runs (D-BASE-R3c2's way), then the core is paused.
  - **PS2: the title restarts**, recorded as `state: "restarted"`, `reason: "ps2_no_relaunch_state"`. B55 is built
    after B54 in this queue; routing the relaunch through B55's PINE slot is a follow-up (disclosed).
  - **Refused, nothing touched:** a cheat or mod session; a system with no multitap; the same ports; no stream client.
  - **A failed new launch** → the old ports again, with the same load. **Both launches fail** → the session ends, PS1's
    error shape. **A failed load** → the title runs from its start (`restarted`).
- **The budget: 15 s from the join to play.** Expected ~6-10 s on PS1 (each step is bounded; a fake-timed run is
  7.6 s). The `relaunch_ports` row carries each step's ms; A reads it at C17.

## 1. Built (`b54_2026-11-08/b54.diff`, 17 files)

**Client:**
- **`PlayerPrompt.kt`**, rewritten on B34 / B38's slots:
  - **The opening:** at every start that is not a self-restart, the map is cleared and the line reads "**Hold any
    button to join**".
  - **Joining:** a 500-ms hold gives the lowest open slot, the 2-s badge `PN`, then "**P1 joined — hold to add Player
    2**", "P1, P2 joined — hold to add Player 3", and so on.
  - **Closing:**
    - a 1-player title (host `players` 1) closes after P1;
    - otherwise the line closes when every port is taken;
    - in any case the line goes 10 s after the last join, and comes back while a pad that has not joined is holding.
  - **The third pad on two ports** asks the activity for the relaunch (`players=4`); the line reads "Setting up 4
    players…".
    - On the answer that pad joins as P3, and the line reads "P1, P2, P3 joined — hold to add Player 4".
    - A failure shows "Couldn't set up 4 players".
    - No multitap on the system: "No multitap on this system — 2 players".
  - **The release** as today (Select + Start 2 s; a fresh hold re-joins).
- **`NativeStreamActivity.kt`:**
  - the join hook before the gameplay gate (the chooser's key and hat hooks removed);
  - the tick at 50 ms during a hold;
  - `startRelaunch` (the gate re-entered with no desync post; no release until the host answers; a 30-s read timeout);
  - `&players_joined=N` on the start and every heartbeat;
  - the report: `join: "hold"`, `players_joined`, `relaunches` (the count and the last answer), `ports_set`,
    `pad_claims`, `players`.
- **`MainActivity.kt`:** `&players_joined=N` on the launch (the title's highest count), only with the prompt on.
- **`PlayerChoiceStoreAndroid.kt`:** the file `privyhub_players_joined` (1-4); B46's picks are not read.

**Host:**
- **`relaunch_ports.py`** (new): the sequence pause → save (PS1) → stop the stream → stop → launch(new ports) →
  resume → 1.0-s settle → load → pause → start the stream (the remembered client, the new pid). Then the
  `relaunch_ports` row (players, players_joined, state, steps_ms, total_ms, within_budget, ok) and a `ports_set` row
  with `source: relaunch`.
- **`plugins/games.py`:**
  - the launch takes `players_joined`, and `ports_set` then has `source: join`;
  - the start and the heartbeat pass `players_joined` to `SlotsLog`;
  - the action `native-stream-relaunch-ports` (a refusal answers `ok: false`, `refused`, with today's `ports_set`).
- **`players_session.py`:** `parse_joined`, `ports_for_joined`, `plan(…, source=)`; `ports_set` reads `join` /
  `relaunch` sessions.
- **`pad_slots.py`:** the rows carry `join: "hold"`, `players_joined` and the labels; a changed count is a change row.
- **`emulator_manager.py`:** `save_relaunch_state()` (new); `load_recovery_state_running(source=None)` (None = today).
- **`native_stream_heartbeat.py`:** `join` / `players_joined` kept on the heartbeat row.
- **Test hygiene:** `tests/players_session` and `tests/relaunch_ports` remove their own temp dirs (B53's
  `_tmp_cleanup`).

## 2. Tests

**JVM (fake pads and remote, a fake clock):**
- the opening line;
- a tap claims nothing, and a joined pad's tap reaches its slot;
- 499 ms → nothing, 500 ms → P1, the badge;
- the joining key's repeats and its up are not play, and a fresh press is;
- repeats never start a hold; the remote never joins; a stick never joins;
- a second pad → P2, and the line closes on two ports;
- **a third pad → the relaunch request (4, asked once), "Setting up 4 players…", other holds wait; the answer → P3,
  with P1 / P2 kept, "hold to add Player 4"; a fourth → P4 with no relaunch, and the line closes**;
- a failed relaunch: no P3, the note;
- no multitap: the note;
- **a 1-player title closes after P1**;
- the release and a fresh hold (a held Start does not re-join);
- the 10-s line and its return while a pad holds;
- a self-restart keeps the map; an unpause clears it;
- `PortsSet`; the flag; off → `PadSlots` alone.

**Host:**
- `players_joined` → the ports (1 / 2 → 2, 3 / 4 → the multitap; `source: join`), with 0 or a malformed value giving
  today's call;
- `players_chosen` is still B46's;
- the rows with `join: hold` / `players_joined` / the labels, and the heartbeat row;
- a changed count alone is a change row; without the key, B46's rows exactly;
- the relaunch:
  - **PS1's call order with the state round trip**;
  - **PS2's recorded `restarted` path (no save, no load)**;
  - the failed launch → the previous ports;
  - both failing → the session ended;
  - the failed load → `restarted`;
  - five refusals touching nothing, and a failed save touching only the pause;
  - the endpoint and its refusal row;
- `load_recovery_state_running()` with no source → today's file; with the source → the relaunch file;
  `save_relaunch_state` copies, verifies and is refused on PS2.

## 3. For A (HOME-7 C15 / C16 / C17; the strings)

- **The lines:**
  - "Hold any button to join";
  - "P1 joined — hold to add Player 2";
  - "P1, P2 joined — hold to add Player 3";
  - "Setting up 4 players…" (the gate's overlay: "The game restarts with 4 controller ports and comes back where it
    was");
  - "P1, P2, P3 joined — hold to add Player 4";
  - the badge `P1`…`P4`.
- **The hub reads:**
  - the `pad_slots` rows' `join: "hold"`, `players_joined` and `label`s;
  - the heartbeats' `players_joined`;
  - **`relaunch_ports`** (`state`, `steps_ms`, `total_ms`, `within_budget`) and the `ports_set` row `source:
    relaunch`;
  - the relaunch launch's `PS1 multitap: port1`, `--device=1:1` … `--device=4:1`;
  - the exit report's `join`, `players_joined`, `relaunches`.

**One line for the user:** hold any button for half a second to join. When a third controller holds on a two-player
game, the picture stays on the game's paused frame with "Setting up 4 players…" for about 6-10 seconds (15 at most),
then the game comes back where it was, with that controller as Player 3.

## 4. Files

`b54_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `b54.diff` (`git apply --check` OK on the tree);
- `proof_flag_off.md`;
- `tests_jvm.txt`, `tests_host_b54_x3.txt`, `tests_host_b54.txt`, `tests_host_baseline.txt`, `mut54_jvm.txt`,
  `mut54_host.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B54_HOLD_TO_JOIN.md`.
