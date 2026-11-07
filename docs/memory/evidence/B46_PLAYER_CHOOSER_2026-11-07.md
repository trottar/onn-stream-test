---
memory_schema: 1
as_of: 2026-11-07
baseline_commit: ea40a93f (the tree clean; B46 built in /tmp/b_q07o_b46, integrated by queue O's coordinator)
---

# B46 — the player chooser at every start and every unpause, per the user

**Classification: SETTLED + BUILT**, client on by default (`debug.privyhub.player_prompt` absent = on, `0` / `off` =
none), host keyed on the client's `players_chosen`.
- **Tests:** JVM `PlayerPromptTest` 15 (B41's 10 replaced, disclosed), the whole JVM suite 224 / 224 in the item's copy
  (228 / 228 integrated); host `tests/players_session` 13 green ×3; every host suite as the baseline copy.
- **Mutations:** 3 caught (the repeat / needs-up filter → 2 JVM fail; the opening keeps the map → 1 JVM fail; the
  device arguments ignore the pick → 1 host fail).
- **Proof:** `0` / `off` = `8ba4d996…`'s absent, hunk by hunk (`b46_2026-11-07/proof_flag_off.md`).
- NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b46_2026-11-07/design_written_before_code.md`, sha256 `73e9eb7c…70eb`, hashed **18:11:45Z, before any B46
code**. Precondition: `evidence/G_A13_VOD_LOG_ADOPTION_2026-11-07.md` present (fifteen lines); only the companion and
`privyhub-diag` active; the tree clean.

## 0. Settled

- **The ports can be set per session at launch, without touching the metadata.**
  - PS1: the launch writes the content's own Beetle `.opt` (`beetle_psx_hw_enable_multitap_port1`) just before
    RetroArch starts, from the per-title override. The same write can take a per-session value.
  - The port devices are RetroArch's `--device=<port>:<device>` arguments (RetroArch ignores `input_libretro_device_pN`
    in config files, as the code records).
  - `controller_overrides.json` and the library are not written.
- **Mid-session: no.** RetroArch's network commands cannot set a core option or a port device, and the `.opt` is read
  when the core starts. So a pick at the chooser that needs other ports applies **at the title's next launch**, and the
  prompt says so. 1 vs 2 needs no host change: only claimed slots send input.
- **SNES:** both installed cores have a port-2 multitap device (strings: bsnes "Super Multitap", snes9x "Multitap").
  The id is 257 from their libretro sources. **That id is recalled, not read from the binaries;** A reads it back from
  RetroArch's log. NES / Genesis have no multitap path → 2.
- **"Unpause" is a new stream start of a running game.** Back on the onn → `native-stream-stop` pauses the core; the
  Resume tile opens the stream again → `native-stream-start` + `ready`. The host sees it as that request pair; the
  client sees it as the activity's session start.
  - A self-restart (`guard_end=1`) and a screen-loss hold return are not unpauses: no chooser, the slots stand.

**One line for the user: what "multitap" means on each system today.**
- **PS1:** four pads on port 1 (Beetle's port-1 multitap; port 2 off), set at launch.
- **SNES:** the multitap device on port 2 (players 2-4 through it, `--device=2:257`), set at launch. Built but never
  run on this hub.
- **NES / Genesis:** none here; 2 players.

## 1. Built (`b46.diff`, 13 files)

**Client:**
- **`PlayerPrompt.kt`** (rewritten on B34 / B38's slots), in three phases: CHOOSING → CLAIMING → DONE.
  - **The opening:** at every start that is not a self-restart, the slot map is cleared and the chooser line reads
    `Players:  1  /  [2]  /  multitap (3-4)`.
  - **Choosing:** left / right comes from a pad's d-pad keys or hat (one move per ±0.5 crossing) or the remote. A face
    button (or the remote's centre / Enter) picks. Repeats are ignored.
  - **The default:** the title's last pick, else 2, or 1 when the host's `players` is 1.
  - **Claiming:** `Player N — press any button` up to the pick. The pick is capped by the session's ports
    (`ports_set`), with the line `Multitap from the next start`, `No multitap on this system — 2 players` or
    `Multitap off from the next start`.
  - **A claim needs a fresh press:** no repeat, and no key held through the pick or a release (C6's held-Start fix).
  - **Beyond the pick:** a pad gets no slot.
  - **The release:** Select + Start held 2 s, as before; both keys must then be lifted.
- **`PlayerChoiceStoreAndroid.kt`:** the last pick, in a private preference keyed by sha256 of the game id (12 hex).
- **`PadSlots.kt`:** `clearAll()`.
- **`NativeControllerSender.kt`:** the key's `repeatCount` is passed to the prompt.
- **`NativeStreamActivity.kt`:**
  - the start response calls `onStartResponse(self-restart?, players, ports_set, game key)`;
  - the chooser intercepts keys and the hat before the gameplay gate;
  - `&players_chosen=N` goes on the heartbeat, and on a self-restart's start;
  - the report gains `players_chosen` and `ports_set`.
- **`MainActivity.kt`:** `&players_chosen=N` on the launch, when the onn holds the title's last pick and the prompt is
  on.

**Host:**
- **`companion/players_session.py`** (new): `parse`, `plan(system, n, device)` and `ports_set(emulator, status)`.
- **`EmulatorManager.launch(…, players_chosen=None)`:**
  - the plan's PS1 mode goes to `_prepare_ps1_multitap_options(session_mode=…)`;
  - `_device_args` (new; with no plan it returns today's list);
  - `_players_session` is kept for the session, and the payload carries `players_session`, read back from the
    command's `--device` arguments and the `.opt` written.
- **The stale guard:** a pick's `.opt` is listed in `data/games/retroarch/players_session_opts.json` by a hash of the
  content stem. A later launch with no pick and no metadata value rewrites that `.opt` with both ports off, then
  unlists it.
- **`plugins/games.py`:**
  - the launch passes `players_chosen` only when present (a malformed value means today's launch);
  - the start adds `ports_set` inside B41's `player_prompt=1` block;
  - the start and the heartbeat pass `players_chosen` to `SlotsLog`.
- **`pad_slots.py`:** with `players_chosen`, the rows carry it and each entry carries `label` `PN`; a changed pick
  writes a change row.
- **`native_stream_heartbeat.py`:** `players_chosen` is copied when present.

## 2. Tests

**JVM (`PlayerPromptTest`, fakes: the virtual remote, pads 1-4):**
- the chooser at the start;
- 2, then B first is P1 and A is P2, then no prompt;
- the pick never claims;
- the unpause opens the chooser again with the last pick (and a new activity reads the same store);
- multitap on four ports → four claims;
- multitap on two ports → stops at 2 and says so; a system with no multitap says so;
- 1 → one claim, and the other pad gets no slot;
- the held-Start release re-claims only after a fresh press (repeats and a held Start never claim);
- a short hold releases nothing;
- a self-restart keeps the map and the pick, with no chooser;
- the default;
- the remote and the hat move the chooser, and the remote never claims;
- a stick never claims;
- `PortsSet`;
- the flag: absent / empty / junk / 1 → on, 0 / off → off;
- off → `PadSlots` alone.

**Host (`tests/players_session`):**
- `parse` and `plan` per system;
- `_device_args`: no pick gives today's list, a pick replaces it;
- the `.opt` read back after a multitap pick (`port1` enabled, port 2 disabled, listed by hash, no name in the list);
- a pick of 2 over a metadata multitap writes off and leaves the metadata untouched;
- the stale guard (a listed title rewritten off and unlisted, then today's path; an unlisted title and a non-PS1 title
  untouched);
- the launch handler passes the pick only when present;
- `ports_set` from the launch, else the metadata, and none without the prompt key;
- the rows' `players_chosen` / `label`, and the heartbeat log;
- without the pick, B41's rows exactly.

**Regression:** every `tests/` suite as the baseline copy. Six `tools/` tests fail in a copy, identically in the
baseline copy (queue N wrote "four"; this run counts six with the same runner).
- One `step_in_place` run failed while two suites ran in parallel; it was OK ×3 on rerun on both sides. That is a
  timing test, disclosed.

## 3. For A (HOME-4 C7 / C8 / C9; strings in `SESSION_B_DONE_2026-11-07O.md`)

- **The chooser's line:** `Players:  1  /  [2]  /  multitap (3-4)`.
- **The claim line:** `Player 1 — press any button`; the badge: `P1`.
- **The notes:** `Multitap from the next start` / `No multitap on this system — 2 players` /
  `Multitap off from the next start`.
- **The launch reads back:** the launch payload's `players_session` (`device_args`, `ps1_opt_multitap`); the game log's
  `PS1 multitap:` line; the start response's `ports_set`.
- **Off:** `adb shell setprop debug.privyhub.player_prompt 0` gives no chooser, no `players_chosen` and no `ports_set`.

**For the user:**
- **A relaunch at the start** when the pick changes the multitap is not built; a changed pick applies at the next
  launch. Say if you want it.
- **A 1-player title** now shows the chooser too, with 1 highlighted, per "every game".

## 4. Files

`b46_2026-11-07/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `predecessors/` + `predecessor_sha256.txt`, `after_sha256.txt`;
- `b46.diff` (`git apply --check` OK on the tree);
- `proof_flag_off.md`;
- `tests_jvm.txt`, `tests_players_session_x3.txt`, `tests_mutations.txt`, `tests_host_b46.txt`,
  `tests_host_baseline.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B46_PLAYER_CHOOSER.md`.
