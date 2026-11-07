# B46 — the player chooser, per the user (design, written and hashed before any B46 code)

Queue: `handoffs/QUEUE_2026-11-07O.md` §B46. The user: "Player one press any button by default also"; "I want every
game to have that 1 player, 2 player, and multitap"; HOME-3 C6: "It should pop up every time a game is active or
unpaused … to assure consistency and reliability each play session". Baseline `ea40a93f`, the tree clean. Built in
`/tmp/b_q07o_b46` (companion/, tools/, tests/, PrivyHub/ only).

## 0. Settled (read from the code and the installed cores, nothing run, nothing fetched)

**S1. How the ports are set today.** At `launch` (`EmulatorManager.launch`), before RetroArch starts:
- PS1: `_prepare_ps1_multitap_options` reads the title's `ps1_multitap` (`port1` / `off`) from
  `data/games/retroarch/controller_overrides.json` (the per-title metadata the UI writes, D087 / D087R1). With a value it
  writes the content's own core-options file `<RetroArch config>/Beetle PSX HW/<content stem>.opt`
  (`beetle_psx_hw_enable_multitap_port1` enabled / disabled, port 2 always disabled) and adds
  `game_specific_options = "true"` to the session input cfg. With no value nothing is written (`managed: false`).
- The ports' devices: RetroArch's command line, `--device=<port>:<libretro device>` for ports 1-2, or 1-4 with the
  multitap on (PS1 only: the PS1 profile carries a `libretro_device`, 1 digital / 517 DualShock; the other systems carry
  none, so no `--device`). The comment in `_prepare_input_override` records why: RetroArch does not honour
  `input_libretro_device_pN` from config files.
- **So yes: both can be set per session at launch without touching the metadata** — the same `.opt` write and the same
  `--device` arguments, fed from a per-session value instead of the override. Nothing in `controller_overrides.json`
  or the library is written.

