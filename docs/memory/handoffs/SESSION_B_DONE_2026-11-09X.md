# SESSION B — done, 2026-11-09 X (QUEUE_2026-11-09X: B65, B66, B67, B68 — B68 run on the user's "go m3u"; run 00:35-01:01Z)

- **Baseline:** `9e77af1e` (HOME-8 committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty.
- **Not done:**
  - nothing committed, adopted or installed;
  - no stream, no companion or keeper restart, no adb, no sudo, no nft;
  - no RetroArch run (none needed this queue);
  - nothing fetched, nothing written to the drive, nothing deleted;
  - **B68 not applied** (the library only read).
- **Session A's files appeared in the tree during the run** (`_cowork_prompt.txt` modified,
  `handoffs/H2-P1_GAMECUBE_PROBE_RUN_TASK.md` new). They were **not touched**.

## What was built (four diffs applied to the tree in order, uncommitted)

1. **B65** (`evidence/B65_N64_CONTINUE_LOAD_2026-11-09.md`):
   - **the cause:** T6's first start that never got ready was not the Continue load, which went into a paused core.
     It was 14 s of link loss right after the stream began (1,887 lost packets). The onn's 15-s start gate latched
     "Game stream isn't ready", and the link was clean for the 15 s after;
   - **the fix:** the gate re-arms while frames flow (in B67's APK);
   - **the host guard:** an N64 load only into a core answering `PAUSED` within 1.5 s, else `continue_skipped`;
   - `tests/b65_n64_continue` 7 ×3.
2. **B66** (`evidence/B66_HITCH_HOLD_SPLIT_2026-11-09.md`):
   - UX-R3's hold-resume seconds counted apart; **the bars compare `hitch_s_bar_per_10min`**. C28's 6.6 re-reads as
     bar 3.3;
   - the `launch_ports` row (`--device`, `ports_set` with `capable` / `capped_from`, `layout`);
   - `tests/b66_hitch_split` 6 ×3.
3. **B67** (`evidence/B67_CLIENT_STRINGS_2026-11-09.md`):
   - the N64 layout card (once), "This game supports 2 players", the onn's stored count capped (T1 → 2 at its first
     start), no joined count before the start response (B64), the start gate's re-arm;
   - JVM 240 / 240 (229 / 229 in the APK tree);
   - **APK `5f72af4b65ebf4bf434668f4ef26c52885be02fb8f5400d63e7b4e548bcdca32`**, pinned at
     `PrivyHub/app/build/queue_x_built/app-debug.apk`, built twice to the same bytes; the baseline tree rebuilds
     `9aa00ba2…` byte for byte. **Not installed.**
4. **B68** (`evidence/B68_LIBRARY_M3U_2026-11-09.md`):
   - `tools/library_m3u.py` `plan | apply [--migrate-states] | undo` behind `PRIVYHUB_IMPORT=1`;
   - **on the hub:** 6 sets / 14 discs; **no PrivyHub save states on them**; one in-game memory card to copy;
   - disc swap from the onn: the next APK;
   - `tests/b68_library_m3u` 11 ×3.
5. **Checks:**
   - mutations: 3 + 4 + 4 + 5 caught (B67's M2 and B68's M2 after findings);
   - every host suite in the combined copy reads as the baseline plus the new suites; the same six `tools/` tests
     fail;
   - 16 touched suites green in the tree;
   - the four diffs reverse-apply to the baseline.

