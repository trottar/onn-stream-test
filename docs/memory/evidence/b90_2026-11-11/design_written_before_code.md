# B90 — design, written before code (queue AG, 2026-11-11)

## What is settled before this design (B, headless, B61's form; the full table comes after the code)

- **Today's activation** (`_apply_active_cheat_profile`, HEAD `d1df1f86`): after B87's ready wait (one answered
  `CHEAT_INDEX_PLUS`), pause, then for each enabled index: `_select_cheat_index_state` steps `CHEAT_INDEX_PLUS` one
  answered pulse at a time (≤ 1 s each) **forward only** until the target's line, then `CHEAT_TOGGLE` (0.25 s settle each
  side), then `_select_cheat_index_state` **again for the same index — a full lap of the list** — to read it back; resume.
  For a list of L entries and picks p₁ < … < pₙ (B85's "must be on" codes and parts included) the pulses are
  ≈ Σ ((pᵢ − cursor − 1) mod L + 1) + n·L. HOME-12T's C46: L = 677 → ~2,000 pulses, ~107 s.
- **RetroArch 1.22.2 itself** (the hub's AppImage, its strings read): the `.cht` keys `cheats`, `cheatN_desc`,
  `cheatN_code`, `cheatN_enable`; the setting **`apply_cheats_after_load`** (the hub's persistent `retroarch.cfg` has no
  line → RetroArch's default, off); its log lines `[Cheats] Load game-specific cheatfile: "…"`, `[Cheats] Applying cheat
  changes.` (once per apply, no per-cheat line) and `[Cheats] Cheat #n: <desc>: on|off` (an index pulse's answer).
- **Exploratory headless runs** (the synthetic fixture ROMs: B61's N64 loop, a SNES LoROM loop, a PS-X EXE loop; a
  made-up 12-entry list; a staged file of 2 picks, both `cheatN_enable = true`; no command at all for 4-5 s):
  | core | `apply_cheats_after_load` | `Applying cheat changes.` | core memory at the picks' addresses | index pulses |
  | --- | --- | --- | --- | --- |
  | Mupen64Plus-Next | true | 1 | **the cheat values** | `on` |
  | Mupen64Plus-Next | false | 0 | zeros | `on` (frontend state only) |
  | snes9x | true | 1 | **the cheat values** (`READ_CORE_RAM`) | `on`, `on` |
  | snes9x | false | 0 | the ROM's fill | `on`, `on` |
  | Beetle PSX HW | true | 1 | **the cheat values** | `on`, `on` |
  | Beetle PSX HW | false | 0 | zeros | `on`, `on` |
  So **all three cores apply a loaded file's enabled cheats with no command**, and RetroArch's evidence for it is the
  `Applying cheat changes.` line after the cheat-file line; the index pulse alone reports RetroArch's own state, not the
  core's (the "off" rows show `on` too) — so the line is required, the pulses confirm which cheats.
- **Found while settling — SNES:** the hub runs snes9x (`PRIVYHUB_SNES_CORE=snes9x`), whose library name is `Snes9x`;
  RetroArch looks under `<cheat db>/Snes9x/`, the hub stages under `bsnes/` (`CHEAT_CORE_LIBRARY_NAMES`): a file there is
  **never loaded** (measured: no cheat-file line, no apply, no pulse answered). Every SNES cheat launch on the hub today
  stops with B87's "cheats not ready". In scope here (the queue's "applied the same way on … snes9x").
- **Pulses sent back to back are lost** (a pulse is a one-frame virtual input; a second inside the same hold is no new
  press): the verification paces pulses ≥ 0.1 s apart and re-sends an unanswered one.

## The design (default on; `PRIVYHUB_CHEAT_STAGED=0` = today, byte for byte)

`PRIVYHUB_CHEAT_STAGED`: absent / anything but `0` → on; `0` → every part below off (today's file, folder, config,
walk, and today's launch answer). One switch for the item.

1. **The staged file** (`_prepare_cheat_runtime`, RetroArch systems): when the session has picks (the real indexes after
   B85's `expand()`: the picks, their parts, their "must be on" codes) and the core is one measured here
   (`Mupen64Plus-Next`, `Snes9x`, `Beetle PSX HW`), the staged `.cht` holds **only those entries**, in the source's
   order, **renumbered 0…k−1**, every key of each source entry copied as read (desc, code, and any other `cheatN_` key),
   `cheatN_enable = true`, `cheats = k`. Written under `<stem>.cht` and B87's RetroArch name; the source file's SHA-256
   still verified on read (today's `_read_cheat_source`); the staged bytes verified against what was built. The session
   carries `staged: {count, source_indexes (staged j → the source's index), sha256}`; the profile identity unchanged
   (the source's SHA, the real indexes) — the same profile and isolated saves as today. **No picks** → today's file (all
   off; no activation, as today). **Other cores** (FCEUmm, BlastEm, bsnes: not measured, no lists on the hub today) →
   today's file and today's walk, unchanged.
2. **The folder:** with `PRIVYHUB_SNES_CORE=snes9x` the SNES cheat folder is `Snes9x` (RetroArch's library name for the
   core it runs); otherwise today's names.
3. **The session config:** a staged session's config carries `apply_cheats_after_load = "true"` (in the A7.3 cheat
   block; a base assignment, if one ever appears, replaced so there is exactly one).
4. **The verification** (`_apply_active_cheat_profile`, a staged session): the PLAYING check and B87's ready wait as
   today (the cheat-file line, then an answered pulse); then, **no pause, no toggle**: RetroArch's `Applying cheat
   changes.` line after the cheat-file line in this launch's log, and every staged index reported `on` by an index
   pulse's answer (the ready probe's answer counts; pulses paced ≥ 0.1 s, an unanswered one re-sent after 0.5 s; each
   line's description must equal the staged entry's) — **at most 2k + 4 pulses and 10 s**. Then `activation_verified`
   true, `active_enabled_cheat_indexes` = the real indexes (as today), `activation_verification_lines`, and
   `activation_mode: "staged"`, `activation_pulses`. A miss (no apply line, a cheat `off`, the bound) → today's
   fail-closed path (the game stopped, the staging removed, "Cheat profile activation failed closed: …").
   **Bound:** the cheat work for any list size = the ready wait + ≤ 2k + 4 paced pulses: **target ≤ 15 s on the
   2,092-entry fixture, measured**.
5. **Per core:** the staged form applies on all three measured cores, so none keeps a walk; the walk stays only where
   the staged form is not used (unmeasured cores; the knob 0) — today's walk, unchanged (no "shorter direction" change
   is made, since no measured core needs one).
6. **The hang-up** (`privyhub_service`, the games plugin's `launch` answer only): when the launch returns its payload,
   before the 200 is written, the hub checks the client's connection (a readable socket whose `recv(MSG_PEEK)` is
   empty = the client closed it) and the time since the request began (≥ 60 s = the onn's read timeout has passed);
   and a write that fails (broken pipe / reset) counts the same. Then the hub **does not leave the game running
   unseen**: it calls the plugin's own `stop` path (the onn's Stop: RetroArch's save flush and graceful close, the
   stream's game session ended) and writes one row **`launch_orphaned`** (reason `client_closed` / `client_wait_passed` /
   `answer_failed`, seconds, `stopped`) to the games recovery log. The onn's next status read shows no game. With the
   knob 0 the answer path is today's line for line.

## Tests (`tests/b90_cheat_staged/`, through the companion's real HTTP server on loopback, `client_contract`'s form)

A child `python3 -I` on B85's / B87's fixture tree (its own companion/), the companion's own `privyhub_service`
handler on a `ThreadingHTTPServer` at 127.0.0.1:0, the onn's call `POST /plugins/games/launch?id=…&cheat_source=0&
cheat_indexes=…`; B87's fake RetroArch on loopback **extended**: it reads the session config, loads the staged file
under RetroArch's name, and with `apply_cheats_after_load` on marks the file's enabled cheats on and logs `Applying cheat
changes.`; pulses before the core "runs" lost.
- a **2,092-entry** N64 list launched with n = 1, 3 picks (one with a "must be on" code): 200, `activation_verified`,
  **pulses ≤ 2k + 4 + the ready probes, toggles 0** (counted, not time alone);
- **the staged file's contents**: only the picks + "must be on", renumbered, all `true`, descriptions and codes as in
  the source; the config line present;
- **the knob 0** → today's pulses (the forward walk's count for the same picks on a short list) and no config line;
- **a client that hangs up** before the answer → the game stopped, the status read shows no game, one
  `launch_orphaned` row; the knob 0 → the game left running (today);
- SNES with `PRIVYHUB_SNES_CORE=snes9x` → staged under `Snes9x/` (the knob 0 → `bsnes/`, today);
- the call kept in `tests/client_contract/calls.json` (already listed); temp dirs removed at exit.

## Measurement (after the code; the record's table)

Headless, B61's form: today's walk (HEAD's code, unchanged) and B90's staged activation (the B90 tree's code), each the
hub's own `_apply_active_cheat_profile` driven against the real RetroArch on the fixture ROM; lists of 12, 188, 677 and
2,092 made-up entries; 1, 2, 4 picks; pulses counted through the hub's own `_retroarch_network_request`; time measured;
core memory read at the picks' addresses afterwards. Staged on all three cores; today's walk on N64 (the slow core).

## Not in scope

The client (no change: the onn already waits 60 s); bsnes / FCEUmm / BlastEm (not measured); a mid-launch abort when the
client goes away early (the check is at the answer).