**S2. Mid-session: no.** RetroArch's network commands (the interface the hub uses: `PAUSE_TOGGLE`, `GET_STATUS`, save /
load state, `QUIT`) have no command that sets a core option or a port's device; a core reads its options through the
frontend, and the frontend re-reads them only from its own menu. The `.opt` on disk is read at core start. So a choice
made after the launch cannot change the running core's multitap or port devices; it needs a relaunch. **The design
does not relaunch** (it would end the stream and lose the session's progress at an unpause); a choice that needs
different ports is applied **at the next launch of the title**, and the prompt says so. 1 vs 2 needs no host change in
the session: the client sends only claimed slots, so a 1-player choice puts input on one port only.

**S3. SNES.** Both installed SNES cores expose a multitap device for port 2 (read-only `strings` on
`runtime/emulators/retroarch/cores-linux/`): bsnes "Super Multitap", snes9x "Multitap". The device id is 257 in both
cores' libretro sources (`RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_JOYPAD, 0)` = `(1 << 8) | 1`) — **recalled, not readable
from the binaries offline; the A run reads it back** from RetroArch's log. With it on port 2, users 2-5 are the tap's
four sockets, so the hub's four virtual pads are players 1-4. So SNES multitap = `--device=2:257` at launch. NES /
Genesis: no multitap path on this hub → 2, and the prompt says so.

**S4. What "unpause" is.** Back on the onn captures the paused frame and posts `native-stream-stop`; the host pauses
the core (`PAUSE_TOGGLE`). The game tile then reads Resume; Resume opens `NativeStreamActivity` again, whose
`native-stream-start` finds the game paused and whose `native-stream-ready` releases it. A fresh game is the same
start after `launch`. **So every unpause the user means is a new stream start of a running game**, seen by the host as
`native-stream-start` + `ready`, and by the client as the activity's session start. The two other starts are not
unpauses: a self-restart (`RestartGuard`'s pending restart, `guard_end=1`) and a surface-hold return (no new start at
all). Neither shows the chooser; their slots stand.

## 1. The flag (client)

`debug.privyhub.player_prompt`: **absent / empty / junk / `1` = ON** (the chooser); **`0` or `off` = no prompt at all**
= `8ba4d996…`'s absent (no `PlayerPrompt` object, no view, no query or report key, the launch URL as today). `off` is
accepted beside the queue's `0`, as B42's `pad_slots` (disclosed). A failed property read = ON. The prompt still
implies stable slots (B41's OR; with B42's default a no-op). **Disclosed (as B42):** B41's `PlayerPromptTest` cases
move to the new meaning; `theFlag…` reads ON for absent.

## 2. The chooser and the claims (client, `PlayerPrompt.kt` rewritten on B34 / B38's `PadSlots`)

Phases per session: **CHOOSING → CLAIMING → DONE**; never blocking the game (no pause is asked; the game runs).

- **Opening.** At the start response of every session start that is not a self-restart (`restart == null` in the
  session thread): the slot map is **cleared** (`PadSlots.clearAll()`, new), the claims cleared, CHOOSING. At a
  self-restart: DONE at once, the map kept, its slots `claimed_by: stable` (B41's behaviour).
- **CHOOSING:** bottom-centre `Players:  1  /  2  /  multitap (3-4)` with the highlighted option in brackets
  (`[2]`). Left / right from any pad's d-pad (keys, or the hat axis crossing ±0.5) or the remote's d-pad moves the
  highlight; a face button (A / B / X / Y) from a pad, or the remote's centre / Enter, picks. Key repeats
  (`repeatCount > 0`) are ignored. While CHOOSING no pad holds a slot, so pads' game input is dropped (as B41 dropped an
  unclaimed pad's keys) — the game keeps running with no input; the remote's Back still exits.
- **The default highlight:** the title's last choice (kept on the onn in a private preference keyed by sha256 of the
  game's id from the start response's `game_session.game.id`, 12 hex; no title or id stored), else **2**, or **1** when
  the host's B41 `players` is 1 (`player_mode` `single`).
- **The pick** stores the title's last choice, sets `players_chosen` (1 / 2 / 4) and goes to CLAIMING. The picking key is
  marked "needs up" on its device so the pick itself never claims.
- **The claim target** `count` = the choice capped by the session's ports (§3's `ports_set`: 4 with the multitap on,
  else 2). If the choice is multitap and the session's ports are 2: the claims go up to 2 and a second line reads
  `Multitap from the next start` (the system has one) or `No multitap on this system — 2 players` (it has none). If the
  choice is 1 or 2 and the session's multitap is on: claims up to the choice; the line `Multitap off from the next
  start`.
- **CLAIMING:** `Player N — press any button` (N = the lowest open slot below `count`) while an eligible connected pad
  (B38's test) has no slot. The first such pad to press a face button or Start — **a fresh press: `repeatCount == 0` and
  not a key marked "needs up"** — takes that slot, badge `PN` for 2 s; the press reaches the game. When `count` slots
  are held: DONE (no line). **A pad beyond `count` gets no slot** (its input dropped): 1 → one claim and one port in use.
- **The release (C6's held-Start fix):** a claimed pad holding Select + Start 2 s frees its slot (`PN released`), and
  **both keys are marked "needs up"**: a key still held when the release fires (Android repeats the held key) can claim
  only after it is lifted and pressed again. Repeats never claim. Back to CLAIMING.
- **A pad pressing nothing keeps no slot after the prompt:** the map was cleared at the opening and re-forms only from
  claims.
- **Unpause:** the next start (Resume) opens the chooser again with the title's last choice highlighted.

**Rows / keys (only with the prompt on):**
- the start: `&player_prompt=1&pad_claims=…` (as B41) plus `&players_chosen=N` once a choice exists in this process for
  this activity (a self-restart carries the session's choice);
- the heartbeat: `&pad_claims=…` (as B41) plus `&players_chosen=N` once picked;
- the launch (`MainActivity`, only with the prompt on): `&players_chosen=N` when the onn has a last choice for that game
  id (the same sha256 key);
- the report: `players`, `pad_claims` (as B41), plus `players_chosen` (or null) and `ports_set` (the host's echo).

## 3. The host

- **`companion/players_session.py` (new):** `parse("1" | "2" | "4")` → int, else None (3 → None: the client sends 4 for
  multitap); `plan(system, n, libretro_device)` → `{players_chosen, ports, multitap, multitap_available, ps1_mode,
  device_args}`:
  - PS1: 1 → `ps1_mode` off, `--device=1:<dev>` `--device=2:0`; 2 → off, `--device=1..2:<dev>`; 4 → `port1`,
    `--device=1..4:<dev>`;
  - SNES: 1 → `--device=2:0`; 2 → none (today's line); 4 → `--device=2:257`;
  - others: 1 → `--device=2:0`; 2 → none; 4 → none, `multitap_available` false, ports 2.
  - `ports_from_metadata(system, multitap_on)` for a session launched without a choice: 4 with the PS1 multitap on, else
    2, `source: metadata`.
- **`launch`** (`plugins/games.py` handle_post): `players_chosen=<n>` in the query (a valid value) → passed as
  `emulator.launch(…, players_chosen=n)`; **without the key the call is today's** (no new argument passed).
- **`EmulatorManager.launch(…, players_chosen=None)`:** with a value:
  - PS1: `_prepare_ps1_multitap_options(…, session_mode=plan.ps1_mode)` — the session mode replaces the override's
    read; the `.opt` is written (managed) as today's code writes it; `game_specific_options` as today with managed;
  - the `--device` arguments from the plan, replacing today's loop (`_device_args`, new: with no value it returns
    today's list exactly);
  - the session kept (`self._players_session`, cleared at stop) and echoed in the launch payload as `players_session`;
  - **the stale-file guard:** the content stems whose `.opt` a session choice wrote are listed in
    `data/games/retroarch/players_session_opts.json`; a later launch of such a title with **no** `players_chosen` and
    **no** metadata value rewrites its `.opt` with both multitap ports disabled (the metadata's default, `default_off`)
    and drops it from the list, so a choice never outlives its session for a client with the prompt off. A title never
    launched with a choice is untouched (absent = today).
- **`native-stream-start`:** in B41's `player_prompt == "1"` block, `ports_set` added: the session's plan (`source:
  launch`) or `ports_from_metadata` (`source: metadata`); `players_chosen` in the query is passed to B34's `SlotsLog`.
- **`native-stream-heartbeat`:** `players_chosen` passed to `SlotsLog.heartbeat`.
- **`pad_slots.py`:** `SlotsLog.start` / `heartbeat` gain `players_chosen=None`. With claims, each slot entry also carries
  `label` `PN`; a row carries `players_chosen` when given; a change of `players_chosen` is a change row. Without the keys
  every row is B41's byte for byte.
- `player_count.py` unchanged (its `players` is the default's input).

## 4. Tests

**JVM (`PlayerChooserTest`, fake devices as B38 / B41: the virtual remote, pads A and B):**
1. start → the chooser line, `[2]` highlighted; no slot held; a pad's key reaches no slot;
2. pick 2 → `Player 1 — …`; B presses first → P1, A → P2; DONE, no line; `players_chosen` 2; claims `0:p,1:p`;
3. the unpause (a second start, not a self-restart) → the chooser again, the map cleared, `[2]` (the last choice);
4. right, right → multitap → four claims possible: with four fake pads, four claims `0:p…3:p` (ports_set 4);
5. multitap on a 2-port session → claims stop at 2, the line `Multitap from the next start`;
6. 1 → one claim; a second pad's press gets no slot; `players_chosen` 1;
7. the held-Start release: Select then Start held 2 s → released; Start's repeats (`repeatCount` > 0) and a held Start
   never re-claim; after Start up and a fresh press → claimed;
8. a self-restart → no chooser, the map kept as `stable`;
9. the default: last choice wins; else 1 when the host's `players` is 1;
10. the remote's d-pad moves and its centre picks; the remote never claims;
11. the flag: absent / empty / junk / `1` → ON; `0` / `off` → off (no object = today byte for byte: the activity builds
    nothing, as `8ba4d996…`'s absent).

**Host (`tests/players_session`):** `parse`; `plan` per system; `_device_args` with no value = today's list (PS1 2 / 4
ports, others none); with 1 / 2 / 4; `_prepare_ps1_multitap_options` with a session mode in a temp config tree → the
`.opt` read back with `port1` enabled / disabled; with no value and no override → nothing written (today); the stale
guard (a listed stem, no value, no override → rewritten off and unlisted; an unlisted stem → untouched); the handler
passes `players_chosen` only when present; `ports_set` in the start response; the `pad_slots` rows with
`players_chosen` / `label`; without the keys B41's rows exactly.

## 5. Not in B46

A relaunch at the start when the choice changes the multitap (the user may want it: say so); the PS2 path (B48); any
change to the hold, the recovery or the stream.
