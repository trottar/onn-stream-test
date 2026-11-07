# SESSION B — done, 2026-11-07 O (QUEUE_2026-11-07O: B46, B47, B48; run 18:07-18:50Z; baseline ea40a93f, the tree clean. Precondition met: `evidence/G_A13_VOD_LOG_ADOPTION_2026-11-07.md` present (fifteen lines). Only the companion + `privyhub-diag` active, checked first. Nothing committed, nothing adopted, nothing installed, nothing fetched, nothing deleted, no stream, no companion restart, no adb, no sudo, no nft; `privyhub-diag` and `~/privyhub_diag/` untouched)

**The user's decisions this queue rests on:**
- "Reconnect by default yes";
- "Player one press any button by default also";
- "I want every game to have that 1 player, 2 player, and multitap";
- HOME-3 C6: "It should pop up every time a game is active or unpaused … to assure consistency and reliability each play
  session";
- PS2 setup first, before user-content import;
- the PS2 BIOS and games go on the external drive the movies are on;
- N64 stays RetroArch.

**How it ran.** B46 and B47 were each built in their own `/tmp/b_q07o_<item>` copy, each design hashed before its
code. B48 is a document only. The two diffs merged with no conflict
(`evidence/queue_o_2026-11-07/queue_o_combined.diff`) and were applied to the tree, uncommitted.
- **Host:** every `tests/` suite matches the baseline copy, plus 1 new suite (`players_session`, 13); `vod_log` 12 → 16;
  `vod_drop_test` 21 with one assertion moved (disclosed). Six `tools/` tests fail in a copy, identically in the
  baseline copy (queue N counted four).
- **JVM:** 228 / 228 integrated (219 + 5 + 4).

