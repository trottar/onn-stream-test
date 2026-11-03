---
memory_schema: 1
as_of: 2026-11-03
status: TASK HANDOFF — HOME-2 (session A, hardware, attended, ~45 min at the TV with two pads and the onn remote; four stages by the user's message). Install queue M's APK `0132b944…` with every property empty; C1' the screen-loss hold (counter fixed), C4' two pads with the onn's remote taking no slot, C5' the movie with the hub-side drop; the close, the CONFIRMED rule, the record, G-A11..13 as the user's questions. Measurement only; nothing adopted; nothing committed
---

# HOME-2 — the hold, the pads, the movie

Read first: `SESSION_B_DONE_2026-11-02M.md` §HOME-2 items 1-6 (**the exact APK hash, properties, commands and pass rows — use theirs**), `B38_…`, `B39_…`, `B40_…`, `HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md` (C1 / C4 / C5 as they failed; the C1 and C4 methods), `CL_B7_…` §6, `docs/memory/CURRENT.md` (rewritten 2026-11-03: fourteen lines, `fcd924c2…` CONFIRMED, `privyhub-diag` active).

**The stage is the user's message.** The read line alone = stage 1. "Stage 2", "Stage 3", "Stage 4" with the user's line as below. **Every reply begins "YOU, now:" and the one thing the user does next, in plain words.**

## Stage 1 — the install (unattended ~10 min)

- Precondition: fourteen lines, `--check` ok (`fcd924c2…` CONFIRMED), `privyhub-diag` active, no `e3_flag.conf`, no game, one device paired, the client on the LAN, the band 5 GHz, the ten properties empty, no `privyhub-*` unit but the companion and `privyhub-diag`, HEAD named (the docs pass committed), the tree clean but the prompt and this file.
- Pre-registration hashed before the install: C1' / C4' / C5' pass rows as B items 2-4; validity; the CONFIRMED rule; the reading (G-A11..13 per cell met).
- The install per B item 1: preserve `fcd924c2…` and `554ccf61…`; `queue_m_built/` → `home2_installed/`, sha256 **`0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f`**, the signer the same; `adb install -r`; read back; paired; the ten properties empty; **the companion restart** (queue M's host code live, inert without its keys / line); fourteen lines; `--check` reads MISMATCH on the APK only (the pin rule).
- Exit: "YOU, now: come to the TV with the onn remote and ONE pad; start any game; when it's running, send 'Stage 2'."

## Stage 2 — C1', the hold (attended ~5 min)

- `setprop debug.privyhub.surface_hold 1` (read back). Reply: "YOU, now: press the remote's Home, count to 2, come straight back to the game — it should still be running where it was. Play about 30 s, then exit the game with Back. Then send 'Stage 3' and pair the second pad."
- On "Stage 3": the rows (B item 2: `surface_lost` `held`, `away_ms` < 12000; no `restart_fast` / `session_ended` at the return; the exit's report `surface_hold.held` 1, `losses` 1, `restarted` 0, `duration_ms` the whole session). The property cleared and read back.

## Stage 3 — C4', two pads (attended ~5 min)

- `setprop debug.privyhub.pad_slots stable` (read back). Reply: "YOU, now, with both pads paired: start a two-player PS1 game; press a button on pad B first, then pad A; exit; relaunch; press pad A first. Then, staying in the game, press only pad A for 5 s, then only pad B for 5 s. Then send 'Stage 4' with the two-player title's class (PS1) and nothing else."
- On "Stage 4": the rows (B item 3: both starts `pad_slots` `when: start` `count` 2, slots 0 and 1, the same two pad hashes, no `google`-class entry; the lower controller number slot 0; `updates_by_player` rising only on the pressed pad's slot while `packets_by_player` rises on all four; `/status` `changes_by_player` the same). The property cleared, read back; with it empty no `pad_slots` row or key.

## Stage 4 — C5', the movie with the hub-side drop (attended ~10 min), the close, the record

- The game ended (confirm no game); B item 4's host lines in `b40-vod-drop.conf`, daemon-reload, restart; `setprop debug.privyhub.vod_retry 1` (read back). Reply: "YOU, now: start a movie and let it play for a full minute. Touch nothing on the onn. Then send 'drop'."
- On "drop": the trigger file appended (B item 4's command); then tell the user: "YOU, now: watch the screen for about a minute — 'reconnecting…' then the movie carrying on from the same spot. Send 'Stage 5' with one line on what you saw." On "Stage 5": the rows (`vod_drop_injected` `dropped: 1` `how: rst` — `dropped: 0` = invalid, say so; `vod_range.jsonl` the `client_reset` request then `bytes=<P>-` 206; `vod_client.jsonl` `vod_error` → `vod_retry` → `vod_resumed`; the user's line).
- **The close:** B item 4's close commands (the drop-in removed, restart, `vod_retry` cleared); every property empty; fourteen lines; `--check` ok; `flags_absent`; `privyhub-diag` active.
- **The CONFIRMED rule as CL-B7 §6:** every cell valid and today's behaviours where no flag was set → `0132b944…` CONFIRMED and the pin moved (the three places; tests green); else `fcd924c2…` reinstalled from `cl_b14_installed/`, read back, paired, the user told why.
- **The record `evidence/HOME_2_HOLD_PADS_VOD_2026-11-03.md` + dir:** the per-cell tables beside HOME-1's rows, the user's lines verbatim, the decision, the APK on the onn named; `KNOWN_ISSUES.md` (the open index), ROADMAP lines, `logs/home2_git_status.txt`, the redactor; `CURRENT.md` (the rewritten form: Verified State and Next Action updated, the headings kept, under its limit — run `tools/check_memory_health.py` after): **G-A11..13 in B's words, one plain paragraph each, only for the cells met**; the guard's return and the G9 checkpoint draft as later items. The reply: "YOU, now: commit, then answer G-A11, G-A12, G-A13 yes or no each." Plus the three cells' one-line results.

No sudo, no nft, the Opal read-only, adb for the install, the three `setprop`s named and their clears, and state reads; no addresses or identifiers anywhere; nothing fetched, nothing deleted; fourteen lines and no `e3_flag.conf` at every teardown; nothing adopted; nothing committed.
