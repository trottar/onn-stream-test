# B62 — design, written before any B62 code (the N64 mapping on T6)

Queue: `handoffs/QUEUE_2026-11-08W.md` §B62. Built after B61 in `/tmp/b_q15w_work` (the diff is against the after-B61
snapshot), inside `PRIVYHUB_N64=1`. T5 / T6 are HOME-7's labels; no title here.

## 0. Settled

**The user's line (C23, T6):** "Half the buttons didn't work so I couldn't jump as any player." T5 (C21): "Felt good to
play, no issues."

**What reached what:**
- **The presses reached the host.** The heartbeats' `updates_by_player` climbed for P1, P2 and P3 through T6's session
  (e.g. `[111, 17, 42, 0]` at 22:33:45 → `[377, 254, 396, 0]` at 22:35:25).
- **RetroArch configured the four virtual pads,** `Autoconf PrivyHub Virtual Gamepad P1-P4 configured in port 1-4`
  (T6's log).
- **The launch was as B59 built it:**
  - `N64 core options: 12 keys`; `--device=1:1 … 4:1`;
  - "Game controller 0-3 (Standard controller) has a Memory pak plugged in";
  - `privyhub-input.cfg` with `analog_dpad_mode "0"`;
  - **no remap file** (none existed; the log has no `[Remap]` line).
- **Nothing raced:** B59 writes no remap, so there is no per-launch race to have. The layout is the core's own.

**The core's own layout** (its input descriptors, the strings in the installed `.so`, read and never loaded;
`core_input_descriptor_strings.txt`):

| RetroPad | the onn's pad | the core's descriptor | so |
| --- | --- | --- | --- |
| B (south) | ⨉ / A | "A Button (C3)" | N64 A |
| Y (west) | □ / X | "B Button (C2)" | N64 B |
| **A (east)** | **○ / B** | **"(C1)"** | **nothing, unless "C Buttons Mode" is held** |
| **X (north)** | **△ / Y** | **"(C4)"** | **nothing, unless "C Buttons Mode" is held** |
| one shoulder / trigger | — | "C Buttons Mode" | the hold that turns the face buttons into C-buttons |
| L2 / R / L | — | "Z Trigger", "R Shoulder", "L Shoulder" | Z, R, L |
| right stick | right stick | "C Buttons X / Y" | the four C-buttons |

- **"Half the buttons"** is two of the four face buttons (○ and △), which do nothing in this layout for every player
  and every title.
- **T6's jump is on the C-buttons** (the right stick here; recalled for that title). The user had no way to know, and
  pressed the face buttons. T5's controls sit on A / B, so T5 felt fine.
- **This is per layout, not per title,** and not a core-option or pak problem. The paks are plugged on all four ports;
  T6 saves to its cartridge (the core's "Save type").

**The remap path, on the hub** (the B61 fixture, headless, temp config, no title):
- a core remap `<RetroArch config dir>/remaps/Mupen64Plus-Next/Mupen64Plus-Next.rmp` → RetroArch logs `[Remap]
  Core-specific remap found at …`;
- with `remap_save_on_exit = "false"` the file is unchanged after the quit
  (`repro/ra_log_remap_line.txt`, `repro/result_remap_loaded.json`);
- the remap's effect on a game's input cannot be seen with the fixture (no input read). **C24 decides it**, on the
  user's line.

## 1. The fix

1. **The idle face buttons get C-buttons, by a core remap written and verified at every N64 launch** (Mupen64Plus-Next
   only):
   - for players 1-4, `input_player<n>_btn_a = "20"` (east ○ → right analog X+, i.e. **C-right**) and
     `input_player<n>_btn_x = "23"` (north △ → right analog Y−, i.e. **C-up**). RetroArch's analog bind indices are
     recalled (16-23 = left X+ / X− / Y+ / Y−, right X+ / X− / Y+ / Y−); C24 reads them back;
   - nothing else is remapped: A on ⨉, B on □, the C-buttons on the right stick, Z on L2 are all kept;
   - written temp + rename, **read back and compared** before the launch. A mismatch refuses the launch ("N64 remap
     could not be verified"), so a launch never runs on an unknown layout;
   - other `.rmp` files in that folder (a game or content-directory remap would take priority in RetroArch) are
     **counted and logged as `shadowed`**. B never writes them; none exist today;
   - `privyhub-input.cfg` gains, for an N64 launch only, `auto_remaps_enable = "true"` and `remap_save_on_exit =
     "false"`, so RetroArch loads the file and never rewrites it.
2. **A per-title layout from the metadata** (the override path; no title needs it today):
   - `controller_overrides.json` `games[<id>].n64_layout`: `"face_c"` (the default above) or `"core"` (the core's own
     layout: the file written with no binds, for a title that wants ○ / △ idle);
   - an unknown value → the default, and the game log says `ignored`;
   - read at launch; **no writer is built** (edited on the user's word).
   - **The pak per title: not built.** No title showed a pak problem; the four memory paks stay.
3. **The layout on the TV without an APK:**
   - the game's details line "Controller: <label>" (the onn shows the host's `controller_profile_label`) reads, for an
     N64 title, **"A = ⨉, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2"**, or for `core`
     "A = ⨉, B = □, C-buttons = right stick, Z = L2", instead of "Core default";
   - **disclosed:** whether the onn's font draws ⨉ □ △ ○ is read at C24. If not, words go in their place;
   - **for the next APK, listed and not built:** the line shown once on the TV at the first N64 launch.
4. **The game log:** `N64 remap: face_c (players 1-4, 8 binds) verified` (or `core (no binds) verified`, `+ shadowed
   <n>`); the payload's `n64_session` gains `layout`.
5. **`tools/n64_core_check.py --remap`** (read-only, for HOME-8 stage 1, before any launch): the folder, whether the
   file is there and matches the default layout (`matches` / `differs` / `absent`, which the first launch writes),
   the shadowing count, and the folder's writability.

**Absent = today:** every hook is inside the N64 launch, the N64 catalog branch or the tool. Without `PRIVYHUB_N64=1`
nothing is reached, and other systems' input files and labels are byte for byte.

## 2. Tests (`tests/b62_n64_mapping/`, plus B59's launch harness extended)

- **The remap text:** 8 binds for players 1-4 (`face_c`), none for `core`; written, read back, verified; a tampered
  read-back → the launch refused; idempotent.
- **The launch** (B59's fake RetroArch tree, `XDG_CONFIG_HOME` a temp dir):
  - the `.rmp` present and complete before the Popen, for every N64 title (two fake titles);
  - the input cfg's two lines; the log line; `n64_session.layout`;
  - a metadata `n64_layout: core` → no binds, the label without the face part;
  - a bad value → the default, logged `ignored`;
  - a shadowing `.rmp` counted;
  - `parallel_n64` → no `.rmp`.
- **The label:** N64 `controller_profile` → the layout string; PS1 / SNES labels unchanged.
- **The tool:** `--remap` absent / matches / differs / shadowed.
- **Absent:** a SNES launch's input cfg and command unchanged with the flag on (B59's test); no `.rmp` without the
  flag.
- **Mutations** (each expected caught): the verify skipped; one player's binds dropped; the override ignored; the
  input-cfg lines on every system.
