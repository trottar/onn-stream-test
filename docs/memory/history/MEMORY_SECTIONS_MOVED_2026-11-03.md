---
memory_schema: 1
as_of: 2026-11-03
status: verbatim sections moved from docs/memory/MEMORY.md at commit b20729b8 (DOCS-APPLY; closed D-BASE-era detail; each left a one-line pointer in place). Nothing rewritten
---

# MEMORY.md sections moved 2026-11-03

<!-- MEMORY.md lines 167-190 at b20729b8 -->
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

<!-- MEMORY.md lines 265-403 at b20729b8 -->
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

<!-- MEMORY.md lines 414-467 at b20729b8 -->
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
