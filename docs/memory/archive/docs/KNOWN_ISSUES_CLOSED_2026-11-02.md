---
memory_schema: 1
as_of: 2026-11-03
status: closed / superseded KNOWN_ISSUES sections, moved verbatim from docs/KNOWN_ISSUES.md at commit b20729b8, moved 2026-11-03
---

# Known issues — closed and superseded sections (moved 2026-11-03)

These sections were moved byte for byte from `docs/KNOWN_ISSUES.md` (at commit `b20729b8`) on 2026-11-03, in their
original order, following `docs/memory/evidence/DOCS_AUDIT_2026-11-02.md` §1.2 / §2.3. Nothing in them was edited. The
only added lines are this header, one note line under the LAN-R1 heading, and blank separator lines where two moved
ranges met without one. The LAN-R1 heading here is the original; what follows it is the B-queue / CL-B chronology
that had grown under that item (its own open text stays in `docs/KNOWN_ISSUES.md`), and some of it (the loss guard /
stall interaction, G-A8 prepared and never applied) is still open and indexed there. The 2026-09-20 link-drop
requirement section's closing `PRIVYHUB_LINK_DROP_RESILIENCE` END marker stayed in `docs/KNOWN_ISSUES.md` with the
`D-BASE-R3` section that opens it. Current state: `docs/memory/CURRENT.md`; open items: `docs/KNOWN_ISSUES.md`.

## 2026-10-25 CL-B13: the WAN class reads the onn on the home Wi-Fi through the overlay as `remote-direct`, and 450 then holds falsely once — G-A6 SHELVED (2026-10-26, the user)

(`docs/memory/evidence/CL_B13_RESTART_FAST_AND_WAN_CLASS_2026-10-25.md` §4-§5)

- With `PRIVYHUB_LINK_RECOVERY_WAN=1` and the onn on the tailnet at home (direct), 3a had one false hold at 451 ms
  (23:18:07Z, no drop). The guard reverted the session to 950 / 400 (`WHY_GUARD`). There was also one false stall
  pause at 207 ms.
- 3b (`@down`) met every row: the stall pauses at 208-214 ms, resumed 41-212 ms after the return.
- The class tells overlay from LAN by address and path, not by the radio underneath. Off-site G4-S4 had 0 at 450; the
  home Wi-Fi does not. **To B:** whether direct-on-the-LAN needs telling apart, or whether H 450 waits for more
  off-site minutes. G-A6 is not a candidate as read.
