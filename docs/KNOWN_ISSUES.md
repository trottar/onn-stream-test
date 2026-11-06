# Known issues and deferred work

as_of: 2026-11-06. Open items only. The closed and superseded sections were moved verbatim on 2026-11-03 to
`docs/memory/archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md` (with the B-queue / CL-B chronology that had grown under LAN-R1); their text is unchanged there.
Sections below keep their text unchanged and their order.

## Open items

One line per open item: date — item — status — where it lives.

**Sections below (file order):**
- 2026-11-06 — Queue N (B41-B45): the prompt, the two defaults, the movie retry made real, the G9 draft, the H0 design; APK built, not installed — OPEN (HOME-3) — `## 2026-11-06 Queue N` below; `docs/memory/handoffs/SESSION_B_DONE_2026-11-06N.md`
- 2026-11-06 — HOME-2: C1' / C4' met; C5' not met (valid: B40's reset absorbed by the player, B35 never reached); `0132b944…` CONFIRMED, every property empty — OPEN (G-A11 / G-A12 the user's; G-A13 to B) — `## 2026-11-06 HOME-2` below; `docs/memory/evidence/HOME_2_HOLD_PADS_VOD_2026-11-03.md`
- 2026-11-02 — Queue M (B38-B40), HOME-1's C1 / C4 / C5 answered in code; APK `0132b944…` CONFIRMED in HOME-2 (2026-11-06) — OPEN (C5' to B) — `## 2026-11-02 Queue M` below; `docs/memory/handoffs/SESSION_B_DONE_2026-11-02M.md`
- 2026-11-02 — G-A10, `PRIVYHUB_STEP_IN_PLACE=1` ADOPTED (the fourteenth line); B's open items from HOME-1 — OPEN (to B) — `## 2026-11-02 G-A10` below; `docs/memory/evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`
- 2026-11-02 — HOME-1: C2 / C3 met; C1 / C4 not met; C5 invalid; `554ccf61…` NOT CONFIRMED — OPEN (to B) — `## 2026-11-02 HOME-1` below
- 2026-10-31 — TRIP-R2, off-site play, four episodes — OPEN (to B, queue L) — `## 2026-10-31 TRIP-R2` below
- 2026-10-31 — Queue L (B32-B37), what stays open — OPEN (HOME-1) — `## 2026-10-31 Queue L` below
- 2026-10-24 — G4-S4, off-site free play (Home auto-resumes; the onn off the overlay ~8 min once; underruns 8-20 / min) — OPEN (to B / a watch item) — `## 2026-10-24 G4-S4` below
- 2026-10-21 — LAN-R1, the ladder does not step down on loss on the LAN; the rule behind `PRIVYHUB_LAN_LOSS_RULE=1` BUILT, NOT ADOPTED — OPEN — `## 2026-10-21 LAN-R1` below
- 2026-10-20 — UX-R1 / UX-R2 / UX-R3, the user's evenings; link vs onn not separable — OPEN — `## 2026-10-20 UX-R1` below
- 2026-10-18 — CL-B4, Opus: off-site fixed (CL-B5); underruns a watch item; decoder spikes OPEN — OPEN (kept: its heading still reads "SPIKES OPEN") — `## 2026-10-18 CL-B4` below
- 2026-10-17 — G8-S1, the rate-cap cells never reached PLAYING — OPEN — `## 2026-10-17 G8-S1` below
- 2026-10-16 — G4-S1, the first off-site session, three items — OPEN — `## 2026-10-16 G4-S1` below
- 2026-10-16 — G5-S1 WAN telemetry: no per-session line on a restart-ended run; CPU cost over its bar — OPEN (CL-B3 W) — `## 2026-10-16 G5-S1` below
- 2026-10-16 — the host-CPU band gate fails on the encoder's share — OPEN (a BAR item, CL-B2 R3) — `## 2026-10-16 the host-CPU band gate` below
- 2026-09-18 — C3.L0 audit: Linux host resource telemetry never starts — OPEN as written ("Phase E prerequisite"; no later record closes it) — `## 2026-09-18 C3.L0 audit findings` below
- 2026-09-21/22 — UDP transport: Entry 1 (the synthetic pathology) PAUSED; Entry 2 RESOLVED — kept for Entry 1 — `## UDP transport: two separate entries` below
- 2026-09-24 — controller transport `lost_packets` under real play — observed, not investigated — below
- 2026-09-23 — open after the `D-BASE` close-out: max output gap, warm-state loss, `host_link`, thermal thresholds — OPEN rows — below (the 2026-09-20 baseline-faults section it closes out was moved)
- 2026-09-22 — open items after the baseline chain: the `lost_packets` restart caveat, `host_link` not implemented, the host's SSH / autologin (H2) and others — mixed, some OPEN — below (its "see the entry above" pointer for `host_link` now points into the closed file)
- (undated) — runtime coverage gaps: NES and Genesis — OPEN — below
- (undated) — security / privacy debt — OPEN — below
- (undated) — Windows / Linux portability debt — OPEN — below
- (undated) — maintainability / test debt — OPEN — below
- 2026-09-20 — the launcher banner does not reconcile when the companion is unreachable — OPEN — below
- 2026-09-20 — link-drop resilience `D-BASE-R3` + `D-BASE-R3a`, its "What is still open" list — kept as written — below (its "preserved below" requirement section was moved)
- 2026-09-20 — a terminal stall leaves no evidence in the session report — OPEN — below
- 2026-10-09 — the onn ↔ host link at its worst recorded (E3-A3) — OPEN, a LINK item — `## 2026-10-09` below

