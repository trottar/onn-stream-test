---
memory_schema: 1
as_of: 2026-10-31
status: TASK HANDOFF — HOME-1 (session A, hardware, when the user is home with the onn on the home 5 GHz LAN; five stages by the user's message, ~2 h with the user at the TV for stages 2 and 4). Stage 1 (unattended): housekeeping, the trip keeper closed and "read the trip", `privyhub-diag` enabled, the companion restart (B33 live), B's APK `554ccf61…` installed with every property empty. Stage 2 (attended): C1 the screen loss. Stage 3 (the onn on the overlay by the user's hand, then unattended): C3 the no-rewind stall, then C2 the step in place. Stage 4 (the onn back; attended): C4 two pads swapped, C5 the movie drop. Stage 5: the close, the CONFIRMED rule, the record, G-A10..13 as the user's questions. Measurement only; nothing adopted; nothing committed
---

# HOME-1 — the trip closed, the queue L cells

Read first: `SESSION_B_DONE_2026-10-31L.md` (**the exact APK hash, properties, flags, strings, commands and pass rows — use theirs: §HOME-1 items 1-7**), `B32_…`, `B33_…`, `B34_…`, `B35_…`, `B36_…` (the rows and the row names), `TRIP_R2_FRIDAY_GAMEPLAY_2026-10-31.md` §1 (the six restarts the trip read must reproduce), `CL_B16_…` (the overlay hand step; `cl_b16_driver.py` is the driver to copy), `CL_B7_…` §6, `TRIP_PREP_2026-10-29.md` (thirteen lines, `fcd924c2…`).

**The stage is the user's message.** The read line alone = stage 1; "Stage 2" … "Stage 5" as below. **Every reply begins "YOU, now:" and the one thing the user does next.** No stage inside 04:15-05:30Z (the nightly watch ended 2026-10-31T06:00Z — confirm `privyhub-link-n1` is gone; if it still exists, leave it).

## Stage 1 — housekeeping, the trip, the keeper, the restart, the install (unattended ~30 min)

- Precondition: thirteen lines, `--check` ok (APK `fcd924c2…` CONFIRMED), no `e3_flag.conf`, no game, one device paired, **the client on the LAN** (Hub host empty, the newest `token_issued` lan; else "YOU, now:" the two steps — Hub host home value, Tailscale Disconnect — and wait), the band 5 GHz, HEAD named (queue L committed), the tree clean but the prompt and this file.
- **Housekeeping:** `git rm` / delete `_cowork_prompt_cap.txt` (never applied; B32 would make its line act); `privyhub-trip-log` stopped by its cap (or `touch evidence/trip_2026-10-30/STOP` and wait), `status.txt` stopped, the manifest checked; `_cowork_prompt_offsite.txt` left (historical).
- **"Read the trip":** `python3 tools/diag_read.py trip` → `evidence/reads/diag_trip_<UTC>.md`; it must show Friday's six restarts as TRIP-R2 §1, plus Saturday's and Sunday's play; the per-session table for the whole weekend; the user's one line on the weekend recorded if given.
- **`privyhub-diag`:** B item 3's commands exactly; `is-active` active; `diag_check` line 6 `unit privyhub-diag active`; chunks under `~/privyhub_diag/<date>/raw/` within 5 min.
- **The companion restart** (B33 live; disclosed as the first live run of B33); thirteen lines; `--check` ok; `rewind_needs_loss_config` row at the plugin's start.
- **The install:** preserve `fcd924c2…` (`cl_b14_installed/`); `PrivyHub/app/build/queue_l_built/app-debug.apk` → `home1_installed/`, sha256 **`554ccf61a87ad061320740adfa830b6fe726e794dfccbe544873bd621b939902`**, the signer the same; `adb install -r`; read back; paired; **the ten properties read back empty** (the seven + `surface_hold`, `pad_slots`, `vod_retry`).
- **Pre-registration hashed before the install:** C1-C5's pass rows as B item 5 states them; the validity rule; the CONFIRMED rule; the reading (G-A10..13 per cell met). Cap per detached launch + 2 h.
- Exit. The reply: "YOU, now: come to the TV with the onn remote and one pad; start any game; then send 'Stage 2'." Plus the trip read's one-line result, the keeper active, the APK read back, the properties empty.

## Stage 2 — C1, the screen loss (attended ~15 min)

- `adb shell setprop debug.privyhub.surface_hold 1` (the one `setprop` this stage; read back). A game running (the user's). Then the reply: "YOU, now, three things, ~20 s apart: (1) press the onn remote's Home, count to 2, come back to the game — it should still be running where it was; (2) press the pad's guide / PS button once — the game should stay; (3) press Home and stay away ~15 s, then come back — this one is allowed to restart. Then send 'Stage 3'."
- The read (after "Stage 3" arrives): C1's pass rows (one host session at (1): no `restart_fast`, no `session_ended`; the `surface_lost` row `outcome: held`, `away_ms` < 12000, a `reason`; `surface_hold.held` 1 in the report; (2) `reason: pad_system_key`, the stream stays; (3) today's restart with a `restarted` row). The property cleared (`setprop … ""`) and read back empty.

## Stage 3 — C3 then C2 over the overlay (the user's hand, then unattended ~35 min)

- The reply to "Stage 3" first gives the hand step: "YOU, now: on the onn, Tailscale → Connect; PrivyHub → SETTINGS → Hub host = the hub's Tailscale name → Save; stay on the home 5 GHz Wi-Fi; then send 'Stage 3 go'."
- On "Stage 3 go": the overlay check (connected, the path stated, two devices by count). The driver `home1_2026-11-0x/home1_driver.py` from `cl_b16_driver.py` (unit `privyhub-home1`, STOP `~/privyhub_home1/STOP`), two cells in one launch, E1-PS1-STREAM, window 720 each, the band every 10 s:
  - **C3:** no drop-in beyond `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1` (14 lines): a remote session climbing from 4000 with today's encoder restarts at each step; B33 live. Pass: every `input_release` from a step-up stall reads `method: resume`, `why: no_loss_under_1s`, `held_ms` < 1000; no `LOAD_STATE_SLOT 9` in the game log; the `rewind_needs_loss_config` row.
  - **C2:** drop-in `PRIVYHUB_STEP_IN_PLACE=1` + the `none` line (15 lines): pass — every `transition_done` `in_place: true`, `ssrc_unchanged: true`, `splice_gap_ms` < 40; the encoder log's `B32 in-place step … active on the same stream`; no SSRC change at the steps in the client report and no `client_stall` within 2 s of a step; fail signal `in_place: false` / `in_place_fallback`.
- Launch, confirm C3's PLAYING, exit: "YOU, now: nothing for ~35 min (until HH:MM Eastern). Then put the onn back — Hub host = home value → Save; Tailscale → Disconnect — pair the second pad, and send 'Stage 4'."

## Stage 4 — C4 two pads, C5 the movie drop (attended ~20 min)

- The unit closed; the client back on the LAN; the properties empty.
- **C4:** `setprop debug.privyhub.pad_slots stable` (read back). The reply: "YOU, now: start a two-player PS1 game; press a button on pad B first, then pad A; play 30 s; exit; relaunch; press pad A first this time; play 30 s; then send 'Stage 4b'." Pass: both starts write `pad_slots` `when: start` with the same two `{slot, pad, class}`; the lower controller number is slot 0 both times; `updates_by_player` on slots 0 and 1 only; the remote takes no slot.
- **C5** (on "Stage 4b"): the property cleared; `setprop debug.privyhub.vod_retry 1` (read back); drop-in `PRIVYHUB_VOD_LOG=1`, restart (the game ended first). The reply: "YOU, now: start a movie; after a minute, turn the onn's Wi-Fi off, count to 10, turn it back on. The movie should show 'reconnecting…' and carry on from the same spot within about two minutes. Then send 'Stage 5' with one line on what you saw." Pass: "reconnecting…" then resumed at the position within 150 s, no "Playback error"; `logs/vod_client.jsonl` `vod_error` → `vod_retry`×n → `vod_resumed`; `logs/vod_range.jsonl` the broken request `client_reset` / `broken_pipe` then `bytes=<P>-`.

## Stage 5 — the close, the rule, the record

- The properties cleared and read back empty (all ten); the drop-ins removed; a restart; thirteen lines; `--check` ok; `flags_absent`; `privyhub-diag` active (it survives the restarts — confirm a chunk after).
- **The CONFIRMED rule as CL-B7 §6:** every cell valid and today's behaviours where no flag was set (B33's intended difference aside) → `554ccf61…` CONFIRMED and the pin moved (the three places; tests green); else `fcd924c2…` reinstalled from `cl_b14_installed/`, read back, paired, the user told why.
- **The record `evidence/HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_<date>.md` + dir:** the trip read's summary, the keeper's state, the per-cell tables C1-C5 (met / not met), the user's lines verbatim, the CONFIRMED decision, the APK on the onn named; `KNOWN_ISSUES.md`, ROADMAP lines, `logs/home1_git_status.txt`, the redactor; `CURRENT.md` Next Action: the user's commit; **G-A10..13 in B's words, one plain paragraph each, only for the cells met** (G-A10 `PRIVYHUB_STEP_IN_PLACE=1` the fourteenth line; G-A11 the screen-loss hold on by default; G-A12 stable slots on by default; G-A13 the movie retry on by default + `PRIVYHUB_VOD_LOG=1`); B33 not a question (its off switch `PRIVYHUB_REWIND_NEEDS_LOSS=0`); the guard's return as a later item. The reply: "YOU, now: commit, then answer G-A10..13 yes or no each." Plus the five cells' one-line results.

No sudo, no nft, the Opal read-only, adb for the install, the four `setprop`s named and their clears, and state reads; the overlay hand steps and the Wi-Fi toggle are the user's; no addresses or identifiers anywhere; nothing fetched; nothing deleted but `_cowork_prompt_cap.txt`; thirteen lines and no `e3_flag.conf` at every teardown; nothing adopted; nothing committed.
