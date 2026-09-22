---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
---

# Group A diagnostic audit — A1, A2, A3, A4

Authorized scope: `investigations/SEAMLESS_LOCAL_PLAY_TEST_BATTERY.md`,
Group A only. Groups B and C were not authorized and were not run.

## Classification

**A2: COMPLETE — RE-SCORED FROM EVERY SESSION ON DISK. Two standing claims
falsified, two metric defects found.**
**A3: COMPLETE — encoder emission cadence measured from on-disk logs;
unique-frame count and grab cadence measured live 2026-09-20 (see "Live
half" at the end): 60 grabs/s at exact 1/60 cadence, 99.6 % unique.**
**A1: COMPLETE — static audit plus on-wire capture 2026-09-20 (see "Live
half"): no B-frames, `max_num_reorder_frames = 0`, `max_dec_frame_buffering
= 1`, `dpb_output_delay = 0`. Hypothesis falsified; the fix, if any, is
client-side.**
**A4: PARTIAL — host side measured 2026-09-20: wired (`r8169`), no radio
present, one wireless hop by role; the onn's association still unread;
`host_link` field not implemented.**

## Run conditions, stated before any result

- A second pass later the same day **had a host shell** and closed the live
  halves of A1 and A3 and the host side of A4. It is recorded under "Live
  half" at the end of this file; everything between here and there is the
  first pass, unchanged.
- The session that produced this record had **file access to the host and no
  shell on it**. It could not start the companion, launch RetroArch, run
  ffmpeg, ffprobe, `iw` or `nmcli`, or drive the onn over ADB. Every live
  step in A1, A3 and A4 is therefore INDETERMINATE for that reason alone, not
  for a physical-action reason. The companion was not running at the start of
  the run (stated by the user) and nothing was started, so teardown is
  trivially satisfied: no process was created on the host and no capture
  artifact was written outside `docs/memory/evidence/group_a_2026-09-20/`.
- Everything below marked *measured* was derived by parsing the raw files
  named, with the scripts retained in
  `evidence/group_a_2026-09-20/`. Re-run either script against the repository
  root to challenge any number here.
- No network address, MAC, ADB endpoint or device identifier appears in this
  record. The host's wireless interface name embeds a MAC and is not
  reproduced; it is referred to by driver and bus.

---

## A2 — Re-score of every decoder session on disk

Source: `logs/games/decoder_sessions/*.json`, all 152 files. 148 carry a
decoder block. Selection for aggregates: decoder block present, duration
>= 15 s, received 2026-09-16 or later — **128 sessions**, 127 excluding the
single `low_latency_enabled` session (`C3.L2c`). The 2026-09-15 bring-up
sessions (8 files, rendered fps 1.6-16.6) are excluded exactly as the
2026-09-20 baseline record excluded them.

Script: `group_a_2026-09-20/a2_rescore_decoder_sessions.py`. Output:
`a2_rescore_result.json` (all statistics), `a2_session_table.csv` (one row
per file, every field used).

### A2.0 — The "47 sessions" of `BASELINE_STREAM_HEALTH_2026-09-20.md`

That record says it aggregated "every decoder session on disk of 15 s or
longer, 47 sessions spanning 2026-09-16 to 2026-09-20". Measured: there are
**128** such sessions. The newest **50 files** on disk contain exactly **47**
sessions of >= 15 s. The 47-session corpus was the last 50 files, not the
disk. Its epoch A ("21 sessions before the flattening, worst stall 338 ms")
was therefore 21 of the 73 pre-flatten sessions that exist.

Aggregate over the full 127-session corpus, excluding `C3.L2c`:

| metric | median | p10 | p90 | min | max | baseline record said |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| spikes >= 20 ms / min | 2,535 | 2,383 | 2,651 | 779 | 2,825 | 2,506 |
| spikes >= 50 ms / min | 274 | 228 | 330 | 192 | 504 | — |
| rendered fps | 55.5 | 51.5 | 56.8 | 13.4 | 57.5 | ~56 |
| received video fps (complete AUs) | 59.2 | 57.1 | 59.7 | 21.7 | 59.9 | — |
| max output gap (ms) | 287 | 133 | 607 | 99 | 7,341 | 345 |
| stale output drops / min | 193 | 149 | 257 | 124 | 341 | 181 |
| lost packets / min (as reported) | 196 | 12 | 729 | 0 | 4,728 | 199 |
| audio underruns / min | 113 | 31 | 414 | 8 | 10,090 | 155 |
| max codec in flight | 11 | 10 | 13 | 7 | 14 | 11-13 |

The headline medians survive. Three things that were built on top of the
47-session view do not; they are A2.2, A2.4 and A2.5 below.

### A2.1 — Q: do audio underruns and decode spikes co-occur, or move independently?

*Limitation stated first:* the session report carries audio underruns only as
session totals. No per-event audio timeline exists in any artifact on disk,
so within-session co-occurrence cannot be measured. What can be measured is
whether the two move together across sessions.

Measured:

- **Underruns are dominated by a fixed per-session burst, not a rate.**
  Total underruns per session regressed on duration: intercept **320 per
  session**, slope 19.7/min with p = 0.61 (not distinguishable from zero),
  r = 0.045. Underruns/min vs duration: Spearman rho = **-0.83**
  (p = 7e-33, n = 127). Sessions >= 300 s (n = 8): median **17.5/min**, median
  total 182. Sessions < 40 s (n = 39): median 263/min, median total 115.
- After removing the duration effect (residual of the fit), the residual
  underrun count correlates with decode pressure and not with packet loss:
  vs spikes >= 50 ms/min rho = 0.35 (p = 5e-5); vs spikes >= 80 ms/min 0.39;
  vs stale drops/min 0.35; vs audio prolonged-starvation events/min 0.43;
  vs **video lost packets/min 0.04 (p = 0.67)**; vs audio lost packets/min
  0.20.
- Audio starvation events/min vs video loss/min: rho = -0.05 (p = 0.61).
  Audio loss/min vs video loss/min: rho = 0.10 (p = 0.28). The two UDP
  streams do not share their loss.

Reading: the "155/min" audio figure is a session-length artifact — most
underruns happen once per session (startup or an outage), and the
steady-state rate in long sessions is ~17/min. The part that varies
co-varies with decode-side pressure (rho 0.35-0.43), not with the link's
packet loss (rho 0.04). That points at shared host or client scheduling
pressure rather than the link, which makes Step 4 a joint investigation with
the decode path rather than a separate one — but weakly (rho ~0.4), and only
cross-sectionally. A per-event audio timeline is the missing instrument.

### A2.2 — Q: is loss bursty or uniform?

Measured, all 127 sessions:

- lost packets per forward-gap event: median **14.3**, p90 26, max 68.5;
  97.6 % of sessions above 1.5. Uniform independent loss at the observed
  0.6 % would give ~1.0.
- `max_forward_gap_packets`: median **39**, p90 108, max 125 — and 125 is a
  censoring artifact: any gap >= 128 packets becomes a sequence resync (see
  next point). At ~840 packets/s, 39 packets is ~46 ms of stream and 125 is
  ~150 ms.
- `late_or_reordered_packets`: **0** across the whole corpus. Nothing
  arrives out of order; things arrive late in bursts or not at all.
- Loss/min median by day: 09-16 392, 09-17 246, 09-18 31, 09-19 174, 09-20 60.
  It moves by an order of magnitude day to day with no code change on the
  transport path.

**Metric defect found: `lost_packets` excludes every gap >= 128 packets.**
`RtpH264Receiver.beginStreamResync` resets `lastSequence` to -1 without adding
the jump to `lostPackets`; the jump is recorded only as
`largest_resync_jump_packets` (max) and, since `C3.L2b`, in
`stream_discontinuities[].jump_packets`. Over the 50 post-`C3.L2b` sessions:
reported lost 23,521 packets, resync jumps **53,679** — the counter misses
**2.3x more packets than it counts**. Corrected loss/min median **252 vs 120
reported**; corrected loss rate 1.51 % vs 0.465 % reported. The biggest
single jump on disk is 29,228 packets (~35 s of stream) in the
2026-09-20T00:08 session; the 7,341 ms session's one resync was 4,632
packets (~5.5 s).

Verdict: **bursty, in outage-class bursts**, matching the deferred UDP
burst/gap pathology signature (`D_LINUX_ONN_STREAM_DIAGNOSIS_2026-09-15.md`:
idle kernel-arrival gaps to 435-792 ms on this path). Not a link budget.

### A2.3 — Q: does spike rate rise with elapsed session time?

Measured:

- Cross-session: spikes >= 20 ms/min vs duration rho = **0.05** (p = 0.57).
  Spikes >= 50 ms/min vs duration rho = -0.19; stale drops/min vs duration
  rho = -0.29 (both fall slightly with length — a startup component again).
- Within-session: the retained slow-event buffer is the *end* of the session
  (64-entry rolling tail since `C3.L2b`, 128 before), so its event density
  can be compared to the whole-session average. Ratio tail/whole for the 70
  sessions >= 60 s: median **0.98**, p10 0.85, p90 1.20. The eight sessions
  >= 300 s: 1.02, 0.99, 1.07, 0.67, 0.87, 0.95, 1.51, 0.99 (the 1.51 is a
  10 s tail window in a 745 s session).
- Host side: encoder emission fps is flat at 60.00 across sessions up to
  1,087 s (A3).

Verdict: **flat.** No thermal or leak signature in decode spikes, host
cadence or stale drops. Rule both out; do not chase them.

### A2.4 — Q: does `stale_output_drops` track in-flight depth, or loss?

Measured, cross-session (n = 127):

| `stale_output_drops/min` vs | rho | p |
| --- | ---: | ---: |
| `max_codec_in_flight` | **0.04** | 0.64 |
| spikes >= 50 ms/min | **0.87** | 4e-40 |
| spikes >= 80 ms/min | 0.84 | 9e-35 |
| rendered fps deficit (60 - fps) | 0.85 | 6e-36 |
| lost packets/min (reported) | 0.47 | 3e-8 |
| lost packets/min (corrected, n = 50) | 0.51 | 2e-4 |
| max output gap | 0.28 | 1e-3 |

Loss-stratified: sessions with < 20 lost/min (n = 15) have stale drops
median 177/min, fps 56.5; sessions with >= 400 lost/min (n = 42) have
227/min, fps 53.4. Roughly four-fifths of the stale-drop rate is present
with the link nearly clean.

Measured, per slow event (13,485 events >= 50 ms receive-to-output, all
non-low-latency sessions): `codec_in_flight` at the moment of the event —
1: 1,698; 2: 3,929; 3: 4,606; 4: 2,535; 5: 463; 6-7: 159; **>= 8: 95
(0.7 %)**. Median 3. By severity: events of 50-80 ms have in-flight median 3;
80-150 ms median 3; 150-300 ms median 2; **300+ ms median 2 (mean 2.28,
n = 122)**. `feed_delay_ms` median 0, > 5 ms in 7.2 % of events.
`output_gap_ms` vs `codec_ms`: rho = **0.925**.

Verdict: stale drops track **client receive-to-output latency (the spike
distribution)**, not in-flight depth, and only secondarily loss. The
"decoder holds 11-13 frames in flight" figure in the baseline record is the
session **maximum** (`max_codec_in_flight`), reached transiently (startup /
resync refill); during the slow events themselves the decoder holds **2-3
frames**, and during the 300 ms+ stalls it holds 2. The baseline record's
mechanism — "buffering for throughput, 180-220 ms of pipeline depth" — is
not what the raw slow events show. See A2.5 for what they do show.

### A2.5 — Not asked, but answered by the same pass: the stall tail

The current work item (Step 1 of `BASELINE_STREAM_HEALTH.md`) rests on
"worst stall 338 ms across 21 sessions before 2026-09-19 01:37 UTC, 7,341 ms
after" and names the `C3.L2b` hot-path instrumentation as the stronger
suspect. Measured on the full corpus:

| epoch | n | max gap median | p90 | worst five | > 1,000 ms |
| --- | ---: | ---: | ---: | --- | ---: |
| A: pre-flatten | 73 | 274 | 467 | **2,035**, 1,832, 1,350, 934, 691 | 3 |
| B: flat, pre-`C3.L2b` | 4 | 631 | — | 1,374, 854, 408, 309 | 1 |
| C: post-`C3.L2b` | 50 | 324 | 664 | 7,341, 3,783, 1,997, 1,271, 1,062 | 5 |

- Pre-flatten stalls of 2,035 ms (a 1,085 s session on 09-16), 1,832 ms and
  1,350 ms exist. The 338 ms ceiling was an artifact of the 21-session
  window.
- A vs C: max gap Mann-Whitney p = 0.045; share > 400 ms 13/73 vs 15/50
  (Fisher p = 0.13); share > 1,000 ms 3/73 vs 5/50 (p = 0.27). Spikes/min,
  fps and stale drops/min are identical between epochs (p = 0.33, 0.99,
  0.80). A modest shift in the tail, no shift in anything else.
- What the tail *is*: `max_output_gap_ms` vs `largest_resync_jump_packets`
  rho = **0.66** (p = 3e-17); vs `max_resync_to_idr_ms` rho = 0.65. In every
  session with a gap above 1,000 ms, `max_codec_ms` equals the gap within
  ~10 ms — the last decoded frame sat inside the codec for the whole gap —
  and every one of them carries an outage-class resync jump or heavy loss
  with hundreds to thousands of packets dropped waiting for an IDR:

| session (UTC) | gap ms | largest jump (pkts) | resyncs | max resync->IDR ms | pkts dropped waiting for IDR |
| --- | ---: | ---: | ---: | ---: | ---: |
| 09-20 00:27 (849 s) | 7,341 | 4,632 | 1 | 73 | 112 |
| 09-20 00:08 (142 s) | 3,783 | 29,228 | 15 | 2,555 | 2,019 |
| 09-16 05:11 (1,085 s) | 2,035 | 327 | 72 | 558 | 5,073 |
| 09-20 04:23 (88 s) | 1,997 | 405 | 38 | 664 | 3,226 |
| 09-16 01:25 (105 s) | 1,832 | 1,105 | 67 | 1,038 | 5,235 |
| 09-19 01:43 (20 s) | 1,374 | 2,364 | 3 | 261 | 279 |
| 09-16 01:31 (41 s) | 1,350 | 622 | 38 | 755 | 4,325 |
| 09-19 14:51 (64 s) | 1,271 | 175 | 2 | 205 | 9 |
| 09-20 04:28 (142 s) | 1,062 | 373 | 15 | 962 | 1,765 |

  Sessions with max gap <= 200 ms (n = 27): largest jump median 0, one
  session with any resync at all.
- The 7,341 ms event itself is **not in the retained slow-event list** of its
  session (retained max 346 ms). The 64-entry rolling tail evicted it. This
  is the second metric defect: the retention added by `C3.L2b` protects
  cycle windows, but the worst ordinary-play event of a session is still
  lost unless it happens in the last 64 events.

Verdict: **the stall tail is transport outages plus the IDR wait, not
client code.** A stall of N ms is a sequence jump or loss burst of roughly N
ms of stream, followed by the receiver's wait for the next complete IDR
(GOP 15 = 250 ms at best; up to 2,555 ms measured when the IDR itself keeps
being hit), with the last good frame held inside the codec meanwhile.
`C3.L2b`'s per-frame bookkeeping cannot produce a 4,632-packet hole in the
RTP sequence space. **Step 1 as written (revert `C3.L2b`, compare the
tail) tests a cause the data already excludes.**

### A2.6 — Not asked, but needed to read the spike column correctly

`spike_20_ms` counts frames whose latency from **access-unit completion in
the receiver to decoder output** is >= 20 ms (`AvcLowLatencyDecoder.
drainOutputs`, `latencyMs = now - info.presentationTimeUs`, where the
presentation time is stamped at AU completion). It is not decode time and it
is not measured against the 16.7 ms frame period. Frames above 60 ms are
dropped unrendered (`stale_output_drops`); frames between 20 and 60 ms are
rendered normally.

Measured shares per session (median, n = 127): receive-to-output < 20 ms
**28.4 %**; 20-60 ms, rendered **66.3 %**; > 60 ms, dropped **5.5 %**. The
rendered-fps deficit decomposes as: network (incomplete AUs never queued)
**0.85 fps**, client stale-drop policy **3.5 fps**. The `C3.L2c` session:
95.5 % of frames under 20 ms, stale 0.5 %, 59.0 fps.

Reading: "~70 % of every frame misses the 16.7 ms budget" is a restatement
of "the decoder's steady-state receive-to-output latency is 20-60 ms". That
is a latency finding (real, and `C3.L2c` shows it is reducible), not a
throughput failure; the frames are decoded. The fps shortfall is mostly the
client's own 60 ms stale threshold acting on that latency distribution.
Whether 20-60 ms of client pipeline latency is acceptable is a product
question; the target table currently answers it "no" via `spike_20_ms`.

### A2.7 — The `C3.L2c` 385 ms gap, which `MEMORY.md` records as unexplained

Measured, `native_decoder_20260919_042611_053.json` (the one
`low_latency_enabled` session): `max_output_gap_ms` 385, `max_codec_ms`
107, **`max_rx_to_decode_ms` 111**. No frame in that session waited more
than 111 ms between arriving complete and leaving the decoder, so an output
gap of 385 ms contains at least **274 ms during which no complete access
unit arrived**. Transport in that session: 5 forward-gap events, largest 31
packets, 5 sequence-gap AU drops, 3 incomplete-AU drops, 8 frames dropped.

Reading: with the codec hold removed, the output gap stops tracking
`codec_ms` and exposes the arrival gap directly. That is why `C3.L2c` moved
`max_output_gap_ms` 359 -> 385 while improving everything else — it did not
create the gap, it stopped hiding where the gap comes from. Owner: transport.
The `C3.L2C_FALSIFIED` record's rule stands (measure the gap directly), and
its open question now has an answer.

---

## A3 — Host-side capture cadence

### Measured from disk: `logs/games/native_video_alpha.log`

The Linux backend appends ffmpeg's full stderr per session, including the
progress line every ~0.5 s (`frame=`, `time=`, `dup=`, `drop=`). Script:
`group_a_2026-09-20/a3_encoder_cadence_from_log.py`; per-session output in
`a3_encoder_cadence_from_native_video_alpha.json`.

- 160 encoder sessions, **924,385 frames over 15,407.8 s of stream time =
  59.995 fps** overall. 69 sessions >= 60 s, longest 1,087 s.
- PS1 (Beetle PSX HW, window 879x720, 153 sessions): per-session average
  fps median **60.004**, min 60.000, max 60.066; **dup 9, drop 1** in
  915,463 frames.
- SNES (bsnes, window 879x672, 7 sessions): average 59.94 median, min
  **59.005**; dup 0, **drop 103** in 8,922 frames — one dropped grab per
  second, with x11grab reporting `59 tbr` in those sessions. Not the current
  test title, but it is a cadence anomaly specific to the SNES window and
  is recorded here for whoever streams SNES next.
- Instantaneous fps between consecutive progress samples: 32,719 samples,
  **11 below 58 fps**, minimum 56.6 (two missed grab slots in one 0.5 s
  window). No session shows a sustained deficit.
- x11grab errors: one `Cannot get the image data` across all sessions.
  Encoder `speed=` never fell below 1.0x.

What this establishes: the encoder emits 60.0 frames per second of stream
time, with wall-clock PTS from the grab (no `-r` on the command line, and
`dup=0` shows ffmpeg's vsync is not synthesizing frames to hold cadence),
continuously, for as long as a session runs. The host is not delivering fewer than 60 encoded frames
per second and is not delivering them unevenly at the resolution of a 0.5 s
sample.

What this does **not** establish: whether consecutive grabs are
pixel-identical. x11grab samples the window on a 60 Hz timer regardless of
whether the emulator redrew, so the emission count cannot distinguish 60
unique frames from 55 unique plus 5 repeats. RetroArch reports the core at
59.826/59.940 fps with `gl` vsync on a 60 Hz display, so the expected beat
is well under one repeat per second, but that is inference.

### INDETERMINATE — unique-frame count and PTS deltas at the grab stage

Reason: requires a live capture on the host; no host shell in this session.
The measurement that closes it, for the next session with a shell, with the
managed RetroArch window on screen and a title in attract mode (state which,
and confirm motion):

```
WIN=$(xdotool search --name 'RetroArch' | head -1); \
ffmpeg -hide_banner -f x11grab -framerate 60 -window_id "$WIN" -i :0.0 -t 30 \
  -f framemd5 logs/games/a3_grab_framemd5.txt
```

`framemd5` is lossless and writes one line per grabbed frame with its PTS
and content hash: duplicates are consecutive identical hashes; PTS deltas are
the grab cadence. Then count with:

```
python3 - <<'EOF'
rows=[l.split(',') for l in open('logs/games/a3_grab_framemd5.txt') if l[0]!='#']
pts=[int(r[1]) for r in rows]; md=[r[-1].strip() for r in rows]
d=[b-a for a,b in zip(pts,pts[1:])]
print('frames',len(rows),'dups',sum(1 for a,b in zip(md,md[1:]) if a==b),'pts_delta_min',min(d),'max',max(d),'mean',sum(d)/len(d))
EOF
```

Content requirement carried forward from the battery: attract/demo loop
preferred; otherwise inject input through the D-076 uinput backend unchanged.

---

## A1 — Encoder bitstream audit

### Static, from current source (measured against the file, not intent)

`companion/native_stream.py::_build_linux_ffmpeg_command` (unchanged since
`C3.L3`, mtime 2026-09-19) emits:

```
ffmpeg -hide_banner -loglevel info -nostdin -vaapi_device <render node>
  -f x11grab -framerate 60 -window_id <id> -i <display>
  -vf scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,
      pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload
  -an -c:v h264_vaapi -profile:v high -b:v 7000k -maxrate 7000k -bufsize 7000k
  -g 15 -bf 0 -payload_type 96 -f rtp rtp://127.0.0.1:48110?pkt_size=1200
```

with `BFRAMES = PROFILE.bframes = 0`
(`native_stream_profiles.py::NATIVE_GAME_720P60_REFERENCE`). Every session
header in `native_video_alpha.log` prints `GOP=15, BF=0`. Nothing else on the
command line touches reordering (`-rc_mode`, `-low_power`, `-async_depth`,
`-sei`, `-coder` all at defaults).

Toolchain on the host, from the log headers and the RetroArch session log:
FFmpeg with Lavf 61.7.103 / Lavc 61.19.101 (= FFmpeg 7.1), `h264_vaapi` on
an AMD Ryzen 5 PRO 4650G (Renoir, VCN 2.x), Mesa 25.0.7 `radeonsi`, kernel
6.12 (Debian 13). No `[h264_vaapi @ ...]` warning of any kind appears in any
of the 160 session logs at `-loglevel info`.

FFmpeg 7.1's SPS for `h264_vaapi` is built in
`libavcodec/hw_base_encode_h264.c` (verified against the n7.1 source):

```
sps->vui_parameters_present_flag = 1;
sps->vui.timing_info_present_flag = 1;
sps->vui.bitstream_restriction_flag    = 1;
sps->vui.motion_vectors_over_pic_boundaries_flag = 1;
sps->vui.log2_max_mv_length_horizontal = 15;
sps->vui.log2_max_mv_length_vertical   = 15;
sps->vui.max_num_reorder_frames        = base_ctx->max_b_depth;
sps->vui.max_dec_frame_buffering       = base_ctx->max_b_depth + 1;
```

With `-bf 0`, `max_b_depth` is 0, so the SPS FFmpeg constructs carries
**`bitstream_restriction_flag = 1`, `max_num_reorder_frames = 0`,
`max_dec_frame_buffering = 1`** — exactly the explicit "no reordering"
instruction the battery asks for. FFmpeg hands that SPS to the driver as a
packed sequence header when the driver advertises
`VA_ENC_PACKED_HEADER_SEQUENCE`.

**Not verified here:** whether Mesa 25.0.7 `radeonsi` emits that packed SPS
verbatim or writes its own SPS (and with what VUI) into the stream. That is
precisely the question the live capture answers, and the Mesa source could
not be retrieved from this session.

Static verdict: **B-frames — none, by explicit `-bf 0`, confirmed in every
session header. VUI — FFmpeg-side intent is correct and explicit; on-wire
content unmeasured.**

### INDETERMINATE — on-wire frame types and SPS VUI

Reason: requires the encoder to run on the host; no host shell in this
session. No `.h264`, `.pcap` or SDP-plus-payload sample exists anywhere in
the repository, `logs/` or `archive/` (searched: 685 log entries, 2,000+
archive entries); the SPS bytes the receiver captures are not written to
any report. For the next session with a shell — the same command the
backend runs, to a file, no session and no client needed (this is the
`privyhub_linux_baseline_19` procedure that already ran on 2026-09-15):

```
WIN=$(xdotool search --name 'RetroArch' | head -1); \
ffmpeg -hide_banner -nostdin -vaapi_device /dev/dri/renderD128 \
  -f x11grab -framerate 60 -window_id "$WIN" -i :0.0 -t 10 \
  -vf 'scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload' \
  -an -c:v h264_vaapi -profile:v high -b:v 7000k -maxrate 7000k -bufsize 7000k -g 15 -bf 0 \
  -f h264 logs/games/a1_sample.h264
ffprobe -v error -select_streams v -show_entries frame=pict_type -of csv=p=0 logs/games/a1_sample.h264 | sort | uniq -c
ffmpeg -v info -i logs/games/a1_sample.h264 -c copy -bsf:v trace_headers -f null - 2>&1 \
  | grep -E 'bitstream_restriction_flag|max_num_reorder_frames|max_dec_frame_buffering|num_ref_frames|vui_parameters_present' | sort | uniq -c
```

`trace_headers` is an FFmpeg-internal bitstream filter; nothing needs
installing. If `pict_type` shows any `B`, or `bitstream_restriction_flag` is
0, or `max_num_reorder_frames` > 0, A1's hypothesis is confirmed and the fix
is host-side. If the output matches the FFmpeg-side expectation above, the
Realtek decoder is ignoring a correct VUI and the client-side low-latency
request (`C3.L2c`) is the only remaining lever on this decoder.

Why this still matters after A2: the slow events show the decoder holding
**2-3 frames** while it waits, and each 300 ms+ stall equals the arrival gap
plus one frame held inside the codec until the next input. A decoder that
honored `max_num_reorder_frames = 0` would release each frame without
waiting for its successor. Which side is at fault is decided by the
on-wire SPS.

---

## A4 — Wireless topology

### Recorded from measured evidence on disk

From `D_LINUX_ONN_STREAM_DIAGNOSIS_2026-09-15.md` (D080 Opal radio mapping,
measured on the router) and `logs/games/linux_wifi_egress_probe.txt`
(measured on the host):

- Host egress on 2026-09-15: a **USB Wi-Fi adapter, Realtek RTL8822BU,
  driver `rtw_8822bu`, USB 3 (5 Gb/s)**; `iw` unavailable on the host at the
  time, so power-save state was not readable; the host reported two
  non-loopback links up.
- The Opal had the **Linux host on one radio (`wlan0`) and the onn on the
  other (`wlan1`)**. Both endpoints wireless, bridged through the Opal.
- The kernel log on the host repeatedly recorded `firmware failed to leave
  lps state` for the RTL8822BU, and UDP `SndbufErrors` rose by thousands
  during streaming (host-side send failures into the wireless driver).

Topology as of 2026-09-15, by role: **two wireless hops — host radio ->
Opal -> onn radio**. Production intent (stated in the battery): host wired
to the Opal, onn wireless, one hop.

### INDETERMINATE — association as of this run

Reason: reading the current association needs `iw dev` / `nmcli` on the
host, and the companion records nothing about the link. Nothing on disk
after 2026-09-15 states the host's link type. Loss/min moved from 392 (09-16)
to 31 (09-18) to 60 (09-20) with no transport code change, which is
consistent with an environment that changed, but does not say how.

### The per-session field, as proposed

Record at session start, in the companion's decoder-session ingestion
(`companion/games/decoder_session_log.py`), a `host_link` block derived
from the host's default-route interface:

```
"host_link": {"kind": "wireless"|"wired", "driver": "<driver name>",
              "wireless_hops": 2|1, "recorded_by": "companion"}
```

`kind` from the presence of `/sys/class/net/<iface>/wireless`; `driver` from
`/sys/class/net/<iface>/device/driver`; `wireless_hops` = 1 + (1 if the onn
is wireless, always true today). No address, SSID, BSSID or MAC. This is a
Group C code change and is not made here.

---

## What Group A changes about the plan

Raw findings, in the order they bear on `BASELINE_STREAM_HEALTH.md`:

1. **Step 1 is chasing a cause the data excludes.** The tail regression was
   an artifact of a 21-session window; on 128 sessions the pre-flatten
   worst stall is 2,035 ms, and every stall over 1,000 ms in any epoch
   coincides with an outage-class sequence jump and an IDR wait. Reverting
   `C3.L2b` will not move the tail. The `C3.L2b` retention defect (worst
   ordinary-play event evicted) is real and separate.
2. **The loss column is undercounted 2-3x** because resync jumps are not
   counted as loss. Fix the counter (or read `stream_discontinuities`) before
   any transport number is compared against the target.
3. **The decoder is not running deep.** In-flight is 2-3 during stalls; the
   11-13 figure is a transient maximum. The chronic latency is 20-60 ms
   receive-to-output on 66 % of frames, and the fps deficit is mostly the
   client's own 60 ms stale threshold acting on that. `C3.L2c` remains the
   demonstrated lever on the latency; A1's live half decides whether the
   bitstream is asking for the hold.
4. **Audio underruns are a per-session burst plus ~17/min steady state**,
   co-varying with decode pressure, not with loss.
5. **The host emits 60.00 fps continuously**; unique-frame content is the
   one host-side cadence question still open, and it is a 30 s capture.
6. **Two wireless hops** as of the last measurement; nothing since records
   the link.

Suggested re-sequencing, for the next session to decide rather than this
record: run A1-live and A3-live first (one host shell session, ~2 minutes,
no client); fix the loss counter; then B1 (host-local decode) and B2
(alternate AP), which the outage-class jumps now make the primary question.

## Files written by this run

- this record;
- `evidence/group_a_2026-09-20/a2_rescore_decoder_sessions.py`,
  `a2_rescore_result.json`, `a2_session_table.csv`;
- `evidence/group_a_2026-09-20/a3_encoder_cadence_from_log.py`,
  `a3_encoder_cadence_from_native_video_alpha.json`;
- `investigations/SEAMLESS_LOCAL_PLAY_TEST_BATTERY.md` (installed with Group
  A status);
- by the live pass: `logs/games/a1_sample.h264`,
  `logs/games/a3_grab_framemd5.txt`,
  `evidence/group_a_2026-09-20/a1_first_sps_pps_sei_trace.txt`,
  `a1_a3_live_summarize.py`, `a1_a3_live_summary.json`; source change to
  `RtpH264Receiver.kt` / `NativeStreamActivity.kt` (loss counter) recorded
  in `patches/D-BASE-R1_GROUP_A_LIVE_AND_RESYNC_LOSS_COUNTER.md`;
- `CURRENT.md`, `2026-09-20.md`, `handoffs/CURRENT_HANDOFF.md`,
  `investigations/BASELINE_STREAM_HEALTH.md`, `docs/KNOWN_ISSUES.md`,
  `MEMORY.md` — updated as listed in `2026-09-20.md`.

No source, tool or probe file under `companion/`, `tools/` or `PrivyHub/`
was touched.

## Privacy

No network addresses, MACs, SSIDs, ADB endpoints or device identifiers
appear in this record or in the retained data files. "Link type" means
wired versus wireless; "hops" counts radios by role.

---

## Live half — run 2026-09-20 (host shell, later the same day)

Run conditions: a host shell was available; **no client, no companion.**
RetroArch 1.22.2 (the managed nightly AppImage) was launched directly with
the last managed session config
(`data/games/retroarch/config/privyhub-session.cfg`), Beetle PSX HW
0.9.44.1, content Tekken 3 (USA); the window came up at 879x720, the same
size the companion's managed launch produces, and was located with
`xdotool search --onlyvisible --name RetroArch`. The pointer was moved off
the window before each capture. RetroArch was stopped after the captures;
no ffmpeg or RetroArch process was left running. Host wall time about four
minutes including boot and the wait for attract mode.

Files: `logs/games/a1_sample.h264` (8,571,494 bytes, SHA-256
`2a3a64cd350c5e1bfb6ebd456a6fb9088d0e929b6085bcd42655efb6b2317a34`),
`logs/games/a3_grab_framemd5.txt` (1,800 rows),
`group_a_2026-09-20/a1_first_sps_pps_sei_trace.txt` (the first SPS, PPS
and SEI of the sample, from `trace_headers`),
`group_a_2026-09-20/a1_a3_live_summary.json`, produced by
`group_a_2026-09-20/a1_a3_live_summarize.py` (re-runnable against the two
`logs/games/` files plus a `trace_headers` log).

### A1-live — on-wire frame types and SPS VUI. COMPLETE.

Command: exactly the one recorded under A1 above (10 s, production filter
chain and encoder arguments, `-f h264` to file). The encoder ran at 60 fps,
speed 1.0x, `dup=2 drop=0`, 6.86 Mbit/s average.

Measured, `ffprobe` `pict_type` over 600 frames: **I 40, P 560, B 0.**
Pattern `IPPPPPPPPPPPPPPI...`, period 15 = `-g 15`. Every I is an IDR
(`nal_unit_type` 5, 40 of them); `has_b_frames = 0`.

Measured, `trace_headers` (41 SPS in the file, one per IDR plus the stream
header, all identical):

| field | on the wire | FFmpeg-side expectation (static audit) |
| --- | ---: | ---: |
| `profile_idc` / `level_idc` | 100 / 32 | High / auto |
| `pic_order_cnt_type` | 2 | — |
| `max_num_ref_frames` | 1 | — |
| `vui_parameters_present_flag` | 1 | 1 |
| `bitstream_restriction_flag` | **1** | 1 |
| `max_num_reorder_frames` | **0** | 0 |
| `max_dec_frame_buffering` | **1** | 1 |
| `num_units_in_tick` / `time_scale` / `fixed_frame_rate_flag` | 1 / 120 / 1 | — |
| `nal_hrd_parameters_present_flag` / `low_delay_hrd_flag` | 1 / 0 | — |

SEI: a buffering-period SEI (payload 0) on every IDR with
`initial_cpb_removal_delay` 67,500 (90 kHz units = 750 ms, three quarters
of the 1 s CPB that `-bufsize 7000k` declares at 7000 kbps — bit-buffer
arrival timing, not picture output timing); a picture-timing SEI (payload 1)
on every frame with **`dpb_output_delay = 0` on all 560 non-IDR frames**.
`pic_order_cnt_type` 2 additionally fixes output order equal to decode
order by construction.

Verdict: **`radeonsi` puts FFmpeg's packed SPS on the wire verbatim. The
bitstream carries no B-frames, declares zero reorder frames, a one-frame
DPB and zero output delay on every picture.** Nothing in the stream asks
the decoder to hold a frame. A1's hypothesis (the bitstream forces deep
buffering) is **falsified**. Per the reading pre-stated in the
INDETERMINATE section: the Realtek decoder is ignoring a correct VUI, and
the client-side low-latency request (`C3.L2c`) is the only remaining lever
on this decoder. The fix, if any, is client-side.

Noted, not chased: the 750 ms `initial_cpb_removal_delay` is what a strictly
HRD-scheduled decoder would wait before removing the first access unit from
its bit buffer. MediaCodec decoders are not HRD-scheduled, and `C3.L2c`
reached 95.5 % of frames under 20 ms on this same stream, so it is not the
mechanism of the 20-60 ms steady state. `-bufsize` is the only stream-side
knob that changes it.

### A3-live — unique-frame count and PTS deltas at the grab. COMPLETE.

Content: the Tekken 3 attract-mode demo fight (in-engine, 60 fps native),
confirmed by single-frame grabs before and after the capture; the demo
ended and the game returned to the static title screen during the final
~3 s. Command exactly the one recorded under A3 above (30 s,
`-framerate 60`, `framemd5`, lossless, 879x720 raw).

Measured, 1,800 frames, `tb 1/60`:

- PTS delta: **1 tick on all 1,799 intervals** (min 1, max 1, mean 1.000).
  No missed and no doubled grab slot in 30 s.
- Duplicate consecutive hashes: **7 in the first 27 s** (1,620 frames,
  99.57 % unique) at frames 361, 894, 900, 1,428, 1,434, 1,437, 1,439; 133
  in the last 3 s while the game faded to the static title screen
  (per-second unique counts 28, 18, 2). During motion the per-second unique
  count was 60 in 24 of 27 seconds, 59 in two, and 56 in the one second
  (frames 1,380-1,439) that holds the 1,428-1,439 cluster — re-derived from
  the hash file by the cloud session, correcting the live pass's "60 in 25".
- The 361 -> 894 -> 1,428 spacing (~533 frames, 8.9 s) is the beat between
  the core's 59.94 fps and the 60 Hz grab; the 894/900 and 1,428-1,439
  clusters coincide with scene cuts in the demo. A repeat every ~9-17 s is
  what a 59.94 fps source sampled at 60 Hz must show.

Verdict: **x11grab delivers 60 grabs per second at exact 1/60 cadence, and
~99.6 % of them are distinct frames of a 60 fps source.** The host is not
the reason the client renders 55.5 fps. A3's hypothesis (capture
duplicating or uneven) is **falsified**.

### A4 — host side of the link, measured 2026-09-20

`ip -br link` on the host: `lo`, `eno1` (UP), nothing else; no
`/sys/class/net/*/wireless` entry exists; the default route is via `eno1`,
driver `r8169` (onboard Ethernet). **The host is wired as of this run**;
the USB RTL8822BU radio of 2026-09-15 is no longer present. The onn's
association (which Opal radio) needs ADB and remains INDETERMINATE. By role
the path is now host wired -> Opal -> onn wireless: **one wireless hop, the
production topology.** Sessions taken since the host was wired cannot be
separated from earlier ones in the corpus because nothing records the link;
the `host_link` field specified above is still the fix. No addresses
recorded.

### `lost_packets` counter — fixed in source (A2.2 defect)

`RtpH264Receiver.beginStreamResync` now adds `jumpPackets` to `lostPackets`
and to a new `lostPacketsInResyncs` counter, serialized as
`video.lost_packets_in_resyncs` in both the status payload and the session
report. `ssrc_change` resyncs carry jump 0 and are unaffected. Reading
rule: reports **without** the field — corrected loss = `lost_packets` +
sum of `stream_discontinuities[].jump_packets`; reports **with** it —
`lost_packets` already includes the jumps, and `lost_packets_in_resyncs`
recovers the pre-fix number. `a2_rescore_decoder_sessions.py` now handles
both. Build and runtime status: `patches/D-BASE-R1_GROUP_A_LIVE_AND_RESYNC_LOSS_COUNTER.md`.

## What the live half changes about the plan

Both host-side root-cause candidates are closed. The bitstream is correct
and explicit; the capture is 60 fps clean; the host link is now the
production one. Every remaining lever on the target table is on the client
(receive-to-output latency, the 60 ms stale policy, resync/IDR acceptance)
or on the wireless hop to the onn (outage-class sequence jumps). The
re-sequenced plan is in `investigations/BASELINE_STREAM_HEALTH.md`.

## A4 correction (2026-09-21, from the user)

The host-side A4 measurement — `eno1`, `r8169`, no radio — is correct, but
the inference drawn from it ("wired to the Opal, one wireless hop by role,
the production topology") is not. The user states the Ethernet cable
currently runs to the **Windows PC**, a temporary arrangement for
debugging; the path to the onn is host -> Windows PC -> Opal -> onn.
Production intent remains host wired directly into the Opal. Consequences:
every session in the corpus was measured with the Windows PC forwarding
the stream — the same machine whose UDP burst/gap/duplication pathology
`D_LINUX_ONN_STREAM_DIAGNOSIS_2026-09-15.md` and the Windows-era records
measured — and the "loss is bursty, in outage-class bursts, matching the
deferred UDP pathology signature" verdict in A2.2 now has an obvious
candidate cause on the path. Moving the host's cable to the Opal is both
the production topology and the first Group B isolation test.
