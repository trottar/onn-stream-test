# HOME-3: pre-registration (written and hashed before the install, 2026-11-06)

Sources: `handoffs/SESSION_B_DONE_2026-11-06N.md` §A items 1-8 (B's rows, used as B states them),
`handoffs/HOME-3_DEFAULTS_PROMPT_VOD_TASK.md`, `B41_…`, `B42_…`, `B43_…`, `HOME_2_HOLD_PADS_VOD_2026-11-03.md`
(C1' / C4' met, C5' not met), `CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md` §6.

**The candidate:**
- APK `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f` (queue N: B5 … B25 + B32 + B34 + B35 + B38 +
  B39 + B41 + B42 + B43; B27 / B29 out), from `PrivyHub/app/build/queue_n_built/app-debug.apk` → `home3_installed/`,
  with the same signer as `0132b944…`.
- **Predecessor (CONFIRMED):** `0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f` (`home2_installed/`).
- **The eleven properties:**
  - the seven, empty throughout: `restart_guard`, `stall_signal`, `link_notice`, `link_report`, `loss_guard`,
    `wifi_lock`, `opus_decode`;
  - the four, empty except during their own step: `surface_hold` (`0` for C1'''s off check only), `pad_slots` (`off`
    for C4'''s off check only), `player_prompt` (`1` for C6), `vod_retry` (`1` for C5'').
- **The host:** fourteen lines throughout; the companion restarted after the install (queue N's host code live, inert
  without `player_prompt=1` in a start query and without `PRIVYHUB_VOD_DROP_TEST=1`); for C5'' only, the drop-in
  `b43-vod-drop.conf` (`PRIVYHUB_VOD_LOG=1`, `PRIVYHUB_VOD_DROP_TEST=1`), removed at the close.

## The cells and their pass rows (B items 2-5)

**C1'', the hold with no property** (LAN; `getprop debug.privyhub.surface_hold` empty, read; a game running; the
remote's Home, back within 3 s; play ~30 s; exit with Back):
- a recovery row `"event": "surface_lost"`, `"outcome": "held"`, `away_ms` < 12000;
- no `restart_fast` and no `session_ended` at the return;
- the exit's report: `surface_hold.held` 1, `losses` 1, `restarted` 0.
- **Off check:** `setprop debug.privyhub.surface_hold 0` → a Home press gives today's restart (`restart_fast`, no
  `surface_lost` row); then `setprop debug.privyhub.surface_hold ""`, read back empty.

**C4'', two pads with no property** (LAN; `getprop debug.privyhub.pad_slots` empty, read; a two-player PS1 title,
multitap off; pad B first; exit and relaunch; pad A first; then in that session only pad A ~5 s, then only pad B):
- both starts write `"event": "pad_slots", "when": "start"` with `count` 2: slots 0 and 1, the same two pad hashes, no
  `google`-class entry;
- the heartbeat rows' `updates_by_player` rises only on the pressed pad's slot, while `packets_by_player` rises on all
  four.
- **Off check:** `setprop debug.privyhub.pad_slots off` → no `pad_slots` row or key in the next session; then
  `setprop debug.privyhub.pad_slots ""`, read back empty.

**C6, the player prompt** (`setprop debug.privyhub.player_prompt 1`, read back; two pads; a 2-player PS1 title,
multitap off). On screen:
1. at the start, "Player 1 — press any button";
2. pad B presses X → "P1" for 2 s, then "Player 2 — press any button";
3. pad A presses X → "P2", and the prompt goes away;
4. pad B holds Select+Start 2 s → "P1 released", then "Player 1 — press any button"; pad B presses again → P1;
5. a 1-player title → no prompt.
- **Pass:** the start response has `players` 2 (the 1-player title `players` 1); the `"event":"pad_slots"` rows
  (`when` `start`, then `change`) carry `claimed_by` (`prompt` for claimed slots, `stable` for kept ones), the
  heartbeat's `pad_slots` the same; the exit report has `players` and `pad_claims`; the game runs throughout and the
  claim press reaches the game; the user's line is the gate on what was on screen.
- **Off:** `setprop debug.privyhub.player_prompt ""` → no `players`, `pad_claims` or `claimed_by`, no prompt.

**C5'', the movie** (no game running, confirmed; the drop-in, daemon-reload, restart; `setprop
debug.privyhub.vod_retry 1`, read back).
- **(a) The 45-s drop:** the movie in front, nothing pressed on the onn, playing ≥ 1 min, then `echo "drop 45" >>
  runtime/vod_drop_test.trigger`.
  - `logs/vod_drop_test.jsonl`: `vod_drop_injected` with `dropped: 1`, `how: rst`, `refuse_s: 45.0`, then
    `vod_refuse_ended` with `vod_refused` ≥ 4;
  - `logs/vod_client.jsonl`: `vod_error` (`reason: reset`) → `vod_retry` × n → `vod_resumed`, the first row ~30-35 s
    after the injection;
  - on screen "reconnecting…", then the movie at the same position, with no "Playback error";
  - `logs/vod_range.jsonl`: `closed: client_reset`, then `range: bytes=<P>-` 206 after the window.
  - **Invalid if:** `dropped: 0`, or no `vod_error` by the window's end → once more with `drop 60`, the user told.
- **(b) A companion restart with the movie open** (playing ≥ 1 min): `systemctl --user restart privyhub-companion`.
  - the movie resumes by itself at the position, with no "connection to hub lost" and no Retry pressed;
  - `vod_client.jsonl` has a `vod_retry` with `reason: "401"` and `token_refetched: true`, then `vod_resumed`;
  - `vod_range.jsonl` shows 401 then 206. The first `vod_error` may be missing (posted while the hub was down).
- **Close:** the drop-in removed, `daemon-reload`, restart; `setprop debug.privyhub.vod_retry ""`.

## Validity

A cell is **valid** when all of these hold:
- its precondition held: its property (and for C5'' the drop-in) read back as stated, the other properties empty;
- the user's action happened as described (C1'': Home and back within the bound, the game in front; C4'': both starts
  and the two 5-s presses; C6: the steps in order; C5'' (a): the movie in front ≥ 1 min, then the drop with nothing
  pressed; (b): the movie in front ≥ 1 min, then the restart, Retry not pressed);
- the band was 5 GHz;
- the rows it names were written, or their absence is itself the reading.

A cell the user could not do, or whose action left the app, is **invalid**, not failed. C5'' (a) with `dropped: 0` or
no `vod_error` by the window's end is invalid (re-run once with `drop 60`).

## The CONFIRMED rule (CL-B7 §6)

- **CONFIRMED:** every cell that ran was valid, and **today's behaviours hold wherever no flag was set (B42's intended
  defaults aside)**. Then `8ba4d996…605f` is CONFIRMED and the pin moves in three places: `tools/e1_suite.py`
  `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test. The tests must be green.
- **Otherwise:** `0132b944…` is reinstalled from `home2_installed/`, read back and paired, and the user is told why.
- "Today's behaviours (B42's defaults aside)" means:
  - with `surface_hold` / `pad_slots` empty: the hold on (12 s) and stable slots on (B42's intended defaults, the
    reading of C1'' / C4''); with `0` / `off`: today's restart and no `pad_slots` row or key (`0132b944…`'s absent);
  - with `player_prompt` empty: no prompt, no `players` / `pad_claims` / `claimed_by`;
  - with `vod_retry` empty: today's VOD error path (not exercised beyond the close);
  - the existing seven defaults unchanged;
  - fourteen lines, `--check` ok and `flags_absent` at the close; `privyhub-diag` active.
- A cell valid but not met does not bear on the rule; it bears on its question.

## The reading (only for cells met; otherwise back to B with the rows)

- **C5'' met ((a) and (b)) → G-A13:** "Turn the movie retry on by default (`debug.privyhub.vod_retry`) and adopt
  `PRIVYHUB_VOD_LOG=1`? A dropped movie, or a hub restart, then reconnects and resumes by itself."
  (`PRIVYHUB_VOD_DROP_TEST` is never a question.)
- **C6 met → the prompt's default:** "Show 'Player N — press any button' by default (`debug.privyhub.player_prompt`)?"
- **C1'' / C4'' met:** G-A11 / G-A12 (already answered yes) are shown working by default; not met → back to B.
- Then the G9 checkpoint (B item 8), and H0 slice 1a as the next B queue with B45's four questions.

Nothing adopted; nothing committed.
