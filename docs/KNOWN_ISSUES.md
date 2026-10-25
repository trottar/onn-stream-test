# Known issues and deferred work

## 2026-10-24 G4-S4, off-site free play: Home auto-resumes (no pause screen, the rung back at the floor); the onn left the tailnet for ~8 min once; underruns 8-20 / min — OPEN (to B / a watch item)

(`docs/memory/evidence/G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` §6, §8, §10)

- **The stack on a WAN path held: 0 false holds and 0 uplink silences ≥ 250 ms** in 100.1 min of play.
  - That is direct only, one evening. The bound is < ~0.3 false holds / 10 min (95 %).
  - The relayed path in play is unmeasured; WAN-R1 reads the earlier sessions.
- **Home (the user: "it didn't pause … I'm use to at home where the pause screen shows up"):**
  - the hold fires ~1.06 s after the Home (save at +0.40 s), the game unattended until then;
  - the return is a new client session: the hold releases and the game resumes with no pause screen and no rewind;
  - the ladder restarts at the floor (7000 → 4000, ~14.5 min back to 7000 under the four lines).
  - Likely G-A4's design, not the WAN; to be confirmed on the LAN. **To B:** should Home pause and wait (the old
    pause screen), and should a Home return keep the rung?
  - **Queue H (2026-10-25):** B22 shortens the return itself (the start answered before the teardown, the
    release at the new stream's first fresh frame; NOT ADOPTED). Pausing at Home and keeping the rung were not in queue
    H: they stay the user's question.
- **The onn left the tailnet once:**
  - no-peer 19:38:33-19:45:50Z, ~1 min after it went idle and ~26 s after a companion restart;
  - a second restart was followed by a brief relayed reading only.
  - The cause is not in the hub's files. **Open.**
- **Underruns, in play:** 8.0 / min under the four lines, 20.2 on the ten-line afternoon sessions at 7000 (G4-S3 3.4).
  Audio packets lost 38 / 30 / 11 in three sessions. A watch item, with the Opus underrun item below.
- **Also:** the client sat "reconnecting" for 21 min after the closing restart (session 12's report is that tail).
  Known, as G4-S3 §5.

## 2026-10-21 LAN-R1: the ladder does not step down on loss on the LAN — OPEN; a rule BUILT behind `PRIVYHUB_LAN_LOSS_RULE=1`, NOT ADOPTED; BENCH-R1 (2026-10-22): the rule back to B, the input hold not a candidate until its trigger is fixed, the death reproduced on the bench; BENCH-R2 (2026-10-22): the Wi-Fi lock not the cause, the hold + rewind + stall stack not a candidate, APK cb0935c8 CONFIRMED; queue D (2026-10-22): the ownership at the return, the stall threshold 400 + rewind SNES-only, the client's loss guard BUILT, NOT ADOPTED; BENCH-R3 (2026-10-22): the stack not a candidate on SNES (snes9x's hold-path rewind reads PAUSED), the PS1 state path works, the loss guard a candidate (the user's call), the onn on 2.4 GHz where the Opal sampler did not look, APK bf5114a2 CONFIRMED; LINK-R1 (2026-10-23): on 5 GHz 0 uplink silences / 0 hitch s per 10 min — the band was most of the flapping; queue E (2026-10-23): the self-restart guard, `state` for every core + the stall resume, the link report on by default + G-A3 prepared, the link notice BUILT, NOT ADOPTED; CL-B10 (2026-10-24): the band settled (2.4 GHz the flapping), the notice shown (the user's word); queue F (2026-10-24): the guard on every path and the stall resume at the client's first frame BUILT, NOT ADOPTED; CL-B11 (2026-10-24): APK e2db0aa0 CONFIRMED, the fast ready resumes 133-458 ms after the return and the guard carries a new-instance return — each back to B with one row; queue G (2026-10-24): both rows answered, the client defaults on, the stack as one line (`PRIVYHUB_LINK_RECOVERY=1`) and G-A4 PREPARED — BUILT, NOT ADOPTED; CL-B12 (2026-10-24): APK 20e3e339 CONFIRMED with every client property empty, the umbrella alone gives every behaviour row (resume 108-349 ms, 0 saves outside, the bye), both Home returns via the start (create→start 96-280 ms, 0 underruns after) — back to B on two narrow rows (a config log line; one 30-underrun interval at a Home press); G-A4 the user's call

**The standard (the user, 2026-10-21):** "This product needs to work at any house especially lan as long as the Internet
is over 50mb/s." Record: `docs/memory/evidence/LAN_R1_LOSS_STEPDOWN_2026-10-21.md`.
- **Why 7000 throughout Sunday (UX-R1):**
  - Every decrease bar of the adopted `live` ladder carries an fps term (capacity_mild: fps < 57 on ≥ 4 of 5 AND
    lost ≥ 50 on ≥ 3).
  - Sunday's loss came as < 50 per report from 04:56 to 05:05, then as single-report bursts (05:06 491, 05:10
    5,376, 05:20 279, 05:21 899), with fps ≥ 57 on most reports.
  - At 05:21 both terms reached their counts, never in the same 5-report window. The one acted step was
    `capacity_mild` at 05:11:01.
  - The replay through the real controller reproduces both evenings exactly.
- **G5-S2's rules** are not gated on the path, and add nothing: R3.1 once, at 05:11, on the ladder's own tick.
- **G8-S1 showed the same gap:** loss-1 and loss-5 (809 lost/min, fps 52.6) held 7000.
- **Built, not adopted:** one rung down when 2 consecutive 10-s windows each hold ≥ 4 FEC-unrecoverable groups
  (the telemetry carries them; the ladder did not read them), through every gate, floor 5000.
  - Replayed: Sunday 7000→6000 at 05:03:05Z (~3 min before the 05:06 burst), →5500 at 05:06:07, →5000 at 05:10:48.
  - 0 asks in every clean window on file (CL-B5 A/B/L, CL-B6, CL-B7 ×3, G4-S3). Last night, 2 asks, refused by the
    60-s session-age guard.
- **Caveats:**
  - Post-FEC loss does not separate Sunday's early minutes from the clean windows. The unrecoverable groups do only
    at an edge cell, chosen in sample.
  - The rule also steps down under random loss (G8-S1 loss-1: 5000 within 9-11 min), where a lower rate does not
    help.
  - It does not address last night's death (UX-R3: 04:54:55-04:54:59Z, a 4-s bidirectional drop). No 2 × 10-s run
    reached ≥ 4 there, so it made no ask.
- **Next (session A):** the shim's loss-1 / loss-5 / burst at 7000 with the flag on vs absent, then the user's room.
- **Now built against it and UX-R3's death (2026-10-22, session B queue B1-B3; none adopted, no live run):**
  - **B1, the bench reproduces the death:** `PRIVYHUB_IMPAIRMENT=blackout-4s@both,every=120s` darkens the downlink
    (`@post-fec`) *and* the uplink (controller packets, heartbeat, client-health at the host's receive points) for
    4 s every 120 s on one clock. `@down` is the downlink only.
    - In process: 4.0-s dark spans; the real controller loop went silent and recovery's silence callback fired once
      per blackout; both directions within 14 ms.
    - Record: `docs/memory/evidence/B1_SHIM_BLACKOUT_BOTH_2026-10-22.md`.
  - **B2, the game freezes with the player:** `PRIVYHUB_INPUT_HOLD=250` pauses the core after 250 ms of controller
    silence, through recovery v2's own pause (reason `input_hold`, one pause row; v2's 5.35-s path takes over a
    longer one). The first packet back resumes it.
    - The client sends ~430 packets/s regardless of input, so a silence is the link.
    - Baseline unattended frames (the core running) per 10 min: Sunday 684, last night 142; the death 84.
    - Record: `docs/memory/evidence/B2_INPUT_HOLD_2026-10-22.md`.
  - **B3, the link beside the loss:** the client reports RSSI / link speed / band (`debug.privyhub.link_report=1`),
    and the host records `link.*` (`PRIVYHUB_LINK_REPORT=1`). APK `e4d02354…` pinned, not installed.
    - Record: `docs/memory/evidence/B3_CLIENT_LINK_REPORT_2026-10-22.md`.
  - **B4, the blackout costs nothing (2026-10-22, session B):** `PRIVYHUB_INPUT_HOLD_REWIND=1` (with the hold) rewinds
    the core on the hold's release by the frames it ran without the player before the pause landed (clock × 60 from
    the last packet to the confirmed pause, less a measured 4-frame lag; cap 30), before the resume. RetroArch 1.22.2's
    rewind is on in the launch config under the flag only (buffer per core from a real savestate: snes9x 26 MiB, PSX
    513 MiB). A handover to v2 is rewound too, so a 20-s outage costs nothing either.
    - Fake-core tests: back at the onset ± 1; a failed rewind still resumes. Flag absent = B2 (AST, config hash).
    - Open (A, BENCH-R2): the CPU per core with rewind on; whether Beetle PSX HW's hardware renderer rewinds at all.
    - Record: `docs/memory/evidence/B4_INPUT_HOLD_REWIND_2026-10-22.md`.
- **ML-R1 (2026-10-22, offline): a learned hitch early-warning detector does not beat the 250-ms silence rule at a usable operating point** (+2.5 points at matched duty). Its hashed bar read "met" only because my false-alarm definition let an always-on alarm pass. No flag; nothing on the host side precedes the death. Record: `docs/memory/evidence/ML_R1_HITCH_EARLY_WARNING_2026-10-23.md`.
- **BENCH-R1, measured (2026-10-22, session A; 8 / 8 cells valid, host gates met in all; nothing adopted):**
  - **The death reproduced** (`blackout-4s@both,every=120s`): all four shape terms in all 5 blackouts, harsher than
    the death (4.0 s dark, ~4.2-s output gaps, ~3,300 lost after FEC). It ran 85.0 unattended frames (core running)
    per blackout, against the death's 83.8.
    - Disclosed: B1 lets the client's desync POST through, so v2 paused the core ~1.5 s into each bench blackout. A
      real drop runs unheld up to ~234 frames.
  - **The hold (`PRIVYHUB_INPUT_HOLD=250`): NOT a candidate until its trigger is fixed (the hashed reading).**
    - **Cell 8, a clean link: 18 holds in 11.5 min.** These are the room's own ≥ 250-ms uplink silences; the shim
      dropped nothing.
    - **Cell 6: −73 % per blackout, against the ≥ 90 % bar.** In the four held blackouts, 6 frames (−93 %).
    - The fifth was skipped by the 6-holds-per-60-s cap, spent a minute earlier on the room's flapping uplink.
    - v2's `client_output_silence` took every blackout hold over ~1 s in. No blackout ended in a release, and the core
      resumed 6 s after a 4-s blackout began.
  - **The LAN loss rule: back to B (the hashed reading).**
    - Cells 2-4 stepped 0.9-1.5 min into the stream (predicted 3-4) and reached 5000 at 5.2-8.2 min (predicted
      8-11).
    - Cell 4 stepped ~2 min before G8-S1's `capacity_mild` point (predicted 2 s before).
    - Disclosed: on LAN-R1's own clock (from the driver's cell start), cell 2 matches.
  - **Downlink-only (`@down`):** 0 unattended frames. The game ran ~2.2-2.6 s without a picture before v2 paused it,
    and the 4th recovery escalated 7000→5000.
  - Record: `docs/memory/evidence/BENCH_R1_BLACKOUT_AND_LOSS_CELLS_2026-10-22.md`.
  - **Next (for the user):** commit; B takes the hold's trigger (false holds, the cap, the v2 handover) and the rule's
    timing; B1's desync gate on `@both`. Then CL-B8 (B3's APK), then BENCH-R2 (the hold + rewind), as sketched by B.
- **Built against BENCH-R1's findings (2026-10-22, session B queue C: B5, B6, B7, B1b, LAN-R2; none adopted, no live
  run, nothing committed):**
  - **B5, the Wi-Fi lock:** the client held **no Wi-Fi lock and no wake lock** during a stream (settled from the
    code). It is now built behind `debug.privyhub.wifi_lock=<low_latency|high_perf>`, acquired at the session's
    start and released at its end and on pause.
    - The idle LAN's 250-ms silences (cell 8: 15.6 / 10 min) are its A/B question.
    - Record: `docs/memory/evidence/B5_CLIENT_WIFI_LOCK_2026-10-22.md`.
  - **B6, the hold's trigger from the data:** **H = 950 ms** under `PRIVYHUB_INPUT_HOLD_B6=1` (`1` / `on`). That is
    the smallest H with ≤ 1 silence per 10 min on each clean session.
    - **The idle room makes 800-1,336-ms silences, so length alone cannot catch the death's 342-967-ms gaps** (950
      catches 1 of 5).
    - The rewind cap is 62. The cap counts released holds only, with a 10-s disarm.
    - A hold v2 took over resumes at the first fresh heartbeat after the return.
    - A late client ready after a hold resume is no longer a new session (it reset the ladder).
    - Record: `docs/memory/evidence/B6_INPUT_HOLD_TRIGGER_2026-10-22.md`.
  - **B7, the stall signal:** with `debug.privyhub.stall_signal=1` / `PRIVYHUB_STALL_SIGNAL=1`, the client sends a
    stall datagram while it cannot show the game: an old output, or its black "Reconnecting" overlay.
    - The host pauses (`client_stall`) and resumes with B4's rewind when the client shows gameplay again.
    - That is cell 7's fix, and it closes the hold's release behind the client's black overlay.
    - The APK (B5 + B7) `cb0935c8…1080` is pinned, not installed.
    - Record: `docs/memory/evidence/B7_CLIENT_STALL_SIGNAL_2026-10-22.md`.
  - **B1b:** `@both` now also drops the client's desync while dark (start / stop / ready pass; why stated).
    Record: `docs/memory/evidence/B1B_SHIM_GATE_2026-10-22.md`.
  - **LAN-R2:** **no host signal on file tells Sunday's pre-burst loss from 1 % random loss.**
    - The rule is renamed to its purpose: `PRIVYHUB_LAN_LOSS_RULE=bidir` steps down when the link is bad in both
      directions (unrec AND ≥ 2 uplink silences ≥ 400 ms in each window).
    - Replayed: 0 asks in BENCH-R1 cells 1-4, every clean window and last night; Sunday 05:06:09Z.
    - Record: `docs/memory/evidence/LAN_R2_LOSS_RULE_RETHOUGHT_2026-10-22.md`.
  - **Next (session A):** BENCH-R2, as in `handoffs/SESSION_B_DONE_2026-10-22C.md`.


- **BENCH-R2, measured (2026-10-22, session A; 15 / 15 cells valid, host gates met in all; nothing adopted):**
  - **The Wi-Fi lock is not the cause of the uplink silences.**
    - ≥ 250-ms silences per 10 min: none 41.8, `low_latency` 151.6, `high_perf` 29.5 (bar −80 %).
    - The room changed across that hour (~1,100-1,300 lost/min after FEC with no shim in the first two cells).
    - With the lock on, every later cell read 9-28, as BENCH-R1 cell 8 did without it.
    - B6's H (950) stands.
  - **The hold + rewind + stall stack is not a candidate.**
    - `@both` with the stack: ~45 unattended frames per blackout (bar ≤ 5; BENCH-R1 cell 5: 85, raw ~226).
    - The stall takes the hold over at the return, so the ~57 pre-hold frames are never rewound. The core resumes
      2-4 s after the link's return; without the stall pair, 1.1 s.
    - Clean hour: 2.6 stall pauses per 10 min at 150 ms (bar ≤ 2), 0 at 400.
    - `@down`: the pause 0.15-0.21 s after the client's last frame (met; BENCH-R1: ~2.4 s of game without a
      picture). But 77 stall pauses per 10 min on that hour's flapping link.
  - **Beetle PSX HW's rewind is not confirmed:** 118 of 123 rewinds failed B4's after-check (the core read PAUSED). The
    buffer is 1,074 MB, +16.6 points of a core and +1.0 GB RSS. snes9x: +0.3 points, +29 MB; its rewind was not
    exercised (no hold on SNES).
  - **The bidirectional LAN rule: 0 asks, 0 steps** on loss-1 / loss-5 / burst (its out-of-sample check).
  - **The user saw corrupted pictures** ("NPC models were missing faces … a rainbow like bar at the top") in the
    loss-1 cell (16:05-16:17Z: 50-99 lost / 14-30 unrecoverable groups per minute after FEC).
    - The client dropped 488 incomplete frames and kept decoding the following ones; no error counter moved. The same
      mechanism shows with the previous APK. A B question: freeze to the next IDR, or count it.
  - **APK `cb0935c8…` CONFIRMED** and pinned (`e1_suite` `EXPECT_APK`, `c3_l4_nft_night`); `93d29b4a…` preserved.
  - Record: `docs/memory/evidence/BENCH_R2_LOCK_HOLD_STALL_CELLS_2026-10-23.md`.
- **Built against BENCH-R2's findings (2026-10-22, session B queue D: B8, B9, B10; none adopted, no live run):**
  - **B8, the ownership at the return** (`PRIVYHUB_INPUT_HOLD_B8=1`, with the hold + B6 + the stall signal): BENCH-R2
    b1's rows show the client's gate `ready` resumed the stall-owned pause without the rewind, and a gate-bit stall
    then paused again. Now the handover carries the hold's rewind (pre-hold + the client's frames before the silence),
    the first fresh heartbeat after the return resumes (`hold_return_stall`), gate stalls over fresh output are
    ignored, the late `stall_end` is a logged no-op; B4's cap 72. 14 tests; B2 / B4 / B6 / B7 unchanged and green.
    Record: `docs/memory/evidence/B8_HOLD_STALL_OWNERSHIP_2026-10-22.md`.
  - **B9:** `PRIVYHUB_STALL_SIGNAL=1` now acts at **400 ms** (150 by number). `PRIVYHUB_INPUT_HOLD_REWIND=1` rewinds
    **snes9x / bsnes only** (Beetle PSX HW: no buffer, `rewind_skipped`); `all` = B4; `state` = a scratch
    `SAVE_STATE_SLOT 9` at a 400-ms silence loaded into a running core at the release (D-BASE-R3C's paused-load
    caveat), the PS1 path for A to measure. 13 tests. Record:
    `docs/memory/evidence/B9_STALL_THRESHOLD_AND_REWIND_CORES_2026-10-22.md`.
  - **B10, the corrupted pictures:** settled — after a dropped access unit the client queues the next P-frames,
    decoded from a lost reference until the next IDR (every 15 frames), and nothing counts them; **the host cannot
    force an IDR on demand** (ffmpeg's GOP is fixed at launch; the only path is a restart, 287-318 ms, longer than the
    ≤ 250-ms wait). Built: `debug.privyhub.loss_guard=1` holds non-IDR frames until the next IDR (the last good frame
    stays, cap 600 ms) and sends one `keyframe_request`; `=count` counts only; `frames_after_dropped_reference` in the
    report and the heartbeat; `PRIVYHUB_LOSS_GUARD=1` counts / rate-limits the requests (today they force nothing).
    JVM 99 / 99, host 10. APK (B5 + B7 + B10) `bf5114a2…cf73` pinned, NOT installed. Record:
    `docs/memory/evidence/B10_CLIENT_LOSS_GUARD_2026-10-22.md`.
  - **Next (session A):** BENCH-R3 on snes9x with the link report on, then CL-B9 (the loss guard, the user
    watching), as in `handoffs/SESSION_B_DONE_2026-10-22D.md`.
