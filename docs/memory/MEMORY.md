<!-- PRIVYHUB_C3_LINUX_ACTUATOR:BEGIN -->
## C3 Linux actuator boundary and classification — durable facts

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-09-23.md` (Phase C is SUSPENDED; `CURRENT.md` "Do Not Reopen" keeps the classification: Linux is `video_only_restart`, not authorized for automatic adaptation during play).

<!-- PRIVYHUB_C3_LINUX_ACTUATOR:END -->

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

`D-BASE-P1`, 2026-09-20, thirteen sessions at 60/90/120/200 ms. Record:
`evidence/D_BASE_P1_STALE_THRESHOLD_2026-09-20.md`. **Nothing was changed;
the product default is 60.**

**Group A's "5.5 % of frames exceed 60 ms, 3.5 of the 4.5 fps deficit" is
a pre-`C3.L2c` measurement and is not true of the current build.** At the
default the policy discards **6, 17 and 15 frames** in three ~97 s
sessions — 0.1-0.3 % — so recovering all would add **0.06-0.18 fps**, and
across four thresholds it recovers nothing (59.65/59.56/59.06/59.27,
drifting with received-AU fps). **The default already meets `rendered fps
>= 59.5`.**

**`spike_20_ms` cannot respond to the threshold** — it is incremented from
`latencyMs` *before* the release decision. `P1`'s arms still differ on it
because the interleave repeated a fixed order: **rotate the order in any
re-run** and do not read that column as an effect.

**The probe knob stays in the tree with the product default.**
`AvcLowLatencyDecoder(staleOutputMs = …)`, default 60, via the intent
extra `privyhub.stale_output_ms`. The report carries
`decoder.stale_output_ms` and `decoder.rx_to_output_histogram_ms` — 20 ms
buckets over **rendered frames only**.
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

`D-BASE-P4` (the onn's radio), `R5` (the series), `O1` (the Opal), `P5`
(which queue) and `P6` (the control), 2026-09-21. Records of those names;
how to read any of it, `TOOLS.md`.

**The transfer function, established end to end — `P5` correlational,
`P6` by intervention:**

> **frame-size tail → large-frame incidence → wireless loss → forward
> gaps.** Cap the tail and every downstream term falls with it.

`P6` capped the encoder's largest frame at **90,000 bytes**: the
≥ 80-packet population went **718 → 0**, loss **2,696 → 311** and, on a
second pair, **2,896 → 408** — **7-9x** against a bar of 2x, forward gaps
306 → 105. **The `< 40`-packet windows were not raised**, the
bucket-specific pattern that makes it causal. **Achieved bitrate did not
move**: a cap does not starve the stream, it redistributes inside it.

**Two bounds.** The benefit **saturates** — a 60,000-byte cap ties on loss
(299 vs 311) — so the looser cap is the better setting. And **`P3`'s
pacing was insufficient at the current budget, not ineffective**: its
8 ms budget clamps above 53 packets a frame, exactly the tail.

**Uncapped, the loss is REPRODUCIBLE, not environmental.** Independent
20-minute sessions minutes apart agreed at **Pearson 0.964** (`O1`),
**0.890** (`P5`) and 0.854/0.779 between `P6`'s baselines: the attract
loop replays and **the loss follows the replay**. `R5`'s "episodic" meant
bursty-within-a-session, not random. **Capped, the lock is gone** — it was
a property of the tail. **Baselines drift ±15 % across a night with
identical frame distributions**, so bookend any arm.

**The supporting evidence.**

- **Loss tracks the frame-size TAIL, not the rate** (`P5`). Max packets
  per frame rho **0.583** over 240 ten-second windows and **0.780** over
  40 minutes; `frames >= 80` **0.569**/**0.779**, while frame *rate* and
  *mean* do not move. Uncapped, ~72,500 frames a session at CBR 7000:
  **p50 11 packets / 12 KB, p90 29 / 32 KB, p99 ~80 / ~90 KB, max ~207 /
  ~245 KB**; 4.0 % of frames >= 40 packets, **1.0 %** >= 80. **The knee is
  a step at 100 KB**: windows above it lose **46.3** packets against
  **1.2-4.2** below (`P6`).
- **It is NOT the onn's receive path** (`P5`). Its UDP socket dropped **0
  datagrams in 40 minutes**, and **0 again over `S3`'s three hours**;
  `rx_queue` peaked at **986,880 bytes of a 2 MiB buffer**; every `wlan0`
  error counter **+0**. **A larger client receive buffer is not a fix.**
  (`wlan0 rx_dropped` advances **+36,988** — broadcast filtering: 16.6x
  the loss, rho **0.040**. Never read it as stream loss.)
- **It selects the bursty stream.** Uncapped, video loses **0.21-0.29 %**
  while audio over the same radio in the same second loses less. The
  encoder is **CBR**, so average rate is not it either.

**By elimination the queue is the wireless hop** — the AP's per-station
queue or the air during the burst. Not observed directly, and it cannot be
on this AP, whose `tx failed` copies `tx retries` (below).

**ADOPTED 2026-09-22 (`P6a`): `max_frame_size_bytes = 90,000` is a
declared field of `native_game_720p60_reference`**, Linux `h264_vaapi`
only, in force with nothing set in the environment. Validated at **loss
249** against an uncapped 2,690-2,896, bitrate/fps/CPU unchanged; the user
checked the picture first ("could barely tell it was over the LAN",
**their words, not instrument evidence**).
**`PRIVYHUB_ENC_MAX_FRAME_SIZE` overrides it and `=0` runs uncapped**;
`any_override` is **false when only the profile decides**. Decision of
the same name under `decisions/`.

**Removing the tail removed the content-lock too.** `O1` found loss
reproduced session to session at Pearson 0.964 because the attract loop
replayed the same large frames in the same minutes; capped, it correlates
with nothing.

**And the residual is a FLOOR** (`S3`, three hours): **5.4 losses/min**,
lower than any 20-minute capped session, **every Spearman under 0.08**
over 1,080 ten-second and 180 per-minute windows, and a **flat** bucketed
table (0.80/1.05/0.85) where uncapped it rose 14-fold. **A tighter cap is
not a lever. The loss column is closed at this level.**

**The driver's cap is a target, not a hard ceiling.** Two frames in three
hours came **9-11 bytes over** 90,000; `P6`'s 60 KB arm measured 60,092 —
about **0.02 %**. Harmless (~76 packets against a >= 80 threshold) but **a
check must allow a tolerance, not test the cap exactly**.

**Levers, measured by `P6`.** The adopted cap gives 7-9x less loss at no
cost in bitrate, fps or encoder CPU. **VBV is not the same lever** —
`-bufsize` at the one-frame budget loses **3x more** and alone *raised*
small-frame-window loss: it trades the tail for a higher floor. A 60 KB
cap ties. **`slices` and intra-refresh do not exist** here and **average
QP is not exposed** (`q=-0.0`) — why adoption waited on the user's look.

**Neither radio explains it.** From the onn (`P4`): loss/min swung 1.4 ->
105 (74x) while RSSI spanned 5 dB, median -66 every session, no scan inside
any session; at n = 597, receive rate vs RSSI **rho -0.022**. From the
Opal (`O1`, 40 min, 269 rounds): loss swung **0-331/min** with channel
utilization **rho -0.434**/min (wrong sign) and **-0.008** at 10 s,
`tx retries` **+0.219**, and **every** `dropped`/`errors` counter on every
interface **constant 0**. **The channel is ~93 % idle while streaming**
(`S3`: mean 6.82 % over three hours, and a 56.6 % excursion moved the loss
not at all, rho +0.073); retries run **10.2-11.3 %** at -70 dBm and do not
track loss. **`sta0`/`sta1` are `Not connected`.**

**What each end can and cannot report.**

- **The onn** (`P4`): 5 GHz **5180 MHz, ch 36, 80 MHz**, 802.11ac, **never
  re-associated**. Live RSSI, link quality, Tx/Rx link speed, `rx_pps`, a
  scan log, and a **`WifiScoreReport` ring — 3,600 rows at ~3 s over
  ~three hours**, append-only, so harvesting it *after* a session costs
  nothing. **No retry, failure, airtime or channel-occupancy counter
  exists at all** — full absence list in `TOOLS.md`, every entry an
  **absence, never a zero**. **But `/proc/net/udp6` is readable and
  carries the receive-buffer `drops` column** (`P5`'s instrument; the
  client's Java socket binds the IPv6 wildcard, so `udp` alone shows
  nothing).
- **The Opal** (`O1`): per-station `tx retries`, tx/rx counters, signal,
  bitrate/MCS/NSS/width, noise, per-interface counters. **Three traps,
  exact readings in `TOOLS.md`:** `survey dump` does not accumulate (a
  fixed 29-30 ms window, never differenced); `channel utilization` is that
  window rounded, quantised in 3.33 % steps at a **0.3 % duty cycle**; and
  **`tx failed` is not independent of `tx retries`**, so **retry
  exhaustion is unreadable here**. `/proc/net/wireless` is all zeros on the
  Opal too. Its SSH host key is RSA-only (Dropbear); it is **read-only
  from this project and nothing is installed on it.**

**The heartbeat carries the receiver's seven cumulative loss counters**
(`R5`) and, since `P7`, **ten audio counters** — schema
**`…heartbeat_v3`**, fields in `TOOLS.md` — read from the **same
snapshot the heartbeat already took**, so **a delta between any two
heartbeats of one session is exact**. `native-stream-status` carries
`loss_per_min_recent`; **None, never 0**, when unmeasurable. **Adding a
field takes TWO edits**: the client *and* `plugins/games.py`'s key
whitelist, which drops unlisted keys silently.

**The counters are the report's.** At the last heartbeat of a 20-minute
session **all seven matched the report exactly**. **Do not revive `P4`'s
derived series** (`relay_rtp − client_rx`, noise sd **86 packets per 10 s
window against a 3.0-packet signal**).

**Size loss measurements in tens of minutes.** The instruments cost
nothing visible: the heartbeat line went 276 → 465 → **~620 bytes**, the
relay's frame counting **0.36 us per packet**.
<!-- PRIVYHUB_R5_HEARTBEAT_LOSS:END -->

<!-- PRIVYHUB_P3_SENDER_PACING:BEGIN -->
## Sender pacing is not the loss lever at 150-400 us — durable fact

Moved verbatim to `history/MEMORY_SECTIONS_MOVED_2026-09-23.md`; the fact stands (`P3`: pacing is closed by measurement; the loss is the frame-size tail, `P6`).

<!-- PRIVYHUB_P3_SENDER_PACING:END -->

<!-- PRIVYHUB_B2_TOPOLOGY:BEGIN -->
## The production path is measured — durable fact

`D-BASE-B2`, 2026-09-21. Record: `evidence/B2_HOST_ON_OPAL_2026-09-21.md`.
**Host wired directly into the Opal, onn wireless, one hop**, gate-checked
on the host before any session ran. Everything measured before that date
ran host -> **Windows PC** -> Opal -> onn.

**The Windows PC is neither implicated nor exonerated.** Six attract-mode
sessions: loss/min median **16.6** against **46.3**, per-gap burst **4.46**
against **11.17**, forward gaps 7 against 11. Every transport column moved
together, but **2.8x is not the order of magnitude the pre-registration
required**, the burst did not collapse toward 1, and **the arms overlap** —
three PC sessions quieter than all six Opal ones, against a day-to-day
swing of 12.6x. **Do not read a 2.8x median shift as a verdict.**

**The host's display path** (`H2-PREP`, 2026-09-22;
`evidence/H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`): a real **X11**
LightDM/XFCE session; the monitor on X **`DisplayPort-0`** = DRM
**`card0-DP-1`**, the two spellings **off by one**; no `xorg.conf`
anywhere, so a forced mode persists through an `xorg.conf.d` `Monitor`
section keyed on the **output name**.

**The console for the headless period exists** (`H1`, verified 2026-09-22;
`evidence/H1_VERIFY_SSH_CONSOLE_2026-09-22.md`, procedure in `TOOLS.md`):
**SSH from the PC on the Opal wifi, key-only** (password, keyboard-
interactive and root login all off; one ED25519 key), with **LightDM
autologin** from `/etc/lightdm/lightdm.conf.d/10-autologin.conf` bringing
up an active X11 `seat0` session at every boot with no password typed.
**`DISPLAY=:0` is the only export the companion needs from SSH** — X
authorises the project user through `SI:localuser:privyhub`, so no
`XAUTHORITY` is required. Still true: **`Linger=no`, nothing at boot** —
a reboot kills tmux and starts no companion.

**The host is headless behind a DisplayPort dummy plug** (`H2`,
2026-09-22; `evidence/H2_HEADLESS_CUTOVER_2026-09-22.md`): X
**`DisplayPort-1`** = DRM **`card0-DP-2`** (not the monitor's port), at
**1920x1080 @ 60.00 Hz by the plug's own EDID** — no X config written.
**Capture verified without a monitor**: the same 879x720 RetroArch window
(`-window_id`, never the screen), 60 fps, x11grab PTS delta 1 on every
interval, 0 repeated frames in motion, session numbers inside the
monitor-attached `B2` range. Headless changes the desktop, not the
capture. **RUNTIME VALIDATED across two plug-only boots**: an unattended
power cycle comes back to the autologin desktop at 1080p60 with adb
recoverable from the host — but **nothing starts the companion at boot**
yet: `H3` (2026-09-23) designed a systemd **user** unit on
`default.target` (XFCE never activates `graphical-session.target`),
`DISPLAY=:0`, a bounded wait for X, **`KillSignal=SIGINT`** (the companion
shuts down cleanly only on SIGINT; SIGTERM orphans a game) — **not
installed**, the user's call.

**adb after a host reboot is recovered from the host**:
`adb connect <onn-address>:5555`, because the user pinned the listener
with `adb tcpip 5555`. Wireless only, no USB path. A **TV** power cycle
can undo the pin, and then the port is readable only on the TV (`H1` §5).
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
- roadmap status: current roadmap representation.
- dated memory/evidence/investigations: chronology and proof.

When roadmap sequencing changes, synchronize active state, roadmap status
and handoff state without rewriting historical evidence.

Compression must not destroy measurements. The 2026-09-18 checkpoint cut
several active files to single-line assertions and left the C1/C2 Linux
baseline numbers outside the repository entirely. When shortening active
memory, verify the canonical evidence record holds the detail first.
