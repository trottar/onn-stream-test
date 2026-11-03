<!-- PRIVYHUB_C3_LINUX_ACTUATOR:BEGIN -->
## C3 Linux actuator boundary and classification — durable facts

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-09-23.md` (written while Phase C was suspended; Phase C CLOSED 2026-10-05, `evidence/C5_CLOSE_2026-10-05.md`. Its "not authorized for automatic adaptation during play" was superseded by `C3-L4`: live adaptive bitrate is adopted line 1, `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`; since G-A10, line 14, a step is spliced in place).

<!-- PRIVYHUB_C3_LINUX_ACTUATOR:END -->

<!-- PRIVYHUB_PHASE_E_G_DURABLE:BEGIN -->
## Phase E / G — durable facts (as of 2026-11-03)

Phase C (closed 2026-10-05), D-BASE (closed 2026-09-23) and the D series are
closed. Phase E is active (E1 frozen, E2 measured, E3 / E4 closed); the G
track is under way. Live state: `CURRENT.md`.

**An adopted line is one environment line in its own drop-in** under
`~/.config/systemd/user/privyhub-companion.service.d/` (`[Service]` /
`Environment=PRIVYHUB_…`), never the unit file and never the user manager's
environment (the preflight requires the manager to carry no `PRIVYHUB_*`).
Fourteen today, listed in `tools/e1_suite.py` `ADOPTED`, each with a
`drop_in_<name>` preflight term; `tools/e3_state.py` prints `ok` on
fourteen (the records' "`--check` ok"; `TOOLS.md` has the table). **The off switch is the same for
every line:** delete its drop-in, `systemctl --user daemon-reload`, then
`systemctl --user restart privyhub-companion`, and reverse the line's
applied `tools/e1_suite.py` diff so `--check` expects one fewer
(`evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md` §5; REMOTE_TRUST
§14). Per-run flags go in `e3_flag.conf` and come out at teardown; the
adopted state has none.

**Only the user's word adopts.** A line is built behind a flag (absent =
today), measured, and then put to the user as one plain question; the
record quotes the answer ("Adopt", G-A10; "Yes to both", TRIP-PREP). The
adoption ends with a **pre-registered confirmation window**: the rows
written and sha256-hashed before the run, one `e1_suite.py run … --e2`
window, each row MET / NOT MET as written (G-A10 §4). The session's
permission check may refuse writing a drop-in or installing a persistent
unit; then the user runs the exact lines (G-A1 §2; HOME-1, `privyhub-diag`).

**The APK rule (CL-B7 §6; HOME-1 "The CONFIRMED rule").** A candidate APK
is installed for a pre-registered run. It stays and becomes CONFIRMED only
if every cell that ran was valid; it is then pinned in `tools/e1_suite.py`
`EXPECT_APK` (and `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`). Otherwise the previous
CONFIRMED APK is reinstalled from its preserved copy
(`PrivyHub/app/build/<task>_installed/`, gitignored, nothing deleted) and
the pin does not move. `--check` reads `APK CONFIRMED` or `MISMATCH`.
Today: `fcd924c2…` (CL-B14's) CONFIRMED; `554ccf61…` NOT CONFIRMED (HOME-1's
C5 invalid); `0132b944…` (queue M) pinned, NOT installed.

**The band is the lever on the home link (LINK-R1, 2026-10-23).** On
5 GHz (5180 MHz, ch 36) one 10-min window had 0 uplink silences ≥ 250 ms
and 0 hitch seconds, against 22.4 silences and 19.9 hitch s on 2.4 GHz
(BENCH-R3 C): the band was most of the flapping (one window, daytime;
caveats in the record). The band is a hand change only the user makes
(UX-R4 §3). The CONFIRMED APK shows a 2.4-GHz link notice by default
(`setprop debug.privyhub.link_notice 0` = off, CL-B14); `diag_check.py`
line 5 reads the band.

**Away from home = the overlay plus session identity v2** (G-A1, lines 6-7;
`docs/REMOTE_TRUST.md` §3-§6). The provider sits behind a boundary
(`companion/overlay/provider.py`; `tailscale` reads `status` / `netcheck`
only, never installs or runs `up`); overlay absent = remote absent, local unchanged.
The source address is routing evidence (class `local` / `lan` / `overlay`
/ `unknown`), never identity: a device pairs once on the home LAN with a
one-time code, then signs a nonce-bound setup for an 8-h token; it declares
its media endpoint, which must share the source's class. Unpaired legacy
clients are LAN only, never over the overlay. No reverse proxy or
`tailscale serve` in front of the companion. The endpoint and addresses
are never logged; `logs/session_audit.jsonl` carries class and reason only.

**Remote-class sessions (line 13, G-A9; REMOTE_TRUST §14).** At each stream
start the host classes the session from the onn's address; on an overlay
address it turns on the remote ladder, the start rung `floor` (4000), the
remote cap 7000 and the WAN telemetry; on the LAN none acts (7000 from the
start). The cost away: every new session starts at 4000 and climbs ~3 min
a rung. Line 14 (G-A10) splices each bitrate step onto the same stream
(no new SSRC, no ~0.2-0.4-s gap; HOME-1 C2). B33 is live inside line 10
(off: `PRIVYHUB_REWIND_NEEDS_LOSS=0`).

**Long unattended runs are detached transient user units**
(`systemd-run --user --unit=<name> --collect -p WorkingDirectory=<repo> …`;
LINK-N1 §1): one `status.txt` line rewritten at each transition and every
few minutes (stale = not running), a `STOP` file checked every ≤ 30 s
(never removed by the tool; remove it before a restart), a cap written in
the pre-registration. Linger was off then, so a logout or reboot ends such
a unit.

**The diagnostics keeper `privyhub-diag` (B36) runs always** (installed
HOME-1, 2026-11-03; `tools/privyhub-diag.service`). Read-only on the hub:
redacted copies of the hub's logs into `~/privyhub_diag/<UTC day>/` every
300 s, samples every 60 s, a `sessions.jsonl` row per session, 30-day
retention (its only deletion), `status.txt` and `STOP` at the root. Read it
with `tools/diag_read.py` and check with `tools/diag_check.py`; it reuses
`tools/trip_log_keeper.py`, which must stay in the tree while the unit
exists (`evidence/B36_DIAG_KEEPER_2026-10-31.md`).
<!-- PRIVYHUB_PHASE_E_G_DURABLE:END -->

<!-- PRIVYHUB_BASELINE_STREAM_HEALTH:BEGIN -->
## D-BASE — CLOSED 2026-09-23: the baseline is met — curated conclusions

`evidence/D_BASE_CLOSEOUT_2026-09-23.md`; decision
`decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md` (closed). One line each:

- **Start (2026-09-20, 128 sessions):** spikes 2,535/min, fps 55.5, max gap
  287 ms, stale 193/min — the stream had never reached 60 fps.
- **Close (cold + warm, adopted build):** spikes 32.8 / 26.0, fps 59.90 /
  59.91, stale 1.1 / 0.8, video loss 8.7 / 8.4 (post-FEC), audio
  underruns 17 / 14 per session, max gap 163 / 110 ms. **The onn is not
  the ceiling** (Step 5 not triggered).
- **Client latency** fixed by `C3.L2c` + `P1` (98-99 % of frames < 20 ms).
- **Audio startup burst** fixed by the `P2a` hold (`P2b` validated).
- **Video loss** is the encoder's frame-size tail: the **90 KB cap**
  (`P6a`) cut it 7-9x.
- **Audio holes** are the path's (`P7`/`P8`): the **12/17 cushion**
  (`P9`/`P9a`) removes 98-99 % of starvation for +34-38 ms.
- **Warm-state loss** (`T2`/`T3`): single packets lost between the ends
  after ~7 min; **audio redundancy 2/4** (`P10`) recovers them, +1.6 Mbps.
- **Link-drop recovery** validated on real loss (`R3`-`R3d`); the recovery
  flow never loads into a live core (`R3c2`).
- **Host**: headless (`H2`), companion a systemd user unit (`H3`).
- **Open, not failures:** max output gap (transport, ~100-330 ms); the
  cause of the warm-state loss (`host_link`); the synthetic UDP
  pathology (PAUSED, `M1`).
- **Method:** a worst-case statistic must not overrule a distribution
  (`C3.L2c` was rolled back on one sample; the user kept it). A window is
  not a corpus. Pre-register the reading; ask when a clause fails on the
  favourable side (`P9a`, `P10`).
<!-- PRIVYHUB_BASELINE_STREAM_HEALTH:END -->

<!-- PRIVYHUB_C3_L2C_FALSIFIED:BEGIN -->
## Decode time is not the stall — durable fact

Measured 2026-09-19 by `C3.L2c`. Record:
`evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`.

Requesting `MediaFormat.KEY_LOW_LATENCY` unconditionally on
`c2.realtek.video.avc.decoder` — overriding its own `FEATURE_LowLatency`
self-report of unsupported — **works**: `low_latency_enabled` flips true.
**It does not help.** In the one session with the flag set, every codec
statistic was the best of eight that day (`max_codec_ms` 107 against
140-433, `spike_250_ms` 0) while **`max_output_gap_ms` was 385, second
worst of the eight** — in ordinary sessions the two track within ~10 ms;
here the gap exceeded the codec time by 278 ms.

**The durable lesson: `max_codec_ms` is not a valid proxy for
`max_output_gap_ms`.** Any candidate justified by "it lowers decode time"
must measure the output gap directly before acceptance. `C3.L2a` E2's
"decoder time is the largest measured contributor" holds as a correlation,
not a mechanism.

**Two corrections override the original wording.** The 2026-09-19 re-run
settled it and **the user KEPT the build**, so `low_latency_enabled: true`
is the shipping state and this is **not** a "do not retry" item. And the
385 ms gap **is no longer unexplained**: `P5` and `P6` locate that gap
class at the frame-size tail (see the loss block).
<!-- PRIVYHUB_C3_L2C_FALSIFIED:END -->

<!-- PRIVYHUB_D_BASE_R3_LINK_DROP_RECOVERY:BEGIN -->
## Link-drop self-recovery — durable facts

`D-BASE-R3` (2026-09-20), corrected by `R3a` the same day, and **confirmed
on natural evidence by `S2`** (2026-09-21). Records of those names plus
`investigations/LINK_DROP_RECOVERY_DESIGN.md`.

**The host is the authority on a desync and pauses the game itself.**
State machine `PLAYING`/`PAUSED_RECOVERING`/`PAUSED_SAVED`/`ENDED` in
`companion/games/link_drop_recovery.py`, every transition logged to
`logs/games/native_stream_recovery.log`. Triggers: controller silence >=
`DESYNC_MS`, or a client `POST …/native-stream-desync`. Pause and resume
go through `EmulatorManager.pause()`/`.resume()` only — `PAUSE_TOGGLE` is
a toggle and a raw send can invert the confirmed state. Constants:
`DESYNC_MS` 1,000, `RECOVERY_CLEAN_TICKS` 3, `GIVE_UP_MS` 120,000,
`RESTART_AFTER_MS` 2,000, backoff 5,000→30,000, `END_MS` 1,800,000.

**It works, on real link failure (`S2`):** seven `desync_pause` events,
**four on the host-side `controller_silence` trigger**, all resumed,
`recovering_ms` 4,713-78,355, `PAUSED_SAVED` never reached, one
`method: "restart"` succeeding while the fault was live. **A bad enough
link starves the client->host controller channel too.** **Still
unexercised: `GIVE_UP_MS`, `END_MS`, the recovery save** — all three
exercised since (`R3b`, `R3d`); the five-run set is complete.

**The recovery save is its own file, not a slot** —
`<stem>.state.recovery`; **RetroArch's `sort_savestates` puts states under
a per-core directory**, so it is *not* at the state root. **`AlertDialog`
ignores `setItems` when `setMessage` is also set.**

**Both original defects are fixed by `R3a`:** a failed `C3.L1` cycle
leaves no encoder, so recovery falls back to `NativeStreamManager.start()`
logging `method: "restart" | "full_start"`; and the restart trigger needs
two fresh rising heartbeats, logging `age_pair_ms`. **The gate's resume
floor is 2.0 s from when video returns**, and `_kill_managed_process` waits
5 s on `SIGTERM` — ~12 s per restart attempt against a SIGSTOPped encoder,
distorting any "time to resume" measured that way.

**Rule (user, 2026-09-22): a recovery state never loads into a live core**
— Resume a live session with no load; prompt only when none is live
(`decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`). **A mid-FMV
recovery save loops when loaded into a paused core — fresh or not — and
plays loaded into a running one (`R3c`)**, so **resume-from-recovery =
launch fresh → unpause → `LOAD_STATE_SLOT 0` into the running core →
pause for the handoff → delete the recovery files** (the user's option A,
`R3c2`, RUNTIME VALIDATED 2026-09-23). The paused `load_recovery_state`
and the player Save/Load path are unchanged.
**`save_state_probe.txt` is reset at every launch.**

<!-- PRIVYHUB_D_BASE_R3_LINK_DROP_RECOVERY:END -->

<!-- PRIVYHUB_D_BASE_R4_REPORT_VISIBILITY:BEGIN -->
## What the decoder report and the heartbeat record — durable facts

`D-BASE-R2` and `R4`, 2026-09-20. Records under `evidence/` and
`patches/`, named for them. Report-only.

**A slow event is recorded on `outputGapMs >= 50` as well as on
receive-to-output latency `>= 50`** (`R2`). Before that a session's worst
`max_output_gap_ms` routinely had no row — an arrival gap ends with a
frame fast by the latency measure, **the arrival-gap signature**. **Read
the trigger before reading an absence.**

**A gap that never ends is now recorded** (`R4`). `drainOutputs` records
a slow event only when a frame comes out, so a terminal stall used to
leave `max_output_gap_ms` at the last *completed* gap — 135 ms for a 46 s
stall. The client now checks output age on its 500 ms tick and at report
assembly and emits **`terminal_slow_event`** / **`output_age_at_end_ms`**,
in which `rx_to_decode_ms`, `feed_delay_ms` and `codec_ms` are **−1
sentinels**.

**Two magnitude-ordered top-16 lists**, `slow_events_top_gap` and
`slow_events_top_latency`, sit beside the FIFO segments and are why a long
session's worst event survives eviction. **They keep no union**;
**`slow_events_marked` has not existed since `C3.L2b`.**

**`logs/games/native_stream_heartbeat.log` is where a session that never
posts a report ends up**, and since `R5` **also where the per-minute loss
series comes from**; since `P7` it carries the audio block too (schema
**v3**, ~620 bytes a line, so 4 MiB is ≈3.7 h). Fields in `TOOLS.md`.
**The snapshot on `native-stream-status` lags up to 2 s**, which made a
counter-diff loss series unusable (`P4`).

**The native-stream logs are bounded**: heartbeat 4 MiB, recovery 1 MiB,
and `P5`'s `native_frame_sizes.jsonl` 4 MiB, each keeping 3 into
`logs/games/stream_log_archive/`, joined by `T1`'s
`host_resource_samples.jsonl`; `tools/diagnostic_retention.py` bounds the
archive through its `stream_log_archive` family. **Policy SHA-256
`b13fbc32dbf7f46a4ca9321985ea2d410804c15b9faaf82c3f87dce8356971b5`**,
which an `--apply` run must quote. **Rotation runs before the append** and
has lost nothing in practice (`R5`: 4 MiB crossed **17.9 min into a
session**, sequence step **1**; `S3`: both logs rotated twice over three
hours, **0 discontinuities in 10,801 rows**). **Anything slicing these
logs by line offset breaks across a rotation** — read archive and live log
together and filter on time.

<!-- PRIVYHUB_D_BASE_R4_REPORT_VISIBILITY:END -->

<!-- PRIVYHUB_D_BASE_P1_STALE_THRESHOLD:BEGIN -->
## The 60 ms stale threshold costs almost nothing now — durable fact

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-11-03.md` (`D-BASE-P1`, 2026-09-20: the 60 ms default already meets `rendered fps >= 59.5`; nothing was changed; `privyhub.stale_output_ms` stays the probe knob).

