# HOME-9+GC: pre-registration (written and hashed before Stage 2, 2026-11-09)

Sources: `handoffs/SESSION_B_DONE_2026-11-09Y.md` §A (stage 1, C29-C36, the hub reads, the "You should see" lines and
the replies — used exactly), `handoffs/SESSION_B_DONE_2026-11-09X.md` §A (C29-C32 as first written),
`handoffs/HOME-9_GC_TASK.md`, `B65_…` … `B69_…`, `H2_P1_GAMECUBE_PROBE_2026-11-09.md` (its two titles, called P1-T1 /
P1-T2 here), `G_A13_VOD_LOG_ADOPTION_2026-11-07.md` (the adoption form).

**The state at hashing:** seventeen adopted lines plus the bench line `PRIVYHUB_GAMECUBE=1` (`b69-gamecube.conf`;
`--check` not ok on the environ only, named); queues X and Y live from the stage-1 restart (05:41:02Z); APK
`5f72af4b65ebf4bf434668f4ef26c52885be02fb8f5400d63e7b4e548bcdca32` installed on the onn, read back, paired (the signer
the same as `9aa00ba2…`, which is preserved in `home9_previous/`); **the twelve properties empty** (HOME-8's eleven +
`debug.privyhub.start_gate_rearm`), no `setprop` at any point; the `.m3u` applied with `--migrate-states` (6 written,
1 card copied; "PlayStation (72)" from "(80)"; the way back `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py undo`);
"GameCube (27)" beside "Nintendo 64 (13)".

T-labels: T1 = the two-player PS1 title (HOME-7 C15 / C17, HOME-8 C26); T6 = the N64 title of HOME-7 C23 / HOME-8 C24;
T9 = the N64 title the user starts in C29; T10 = the N64 title of C32; T11 = the `.m3u` set whose card was copied (S1);
T12 = the GameCube title of C34-C36. No title, serial, game id or path is written.

## The cells (B's rows)

