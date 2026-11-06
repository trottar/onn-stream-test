# SESSION B — done, 2026-11-06 N (QUEUE_2026-11-06N: B41, B42, B43, B44, B45; run 17:51-18:34Z; baseline 795d80d4, the tree clean. Only the companion + `privyhub-diag` active, checked first. Nothing committed, nothing adopted, nothing installed, no stream, no companion restart, no adb; `privyhub-diag` and `~/privyhub_diag/` untouched)

**The user's decisions this queue rests on (2026-11-06):** G-A11 yes (the hold on by default), G-A12 yes (stable slots
on by default), the player prompt wanted, the next phase H0 (user-content import) then PS2 etc.

**How it ran.** B41-B43 were each built in their own `/tmp/b_q06n_<item>` copy, each design hashed before its code;
B44 and B45 are documents only. The three diffs merged with no conflict (`evidence/queue_n_2026-11-06/queue_n_combined.diff`)
and were applied to the tree, uncommitted.
- **Host:** every `tests/` suite as the baseline (43 / 43) plus 1 new suite (`player_prompt`); `vod_drop_test` 14 → 21 and
  `vod_log` 9 → 12, all OK. The four `tools/` tests fail in a copy as at every baseline.
- **JVM:** 219 / 219 (195 + 10 + 6 + 8).