1. **B46 SETTLED + BUILT — the player chooser** (`debug.privyhub.player_prompt`: absent = on, `0` / `off` = none).
   - **Settled:** the ports can be set per session **at launch** without touching the metadata. Mid-session they cannot
     be changed: no RetroArch network command sets a core option or a port device. "Unpause" = Resume's new stream
     start (`native-stream-start` + `ready`).
   - **What it does:**
     - at every start and every unpause (not at a self-restart or a hold return) the slot map is cleared and
       `Players:  1  /  [2]  /  multitap (3-4)` shows bottom-centre;
     - the default is the title's last pick, else 2, or 1 for a `single` title;
     - then `Player N — press any button` up to the pick, capped by the session's ports, with a note when the pick
       needs the next start;
     - a claim needs a fresh press (C6's held-Start fixed); a pad beyond the pick gets no slot.
   - **The host:**
     - `players_chosen` on the launch → the PS1 port-1 multitap `.opt`, the `--device` ports, SNES's port-2 multitap
       (257, recalled);
     - `ports_set` in the start response;
     - `players_chosen` / `label` on the `pad_slots` rows;
     - a stale-file guard.
   - **One line for the user, what "multitap" means today:**
     - **PS1:** four pads on port 1;
     - **SNES:** the multitap device on port 2 (players 2-4 through it), set at launch, never run on this hub;
     - **NES / Genesis:** none (2 players).
   - Record: `evidence/B46_PLAYER_CHOOSER_2026-11-07.md`.
2. **B47 BUILT — the movie retry on by default** (`debug.privyhub.vod_retry`: absent = on, `0` / `off` = today).
   - "reconnecting…" is cleared at every READY: any scheduled attempt is dropped and every tagged mark swept. The
     leftover mark's cause was **not found**; the fix makes the clear unconditional.
   - A range request open at a companion restart gets a `closed: "shutdown"` row: a SIGTERM handler inside the adopted
     `PRIVYHUB_VOD_LOG=1` block.
   - Record: `evidence/B47_VOD_RETRY_DEFAULT_ON_2026-11-07.md`.
3. **B48 WRITTEN — the PS2 probe design:** `architecture/H3_P1_PS2_PROBE_DESIGN_2026-11-07.md`, no code, nothing
   fetched.
   - **The emulator:** standalone PCSX2, the maintained upstream with its hardware renderers.
   - **What carries over:**
     - the capture (x11grab by PID) is emulator-agnostic;
     - the audio is a per-app sink by PID;
     - the input is the same four uinput pads, so no bridge, only an SDL mapping.
   - **What needs code (B49):** the launch, pause / exit (no network commands: PINE status plus a hotkey or
     SIGSTOP), the multitap at launch, the keep-awake.
   - **The files:** BIOS and games at the user's folders on the movies drive (placeholders), saves on the hub disk; the
     G0 boundary deferred by the user's decision, written into ROADMAP §H3.
   - **The metrics and the A run:** M1-M7 and pass rows P0-P7 pre-registered for A.
4. **The APK (B5 … B25 + B32 + B34 + B35 + B38 + B39 + B41 + B42 + B43 + B46 + B47; B27 / B29 out)
   `cfe0211ca36071901a8be3ea9f77855109cd957c3950903669997d6a0b10a65f`**, 9,699,504 B.
   - **How it was built:** the tree with queue O applied, then `b29.diff` and `b27.diff` reversed. Its client sources
     minus queue O are byte-equal to `8ba4d996…`'s build copy. Offline, `--rerun-tasks --no-configuration-cache`; JVM
     217 / 217.
   - **Checks:** a rebuild gives the same bytes; `apksigner verify` OK; the same signer as `8ba4d996…`; 945 entries, with
     `classes3/5/6.dex` differing.
   - **Pinned, NOT installed** (`PrivyHub/app/build/queue_o_built/app-debug.apk`). `8ba4d996…` stays CONFIRMED. Files:
     `evidence/queue_o_2026-11-07/`.
5. **Live at the next companion restart** (queue O's host code; inert without the client's keys):
   - `players_chosen` on a launch sets that session's ports;
   - `ports_set` goes to a prompt client;
   - the `shutdown` range row (the fifteenth line is set).

## A — HOME-4 (the user at the TV; restarts outside 04:30-05:30Z, no game and no movie running)

**The properties** (all eleven, each read back empty at the start and the close): `restart_guard`, `stall_signal`,
`link_notice`, `link_report`, `loss_guard`, `wifi_lock`, `opus_decode`, `surface_hold`, `pad_slots`, `vod_retry`,
`player_prompt` (all `debug.privyhub.*`).

1. **Setup:**
   - pre-register the rows below, hashed, before the install;
   - `e3_state.py --check` ok on fifteen; `8ba4d996…` CONFIRMED read back;
   - preserve `8ba4d996…` (`home3_installed/`);
   - copy `PrivyHub/app/build/queue_o_built/app-debug.apk` to `PrivyHub/app/build/home4_installed/`, `adb install -r`,
     and read back `cfe0211ca36071901a8be3ea9f77855109cd957c3950903669997d6a0b10a65f`, paired;
   - **every property empty**: the chooser and the movie retry are now on by default;
   - **the companion restart**, so queue O's host code is live.
2. **C7, the chooser at a start and at an unpause** (two pads; a 2-player PS1 title, multitap off in its metadata;
   LAN).
   - **Do, and what the screen must show:**
     1. Launch the title. Bottom-centre: `Players:  1  /  [2]  /  multitap (3-4)` (the title's first launch since this
        APK, so 2).
     2. Pad A presses X → `Player 1 — press any button`. That pick press claims nothing.
     3. Pad B presses X → `P1` for 2 s, then `Player 2 — press any button`.
     4. Pad A presses X → `P2`, and the line goes.
     5. Back on the remote (the paused frame), then the title's Resume. The chooser shows again with `[2]`.
     6. Pick with pad A, then pad A → P1 and pad B → P2 (any order works; record which).
   - **Pass:**
     - the game runs throughout (never paused by the chooser);
     - the `"event": "pad_slots"` rows: after each pick, a `change` row with `players_chosen` 2 and both slots
       `claimed_by: prompt` with `label` `P1` / `P2`; the heartbeat rows carry `players_chosen` 2;
     - each exit's report: `players_chosen` 2, `pad_claims` `[{0, prompt}, {1, prompt}]`, `ports_set` (`players` 2,
       `source` `metadata` for the first launch);
     - after the unpause's pick, a new `change` row with `players_chosen` 2 and the claims. The unpause's own `start`
       row still shows the old map: the start query is sent before the response opens the chooser and clears it.
   - **Off check:** `adb shell setprop debug.privyhub.player_prompt 0` → no chooser, no `players_chosen` / `ports_set`
     / `pad_claims`, today's slots. Then `adb shell setprop debug.privyhub.player_prompt ""`.
