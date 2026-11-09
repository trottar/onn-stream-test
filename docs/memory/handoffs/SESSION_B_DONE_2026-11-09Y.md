# SESSION B — done, 2026-11-09 Y (QUEUE_2026-11-09Y: B69 — the GameCube launch kind; run 02:49-03:30Z)

- **Baseline:** `9db5a35c` (H2-P1 committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty.
- **Not done:**
  - nothing committed, adopted or installed; no drop-in written;
  - no stream, no companion or keeper restart, no adb, no sudo, no nft;
  - **Dolphin not started at all** (H2-P1's `--help` / `--version` were enough); its binary read only as an archive
    (`7z`, nothing run);
  - nothing fetched, nothing written to the drive, nothing deleted (my own scratch excepted, below).

## What was built (one diff applied to the tree, uncommitted)

**B69** (`evidence/B69_GAMECUBE_LAUNCH_KIND_2026-11-09.md`, patch `patches/B69_GAMECUBE_LAUNCH_KIND.md`):
- **behind `PRIVYHUB_GAMECUBE=1`**; absent = today, proved hunk by hunk;
- **the `dolphin` kind** beside `pcsx2`, chosen by the system `gamecube`:
  - the command `-b -u data/games/gamecube/user -e <title>`;
  - **the config written whole per launch**: H2-P1's keys, the FPS overlay and the on-screen messages off, only F10 /
    Shift+F<n> / F<n> bound (slots 1-3, 8, 9);
  - **`GCPadNew.ini`** for the four virtual pads by their evdev names, read from Dolphin's binary and libevdev;
- **the pause:** F10 with the window focused, confirmed by the `CPU thread`'s clock, else SIGSTOP / SIGCONT. The launch
  returns after the window, the shader pre-compile window and the sink-input;
- **states:**
  - SAVE: Shift+F<n> → the file stable within 1 s → the PS1-shaped reply;
  - LOAD: F<n> → B52's picture check;
  - **live:** the hold's return and the stall resume (slot 9), the give-up save / Resume / copy (slot 8);
  - **off:** the rewind and the relaunch;
- four native ports always (hold-to-join to 4, no relaunch); the `gamecube` list in place (`.rvz` first, the `.bin`
  and anything under 1 MiB skipped);
- the exit by SIGTERM, with the AppImage helper waited for (≤ 10 s, then SIGKILL) at the next launch;
- the game log `GC …` lines; `gc_mode`; the `gc_session` row;
- Dolphin's log per launch (with its render / vblank counters); the keeper and `diag_read` (`system: gamecube`,
  `dolphin_log` counts); `tools/gc_frames.py` per 60 ↔ 30 segment with Dolphin's counters beside;
- **checks:**
  - `tests/gamecube_session` 54 ×3 green, no temp dir left;
  - **5 / 5 mutations caught**;
  - every host suite in the B69 copy reads as the baseline copy, plus the new suite; the same six `tools/` tests
    fail in both;
  - 18 touched suites green in the tree; the diff reverse-applies.

**For the next APK (listed, not built):** the "Change disc" entry (B68's); any GameCube string (none needed: the onn
renders the host's nodes).

**One line for the user:** on your controller, ✕ = A, □ = B, ○ = X, △ = Y, R1 = Z, L2 / R2 = L / R (press all the way
for the click), the left stick is the main stick, the right stick the C-stick, and Start and the D-pad are where they
are.

## A — HOME-9+GC, ONE sitting (~50 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): the twelve — HOME-8's eleven plus B67's
`debug.privyhub.start_gate_rearm`.

### Stage 1 — unattended (A alone; no game, no movie; outside 04:30-05:30Z)

1. **Preconditions:**
   - HEAD with queue Y committed, the tree clean; `/tmp` ≥ 1 GB free;
   - **seventeen** `PRIVYHUB_` lines; `e3_state.py --check` ok; `9aa00ba2…` CONFIRMED, read back on the onn;
   - the twelve properties empty; only the two units.
2. **The bench drop-in for the GameCube cells:**
   - `printf '[Service]\nEnvironment=PRIVYHUB_GAMECUBE=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b69-gamecube.conf`,
     then `systemctl --user daemon-reload`;
   - `GAMECUBE_DIR=` is already in the gitignored paths file (H2-P1).
3. **The companion restart** (queues X and Y live: B65's guard, B66's row, B69): `systemctl --user restart
   privyhub-companion`.
   - Seventeen lines plus the bench line (`--check` not ok on the environ only: `PRIVYHUB_GAMECUBE=1`, as IMPORT-1's
     bench flag); the journal clean;
   - the games list reads **"GameCube (27)"** beside "Nintendo 64 (13)".
   - The keeper is not restarted (`diag_read` reads the live logs).
4. **The install:**
   - preserve `9aa00ba2…` (`home9_previous/`);
   - copy `PrivyHub/app/build/queue_x_built/app-debug.apk` to `home9_installed/`;
   - `adb install -r`; read back **`5f72af4b65ebf4bf434668f4ef26c52885be02fb8f5400d63e7b4e548bcdca32`**, paired;
   - **every property empty (twelve)**.
5. **The `.m3u`, applied:** the user's **"apply m3u" is on record (2026-11-09)**, and they said yes to the whole,
   including the card copy.
   - `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py plan` → S1-S6 (6 sets / 14 discs, no PrivyHub save states on them,
     one in-game card);
   - then `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py apply --migrate-states` (the one card copied);
   - the list reads **"PlayStation (72)"** (from "(80)");
   - the way back: `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py undo`.
6. **Pre-register** C29-C36, hashed.
7. **Reply:** "YOU, now: open Games → Nintendo 64 and start any game. Tell me what the first screen shows before you
   press anything, then press any button. Send 'Stage 2'."

### C29-C32 — as queue X wrote them (`SESSION_B_DONE_2026-11-09X.md`)

- **C29, the N64 layout card:** "A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2", gone at
  the first press, not shown again after Back / Stop / start. Hub: `launch_ports` (`layout face_c`, `device_args`
  1-4). Next reply: "YOU, now: Back and Stop. Start the N64 game from last time that didn't start at first, and choose
  Continue (the saved game). Tell me whether it comes up and plays. Send 'Stage 3'."
- **C30, T6 Continue:** `continue_load` (`status_ms` < 1500), no `continue_skipped`; `native-stream-ready`,
  `session_started`; a link drop at the start → the onn's re-arm, with no "Game stream isn't ready" while frames flow.
  Next reply: "YOU, now: Back and Stop. Start the two-player PlayStation game whose player 2 stopped working before.
  Join with controllers 1 and 2, then hold ✕ on a third controller. Tell me what the TV says. Send 'Stage 4'."
- **C31, the incapable PS1 title:** "**This game supports 2 players**"; players 1 / 2 work; `launch_ports`
  `ports_set` players 2, `capable` false, `capped_from` 4 (this first launch only); no `relaunch_ports` row. Next
  reply: "YOU, now: Back and Stop. Start an N64 game you like and play about 10 minutes with two controllers (Home once
  in the middle is fine). Then tell me how it felt. Send 'Stage 5'."
- **C32, 10 min of N64:** `diag_read` over the sitting, **`hitch_s_bar_per_10min`** with `hitch_s_per_10min` and
  `hold_resume_s` beside it and a PS1 session of the evening. Met: the bar ≤ the PS1 session's + 2, no freeze, the
  user's line.
- **Reply:** "YOU, now: Back and Stop. Open Games → PlayStation and tell me how many games it shows and whether each
  multi-disc game is now one entry. Start the one whose save was copied and look for your saved game. Send 'Stage 6'."

### C33 — the `.m3u` check

- **You should see:** "PlayStation (72)"; one entry per multi-disc set, titled without "(Disc N)"; the set starting on
  disc 1; **the migrated card's save showing** in that game's own load screen.
- **Hub reads:** `launch_ports` for the `.m3u` entry; RetroArch loading the `.m3u`.
- A disc swap from the TV is not possible yet (the next APK); the cell records that.
- **Met:** one entry per set, disc 1, the save there (the user's line).
- **Reply:** "YOU, now: Back and Stop. Open Games → GameCube — it should say GameCube (27). Start any game. Count the
  seconds until the game's picture appears and tell me what the TV shows meanwhile. Then hold ✕ on your controller to
  join as player 1, and hold ✕ on a second controller for player 2. Try the sticks, ✕ □ ○ △, the triggers L2 / R2 and
  R1, and tell me which do what. Send 'Stage 7'."

### C34 — the first GameCube title from the onn

- **Hub reads:**
  - the game log `<ts>-gamecube.log`: `GC launch: dolphin ports=4 backend=vulkan adapter=0 config=whole`,
    `GC window: <s>`, **`GC boot: cpu thread <s>`** (the shader pre-compile window on a first boot), `GC audio:
    sink-input <s>`, **`GC pads: P1=evdev/0 P2=evdev/0 P3=evdev/0 P4=evdev/0`** (at the first pause / the
    `gc_session` row);
  - **Dolphin's log** `data/games/gamecube/logs/<stamp>-dolphin.log`: `Added device: evdev/0/PrivyHub Virtual Gamepad
    P1` … `P4` — **the pad names read here, at the first launch**;
  - `launch_ports` (`kind dolphin`, `device_args []`, `ports_set` players 4, `multitap_available` false, `source`
    `join` or `gamecube`); `gc_session` (`gc_states hotkey`, `live` 4, `off [rewind, relaunch]`, `pads`);
    `session_started`; no `relaunch_ports` row.
- **You should see:** the onn's launching screen while the hub compiles shaders (the user's count; H2-P1: the title by
  ~15 s on a first boot, ~9 s after), then the game; P1 and P2 join with no "Setting up 4 players…".
- **The layout:** A = ✕, B = □, X = ○, Y = △, Z = R1, L / R = L2 / R2 (the click at full press), the main stick = the
  left stick, the C-stick = the right stick. The user's line per item.
- **Met:** the game plays, both pads join, the user's layout line matches. **A mapping miss** (a `MISMATCH` in
  `GC pads:`, a dead input or a swapped one) → to B: `PAD_DEVICE` / `PAD_LAYOUT`. It is not fixed at the TV.
- **Reply:** "YOU, now: play to a spot you'll recognise, press Back and choose Save (slot 1). Then Back again and Stop.
  Start the same GameCube game again, press Back, choose Load (slot 1) and tell me whether you're back at that spot.
  Then press Home on the remote, wait about 5 seconds, come back to PrivyHub and tell me if the game carries on. Send
  'Stage 8'."

### C35 — SAVE, Stop, relaunch, LOAD, and the Home hold

- **Hub reads:**
  - SAVE: `GC pause: hotkey`, `GC save: slot 1 hotkey; file stable <s>` (≤ 1.0), the reply `confirmed`;
  - Stop: `GC exit: sigterm <s>s helper=<n>`; the relaunch's log `GC helper: none | gone <s>s` (a `killed` is a
    reading → B);
  - LOAD: **`GC load: slot 1 hotkey; picture ok <s>`**, the reply `confirmed`, `verification picture`;
  - the Home hold: `state_saved` (slot 9, `core dolphin`, `gc_states hotkey`), `input_release` (slot 9,
    `verification picture_after_resume`), then **`gc_states` verdict ok**; no `rewind_failed`.
- **You should see:** the saved spot after the load (the user's line); after Home, the game goes on from where it was
  (or a moment before).
- **Met:** the save file, the picture ok, the user's line, the hold's verdict ok. A `file not stable` or `picture
  static` → B (the paused save / load path is the unmeasured part).
- **Reply:** "YOU, now: play this GameCube game for about 10 minutes with two controllers. Then Back and Stop, and tell
  me how it felt (smooth, any stutter, any input lag). Send 'Stage 9'."

### C36 — 10 min with two pads

- **A reads:**
  - `diag_read` over the sitting: the GameCube session row (`system gamecube`, core `dolphin`),
    **`hitch_s_bar_per_10min`** beside a PS1 session of the evening, and `dolphin_log` (boot, pad_added 4, error,
    warning);
  - after the Stop, Dolphin's counters for that launch: `python3 tools/gc_frames.py --render
    data/games/gamecube/logs/<stamp>-render_times.txt --vblank data/games/gamecube/logs/<stamp>-vblank_times.txt` —
    the per-segment fps (60 / 30) with VIs per second beside. A capture is optional (`gc_frames.py showinfo.txt`).
- **Met:** the bar ≤ the PS1 session's + 2; each segment's median ≥ its rate − 1; no freeze; the user's line.

### The close

- **Every property empty** (twelve).
- **`5f72af4b…` CONFIRMED** if C29 and C31 are valid and met with every property empty. The pin moves:
  `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise `9aa00ba2…`
  goes back on.
- **The verdicts:** C30 → B65 (with the re-arm), C32 → B66's bar, C33 → B68, C34-C36 → B69 (the pad names as read from
  Dolphin's log at the first launch; a mapping miss → the fix, in B's next queue).
- **G-A16:** ask the user "**should GameCube stay on?**".
  - **On their yes:** `PRIVYHUB_GAMECUBE=1` is adopted as **the eighteenth line**. Move `b69-gamecube.conf` to
    `gamecube.conf`; `tools/e1_suite.py` `ADOPTED` gains it; `systemctl --user daemon-reload`, restart; eighteen
    lines; `--check` ok.
  - **Otherwise:** remove `b69-gamecube.conf`, daemon-reload, restart; seventeen lines; `--check` ok.
- **The record:** `evidence/HOME_9_GC_<date>.md` (no title, serial, game id or path).

## Files

- **Record:** `evidence/B69_GAMECUBE_LAUNCH_KIND_2026-11-09.md` with `b69_2026-11-09/`. **Patch note:**
  `patches/B69_GAMECUBE_LAUNCH_KIND.md`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the B69 line and section), `docs/ROADMAP.md` (§H2, B69).
- **Logs:** `logs/b69_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q17y_b69`, `/tmp/b_q17y_base` (~18 MB); `~/.cache/b_q17y_tmp/` (~28 MB: the older suites' own temp dirs from the two host runs; none from
  `tests/gamecube_session`, which removes its own). My scratch
  `/tmp/b69_scratch/` (the binary's strings, the runner scripts) was removed at the end.
