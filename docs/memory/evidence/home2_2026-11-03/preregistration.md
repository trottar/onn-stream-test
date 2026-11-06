# HOME-2: pre-registration (written and hashed before the install, 2026-11-06)

Sources: `handoffs/SESSION_B_DONE_2026-11-02M.md` §A items 1-6 (B's rows, used as B states them),
`handoffs/HOME-2_HOLD_PADS_VOD_TASK.md`, `CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md` §6, and HOME-1's C1 / C4 / C5
as they failed (`HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md`).

**The candidate:**
- APK `0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f` (queue M: B5 … B25 + B32 + B34 + B35 + B38 +
  B39; B27 / B29 out), from `PrivyHub/app/build/queue_m_built/app-debug.apk` → `home2_installed/`, with the same
  signer as `fcd924c2…`.
- **Predecessor (CONFIRMED):** `fcd924c28cbf70a85bb9a886caabcb07873eee2d028b6538284fce5a7ae39b96`
  (`cl_b14_installed/`). Also preserved: `554ccf61…9902` (`home1_installed/`).
- **The ten properties:**
  - the seven, empty throughout: `restart_guard`, `stall_signal`, `link_notice`, `link_report`, `loss_guard`,
    `wifi_lock`, `opus_decode`;
  - the three, empty except during their own cell: `surface_hold` (C1'), `pad_slots` (C4'), `vod_retry` (C5').
- **The host:** fourteen lines throughout; the companion restarted after the install (queue M's host code live, inert
  without the client's `pad_slots` key and without `PRIVYHUB_VOD_DROP_TEST=1`); for C5' only, the drop-in
  `b40-vod-drop.conf` (`PRIVYHUB_VOD_LOG=1`, `PRIVYHUB_VOD_DROP_TEST=1`), removed at the close.

## The cells and their pass rows (B items 2-4)

**C1', the hold** (stage 2, LAN; `setprop debug.privyhub.surface_hold 1`; a game running; the remote's Home, back
within ~2 s; play ~30 s; exit with Back):
- a recovery row `"event": "surface_lost"`, `"outcome": "held"`, `away_ms` < 12000;
- no `restart_fast` and no `session_ended` at the return;
- **the exit's report: `surface_hold.held` 1, `losses` 1, `restarted` 0**, and `duration_ms` covering the whole
  session (the start to the exit, not the start to the loss).
- Optional, not a pass term: a pad guide press behaves as a Home press (`reason` `user_leave`).
- **Off:** `setprop debug.privyhub.surface_hold ""`, read back empty.

**C4', two pads** (stage 3, LAN; `setprop debug.privyhub.pad_slots stable`; two pads paired; a two-player PS1 title;
pad B first, then pad A; exit and relaunch; pad A first; then in that session only pad A ~5 s, then only pad B ~5 s):
- both starts write `"event": "pad_slots", "when": "start"` with **`count` 2**: slots 0 and 1, the same two pad hashes
  both times, **no `google`-class entry** (the virtual remote takes no slot);
- the lower controller number of the two pads is slot 0;
- the heartbeat rows' **`updates_by_player` rises only on the pressed pad's slot** (a few from stick drift at most),
  while `packets_by_player` rises on all four; `/status` `changes_by_player` the same.
- **Off:** `setprop debug.privyhub.pad_slots ""` → no `pad_slots` row or key, and no `packets_by_player`.

**C5', the movie with the hub-side drop** (stage 4; no game; the drop-in and a restart; `setprop
debug.privyhub.vod_retry 1`; a movie playing ≥ 1 min, the player in front, nothing pressed on the onn; the trigger
`date -u +%FT%TZ >> runtime/vod_drop_test.trigger` from the hub):
- `vod_drop_injected` with `dropped: 1`, `how: rst` (**`dropped: 0` = nothing was streaming → the cell is invalid**);
- in `logs/vod_range.jsonl`: the movie's request `closed: client_reset` with bytes < length, then `range: bytes=<P>-`
  answered 206;
- in `logs/vod_client.jsonl`: `vod_error` → `vod_retry` → `vod_resumed`;
- on screen (the user's line): "reconnecting…", then the movie at the same position, with no "Playback error".
- **Close:** the drop-in removed, `daemon-reload`, restart; `setprop debug.privyhub.vod_retry ""`.

## Validity

A cell is **valid** when all of these hold:
- its precondition held: the property (and for C5' the drop-in) read back as set, and the other properties empty;
- the user's action happened as described (C1': Home and back within the bound with the game in front; C4': both
  starts and the two 5-s presses; C5': the movie in front ≥ 1 min, then the drop with nothing pressed);
- the band was 5 GHz;
- the rows it names were written, or their absence is itself the reading.

A cell the user could not do, or whose action left the app (as HOME-1's C5 did), is **invalid**, not failed. C5' with
`dropped: 0` is invalid.

## The CONFIRMED rule (CL-B7 §6)

- **CONFIRMED:** every cell that ran was valid, and **today's behaviours hold wherever no flag was set**. Then
  `0132b944…e24f` is CONFIRMED and the pin moves in three places: `tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test. The tests must be green.
- **Otherwise:** `fcd924c2…` is reinstalled from `cl_b14_installed/`, read back and paired, and the user is told why.
- "Today's behaviours" means:
  - with every new property empty: no `surface_lost` hold, no `pad_slots` row or key (and no `packets_by_player`),
    today's VOD error path;
  - the existing seven defaults unchanged;
  - fourteen lines, `--check` ok and `flags_absent` at the close; `privyhub-diag` active.
- A cell valid but not met does not bear on the rule; it bears on its question.

## The reading (only for cells met; otherwise back to B with the rows)

- **C1' met → G-A11:** "Turn the screen-loss hold on by default in the next APK (`debug.privyhub.surface_hold`)? A
  Home press, a guide press or a system panel of up to 12 s then keeps the session."
- **C4' met → G-A12:** "Turn stable player slots on by default (`debug.privyhub.pad_slots=stable`)? Real pads keep
  their player number across launches; the onn's remote never takes one."
- **C5' met → G-A13:** "Turn the movie retry on by default (`debug.privyhub.vod_retry`) and adopt
  `PRIVYHUB_VOD_LOG=1`? A dropped movie reconnects and resumes by itself for 2.5 min."
- `PRIVYHUB_VOD_DROP_TEST` is never a question. Nothing is adopted in this session.