<!-- PRIVYHUB_D_BASE_P1_STALE_THRESHOLD:END -->

<!-- PRIVYHUB_D_BASE_P2_AUDIO_UNDERRUN_BURST:BEGIN -->
## The audio underrun count is a startup artifact — durable fact

*(Partly superseded, `P9`/`P9a`: with the `P2a` hold in force the startup
burst is gone and a 20-min total of 4-20 is mostly mid-session events of
1-3 — read events, not totals.)*

`D-BASE-P2` characterized it (2026-09-20), `P2a` fixed it and `P2b`
validated the fix (2026-09-21). Records of those names.

**A median 98.7 % of a session's `audio.underruns` occur in the first
three seconds**, ending the tick the audio queue first fills at the first
real PCM write (median 1,800 ms). **So "113 underruns/min" is a fixed
per-session burst divided by a short session**: across 177 sessions
`underruns` is flat at 116-162 from the 0-40 s bucket to 300 s+ while
starvation and concealment scale with duration (**−0.725**). **Do not read
`audio.underruns/min` as a rate**; read the per-session total. **Audio
loss does not drive underruns** (rho 0.113); a *shallow* queue does
(**−0.414**).

**The fix (`P2a`): `playbackLoop` waits for the first real PCM packet**
before the prefill and `AudioTrack.play()`, bounded at 3,000 ms. It had
given up after 100 ms while the first real packet arrives at ~1,800 ms.
**RUNTIME VALIDATED**: underruns median 6 against 207, replicated by P2b
at **19 on against 276 off**; `first_write_elapsed_ms` moves ~7 ms, so
audio is not delayed, only the track's start.