- **BENCH-R3, measured (2026-10-22, session A; 6 / 6 cells valid, host gates met in all; nothing adopted):**
  - **The stack is not a candidate on SNES.**
    - `@both` (A): one hold per blackout at 0.95-0.97 s, but all 7 hold-path rewinds (59-60 frames, ~1 s each) failed
      B4's after-check (snes9x read PAUSED).
      - So 47.5-48.7 unattended frames per blackout (bar ≤ 5), as BENCH-R2's b1 / b2.
      - The resume came 2.06-3.13 s after the return, via the gate's ready in 4 of 5.
    - B's 2-3-frame `stall_end` rewinds on the same core passed 4 / 5. So the hold path's method or after-check is the
      suspect, not the core.
    - `@down` (B): the pause 420-428 ms after the client's last frame in 4 of 5 blackouts, 484 in one (bar 0.40-0.46).
      Recovery v2 resumed each blackout's pause (an encoder restart in 3 / 5, one ladder step 7000→5000); only a second,
      in-gate pause got a rewind. Stall pauses outside the blackouts 0 (BENCH-R2 c1: 77 / 10 min at 150).
    - Clean (C): 0 false holds, 0 stall pauses (met).
  - **The PS1 savestate fallback works (D):** a save 403-408 ms into each blackout, the load played in 5 / 5, 34-36
    frames restored, net 24 per blackout, B8's resume in every one. It joins nothing: the stack is not a candidate.
  - **The loss guard is a candidate (the user's call):** E-on held 3,010 frames = its counter's 3,010, 0 timeouts, max
    wait 501 ms; the requests force nothing.
    - Costs: freezes up to ~0.5 s instead of corrupted frames; 125.7 hitch s / 10 min against 68.8 off (104.3 outside
      a house cluster); 55.2 against 57.8 fps.
    - E-off's counter read 462 / min (expected ~300), part of it the house's loss.
    - No watch.
  - **The link:** the onn streamed on 2.4 GHz channel 1 (802.11n, RSSI −67…−69, tx 108-135 / rx 81-162 typical).
    - The Opal's 5 GHz `wlan1`, which the O1 sampler reads, had no station in 18 rounds; channel 1 is the Opal's
      `wlan0`.
    - E-on's cluster of 42 uplink silences (21:42:20-21:43:25Z) coincided with the onn's tx rate falling to 27-81 Mbps.
    - The downlink loss bursts (D 21:14 / 21:16 / 21:19Z; E-off 21:27Z, two heartbeats 20-68 s late) coincided with no
      RSSI change beyond 1 dB.
    - Coincidence in time, not cause.
  - **APK `bf5114a2…cf73` CONFIRMED** and pinned; `cb0935c8…` preserved.
  - Record: `docs/memory/evidence/BENCH_R3_SNES_STACK_AND_LOSS_GUARD_2026-10-23.md`.
  - **Next:** the user's call on the loss guard; the Opal's `wlan0` read beside a stream (is the onn on the Opal?); B
    on the hold-path rewind's after-check and `@down`'s ownership.
- **UX-R4 (2026-10-23, the user's "severe lag … I saved at the spot", Zelda on snes9x, the eight lines, APK
  `bf5114a2…`, no link report):** the mark is the 05:01:30Z save, after a 41-s storm (05:00:40.9-05:01:20Z) of 19
  uplink silences ≥ 250 ms (9.5 s silent, the longest 1.4 s), with downlink loss ×9 beside it and the host steady
  (both directions, uplink-dominant). 47 s after the resume came a 4.9-s two-way drop (05:03:39.8Z) the client restarted
  its stream from. It was the same quarter-hour after 00:50 EDT as UX-R2's step and UX-R3's death. Record:
  `docs/memory/evidence/UX_R4_SAVED_AT_THE_LAG_2026-10-23.md`.
- **The band (LINK-R1, 2026-10-23):** on 5 GHz (ch 36, −68 dBm) **0 uplink silences ≥ 250 ms and 0 hitch seconds per
  10 min**; on 2.4 GHz 16-22 and 20 in every room (BENCH-R1 cell 8, BENCH-R3 C). The onn had been on 2.4 GHz at
  −68 dBm all month and nothing told anyone; the link report was off on every night that mattered. Record:
  `docs/memory/evidence/LINK_R1_5GHZ_CHECK_2026-10-23.md`.
- **Built against it (2026-10-23, session B queue E: B11-B14; none adopted, no live run, APK `da09e154…6cf` pinned, not
  installed):**
  - **B11, the self-restart:** settled — the client starts a stream only from `surfaceCreated`; a lost surface caches
    the report (never posted), stops the whole pipeline including the controller sender (so UX-R4's 4.9-s "uplink
    silence" is at least partly the client's own), and the next start posts no stop; the host's start restarts its
    audio at sequence 0 while the new receiver had locked onto the old stream, so every frame read LATE (the underrun
    storm). `debug.privyhub.restart_guard=1`: the old report and `native-stream-stop` before the start, the audio
    rebuilt after the host's start, `restart_cause`. Record: `docs/memory/evidence/B11_CLIENT_RESTART_GUARD_2026-10-23.md`.
  - **B12:** `PRIVYHUB_INPUT_HOLD_REWIND=1` now means `state` for every core (`rewind` = B9's allow-list);
    `PRIVYHUB_STALL_RESUME=1`: a save at the stall, one resume with that load (at `stall_end` or the client's gate
    `ready`), v2's encoder restart held off until 5 s, then v2 once. Record:
    `docs/memory/evidence/B12_STATE_FOR_ALL_AND_STALL_RESUME_2026-10-23.md`.
  - **B13:** `debug.privyhub.link_report` absent now means ON in the client; the ninth adopted line
    (`PRIVYHUB_LINK_REPORT=1`) PREPARED only: `docs/memory/patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md`. Record:
    `docs/memory/evidence/B13_LINK_REPORT_DEFAULT_ON_2026-10-23.md`.
  - **B14, the "any house" notice** (`debug.privyhub.link_notice=1`): on 2.4 GHz, or RSSI ≤ −72 dBm / tx ≤ 54 Mbps for
    10 s, "Wi-Fi: 2.4 GHz — Use your router's 5 GHz Wi-Fi for this box." on the stream and the diagnostics page; the
    host logs `link_notice_shown` / `_cleared`. Record: `docs/memory/evidence/B14_LINK_NOTICE_2026-10-23.md`.
  - **G-A3 (2026-10-23): `PRIVYHUB_LINK_REPORT=1` ADOPTED, the ninth line.**
  - **CL-B10 (2026-10-23/24, 4 / 4 cells valid; APK `da09e154…` CONFIRMED):**
    - **The band, settled in one hour:** 2.4 GHz gave 168 silences ≥ 250 ms and 149 hitch s per 10 min; 5 GHz minutes
      apart gave 0 and 0-9. The user, on 2.4 GHz: "It's running like absolute shit right now".
    - **B12's stack: back to B,** one row missed in each cell.
      - `@both`: the resume 2.13 s after the return in 1 of 5.
      - `@down`: one `encoder_restart` in 1 of 5.
      - Costs: net 24 frames per two-way drop, a save per stall, the picture frozen 3.5-7.2 s per 4-s drop.
    - **B11's guard: back to B.** A Home press gave no old report and no `session_ended` before the new start, and a
      null `restart_cause`. Then 2,418 underruns in 28 s.
    - **B14's notice:** raised on 2.4 GHz at the first heartbeat (reason 1) and cleared on 5 GHz. "Shown" on screen
      awaits the user's word.
    - Record: `docs/memory/evidence/CL_B10_RESTART_GUARD_STATE_STALL_NOTICE_2026-10-23.md`.
  - **The notice: shown.** The user's word (2026-10-24, verbatim): "I saw that box". CL-B10's gate is MET, and B14 works
    as built. Whether it becomes a client default is the user's call.
  - **Queue F (2026-10-24, session B; nothing adopted, no live run):**
    - **The guard: still OPEN, rebuilt (B15, the same `debug.privyhub.restart_guard=1`).**
      - Why it missed: cell 1's start ran in a **new activity instance**. The old process was gone after Home, and the
        activity was re-created on the return. B11 kept its pending in the activity object only, so the new guard was
        empty. The property read 1.
      - Now: the pending is kept in a private file. Every start flushes it (report, stop, start; audio rebuilt), and
        `restart_cause.trigger` reads `surface` / `recreate` / `process`. A recreation hands over instead of racing its
        stop.
      - JVM 122 / 122 (125 / 125 with B16). Record: `docs/memory/evidence/B15_RESTART_GUARD_ALL_PATHS_2026-10-24.md`.
    - **The resume: still OPEN, rebuilt (B16, inside `PRIVYHUB_STALL_RESUME=1` / `PRIVYHUB_INPUT_HOLD_REWIND=1`).**
      - Why it was slow: `@down`'s ready waited on the client's 500-ms gate (~2-3 s after the frames return); v2's 5-s
        hold expired first, and blackout 5's restart acted on a pre-return heartbeat. `@both` waited on the 2-s
        heartbeat. B12 saved at every 150-ms client stall.
      - Now: the host's start response arms the client's ready at its first decodable frame. The stall save comes only
        at ≥ 400 ms. v2 acts only while the newest stall datagram says stalled.
      - Tests: 301 ms after the return in both, no restart, no handover, 0 saves under 400 ms; net 9 → 24 on `@down`
        (stated).
      - Record: `docs/memory/evidence/B16_STALL_RESUME_SPEED_2026-10-24.md`.
    - **APK (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16) `e2db0aa0…6b33`, pinned, NOT installed;** `da09e154…` stays
      CONFIRMED.
  - **CL-B11 (2026-10-24, 3 / 3 cells valid; APK `e2db0aa0…` CONFIRMED and pinned):**
    - **B16's fast ready: back to B with one row.** In all 10 blackouts the resume came via the client's ready **133-458
      ms after the return**, with no `encoder_restart`, no v2 handover, and the stall save at 429-433 ms before the
      pause. Net 24 / 26. The picture was held 4.13-4.47 s per 4-s drop (CL-B10 3.5-7.2 s).
      - The miss: **one silence save at each session's end** (~205 ms before `session_ended`), against "zero saves
        outside the blackouts" (CL-B10: 4).
    - **B15's guard: back to B with one row.** A Home press and a return through PrivyHub's menu (a new stream activity
      in the live process; the events read confirms it):
      - the old report and the stop came before the new start, `restart_cause.trigger` `recreate`, `away_ms` 21,356;
      - 52 underruns in the new session's 441 s;
      - the miss: **one 2-s interval of 221 underruns** before the guard's restart.
      - The user: "I had to click into the game but seemed to be at same spot".
    - **On 5 GHz, cell 1:** 4.4-5.6 silences and 6.9-12.9 hitch s per 10 min (CL-B10 cell 1: 0 / 0).
    - Record: `docs/memory/evidence/CL_B11_GUARD_AND_FAST_READY_2026-10-24.md`.
  - **Queue G (2026-10-24, session B; nothing adopted, no live run):**
    - **B17, the guard's 221-underrun interval.** The new instance's audio started on the host's old stream and starved
      when the host's stop tore it down. That stop took ~2.3 s, and the host's start runs the same teardown itself.
      - Now (`restart_guard`): the audio is held until the guard's start is answered. The old session's end rides in
        the start (`native-stream-start?…&guard_end=1`; the host runs the stop's bookkeeping at the start's entry, with
        no separate stop), and the report follows it. `restart_cause.create_to_start_ms` is recorded.
      - JVM: the start goes out 670 ms after creation with a 300-ms-per-post host.
      - Record: `docs/memory/evidence/B17_GUARD_AUDIO_ORDER_2026-10-24.md`.
    - **B18, the save at each session's end.** It fired at 400 ms, before the client's report (+154-181 ms) and stop
      (+205-207).
      - Now: a finishing client says `bye` (`PHS1` kind 3) before its sender stops, and the owner (`state` path) saves
        and holds nothing after it, nor in a non-PLAYING state, nor when the stream's sender has gone flat 250 ms.
      - Record: `docs/memory/evidence/B18_NO_SAVE_AT_SESSION_END_2026-10-24.md`.
    - **B19, the client defaults on.** `debug.privyhub.stall_signal` and `restart_guard` are on unless `0`;
      `link_notice` stays opt-in. Today's host counts a stall datagram as a bad controller packet only.
      - **APK (B5 … B19) `20e3e339…563d`, pinned, NOT installed;** `e2db0aa0…` stays CONFIRMED.
      - Record: `docs/memory/evidence/B19_CLIENT_DEFAULTS_ON_2026-10-24.md`.
    - **B20, one line for the stack.** `PRIVYHUB_LINK_RECOVERY=1` means exactly the six lines (an explicit one wins).
      - **G-A4 (the tenth adopted line) is PREPARED only:** `docs/memory/patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`.
      - Record: `docs/memory/evidence/B20_LINK_RECOVERY_UMBRELLA_2026-10-24.md`.
  - **CL-B12 (2026-10-24, 3 / 3 cells valid; APK `20e3e339…` CONFIRMED and pinned; every client property EMPTY):**
    - **The stack via `PRIVYHUB_LINK_RECOVERY=1` alone, the client's defaults:** in 11 / 11 blackouts the resume came
      **108-349 ms after the return**, with 0 restarts, 0 v2 handovers and net 24 / 26. The picture was held 4.11-4.35
      s. **0 saves outside the blackouts;** at each teardown the bye, then `state_save_skipped` `client_bye`.
      `stall_signal_ms` 150 with no property.
    - **The guard's order (B17), two Home presses:**
      - no separate stop; `session_ended` logged by the start; the old report 56-70 ms after the start's response;
      - `restart_cause` `via_start`, `create_to_start_ms` 280 / 96;
      - 0 underruns in the first interval after each new start.
      - Both returns (the menu and "direct") were new instances in the live process (`recreate`); the surface and
        process paths were not exercised.
      - The user: "Each home and return behaved as expected and ran well".
    - **Back to B on two narrow rows:**
      - `link_recovery_config` logs the six as `explicit` (a second `apply()` in `plugins/games.py:201`; the behaviour
        is the umbrella's);
      - one 30-underrun interval at press 2's Home (the activity pausing), against "no interval above 15".
    - On 5 GHz: 0 silences / 10 min in every span.
    - Record: `docs/memory/evidence/CL_B12_DEFAULTS_AND_UMBRELLA_2026-10-24.md`.
  - **Queue H (2026-10-24, session B; nothing adopted, no live run; inserted 2026-10-25):**
    - **B21, the config row.** `link_recovery_config` now reports the import-time `apply()` (the process's first:
      `emulator_manager`'s, imported before `plugins/games.py`'s block). With the umbrella alone it reads `implied` the
      six, `explicit` {}, `at` `import`, `reapply` []. The wire's second `apply` is removed. It takes effect after the
      next companion restart. Record: `docs/memory/evidence/B21_LINK_RECOVERY_CONFIG_LOG_2026-10-24.md`.
    - **B22, the picture after a Home return.**
      - **Settled:** the host's 2.0-2.2-s start = the old audio's teardown before the encoder's kill (~0.78 s) + the
        new encoder (~0.45 s) + a fixed 0.75-s check and the new audio (~0.85 s).
      - The client's 8.8 / 4.2 s = the start-up gate's baseline + 6 clean 500-ms ticks (press 1 reset at least once);
        the picture itself was back ~1.3-2.0 s after `startSession`.
      - **Built:** `PRIVYHUB_RESTART_FAST=1` answers a guarded start before the teardown (the old encoder killed first,
        the old audio stopped beside the new encoder; the ready waits on the lock). The client (inside
        `restart_guard`, armed by the host's key) releases at the new stream's first fresh frame, with the audio at
        the ready's return.
      - **APK (B5 … B19 + B22) `6bddafc0…a927`, pinned, NOT installed.** Expected new activity → `session_started`
        ≈ 1.5-2.6 s (target ≤ 3 s), measured only by CL-B13.
      - Record: `docs/memory/evidence/B22_RESTART_FAST_2026-10-24.md`.
    - **B23, the thresholds on a WAN path (from WAN-R1).** `PRIVYHUB_LINK_RECOVERY_WAN=1`: on the overlay's direct
      path H 450 / the stall 200; the LAN, relayed and unknown paths as wired (950 / 400).
      - The path is re-read every 10 s; a guard reverts a direct session at its first non-drop hold.
      - G4-S4's replay: 0 false holds at 950 and 450. G4-S1 run 2 (direct → no-peer): 18 at a fixed 450, 2 with the
        guard.
      - Record: `docs/memory/evidence/B23_LINK_RECOVERY_WAN_THRESHOLDS_2026-10-24.md`.
    - **Still open:** CL-B12's 30-underrun interval at press 2's Home (the activity pausing, not a return) was not in
      this queue.
  - **Next:** G-A4 (the tenth line) on the user's say-so (`docs/memory/CURRENT.md`); B on the two rows; the user's own
    play on 5 GHz.
## 2026-10-20 UX-R1, the user's extended evening (2026-10-20 04:19-05:22Z) was bad and got worse — OPEN; the files agree; link vs onn not separable from them; UX-R2: the second evening mostly clean, the damage not repeated (one event so far, untested past play-minute 44); H5 closed (not new); UX-R3: one of last night's two "deaths" found (04:54:55-59Z, a 4-s drop in both directions); the second not distinguishable

**The user's standard, verbatim (2026-10-21): "This product needs to work at any house especially lan as long as the Internet is over 50mb/s."**
On last night, verbatim: "It felt better but there were two memorable instances where I literally died because of
lag. That is completely unacceptable especially over LAN." Where: "Zelda and no idea probably halfway through to last
third of the playthrough." Both evenings were played on a different TV and room from the usual test TV.

**UX-R3 (2026-10-21, read-only from the copies; `docs/memory/evidence/UX_R3_FIND_THE_DEATHS_2026-10-21.md`):**
- **Death 1, seen by the instruments: 04:54:55-04:54:59Z**, 12.3 of 26.4 min into Zelda, both directions at once.
  - The uplink was silent 2.65 s of 4 s (gaps of 967, 350, 342, 546 and 442 ms).
  - Output gaps 410 and 307 ms, the session's largest.
  - A heartbeat was held ~1.5 s, with 61 packets lost after FEC and a 406-ms audio arrival gap.
  - Frame sizes were normal. No recovery row. The ladder read clean.
- **Death 2 is not distinguishable.** The user's window 04:56-05:03Z holds only small hitches (control gaps
  277-297 ms, output gaps 215 / 223 ms).
- **Hitch seconds** (rendered < 50 fps, or a control gap ≥ 250 ms, or an output gap ≥ 200 ms, or post-FEC loss ≥ 30;
  pauses excluded):
  - Sunday 43.3 / 10 min (longest run 28 s); last night 12.9 (mid-play 7.8, longest run 5 s = death 1). This orders
    the two evenings as the user does.
  - September cannot be scored (its logs have rotated). Its reports do not show it cleaner.
  - A candidate metric, not adopted.
- **live cannot act on a 3-5-s drop.** Its rules need 4 of 5 two-second reports bad. In death 1 the window had 1 slow
  report and 0 lossy ones, and the heartbeat was held through the worst of it.
- **What the instruments CAN see:**
  - uplink silences ≥ 250 ms (start and length);
  - downlink loss, FEC, rendered frames and audio per ~2 s;
  - each session's 16 largest output gaps;
  - host transmit per second;
  - the ladder per report.
- **What they CANNOT see:**
  - controller-to-screen latency;
  - input delayed less than 250 ms;
  - the client's send timing;
  - output gaps below the top 16 outside the last 1,024 slow events (so 04:56-05:03:48 last night);
  - the Wi-Fi link's retries and rate (no Opal read);
  - the game's frame on the host;
  - a clock mark from the user at the moment of a death.

**UX-R2 (2026-10-21, the second evening, 2026-10-21 04:42-05:26Z, 43 min, SNES first;
`docs/memory/evidence/UX_R2_SECOND_EVENING_2026-10-21.md`, read-only).** The user: "Ran a few games last night." How it
felt: **no report yet.**
- **Mostly clean.**
  - After the first 5 minutes: post-FEC loss 37.5 / min (UX-R1: 173), underruns 3.9 / min (39.4), concealed 120 / min
    (328).
  - No silence pause, no encoder restart, no resync. Max output gap 534 ms. Only Soul Reaver's first ~2 minutes were
    rough.
- **The single-loss step repeated by the clock, not by play-minute.** FEC-recovered rose ~5 → 20-38 / min at 04:52Z;
  on UX-R1 it came at 04:54-04:56Z.
  - That is play-minute 10 against 35, and SNES was on screen both times.
  - On R2 it fell back to 10-15 / min under PS1.
  - The clock and SNES content cannot be split with two evenings.
- **UX-R1's damage did not repeat at its clock** (05:04-05:21Z read clean on R2). R2 ended at play-minute 44, so
  UX-R1's damaging play-minutes (45-64) are **untested**.
- **SNES played first was clean**, so H3 is weakened. H4 (Opus) is weakened: the same codec was clean.
- **H2 (onn uptime):** weakened *if* the onn was not power-cycled between 10-20 18:31Z and the evening. Its uptime at
  the first frame cannot be read from the device: 14 h 20 m if not cycled. It was cold-booted again ~15:01Z 10-21.
- **H5 CLOSED: not new.** The client ends its stream session at the **Pause menu** (load, save, or anything else) and
  starts a new one at Resume. The gap is the time in the menu.
  - The user's play on 2026-09-20 05:59-06:20Z (same titles, PCM) did the same: 8 reports, every one ending with the
    pause image `saved`, 6-18 s gaps.
- **Added to the instrumented evening:**
  - ≥ 65 min of play;
  - 00:40-01:30 EDT on the clock, starting on PS1 and switching to SNES after ~00:56;
  - the Opal's station counters every 5 min (read-only), required;
  - `boot_count` read at the start and the end.


**The user's report, verbatim (2026-10-20):**
> "I just played for an extended play session and it was horrible. It is much worse than it was weeks ago when I last did one"
> 1. "All the above. Every issue from audio to visual to gameplay. Multiple games all played terrible, especially later on with SNES"
> 2. "Every game got worse as time went on"
> 3. "besides the first 5 minutes, it was not good to terrible"
> 4. (when the earlier good session was) "Earlier" — before the October adoptions.

**The read** (`docs/memory/evidence/UX_R1_EXTENDED_SESSION_REGRESSION_2026-10-20.md`, read-only; nothing run):
- **The files agree with the user.** Five games, 20 client sessions, on the LAN.
  - First 5 minutes: underruns 3.9 / min, concealed 37 / min, post-FEC loss 26 / min. This is the week's clean windows.
  - After: 39.4 / 328 / 173. Bursts at 05:06, 05:10 and 05:20-21 hit video, audio and the onn's control uplink
    together. They ended in two `client_output_silence` pauses, one with an encoder restart (max output gap 4.9 s).
- **SNES is worst, and is also the last 31 minutes.** SimCity, the first SNES game, was clean. The step came at
  04:56Z, one minute into Super Mario RPG, and held into Zelda.
- **Ruled out by the files:**
  - the host (flat);
  - the guide grabs (none in the span);
  - the ladder (7000 throughout);
  - the frame-size tail (the cap held; loss vs frames ≥ 40, ρ −0.13).
- **Loss rose with the minute of the evening (ρ 0.52), and the audio followed the loss (ρ 0.83).**
- **Not separable from the files:** the link, or the onn's receive side. Neither end was read: the link watch is
  stopped, and the onn's `udp6` drops and the Opal were not read. The onn was cold-booted afterwards, so its end state
  is lost. It was ~11.5 h up at the start, not ~1 h.
- **Load State restarts the client session.** That was 16 times in 19 minutes of Emperor's New Groove, at 6-21 s each.
  It is a gameplay cost, but not the trend. Whether it is new since October is unread.

**The hypotheses, ranked by the files** (each test written in the record, none run):
1. **H1 — the receive path degraded over the evening (link or onn).** Test: one instrumented evening, the user
   playing ≥ 60 min, the onn power-cycled first. Every 5 min, read the onn's `udp6` drops plus
   `cl_b6_onn_read` / `cl_b7_onn_threads`, and the Opal's station counters read-only (or the link watch resumed).
2. **H2 — the onn's state with time / sessions.** Tested by the same evening.
3. **H3 — SNES.** Test: the order reversed for one evening; then its kill switches, one per evening.
4. **H4 — Opus (G-A2).** Test: its kill switch for one evening, as a bisect step after H1.
5. **H5 — Load State's restart cost.** CLOSED by UX-R2: not new (the Pause menu ends the stream session; same on 2026-09-20).

## 2026-10-18 CL-B4, the first Opus session: underruns 40 against 9; an off-site Opus start would be refused — OFF-SITE FIXED (CL-B5); UNDERRUNS: G-A2's 78 NOT REPEATED AFTER AN ONN RESTART (CL-B6: 22 / 13), A WATCH ITEM; SPIKES OPEN (the client's CPU measured)

**The user's decision 2026-10-19: Opus stays adopted — the data saving with nothing noticeable; a watch item; hands-on testing will be needed as things change.**

**CL-B7 (2026-10-19, three arms on a fresh onn, per thread; `docs/memory/evidence/CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md`):**
- **Where the cost is: LOCATED (the platform's Opus MediaCodec).**
  - Opus today minus PCM, 150 s in: the PrivyHub process +19.5 % of a core, **plus `media.swcodec` +11.1 %**, ≈ 0.31
    core on the onn.
  - Three quarters of it is framework-side: `MediaCodec_loop` +9.8 (a second looper thread), binder +2.2,
    `media.swcodec` +11.1.
  - Our own threads add +7.5. The `PrivyHub-Native` group (+6.8) cannot be split by name (15-char `comm`).
- **Lean (one call per frame fewer) moved nothing:** framework / binder −0.1 / 0.0, process −0.7. The per-call count
  is not the owner.
- **Spikes ≥ 20 ms:** PCM 70.1, today 121.0, lean 108.7 per min. Lean sits between them, which by the letter of the
  reading means the spikes follow the call count; this is one run each, with lean on the longest uptime and its CPU
  unchanged. **Spikes stay OPEN** with the owner named.
- **Underruns:** PCM 16 / 6, today 25 / 14 (decode queue 45 / 218 ms), lean 12 / 7. Still a watch item.
- **What would cut it** is the user's call: fewer frames through MediaCodec (20-ms frames, +10 ms) or a decoder
  outside it (libopus via JNI; no NDK on the host today).

**G4-S3 (2026-10-19, off-site at 4000):** underruns **34** in the window, across three client starts (Pause/Resume
and a relaunch). Net audio loss 0. Decoder spikes ~45 / min (≥ 50 ms ~4.7). Spikes are lower at 4000 than at 7000 on
the LAN; there is no PCM arm in the run. Underruns stay a watch item.

**G4-S4 (2026-10-24, off-site free play, 100 min; `docs/memory/evidence/G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` §8):**
- **Underruns in play:** 8.0 / min under the four lines, 20.2 on the ten-line sessions at 7000 from the start. The onn
  ran all afternoon.
- **Audio packets lost:** 38 / 30 / 11 in three of 13 sessions.
- **Spikes ≥ 20 ms:** 85 / min in the 41-min session at 7000 (the LAN at 7000: 105-163).
- Underruns stay a watch item.

**CL-B6 (2026-10-19, the A/B repeated after an onn power-cycle; `docs/memory/evidence/CL_B6_AB_REPEAT_AFTER_RESTART_2026-10-19.md`):**
- **Underruns: G-A2's 78 not repeated.** On a fresh onn (uptime ~7-17 min in the window), Opus read **22 / 13**
  (session / window) and PCM 11 / 8.
  - By the pre-registered reading, G-A2's 78 is consistent with the onn's state after a long evening, not the codec.
    Not proved: one restart, one run per arm.
  - Opus's session count is 2 over ≤ 20; the window count is under.
  - **Watch item:** the underruns of the next sessions, with the onn's uptime beside them.
- **Spikes: OPEN, now with a measured candidate.** ≥ 20 ms: Opus 104.7 / min against PCM 61.4 on the same evening
  (CL-B5: 144 against 100).
  - The onn's PrivyHub process used 107 % against 85 % of a core 150 s into each window (onn busy 51 % against 46 %).
    The Opus decode costs the client ~0.2 core.
  - The ≥ 50-ms spikes are small in both arms (2.9 / 2.2 per min). G-A2's 11.8 did not recur.
  - Not located.
- **CL-B7P (2026-10-19, software only; `docs/memory/evidence/CL_B7P_OPUS_CLIENT_COST_2026-10-19.md`): a hypothesis
  added, a candidate built, CL-B7 pending.**
  - **Hypothesis, from the code:** the ~0.2 core is the MediaCodec client-side per-buffer machinery. That is
    500 synchronous calls/s (5 per 10-ms frame), each a post-and-wait to the codec's looper, plus ~200 Codec2 binder
    transactions/s. The decode itself is expected in `media.swcodec`, outside the process.
  - The count alone gives ~0.03-0.05 core, so the size is unproved.
  - **The spikes would follow** because the client sets no thread priority: the video threads compete as equals with
    a ~6-8-thread audio wake-up chain every 10 ms.
  - **Candidate:** `debug.privyhub.opus_decode=lean` (absent = today) drops one of the five calls. The APK
    `93d29b4a…1624` is built, NOT installed.
  - **CL-B7 (session A):** install it; three arms (PCM, Opus today, Opus lean) with per-thread reads
    (`tools/cl_b7_onn_threads.py`).

**G-A2 (2026-10-19, Opus ADOPTED; `docs/memory/evidence/G_A2_OPUS_ADOPTION_2026-10-19.md` §4):**
- **Underruns REOPENED:** the confirmation run read **78** (50 in the window), over ≤ 20, against CL-B5's 11 / 13 on
  the same APK and codec.
  - One burst of 22 at ~11 s (start-up); ≥ 50-ms decoder spikes 138 (51 / 34); two > 1-s host ctrl gaps.
  - Net audio loss ~0, and the onn's thermal status 0.
  - Not located. The onn had run five sessions since 22:00Z, so a client-side long-uptime effect is a candidate,
    not shown.
  - **Next:** a paired A/B after an onn restart, or the next sessions' underruns watched.
- **Spikes: still OPEN** (163 / min here, under 200).

**CL-B5 (2026-10-18, `docs/memory/evidence/CL_B5_OPUS_DECODE_THREAD_AB_2026-10-18.md`):**
- **Underruns:** with the decode on its own thread, the paired A/B read A (PCM) 19, B (Opus) 11: under ≤ 20. The
  item is closed for underruns.
  - The codec call is still 3.2 ms average and 102 ms max. The decode queue once held 19 frames (185.5 ms behind),
    with 0 dropped.
- **Off-site: FIXED.** `audio_codec.py` `note_setup` records the overlay host for `sig_v` in (2, 3) (one line, with a
  test).
- **Spikes: still OPEN.** On the same evening: 144 / min in B against 100 in A, and max output gap 227 against 180 ms.
  Not located: the onn's CPU shared with the Codec2 thread is the remaining candidate; the onn's CPU was not read.


(`docs/memory/evidence/CL_B4_APK_OPUS_DECODE_2026-10-18.md` §4)

- **Underruns 40** (session report; 32 in the heartbeat window) against CL-B3 R1's 9, on the same rung, with 0 audio
  frames lost net.
  - The client's MediaCodec `audio/opus` runs synchronously on the audio receive thread: 3.3 ms per frame on average,
    84 ms at most, 4 drain timeouts. While it waits, the socket is not read and the queue is not fed.
  - The likely cause, not proven. **Next:** decode off the receive thread (or the async callback, the release order
    kept), then a paired PCM / Opus A/B on one day.
- **Decoder spikes ≥ 20 ms 178/min against 87** (CL-B3 R1), max output gap 501 against 410 ms. The cause is not
  located: the link (the runs are not paired) or the onn's CPU shared with the Codec2 thread. Under the < 200 bar.
- **Off-site, fails closed:** `companion/audio_codec.py` `note_setup` adds the declared overlay host only when
  `sig_v` == 2.
  - A `sig_v` 3 client (every client from CL-B4) has its media host recorded but not its overlay host, so an Opus
    start over the overlay is refused ("the client did not declare it").
  - **Fix before the off-site run at 4000 with Opus:** accept `sig_v` in (2, 3) there (one line, B's module).

## 2026-10-17 G8-S1: the rate-cap cells never reached PLAYING; delay-150 not read as latency-limited — OPEN

(`docs/memory/evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §4 (iii), §5)

- **The four cap cells (17-20: `cap-6000`, `cap-4500` @post-fec, off and on) did not reach PLAYING** in any of 12
  suite attempts (23 client sessions).
  - The stream entered the shim at ~8.25 Mbit/s (the 7000 rung with FEC and audio), above both caps.
  - The cap held its rate: 6,000.0 / 4,500.0 kbps out per second, `send_errors` 0, the queue at its 100-ms bound.
  - 27-29 % / 44-45 % was tail-dropped in every second.
  - The client received ~600 packets/s, rendered 9-27 frames and then nothing; each session ended after ~49 s.
  - No ladder decision was written: no PLAYING, so no window.
  - **Candidate readings, none chosen:** (a) the stream's own rate exceeds the cap and the bounded queue drops it;
    (b) the cap stage mis-paces within a second (not visible in 1-s lines); (c) a client start-up timeout.
  - G8-P1's cap proof used a steady synthetic ~6.9 Mbit/s source.
  - A follow-up (G8-S2) is the user's option.
- **G8-S3 / G8-S5 (the 5000 start under cap-6000): PLAYING reached; the drop above the bench, by the spread — MEASURED.**
  - G8-S3 (`docs/memory/evidence/G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md` §3): 6.75 % tail-dropped against the bench's
    1.8-2.4 %, at the bench's mean wire rate (~6.04 Mbit/s); not explained by the mean, it comes with the per-second and
    frame-size spread. Its rules-on cell went silent 417 s in and recovery gave up.
  - **G8-S5 (2026-10-19, `docs/memory/evidence/G8_S5_CAP_CELL_ENCODER_RC_TIGHT_2026-10-19.md`):** paired, flag absent
    against `PRIVYHUB_ENCODER_RC=tight`, both valid with host gates met.
    - Before the control's pause (the first 235 s), the tail drop was 6.52 → 4.43 %, the loss 2,286 → 1,534/min and
      rendered 53.45 → 55.12 fps.
    - **The per-second drop p95 was 19.68 → 15.75 %: not halved** (the bench: 17.1 → 8.0). The largest frame was
      89,248 B in both.
    - **The control cell went silent 235 s in** (`client_output_silence`, 5 restarts, `gave_up_saved`; max gap 366.8 s).
      The `tight` cell held 600 s. That is one run each.
    - By the pre-registered reading the bench did not transfer, and the `tight` item closes as measured; nothing
      adopted.
  - **Still open:** the silences under the cap (G8-S3 cell 2 at 417 s, G8-S5 cell A at 235 s, both without `tight`), not
    located.
- **`delay-150` read lossy (off) and path-changed (on), with 0 latency-limited windows.** Reported. The `rtt_ms`
  measure's source is the client's control echo, which the shim's video-only delay does not cross.

## 2026-10-16 G4-S1, the first off-site session: three items — OPEN

(`docs/memory/evidence/G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md` §6)

- **The remote row cannot read the host gate (a harness gap, G4-P1).** `tools/e1_remote.py` writes no RetroArch
  FPS-counter override (the title carries no "FPS / Frames"), and it starts the sampler without `--e2`, so no
  `encoder.jsonl`. RetroArch ≥ 59.9, capture 60 ± 0.1 and dup+drop ≤ 0.2/min are therefore not evaluable for any
  remote run. To fix before G4-S2: the remote row writes the same counter override as the local suite, and keeps the
  encoder progress.
- **The hotspot toggle ended the session; the stream came back after a LAN setup** (run 2).
  - The recovery log has `session_ended` 23:12:47.6Z, then `session_started` 157.4 s later, with no `desync_pause` or
    `resumed`. The next `token_issued` was `routing_evidence: lan`, and the overlay path read no-peer to the end.
  - The pre-registered "recovery pause, then a resume" over the overlay was not shown.
  - Whether the onn joined the home Wi-Fi by itself, or the LAN check began then, is not in the files. The hub's
    tailnet-interface firewall is still unread (no `nft`).
- **Run 1 was very lossy and had one 24.5-s controller-silence pause:** 2,259 post-FEC loss/min, 2,344 audio
  underruns, rendered 57.16. The pause coincided with a direct → relayed → direct path change (22:55:52-22:56:23Z).
  Reported, not gated. Run 2's overlay part (before the toggle) read 13.9 loss/min.
- **Also seen:** after the onn changed networks, `tools/e3_state.py` cannot reach it over adb (`adb connect` needed),
  so `--check` reads not ok on `adb` and on the APK while every host field holds.

## 2026-10-16 G5-S1 WAN telemetry: no per-session line when a run ends in a restart; CPU cost over its bar — OPEN (CL-B3 W)

- **Seen:** CL-B3's live smoke, with `PRIVYHUB_WAN_TELEMETRY=1` as a per-run drop-in
  (`docs/memory/evidence/CL_B3_HARDENED_APK_LAN_2026-10-16.md` §4).
  - The `wan` object was live on `/status` and `/diagnostics/stream-telemetry`, with all eleven measures and a
    class per window.
  - **`logs/wan_sessions.jsonl` was never written.** `wan_telemetry.py` closes a session (and writes its line) only
    when the next stream session starts in the same process. The suite's teardown restart ends the process first,
    so a one-session run never logs. The fix belongs to G5-S2: write the line at stream stop and at shutdown.
- **The cost:** the companion was +0.633 point of a core (≤ 0.5 set) and +0.35 MB PSS (≤ 2), W minus R1.
  - These are two runs, not paired arms, at the same 7000 rung. RetroArch was also +1.35 in W.
  - The provider's own cost is not isolated. An idle A/B in G1-S2's way would settle it.
- Not adopted, so the flag stays off. Whether these block G5's adoption is the user's call.

## 2026-10-16 the host-CPU band gate fails on the encoder's share, not on the stack — a BAR item (CL-B2 R3), OPEN

- **Seen:** CL-B2's R3 (PS1-STREAM ×10 min, flag and setting off,
  2026-10-16 13:54Z) read host CPU **12.963 %**, against the band
  10.9 ± 2. It **FAILED by 0.06**, and every other gate held. The user
  decided the APK stays and CL-B2 closes, with the gate recorded FAILED
  (`docs/memory/evidence/CL_B2_IDENTITY_APK_AND_LAN_SMOKE_2026-10-16.md`
  §2a; `cl_b2_cpu_split.json`).
- **The split (% of one core):**
  - The companion and RetroArch were within a point of R1.
  - The **encoder was 46.65, against 35.75** in R1.
  - The ladder polled 7000-7000 in R3, against 5000-7000 in R1.
- **Not explained by the rung mix:** E4-S1's 10.9 reference and CL-B2's
  R2 held 7000 for every poll, with no ladder action, at 36.04 and 35.64 %
  encoder. The cause of R3's +10.9 points is not located.
- **The bar lesson (the user's, extended by the files):**
  - Host-CPU bands must compare runs at an equal rung mix, or report the
    encoder together with its rung.
  - At an equal rung the encoder can still move by ~11 points, so a
    near-edge failure is read through the per-process split before a
    cause is named.
  - Not applied to any tool. Changing the gate or the band is the user's
    call.

## 2026-10-16 session identity (G3) on the LAN — three follow-ups for G3-S3, seen in CL-B2 — PORTS ADDRESSED (G3-S3, CL-B3)

- **Update 2026-10-16 (G3-S3 built; G-A1 adopted the host flag; CL-B3 installed the APK):**
  - `audio_port` is now signed (setup canon v2). The stream-start port is bound to the signed one (403
    `endpoint-port-mismatch`, audited). The host chooses the declared target by routing class.
  - CL-B3's R1 showed `?port=48100` → 200 under a `sig_v` 2 token, with no refusal.
  - The wire destination is still not observable unprivileged (unchanged).
  - **Still open:** the store directory's 0775, and the extra setup per entry. CL-B3 saw a fresh setup after
    each teardown restart, which is expected.

- **Context:** CL-B2 (`docs/memory/evidence/CL_B2_IDENTITY_APK_AND_LAN_SMOKE_2026-10-16.md`)
  ran G3 end to end on the LAN. It is CLOSED, and the APK `77011eef…`
  stays.
  - Pairing, signed setup and token, a 20-min stream with every host gate,
    a forged token → 401, and an unpaired device → `unknown-device`.
  - R3's host CPU FAILED by 0.06 (the entry above).
  - The host flag and the client setting are NOT adopted (the user's call).
  - G3-S3 also carries the range server over the overlay and the
    TV-sync / EPG / diagnostics tokens.
- **The declared ports:**
  - `audio_port` is declared but unsigned and ignored by the host; only
    `video_port` is signed and checked.
  - The host's chosen destination cannot be seen from outside: the
    encoder feeds the loopback FEC sender, and its sends are unconnected.
  - A smoke can therefore show the declared target only through the code
    path and the audit (no `legacy_setup`), not on the wire.
  - G3-S3: sign and check `audio_port`; report the chosen target's class
    and hash (no address).
- **The store's directory:** `~/.config/privyhub` is 0775 (it predates
  G3). The store file itself is 0600.
- **Two setups per stream entry:** the client issues `token_issued` twice
  for one device within two minutes. Seen; not a fault.

## 2026-10-10 SNES capture at 59 fps (or 59.94) for a whole encoder session — FIXED, ADOPTED 2026-10-15 (E4-S5D)

- **Adopted (E4-S5D, the user's decision, 2026-10-15)**
  (`docs/memory/evidence/E4_S5D_SNES_CAPTURE_FIX_ADOPTION_2026-10-15.md`):
  - the drop-in `snes-capture.conf`,
    `Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`, is the fifth
    adopted line;
  - the encoder's argv carries `-r 60`;
  - the state checks require it (`tools/e1_suite.py` `ADOPTED`).
- **Confirmed** on the adopted state:
  - a 20-min SNES-STREAM: capture 59.964, dup+drop 0.05/min, RetroArch
    59.999, host 7.81 %;
  - a 10-min PS1-STREAM: capture 59.942, 0.10/min.
  - Both SNES starts probed 60, so tonight's run did not exercise a bad
    probe; E4-S5C's 4 / 4 is the evidence for that case.
- **The revert:** delete the drop-in, `systemctl --user daemon-reload`,
  restart the companion, and take the line out of `ADOPTED`.
- The history below is kept as it was.

- **Seen** (E4-S1 §4, E4-S2 §2): on SNES-STREAM (Snes9x), the encoder
  sometimes outputs exactly 59 fps, dropping one frame per second, for a
  whole session; or 59.94, one drop per ~17-20 s. RetroArch holds
  59.999. It is not load.
- **Cause, located** (`docs/memory/evidence/E4_S5_SNES_CAPTURE_59FPS_2026-10-10.md`):
  - ffmpeg estimates the x11grab input's frame rate (`tbr`) from its
    first frames, and the encoder command sets no output rate.
  - The SNES window (897×672) is usually probed at 60, but sometimes at
    59.94 or 59.
  - The encoder keeps that rate until it restarts; each restart re-probes.
  - Output = probe in 15 / 15 logged sessions and 6 / 6 fresh segments.
    PS1's 1920×1080 window never gets an estimate (`1000k tbr`) and
    falls back to `-framerate 60`.
- **Fix, built and dormant:** `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`
  (an output `-r 60`; `companion/native_stream.py`; absent = today).
  - The verification was REJECTED on rendered fps on a lossy link.
  - All five of its probes read 60, so the fix was not exercised.
- **E4-S5B** (`docs/memory/evidence/E4_S5B_SNES_CAPTURE_PROBE_BENCH_2026-10-10.md`),
  a bench of 48 × 60-s encoder sessions beside a live SNES-STREAM:
  **INCONCLUSIVE** (the mechanism did not reproduce in the no-flag arm).
  - With the flag, all 4 bad probes (59, 59.94 ×3) output 60.
  - The bench's `-f null` sink passes frames through, so it shows no drops
    in either arm. A synthetic check shows the companion's rtp
    constant-rate mode drops: 58 per minute at 59, 2 at 59.94, 0 with
    `-r 60`.
  - The fault was live in the companion's own unflagged stream the same
    night: 2 bad probes in 11 encoder starts; capture 59.944, 2.25
    dup+drop/min.
  - PS1 with the flag: unchanged (capture 59.99, 0.10/min).
- **E4-S5C** (`docs/memory/evidence/E4_S5C_SNES_CAPTURE_PROBE_BENCH_CFR_2026-10-10.md`),
  E4-S5B's bench with the sink in `-fps_mode cfr`:
  **INCONCLUSIVE** (the mechanism clause, by its pre-registered window).
  - With the flag, all 4 bad probes (59 ×2, 59.94 ×2) output 60 with 0
    drops. **The fix works.**
  - Without the flag, all 5 bad probes output their probe and dropped:
    59 → 58 drops (inside 60 ± 12); 59.94 → **2** drops ×4, against the
    pre-registered 3-4. 3,597 frames came out, 3 short of 3,600, but
    ffmpeg's drop counter reads 2 (the synthetic check read 2 too). The
    window was the task's formula; it was not changed after the data.
  - The live SNES-STREAM was host-clean (RetroArch 59.999; host 8.90 %
    net of the bench). The companion's own unflagged stream probed
    59.94 on 2 of 6 starts; capture 59.97, 1.67 dup+drop/min.
- **Decided 2026-10-15:** adopt. The user adopted it on this evidence; it
  was applied and confirmed by E4-S5D (above).

## 2026-10-10 runner: the EPG refresh loop has no back-off on a refused call — FIXED (E4-S3B)

- **Fixed 2026-10-10** (`docs/memory/patches/E4-S3B_RUNNER_REFRESH_BACKOFF.md`):
  - A call with no HTTP reply now backs off 1 s, doubling to 30 s. Each
    failure streak is written as one row.
  - In E4-S3B's two OOM-killed runs each restart wrote one row, and every
    `epg.jsonl` stayed at 53-62 KB.
  - The history below is kept.

- E4-S3: while the companion's unit was restarting after OOM kills, the
  suite's `EpgCycle` re-asked at once and logged ~1.4-1.5 M failed
  "grabs".
  - That produced two ~300 MB `epg.jsonl` files in
    `evidence/e4_s3_2026-10-10/` (kept; the user's call before commit).
- A one-line back-off in `tools/e1_suite.py` would prevent it.
  Measurement tooling only.

<!-- PRIVYHUB_BASELINE_STREAM_HEALTH:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 baseline stream health — open faults, corrected by Group A

The reference stream fails its own target. Original record:
`docs/memory/evidence/BASELINE_STREAM_HEALTH_2026-09-20.md` (47 sessions =
the newest 50 files). Full-corpus re-score, 128 sessions:
`docs/memory/evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`. Read the
first with the second.

- **Client receive-to-output latency.** `spike_20_ms` (>= 20 ms from
  access-unit completion to decoder output) median 2,535/min: 66 % of
  frames sit at 20-60 ms and are rendered, 5.5 % exceed 60 ms and are
  dropped by the client's stale policy, which is 3.5 of the 4.5 fps
  deficit. The decoder holds 2-3 frames during slow events (11-13 is a
  transient maximum). A1-live (2026-09-20) read the SPS on the wire: no
  B-frames, `max_num_reorder_frames 0`, `max_dec_frame_buffering 1`,
  `dpb_output_delay 0` on every frame. **The bitstream is not asking for the
  hold; the decoder is.** Client side. Status: **answered by `C3.L2c`,
  decision pending.** Three 130 s sessions on the unconditional
  `KEY_LOW_LATENCY` build (2026-09-20 evening) read 203/107/119 spikes per
  minute against a corpus median of 2,535, with 94.3-97.0 % of frames under
  20 ms and the client-side fps deficit down to 0.22-0.67 fps. **Kept by
  the user.** Record:
  `docs/memory/evidence/C3_L2C_DISTRIBUTION_2026-09-20.md`.
- **The 60 ms stale threshold — CHARACTERIZED 2026-09-20 (`D-BASE-P1`), no
  change recommended.** The clause above — "5.5 % exceed 60 ms and are
  dropped … 3.5 of the 4.5 fps deficit" — was measured **before** `C3.L2c`
  and is no longer true of the current build. Thirteen sessions at
  thresholds 60 / 90 / 120 / 200: at the default the policy discards 6, 17
  and 15 frames per ~97 s session, so recovering all of them would add
  **0.06-0.18 fps**, and the arm medians show no gain (59.65 / 59.56 /
  59.06 / 59.27, tracking received-AU fps). p50 and p90 of rendered-frame
  latency are <= 20 ms in every arm; only p99.9 moves (<= 40 ms → <= 120 ms),
  and rendered frames above 60 ms go 0.000 % → 0.279 %.
  `max_output_gap_ms` shows no trend. **The default already meets
  `rendered fps >= 59.5`.** Record:
  `docs/memory/evidence/D_BASE_P1_STALE_THRESHOLD_2026-09-20.md`; knob:
  `docs/memory/patches/D-BASE-P1_STALE_THRESHOLD_PROBE_KNOB.md`.
  Caveats that matter: thirteen idle attract sessions on a quiet link with
  zero resyncs, n = 3 per arm, and the interleave's fixed cycle order is
  confounded with the arm — so the `spike_20_ms` differences between arms
  are position, not threshold. **The decision is the user's; nothing was
  changed.**
- **Stall tail = transport outages + IDR wait.** Every stall over 1,000 ms
  in every epoch carries an outage-class sequence jump and an IDR wait,
  with the last frame held inside the codec meanwhile; pre-flatten stalls
  of 2,035 ms exist. The 2026-09-19 "regression" was a 21-session window
  artifact. Status: **owner Step 3 (transport).** The `C3.L2b` revert
  (Step 1) is withdrawn.
- **Thermal headroom on both ends — telemetry only, no threshold set
  (`D-BASE-T1`, 2026-09-21).** The host will be an always-on server and the
  eventual PS2 / GameCube work needs thermal headroom, so host and onn
  temperatures are now recorded in every session: the onn's
  `thermal_status`, `thermal_headroom` and `thermal_zones_c` in each
  heartbeat plus a `thermal` block in each report, and the host's through
  `tools/host_resource_sampler.py` and `host_thermal_c` on
  `native-stream-status`. **No threshold is set and nothing acts on the
  numbers.** A thermal pause on the recovery state machine is deferred with
  its reopen condition in
  `docs/memory/investigations/DEFERRED.md` ("Thermal pause on the link-drop
  recovery state machine"). Evidence:
  `docs/memory/evidence/D_BASE_T1_THERMAL_TELEMETRY_2026-09-21.md`.

- **RetroArch memory growth during play — CLOSED 2026-09-21
  (`D-BASE-S2`). It is not a leak.** `D-BASE-S1` measured +108 MB per
  30 minutes across four 30-minute sessions and could not say where it
  stopped. A 3-hour session says: it stops. Total growth **+119.9 MB**, of
  which **+110.2 MB is the first 30 minutes**; the last block was +4 kB.
  And it is **file-backed** — `RssFile` +113.6 MB against `RssAnon`
  **+6.2 MB over three hours** (~2.1 MB/h), `RssShmem` +88 kB, `VmSwap` 0
  throughout. That is the emulator's mapped ROM, core and assets becoming
  resident, which finishes, and is reclaimable under pressure;
  `MemAvailable` was *higher* at the end of the session (7,954,440 kB) than
  at the start (7,832,556 kB) against a MemTotal of 14.94 GiB. The
  companion plateaus the same way (+6.8 MB total, ~0.18 MB per 30 min after
  startup) and the encoder is flat (+0.5 MB, then nothing). **No action.**
  Evidence: `docs/memory/evidence/D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`.

- ~~Native-stream log rotation is only synthetically tested~~ **RESOLVED
  2026-09-21 (`D-BASE-R5`): rotation has now run against real traffic and
  lost nothing.** The heartbeat log crossed 4 MiB **17.9 minutes into a
  20-minute session** and rotated to
  `stream_log_archive/native_stream_heartbeat.log.1` (4,194,628 bytes):
  sequence step **1** and elapsed step **2,007 ms** across the boundary —
  exactly one heartbeat interval, **no line lost**.
  **Growth is now ~819 KB/h, not ~453**, because `D-BASE-R5` took the
  heartbeat line from 276 to **465 bytes**; the log therefore fills 4 MiB
  in **~5.0 hours** of continuous streaming, not ~9. **Still untested: the
  archive family's retention limit**, which has not yet had to discard a
  rotated file.
  **A slicing trap comes with it:** anything that cuts this log by line
  offset breaks across a rotation — the file gets *shorter* than the
  offset and the slice comes back empty, which is what happened to
  `D-BASE-R5`'s own harness. Read the archive and the live log together
  and filter on a rising `elapsed_ms` run (`TOOLS.md`).

- **Audio underruns — CHARACTERIZED 2026-09-20 (`D-BASE-P2`).** The
  per-event timeline now exists (`audio.tick_series`) and it places the
  whole thing: **a median 98.7 % of a session's underruns occur in the
  first 3 seconds**, 80 % by 1,512 ms, ending the tick the audio queue
  first fills. `queue_depth` is **0** for every tick of the burst. It is
  over before the stabilization gate releases gameplay (median 5,757 ms)
  and it ends at the first real PCM write (median 1,800 ms), which is a
  median 1,013 ms *after* the first video frame.

  **So "113/min" is a fixed per-session burst divided by a short session,
  and "~17/min steady state" was the same artifact at a longer duration.**
  Across 177 sessions `underruns` is flat at 116-162 from the 0-40 s bucket
  to the 300 s+ bucket while `prolonged_starvation_events` and
  `concealed_underruns` scale ~20x with duration; Spearman
  `underruns_pm` against duration is **-0.725**. Steady-state underruns are
  2-12 per session and do not coincide with video slow events, so the
  "tracks decode pressure" reading is withdrawn — the correlation with
  `lost_packets` is 0.113 and with `avg_queue_residence_ms` **-0.414**
  (shallow queue, i.e. starvation).

  **`prolonged_starvation_events` is a second phenomenon**, not the same
  thing counted differently: absent from the burst, steady at 1-2 per 10 s
  afterwards, rho 0.195 against underruns. It is unexplained and deserves
  its own question.

  **The fix is implemented and works (`D-BASE-P2a`, 2026-09-21).**
  `playbackLoop` now holds the AudioTrack until the first real PCM packet
  is queued, bounded at 3,000 ms, after which the original behaviour
  resumes. `audio.underruns` per session: **0 / 6 / 21 / 20 / 3, median 6**
  against P2's median 207, with 0-3 in the first three seconds against
  ~204. `first_write_elapsed_ms` moved 7 ms at the median, so audio is not
  delayed — only the track's start. Records:
  `docs/memory/evidence/D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md`
  (where the burst is) and
  `docs/memory/evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md` (the
  fix); patches of the same names.

  Status: **RUNTIME VALIDATED 2026-09-21** by `D-BASE-P2b`
  (`docs/memory/evidence/D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`),
  which closed both of P2a's open checks. Ten sessions, five matched pairs,
  strictly alternating against a build with the hold compiled out: that
  build measures `prolonged_starvation_events` **125-157, median 151** —
  the same band the fix was blamed for — pooled Spearman against run index
  is **-0.036** (no drift either), and the sign test puts hold-on above
  hold-off in only **3 of 5** pairs. `avg_queue_residence_ms` is 27.70 off
  against 27.62 on, so the shifted-queue mechanism P2a proposed is absent.
  Both arms clear the fps bar on a quiet link (median **59.53** off,
  **59.56** on). The underrun result replicated: median **276** off against
  **19** on.

  **`prolonged_starvation_events` itself is still unexplained** and is the
  surviving open question — a second phenomenon (`D-BASE-P2`), insensitive
  to the startup hold, with no run-order trend, varying session to session
  in a 125-157 band and not following video loss (1.9-23.7 per minute
  across the same ten sessions). Nobody has related it to anything
  audible.

  **Since explained and priced (2026-09-22/23).** `P7`/`P8`: it counts
  audio arrival holes > 15 ms, and the holes are the path's. `P9`: a
  deeper cushion (profile `audio_queue_capacity_packets` 8 → 17) takes it
  from 42.4 to **0.8/min** for **+36.0 ms** of measured audio latency, but
  underruns went 20 → 25 and the pre-registered rule reverted the default
  to 3 / 8 — **open as the user's decision**
  (`docs/memory/decisions/D-BASE-P9_AUDIO_CUSHION.md`). Note also: with
  the `P2a` hold in force, most of a session's `audio.underruns` is now
  mid-session, not the startup burst (`P9`, all three arms).
  **`P9a` (interleaved)**: 12/17 again -98-99.5 % at +33.5-37.9 ms, its
  underruns inside the 3/8 band of 4-20 — still the user's decision.
- **Audio packet loss builds over back-to-back streaming** (`P9`, `P9a`,
  2026-09-23). Within a run of consecutive 20-minute sessions the audio
  `lost_packets` rate climbs from ~3/min to 50-130/min and resets after
  idle time (~40 min); interleaving shows it is **time-driven, not the
  audio cushion's** (counted before the queue). **`D-BASE-T2`
  (2026-09-23)**: it is a **step at a warm state** — 1-6/min for ~7 min
  from cold, then 30-90/min; 30 min idle resets it. Every temperature
  (host, onn CPU, Opal SoC) moves with it; RSSI, MCS, retries and video
  loss do not. **Narrowed by `D-BASE-T3`**: the host sends every packet
  (0 send errors, 0 kernel `SndbufErrors`) and the onn's audio socket and
  UDP stack drop none — the packets are **lost between the ends** (wired
  hop, Opal, air, or the onn's Wi-Fi firmware). **Mitigated by
  `D-BASE-P10`** (adopted 2026-09-23): every audio datagram is sent twice,
  20 ms apart; warm loss 78 → 1.4-2.8/min, +1.6 Mbps
  (`docs/memory/evidence/D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md`).
  Status: **mitigated; the cause between the ends is still open**
  (`host_link`). Thresholds proposed, not enforced.
  `docs/memory/evidence/D_BASE_T3_AUDIO_LOSS_LOCATION_2026-09-23.md`;
  `docs/memory/evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`.
- **Link type.** Host measured wired (`eno1`, `r8169`, no radio present) on
  2026-09-20; on 2026-09-15 it was a USB RTL8822BU radio. The onn's
  association is still unread. One wireless hop by role. Nothing per
  session records it. Status: **open** — implement the `host_link` field
  specified in the Group A record before the next transport comparison.

Two metric defects found by the re-score, both open:

- **`lost_packets` excludes every gap >= 128 packets.**
  `RtpH264Receiver.beginStreamResync` resets the sequence tracker without
  adding the jump to `lostPackets`. Post-`C3.L2b` corpus: 53,679 jump
  packets vs 23,521 counted (2.3x); corrected loss/min median 252 vs 120.
  Status: **fixed and runtime-confirmed 2026-09-20** (`D-BASE-R1`):
  `beginStreamResync` adds the jump to `lost_packets` and to a new
  `lost_packets_in_resyncs` field. Confirmed on the onn in
  `native_decoder_20260920_145024_777.json` (`lost_packets_in_resyncs` 493 =
  the sum of the session's three resync jumps; `lost_packets` 695 against a
  pre-fix 202) and carried by every session since. Record:
  `docs/memory/evidence/D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md`.
  Reports without the field: read loss as `lost_packets` + sum of
  `stream_discontinuities[].jump_packets`; reports with it: `lost_packets`
  already includes the jumps.
- ~~The worst ordinary-play slow event is evicted from the report~~
  **FIXED 2026-09-20 (`D-BASE-R4` item 2).** Two magnitude-ordered top-16
  lists now sit beside the two FIFO segments: `slow_events_top_gap` and
  `slow_events_top_latency`, same seven columns, with
  `slow_event_retained_top_gap` / `_top_latency` and their capacities. In
  all four validation reports the top-gap maximum equals
  `max_output_gap_ms` and the top-latency maximum equals
  `max_rx_to_decode_ms`; in one the worst event had already been evicted
  from the merged array and only the top list held it. Record:
  `docs/memory/evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`.
  The lists keep no union, so an event 17th worst on both axes is in
  neither.
- ~~A slow event is recorded only on receive-to-output latency >= 50 ms~~
  **FIXED 2026-09-20 (`D-BASE-R2` piece 1).** `drainOutputs` now also
  records when `outputGapMs >= 50`. Confirmed on three sessions: each one's
  `max_output_gap_ms` (276 / 744 / 474 ms) has its own row, every one
  ending on a frame with `rx_to_decode_ms` 10-18 and `codec_ms` 10-13 —
  rows the predecessor trigger could not produce. One session recorded
  `slow_event_retained_marked` **3** against its 3 resyncs, the first
  non-zero marked segment on a low-latency build, so the `C3.L2b` cycle
  window now protects something. Record:
  `docs/memory/evidence/D_BASE_R2_STALL_VISIBILITY_2026-09-20.md`.
  **This made the worst gap qualify, not survive** — both halves are now
  closed by `D-BASE-R4`: the retention item above (top-16 lists) and, for a
  gap that never ends at all, item 1 below. Keep the retention counters in
  the report; they are what makes an absence readable.
- ~~A gap that never ends is never recorded~~ **FIXED 2026-09-20
  (`D-BASE-R4` item 1).** `drainOutputs` only records when a frame comes
  out, so a terminal stall used to leave `max_output_gap_ms` at the last
  *completed* gap — `D-BASE-R3` F15 reported 135 ms for a 46 s stall. The
  client now checks the age since the last output on its 500 ms tick and
  again at report assembly, raises `max_output_gap_ms` to it, and emits
  `terminal_slow_event` (flagged `terminal: true`, with `-1` for
  receive-to-output, feed delay and codec time, which do not exist for a
  frame that never arrived) plus `output_age_at_end_ms`. Confirmed: a 70 s
  held stall reported both as 68,617 ms. The slot clears whenever a frame
  is output, so `terminal: true` never labels a gap that closed.
- ~~The native stream heartbeat log is append-only and is not rotated~~
  **FIXED 2026-09-20 (`D-BASE-R4` item 4).**
  `logs/games/native_stream_heartbeat.log` rotates at 4 MiB keeping 3, and
  `logs/games/native_stream_recovery.log` at 1 MiB keeping 3, into
  `logs/games/stream_log_archive/`. Rotation runs before the append, so the
  line that triggers it becomes the first line of the fresh file; a
  5,000-append run across 25 files lost no line and preserved ordering.
  `tools/diagnostic_retention.py` covers the archive through a new
  `stream_log_archive` family — **its policy SHA-256 is now
  `b13fbc32dbf7f46a4ca9321985ea2d410804c15b9faaf82c3f87dce8356971b5`, which
  an `--apply` run must quote.**
- **The launcher's game-session banner refreshes only on `onResume`.**
  `D-BASE-R2` piece 3 fixed what a *failed* poll does — it now clears the
  banner and says "Companion unreachable", and retires that notice when the
  companion answers again. It did not add a timer, so a launcher left in the
  foreground while the companion dies underneath it still shows a stale
  banner until the next resume. Status: **open by design**; a timer was not
  authorized.
- **Stopping the companion with a game active orphans RetroArch.** A
  restarted companion reports `active: false` and does not reclaim the
  running emulator. Seen twice on 2026-09-20 during the `D-BASE-R2`
  piece-3 checks; both were killed directly.
  `tools/recover_orphan_game_session.py` exists for the case where the
  session is worth recovering. Status: **open**, pre-existing.

Also open, from the `C3.L3a` Part 2 probe's first run — fix before any rerun:

- the mark-association window anchors on sequence start, so a ramp closes its
  window before it finishes and marks are lost;
- telemetry field paths were taken from a probe's output artifact rather than
  the endpoint, so settling was never measured;
- the picture rating used an unanchored 1-5 scale and silently rescaled 1-10
  answers.

The 2026-09-20 session's raw marks and per-cycle timings are retained in
`logs/streaming/c3_l3a_gameplay_acceptance_state.json` and can be re-scored
without replaying.
<!-- PRIVYHUB_BASELINE_STREAM_HEALTH:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:KNOWN_ISSUES:BEGIN -->
## 2026-09-16 current issue override

Current Phase-D blocker:
- **PS1 multiplayer / multitap parity on Linux** — active. Windows Phase A proved
  the intended Port-1 multitap behavior; Linux currently fails to reproduce it.
  Exact boundary is not yet classified.

Resolved/superseded:
- broad "Linux controller input is broken" — resolved for the tested paths by
  D-084/D-085 and runtime validated across three games / three input profiles;
- "native Games streaming host is Windows-specific" — superseded for Games by
  the current Linux X11/VAAPI/PulseAudio/uinput runtime.

Do not reopen the lower controller transport or D-pad mapping while debugging
multitap unless a fresh diagnostic contradicts the D-085 runtime acceptance.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L0 audit findings

Added by the `C3.L0` Linux actuator boundary audit. Neither item is fixed by
that work.

- **Linux host resource telemetry never starts.**
  `NativeStreamManager._host_telemetry.start()` is called only inside the
  Windows start path, gated on `_capture_process is not None`.
  `_start_linux_locked` never calls it, while `status()` still publishes a
  `host_telemetry` section, so the field reports an inactive profiler on every
  Linux session. The C2 telemetry contract is unaffected because its sender
  metrics come from the FEC relay `sendto()` boundary, which does run on Linux.
  Status: open, Phase E prerequisite. Does not block C3.

- **`_patches/` and `_probes/` are not covered by `.gitignore`.**
  Status: **RESOLVED 2026-09-18** by the STREAMLINE patch. `.gitignore` was
  deduplicated and now covers `_patches/`, `_probes/` and `Claude outputs/`
  explicitly, alongside the existing `privyhub_*` patterns. The directories
  themselves are left on disk; delete them when you want the space back.

- **Existing C3 probes cannot run on Linux.**
  `companion/diagnostics/c3_actuator_probe.py` and
  `companion/diagnostics/c3_fixed_bitrate_probe.py` require `_wgc_ready()`, an
  HWND capture target and `_build_ffmpeg_command`, and fail closed with
  `wgc_runtime_unavailable` before modifying anything. They are correct as
  written. Status: expected prototype limitation; resolved by the `C3.L1` Linux
  cycle implementation.
<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L2A_E1:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L2a E1 diagnostic retention findings

Found by the `C3.L2a` E1 evidence pass. Record:
`docs/memory/evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.

- **The decoder session report's slow-event list was a 128-entry ring that
  discarded the actuator cycle.** In the `C3.L1R1` session it held 128 of 128
  and covered only the last 29.4 s of a 64.8 s session, so the row explaining
  `max_output_gap_ms` 287 was already gone. Any session with more than 128
  slow events after a cycle lost the cycle's evidence. Status: **code fix
  installed 2026-09-18 by `C3.L2b`** (`docs/memory/patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`)
  — segmented marked/recent retention plus `elapsed_ms`-anchored
  discontinuity and first-IDR-after-discontinuity lists. **Not yet
  runtime-confirmed**: no APK built with the real Android/Gradle toolchain has
  been installed on the onn device, and no actuator cycle has been run against
  it. `C3.L2a` itself stays open until that cycle runs and the new report
  fields are read. Diagnostic-only client work; no streaming constant changed.

- **The encoder swap is not visible in the native video host log tail.** The
  bundle carries the last 500 lines, which for the `C3.L1R1` session showed a
  single continuous frame counter with no restart banner while the receiver
  recorded one SSRC change. Status: open question for the probe source; either
  the replacement encoder does not write to that log or the swap fell outside
  the tail. Unaffected by `C3.L2b`.

- **Decoder time dominates the large output gaps on the onn client.**
  `output_gap_ms` tracks `codec_ms` one-to-one in ordinary play, reaching 238 ms
  with no actuator involved; 2,696 spikes at or above 20 ms against 3,847 queued
  frames; `low_latency_enabled` is false on `c2.realtek.video.avc.decoder`.
  Status: open, unattributed. Enabling low-latency decode is `C3.L2c`, a
  separate production-behavior candidate, registered but not scheduled and
  not authorized; it was not folded into `C3.L2b`.
<!-- PRIVYHUB_C3_L2A_E1:KNOWN_ISSUES:END -->

Status as of 2026-09-11.

| Issue | Status | Blocks current Phase C work? | Resume / resolve when |
| --- | --- | --- | --- |
| Bidirectional UDP burst/gap distortion and duplication in the current test path | **RESOLVED on the Linux host path, 2026-09-22.** Mechanism: **frame-size tail → large-frame burst → wireless queue overflow.** `D-BASE-P6` proved it by intervention and `D-BASE-P6a` adopted the fix — `max_frame_size 90,000` is now a declared profile parameter, validated at **loss 249 against an uncapped 2,690-2,896**, zero ≥80-packet frames, bitrate/fps/CPU unchanged. **The Windows-era pathology is a separate deferred note and is NOT claimed resolved** | No | Windows path: replay after a representative Windows baseline. Linux path: closed |
| Native streaming host is Windows-specific | Expected prototype limitation | No | Phase D Linux migration |
| NES runtime coverage | No local A9 fixture | No | Representative NES fixture is available |
| Genesis runtime coverage | No local A9 fixture | No | Representative Genesis fixture is available |
| Android cleartext/exported diagnostics and companion network exposure without mature auth | Security/privacy debt | No for isolated prototype | Dedicated threat-model/auth/encryption/privacy work |
| WGC/FFmpeg/process-audio bootstrap is not fully portable | Portability debt | No | Phase D / clean-machine reproducibility work |
| Conventional automated CI is minimal | Engineering debt | No | Before productization / broader platform expansion |
| Large orchestration files | Maintainability debt | No | Dedicated refactor with its own validation objective |
| Remaining Live TV / EPG / guide polish | Planned product work | No | Phase F |
| Game Session banner latency | Low-priority polish | No | Dedicated measured latency investigation if prioritized |

Resolved items such as the historical `companion/games/` ignore defect,
four-player support, manual PS1 multitap, and Sunshine/Moonlight production
integration are not open issues.

## UDP transport: two separate entries

**Read this first.** What was one entry is now two, because the evidence
separated them on 2026-09-22.

### Entry 1 — the synthetic burst/gap/duplication pathology: PAUSED

**Symptom.** The Prototype 1 environment could transform nominally paced
UDP traffic into large arrival bursts/gaps and produce **same-stamp
duplicates**, reproduced by synthetic probes **without game load, in both
directions**.

**It is not a Windows-only artifact, and saying so would be wrong.**
`docs/memory/investigations/DEFERRED.md` ("Linux + home Opal + onn UDP
transport root cause", PAUSED after the D083 closeout) records that the
pathology **was replayed from a Linux sender and reproduced
bidirectionally while idle**, that a Linux-only sender implementation
cannot explain it, that `wlan0`/`wlan1`/`br-lan` capture points on the
Opal were **zero-record during confirmed traffic**, and that disabling
OpenWrt flow-offload did not repair it. Proprietary Siflower components
remain in the unresolved region. **D082 is the last valid router-boundary
measurement; D083/D083R1 are invalid as networking evidence.**

**What `D-BASE-B2` changed.** That replay ran on what was then called the
"representative Linux path" — but **the Windows PC was still in it**, a
fact not known when the wording was written. Since `B2` (2026-09-21) the
host is wired directly into the Opal. `B2` compared the two arms and could
**neither implicate nor exonerate** the PC: loss/min median fell only
**2.8x** where the pre-registration required an order of magnitude, the
loss stayed bursty (**4.46** packets per forward-gap event against 11.17),
and **the arms overlapped**, with three PC-path sessions quieter than
every Opal session. **Same-stamp duplication was never re-measured on the
wire** — `duplicate_highest_packets` is 0 in all 29 client reports of both
arms, which is the receiver's view, not the link's.

**So: the synthetic suite has never been replayed on the current
production topology**, and duplication in particular is untested there.
**Status: PAUSED, not resolved.** What would move it: replaying the
preserved synthetic suite on the post-`B2` `Linux + home Opal + onn` path,
or on a different representative router. Do not continue open-ended
router/vendor reverse engineering, and **do not tune product buffering,
bitrate, FEC or decoder thresholds to hide it.** Records:
`docs/memory/investigations/DEFERRED.md`,
`docs/memory/evidence/B2_HOST_ON_OPAL_2026-09-21.md`; full chronology
`investigations/2026-09-07-udp-transport.md`.

### Entry 2 — the in-session packet loss on the production path: RESOLVED

**This is a different fault from Entry 1** — measured under real game
load, on the post-`B2` topology, in the per-second loss counters rather
than in a synthetic probe. Entry 1's duplication signature does not appear
here at all: `late_or_reordered_packets` is **0 across 11 M packets**.

**Cause.** A per-frame micro-burst meeting the wireless hop. The CBR
encoder emits one frame in a hundred as an 80-plus-packet burst at line
rate; that burst overflows the access point's per-station queue; the client
records a forward gap. Established **by intervention, not inference**
(`D-BASE-P6`, 2026-09-21).

**Fix, adopted.** `max_frame_size_bytes = 90,000` is a declared field of
`native_game_720p60_reference` (`D-BASE-P6a`, 2026-09-22), in force with
nothing set in the environment. Loss falls **7-9x** with achieved bitrate,
fps, encoder CPU and GPU power unchanged.

**Residual, measured over three hours** (`D-BASE-S3`, 2026-09-22):
**5.4 losses/min**, 0 resyncs, 0 client socket drops, fps 59.96, hourly
totals trending down (380/340/253). **The residual tracks nothing** —
every Spearman under **0.08** across 1,080 ten-second and 180 per-minute
windows, and the bucketed loss table is flat where uncapped it rose
14-fold. **A tighter cap is not a lever; the loss column is closed at this
level.**

**Reopen conditions** (from `docs/memory/CURRENT.md`, "Do Not Reopen
Without New Evidence"): a sub-second airtime instrument; a driver whose
`tx failed` is independent of `tx retries`; or a moving `drops` column on
the client's socket. Absent one of those, do not re-derive this column.
**Do not revive** loss-as-`host_sent − client_received` (`D-BASE-P4`
measured it at 29x noise) — use the heartbeat's cumulative counters.

**One testing trap:** the driver's `max_frame_size` is a **target, not a
hard ceiling**. Frames land up to ~0.02 % over it. Check with a tolerance,
never `<= 90000` exactly.

### The chronology, 2026-09-21 onward

The subsections below are the investigation in order. **The last three are
the ones to read.**

### Current conclusion — updated 2026-09-21, the cause is identified

**Superseding the 2026-09-15 reading.** As originally written, this section
said the investigation did not establish which network component was at
fault, and listed endpoint Wi-Fi/driver/firmware behaviour, network-device
behaviour, offload/bridging/routing effects and RF scheduling as open
possibilities. **That list is now closed.**

**The cause is a per-frame micro-burst meeting the wireless hop**, and it
was established by intervention, not inference: capping the encoder's
largest frame removes the burst and **7-9x of the loss with it**
(`D-BASE-P6`).

| candidate | state |
| --- | --- |
| the Windows PC as sole cause | **excluded** as sole cause (`B2`); not exonerated |
| the host's send path | **excluded** — relay `send_errors` 0, host UDP `SndbufErrors` 0 (`P3`, `P5`) |
| the air / interference / contention | **excluded** — channel ~93 % idle, no Opal counter moves with the loss (`P4`, `O1`) |
| the Opal's forwarding | **excluded** — every interface `dropped`/`errors` constant 0 (`O1`) |
| the onn's receive path | **excluded** — its UDP socket dropped 0 of 4,349 (`P5`) |
| **a per-frame burst at the wireless hop** | **the cause** — correlated by `P5`, **demonstrated by `P6`** |

The loss is also **reproducible from stream position** rather than
environmental: the same attract loop loses in the same minutes across
sessions. The sections below are the chronology; **the last three are the
ones to read.**

### Which side of the Windows PC it lives on — measured 2026-09-21 (`D-BASE-B2`)

Until 2026-09-21 the host's Ethernet ran to the **Windows PC**, so every
session on disk was measured on host -> PC -> Opal -> onn — the same machine
whose burst/gap/duplication pathology this section records. `D-BASE-B2` moved
the host onto the production path (wired directly into the Opal, onn wireless,
one hop, gate-checked on the host) and re-measured.

**The pathology does not live wholly in the Windows PC.** With the PC out of
the path, across six attract-mode sessions:

- loss/min median **16.6** against the PC-path arm's **46.3** — a 2.8x fall,
  where the pre-registered reading required an **order of magnitude** to
  implicate the PC;
- loss is **still bursty**: **4.46 packets per forward-gap event** against
  11.17, where uniform independent loss would give ~1.0 and A2.2's own
  burstiness threshold is 1.5;
- forward-gap events **did not vanish** — 7 per session against 11.

**And the two arms overlap**: the PC-path arm spans 0.0-206.7 loss/min and
contains the whole Opal range of 7.0-24.1, with three PC-path sessions quieter
than every Opal session. Against a day-to-day swing of 12.6x in the Group A
medians, a 2.8x median shift is **not a verdict**. Every transport column did
move the same way at once (max forward gap 2.84x, max output gap 1.75x, spikes
1.82x) and the Opal arm is markedly tighter, so a real improvement is
plausible — but six sessions in one 17-minute window cannot separate it from a
quiet quarter of an hour.

**So: the burst shrank and stayed bursty. The Windows PC is neither
implicated nor exonerated, and this entry stays open.** Same-stamp
duplication was not re-measured on the wire; `duplicate_highest_packets` is 0
in all 29 client reports of both arms, which is the receiver's view, not the
link's.

Record: `docs/memory/evidence/B2_HOST_ON_OPAL_2026-09-21.md`.

### Is it the host's own send burst? Tested 2026-09-21 (`D-BASE-P3`)

The encoder emits a frame's packets back to back at line rate, so every
frame is a micro-burst into the wireless queue. A diagnostic sender pacer
in the FEC relay (`PRIVYHUB_FEC_PACING_US`, environment, **default off**)
spread each frame's packets instead, clamped so a frame is still out within
8 ms of its first packet arriving. Fifteen 120 s sessions, strictly
alternating with the companion restarted for each, 0 rejected.

**The account is neither confirmed nor dead.** Loss per minute fell in only
**3 of 5** pairs and the medians **1.72x**, short of the pre-registered 4
of 5 and 2x; packets per gap did fall in **4 of 5** and the median maximum
forward gap **halved, 16 → 8**; and **`spike_20_ms`/min rose in 5 of 5**,
+41 %, which the criterion forbids. At 400 µs the achieved spacing reaches
only 187.5 µs and loss fell in **0 of 2** pairs, so the effect does not
scale.

**Read that null with its bound.** Spacing is capped at
`8000 µs / packets-in-frame`, so a frame is clamped above **53 packets** at
150 µs; the mean frame is **15.85** and **11 %** exceed 53. **The large
frames this account blames are exactly the ones the budget refuses to
spread**, so pacing was tested hardest where it applies least. A stronger
test needs a larger frame budget, which costs latency and is a product
decision. Separately the unpaced arm swung **1.8-35.2 loss/min inside one
hour**, so five pairs cannot resolve a 1.7x effect against it.

**Nothing was adopted and the knob defaults to off.** Record:
`docs/memory/evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md`.

### Is it the air? Tested 2026-09-21 (`D-BASE-P4`)

Radio telemetry read from the onn over adb beside seven sessions, no code
change. **The onn is on 5 GHz** — 5180 MHz, channel 36, 80 MHz, 802.11ac,
866 Mbps ceiling, supplicant `COMPLETED` and **never re-associated**.

**The radio does not move with the loss.** Loss/min swung **1.4 → 105, a
74x range**, while RSSI spanned **5 dB in total** across 639 three-second
samples with a median of **−66 in every session**, and **not one scan of any
kind** was logged inside any session window. At **n = 597** heartbeat ticks
in a 20-minute session the client's receive rate against RSSI gives
**rho = −0.022**, against Tx link speed **−0.001**; the 5 % of ticks more
than 10 % below median rate all sit at ordinary RSSI.

**What could not be tested, and it is the half that matters most here.**
This client exposes **no retry, failure, airtime or channel-occupancy
counter** — `tx_retry`, `tx_bad`, `bcnCnt`, `total_tx_retries`,
`total_tx_bad`, the `/proc/net/wireless` discard columns and missed-beacon
count are all identically 0, `noise` is −256, `channel_utilization_ratio` a
constant 15. **Signal strength, association, link rate and background
scanning are excluded as the cause. Interference and airtime contention are
not excluded — they are invisible from this device**, and settling them
needs the Opal side or a client that reports retries.

**The loss is episodic.** A 20-minute session lost **105/min at 14.89
packets per gap** against 3.0-7.0 in two-minute sessions with identical
radio readings — bigger bursts accumulating over longer observation. **Short
sessions sample this pathology badly**, which is the best available account
of the swing that has made every previous arm overlap.

**`D-BASE-R5` (2026-09-21) then made the series directly measurable** and
confirmed it at sixty times the resolution: inside one 20-minute session
the per-minute loss ran **0, 2, 4, 5, 7, 9, 72, 78, 87, 128, 146, 152, 159,
161, 203, 228, 230, 236, 303** — **0 to 303 per minute** with the RSSI
moving 2 dB and the link speed not moving at all. **Minute 6 lost 303
packets and minute 15 lost none, at the same RSSI and the same link
speed.** The per-minute series is now read straight from the heartbeat log
(`TOOLS.md`); the derived-from-counters approach `D-BASE-P4` abandoned is
not needed and should not be revived.

### And the Opal's own view? Read 2026-09-21 (`O1`) — still not the air

The access block is gone; the router was read **read-only** over `ssh opal`
beside two 20-minute sessions — 40 minutes, 269 sampling rounds, 1,196
heartbeats — and it gives the retry and airtime counters the onn cannot.

**Neither airtime nor the Opal's radio is implicated.** Client loss swung
**0-331/min** while every Opal reading stayed flat: channel utilization
**rho −0.434** per minute — *and on the wrong sign*, a busier channel going
with **less** loss — **−0.008** at 10 s, `tx retries` **+0.219**, and
`rx drop misc` plus **every** `dropped` and `errors` counter on `wlan1`,
`br-lan`, `eth0` and `eth0.1` **constant 0** for the whole 40 minutes. The
24 worst ten-second windows read **6.78 %** utilization against **6.94 %**
in the 141 windows that lost nothing at all. In absolute terms **the
channel is ~93 % idle while the game streams** (2.9-3.3 % idle, 6.9 % under
load), so sustained contention is not merely uncorrelated with the loss —
it is **not present**. Retries do run **10.2-11.3 %** of transmitted
packets at −70 dBm, and they do not track the loss.
**`iw dev sta0 link` and `iw dev sta1 link` both read `Not connected`**, so
the 5 GHz radio is not time-shared with a wifi uplink.

**And the loss is reproducible.** The per-minute loss series of two
sessions started three minutes apart agree at **Pearson 0.964** while their
totals differ:

```text
A  4  2 214  8 123 180 121  0  84  89 188 115 272 17 90 0 242 331 148  2
B 12 30 212  3  94 173 135  4 103  80 162 121 204  0 72 2 183 251 185 14
```

Each session relaunches the title, so the attract loop replays and **the
loss follows the replay**. **No wall-clock account — a neighbour, a
microwave, a scan, a thermal ramp — can produce a shape that repeats on
restart.**

### Which queue, then? Answered 2026-09-21 (`D-BASE-P5`)

Two queues were left standing: the AP's per-station wireless queue and the
onn's own receive path. `P5` put three instruments on one clock across two
more 20-minute sessions — **packets per frame** counted in the relay,
**the onn's `/proc/net/udp6` receive-queue `drops`** read over adb, and the
`D-BASE-R5` heartbeat loss counters.

**The onn's receive path is not the queue.** Its UDP socket discarded **0
datagrams in 40 minutes** — 0 of 4,349 lost packets, **0 of 240**
ten-second windows, on the video and the audio socket both. `rx_queue`
peaked at **480,512 bytes of a 2 MiB buffer**, a quarter used at its worst.
Below the socket, `wlan0` `rx_errors`, `rx_missed_errors`,
`rx_over_errors` and `rx_fifo_errors` are **all +0**, and device-wide UDP
`RcvbufErrors` moved **+1** in twenty minutes. **A larger client receive
buffer is not a fix** — ruled out rather than assumed.

**One counter on the onn looks like the answer and is not.** `wlan0
rx_dropped` advances **+36,988** over a session, **16.6x** the loss, but
does **not** track it — per minute Spearman **0.040**, Pearson **−0.123**,
ranging 203 to 8,154 against a loss range of 0 to 293, with every hardware
error counter beside it at zero. It is the ordinary Android
broadcast/multicast filter on a busy home network. **Never read it as
stream loss.**

**The loss tracks the frame-size tail.** Max packets per frame gives rho
**0.583** over 240 ten-second windows and **0.780** over 40 minutes;
`frames >= 80 packets` **0.569** and **0.779**; forward-gap events the
same. Meanwhile **frame rate and mean frame do not move at all** — 599-601
frames per 10 s, mean 12.96-14.20 packets — so nothing about the *volume*
of traffic changes. **Only the tail moves, and the loss moves with it.**

**The distribution**, ~72,600 frames a session at CBR 7000 kbps:

| | p50 | p90 | p99 | max | >= 40 pkt | >= 80 pkt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| session A | 11 | 29 | **82** | **207** | 3.99 % | 1.01 % |
| session B | 11 | 29 | **78** | **208** | 4.03 % | 1.00 % |

**The shape is the problem, not the rate.** A nineteen-fold spread between
the median frame and the p99, emitted back to back at line rate into a
wireless queue.

**So the mechanism is a per-frame micro-burst meeting the wireless hop** —
the AP's per-station queue or the air during the burst. It is **not
observed directly and cannot be on this AP**, whose `tx failed` is a copy
of `tx retries` (`O1`), so retry exhaustion is unreadable. The case is that
**everything else on the path now reports zero** and the one thing that
moves with the loss is how big the burst is. Three earlier results fall
into place: **`P3`'s bounded null** (its 8 ms budget clamps above 53
packets a frame — exactly this tail), **the audio/video split** (0.024 %
against 0.214 % on one radio in one second), and **the content-lock** (the
frame-size tail repeats across sessions at Pearson **0.996**, more tightly
than the loss at 0.890).

Records: `docs/memory/evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`,
`O1_OPAL_AIR_VIEW_2026-09-21.md`,
`D_BASE_P4_AIR_TELEMETRY_2026-09-21.md`,
`D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`.

### Controlled 2026-09-21 (`D-BASE-P6`) — and that settles the cause

`P5` left a correlation: loss rises and falls with the count of large
frames. `P6` **intervened on that variable** across seven 20-minute arms
with baseline bookends, and the loss followed.

| arm | encoder | loss | ≥80-pkt frames | max frame | achieved kbps |
| --- | --- | ---: | ---: | ---: | ---: |
| A0 | default | 2,696 | 718 | 242,418 B | 6,928.9 |
| **A1** | **`-max_frame_size 90000`** | **311** | **0** | 89,996 B | 6,929.7 |
| A2 | `-max_frame_size 60000` | 299 | 0 | 60,092 B | 6,929.2 |
| B1 | `-bufsize 117k` (VBV) | 938 | 0 | 17,144 B | 6,931.3 |
| A0′ | default | 2,189 | 717 | 244,794 B | 6,930.0 |
| A1r2 | `-max_frame_size 90000` | 408 | 0 | 89,937 B | 6,929.7 |
| A0r2 | default | 2,896 | 734 | 247,170 B | 6,929.9 |

**8.7x and 7.1x on two independent pairs**, against a pre-registered bar of
2x. Forward gaps 306 → 105, maximum forward gap 61 → 13-27 packets, spikes
61.6 → 33-35 per minute, fps 59.58 → 59.88; audio loss falls too.

**The causal pattern, not just the totals.** Windows assigned to the bucket
of their largest frame:

| bucket | A0 loss/window | A0r2 | A1 | A1r2 | B1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| < 40 packets | 3.33 | 4.62 | 1.63 | 2.88 | **7.79** |
| 40-59 | 2.45 | 2.71 | 2.83 | 4.91 | — |
| 60-79 | 1.27 | 3.79 | 2.69 | 2.75 | — |
| **≥ 80** | **42.5** | **45.5** | *(none)* | *(none)* | *(none)* |

**In both baselines the ≥ 80 bucket carries 93-95 % of all loss at ~14x
the loss per window of anything below it.** Capping deletes that bucket
**while the small-frame buckets stay where they were** — which is the
bucket-specific evidence that distinguishes cause from coincidence.

**The knee was measured, not assumed.** Bucketing A0's windows by their
largest frame in bytes gives **1.2-4.2 loss/window up to 100 KB and 46.3
above it** — a step, not a slope. A1's cap was set just under it and A2's a
third lower.

**And it costs nothing this run can measure.** Achieved bitrate spans
**6,928.9-6,931.3 kbps across all seven arms** (0.03 %); encoder CPU
**26.6-26.9 %**; GPU power overlapping. A cap does not starve the stream,
it redistributes inside it.

**Two bounds on the finding.** The benefit **saturates** — A2 constrains a
third harder for no further gain (299 vs 311) — so the looser cap is the
better setting. And **conventional rate control is a different lever, not a
better one**: B1 flattened hardest of all (every frame 14-16 packets, its
per-0.5 s bitrate range 6,661-7,168 against the default's 64-15,792) yet
lost **3x more than the cap**, and it is **the only arm that raised loss in
windows that had none**. It trades the tail for a higher floor.

**Drift was flagged and survived.** The three baselines ran 2,696 / 2,189 /
2,896 — ±15 %, wider than expected — while their frame distributions stayed
near-identical (≥ 80: 718/717/734). The environment moved; the content did
not; each pair clears the bar against its own bookend.

Record: `docs/memory/evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`.

### Resolved on the Linux host path, 2026-09-22 (`D-BASE-P6a`)

**The user made the judgement and adopted the fix.** Having played the
capped arm for about a minute — **no stutters, "could barely tell it was
over the LAN"** (their words, 2026-09-22; a user-stated perceptual result,
not instrument evidence) — they decided to adopt.

**`max_frame_size_bytes = 90,000` is now a declared parameter of the
`native_game_720p60_reference` profile**, in force with nothing set in the
environment. Validated the same day: **loss 249** against an uncapped
2,690-2,896, **zero ≥ 80-packet frames**, max frame **89,874 bytes**,
bitrate **6,929.6 kbps**, fps **59.90**, zero resyncs, zero socket drops,
encoder CPU 26.6 %.

**The mechanism, stated once for the record:**

> **frame-size tail → large-frame burst → wireless queue overflow →
> forward gaps at the client.**

The encoder is CBR, so the *average* rate never moved; what moved was the
*shape*. One frame in a hundred was 80+ packets emitted back to back at
line rate, that burst overflowed the AP's per-station queue, and the client
saw it as a forward gap. Capping the frame bounds the burst. The encoder
spends the same bits — the cap only changes when it may spend them.

**Scope of this resolution.** It is the **Linux host path** only. The
Windows-era burst/gap/duplication pathology recorded at the top of this
section is a **separate deferred note** — measured on a different encoder,
a different capture path and a different machine — and **nothing here
claims it fixed**. The Linux fix is an `h264_vaapi` profile parameter; the
NVENC path ignores the field and logs that it does.

**The uncapped path remains available** — `PRIVYHUB_ENC_MAX_FRAME_SIZE=0`
runs with the flag absent — so the pre-fix behaviour can be reproduced for
comparison at any time without editing source.

**Measured alternatives, not chosen:** a 60,000-byte cap (ties on loss,
constrains a third harder) and VBV `-bufsize` at the one-frame budget
(smoothest bitrate, best spike rate, but 3x the loss and it raises loss in
windows that had none). Both stay reachable through the overrides.

Records: `docs/memory/evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`,
`D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`;
`docs/memory/decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

### The audio starvation counter, named 2026-09-22 (`D-BASE-P7`)

`audio.prolonged_starvation_events` was the last counter in the decoder
report whose meaning was unknown, and it was read as a fault because 32-76
a minute sounds like one. **It is an audio arrival-gap counter**: the code
latches it, so it increments **once per hole in the audio arrival stream
longer than ~15 ms**, never twice for the same hole. Episodes, not polls.

**It measures jitter, not loss** — rho **+0.684** against the per-tick
maximum audio inter-arrival gap over 596 ticks, **+0.020** against audio
loss, and a packet deficit averaging **+0.54 of ~400 expected**, i.e. no
packets missing, only late.

**The hole is periodic and it is not the sender's**: 93 % of ticks show a
largest gap of **50-69 ms**, while the host's audio pacer measures **5.0 ms
average, max 5.08**. The jitter appears between the host's socket and the
onn's, and the rate is therefore a property of the path — 75.9/min on the
old PC path, 32/min on the capped Opal path.

**Read it as a path-jitter rate, not a fault.** 32/min accompanied **4
actual underruns in 20 minutes**. The only client-side lever is a deeper
audio cushion — the queue target is **3 packets (15 ms)** against a p90
hole of **60 ms**, so absorbing it costs about **+45 ms of audio
latency** — and sender-side pacing is closed by measurement. Nothing was
changed and the counter was not renamed; the name is accurate.

**Narrowed by `D-BASE-P8` (2026-09-22):** the holes are ~100/min at
≥ 40 ms (half 50-60 ms), **not aligned with the client's heartbeat or
client-health posts** (5.7-6.6 % within 100 ms of a send, uniform 5 %),
and unchanged by removing the adb socket sampler (-1 %) or slowing the
heartbeat to 10 s (-11 %). The hole is the path's; the AP's per-station
scheduling is the remaining, unmeasured candidate. Records:
`docs/memory/evidence/D_BASE_P8_AUDIO_HOLE_ORIGIN_2026-09-22.md`,
`docs/memory/evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`.

### Product decision

Do not encode this environment’s measured jitter/duplicate rate into product
buffering or transport architecture.

Preserve the diagnostics. After Phase D establishes the representative native
Linux baseline, replay the acceptance suite during Phase E Linux
resource/transport characterization unless the issue becomes a blocker sooner.

Full record: `investigations/2026-09-07-udp-transport.md`.

<!-- PRIVYHUB_CONTROLLER_LOST_PACKETS_UNDER_PLAY:KNOWN_ISSUES:BEGIN -->
## 2026-09-24 controller transport `lost_packets` under real play — observed, not investigated

- **The controller transport's `lost_packets` rose 76 → 3,177 in ~9 min of
  real play** (the `C3.L3a` smoke session, run `20260924_000330`, preflight
  to state write): **~345 / min**, against ~23 / min on the 2026-09-20
  `C3.L3a` session (287 → 498 over a similar span). `bad_packets` stayed 0,
  and the user reported nothing wrong with input. The counter is a
  sequence-gap count on the client's input datagrams
  (`companion/native_session_io.py`: each jump in the 32-bit sequence adds
  the missing count). **It has never been read under play in the `D-BASE`
  era**: every `D-BASE` session was an attract-mode hold with zero input,
  so there is no baseline for it on the adopted build. Cause not
  investigated; whether this is loss, or the client skipping sequence
  numbers by design, is not known. Status: **open, observed not
  investigated.** Record:
  `docs/memory/evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md`.
- **Zero-input baseline, 2026-09-24 overnight (`C3.L3a-S1`)**: with no
  input the client sends ~25,700 controller datagrams a minute, and the
  counter reads **213-438 lost / min** (0.8-1.8 %) across seven attract-mode
  sessions, `bad_packets` 0; the close-out's own C / W status files give
  ~630 / ~680 / min, also zero input. **The ~345 / min under play is inside
  the zero-input range; play does not raise it.** The 2026-09-20 ~23 / min
  is the outlier. Still open, still not investigated. Record:
  `docs/memory/evidence/C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md` (item F).
- **The `C3.L3a` rerun sessions, 2026-09-24, under play**: session 1 (run
  `20260924_115810`) 15 → 3,868 over ~17.2 min, **~225 / min**, inside
  the zero-input band; session 2 (run `20260924_130016`) **1 → 60** over
  ~15.5 min (run start to state write), **~3.8 / min**: ~60× lower than
  session 1 and below every zero-input session, on the same build, host
  and day, about an hour apart. `bad_packets` 0 in both. Recorded as a
  fact; no cause proposed. Record:
  `docs/memory/evidence/C3_L3A_R2_SESSION2_2026-09-24.md`.
- **Session 3** (run `20260924_151953`, under play): **0 → 95** over
  ~16.9 min (run start to state write; the counter started at 0 after the
  companion's 18:00:52Z restart), **~5.6 / min**, `bad_packets` 0 — near
  session 2, below every zero-input session. Record:
  `docs/memory/evidence/C3_L3A_R3_SESSION3_2026-09-24.md`.

  | session | run | lost / min | `bad_packets` |
  | --- | --- | ---: | ---: |
  | rerun 1 | `20260924_115810` | ~225 | 0 |
  | rerun 2 | `20260924_130016` | ~3.8 | 0 |
  | rerun 3 | `20260924_151953` | ~5.6 | 0 |
- **LOCATED 2026-09-24 (`CTRL-L1`): PATH.** Three plain 20-min holds
  (cold, warm, warm) read +171 / +266 / +301 lost (9-15/min). Over the
  same holds every host-side counter read +0: the controller socket's
  `drops`, Udp RcvbufErrors / InErrors, softnet dropped, NIC rx_dropped /
  missed / fifo / errors. So did every Opal interface counter. The onn's
  UDP stack sent everything (SndbufErrors +0).
  - **Where the datagrams go missing**: between the onn's UDP stack and
    the host's NIC, the stretch `T3` located the reverse audio loss in.
  - **What the counter counts**: sequence gaps on one global sequence
    over the four player datagrams of each tick. A reordered pair counts
    2, and a client send error counts 1.
  - **Most of it is true non-arrival.** The per-player lower bound puts
    85-95 % of it there in the high-loss sessions, and ≥ 40-67 % in
    these holds.
  - **The capture was not run** (no tcpdump, no root).
  - **The swing between low (≤ 15/min) and high (200-650/min) regimes is
    not explained.** The client's send rate is the same in both
    (~25,960/min).
  - Status: **located, not fixed**; nothing to fix on the host. Record:
    `docs/memory/evidence/CTRL_L1_CONTROLLER_LOSS_LOCATION_2026-09-24.md`.
<!-- PRIVYHUB_CONTROLLER_LOST_PACKETS_UNDER_PLAY:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_DECODER_REPORT_OVER_SIZE_CAP:KNOWN_ISSUES:BEGIN -->
## 2026-09-24 end-of-session decoder report not received after BACK (session 2): rejected as too large — MITIGATED 2026-09-24 (cap 48,000), RUNTIME VALIDATED 2026-09-24 (session 3)

- **What happened.** `C3.L3a` rerun session 2 (run `20260924_130016`)
  ended with BACK at ~17:16:42Z. The client **did** post its decoder
  session report: `POST /plugins/games/decoder-session-log?report=…` at
  17:16:42.799Z. The companion answered **HTTP 400**, stored nothing, and
  logged nothing beyond the access line. Then the client's
  `native-stream-stop` (17:16:45.8Z) and `/plugins/games/stop`
  (17:16:47.9Z) went through normally.
- **Why.** `companion/games/decoder_session_log.py` refuses a report whose
  decoded text is longer than **`MAX_REPORT_CHARS = 32_000`**, and this one
  was **32,057 characters** (57 over). It was otherwise valid: a JSON
  object, schema `privyhub_native_decoder_session_v2`, 1,000.8 s, 24
  `ssrc_change` discontinuities (the run's expected 24). The other three
  refusals (empty, invalid JSON, not an object) are all false for it. The
  route turns the `ValueError` into a 400 whose `error` text is sent only in
  the response body, so the journal shows the status and not the reason.
  The reason comes from checking the rebuilt report against the source.
- **Nothing reports the loss.** The client's stop thread
  (`NativeStreamActivity.kt`, `PrivyHub-Native-Stop`) catches the exception
  that `httpPost` throws on a non-2xx and swallows it ("Logging must never
  prevent the existing stop path"). It does not retry, and nothing on the
  TV or the host shows the loss. The probe's `--finalize` later found "no
  candidate (0 rejected)".
- **The report is not lost.** The request line is in the journal (journald
  split it in two at its line limit). The report is rebuilt byte-exact at
  `docs/memory/evidence/c3_l3a_r2_2026-09-24/rejected_report_20260924_171642_from_journal.json`.
  The rebuild is checked by `report_check.py` beside it. It has not been
  fed to `--finalize`.
- **It will recur.** Reports without transitions sit at ~25.6K characters.
  `audio.arrival_holes` (~10K) and `audio.tick_series` (~8K) take most of
  that. Each SSRC change adds ~270-310 characters
  (`first_idr_after_discontinuity`, `stream_discontinuities`, the slow
  events). The S1 soak's 20-transition sessions came within **39, 116 and
  426 characters** of the cap. Session 1's two halves fit only because an
  accidental BACK split them (9 + 15). **A pre-registered rerun session
  (24 transitions in one client session) is expected to exceed the cap
  every time.** That would take sessions 3 and 4's decoder-axis check
  (`C3-L2` requirement 4) with it.
- ~~**Status: open, not fixed.**~~ **MITIGATED 2026-09-24 (`C3-L3A-R2B`).**
  `MAX_REPORT_CHARS` is now **48,000**. A refused report now leaves one
  journal line: `WARNING decoder-session-log rejected (400): <reason>;
  report_chars=<n>`. The companion was restarted through systemd and the
  adopted profile confirmed. Session 2's report, rebuilt from the journal,
  was then finalized: 24 = 24, and the decoder axis is done. Record:
  `docs/memory/evidence/C3_L3A_R2B_REPORT_CAP_2026-09-24.md`. **Runtime
  validation is PENDING** until a real 24-change session's report is
  stored (session 3).
- **RUNTIME VALIDATED 2026-09-24 (`C3-L3A-R3`).** Rerun session 3's
  24-change report was stored (`native_decoder_20260924_193658_993.json`,
  POST 200, no WARNING line): 32,435 compact characters, **15,565 under
  48,000** (it would have been refused at 32,000 by 435). Its URL-encoded
  value was 51,105 characters (ratio 1.576, request line 51,163 of 65,536
  bytes), ~9.1K under the transport ceiling. Record:
  `docs/memory/evidence/C3_L3A_R3_SESSION3_2026-09-24.md`. **Mitigated and
  validated; the body-POST follow-up below stays open.**
- **The transport's own ceiling remains: ~41.4K decoded characters.** The
  report travels URL-encoded in the request target (~1.58 encoded
  characters per decoded one), and `http.server` refuses a request line
  over 65,536 bytes before any handler runs. So 48,000 never refuses what
  the transport can carry, but a report over ~41.4K would still be lost.
  Past that ceiling nothing is logged cleanly: the 414 path calls the
  companion's `log_message` override before `self.path` exists. That
  raises an `AttributeError` traceback in the journal, no 414 is sent, and
  the client sees an empty response and swallows it. This was checked on a
  throwaway server of the same shape, not on the companion. A 24-change
  session is ~32K, so there is ~9K (~30 more SSRC changes) of room.
- **Follow-up, open: the client posts the report as a request body**
  (`NativeStreamActivity.kt`, stop thread, instead of `?report=`). The
  companion route would then read the body. This lifts the transport
  ceiling, and it is a client change (new APK). Also open, low cost: the
  client could log or surface a non-2xx on the report post instead of
  swallowing it.
- **Body-POST follow-up DONE on a comparison path, 2026-09-25 (`CL-B1`).**
  - The companion accepts the report as a POST body; the target form is
    unchanged. The cap is 128,000.
  - The 414-path `log_message` crash is fixed: a 414 is now sent.
  - The arm client posts the body. **It is not adopted**: the installed
    APK still uses the target form.
  - Record: `docs/memory/evidence/CL_B1_DECODER_REPORT_BODY_2026-09-25.md`.
<!-- PRIVYHUB_DECODER_REPORT_OVER_SIZE_CAP:KNOWN_ISSUES:END -->

## 2026-09-23 — open after the `D-BASE` close-out (baseline MET)

`D-BASE` is closed (`docs/memory/evidence/D_BASE_CLOSEOUT_2026-09-23.md`).
What stays open, recorded as open rows, not failures:

- **Max output gap** — 163 / 110 ms at close-out against the ≤ 100 ms
  target; ~100-330 ms across the capped build. The transport's: single
  loss bursts or a late IDR, not the decode path. **Open.**
- **Warm-state loss between the ends** — from ~7 min into a cold stream
  the path drops single packets between the host's NIC and the onn's IP
  stack (`T2`, `T3`); audio redundancy covers audio, FEC covers most
  video. Cause not located. **Open → `host_link`.**
- **The synthetic UDP pathology** — PAUSED (`M1`), never seen on the
  post-`B2` topology. **Paused.**
- **`host_link`** — the per-session link-type field; its first fact is
  `T3`'s. **Open, roadmap.**
- **Thermal thresholds** — proposed from `T2`/`T3` (onn cpu-thermal
  ≥ ~67.5 °C marks the warm state), none enforced; the user's call.

## 2026-09-22 open items after the baseline-stream-health chain

One line each; the record named is authoritative.

- **`D-BASE-R3b` — nftables loss injection, PARTLY RUN 2026-09-22.** The
  user drove `r3b_run.sh` by hand (the session classifier still refuses every
  `nft` write). **N3, N15 and N150 all PASS**, so `GIVE_UP_MS` and the
  `.state.recovery` save are now exercised under controlled loss, and N15
  reached the case no substitute fault could — an encoder restart that
  **succeeded while the fault was still dropping every packet**. **Narrowed
  by `R3d` (2026-09-22, hand runs): N15b PASS, E30 PASS (`END_MS`
  validated); N05 NOT RUN** — its directory is empty, the companion was not
  running. Records:
  `docs/memory/evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`,
  `docs/memory/evidence/D_BASE_R3D_HAND_RUNS_2026-09-22.md`.
  **Closed 2026-09-23**: N05 PASS (0.556 s hole, no pause, max gap
  625 ms) — `R3` + `R3a` RUNTIME VALIDATED for real loss. **Status:
  closed.**

- **A recovery restart hides the outage from `lost_packets`.** `D-BASE-R3b`
  measured it: a 3 s outage with **no** restart counted **2 348** lost
  packets; 15 s and 150 s outages that **did** restart counted **22** and
  **40**, because the new ffmpeg brings a new SSRC and the client books the
  return as an `ssrc_change` (`jump_packets: 0`), not as loss. Every
  loss-per-minute figure in the `D-BASE` column therefore under-counts
  outages that triggered a restart; **`max_output_gap_ms` is the honest
  column for them.** **Status: open — the loss column needs this caveat
  applied.**

- **`R3b-D1` — a stream-stop leaves the game session live, and the launcher
  then cannot launch.** `native-stream-stop` pauses the game and keeps the
  session by design, so after the N150 run RetroArch stayed alive and paused.
  Launching the same title from the launcher resolved to `recovery-resume`,
  which loaded the state into the running process and reported **"Loaded"**
  while **no window opened**; no `POST /plugins/games/launch` was ever issued.
  Record: `docs/memory/evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.
  **Closed 2026-09-23 by `D-BASE-R3c2`** (`docs/memory/evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`): a live session's tile is
  **Resume** (same pid, no load); the recovery prompt appears only with no
  live session, and resume-from-recovery launches fresh. **Status:
  closed.**

- **`R3b-D2` — after a recovery-state load the picture cycles through about
  four frames.** The stream itself was clean (`lost_packets 0`,
  `sequence_resyncs 0`, 59.85 fps); the **source** looped. Measured by IDR-size
  dispersion: spread **3 686 B** against **52 923-74 242 B** for live gameplay
  and **0 B** for a frozen window — so neither a freeze nor gameplay. Starts
  within one second of the core being unpaused. Cause not resolved: either the
  load-while-paused ordering or Beetle PSX HW's state restore under GL
  hardware rendering. Needs a run to separate. **Narrowed 2026-09-22
  (`D-BASE-R3c` Part 1, `evidence/D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md`):**
  the ordering, not the renderer. The N150 save (taken **mid-FMV**) loops
  whenever it is loaded into a **paused** core — a fresh core too, 3 s or
  20 s after boot (2 distinct frames per second over 30 s); loaded into a
  **running** core it plays; a **gameplay** state loaded paused plays at
  60 fps. **Closed 2026-09-23 by `D-BASE-R3c2`** (the user's option A —
  load into a fresh, running core): the N150 save now plays (607 distinct
  frames in 30 s; 61/61 distinct IDR sizes over 60 s through the client),
  and a gameplay save plays at 60 fps (1,630 distinct). `docs/memory/evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`.
  **Status: closed.**

- **The `.state.recovery` file survives being consumed.**
  `load_recovery_state` stages it as slot 0 and does not remove it, so the
  recovery prompt reappears on the next launch of that title. The Tekken 3
  pair is being kept deliberately as the evidence for `R3b-D1`/`R3b-D2`.
  **Closed 2026-09-23 by `D-BASE-R3c2`**: a successful resume, a copy
  to a slot and a discard each delete the file, its `.png` and the index
  (checks 2-4). The N150 copy stays under
  `docs/memory/evidence/d_base_r3c_2026-09-22/recovery_copy/`. **Status:
  closed.**

- **`END_MS` (30 minutes) has never been exercised.** **Closed
  2026-09-22** by `R3d` E30: `PAUSED_SAVED` → `ENDED` in 1,801.4 s, clean
  RetroArch shutdown. **Status: closed.**

- **`audio.prolonged_starvation_events` is characterized, not a fault.**
  `D-BASE-P7` (2026-09-22) established it counts **one hole in the audio
  arrival stream longer than ~15 ms**, episodes not polls, and measures
  **jitter, not loss** (rho +0.684 against the arrival gap, +0.020 against
  audio loss; the packet deficit averages +0.54 of ~400, so nothing is
  missing, it is late). 32/min accompanied **4 actual underruns in 20
  minutes**. **Status: not a defect.** `P8` (2026-09-22) cleared the
  heartbeat and the adb socket sampler as causes; the hole is the path's
  (AP scheduling the remaining candidate, unmeasured). The only client lever is a deeper cushion at about
  **+45 ms of audio latency**, which has not been spent. Record:
  `D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`.

- **Thermal thresholds: deferred.** `D-BASE-T1` measured both ends — the
  host's hottest sensor rises 54 -> 60 °C over ten minutes and plateaus
  (`S3` confirms over three hours). **No threshold, no throttle response
  and no action on a thermal reading exists**, and none is authorized.
  **Status: deferred**, reopen with a sustained-load complaint.

- **`host_link` is specified but not implemented.** The session record has
  no field saying which link the host was on. **Status: open** — see the
  entry above at "implement the `host_link` field".

- **The onn reports no radio or thermal detail, and that is the device,
  not a gap in the search.** `D-BASE-P4`: **no retry, failure, airtime or
  channel-occupancy counter at all**. `D-BASE-T1`: **thermal status only**,
  no zones and no headroom, reading 0 (NONE) throughout. Every such field
  is recorded as an **absence, never a zero**. **Status: closed on this
  hardware**; reopen with a different device.

- **The Opal's SSH host key is RSA-only (Dropbear).** Noted in
  `docs/memory/TOOLS.md`. It constrains which client key types work
  against the router and is a **note, not an action item** — the Opal is
  read-only from this project and nothing is installed on it.

- **The Linux host has no SSH server and no autologin** (`H2-PREP`,
  2026-09-22). `openssh-server` is not installed and every `autologin-*`
  line in LightDM's config is commented out, so a reboot stops at the
  greeter with no X session and therefore no capture. Nothing starts the
  companion at boot and `Linger=no`. **Status: blocking the headless
  cutover (`H2`)**; both are user-side root writes. Record:
  `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`.

- **Adding a heartbeat field takes two edits.**
  `companion/plugins/games.py`'s `native-stream-heartbeat` handler carries
  an **explicit key whitelist** and drops unlisted keys **silently**, with
  no warning and an otherwise healthy heartbeat. `D-BASE-P7`'s first
  session recorded no audio fields at all because of it and had to be
  re-run. **Status: a documented trap, not a defect to fix** — the
  whitelist is deliberate.

## Runtime coverage gaps: NES and Genesis

NES and Genesis are configured/supported, and earlier user testing indicated
normal behavior, but the final A9 evidence did not have local fixtures for those
families.

Current durable status is therefore:

- NES — **not runtime validated**;
- Genesis — **not runtime validated**.

Do not infer validation from configuration or from another emulator family.
Upgrade status only after a normal launch/input/lifecycle regression with a real
fixture.

## Security/privacy debt

The isolated prototype still has security surfaces that require a dedicated
hardening phase:

- Android cleartext networking;
- exported diagnostic/probe activities;
- companion network listening without mature authentication;
- normal service logging that may contain operational requester information.

These should be handled together with a threat model, authentication,
encryption, authorization and privacy review. Do not mix ad-hoc security changes
into unrelated C1 streaming work.

## Windows/Linux portability debt

The current native path intentionally uses Windows-specific components,
including WGC, NVENC/FFmpeg integration, process-loopback audio and ViGEm.

Phase D owns Linux functional parity. Phase E owns representative Linux
resource/transport characterization. The current Windows implementation remains
the validated behavior reference until those phases execute.

## Maintainability / test debt

Large central files remain:

- Android `MainActivity.kt`;
- companion `games/emulator_manager.py`;
- companion `plugins/games.py`.

Minimal conventional CI also remains. Existing deterministic probes and runtime
evidence are strong, but they are not a substitute for future automated
multi-platform coverage.

Refactor only with a dedicated objective and explicit regression boundary.

<!-- PRIVYHUB_CLIENT_BANNER_RECONCILE:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 launcher banner does not reconcile when the companion is unreachable

`MainActivity.refreshGameSessionBanner()` clears the "NOW PLAYING" banner only
on a successful `/plugins/games/status` answer with `active: false`; on any
exception it logs and leaves the banner as it was. If the game is ended
host-side and the companion then goes away before the launcher resumes, the
onn keeps showing a paused game that no longer exists until the app is
relaunched or the companion comes back. Seen after the first autonomous
session on 2026-09-20. Status: **open, client UX, low priority** — the
operational rule (end the game via the client, stop the companion last) is
in `docs/memory/TOOLS.md`; a client fix would treat companion-unreachable as
"no active session" after a bounded retry, or poll status periodically while
the banner is visible.
<!-- PRIVYHUB_CLIENT_BANNER_RECONCILE:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_LINK_DROP_RESILIENCE:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 link-drop resilience — `D-BASE-R3` + `D-BASE-R3a`

**Status: built, installed, RUNTIME VALIDATED FOR THE SUBSTITUTE FAULT, and
as of 2026-09-22 exercised against real on-the-wire loss by `D-BASE-R3b` —
N3, N15 and N150 all PASS, but N05, N15b and E30 were not run, so the set the
handoff requires is incomplete and this is NOT yet RUNTIME VALIDATED for real
loss.** `D-BASE-R3b` record:
`docs/memory/evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`; two
post-run defects in
`docs/memory/evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.
Records: `docs/memory/evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md`
and `docs/memory/evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`.
Patches: `docs/memory/patches/D-BASE-R3_LINK_DROP_SELF_RECOVERY.md`,
`docs/memory/patches/D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md`.
Design and constants:
`docs/memory/investigations/LINK_DROP_RECOVERY_DESIGN.md`.

The behaviour the user specified is in place: the host pauses the game on
desync, keeps restarting the encoder with backoff, resumes only after the
client passes the stabilization gate again, and after `GIVE_UP_MS` saves the
game to its own file and stays paused with the launcher saying so. Observed
constants: pause 1.3-1.7 s after the fault; give-up at 120.243 s against
120,000; backoff 5 / 10 / 20 / 30 / 30 s; recovery save
`<stem>.state.recovery`, never a slot.

**Both `D-BASE-R3` defects are FIXED by `D-BASE-R3a`** (2026-09-20,
`docs/memory/evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`,
`docs/memory/patches/D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md`):

- ~~A failed encoder restart is terminal~~ **fixed.** When the session has
  no encoder the recovery now calls the same `NativeStreamManager.start()`
  `native-stream-start` uses instead of re-entering the `C3.L1` cycle, and
  logs `method: "full_start"`. Confirmed on two runs that the pre-fix build
  left stuck in `PAUSED_RECOVERING`.
- ~~The restart decision reads a heartbeat up to 2 s stale~~ **fixed.** It
  now needs the two newest heartbeats both at or above `DESYNC_MS` with the
  newer not lower, and the newer received at or after the restart became
  eligible; each line logs `age_pair_ms`. A 3 s outage records `restarts`
  **0** where the pre-fix build restarted every time.

**What is still open:**

- **The nftables runs are owed.** Every run so far used a substitute
  (SIGSTOP on the managed encoder) because this host has no
  non-interactive root (`sudo -n nft …` → "a password is required"). Loss,
  sequence jumps and FEC during an outage are therefore untested, and so is
  a `C3.L1` restart whose replacement encoder is alive but unheard. A
  passwordless `sudo nft` rule, or an equivalent, is the unblock.
- **The host-side controller-silence trigger is unexercised.** Every run was
  triggered by the client's own notice, because no host-side fault
  interrupts the client->host controller channel. Testing it needs the
  client stopped, not the link.
- **`END_MS` (30 minutes) was never exercised.**
- **Two of the plan's pass criteria are not reachable as written**, and
  `D-BASE-R3a` measured why: "resume within 2.5 s" is below the gate's
  baseline-plus-three-ticks 2.0 s floor plus encoder resume time, and
  "within one backoff interval" on a 15 s outage is dominated by
  `_kill_managed_process` waiting 5 s on a `SIGTERM` the *substitute*
  injector's stopped encoder cannot act on.

The original statement of the requirement, and the freeze that prompted it,
are preserved below.

---

## 2026-09-20 link-drop resilience — stated requirement, not yet owned

During the first play session on the `C3.L2c` build the stream froze once
(onn on a stale frame, host still running) and did not recover, coincident
with a house-network disturbance the user observed independently (chats
arriving out of order). Not attributed to the build: the only report from
that period (`native_decoder_20260920_173423_609.json`, 1,133 motion
events) scores like the attract sessions. Happened once.

**Requirement (user, 2026-09-20):** when the Linux host is a headless
server, a Wi-Fi drop must self-heal end to end — the client must detect a
dead stream, resync or restart it, the companion must keep or restore
session state, and the launcher must reflect reality — without anyone
accessing the host. Today none of that is automatic: a long outage leaves
the client frozen or on a stale banner and the fix is manual.

Pieces that exist: sequence/SSRC resync and IDR wait in `RtpH264Receiver`
(recovers from gaps that end), the actuator's encoder-only restart primitive
(`C3.L1`), `tools/recover_orphan_game_session.py` (host side). Pieces that do
not: a client-side "no output for N ms" watchdog that re-requests the stream
or returns to the launcher with state intact; a companion-side stream
liveness check that restarts the encoder when the client reappears; a
launcher that reconciles from a failed poll (see the banner issue below).
**Behaviour, as the user specified it (2026-09-20, late):**

1. **Pause on desync.** The moment the session looks desynced — the client
   has stopped getting decoder output, or the host has stopped hearing
   from the client — the game is paused on the host so it does not advance
   while the player is blind. The pause must be host-side: when the link
   is down the client cannot ask for it, so the companion pauses on its own
   when the client's heartbeat (`D-BASE-R2`) goes stale.
2. **Auto-recover.** Host and client keep trying to re-establish the stream
   on their own — client re-requests `native-stream-start`; companion
   restarts the encoder with the validated encoder-only restart primitive
   (`C3.L1`) when the client reappears — with backoff, for as long as it
   takes, with no one touching the host.
3. **Resync check before resume.** The game unpauses only when a separate
   check says the stream is actually good again: reuse the startup
   stabilization gate (clean frames, fps, gap — `C3_STARTUP_STABILIZATION`)
   that already gates the first unpause via `native-stream-ready`. Same
   gate, second use.
4. **Give up safely.** After a bounded time, save state, leave the game
   paused, and make the launcher say so. Nothing is lost and nothing is
   left running blind.

Detection thresholds, backoff, and the give-up bound are the design
note's to propose; the four steps above are settled. Status: **open,
registered, behaviour decided, not yet authorized for code.** Prerequisite:
`D-BASE-R2` (the heartbeat is the host-side detector). Owner: transport
(Step 3).
<!-- PRIVYHUB_LINK_DROP_RESILIENCE:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_TERMINAL_STALL_UNRECORDED:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 a terminal stall leaves no evidence in the session report

`max_output_gap_ms` is updated when the *next* frame leaves the decoder, so
a stall that never ends is never recorded, and an app killed during it posts
no report at all. The freeze above therefore has no row anywhere. Fix
direction: a "last output age" the companion polls (or the client posts
periodically), so a frozen session leaves a timestamped trace and the
companion can act on it; this is also the trigger the link-drop watchdog
above needs. Status: open, diagnostic instrumentation, low cost.
<!-- PRIVYHUB_TERMINAL_STALL_UNRECORDED:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L2A_E2:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L2b reporting defect

- ~~`slow_events_marked` is emitted as an empty array.~~ **CLOSED
  2026-09-20 (`D-BASE-R4` item 3), no code change needed.** That key does
  not exist on the current code: `C3.L2b` merges the marked and recent
  segments into the single chronological `slow_events_ge_50_ms`, and the
  two retention counters say how many of each went in. Two reports already
  on disk show the merged array's length equal to marked + recent exactly —
  `d_base_r2_2026-09-20/native_decoder_20260920_180217_204.json` (67 =
  3 + 64) and `d_base_r3a_2026-09-20/native_decoder_20260920_205736_106.json`
  (75 = 11 + 64) — and neither contains a `slow_events_marked` key. The
  marked window is inspectable row by row. Record:
  `docs/memory/evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`.

- **Decoder time correlates with perceptible interruption on the onn client,
  but is not its mechanism.** `low_latency_enabled` is false on
  `c2.realtek.video.avc.decoder`; `max_codec_ms` 367; the two largest output
  gaps in the `C3.L2a` E2 session, 359 ms and 352 ms, tracked `codec_ms` to
  within 8 ms with feed delay at zero. `C3.L2c` then cut `max_codec_ms` to
  107 ms and `max_output_gap_ms` got **worse** (385 ms), which falsifies
  `max_codec_ms` as a proxy for the gap. Status: open, owner unassigned —
  `C3.L2c` is closed as falsified and is not the owner. Any future candidate
  justified by "it lowers decode time" must measure `max_output_gap_ms`
  directly before acceptance. Record:
  `docs/memory/evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`.
<!-- PRIVYHUB_C3_L2A_E2:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG:KNOWN_ISSUES:BEGIN -->
## 2026-09-19 C3.L3 characterization probe finalize bug

Found during `C3.L3` Linux fixed-bitrate characterization (third run).
Corrected 2026-09-19 by `C3-L3R1`: the original entry misidentified the
decoder-session file involved and implied the 6000 kbps result was
unrecoverable. Neither was right. The defect itself is real and stays open.

- **`--finalize` can match the wrong decoder-session file.**
  `tools/probe_c3_fixed_6000_characterization.py --finalize`, run
  immediately after `tools/probe_c3_fixed_5500_characterization.py
  --finalize` in the same sequence, returned measurements byte-identical to
  the 5500 kbps result (`session_duration_ms` 66,638, every
  decoder/controller count, `sequence_resyncs`, `ssrc_changes`) apart from
  `target_bitrate_kbps` itself, and was missing several audio fields the
  5500 result had. It had matched the 5500 kbps run's own decoder-session
  file, `logs/games/decoder_sessions/native_decoder_20260919_055703_163.json`.
  That attempt was discarded.

  **The defect is intermittent.** The 6000 kbps rerun taken the same
  session matched correctly:
  `logs/streaming/c3_fixed_6000_characterization.json` records
  `payload.decoder_session_log =
  logs/games/decoder_sessions/native_decoder_20260919_060325_369.json`, a
  distinct 64,840 ms session written 9.4 s before that finalize, whose
  figures differ from the 5500 kbps session in every field. So back-to-back
  finalizes do not fail deterministically, and the data that was thought
  lost was never lost.

  Not root-caused. Status: **open**. Affects
  `tools/probe_c3_fixed_*_characterization.py`'s decoder-session matching
  only — the `C3.L3` companion-side Linux cycle
  (`companion/diagnostics/c3_linux_actuator_probe.py`) is not implicated.

  **Workaround until fixed:** after any `--finalize`, check
  `payload.decoder_session_log` and `session_duration_ms` in the written
  JSON against the session you intended to measure, before using the
  result. A finalize that reports the previous bitrate's duration has
  matched the wrong file.

  Records: `docs/memory/evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`,
  `docs/memory/patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md`.
<!-- PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG:KNOWN_ISSUES:END -->

- **The decoder report travels as a URL query, capped at 64 KiB** (2026-09-22,
  `D-BASE-P8`). `POST /plugins/games/decoder-session-log?report=…` is refused
  with **414** once the encoded report passes 65,536 bytes, and the
  companion's `http.server` then raises `AttributeError: … no attribute
  'path'` in `send_error`. P8's first build lost two 20-minute reports this
  way; build v2 keeps the report ~40 KB. **Any new report field must stay
  bounded.** **Status: open** (moving the report to the request body is the
  fix; not done).

- **The companion was not running for the N05 hand run** (2026-09-22,
  `R3d`): the overnight queue's teardown stopped it deliberately at ≈ 21:21
  local, per `TOOLS.md`'s "stop the companion last", and nothing starts it
  again; N05 and the first N15b attempt ran against no listener. Not a
  crash. Until companion autostart (`H3`) exists, **check `ss -lnt | grep
  8765` before a hand run**, and a session that tears down should say
  plainly that the companion is left stopped. **Narrowed 2026-09-23**:
  `H3` designed the autostart unit (`docs/memory/evidence/H3_COMPANION_AUTOSTART_DESIGN_2026-09-23.md`).
  **Status: open — designed, awaiting the user's install.**

## 2026-10-08 link-drop recovery pauses a running game with the link up (`E3-R1`) — FIXED AND ADOPTED (recovery v2, E3-A3B, 2026-10-09)

- **Seen:** five times in 20-min suite windows across four nights (E2's
  PS1-1080P r1, E3-S1's control and both CONC runs, E3-A2's PS1 r1), and
  more outside the suite on 10-05.
- **Cause, the harmful case:** the host's `controller_silence` trigger
  (1 s without a controller packet) fires on a 1-3-s client→host stall.
  The client keeps playing, so the pause has no exit: it gives up after
  120 s, saves, and stays `PAUSED_SAVED` (3 of 4).
- **The fix:** `PRIVYHUB_RECOVERY_TRIGGER=v2` (E3-R2):
  - the threshold at 5 s on two checks;
  - **an exit when the packets return and the output is fresh**;
  - a silence-gap log.
- **How it has done:**
  - the user's nft check (2026-10-09) passed: real drops unchanged; a 2-s
    controller drop no pause; an 8-s one paused at +5.35 s and resumed
    itself 1.6 s after the clear;
  - in ~3 h of suite windows (E3-R2 4, E3-A3 6) it fired **no**
    controller pause and no save, while the gap log saw 28 silences over
    1 s.
- **Adopted 2026-10-09** (E3-A3, then reverted by a validity rule that
  voided runs on the client's own pauses).
- **Re-adopted (E3-A3B), and the adoption stands**, under a bar judged
  on the trigger's own events.
  - 0 controller pauses and 0 saves in both windows.
  - Two > 1-s uplink silences that the old rule would have paused on
    passed.
  - `recovery.conf`; the kill switch is in `memory/TOOLS.md`.
- **Still open, the client's:** `client_output_silence` pauses on real
  1-3-s output stalls. They resume by themselves, and the host cannot
  tell them from a short real drop: 19 in six windows on 2026-10-09
  night, 5 in two windows the next morning.
- Records: `memory/evidence/E3_R1_RECOVERY_FALSE_PAUSE_2026-10-08.md`,
  `memory/evidence/E3_R2_RECOVERY_PAUSE_EXIT_2026-10-08.md`,
  `memory/evidence/E3_A3_RECOVERY_V2_ADOPTION_2026-10-09.md`,
  `memory/evidence/E3_A3B_RECOVERY_V2_READOPTION_2026-10-09.md`.

## 2026-10-09 the onn ↔ host link at its worst recorded (E3-A3) — OPEN, a LINK item

- **Seen:** E3-A3's six suite windows (00:38-03:01Z), the worst link of
  E3.
  - Plain PS1-STREAM: loss 201-2,938 per min, rendered down to 52.6 fps,
    resyncs up to 189.
  - CONC: 932-1,952 per min.
  - The gap log: 364 client→host silences > 250 ms, 27 over 1 s.
- **Still lossy that morning** (E3-A3B, 04:55-05:40Z): PS1 381, CONC
  1,130 per min.
- **For comparison:** E2's PS1-STREAM ran at 32.3 per min, E3-R2's at
  40-59.
- **Not a host change:** the code and the adopted state were E3-R2's.
  The cause between the ends (the air, the onn) is not located; see
  `host_link` / the warm-state loss (`T3`).
- **Effect:** the client's own output-stall pauses rise with it. Any
  performance comparison across these nights carries the link's drift;
  use same-night controls.
- **Still lossy on 10-10** (`QUEUE_2026-10-10B`, 07:12-14:04Z):
  - every stream run lost 39-863 per min;
  - E4-S4B's clean-link gate (loss < 10) failed all four of its
    controls, at 426, 66, 652 and 109 per min, 30 min apart;
  - host-side, every run was clean (RetroArch 59.999, host CPU in band).
  - Records: `docs/memory/evidence/E4_S4B_GRAB_DEFERRAL_CLEAN_LINK_2026-10-10.md`.
  - A link-gated bar has now waited on this item twice: E4-S4 and E4-S4B.
- **The planned watch never ran.** E4-S4C, a link watch planned to
  start 2026-10-10, never started: the 10-10 Code session stalled after
  its first job, and nobody saw it for five days.
- **Still lossy on 10-15.** E4-S5D's runs (21:01-21:36Z):
  - SNES 1,006 lost/min, PS1 3,349;
  - rendered 57.7 / 53.3;
  - host-side clean.
- **The watch, detached (E4-S4D), launched 2026-10-15 21:41:41Z:**
  - it runs in the `systemd --user` transient unit
    `privyhub-link-watch`, not inside a Code session;
  - one 5-min PS1 probe every 45 min until `2026-10-20T04:00:00Z`;
  - grab deferral runs on the first clean window.
- **Reading the watch:**
  - its status is `cat ~/privyhub_link_watch/status.txt`: one line,
    rewritten after every probe and run, with a 5-min heartbeat;
  - beside it are `history.csv` (one row per probe) and `watch.log`;
  - to stop it: `touch ~/privyhub_link_watch/STOP`.
  - Record: `docs/memory/evidence/E4_S4D_LINK_WATCH_LAUNCH_2026-10-15.md`.
- **PARKED 2026-10-16** (the user: remote first). The watch was stopped
  after six probes, 10-15 17:41-21:26 US Eastern
  (`docs/memory/evidence/E4_S4C_LINK_WATCH_2026-10-16.md`).
  - None was clean: 102-4,299 loss/min. Grab deferral stays INCONCLUSIVE
    (link).
  - The host side was clean throughout.
- **What the watch saw, with no cause claimed:**
  - Loss rose and fell with the AP's retry % (ρ +0.77) and the client's
    pauses.
  - Air utilisation (8-14 %), the channel (36 / 80 MHz) and the client's
    own RSSI did not move.
  - The two ends disagree. The client hears the AP at −68/−69 dBm; the AP
    hears the client at −78 to −80 dBm. The AP's tx rate to the client
    read 6.5 Mb/s in every probe, against the client's reported 117-195
    Mb/s link.
  - Ping loss was 0.14 % idle and 1.66 % while a stream ran.
- **The one hand option** the user has: a wired (USB Ethernet) adapter on
  the client. That takes the onn's radio out of the path.
  - Nothing else is queued for the LAN loss row.

## 2026-10-18 the off-site wire rate at 4000 is ~2× the encoder's rate (G4-S2) — ADDRESSED BY OPUS (G4-W1 → G-A2; G4-S3)

**G4-S3 (2026-10-19, `docs/memory/evidence/G4_S3_OFFSITE_4000_OPUS_2026-10-19.md` §4):** with Opus adopted, the
tailnet wire rate at 4000 is **5,299 kbit/s** (median; G4-S2 8,243 on the same reader), which is ~40 MB/min and
~2.4 GB/h.
- The excess over the encoder is ~1.3 Mbit/s: FEC parity, headers and control (G4-W1) plus Opus's ~0.33.
- The source was G4-W1's largest term, audio, and it is cut. The rest is by design.
- A cellular session at 4000 is now ~440 MB per 11.5 min.


- At 720p/4000 over the overlay the hub's tailnet interface sent **8.29 Mbit/s** steady (~62 MB/min, ~3.7 GB/h);
  the pre-registered expectation was ~4.65. At 7000 (G4-S1) it was 11.42. The excess over the encoder's rate is
  ~4.3 Mbit/s at both rungs, so dropping to 4000 saves ~27 % of the data, not ~43 %. Source not identified
  (candidates: audio + its 2/4 redundancy, FEC parity, the overlay's per-packet cost). This made a cellular session
  impractical for the user (run 2 not run). Record: `docs/memory/evidence/G4_S2_OFFSITE_REMOTE_LADDER_2026-10-17.md` §4.

## 2026-10-18 the remote row's RetroArch counter was not on the title (G4-S2) — CLOSED (G4-S3: the counter read)

**G4-S3 (2026-10-19):** with the user starting Tekken 3 (the fixture), the counter was on the title and read
RetroArch **59.999**, so gate 3 was evaluable and met. The window's fixed sleep after the stream ends (below) is
unchanged: G4-S3's teardown stopped the game at the window's end, and the onn then sat "reconnecting" (by design).


- RetroArch's title carried no "FPS / Frames" counter in any of 112 reads, so gate 3's RetroArch clause was not read.
  The row's override is per game (Tekken 3, the PS1-STREAM fixture); whether another title was launched or the
  override did not take is not determined. Also: the remote row's window is a fixed sleep and runs on after the
  stream ends (G4-S2 §6).
