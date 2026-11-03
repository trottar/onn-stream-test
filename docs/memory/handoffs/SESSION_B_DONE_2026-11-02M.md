# SESSION B — done, 2026-11-02 M (QUEUE_2026-11-02M: B38, B39, B40; run 2026-11-03 02:55-03:11Z; baseline e0155d1c plus A's uncommitted G-A10 `tools/` edits, untouched. G-A10's record present, only the companion + `privyhub-diag` active, checked first; the first attempt at 02:27Z stopped on the missing record, one status line. Nothing committed, nothing adopted, nothing installed, no stream, no companion restart, no adb; `privyhub-diag` and `~/privyhub_diag/` untouched)

**How it ran.** Each item was built in its own `/tmp/b_q02m_<item>` copy, each design hashed before its code. The
three diffs merged with no conflict (`evidence/queue_m_2026-11-02/queue_m_combined.diff`) and were applied to the tree,
uncommitted.
- **Host:** every `tests/` suite as the baseline (41 / 41) plus 2 new suites, all OK. The four `tools/` tests fail in a
  copy as at every baseline.
- **JVM:** 195 / 195 (184 + 11).

1. **B38 SETTLED + BUILT — the virtual remote takes no slot; the host counts the pad that moved** (inside
   `debug.privyhub.pad_slots=stable`; no new flag).
   - **Settled:**
     - **The controller-number-1 device** is the onn's "virtual-remote": KEYBOARD | DPAD | GAMEPAD, EXTERNAL, vendor
       class `google`, no stick or hat axis.
     - **Why it passed B34:** `isVirtual()` is false for it (true only for the built-in virtual keyboard, id −1). It
       declares GAMEPAD and answers the gamepad buttons as present, so a button test alone cannot exclude it.
     - **Why slot 0 both times:** B34 assigns by controller number (1 before the pads' 2 and 3).
     - **Why all four counters rose equally:** the sender sends players 0-3 every ~8-ms tick (CTRL-L1), and the
       bridge's `_apply_report` added one per packet. It counted ticks, not pads.
   - **Built (client):** `PadSlots.eligible()` also needs a face button (A/B/X/Y) **and** stick or hat axes. The onn's
     own devices are key-only, so they are excluded by class, with no identifier compared or written.
   - **Built (host):** only when the client sends its own `pad_slots` key, a changed-only counter.
     - The heartbeat row's `updates_by_player` = changes (a press or axis move against that player's previous
       state), and `packets_by_player` = today's per-packet count.
     - `/status` gains `changes_by_player`; its `updates_by_player` stays per-packet (the `tools/` probes read it).
   - **Tests:** JVM 5 (`VirtualRemoteNoSlotTest`; B34's unedited); host 7 (`tests/pad_slots_changes`; B34's
     unedited); 2 mutations caught; absent PROVEN.
   - **Disclosed by the worker:** a stray `rm -rf /dev/null` in one mutation command. It failed as a non-root user;
     `/dev/null` was checked unchanged; nothing was deleted.
   - Record: `evidence/B38_VIRTUAL_REMOTE_NO_SLOT_2026-11-02.md`.