**The hold does not move `prolonged_starvation_events` (`P2b`)** — and
`P7` now says why: they are unrelated mechanisms, one a startup artefact
and the other a path-jitter rate. **`startup_wait_ms` identifies the
arm**: 0 with `timed_out: true` means the hold is out.

**`video.recent_fps` is a spot reading, not a session rate** — **43.8 to
71.6** across ten 120 s sessions whose true rate was 59.4-59.7, and **49.80
on an `O1` session that rendered 59.71**. Compute fps as
`decoder.rendered_frames / duration_s`.

**`audio.tick_series` is how any of this is readable.** One delta row per
existing 500 ms tick, capped at 400 rows = 200 s. **On a long session it
covers only the first 200 s**; the heartbeat log is the per-minute
series.

<!-- PRIVYHUB_D_BASE_P2_AUDIO_UNDERRUN_BURST:END -->

<!-- PRIVYHUB_C5A_STALLED_ENCODER_NO_SEQUENCE_GAP:BEGIN -->
## A stalled encoder makes no sequence gap — FALSIFIED as written

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-09-23.md` (`B2` falsified the universal claim; the per-run record is `evidence/B2_HOST_ON_OPAL_2026-09-21.md`).

<!-- PRIVYHUB_C5A_STALLED_ENCODER_NO_SEQUENCE_GAP:END -->

<!-- PRIVYHUB_C5_COMPLETENESS_GATE_FALSIFIED:BEGIN -->
## The completeness gate is not what makes a resync slow — durable fact

**`C5`'s second cost is FALSIFIED** (`D-BASE-S2`, 2026-09-21; record
`evidence/D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`). Of the seven
retained resyncs over 250 ms in a degrading 3-hour session, **six rejected
zero IDRs** including the longest at **1,340 ms**, and the one row carrying
a rejection took **240 ms while rejecting 1**, which the mechanism forbids.
Across `P2b`, `S1` and `S2`: **69 natural resyncs, 66 rejecting zero IDRs.**

**What the tail actually is.** Resyncs are mostly fast — p50 **71 ms**, p90
253 — and the long ones are distinguished by `dropped_non_idr_aus`
(40/54/67 on the three longest), not by rejections: the receiver waits for
an IDR **to arrive** on a link losing 389 packets/min, where the next
scheduled IDR is itself often lost and the wait becomes two or three GOPs.
`C5`'s "one GOP of unavoidable wait" stands; its second cost does not, and
**§5's bounded fallback is retired.**

<!-- PRIVYHUB_C5_COMPLETENESS_GATE_FALSIFIED:END -->

<!-- PRIVYHUB_R5_HEARTBEAT_LOSS:BEGIN -->
## The loss column: what explains it, and how to read it — durable facts

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-11-03.md` (`D-BASE-P4`/`R5`/`O1`/`P5`/`P6`/`S3`, 2026-09-21/22: the loss was the encoder's frame-size tail; the adopted 90,000-byte cap (`P6a`; `PRIVYHUB_ENC_MAX_FRAME_SIZE`, `=0` uncapped) cut it 7-9x and the residual is a floor; neither radio explains it; a heartbeat field takes two edits, the client and `plugins/games.py`'s key whitelist).