**For the next APK (listed, not built):** a "Change disc" entry in the Back menu with a host `disc-swap` action
(RetroArch's `DISK_EJECT_TOGGLE` / `DISK_NEXT`).

**One line for the user:**
- the N64 game that "didn't start" was a 15-second Wi-Fi drop right at the start. The new app keeps waiting while the
  picture is coming;
- the new app also shows the N64 layout once, and says "This game supports 2 players" on your two-player PS1 game;
- the `.m3u` tool is ready: your 6 multi-disc games become one entry each. You have no PrivyHub saves on them; one
  game's in-game memory card would be copied if you say so. Say "apply m3u" when you want it.

## A — HOME-9 (~30 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): the eleven of HOME-7 / HOME-8, plus B67's
`debug.privyhub.start_gate_rearm`.

**Stage 1 (A alone; no game, no movie; outside 04:30-05:30Z):**
1. **Preconditions:**
   - `/tmp` ≥ 1 GB free;
   - **seventeen** `PRIVYHUB_` lines; `e3_state.py --check` ok;
   - `9aa00ba2…` CONFIRMED, read back on the onn;
   - the twelve properties empty; only the two units.
2. **The companion restart:** queue X's host code goes live (B65's guard, B66's row). Seventeen lines read back,
   `--check` ok.
3. **The install:**
   - preserve `9aa00ba2…` (`home9_previous/`);
   - copy `PrivyHub/app/build/queue_x_built/app-debug.apk` to `home9_installed/`;
   - `adb install -r`; read back `5f72af4b…`, paired;
   - **every property empty**;
   - the card's preference is new, so the card will show at the first N64 start.
4. **If the user has said "apply m3u":**
   - `PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py plan` → S1-S6;
   - then `apply --migrate-states` (with their word on the card copy) or plain `apply`;
   - the list then reads "PlayStation (72)" from "(80)";
   - `undo` is the way back.
5. **Pre-register** C29-C33, hashed.
6. **Reply:** "YOU, now: open Games → Nintendo 64 and start any game. Tell me what the first screen shows before you
   press anything, then press any button. Send 'Stage 2'."

**Stage 2 — C29, the N64 layout card:**
- **You should see:** "A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2" (or the names in
  words), gone at the first press.
- **Hub reads:** the start's `game_session.game.system` n64; `launch_ports` (`layout face_c`, `device_args` 1-4).
- **Met:** shown once, dismissed by the press. **Then:** Back, Stop, start an N64 game again, and the card does not
  come back (the user's line).
- **Reply:** "YOU, now: Back and Stop. Start the N64 game from last time that didn't start at first, and choose
  Continue (the saved game). Tell me whether it comes up and plays. Send 'Stage 3'."

**Stage 3 — C30, T6 with its stored state (Continue):**
- **Hub reads:**
  - `continue_load` (`slot`, `status_ms` < 1500, `load_ms`); no `continue_skipped`;
  - `native-stream-ready`, `session_started`;
  - if the link drops at the start: the onn's re-arm (no "Game stream isn't ready" while frames flow) and the ready
    after it.
- **Met:** up and ready (the user's line). A `continue_skipped` row → the fresh start and its reason (a reading → B).
- **Reply:** "YOU, now: Back and Stop. Start the two-player PlayStation game whose player 2 stopped working before.
  Join with controllers 1 and 2, then hold ✕ on a third controller. Tell me what the TV says. Send 'Stage 4'."

**Stage 4 — C31, an incapable PS1 title with a third pad:**
- **Hub reads:**
  - `launch_ports` `ports_set` players 2, `capable` false, `capped_from` 4. This first launch with the new APK still
    sends the onn's stored 3, and B67 lowers the store to 2 at this start's response (its migration), so the next
    launch of this title carries no `capped_from`;
  - no `relaunch_ports` row.
- **You should see:** "**This game supports 2 players**"; players 1 / 2 work.
- **Met:** the line and both players.
- **Reply:** "YOU, now: Back and Stop. Start an N64 game you like and play about 10 minutes with two controllers
  (Home once in the middle is fine). Then tell me how it felt. Send 'Stage 5'."

**Stage 5 — C32, 10 min of N64:**
- **A reads** (no capture): `diag_read` over the sitting, **`hitch_s_bar_per_10min`** (the bar), with
  `hitch_s_per_10min` and `hold_resume_s` beside it and a PS1 session of the evening.
- **Met:** the bar's number ≤ the PS1 session's + 2, no freeze, and the user's line.
- **Reply:** if "apply m3u" was said: "YOU, now: Back and Stop. Open Games → PlayStation and tell me how many games
  it shows and whether each multi-disc game is now one entry. Start one of them and play a moment. Send 'Stage 6'."
  Else "YOU, now: that's all — thank you."

**Stage 6 — C33 (only if B68 was applied):**
- **You should see:** "PlayStation (72)"; one entry per multi-disc set, titled without "(Disc N)"; the game starting
  on disc 1.
- **The S1 title:** its in-game save shows when `--migrate-states` ran.
- **A disc swap from the TV is not possible yet** (listed for the next APK). The cell records that.
- **Hub reads:** `launch_ports` for the `.m3u` entry; RetroArch loading the `.m3u`.
- **Met:** one entry per set and the game plays.
- **Reply:** "YOU, now: that's all — thank you. I'll tidy up on the hub."

**The close and the CONFIRMED rule:**
- every property empty;
- **`5f72af4b…` CONFIRMED** if C29 and C31 are valid and met with every property empty (the client items). The pin
  moves (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test);
- otherwise `9aa00ba2…` goes back on.
- C30 decides B65 (with the re-arm), C32 B66's bar, C33 B68.
- Nothing to adopt: all inside adopted flags or default-on host / client paths.
- The record is `evidence/HOME_9_<date>.md` (no title, serial or path).

**Then H2-P1** (the GameCube probe, B60's design) on the user's go for Dolphin.

## Files

- **Records:** `evidence/B65_N64_CONTINUE_LOAD_2026-11-09.md`, `B66_HITCH_HOLD_SPLIT_2026-11-09.md`,
  `B67_CLIENT_STRINGS_2026-11-09.md`, `B68_LIBRARY_M3U_2026-11-09.md`, with the dirs `b65_2026-11-09/` …
  `b68_2026-11-09/`.
- **Patch notes:** `patches/B65_…`, `B66_…`, `B67_…`, `B68_…`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the queue X section), `docs/ROADMAP.md` (§H1 B65-B67, §H0 B68).
- **Logs:** `logs/b65_git_status.txt` … `logs/b68_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **The APK:** `PrivyHub/app/build/queue_x_built/app-debug.apk` (gitignored).
- **Left (not deleted):** `/tmp/b_q16x_*` (~229 MB); `~/.cache/b_q16x_tmp/` (~51 MB).