1. **B41 SETTLED + BUILT — the player prompt** (`debug.privyhub.player_prompt=1`, opt-in).
   - **Settled:** the hub has no per-title "players" field. `companion/player_count.py`:
     - `player_mode` `single` → 1;
     - else the ports the core reads: 4 for PS1 with the multitap on, else 2, capped by the metadata's `max_players`
       (≥ 2);
     - unknown → 2. With no SNES multitap path, a 4-player SNES title reads 2.
   - **Host:** `players` / `players_source` in the `native-stream-start` response, only when the start query carries
     `player_prompt=1`. The client's parse ignores unknown keys; an old host sends none → 2.
   - **Client (`PlayerPrompt.kt`, on B34 / B38's slots):** "Player N — press any button" bottom-centre.
     - The first unclaimed real pad to press a face button or Start takes the lowest open slot below `players`, with a
       2-s "PN" badge. The claim press reaches the game (input never blocked); an unclaimed pad's sticks and other keys
       are dropped until it claims.
     - A pad already in the map keeps its slot and shows its badge. Select+Start held 2 s → "PN released".
     - A 1-player title: no prompt. The prompt implies stable slots (`padSlots` built when `pad_slots` is stable **or**
       `player_prompt=1`).
   - **Rows:** `pad_claims` on the start / heartbeat / report; the host adds `claimed_by: prompt | stable` to each
     `pad_slots` entry.
   - **Tests:** JVM 10; host 11; 3 mutations caught; absent PROVEN. Record: `evidence/B41_PLAYER_PROMPT_2026-11-06.md`.
2. **B42 BUILT — the two defaults (G-A11, G-A12).**
   - **The flags:**
     - `debug.privyhub.surface_hold`: absent / empty / junk → the 12-s hold; `0` / `off` → off; `1` or a bound of
       10000-30000 as before;
     - `debug.privyhub.pad_slots`: absent / empty / junk → stable; `off` / `0` → today's first-input order.
   - Only the two flag objects changed. `0` / `off` = `0132b944…`'s absent PROVEN; `NativeStreamActivity.kt` is
     byte-equal.
   - **Disclosed (as B13 / B19 / B25):** `SurfaceHoldTest.theFlagIsOffUnlessOneOrABoundInRange`,
     `PadSlotsTest.theFlagIsStableOnly` and `VirtualRemoteNoSlotTest.absentIsToday` moved to the new meaning.
   - **The host is unchanged, but from this APK every session sends `pad_slots`.** So:
     - every start writes a `pad_slots` row, and B38's changed-only counter is on for every session;
     - the heartbeat's `updates_by_player` is the change count, and the old count is `packets_by_player`;
     - every screen loss writes `surface_lost`.
   - **Tests:** JVM 6; 1 mutation caught. Record: `evidence/B42_HOLD_AND_SLOTS_DEFAULT_ON_2026-11-06.md`.
3. **B43 SETTLED + BUILT — the movie retry made real** (inside `debug.privyhub.vod_retry=1`; B40's
   `PRIVYHUB_VOD_DROP_TEST=1`).
   - **Settled:**
     - **Where the token lives:** in `IdentitySession`'s memory, sent as a header. A companion restart empties the hub's
       sessions, but the onn's cache isn't near expiry, so every media request got 401. Only control calls drop the
       token. B35 read the 401 (code 2004) as "connection lost".
     - **Media3 1.11.0's own reconnect:** delay `min((n−1)×1000, 5000)` ms, minimum 3 retries, and progress resets the
       count. An error surfaces only after the 15-30 s buffer is spent, so a drop must outlast ~35 s. **`drop 45`**
       explains HOME-2's 12.8-s resets never reaching B35.
   - **Client:**
     - each error has a `reason` (`reset` / `refused` / `timeout` / `401` / `403`);
     - a 401 / 403 refetches the token and retries at once;
     - three refusals after refetches → `refused` ("The hub refused this playback…"), never "lost";
     - "connection to hub lost" only after 150 s with no answer;
     - Retry refetches first;
     - rows gain `reason`, `token_refetched`, `kind`.
   - **Host:**
     - a trigger line `drop <seconds>` (0-600) → after the one reset, every new `/vod/` request gets an immediate RST
       (not a 503, which reads as a refusal) for that long;
     - only the appended bytes are read; the file is never written or removed;
     - a plain line or `drop 0` = B40 as built;
     - rows `refuse_s` and `vod_refuse_ended` (`vod_refused`).
   - **Tests:** JVM 8; host 7 + 3; 4 mutations caught (one restores HOME-2's `vod_gave_up`); absent PROVEN.
   - Record: `evidence/B43_VOD_RETRY_TOKEN_2026-11-06.md`.
4. **B44 WRITTEN — the G9 checkpoint draft:** `handoffs/G9_CHECKPOINT_DRAFT_2026-11-06.md`, against §G9's list verbatim.
   - **9 met:**
     - the trust topology, the overlay provider, the first provider path;
     - source vs identity, auth;
     - the real off-site sessions, telemetry under WAN, the adverse-network envelope;
     - the household LAN, by design, never probed.
   - **3 deferred:** the travel router (contract preserved), the handheld (no hardware), Steam (with the §G7 contract).
   - **2 open:**
     - local operation without remote: LAN play with the onn off the overlay is shown, but no session has been scored
       with the hub's own Tailscale down (the G4 runbook's step 18; needs the user);
     - the clean checkpoint itself.
   - Plus what G leaves open, and the README paragraph. Nothing applied to ROADMAP / README / CURRENT.
5. **B45 WRITTEN — the H0 import contract:** `architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`, no code.
   - **The layout:** `PrivyHub-Import/games/<system>/` mirrors the library `games/<system>/`. A title's id comes from its
     path and saves are keyed by basename, so an import never moves or renames an existing title.
   - **`tools/import_usb.py`:** inspect → dry-run manifest → hash → validate (CHD v5, cue tracks, the disc's `CD001` /
     `PLAYSTATION`) → duplicate by content hash → copy (same-filesystem temp, link without overwrite, the entry file
     last, a journal and rollback) → verify → sanitized log.
   - **Slice 1a (the next queue):** PS1 only, inspect + dry run + manifest, `PrivyHub-Import/` in `.gitignore`. Then 1b,
     the copy.
   - **Found:** PS1 `.iso` is listed but refused at launch. The PS1 BIOS dir is empty (OpenBIOS in the core, inferred).
   - **The user's questions:**
     - a real BIOS or OpenBIOS;
     - write an `.m3u` for multi-disc titles, or refuse;
     - a "NEW" tag;
     - hide PS1 `.iso`.
6. **The APK (B5 … B25 + B32 + B34 + B35 + B38 + B39 + B41 + B42 + B43; B27 / B29 out)
   `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f`**, 9,689,568 B.
   - **How it was built:** the tree with `b29.diff` then `b27.diff` reversed (client sources byte-equal to `0132b944…`'s
     build copy), then queue N's diff. Offline, `--rerun-tasks --no-configuration-cache`; JVM 208 / 208.
   - **Checks:** a rebuild gives the same bytes; `apksigner verify` OK; same signer as `0132b944…`.
   - **Pinned, NOT installed** (`PrivyHub/app/build/queue_n_built/app-debug.apk`). `0132b944…` stays CONFIRMED.
     Files: `evidence/queue_n_2026-11-06/`.
7. **Live at the next companion restart:**
   - `players` in the start response, only for a client sending `player_prompt=1`;
   - B43's host part, only with `PRIVYHUB_VOD_DROP_TEST=1`;
   - B43's three whitelisted fields in `vod_client.jsonl`, only when such a client posts them.
   - Today's behaviour otherwise.

## A — HOME-3 (the user at the TV; restarts outside 04:30-05:30Z, no game running)

1. **Setup:**
   - pre-register the rows below, hashed, before the install;
   - `--check` ok on fourteen; `0132b944…` CONFIRMED read back;
   - preserve `0132b944…` (`home2_installed/`);
   - copy `PrivyHub/app/build/queue_n_built/app-debug.apk` to `PrivyHub/app/build/home3_installed/`, `adb install -r`,
     and read back `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f`, paired;
   - **every property empty** (HOME-2's ten; `surface_hold`, `pad_slots`, `vod_retry`, `player_prompt` among them).
   - **The companion restart** (queue N's host code live, inert without its keys / line).
2. **C1'', the hold with no property** (LAN).
   - **Do:** `getprop debug.privyhub.surface_hold` reads empty; start a game; press the remote's Home and come back
     within 3 s; play ~30 s; exit with Back.
   - **Pass:**
     - a recovery row `"event": "surface_lost"`, `"outcome": "held"`, `away_ms` < 12000;
     - no `restart_fast` and no `session_ended` at the return;
     - the exit's report: `surface_hold.held` 1, `losses` 1, `restarted` 0.
   - **Off check:** `adb shell setprop debug.privyhub.surface_hold 0` → today's restart (`restart_fast`, no
     `surface_lost` row); then `adb shell setprop debug.privyhub.surface_hold ""`.
3. **C4'', two pads with no property** (LAN, a two-player PS1 title).
   - **Do:** press pad B first; exit and relaunch; press pad A first. Then, in one session, press only pad A for ~5 s,
     then only pad B.
   - **Pass:**
     - both starts write `"event": "pad_slots", "when": "start"` with `count` 2: slots 0 and 1, the same two pad
       hashes, no `google`-class entry;
     - the heartbeat rows' `updates_by_player` rises only on the pressed pad's slot, while `packets_by_player` rises on
       all four.
   - **Off check:** `adb shell setprop debug.privyhub.pad_slots off` → no `pad_slots` row or key; then
     `adb shell setprop debug.privyhub.pad_slots ""`.
4. **C6, the player prompt** (`adb shell setprop debug.privyhub.player_prompt 1`; two pads; a 2-player PS1 title,
   multitap off).
   - **Do, and what the screen must show:**
     1. At the start, "Player 1 — press any button".
     2. Pad B presses X → "P1" for 2 s, then "Player 2 — press any button".
     3. Pad A presses X → "P2", and the prompt goes away.
     4. Pad B holds Select+Start 2 s → "P1 released", then "Player 1 — press any button"; pad B presses again → P1.
     5. A 1-player title → no prompt.
   - **Pass:**
     - the start response has `players` 2 (the 1-player title `players` 1);
     - the `"event":"pad_slots"` rows (`when` `start`, then `change`) carry `claimed_by` (`prompt` for claimed slots,
       `stable` for kept ones); the heartbeat's `pad_slots` the same;
     - the exit report has `players` and `pad_claims`;
     - the game runs throughout, and the claim press reaches the game.
   - **Off:** `adb shell setprop debug.privyhub.player_prompt ""` → no `players`, `pad_claims` or `claimed_by`, no
     prompt.
5. **C5'', the movie** (two parts).
   - **Setup:**
     ```
     printf '[Service]\nEnvironment=PRIVYHUB_VOD_LOG=1\nEnvironment=PRIVYHUB_VOD_DROP_TEST=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b43-vod-drop.conf
     systemctl --user daemon-reload && systemctl --user restart privyhub-companion
     adb shell setprop debug.privyhub.vod_retry 1
     ```
   - **(a) The 45-s drop:** the movie in front, nothing pressed on the onn, playing ≥ 1 min, then
     `cd ~/Projects/onn-stream-test && mkdir -p runtime && echo "drop 45" >> runtime/vod_drop_test.trigger`.
     - **Pass:**
       - `logs/vod_drop_test.jsonl`: `vod_drop_injected` with `dropped: 1`, `how: rst`, `refuse_s: 45.0`, then
         `vod_refuse_ended` with `vod_refused` ≥ 4 (the player's own reconnects gave up);
       - `logs/vod_client.jsonl`: `vod_error` (`reason: reset`) → `vod_retry` × n → `vod_resumed`, the first row ~30-35 s
         after the injection;
       - on screen "reconnecting…", then the movie at the same position, with no "Playback error";
       - `logs/vod_range.jsonl`: `closed: client_reset`, then `range: bytes=<P>-` 206 after the window.
     - **Invalid if:** `dropped: 0`, or no `vod_error` by the window's end (run again with `drop 60`).
   - **(b) A companion restart with the movie open** (playing ≥ 1 min): `systemctl --user restart privyhub-companion`.
     - **Pass:**
       - the movie resumes by itself at the position, with no "connection to hub lost" and no Retry pressed;
       - `vod_client.jsonl` has a `vod_retry` with `reason: "401"` and `token_refetched: true`, then `vod_resumed`;
       - `vod_range.jsonl` shows 401 then 206.
       - The first `vod_error` may be missing (posted while the hub was down).
   - **Close:**
     ```
     rm ~/.config/systemd/user/privyhub-companion.service.d/b43-vod-drop.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion
     adb shell setprop debug.privyhub.vod_retry ""
     ```
6. **The close and the CONFIRMED rule (CL-B7 §6):**
   - **The close:** every property empty; the drop-in removed; fourteen lines; `e3_state.py --check` ok; `flags_absent`.
   - **The rule:** if every cell that ran is valid and today's behaviours hold wherever no flag was set (B42's intended
     defaults aside), **`8ba4d996…605f` is CONFIRMED** and the pin moves: `tools/e1_suite.py` `EXPECT_APK`,
     `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise `0132b944…` goes back on.
7. **The user's questions** (only for cells met; otherwise back to B with the rows):
   - **G-A13 (C5''):** "Turn the movie retry on by default (`debug.privyhub.vod_retry`) and adopt `PRIVYHUB_VOD_LOG=1`?
     A dropped movie, or a hub restart, then reconnects and resumes by itself." (`PRIVYHUB_VOD_DROP_TEST` is never a
     question.)
   - **The prompt's default (C6):** "Show 'Player N — press any button' by default (`debug.privyhub.player_prompt`)?"
8. **Then the G9 checkpoint:**
   - apply `handoffs/G9_CHECKPOINT_DRAFT_2026-11-06.md` to the ROADMAP §G9 marker and `CURRENT.md`;
   - the two open items stated: the hub-overlay-down local check is the user's, and the clean checkpoint is the user's
     commit;
   - then H0 slice 1a is the next B queue (B45's questions to the user first).

## Files
- **Records:** `evidence/B41_PLAYER_PROMPT_2026-11-06.md`, `B42_HOLD_AND_SLOTS_DEFAULT_ON_2026-11-06.md`,
  `B43_VOD_RETRY_TOKEN_2026-11-06.md`.
- **Documents:** `handoffs/G9_CHECKPOINT_DRAFT_2026-11-06.md`, `architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`.
- **Dirs:** `b41_` … `b45_2026-11-06/`; integration `evidence/queue_n_2026-11-06/`.
- **Patch files:** `patches/B41_PLAYER_PROMPT.md`, `B42_HOLD_AND_SLOTS_DEFAULT_ON.md`, `B43_VOD_RETRY_TOKEN.md`.
- **Logs:** `logs/b41_` / `b42_` / `b43_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (an index line and a section), `docs/ROADMAP.md`.
- **Left in /tmp:**
  - `b_q06n_base`, `b_q06n_all`, `b_q06n_apk`, `b_q06n_apk_pre`, `b_q06n_jvmbase`, `b_q06n_treecheck*`;
  - the item copies `b_q06n_b41` / `b42` / `b43` and their `_scratch/`;
  - `b_q06n_scratch/`, the scripts `b_q06n_*.sh` / `b_q06n_junit.py`.