<!-- PRIVYHUB_R5_HEARTBEAT_LOSS:END -->

<!-- PRIVYHUB_P3_SENDER_PACING:BEGIN -->
## Sender pacing is not the loss lever at 150-400 us — durable fact

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-09-23.md`; the fact stands (`P3`: pacing is closed by measurement; the loss is the frame-size tail, `P6`).

<!-- PRIVYHUB_P3_SENDER_PACING:END -->

<!-- PRIVYHUB_B2_TOPOLOGY:BEGIN -->
## The production path is measured — durable fact

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-11-03.md` (`B2`/`H1`/`H2`, 2026-09-21/22: the PC path against the Opal, the host's display path, the SSH console, the headless cut-over behind a DisplayPort dummy plug, adb recovered from the host after a reboot. `H3`'s unit was installed since: `privyhub-companion`, `KillSignal=SIGINT`, `TOOLS.md`).

<!-- PRIVYHUB_B2_TOPOLOGY:END -->

<!-- PRIVYHUB_R3B_REAL_LOSS:BEGIN -->
## A recovery restart hides the outage from `lost_packets` — durable fact

`D-BASE-R3b`, 2026-09-22, the first real on-the-wire loss measured on this
build. Record: `evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`.

**Identical faults, loss counts 50x apart.** A **3 s** outage with **no**
encoder restart counted **2 348** lost packets. **15 s** and **150 s**
outages that **did** restart counted **22** and **40**. A restart spawns a
new ffmpeg with a **new SSRC**, so the client books the return as an
`ssrc_change` carrying `jump_packets: 0` — not as loss. **Every
loss-per-minute figure under-counts outages that restarted;
`max_output_gap_ms` is the honest column**, and it reproduced all three
faults to within 60 ms (3 114 / 15 116 / 150 090 against 3 060 / 15 060 /
150 070).

