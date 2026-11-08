# HOME-4+: pre-registration (written and hashed before the install, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08Q.md` §A (B's stages, strings, commands, log lines, ini keys and pass rows,
used as B states them), `handoffs/HOME-4_PLUS_CHOOSER_PS2_VOD_TASK.md`, `B50_PS2_FIXES_2026-11-08.md`,
`SESSION_B_DONE_2026-11-07O.md` §A (C7 / C8 / C9 / C10 as first written), `H3_P2_PS2_STREAMED_2026-11-08.md`,
`G_A13_VOD_LOG_ADOPTION_2026-11-07.md` (the adoption form), `CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md` §6.

**The candidate:**
- APK `cfe0211ca36071901a8be3ea9f77855109cd957c3950903669997d6a0b10a65f` (queue O: B46 the player chooser, B47 the
  movie retry default-on, on `8ba4d996…`'s base), from `PrivyHub/app/build/queue_o_built/app-debug.apk` →
  `home4_installed/`, with the same signer as `8ba4d996…` (`455bde4effefd742…`, read before the install).
- **Predecessor (CONFIRMED):** `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f`
  (`home3_installed/`).
- **The eleven properties** (`debug.privyhub.*`), each read back empty at the start and the close:
  - empty throughout: `restart_guard`, `stall_signal`, `link_notice`, `link_report`, `loss_guard`, `wifi_lock`,
    `opus_decode`, `surface_hold`, `pad_slots`;
  - empty except during their own off check: `player_prompt` (`0` for C8's off check only, stage 4b), `vod_retry`
    (`0` for C10's off check only, stage 7).
  - The chooser and the movie retry are on by default in this APK (B46 / B47).
- **The host:** fifteen lines; after the install the two bench drop-ins (B's printf lines, exactly):
  `b49-ps2.conf` (`PRIVYHUB_PS2=1`) and `b47-vod-drop.conf` (`PRIVYHUB_VOD_DROP_TEST=1`), `daemon-reload`, restart;
  **seventeen** `PRIVYHUB_` lines read back; queue O's, B49's and B50's host code live. At the close
  `b47-vod-drop.conf` removed; `b49-ps2.conf` replaced by `ps2.conf` under G-A14, or removed.
- **The drive:** read-only; its two folders' listings and mtimes before = after (stage 1, stage 6, the close).
- **The hub's memory cards before:** `Mcd001.ps2` / `Mcd002.ps2` both
  `47ebe237a3987f843fc19b0f801ce1edc1690768ef6b18e4b03a12ca6b298358` (all `0xFF`; `ps2_memcard.check`
  `formatted: False`).

## The cells and their pass rows (B §A stages 2-7)

**C7, the chooser at a start and an unpause** (stage 2; a two-player PS1 title, multitap off; queue O's strings):
- You should see, at the start: bottom-centre `Players:  1  /  [2]  /  multitap (3-4)`.
  1. Pad A presses X: `Player 1 — press any button` (the pick claims nothing).
  2. Pad B presses X: `P1` for 2 s, then `Player 2 — press any button`.
  3. Pad A presses X: `P2`, and the line goes.
  4. Back on the remote, then the title's Resume: the chooser again with `[2]`. Pick, then claim P1 and P2 again.
- **Pass:**
  - the game is never paused by the chooser;
  - a `"event": "pad_slots"` `change` row after each pick, with `players_chosen` 2 and both slots `claimed_by:
    prompt`, `label` `P1` / `P2`; the heartbeats carry `players_chosen` 2;
  - each exit's report: `players_chosen` 2, `pad_claims`, `ports_set` (`players` 2, `source` `metadata`).

**C9, the held-Start release** (stage 3; the same title, both pads claimed):
- Do: pad B presses Select, then Start, and holds both 2 s. You should see `P1 released`, then `Player 1 — press any
  button`. Keep Start held 3 s more, let go, then press Start again: `P1`.
- **Pass:** no `change` row with slot 0 `prompt` while Start was held; one after the fresh press.

**C8, multitap** (stage 4; a PS1 title that supports four players):
- Do: (1) at the chooser, right twice → `[multitap (3-4)]`, pick. The line reads `Player 1 — press any button` and
  `Multitap from the next start` (unless the title's metadata already has the multitap on). (2) Stop the game, then
  launch it again. The chooser shows `[multitap (3-4)]`; pick; pad B → P1, pad A → P2. P3 / P4 stay open.
- **Pass (hub reads: these lines only, never a path or title):**
  - the game log's `PS1 multitap: port1`;
  - the Beetle `.opt` key `beetle_psx_hw_enable_multitap_port1 = "enabled"`;
  - RetroArch's `--device=1:<d>` … `--device=4:<d>`;
  - `ports_set` `players` 4, `multitap` true, `source` `launch`.
- **Off check (stage 4b):** `setprop debug.privyhub.player_prompt 0`, read back → the user relaunches once → no
  chooser on screen, and no `players_chosen` / `ports_set` / `pad_claims` in that session's rows or report; today's
  slots (`8ba4d996…`'s stable slots); then `setprop debug.privyhub.player_prompt ""`, read back empty.

**C11, a two-player PS2 title** (stage 5; the user's pick from the list; a PS2 title is a `T`-label in the record):
- You should see: the game's first picture within ~a few seconds (H3-P2: 2.5-2.7 s); the chooser
  `Players:  1  /  [2]  /  multitap (3-4)`; after the pick, `Player 1 — press any button` → pad B → `P1`, pad A →
  `P2`. Then both players in the game (a two-player mode): pad 1 drives player 1, pad 2 drives player 2. Watch for
  tearing.
- **Pass:**
  - **the user's line:** both pads drive their players; any tearing;
  - **the PS2 game log:** `PS2 launch: pcsx2 players=2 multitap=false adapter=named`, `PS2 memcards:
    Mcd001.ps2=formatted Mcd002.ps2=formatted` (the first launch after B50), `PS2 audio: sink-input <s>s`,
    `PS2 pause: hotkey`;
  - **PCSX2's own log** (`data/games/ps2/config/PCSX2/logs/emulog.txt`, read in place): no `Invalid binding:` line;
    four `Opened gamepad` lines for `PrivyHub Virtual Gamepad`; `McdSlot 0 [File]: Mcd001.ps2 [8 MB, Formatted]`;
  - **the hub's ini:** `[Pad] MultitapPort1 = false`, `[Pad2] Cross = SDL-1/FaceSouth`, `[EmuCore/GS] VsyncEnable =
    true`;
  - **the rows:** `ports_set` `players` 2, `multitap` false; a `pad_slots` `change` row with `players_chosen` 2; the
    `ps2_session` row; `ps2_mode` on the heartbeats.

**C12, a PS2 save on the hub's card** (stage 6):
- Do: the user saves (the game confirms). Then Back, Stop, launch the same title again, and load the save. You should
  see the save in the game's load list, and the game continue from it.
- **Pass:**
  - `Mcd001.ps2`'s sha256 differs from the post-format value, and `ps2_memcard.check` still reads it `formatted`
    (`python3 -c "import sys; sys.path.insert(0,'companion'); import ps2_memcard as m; print(m.check(open('data/games/ps2/memcards/Mcd001.ps2','rb').read())['formatted'])"`);
  - the relaunch carries `players_chosen=2`: the PS2 log `players=2 multitap=false`, the launch's `players_session`;
  - the drive's folders unchanged (listing + mtimes);
  - the user's line.
  - "The post-format value" is `Mcd001.ps2`'s sha256 read after C11's first launch formatted it (before the save).

**C10, the movie with no property** (stage 7; `vod_retry` empty, read; queue O's C10):
- **(a) The drop:** `echo "drop 45" >> runtime/vod_drop_test.trigger` (from the repo root), the movie playing ≥ 1 min,
  nothing pressed. You should see "reconnecting…" in the corner, then the movie continue at the same place, **with
  "reconnecting…" gone**.
  - **Pass:** `vod_drop_injected` `dropped: 1`; `vod_error` (`reset`) → `vod_retry` × n → `vod_resumed`; no "Playback
    error"; the user's line (the mark gone). **Invalid** if `dropped: 0`: run again with `drop 60`.
- **(b) The restart:** with the movie playing ≥ 1 min more, `systemctl --user restart privyhub-companion`. You should
  see the movie pause briefly and resume by itself.
  - **Pass:** a `vod_range.jsonl` row with `closed: "shutdown"`; `401` → `token_refetched: true` → `vod_resumed`.
- **Off check:** `setprop debug.privyhub.vod_retry 0`, read back → one more `drop 45` → today's "Playback error" (the
  user told what to expect); then `setprop debug.privyhub.vod_retry ""`, read back empty.

## Validity

A cell is **valid** when all of these hold:
- its precondition held: the properties read back as stated (only its own off-check property set, the others empty),
  seventeen `PRIVYHUB_` lines live;
- the user's action happened as described (C7: a start and an unpause, the picks and claims; C9: Select then Start
  held, the fresh press; C8: the multitap pick, the stop and relaunch, and for the off check one relaunch; C11: a
  two-player PS2 title, both players in a two-player mode; C12: the game's own save confirmed, Stop, relaunch, load;
  C10 (a): the movie in front ≥ 1 min, then the drop with nothing pressed; (b): the movie in front ≥ 1 min, then the
  restart, Retry not pressed);
- the band was 5 GHz;
- the rows it names were written, or their absence is itself the reading.

A cell the user could not do, or whose action left the app, is **invalid**, not failed. C10 (a) with `dropped: 0` is
invalid (re-run once with `drop 60`). The user's lines are the gate on anything on screen.

## The CONFIRMED rule (CL-B7 §6)

- **CONFIRMED:** every cell that ran is valid, and **today's behaviours hold wherever a property was `0` / `off`
  (B42 / B46 / B47's intended defaults aside)**. Then `cfe0211c…a65f` is CONFIRMED and the pin moves in three places:
  `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test; the tests green;
  the patch note indexed.
- **Otherwise:** `8ba4d996…` is reinstalled from `home3_installed/`, read back and paired, and the user is told why.
- "Today's behaviours (B42 / B46 / B47's defaults aside)" means:
  - with `player_prompt` empty: the chooser (B46's intended default, the reading of C7 / C9 / C8); with `0`: no
    chooser and no `players_chosen` / `ports_set` / `pad_claims`, today's slots;
  - with `vod_retry` empty: the retry (B47's intended default, the reading of C10 (a) / (b)); with `0`: today's
    "Playback error";
  - with `surface_hold` / `pad_slots` empty: the hold and stable slots (B42's, G-A11 / G-A12);
  - the other seven defaults unchanged;
  - the adopted line count, `--check` ok and `flags_absent` at the close; `privyhub-diag` active.
- **C11 / C12 are PS2 cells: they bear on B50 and on G-A14, not on the APK rule.** A cell valid but not met bears on
  its question, not on the rule.

## G-A14's condition

- **If C11 and C12 are both met:** `PRIVYHUB_PS2=1` is adopted as the **sixteenth** line (the user's "Yes",
  2026-11-08), in G-A13's applied form: `PS2` in `ADOPTED`, `drop_in_ps2` required in `ok`, the wording files,
  `patches/G-A14_PS2_ADOPTION.md` checked and applied, `git diff --check` clean, `e1_suite --self-test`,
  `test_e1_remote`, `test_c3_l4_nft_night`, `tests/ps2_session` green; `ps2.conf` written, `b49-ps2.conf` removed,
  `daemon-reload`, restart; sixteen lines read back; `--check` ok on sixteen; `flags_absent`; the off switch stated.
- **Else:** `b49-ps2.conf` removed, fifteen lines, `--check` ok, and the user told which of C11 / C12 was not met
  (PS2 stays bench-only until B fixes it).
- PS2 save states through PINE: the user's yes, **later** (after the import work) — open in the record, not built, not
  asked again.

Nothing else adopted; nothing committed.