**Carried out (no section of their own here):**
- 2026-10-27..29 — the loss guard / stall interaction (the guard's holds draw stall pauses; B29's fix did not take); G-A8 (`PRIVYHUB_LOSS_GUARD=1`) PREPARED, never applied; the guard out since TRIP-PREP (`fcd924c2…` CONFIRMED, no guard default) — OPEN (a B item) — the moved LAN-R1 chronology (B27, CL-B15, B29, CL-B16, TRIP-PREP) in the closed file; `docs/memory/patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`
- 2026-11-02 — HOME-1 C1, the hold's report counter — MET in HOME-2 C1' (B39; `held` 1, `losses` 1, `restarted` 0) — G-A11 the user's question — `docs/memory/evidence/HOME_2_HOLD_PADS_VOD_2026-11-03.md`
- 2026-11-02 — HOME-1 C4, the onn's virtual remote takes a pad slot — MET in HOME-2 C4' (B38; `count` 2, no `google` entry) — G-A12 the user's question — same record
- 2026-11-02 — HOME-1 C5, the VOD drop — INVALID; HOME-2 C5' valid, NOT MET: B40's single reset (`dropped: 1`, `rst`, twice) was absorbed by the player's own reconnect (`bytes=<P>-` 206), no player error, so B35's retry never ran — OPEN (to B: a drop that outlasts the player's own retries) — same record
- 2026-10-19 — G8-S6, three paired cap-6000 cells, control vs `PRIVYHUB_ENCODER_RC=tight` (does `tight` keep a capped stream from going silent?) — QUEUED, NEVER RUN — `docs/memory/handoffs/QUEUE_2026-10-19N.md` §1 (its preconditions are stale)
- 2026-10-19 — G5-S2-L, the first live LAN smoke of the WAN adaptation rules (`PRIVYHUB_WAN_ADAPTATION=1`) — QUEUED, NEVER RUN — `docs/memory/handoffs/QUEUE_2026-10-19N.md` §2
- 2026-10-23 — LINK-N1, the nightly watch (unit `privyhub-link-n1`, ended 2026-10-31): its nights NOT WRITTEN UP — only `docs/memory/evidence/LINK_N1_LAUNCH_2026-10-23.md` and `docs/memory/evidence/link_n1_2026-10-23/` exist — OPEN ("read LINK-N1's nights")
- 2026-10-16 — `docs/memory/handoffs/G4_RUNBOOK_HOTSPOT.md` step 18, the "local behaviour unchanged when the overlay is absent" check — NEVER SCORED — that runbook

## 2026-11-06 Queue N (B41-B45): the player prompt, the hold and stable slots on by default, the movie retry made real, the G9 draft, the H0 design — OPEN (HOME-3)

(`docs/memory/handoffs/SESSION_B_DONE_2026-11-06N.md`; the records `docs/memory/evidence/B41_…`, `B42_…`, `B43_…_2026-11-06.md`)

- **B42 (G-A11 / G-A12, the user's yes):** in queue N's APK the hold and stable slots are **on with no property**;
  `0` / `off` turns each off. Every session then sends `pad_slots`, so the heartbeat row's `updates_by_player` is the
  changed-only count and the old per-packet count is `packets_by_player`: a comparison across this APK must read
  `packets_by_player`. `NativeStreamActivity`'s comments for the two lazies still say "(null = today)", which now
  means `0` / `off`.
- **B41, the player prompt** (`debug.privyhub.player_prompt=1`, opt-in): it implies stable slots and claims by first
  press. An unclaimed pad's sticks and non-claim keys are dropped until it presses a face button or Start; the claim
  press and Select+Start both reach the game. The player count comes from `player_mode` / `max_players` / the PS1
  multitap: unknown = 2, and with no SNES multitap path a 4-player SNES title reads 2.
- **B43, the movie retry:** under `vod_retry=1`, a 401 / 403 now refetches the media token (a companion restart no
  longer strands the movie), and "connection to hub lost" shows only after 150 s with no answer. Media3's own reconnect
  hides any outage its 15-30 s buffer covers, so B35 / B43 act only beyond ~35 s; the bench uses `drop 45`. Rows
  posted while the hub is down are lost (posted once).
- **B44, the G9 draft:** 9 met / 3 deferred / 2 open. Open: the local check with the hub's own overlay down (the G4
  runbook's step 18, never scored) and the clean checkpoint. The household-LAN boundary is met by design and never
  probed; relayed-path WAN play is unmeasured.
- **B45, H0 (found while designing):** PS1 `.iso` is listed by the scanner (`games.py` `SYSTEMS`) but refused at launch
  (`emulators.json` has no `.iso`). The PS1 BIOS directory is empty (RetroArch logs the missing firmware at every
  start; the core runs its built-in OpenBIOS, inferred); a real BIOS is the user's decision (save-state compatibility).

## 2026-11-06 HOME-2: C1' / C4' met; C5' not met (valid); `0132b944…` CONFIRMED — OPEN (G-A11 / G-A12 the user's; G-A13 to B)

(`docs/memory/evidence/HOME_2_HOLD_PADS_VOD_2026-11-03.md`)

- **C1' MET:** a 3.5-s Home press kept the session (`held`); the report reads `held` 1, `losses` 1, `restarted` 0 over
  the whole session. G-A11 is the user's question.
- **C4' MET:** two pads in slots 0 / 1 both starts, the onn's virtual remote in none; `updates_by_player` and `/status`
  `changes_by_player` count only the pad that moved. G-A12 is the user's question.
- **C5' NOT MET (valid):** B40's reset hit the streaming movie twice (`dropped: 1`, `how: rst`); the player's own loader
  reopened at `bytes=<P>-` (206) and played on; no player error, no `vod_client.jsonl`, no "reconnecting…". Then the
  close's companion restart, mid-movie, ended its media token: B35 showed "reconnecting…", retried ~2.5 min against
  401s with the hub up, and gave up with "connection to hub lost". **To B:** a drop that outlasts the player's own
  retries; B35 to re-fetch the session / token on retry; a 401 is not a lost hub.
- `0132b944…` CONFIRMED; the pin moved; every property empty on the onn.

## 2026-11-02 Queue M (B38-B40): HOME-1's C1 / C4 / C5 answered in code; APK `0132b944…` built, not installed — OPEN (HOME-2)

(`docs/memory/handoffs/SESSION_B_DONE_2026-11-02M.md`; the records `docs/memory/evidence/B38_…`, `B39_…`, `B40_…_2026-11-02.md`)

- **C4, the onn's "virtual-remote":** KEYBOARD | DPAD | GAMEPAD, controller number 1, **not `isVirtual()`** (that is
  true only for the built-in virtual keyboard) and it answers the gamepad buttons as present, so B34's button test
  passed it. B38 (inside `debug.privyhub.pad_slots=stable`) also needs a face button **and** stick or hat axes. The
  onn's own devices are key-only, so they are excluded by class. **A pad in keyboard-emulation mode (no axes) gets no
  slot either.**
- **`updates_by_player` counted packets, not pads:** the sender sends players 0-3 every ~8-ms tick (CTRL-L1).
  - For a stable-slot client (B38), the heartbeat row's `updates_by_player` is the changed-only count, the old count
    moves to `packets_by_player`, and `/status` gains `changes_by_player`.
  - `/status`'s own `updates_by_player` stays per-packet: the `tools/` probes read it that way.
- **C1, the hold's report counter (B39):** under `surface_hold`, every report after a held loss was the first loss's
  cached snapshot (counters 0, `duration_ms` cut at the loss). Fixed in `0132b944…`; reports from `554ccf61…` with a
  held loss are truncated.
- **The pad's guide key cannot be kept from the onn's system:** its input policy turns it into Home before any app sees
  it. B32's "consume" half is dropped (B39); the hold covers a guide press like a Home press within 12 s.
- **C5 needs the drop from the hub:** B40 builds it behind `PRIVYHUB_VOD_DROP_TEST=1` (bench only, per run, **never to be
  adopted**). A line appended to `runtime/vod_drop_test.trigger` resets the playing movie's connection once (a real
  RST). Its row goes into `logs/vod_drop_test.jsonl`, which is not in B36's keeper list; with `PRIVYHUB_VOD_LOG=1` the
  row is also in `vod_range.jsonl`.