3. **C8, multitap → four claims** (two pads; a PS1 title that supports four players).
   - **Do:**
     1. Launch. At the chooser, right twice → `[multitap (3-4)]`, then pick. The line reads `Player 1 — press any
        button` and `Multitap from the next start` (this launch had no pick for the title). If the title's metadata
        already has the multitap on, there is no note and claims go up to 4; step 2's relaunch then reads back
        `source: launch`.
     2. Stop the game from the onn's games screen, then launch it again. This launch carries `players_chosen=4`.
     3. The chooser shows `[multitap (3-4)]`; pick. Pad B → P1, pad A → P2. With no third pad, the line is gone and P3 /
        P4 stay open.
   - **Pass:**
     - the second launch's host readback (copy **only** these, never a path or title):
       - the game log's `PS1 multitap: port1` line;
       - the content's Beetle `.opt` with `beetle_psx_hw_enable_multitap_port1 = "enabled"` (grep that key alone);
       - RetroArch's command line `--device=1:<d>` … `--device=4:<d>` (from `/proc/<pid>/cmdline`, the `--device`
         arguments only);
       - RetroArch's log line for the port devices;
     - the second start's `ports_set`: `players` 4, `multitap` true, `source` `launch`;
     - the report's `players_chosen` 4 and `pad_claims` for slots 0 and 1.
   - **Then:** pick `2` at the next start and relaunch. The game log's `PS1 multitap: off`, the `.opt` key `disabled`;
     the metadata (`controller_overrides.json`'s entry for the title) unchanged before = after (compare the hash of
     that one entry).