**Link-drop recovery works against real loss, as far as it was tested.**
Pause at 1.27-1.44 s after the drop; give-up at **120.42 s** against
120,000 ms; backoff 5/10/20/30/30 s; `.state.recovery` written, never a
slot. N15 reached the case no substitute fault could: an encoder restart
that **succeeded 9.45 s before the rule was deleted**, while every packet
was still being dropped. **`R3d` (hand runs, 2026-09-22): N15b PASS
(repeat of N15, resume 3.60 s after the clear); E30 PASS — `END_MS`
RUNTIME VALIDATED (`PAUSED_SAVED` → `ENDED` 1,801.4 s, clean shutdown);
N05 PASS on 2026-09-23 (0.556 s hole, no pause, one 423-packet
resync, max gap 625 ms) — **`R3`+`R3a` RUNTIME VALIDATED for real loss.****

**`C5` cannot be tested by a clean link drop.** All three resyncs returned
to an IDR in **40-75 ms**, nowhere near the 250 ms threshold, and
`idr_aus_rejected_waiting_for_idr` was 0 throughout. C5a stays
INDETERMINATE. Recovery is too fast to produce the slow resync C5 is about.

**A stopped stream does not end the game session** — `native-stream-stop`
pauses the game and keeps it, by design. Consequence, open as `R3b-D1`:
the launcher tile then resolves to `recovery-resume`, which loads a state
into the live process and reports **"Loaded"** with **no window opening**,
and no `POST /plugins/games/launch` is ever issued. Related, `R3b-D2`: after
that load the **source picture cycles through about four frames** while the
stream itself is clean. `load_recovery_state` also **does not remove**
`.state.recovery`, so the prompt reappears next launch.
`evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.

**Reading a picture complaint off the wire**: IDR size measures source
complexity, and per-second `max_bytes` from `native_frame_sizes.jsonl`
separates the three cases cleanly — spread **0 B** frozen, **3 686 B** a
short loop, **52 923-74 242 B** live gameplay. Mean frame size cannot: the
encoder is CBR and pads, so a loop and real gameplay both read ~14.5 KB.
<!-- PRIVYHUB_R3B_REAL_LOSS:END -->

<!-- PRIVYHUB_S1_SOAK:BEGIN -->
## Five hours of streaming: what holds and what grows — durable facts

`D-BASE-S1` (four 30-min sessions) and `S2` (one 3-hour session),
2026-09-21, on the **PC path**. Records:
`evidence/D_BASE_S1_OVERNIGHT_SOAK_2026-09-21.md`,
`D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`.

**The stream does not degrade with elapsed time**, to 150 minutes (`S2`)
and **180 on the capped profile** (`S3`, whose hourly loss *fell*:
380/340/253). `S1`: per-minute fps Spearman against elapsed minute
−0.298/−0.127/−0.119/**+0.246** — signs disagree — and **in two hours not
one output gap over 1 second**. Encoder CPU flat at **25.5-27.3 %**.

**Memory growth is a warm-up, not a leak — with a caveat since `S3`.**
`S2`: RetroArch **+119.9 MB over 3 h**, **file-backed** (`RssAnon` only
**+6.2 MB**). **`S3` does not reproduce that cleanly**: +140.2 MB total
but **+34.3 MB anonymous**, still rising at the end. Majority file-backed
either way, so the main claim survives — **but `S2`'s +6.2 MB is not
settled.** Re-check on the next soak.

**`prolonged_starvation_events` is an AUDIO ARRIVAL-GAP counter**
(`P7`, 2026-09-22 — this replaces the "what it counts is unknown" line).
The code latches it: **one increment per hole in the audio arrival stream
longer than ~15 ms** (three or more empty 5 ms queue polls), and it cannot
fire twice for the same hole. It is **not** a poll-quantized duty cycle.

**It measures jitter, not loss.** Over 596 ticks: rho **+0.684** against
the per-tick maximum audio inter-arrival gap, **+0.020** against audio
loss, **+0.036** against the packet deficit — which averages **+0.54 of
~400 expected**, so **no packets are missing, they are late**.

**The hole is periodic and not the sender's.** 93 % of ticks peak between
**50 and 69 ms** (median 55, p90 60) and only **6 of 596** stay under the
15 ms threshold, while the host's audio pacer measured **5.0 ms average,
max 5.08**. **The jitter appears between the host's socket and the
onn's.**

**The rate is a property of the path**: 75.9/min PC-path (`S2`),
35.8-40.7 Opal uncapped (`O1`), **32.0-32.5 Opal capped** (`S3`, `P7`).
The frame cap barely moves it — audio is low-rate, evenly paced and small,
never the bursty stream. **Read it as a path-jitter rate, not a fault**:
32/min came with **4 actual underruns in 20 minutes**. Sender pacing is
closed by measurement.

**The audio cushion is a profile setting; the CAPACITY sets the latency**
(`P9`, 2026-09-23). `audio_queue_{target,capacity}_packets` (5 ms each),
override `PRIVYHUB_AUDIO_QUEUE_*`. The target is only the startup prefill
(and the host's value lands after the first PCM); every hole's late burst
refills the queue to the capacity, so residence ≈ capacity − ~2 packets.
**12 / 17 is the profile default — adopted by the user 2026-09-23.**
Measured three times: **+33.5-37.9 ms residence, starvation -98-99.5 %**
(`P9`, `P9a`); 12 / 24 = +71.7 ms. The user's listen: "No issues from
playing for a minute or two" (user-stated).

**A 20-minute `audio.underruns` total is noise: 4-20 across six 3/8
sessions** (median 9.5), arriving as events of 1-3 spread through the
session (`P9a`, heartbeat deltas). Read events, not totals; one 8-event
(`P9`-B) is the only large one on record.

**The hole's origin is the path, not the client's 2 s senders** (`P8`):
~158 holes > 15 ms/min, half 50-60 ms; 5.7-6.6 % start within 100 ms of
a heartbeat send (uniform 5 %); the adb socket sampler moved the rate
-1 % — safe during audio measurements.

**Warm-state audio loss** (`T2`/`T3`): from cold, ~7 min at 1-6/min, then
30-90/min, single packets, lost **between** the ends (host `send_errors`
0, onn socket drops 0); idle resets it. **Mitigated by audio redundancy
2/4** (`P10`, adopted): each datagram sent twice 20 ms apart, loss
−96-98 %, +1.6 Mbps, no latency. onn CPU temp: `dumpsys thermalservice`.

**Nothing reorders, ever.** `late_or_reordered_packets` is **0** across
11 M packets on the PC path including a half-hour losing 389/min, and 0 on
the Opal path across `B2`, `O1`, `P5`, `P6`, `S3` and `P7`. **Natural
resyncs are rare and cheap on a healthy link** (three in two hours, all
jumping **exactly 128 packets**; zero in `S3`'s three hours) and frequent
the moment it degrades: 94 in one bad half-hour.

**Rotation has since run against real traffic and lost nothing** (`R5`);
the ~453 KB/h measured here became ~819 once R5 grew the line.

<!-- PRIVYHUB_S1_SOAK:END -->

<!-- PRIVYHUB_T1_THERMAL:BEGIN -->
## Thermals, both ends — durable facts

**Why (user, 2026-09-21):** the host is to be an **always-on server** and
the eventual **PS2 / GameCube** work needs headroom. Nothing acts on a
temperature; a thermal pause on recovery is deferred (`DEFERRED.md`).

**The onn: status via `getCurrentThermalStatus()` (0 throughout) and — found
by `T2` — a live `cpu-thermal` temperature via `dumpsys thermalservice`**
(62-70 °C streaming, HAL thresholds 95 / 125 °C). `/sys/class/thermal` and
`getThermalHeadroom` stay unavailable. *(Superseded: "the onn reports
thermal status only", `T1`.)*

**Host thermals ramp to a plateau and stay:** 54 → 60 °C over ten minutes,
42-44 → 57-59 °C over thirty. **The host warms while the onn reports
nothing.** Both ends ride every session without a harness (`TOOLS.md`).

**The `pgrep -f` trap applies to an explicit `ps` scan too**: a
`/bin/bash -c` whose command line contains the needle matches, so select a
pid by executable basename.

<!-- PRIVYHUB_T1_THERMAL:END -->

<!-- PRIVYHUB_NEGATIVE_RESULT_POLICY:BEGIN -->
## Record failures, not only successes

Durable memory must capture what did **not** work alongside what did: a
record preserving only successes teaches nothing and invites repeated
attempts down paths already known dead. Every meaningful patch, probe,
diagnostic or roadmap change records, in the same work: what was attempted
and why; what succeeded, with measurements; what failed, was rejected or
rolled back, with the measurement that decided it; what remains unknown;
and the durable lesson, promoted to `LEARNINGS.md` when it generalizes.

A rejected candidate, a rolled-back installer and a wrong-state rejection
are each a result. An absent failure section must mean "none occurred",
never "none were written down". Preserve superseded records rather than
deleting them; mark newer state authoritative. Raw measurements outrank
later summaries.

<!-- PRIVYHUB_NEGATIVE_RESULT_POLICY:END -->

## Memory health

Memory responsibilities remain separated:

- CURRENT.md: active resumable state.
- MEMORY.md: durable facts and rules only.
- CURRENT_HANDOFF.md: concise continuation instructions.
- `docs/ROADMAP.md`: current roadmap representation.
- `evidence/` records and investigations: chronology and proof (the dated
  `YYYY-MM-DD.md` logs ended 2026-10-10; archived under `archive/memory/daily/`).

When roadmap sequencing changes, synchronize active state, roadmap status
and handoff state without rewriting historical evidence.

Compression must not destroy measurements. The 2026-09-18 checkpoint cut
several active files to single-line assertions and left the C1/C2 Linux
baseline numbers outside the repository entirely. When shortening active
memory, verify the canonical evidence record holds the detail first.
