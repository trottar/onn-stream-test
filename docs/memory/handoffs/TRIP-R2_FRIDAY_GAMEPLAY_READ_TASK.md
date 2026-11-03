---
memory_schema: 1
as_of: 2026-10-31
status: TASK HANDOFF — TRIP-R2 (session A, READ-ONLY, now; the user is away at the friend's, may play again today): Friday 2026-10-30's and the night's play (local EDT evening 10-30 → ~01:00 10-31 EDT; UTC 10-30 21:00 → 10-31 05:00), every session, and the severe episodes located, timed and explained from the rows: (1) the restart loop (12 self-restarts in 35 min around 04:00-04:40Z; each ~1 s after a ladder step-up); (2) "inputs took minutes" during a golf title; (3) two-player NFL Blitz; (4) the movie that stopped at ~1:50 and needed a manual continue. The user's words: "overall ran very well, but a few massive issues". Copies only; no restart, no drop-in, no setprop, no adb, no run; the log-keeper untouched. Nothing changed; nothing committed
---

# TRIP-R2 — Friday's play, the four episodes

Read first: the keeper's copies (`evidence/trip_2026-10-30/raw/` by file and rotation; `samples/overlay.jsonl`, `session.jsonl`) and the live logs for anything newer; `G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` §2-§3 (the per-session method), `UX_R3_…` §1 (the hitch reader), `UX_R4_…` §1 (the ±60-s per-second view), `B11_…` / `B15_…` / `B17_…` (the client's self-restart: what triggers `restart_fast` on the client side — the surface loss, the silence, a stall? **name the trigger from the code**), `B7_…` / `B9_…` (the stall signal: 150 at the client, 400 at the host), `B28_…` / `G5_S3_REMOTE_LADDER_…` (the remote ladder's transitions: does a step-up change the encoder's SPS / restart the encoder, or only the bitrate?), `CTRL_L1_…` (per-player updates), `TRIP_PREP_2026-10-29.md` (in force: thirteen lines, APK `fcd924c2…`, the guard off).

**My own read of the keeper's files, 04:00-04:38Z, for Code to confirm or correct:** the overlay direct in every sample; the onn at −54 dBm on 5785 MHz; post-FEC loss ≤ 10 / min; rendered 59-60 fps whenever running; **12 `session_ended_reset` rows in the ladder log and the recovery log's pattern `client_stall` (419-464 ms) → `desync_pause` → `resumed via stall_end` (30 ms) → ~1-2 s later `session_ended` + `restart_fast` + `session_started`** (04:19:18, 04:30:10; the 04:37:43 stall 1 s after the 4000 → 5000 transition at 04:37:42; the 04:28:37 transition 5500 → 6000 then the stall at 04:30:10); the rung at 4000 most of the window (`RECOVERY_PROBATION`).

## 0. Preserve, then the whole evening

- Assemble into `evidence/trip_r2_2026-10-31/copies/` with `manifest.sha256` (the keeper's dir never written to).
- **Every client session 21:00Z 10-30 → 05:00Z 10-31** (and any since): start, length, core and the title's class + a short tag (no full titles), players sending state, path, the rung history with every transition and its reason, `session_ended_reset`, loss, RTT if any row carries it, rendered, resyncs, pauses, holds, stall rows, `restart_fast` rows, hitch s and silences per 10 min, underruns, the audio starvation events. The per-10-min table across the evening (UX-R3), with the user's four episodes marked where the rows place them.

## 1. The restart loop (the largest)

- Every `restart_fast` / `session_ended` not preceded by `session_end_bye` (the client's own restarts, not the user's exits) across the evening: its time, what preceded it in the 5 s before (a stall and its age, a hold, a ladder transition and its Δt, an output gap, a resync, an SSRC change), the rung before and after, and the client's `restart_cause` fields in its report.
- **From the code: what makes the client restart after a ~420-ms stall that the host resumed in 30 ms** — the client's own reconnect threshold? the decoder's reconfiguration on the new rung's SPS/PPS? the restart guard's path? Name it, with the file and the condition. **And whether a remote-ladder step-up restarts or reconfigures the encoder** (a new SPS/PPS, an IDR burst) in a way the LAN ladder does not.
- Count: restarts per hour across the evening; the hours that had none (the "ran very well" stretch) against the hours that cycled; what differed (the rung reached? a transition rate? the loss?).

## 2. "Inputs took minutes" (golf)

- Find the golf title's sessions (the class tag). For the stretch the user describes: the per-second view (UX-R4) — the controller updates per player per second arriving at the host, the control gaps, the holds and pauses, the stream's state (PLAYING / paused / restarting), rendered frames at the client, output gaps. **The question:** were inputs delayed in flight (gaps on the uplink), swallowed by a hold / pause, or was the stream simply down or restarting while the user kept pressing? State which from the rows, with the longest span in which a pressed input could not have reached a running game.

## 3. Two-player NFL Blitz

- As `TRIP-R1_MULTIPLAYER_BLITZ_READ_TASK.md` §1-§3 (its prompt was never run): the Blitz session(s) by the launch row and ≥ 2 players; single vs two-player on the link, host and per-player controller columns; the pad setup for port 2 from the config (read-only). One verdict.

## 4. The movie that stopped at ~1:50

- From the companion journal and the range server's requests in the keeper's copies: the VOD session(s) of the evening (the class only), the request timeline around 1 h 50 min into playback (or 1:50 min:s — both checked): a gap in range requests, a connection reset, a companion restart, an overlay path change, the hub's load, the keeper's `session.jsonl` state. **Which side stopped:** the server (no response / reset), the link (requests arriving, responses late), or the player (no request for N s). State what the record can and cannot see (the onn's player logs are not on the hub).

## 5. The reading

- Per episode: the cause as the rows show it, one plain paragraph each; what the system did to adapt and why it was not enough; **the fix each needs**, named as a B item: (1) the client must not restart on a sub-second stall, and a step-up must not produce one; (2) inputs during a pause / restart; (3) the Blitz pad setup; (4) the VOD stop. And the one thing the user can do today if they play again (the 4000 pin, `_cowork_prompt_cap.txt`, if the loop returns — or nothing if it has not).
- `evidence/TRIP_R2_FRIDAY_GAMEPLAY_2026-10-31.md` + `trip_r2_2026-10-31/` (the copies, the tables, the per-second views, `redact_check.txt`, `manifest.sha256`); `docs/KNOWN_ISSUES.md` (the four, one line each, at the top); `logs/trip_r2_git_status.txt`; `CURRENT.md` Next Action (the user's commit when home; queue L for B: the four fixes; the permanent diagnostics keeper). Exit. **The reply begins "YOU, now:"** (one line: what to do today, or "nothing"), then the four episodes, one short paragraph each, cause first.

No sudo, no nft, the Opal read-only, **no adb (off-LAN), no restart, no drop-in, no setprop, no run, no game launched; the log-keeper and its files untouched**; copies only; no addresses, names or identifiers (the friend's network and the tailnet as placeholders; titles as class + tag); nothing fetched, deleted or moved; nothing adopted; nothing committed.