**C29 — the N64 layout card (B67).** You should see: "A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ =
C-right), Z = L2" (or the names in words), gone at the first press; not shown again after Back / Stop / start. Hub
reads: `game_session.game.system` n64; `launch_ports` (`layout face_c`, `device_args` 1-4). **Met:** shown once,
dismissed by the press, not back on the next start (the user's line). **Decides** B67's card (client item → the
CONFIRMED rule).

**C30 — T6 with its stored state (Continue) (B65).** Hub reads: `continue_load` (`slot`, `status_ms` < 1500,
`load_ms`); no `continue_skipped`; `native-stream-ready`, `session_started`; if the link drops at the start, the onn's
re-arm (no "Game stream isn't ready" while frames flow) and the ready after it. **Met:** up and ready (the user's
line). A `continue_skipped` row → the fresh start and its reason (a reading → B). **Decides B65** (with the re-arm).

**C31 — T1, an incapable PS1 title, with a third pad (B66 / B67).** Hub reads: `launch_ports` `ports_set` players 2,
`capable` false, `capped_from` 4 (this first launch with the new APK; B67 lowers the onn's store to 2 at this start's
response); no `relaunch_ports` row. You should see "**This game supports 2 players**"; players 1 / 2 work. **Met:** the
line and both players. **Decides** B67's string and the store cap (client item → the CONFIRMED rule).

**C32 — 10 min of N64 (B66).** `diag_read` over the sitting: **`hitch_s_bar_per_10min`** with `hitch_s_per_10min` and
`hold_resume_s` beside it, and a PS1 session of the evening (C31's T1). **Met:** the bar ≤ the PS1 session's + 2, no
freeze, the user's line. **Decides B66's bar.**

**C33 — the `.m3u` check (B68).** You should see "PlayStation (72)"; one entry per multi-disc set, titled without
"(Disc N)"; the set starting on disc 1; the migrated card's save showing in T11's own load screen. Hub reads:
`launch_ports` for the `.m3u` entry; RetroArch loading the `.m3u`. The disc swap from the TV is not possible yet (the
next APK); the cell records that. **Met:** one entry per set, disc 1, the save there (the user's line). **Decides B68.**

**C34 — T12, the first GameCube title from the onn (B69).** Hub reads: the game log `GC launch: dolphin ports=4
backend=vulkan adapter=0 config=whole`, `GC window: <s>`, `GC boot: cpu thread <s>`, `GC audio: sink-input <s>`,
`GC pads: P1=evdev/0 … P4=evdev/0`; **Dolphin's log `Added device: evdev/<n>/PrivyHub Virtual Gamepad P1 … P4`, read at
this first launch**; `launch_ports` (`kind dolphin`, `device_args []`, `ports_set` players 4, `multitap_available`
false, `source` `join` or `gamecube`); `gc_session` (`gc_states hotkey`, `live` 4, `off [rewind, relaunch]`, `pads`);
`session_started`; no `relaunch_ports`. You should see the onn's launching screen while shaders compile (the user's
count; H2-P1: the picture by ~15 s first boot, ~9 s after), then the game; P1 and P2 join with no "Setting up 4
players…". The layout, the user's line per item: ✕ = A, □ = B, ○ = X, △ = Y, R1 = Z, L2 / R2 = L / R (the click at
full press), left stick = main, right stick = C. **Met:** the game plays, both pads join, the layout line matches. A
mapping miss (`MISMATCH` in `GC pads:`, a dead or swapped input) → B (`PAD_DEVICE` / `PAD_LAYOUT`), not fixed at the TV.
**Decides B69's launch, pads and layout.**

**C35 — SAVE, Stop, relaunch, LOAD, the Home hold (B69).** Hub reads: SAVE `GC pause: hotkey`, `GC save: slot 1 hotkey;
file stable <s>` (≤ 1.0), the reply `confirmed`; Stop `GC exit: sigterm <s>s helper=<n>`; the relaunch's `GC helper:
none | gone <s>s` (a `killed` is a reading → B); LOAD **`GC load: slot 1 hotkey; picture ok <s>`**, `confirmed`,
`verification picture`; the Home hold `state_saved` (slot 9, `core dolphin`, `gc_states hotkey`), `input_release`
(slot 9, `verification picture_after_resume`), **`gc_states` verdict ok**; no `rewind_failed`. You should see the saved
spot after the load; after Home the game goes on. **Met:** the save file, the picture ok, the user's lines, the hold's
verdict ok. A `file not stable` or `picture static` → B. **Decides B69's states.**

**C36 — 10 min of GameCube with two pads (B69).** `diag_read` over the sitting: the GameCube session row (`system
gamecube`, core `dolphin`), **`hitch_s_bar_per_10min`** beside a PS1 session of the evening, `dolphin_log` (boot,
pad_added 4, error, warning); after the Stop `tools/gc_frames.py --render … --vblank …` per 60 / 30 segment with VIs
per second beside. **Met:** the bar ≤ the PS1 session's + 2; each segment's median ≥ its rate − 1; no freeze; the
user's line. **Decides B69's streamed play** (H2's P0d / P7 read here).

## Validity

The twelve properties empty throughout (read at the close); the seventeen lines + the bench line unchanged; the user's
actions as described; the user's lines are the gate on anything on screen; a row's absence is itself the reading; a
step the user could not do, or that left the app, is invalid, not failed. No capture unless noted.

## The rules

- **The CONFIRMED rule (CL-B7 §6) for `5f72af4b…`:** C29 and C31 valid and met with every property empty → CONFIRMED,
  the pin moved (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; tests
  green; the patch note indexed). Otherwise `9aa00ba2…` reinstalled from `home9_previous/`, read back, paired, the user
  told why.
- **G-A16's gate is the user's word** at the close ("should GameCube stay on?", the answer verbatim). On "yes":
  `PRIVYHUB_GAMECUBE=1` the eighteenth line in G-A13's applied form (`GAMECUBE` in `ADOPTED` with the comment
  `G-A16 (adopted 2026-11-09, the user)`, `drop_in_gamecube` required in `ok`, the wording files,
  `patches/G-A16_GAMECUBE_ADOPTION.md` checked and applied, `git diff --check` clean, the four suites +
  `tests/gamecube_session` green, `gamecube.conf` written and `b69-gamecube.conf` removed, daemon-reload, restart,
  eighteen lines, `--check` ok on eighteen, `flags_absent`, the off switch stated). On "no" or no answer:
  `b69-gamecube.conf` removed, seventeen lines, `--check` ok.
- Nothing else adopted; a not-met goes to B. Nothing committed.