- **G-A6 SHELVED (2026-10-26, the user's decision):** `PRIVYHUB_LINK_RECOVERY_WAN` stays built and off. It gains at
  most ~0.5 s per real drop. It would reopen with a way to tell a remote path from the home radio, and with off-site
  data on a relayed path. (`G_A5_RESTART_FAST_ADOPTION_2026-10-26.md` §6)

## 2026-10-21 LAN-R1: the ladder does not step down on loss on the LAN — OPEN; a rule BUILT behind `PRIVYHUB_LAN_LOSS_RULE=1`, NOT ADOPTED; BENCH-R1 (2026-10-22): the rule back to B, the input hold not a candidate until its trigger is fixed, the death reproduced on the bench; BENCH-R2 (2026-10-22): the Wi-Fi lock not the cause, the hold + rewind + stall stack not a candidate, APK cb0935c8 CONFIRMED; queue D (2026-10-22): the ownership at the return, the stall threshold 400 + rewind SNES-only, the client's loss guard BUILT, NOT ADOPTED; BENCH-R3 (2026-10-22): the stack not a candidate on SNES (snes9x's hold-path rewind reads PAUSED), the PS1 state path works, the loss guard a candidate (the user's call), the onn on 2.4 GHz where the Opal sampler did not look, APK bf5114a2 CONFIRMED; LINK-R1 (2026-10-23): on 5 GHz 0 uplink silences / 0 hitch s per 10 min — the band was most of the flapping; queue E (2026-10-23): the self-restart guard, `state` for every core + the stall resume, the link report on by default + G-A3 prepared, the link notice BUILT, NOT ADOPTED; CL-B10 (2026-10-24): the band settled (2.4 GHz the flapping), the notice shown (the user's word); queue F (2026-10-24): the guard on every path and the stall resume at the client's first frame BUILT, NOT ADOPTED; CL-B11 (2026-10-24): APK e2db0aa0 CONFIRMED, the fast ready resumes 133-458 ms after the return and the guard carries a new-instance return — each back to B with one row; queue G (2026-10-24): both rows answered, the client defaults on, the stack as one line (`PRIVYHUB_LINK_RECOVERY=1`) and G-A4 PREPARED — BUILT, NOT ADOPTED; CL-B12 (2026-10-24): APK 20e3e339 CONFIRMED with every client property empty, the umbrella alone gives every behaviour row (resume 108-349 ms, 0 saves outside, the bye), both Home returns via the start (create→start 96-280 ms, 0 underruns after) — back to B on two narrow rows (a config log line; one 30-underrun interval at a Home press); G-A4 the user's call

> Moved 2026-11-03: below is this section's chronology from its `B1-B3` bullet on; its own LAN-R1 text (the standard to the first "Next (session A)" bullet) stays in `docs/KNOWN_ISSUES.md`.

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
  - **Queue J, B27 (2026-10-27; the user's "Also adopt"; BUILT, NOT ADOPTED, no live run): the loss guard on by
    default in the client** (`debug.privyhub.loss_guard`: absent / empty / junk = on, `0` off, `count` as before).
    - **The replay first** (B10's rule as a bound over 47 reports since CL-B10): the LAN ~6,830 frames held in 212
      min (~32 / min, about one ≤ 0.25-s freeze every 15-30 s); G4-S4 ~1,860 in 122 min. A hold > 0.5 s (two IDRs
      lost in a row; the 600-ms cap) is possible in 9 LAN sessions and 1 off-site.
    - **The cost:** the same with or without the host's `PRIVYHUB_LOSS_GUARD=1`, which forces no keyframe (no
      runtime IDR); without it each freeze's 24-B request is one host `bad_packets`.
    - JVM 154 / 154. **APK (B5 … B25 + B27) `8b0fbb74…3f4e` pinned, NOT installed;** `fcd924c2…` stays CONFIRMED.
    - **G-A8 (`PRIVYHUB_LOSS_GUARD=1`, thirteen lines) PREPARED, not applied:**
      `docs/memory/patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`.
    - Next: CL-B15 (`docs/memory/handoffs/SESSION_B_DONE_2026-10-27J.md`). Record:
      `docs/memory/evidence/B27_LOSS_GUARD_DEFAULT_ON_2026-10-27.md`.
  - **CL-B15 (2026-10-28; `8b0fbb74…` CONFIRMED and pinned, the guard now ON by default on the onn; every client
    property empty, 5 GHz, E1-PS1-STREAM): back to B on three rows — OPEN.**
    - **1 % loss + `PRIVYHUB_LOSS_GUARD=1`:** 320 freezes in 11.55 min (27.7 a minute, ~0.13 s each). **One hold ran
      685 ms, past the 600-ms cap: it timed out and showed 7 corrupted frames** (held 2,478 of 2,485).
    - **9 holds of ≥ ~0.4 s tripped the adopted stall stack** (save, pause, 2-3 frames restored, resume). This is new
      under the twelve lines; BENCH-R3 E ran without the stack.
    - The host side as built: `NoRuntimeIdr`, forced 0, received 319 of 320.
    - **Clean LAN, no flag:** 38 freezes (3.3 a minute, ~0.13 s, the longest 0.27 s); 0 timeouts; no stall pause.
    - **Not read:** the controller's `bad_packets` (not sampled).
    - **For B:** why the cap fired 85 ms late; whether the guard's hold and the stall signal should know of each other.
      G-A8 is not a candidate as read. Off on the onn: `setprop debug.privyhub.loss_guard 0`, or `fcd924c2…` back.
      Record: `docs/memory/evidence/CL_B15_LOSS_GUARD_DEFAULT_2026-10-27.md`.
  - **Queue K, B29 (2026-10-28; BUILT in the client, NOT ADOPTED, no live run): a guard hold is not a stall; the cap
    on the hold's own clock.**
    - **Settled:**
      - a hold ages the decoder's output exactly as a link stall does, so the monitor sent stalls and the host acted
        at 400;
      - **the "685 ms" was the episode's drop-to-IDR span** (`loss_guard_max_wait_ms`), not a late cap. The hold
        ended at the cap and 7 frames passed before the IDR.
    - **Built:** while the guard holds, the stall monitor decides on the time since the last frame received
      (suppressed; a real stall still goes out). The cap runs on the controller loop's ~8-ms tick; a new key,
      `loss_guard_max_hold_ms`.
    - JVM 161 / 161. **APK (B5 … B27 + B29) `9719ea82…0110` pinned, NOT installed;** `8b0fbb74…` stays CONFIRMED.
    - A hold whose next good IDR is > 600 ms away still times out by design.
    - Next: CL-B16 (`docs/memory/handoffs/SESSION_B_DONE_2026-10-28K.md`). Record:
      `docs/memory/evidence/B29_GUARD_QUIET_STALL_2026-10-28.md`.
    - **CL-B16 (2026-10-29; `9719ea82…` CONFIRMED and pinned by the validity rule): S1 NOT MET — OPEN.**
      - At 1 % loss: 0 timeouts, held = counter (3,290), max hold 469 ms (S2-S4 met).
      - **But 12 stall pauses** (CL-B15: 9), none with an uplink silence behind it, clustered among guard holds.
      - On this evening's LAN with no impairment: 8 and 5 stall pauses (CL-B15 cell C: 0; that LAN lost a third as
        many packets).
      - Cost at 1 %: 35.6 freezes a minute, hitch 55.6 s / 10 min, rendered 54.48.
      - **For B:** what "the last frame received" counts during a hold, and why ages reach 597 ms with no silence.
      - `8b0fbb74…` is kept at `PrivyHub/app/build/cl_b15_installed/`. Record:
        `docs/memory/evidence/CL_B16_REMOTE_UMBRELLA_AND_QUIET_GUARD_2026-10-29.md`.
      - **TRIP-PREP (2026-10-29, the user's "Yes"): the loss guard OUT for the trip.** CL-B14's `fcd924c2…`
        (no guard default) is reinstalled and the pin moved back. `9719ea82…` is kept at `cl_b16_installed/`.
      - **The guard / stall interaction stays open for B:** the guard's holds draw stall pauses with 3-frame rewinds,
        and B29's fix did not take. The guard's return after the trip is a B item.
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
  - **The band again (inserted 2026-10-26):** G-A5's precondition read at 02:59Z found the onn back on **2.4 GHz**
    (2412 MHz), although CL-B13 had closed on 5 GHz at ~00:05Z. Nobody had touched the band, and nothing told anyone:
    B14's notice was opt-in. G-A5's session (03:10Z) ran on 5 GHz.
  - **Queue I, B25 (2026-10-26; the user's "Yes"; BUILT, NOT ADOPTED, no live run):** `debug.privyhub.link_notice`
    absent / empty / junk = **ON** (`0` off), as B13 / B19 did. B14's conditions, wording, once-a-session rule and
    30-s clear are unchanged.
    - **The replay first** (B14's rule over every heartbeat with the link keys since G-A3, 45 sessions): **3 / 3
      sessions on 2.4 GHz show it, 0 / 42 on 5 GHz.** The port matches the real client's bits in CL-B10 (0
      disagreements).
    - **The 5-GHz margin, for the user (not changed):** the lowest RSSI any 5-GHz session held 10 s is −70 dBm (G-A4,
      CL-B12 c1, G-A5), 2 dB above B14's −72. −71 is the loosest threshold that keeps them all quiet; at −70 three
      would show. The lowest tx held 10 s on 5 GHz is 130 Mbps (threshold 54).
    - JVM 150 / 150. **APK (B5 … B19 + B22 + B25) `fcd924c2…9b96`, pinned, NOT installed;** `6bddafc0…` stays
      CONFIRMED until CL-B14.
    - Record: `docs/memory/evidence/B25_LINK_NOTICE_DEFAULT_ON_2026-10-26.md`.
  - **CL-B14 (2026-10-27): `fcd924c2…9b96` CONFIRMED and pinned; the notice is now on by default on the onn.** On 5
    GHz with no property: `link_notice` 0 in 663 / 663 heartbeats (two attempts), no `link_notice_shown` row, the
    reports 0. The shown path (2.4 GHz) was not exercised. Off: `setprop debug.privyhub.link_notice 0`. Record:
    `docs/memory/evidence/CL_B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_2026-10-26.md`.

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