4. **C9, the held-Start release** (C7's title, both pads claimed).
   - **Do:** pad B presses Select, then Start, and holds both 2 s → `P1 released`, then `Player 1 — press any button`.
     Keep Start held 3 s more, then release Start, then press Start again.
   - **Pass:**
     - no claim while Start is held: no `change` row with slot 0 `prompt` until the fresh press;
     - after the fresh press, slot 0 `prompt` for pad B, `P1` shown.
5. **C10, the movie with no property** (`vod_retry` empty).
   - **Setup:**
     ```
     printf '[Service]\nEnvironment=PRIVYHUB_VOD_DROP_TEST=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b47-vod-drop.conf
     systemctl --user daemon-reload && systemctl --user restart privyhub-companion
     ```
     The fifteenth line already sets the log.
   - **(a) The 45-s drop:** the movie in front, nothing pressed, playing ≥ 1 min, then
     `cd ~/Projects/onn-stream-test && mkdir -p runtime && echo "drop 45" >> runtime/vod_drop_test.trigger`.
     - **Pass:**
       - `vod_drop_injected` `dropped: 1`, then `vod_refuse_ended`;
       - `vod_client.jsonl` `vod_error` (`reset`) → `vod_retry` × n → `vod_resumed`;
       - the movie at the position, no "Playback error";
       - **"reconnecting…" gone at the resume** (the user's line).
     - **Invalid if:** `dropped: 0`, or no `vod_error` by the window's end (run again with `drop 60`).
   - **(b) The range row:** with the movie still playing ≥ 1 min after (a)'s resume, `systemctl --user restart
     privyhub-companion`.
     - **Pass:**
       - `vod_range.jsonl` has a row for the request open at the restart, with `closed: "shutdown"`, 206, its range and
         its bytes so far (the `bytes=<P>-` request (a) resumed with, if it was still open);
       - the movie resumes by itself (B43: `401` → `token_refetched: true` → `vod_resumed`).
   - **Off check:** `adb shell setprop debug.privyhub.vod_retry 0` → a drop shows today's "Playback error" at once, with
     no `vod_*` client rows. Then `adb shell setprop debug.privyhub.vod_retry ""`.
   - **Close:** after the user stops the movie:
     ```
     rm ~/.config/systemd/user/privyhub-companion.service.d/b47-vod-drop.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion
     ```
6. **The close and the CONFIRMED rule (CL-B7 §6):**
   - **The close:** every property empty; the drop-in removed; fifteen lines; `e3_state.py --check` ok; `flags_absent`.
   - **The rule:** if every cell that ran is valid and today's behaviours hold wherever a property was `0` / `off`
     (B42 / B46 / B47's intended defaults aside), **`cfe0211c…a65f` is CONFIRMED** and the pin moves:
     `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise
     `8ba4d996…` goes back on.
7. **The user's questions:**
   - a relaunch at the start when the pick changes the multitap (not built), or keep "from the next start";
   - a 1-player title now shows the chooser with 1 highlighted ("every game"): keep it, or skip the chooser for
     `single` titles.

## A — then H3-P1, the PS2 probe (`architecture/H3_P1_PS2_PROBE_DESIGN_2026-11-07.md` §5)

1. **YOU, now:** put the PS2 BIOS into a folder on the movies drive, and one or two PS2 games into another (the design
   calls them `<MOVIES_DRIVE>/PrivyHub/ps2/bios/` and `<MOVIES_DRIVE>/PrivyHub/ps2/games/`). Tell A the two folders.
2. **YOU, now:** say whether A may fetch PCSX2 (the official Linux AppImage, current stable) into
   `runtime/emulators/pcsx2/`, or download it yourself and put it there. **Nothing is fetched without this go.**
3. **A, unattended:**
   - write the ini under `data/games/ps2/config/`, then hash the pass rows;
   - start T1 from a shell on the hub's display;
   - read P0a-P0c, then P1-P5 at the menu (with a 10-min idle for the drive's spin-up).
4. **YOU, now (~15 min):** two pads plugged into the hub, the hub's screen; play T1 for 10 min, then send one line on
   how it felt (P6).
5. **The stream over PCSX2 (P7) is B49.** The launch, pause and keep-awake need code. The record is
   `evidence/H3_P1_PS2_PROBE_<date>.md`, with titles as `T1` / `T2` only.

## Files
- **Records:** `evidence/B46_PLAYER_CHOOSER_2026-11-07.md`, `evidence/B47_VOD_RETRY_DEFAULT_ON_2026-11-07.md`.
- **Document:** `architecture/H3_P1_PS2_PROBE_DESIGN_2026-11-07.md`.
- **Dirs:** `b46_2026-11-07/`, `b47_2026-11-07/`; the integration `evidence/queue_o_2026-11-07/`.
- **Patch files:** `patches/B46_PLAYER_CHOOSER.md`, `patches/B47_VOD_RETRY_DEFAULT_ON.md`. `PATCH_INDEX.md` has no
  rows for them yet, as for queue N's three.
- **Logs:** `logs/b46_` / `b47_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (a section), `docs/ROADMAP.md` (§H3's pointer and the deferral; a
  queue-O line under G's HOME-3 items).
- **Left in /tmp:**
  - `b_q07o_base`, `b_q07o_b46`, `b_q07o_b47`, `b_q07o_all`, `b_q07o_apk`;
  - `b_q07o_scratch/` (the scripts, the mutation copies, the APK copy);
  - the gradle consoles `b_q07o_b46_jvm*.txt`, `b_q07o_b47_jvm1.txt`.