2. **B39 SETTLED + FIXED — the hold's report counter; the guide key recorded** (inside `debug.privyhub.surface_hold`).
   - **Settled:** the activity caches its report and clears it only at a new start. B32 snapshotted that report at
     every loss, before counting it. A held loss keeps the session, so the first loss's snapshot was never replaced.
     C1's report shows exactly that: every counter 0, `duration_ms` 16270 = the start to the first loss.
   - **Fixed:**
     - a held re-attach clears the cache;
     - a loss is counted before the snapshot;
     - the snapshot's `surface_hold` object is refreshed when the outcome is decided (at the expiry, and at
       `onDestroy` inside a hold).
     - C1's sequence now reports `losses` 2, `held` 1, `restarted` 1.
   - **The guide key:** the onn's input policy turns it into Home before any app sees it. B32's "consume" half is
     dropped (`onKey` returns false for every key; keys still noted in the rows; `pad_system_keys_consumed` always 0).
     The hold covers a guide press like a Home press within the bound. A dated note is appended to B32's record.
   - **Tests:**
     - JVM 6 (`HoldReportTest`, the report cache modelled as written) on 190 / 190 in the worker's copy.
     - B32's `aPadSystemKeyIsConsumedTheRemotesIsNot` edited and renamed `noKeyIsConsumedEveryKeyIsNoted`
       (disclosed).
     - 3 mutations caught; a fourth (today's order) is equivalent under the refresh, as the record states.
     - Absent PROVEN.
   - Record: `evidence/B39_HOLD_COUNTER_2026-11-02.md`.
3. **B40 BUILT — a hub-side VOD drop for the bench** (`PRIVYHUB_VOD_DROP_TEST=1`; host, per run, **never to be
   adopted**).
   - **A file, not a signal:** `<repo>/runtime/vod_drop_test.trigger`.
     - The range server polls its (mtime, size) every 250 ms. The signature at the server's start is the baseline, so a
       leftover trigger never fires; each change drops once. The file is never read, written or removed.
     - A signal would kill a range server running without the flag, and nothing records its pid.
   - **The drop:** `SO_LINGER {1,0}` plus `connect(AF_UNSPEC)` sends a real RST on each `/vod/` connection that is
     streaming a body. B35's row reads `client_reset`. Live media is never touched. `shutdown` is only the fallback
     (`how: shutdown`): it gave the client a clean EOF.
   - **The row:** `vod_drop_injected` (`trigger`, `dropped`, opaque `ids`, `how`) in `logs/vod_drop_test.jsonl`, and in
     `logs/vod_range.jsonl` when B35's log is on.
   - **The flag** reaches the range server by inheritance at the service's start, so it needs a drop-in and a restart.
   - **Tests:** 14; B35's `tests/vod_log` one filter line so its AST count skips B40's two nodes (disclosed); 3
     mutations caught; absent PROVEN (the same bytes; a trigger with no flag does nothing).
   - Record: `evidence/B40_VOD_DROP_TEST_2026-11-02.md`.
4. **The APK (B5 … B25 + B32 + B34 + B35 + B38 + B39; B27 / B29 out)
   `0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f`**, 9,677,160 B.
   - **How it was built:** the tree with `b29.diff` then `b27.diff` reversed (the client sources byte-equal to
     `554ccf61…`'s), then queue M's diff. Offline, `--rerun-tasks --no-configuration-cache`; JVM 184 / 184 (195 less B27's
     4 and B29's 7).
   - **Checks:** a rebuild gives the same bytes; `apksigner verify` OK; same signer as `fcd924c2…`. Against `554ccf61…`,
     only `classes3.dex` differs.
   - **Pinned, NOT installed** (`PrivyHub/app/build/queue_m_built/app-debug.apk`). `fcd924c2…` stays CONFIRMED;
     `554ccf61…` stays preserved at `home1_installed/`. Files: `evidence/queue_m_2026-11-02/`.
5. **Live at the next companion restart:**
   - B38's host counter, only for a client sending `pad_slots` (none does on `fcd924c2…`);
   - B40, only with `PRIVYHUB_VOD_DROP_TEST=1`.
   - Today's behaviour otherwise; the running companion keeps today's code until then.

## A — HOME-2 (the user at the TV for the hand steps; restarts outside 04:30-05:30Z, no game running)

1. **Setup:**
   - pre-register the rows below, hashed, before the install;
   - `--check` ok on fourteen; `fcd924c2…` CONFIRMED read back;
   - preserve `fcd924c2…` (`cl_b14_installed/`) and `554ccf61…` (`home1_installed/`);
   - copy `PrivyHub/app/build/queue_m_built/app-debug.apk` to `PrivyHub/app/build/home2_installed/`, `adb install -r`,
     and read back `0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f`, paired;
   - **every property empty** (the ten HOME-1 read, `surface_hold` / `pad_slots` / `vod_retry` among them).
   - **The companion restart** (brings queue M's host code live, inert without its keys / line).
2. **C1', the hold** (LAN).
   - **Do:** `adb shell setprop debug.privyhub.surface_hold 1`; start a game; press the remote's Home and come back
     within 3 s; play ~30 s; exit with Back.
   - **Pass:**
     - a recovery row `"event": "surface_lost"`, `"outcome": "held"`, `away_ms` < 12000;
     - no `restart_fast` and no `session_ended` at the return;
     - **the exit's report: `surface_hold.held` 1, `losses` 1, `restarted` 0**, and `duration_ms` covering the whole
       session.
   - **Optional:** a pad guide press behaves as a Home press (`reason` `user_leave`); not a pass term.
   - **Off:** `adb shell setprop debug.privyhub.surface_hold ""`.
3. **C4', two pads** (LAN, a two-player PS1 title, two pads paired).
   - **Do:** `adb shell setprop debug.privyhub.pad_slots stable`; press pad B first; exit and relaunch; press pad A
     first. Then, in one session, press only pad A for ~5 s, then only pad B for ~5 s.
   - **Pass:**
     - both starts write `"event": "pad_slots", "when": "start"` with **`count` 2**: slots 0 and 1, the same two pad
       hashes both times, **no `google`-class entry** (the virtual remote takes no slot);
     - the lower controller number of the two pads is slot 0;
     - the heartbeat rows' **`updates_by_player` rises only on the pressed pad's slot** (a few from stick drift at
       most), while `packets_by_player` rises on all four; `/status` `changes_by_player` the same.
   - **Off:** `adb shell setprop debug.privyhub.pad_slots ""` → no `pad_slots` row or key, and no `packets_by_player`.
4. **C5', the movie with the hub-side drop.**
   - **Host lines for this run only, then restart:**
     ```
     printf '[Service]\nEnvironment=PRIVYHUB_VOD_LOG=1\nEnvironment=PRIVYHUB_VOD_DROP_TEST=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b40-vod-drop.conf
     systemctl --user daemon-reload && systemctl --user restart privyhub-companion
     ```
   - **Do:**
     - `adb shell setprop debug.privyhub.vod_retry 1`;
     - start a movie and let it play ≥ 1 min, **the player in front, nothing pressed on the onn**;
     - trigger the drop from the hub:
       ```
       cd ~/Projects/onn-stream-test && mkdir -p runtime && date -u +%FT%TZ >> runtime/vod_drop_test.trigger
       ```
   - **Pass:**
     - `vod_drop_injected` with `dropped: 1`, `how: rst` (**`dropped: 0` = nothing was streaming → the cell is
       invalid**);
     - in `logs/vod_range.jsonl`: the movie's request `closed: client_reset` with bytes < length, then
       `range: bytes=<P>-` answered 206;
     - in `logs/vod_client.jsonl`: `vod_error` → `vod_retry` → `vod_resumed`;
     - on screen: "reconnecting…", then the movie at the same position, with no "Playback error".
   - **Close:**
     ```
     rm ~/.config/systemd/user/privyhub-companion.service.d/b40-vod-drop.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion
     adb shell setprop debug.privyhub.vod_retry ""
     ```
5. **The close and the CONFIRMED rule (CL-B7 §6):**
   - **The close:** every property empty; the B40 drop-in removed; fourteen lines; `e3_state.py --check` ok;
     `flags_absent`.
   - **The rule:** if every cell that ran is valid and today's behaviours hold wherever no flag was set,
     **`0132b944…e24f` is CONFIRMED** and the pin moves: `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py`
     `ADOPTED_APK_SHA256` and its test. Otherwise `fcd924c2…` goes back on.
6. **G-A11..13, the user's questions** (only for cells met; otherwise back to B with the rows):
   - **G-A11 (C1'):** "Turn the screen-loss hold on by default in the next APK (`debug.privyhub.surface_hold`)? A Home
     press, a guide press or a system panel of up to 12 s then keeps the session."
   - **G-A12 (C4'):** "Turn stable player slots on by default (`debug.privyhub.pad_slots=stable`)? Real pads keep their
     player number across launches; the onn's remote never takes one."
   - **G-A13 (C5'):** "Turn the movie retry on by default (`debug.privyhub.vod_retry`) and adopt `PRIVYHUB_VOD_LOG=1`?
     A dropped movie reconnects and resumes by itself for 2.5 min." (`PRIVYHUB_VOD_DROP_TEST` is never a question.)

## Files
- **Records:** `evidence/B38_VIRTUAL_REMOTE_NO_SLOT_2026-11-02.md`, `B39_HOLD_COUNTER_2026-11-02.md`,
  `B40_VOD_DROP_TEST_2026-11-02.md`.
- **Their dirs:** `b38_2026-11-02/`, `b39_2026-11-02/`, `b40_2026-11-02/`. Integration: `evidence/queue_m_2026-11-02/`.
- **Patch files:** `patches/B38_VIRTUAL_REMOTE_NO_SLOT.md`, `B39_HOLD_COUNTER.md`, `B40_VOD_DROP_TEST.md`.
- **Logs:** `logs/b38_` / `b39_` / `b40_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md`; B32's record (a dated note at its end).
- **Left in /tmp:** `b_q02m_base`, `b_q02m_all`, `b_q02m_apk`, `b_q02m_apk_pre`, `b_q02m_jvmbase`,
  `b_q02m_treecheck*`, the item copies `b_q02m_b38` / `b39` / `b40` and their `_scratch/`, `b_q02m_scratch/`, and the
  scripts `b_q02m_*.sh` / `b_q02m_junit.py`.