## 2026-11-02 G-A10: the step-up gap closed (`PRIVYHUB_STEP_IN_PLACE=1`, the fourteenth line); B's open items from HOME-1 — OPEN (to B)

(`docs/memory/evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`)

- **CLOSED: every ladder step restarted the encoder with a new SSRC** (TRIP-R2 E1's ~430-ms gaps, B32).
  - Adopted 2026-11-02: each step is spliced onto the same stream; HOME-1 C2 measured 0.9 / 6.1 ms.
  - The fallback (no splice in 2 s → today's restart, `in_place: false`) has not been seen.
  - G-A10's LAN window had no step to read.
- **Open for B (HOME-1):**
  - **(1) The virtual-remote slot:** the onn's "virtual-remote" declares GAMEPAD and takes player slot 0 under
    `pad_slots=stable`; `updates_by_player` rises on all four.
  - **(2) The hold counter:** the report's `surface_hold.held` reads 0 after a held loss. The onn takes a pad's guide
    key as Home before any app sees it.
  - **(3) The VOD drop test:** it needs the drop with the player in front (the hub-side shim or the router), not the
    onn's Wi-Fi Settings, which release the player first.
- **Seen in G-A10's window, not the line's:** the onn at −67…−69 dBm on 5180 MHz this evening (−51…−56 on the trip).
  Two real stalls with loss (B33 rewound, `why: loss` / `uplink_loss`); hitch 27.7 s / 10 min.

## 2026-11-02 HOME-1: queue L's cells: C2 / C3 met; C1 / C4 not met, C5 invalid; `554ccf61…` not confirmed — OPEN (to B)

(`docs/memory/evidence/HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md`)

- **C1, B32's screen-loss hold:** works for the remote's Home (held, 4.4 s, the same session).
  - The client report's `surface_hold.held` reads 0 after a held loss.
  - **The onn's system turns a pad's guide / PS button into Home before any app sees it** ("dropped because the
    policy consumed it"), so B32's key consumption cannot act there.
- **C4, B34's stable slots:** the map is stable across the press order, but the onn's "virtual-remote" input device
  (it declares GAMEPAD) takes slot 0. Two pads then become players 2 and 3, and port 3 is not read on a PS1 without
  multitap. `updates_by_player` still rises on all four players.
- **C5, B35's movie retry: invalid.** Turning the onn's Wi-Fi off from its Settings leaves the app, which releases the
  player before the drop. The cell needs the drop with the player in front (the hub-side shim or the router).
- **`554ccf61…` NOT CONFIRMED** (C5 invalid); `fcd924c2…` is back on the onn. G-A10 (step in place, C2 met) is the
  user's question.

## 2026-10-31 TRIP-R2, Friday off-site play: four episodes — OPEN (to B, queue L)

(`docs/memory/evidence/TRIP_R2_FRIDAY_GAMEPLAY_2026-10-31.md` §5)

- **E1, the self-restarts:** 6 in the evening (3 in golf). Each time the onn took the stream activity out of the
  foreground for 1-9 s (`restart_cause.trigger` surface), not because of a stall or the ladder. Every ladder step also
  restarts the encoder (a new SSRC; 3 of 32 gave a ~430 ms gap and a stall pause). → B32.
- **E2, golf inputs:** no minutes-long delay is in the rows. Presses went into the restarts (≤ 5.3 s), into 3 stall
  rewinds (~0.45 s dropped each), and a 125 / 410 ms control echo. → B33.
- **E3, two-player football:** the link and host were flat. The cause is the pad setup and the client's slot order
  (first input wins, reset at every start). Inferred: no row is per player. → B34.
- **E4, the movie:** the feature's connection ended from the client side at about 1 h 50 min (~07:54Z), and the
  player stopped without retrying. The hub was healthy. → B35.

## 2026-10-31 Queue L (B32-B37): what was built for TRIP-R2's four episodes, and what stays open — OPEN (HOME-1)

(`docs/memory/handoffs/SESSION_B_DONE_2026-10-31L.md`; the records `docs/memory/evidence/B32_…` … `B37_…_2026-10-31.md`)

- **B32, the surface hold:** built behind `debug.privyhub.surface_hold=1` (in APK `554ccf61…`, not installed): a screen
  loss ≤ 12 s keeps the session; each foreground loss is a `surface_lost` row in the recovery log. The cause of
  Friday's six is not knowable from the code; the rows will name it. `KEYCODE_HOME` / `APP_SWITCH` never reach the
  activity (the system takes them): a pad whose Home maps to `KEYCODE_HOME` still leaves (row `user_leave`, no key).
  After a re-attach the heartbeat's `rendered_frames` drops back once (the report keeps `rendered_before_reattach`).
- **B32, every ladder step restarts the encoder with a new SSRC** (32 of 32 on Friday; a ~430-ms gap in 3).
  `h264_vaapi` has no runtime rate control; a same-stream splice is built behind `PRIVYHUB_STEP_IN_PLACE=1` (not
  adopted). Two encoders run at once for ~0.2-0.4 s per step; the onn's handling of an in-stream IDR with no SSRC change
  is untested. **An explicit `PRIVYHUB_REMOTE_RUNG_CAP` beside `PRIVYHUB_REMOTE=1` was inactive;** fixed in the tree
  (live at the next companion restart; no such line is set today).
- **B33, no rewind without loss:** inside the adopted `PRIVYHUB_LINK_RECOVERY=1`, so **live at the next companion
  restart** (off: `PRIVYHUB_REWIND_NEEDS_LOSS=0`). Loss inside the stall's own ~0.5 s shows only in the next heartbeat,
  which the rule cannot wait for; a session's first heartbeats have no predecessor and load as today. The host's
  controller-sequence loss counter is in `/status` only, never in a log.
- **B34, player slots:** first-input order, reset at every start, any stick-axis device eligible, until
  `debug.privyhub.pad_slots=stable` (built, in the APK, not installed). Stable slots last for the app process's life.
- **B35, the movie player:** no retry today; `debug.privyhub.vod_retry=1` (client, 150 s) and `PRIVYHUB_VOD_LOG=1`
  (the per-request range log) built, neither live.
- **B36, the diagnostics keeper:** `privyhub-diag` built, not installed; it imports `tools/trip_log_keeper.py` (keep it).
  A restart's client cause reaches `sessions.jsonl` only in the next session's row (`restart_cause`), or in the same
  session from B32's `surface_lost`.
- **B37, "the control echo" is not a control echo:** `control_round_trip_ms` (the `wan` block's `rtt_ms`) is the 2-s
  health POST's HTTP round trip (a new TCP connection + the hub's synchronous handler), ~4-5× a press's real delay
  off-site. The off-site p95 tail (+~280 ms over p50) is unexplained. Input → photon is measured nowhere.

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
  - **Queue K, B28 (2026-10-28; BUILT behind `PRIVYHUB_REMOTE=1`, NOT ADOPTED, no live run): one line for the
    four WAN lines, each acting only on a remote-class session.**
    - **Settled:** as written the four are not LAN-neutral. `PRIVYHUB_START_RUNG=floor` starts a LAN session at
      **5000** (the LAN list's floor), and the other three add rows and fields on the LAN.
    - Under the umbrella a LAN session is today's byte for byte. On an overlay address (direct / relayed / unknown) the
      four are G4-S4's, with one `remote_config` row per session.
    - The replay: G4-S4 13 / 13 the same; the home LAN 16 / 16 today's 7000.
    - **The floor start per new session (a Home return too) stays:** ~12-15 min below 7000 away from home.
    - G-A9 (the thirteenth line) PREPARED, not applied: `docs/memory/patches/G-A9_REMOTE_ADOPTION_PREPARED.md`.
    - Record: `docs/memory/evidence/B28_REMOTE_UMBRELLA_2026-10-28.md`.
    - **CL-B16 (2026-10-29; at home, the onn on 5 GHz, APK `9719ea82…`): back to B on R3 — OPEN.**
      - On the LAN the umbrella is today's: 7000, no remote rows (U1-U3 met).
      - Over the overlay (direct): `remote-direct`, the four in force, the 4000 floor, the 7000 cap once with 0 clamps,
        `wan` in `/status`.
      - **The climb was 2 steps in 13.6 min (4000 → 5500), not ≥ 3:** a client stall with a 333-ms uplink silence put
        the ladder in `HOLD_DOWN` and restarted its count.
      - **The session's `wan_sessions` row was never written:** the companion restarted before a next session in the
        same process.
      - G-A9 is back to B as read. Record: `docs/memory/evidence/CL_B16_REMOTE_UMBRELLA_AND_QUIET_GUARD_2026-10-29.md`.
      - **G-A9 ADOPTED anyway (2026-10-29, the user's "Yes", TRIP-PREP):** the thirteenth line. Its LAN window was
        valid: today's 7000, no remote row.
      - **Still open for B:** `logs/wan_sessions.jsonl` loses the last remote session's row at a companion restart
        (written only when a next session starts in the same process). During the trip, read the keeper's copies and
        `wan` in `/status`. Record: `docs/memory/evidence/TRIP_PREP_2026-10-29.md`.
  - **Queue H (2026-10-25):** B22 shortens the return itself (the start answered before the teardown, the
    release at the new stream's first fresh frame; NOT ADOPTED). Pausing at Home and keeping the rung were not in queue
    H: they stay the user's question.
  - **CL-B13 (2026-10-25):** on the LAN, with B22's `PRIVYHUB_RESTART_FAST=1`, the picture was back 1.7-2.0 s after
    the new activity at three of four returns (6.7-7.5 s without it). Return 1 took 3.12 s (the old audio's stop, 2.2
    s, inside the worker's lock). Back to B with that row and the old encoder's +0.35 / +0.39 s at two returns. Pausing
    at Home is still the user's question.
  - **G-A5 (2026-10-26):** `PRIVYHUB_RESTART_FAST=1` ADOPTED (the eleventh line). The slow return stays OPEN for B:
    3.12 s once (the old audio's 2.2-s stop inside the worker's lock), and the old encoder at +0.35 / +0.39 s at two
    returns.
  - **Queue I, B24 (2026-10-26; BUILT behind `PRIVYHUB_RESTART_FAST_UNLOCK=1`, NOT ADOPTED, no live run):**
    - **Settled:** return 1's old-audio stop ran 2,088 ms because the audio capture's 2-s SIGTERM wait expired (then
      SIGKILL); the other three ran 203-352 ms.
    - The new ready needs only the new encoder's check and `prepare`. The old encoder's flushed frames were forwarded
      because the relay was stopped after its exit.
    - **Built:** the ready answers at the check's end. The old audio's stop runs after it outside the lock (the capture
      killed at 300 ms; `restart_fast_audio_stop`). The relay stops before the old encoder's SIGTERM (SIGKILL after
      100 ms).
    - CL-B13's returns re-timed predict the picture back ~1.2-1.98 s (return 1 tight against the 2.0-s row).
    - No client change: `6bddafc0…` stays. Next: CL-B14 (`docs/memory/handoffs/SESSION_B_DONE_2026-10-26I.md`).
      Record: `docs/memory/evidence/B24_RESTART_FAST_UNLOCK_2026-10-26.md`.
  - **CL-B14 (2026-10-27; `PRIVYHUB_RESTART_FAST_UNLOCK=1`, the onn on 5 GHz, every client property empty):** every
    row met at four returns. The picture was back 1.15-1.86 s after the new activity (one clock), the lock released at
    the check (`unlocked_ms` − `checked_ms` 0), and the old encoder's picture frames ended at the entry. At two returns
    the old audio capture was SIGKILLed at the 300-ms bound. **G-A7 is the user's question.** For B: one 8-byte,
    single-packet frame logged by the relay at the old encoder's exit at every return, and `relay_stopped_ms` 500 once.
    Pausing at Home is still the user's question. Record:
    `docs/memory/evidence/CL_B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_2026-10-26.md`.
  - **G-A7 (2026-10-27): `PRIVYHUB_RESTART_FAST_UNLOCK=1` ADOPTED (the twelfth line). The slow return is CLOSED:** the
    picture back 1.15-1.86 s at four of four Home returns (CL-B14), the ready no longer waiting on the old audio's
    stop. The confirmation window (no Home press) met every row. Record:
    `docs/memory/evidence/G_A7_RESTART_FAST_UNLOCK_ADOPTION_2026-10-27.md`.
  - **Still OPEN (to B): the stray 8-byte packet.** At each CL-B14 return the relay logged one 1-packet, 8-byte,
    unmarked "frame" within 1 ms of the old encoder's exit, 100-140 ms after the relay's stop (not in CL-B13). It is
    not a picture frame; whether it reached the onn is not in the rows. Also for B: `relay_stopped_ms` read 500 once
    (50-214 at the others). Pausing at Home and keeping the rung stay the user's question.
  - **Queue J, B26 (2026-10-27; SETTLED + BUILT inside the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1`, no new flag,
    no live run): the stray 8-byte packet is not an exit packet.**
    - It is the old encoder's next frame's first packet. The receive thread read it while the relay's `stop()` held
      its lock for the post-fec shim's ≤ 50-ms join, then sent it once the lock was released.
    - The row's time is the new `start()` closing that open frame; `relay_stopped_ms` is mostly the frame-log
      thread's 0.5-s sleep.
    - **In CL-B14 it never reached the onn** (it was sent to the stopped shim's closed port). Without a shim it would
      reach the onn, where it counts only in `packets` / `bytes`.
    - **Fixed:** the relay's send target is cleared before its stop, and what was noted after the close is dropped.
      The mutation is caught 5 / 5 with the real relay on loopback. It takes effect at the next companion restart.
    - Record: `docs/memory/evidence/B26_RELAY_STOP_STRAY_PACKET_2026-10-27.md`.
- **The onn left the tailnet once:**
  - no-peer 19:38:33-19:45:50Z, ~1 min after it went idle and ~26 s after a companion restart;
  - a second restart was followed by a brief relayed reading only.
  - The cause is not in the hub's files. **Open.**
- **Underruns, in play:** 8.0 / min under the four lines, 20.2 on the ten-line afternoon sessions at 7000 (G4-S3 3.4).
  Audio packets lost 38 / 30 / 11 in three sessions. A watch item, with the Opus underrun item below.
- **Also:** the client sat "reconnecting" for 21 min after the closing restart (session 12's report is that tail).
  Known, as G4-S3 §5.

## 2026-10-21 LAN-R1: the ladder does not step down on loss on the LAN — OPEN; a rule BUILT behind `PRIVYHUB_LAN_LOSS_RULE=1`, NOT ADOPTED

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

> 2026-11-03: this item's original long heading and the B-queue / CL-B chronology that had grown under it (B1-B4, ML-R1, BENCH-R1..R3, queues C-K, CL-B10..CL-B16, B27 / G-A8, TRIP-PREP, UX-R4, LINK-R1, CL-B14, the old APK pins) moved verbatim to `docs/memory/archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md`. Still open from it: the loss guard / stall interaction (index above).

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

> 2026-11-03: `## 2026-09-20 link-drop resilience — stated requirement, not yet owned` moved verbatim to `docs/memory/archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md` (now owned by recovery v2 / `PRIVYHUB_LINK_RECOVERY`). The marker below closes this pair.

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

