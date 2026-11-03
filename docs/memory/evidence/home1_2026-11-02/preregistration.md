# HOME-1: pre-registration (written and hashed before the install, 2026-11-03 ~00:45Z)

Sources: `handoffs/SESSION_B_DONE_2026-10-31L.md` §HOME-1 items 5-7 (B's rows, used as B states them),
`handoffs/HOME-1_TRIP_CLOSE_AND_QUEUE_L_CELLS_TASK.md`, `CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md` §6.

**The candidate:**
- APK `554ccf61a87ad061320740adfa830b6fe726e794dfccbe544873bd621b939902`, from
  `PrivyHub/app/build/queue_l_built/app-debug.apk` → `home1_installed/`, with the same signer as `fcd924c2…`.
- **Predecessor:** `fcd924c28cbf70a85bb9a886caabcb07873eee2d028b6538284fce5a7ae39b96` (`cl_b14_installed/`).
- **The ten properties:**
  - the seven, empty: `restart_guard`, `stall_signal`, `link_notice`, `link_report`, `loss_guard`, `wifi_lock`,
    `opus_decode`;
  - the three new, empty except during their own cell: `surface_hold`, `pad_slots`, `vod_retry`.

## The cells and their pass rows

**C1, the surface loss** (stage 2; `setprop debug.privyhub.surface_hold 1`; the user at the TV):
- **(1) Home, back within ~2-3 s.**
  - One host session: no `restart_fast` and no `session_ended` at the return.
  - The recovery row `"event": "surface_lost"` with `"outcome": "held"`, `away_ms` < 12000 and a `reason`.
  - The report's `surface_hold.held` ≥ 1; the picture back within ~0.5 s; the game paused through the loss.
- **(2) The pad's guide / PS button once:** `"reason": "pad_system_key"`, keys containing `110:pad:…`, and the stream
  stays (no `restart_fast`).
- **(3) Home, away ~15 s:** today's restart and a `"restarted"` row.
- **Off:** `setprop debug.privyhub.surface_hold ""`, read back empty.

**C3, the no-rewind stall** (stage 3; over the overlay at home; B33 live; no `PRIVYHUB_REWIND_NEEDS_LOSS` line;
`PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1` only, 14 lines; E1-PS1-STREAM 720 s):
- Every `input_release` from a step-up stall reads `method: resume`, `why: no_loss_under_1s`, `held_ms` < 1000, then
  `resumed`.
- No `LOAD_STATE_SLOT 9` in the game log.
- One `rewind_needs_loss_config` row at the plugin's start.
- **If no step-up produces a stall ≥ 400 ms in the window,** C3's B33 rows are NOT EXERCISED. Recorded as such, not
  as met.

**C2, the step in place** (stage 3, the second cell of the same launch; `PRIVYHUB_STEP_IN_PLACE=1` + the `none` line,
15 lines; a remote session climbing from 4000; at least two step-ups):
- Every `transition_done` in `adaptive_bitrate_shadow.jsonl` reads `in_place: true`, `ssrc_unchanged: true`,
  `splice_gap_ms` < 40.
- The encoder log reads `B32 in-place step: … active on the same stream`.
- The client report shows no SSRC change at the steps, and there is no `client_stall` within 2 s of a step.
- **Fail signal:** `in_place: false` / `in_place_fallback`.
- **Afterwards:** the drop-ins removed, a restart.

**C4, two pads swapped** (stage 4; `setprop debug.privyhub.pad_slots stable`; two pads; a two-player PS1 title; pad
B first, then pad A; exit and relaunch; pad A first):
- Both starts write `"event": "pad_slots", "when": "start"` with the same two `{slot, pad, class}`.
- The lower controller number is slot 0 both times.
- `updates_by_player` rises on slots 0 and 1 only; the remote takes no slot.
- **Off:** with the property empty, no `pad_slots` row or key.

**C5, the VOD drop** (stage 4b; `setprop debug.privyhub.vod_retry 1`; drop-in `PRIVYHUB_VOD_LOG=1` and a restart; a
movie; the onn's Wi-Fi off ~10 s mid-play, the user's hand):
- "reconnecting…" shows, and the movie resumes at the same position within 150 s, with no "Playback error".
- `logs/vod_client.jsonl` reads `vod_error` → `vod_retry`×n → `vod_resumed`.
- `logs/vod_range.jsonl` has the broken request (`client_reset` / `broken_pipe`, bytes < length), then
  `bytes=<P>-`.
- **Down case** (> 150 s unreachable): `vod_gave_up`, then "Playback error", then Retry. That is a valid run but not
  a pass.

## Validity

A cell is **valid** when all of these hold:
- its precondition held: the property or drop-in read back as set, and the other properties empty;
- the user's action happened (C1, C4, C5), or the driver's window ran to its end (C2, C3);
- the band was 5 GHz;
- the rows it names were written, or their absence is itself the reading.

A cell the user could not do, or a window cut short, is **invalid**, not failed.

## The CONFIRMED rule (CL-B7 §6)

- **CONFIRMED:** every cell that ran was valid, and **today's behaviours hold wherever no flag was set**. B33's
  intended difference (a resume instead of a rewind on a no-loss sub-second stall) is set aside as designed. Then
  `554ccf61…9902` is CONFIRMED and the pin moves in three places: `tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test. The tests must be green.
- **Otherwise:** `fcd924c2…` is reinstalled from `cl_b14_installed/`, read back and paired, and the user is told
  why.
- "Today's behaviours" means:
  - with every new property empty: no `surface_lost` hold, today's restart on a lost surface, no `pad_slots`
    row, today's VOD error path;
  - the existing seven defaults unchanged;
  - `--check` ok and `flags_absent` at the close.

## The reading (only for cells met; otherwise back to B with the rows)

- **C2 met → G-A10:** "Adopt `PRIVYHUB_STEP_IN_PLACE=1` as the fourteenth line? Each bitrate step then keeps the same
  stream (no new SSRC, no ~0.4-s gap)."
- **C1 met → G-A11:** "Turn the screen-loss hold on by default in the next APK (`debug.privyhub.surface_hold`, as B25
  did for the link notice)? A Home press or a system panel of up to 12 s then keeps the session."
- **C4 met → G-A12:** "Turn stable player slots on by default (`debug.privyhub.pad_slots=stable`)? Pads keep their
  player number across launches, and only real gamepads get one."
- **C5 met → G-A13:** "Turn the movie retry on by default (`debug.privyhub.vod_retry`) and adopt
  `PRIVYHUB_VOD_LOG=1`? A dropped movie reconnects and resumes by itself for 2.5 min."
- **C3 is not a question.** B33 is inside the adopted line; `PRIVYHUB_REWIND_NEEDS_LOSS=0` is its off switch if C3
  shows harm.

**Cap:** the detached launch (C3 + C2) ends at its windows' end, or at most 2 h after its start (the driver's cap).
`STOP` is `~/privyhub_home1/STOP`.
