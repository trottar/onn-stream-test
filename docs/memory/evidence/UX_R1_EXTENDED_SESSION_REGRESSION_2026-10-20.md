---
memory_schema: 1
as_of: 2026-10-20
status: UX-R1 READ (session A, read-only) — the user's evening of 2026-10-19/20 is in the files and the files agree with the user. The play was 04:19-05:22Z (00:19-01:22 EDT), five games, 20 client sessions. The first 5 minutes match the week's clean windows; after them, underruns rise ~12x, concealed underruns ~9x and post-FEC loss ~7x. The worst is in the SNES games, which were also the last 30 minutes. Loss does NOT follow the frame-size tail tonight (the cap held). The host, the grabs and the ladder read clean. Single losses step up ~5x at 04:56Z and stay up through the game change; three loss bursts hit both directions at once and end in two silence pauses and an encoder restart. The files cannot say whether the link or the onn's receive side caused it, and the onn was cold-booted afterwards, so its end state is gone. First-ranked test: one instrumented evening (written, not run). Nothing changed, restarted or adopted; nothing committed
---

# UX-R1 — the extended session that went bad: the read

Task: `handoffs/UX-R1_EXTENDED_SESSION_REGRESSION_READ_TASK.md`. Files: `ux_r1_2026-10-20/`.

**The user's report, verbatim (2026-10-20):**
> "I just played for an extended play session and it was horrible. It is much worse than it was weeks ago when I last did one"
> 1. "All the above. Every issue from audio to visual to gameplay. Multiple games all played terrible, especially later on with SNES"
> 2. "Every game got worse as time went on"
> 3. "besides the first 5 minutes, it was not good to terrible"
> 4. (when the earlier good session was) "Earlier" — before the October adoptions.

## The answer, plainly

- **The files agree with the user.** The first 5 minutes read like the week's clean 10-minute windows. Everything
  after reads several times worse, and it gets worse later in the evening.
- **Ruled out by the files:**
  - the host (CPU, load, temperatures, memory all flat);
  - the guide grabs (none ran in the span);
  - the ladder (held 7000; it did not cause the damage and did not relieve it);
  - the frame-size tail (the 90 KB cap held; loss did not follow it).
- **What the files show:** the receive path got worse during the evening.
  - Single losses that FEC repaired stepped up ~5x at 04:56Z and stayed up across a game change.
  - Three bursts hit video, audio and the onn's control uplink in the same minutes.
  - The audio failures track the loss (ρ 0.83).
- **What the files cannot say:** whether the link or the onn's receive side did it.
  - Neither end was read during the evening: the link watch is stopped, there was no Opal read, and the onn's
    `udp6` drops were not read.
  - The onn was cold-booted afterwards (uptime now 4 h 05 m), so its state at the end of the evening is lost.
- **First-ranked test (§3, H1):** one instrumented evening with both ends read every 5 minutes. Written, not run.

## 0. Preserved, and the state now

**Copies** (`session/`, 70 files; `ux_r1_preserve.py`, copied at `session/copied_at.txt`). Nothing was moved. Every
copy went through the project redactor plus a client-id / token mask.
- Every ladder log: the current one and `stream_log_archive/adaptive_bitrate_shadow.jsonl.1-3`.
- The frame-size log and its three archives.
- The heartbeat, recovery, control-gap, host-sampler and audio-encoder logs.
- All 21 decoder health reports with mtime in the span (20 are the evening's; one is CL-B7's last).
- The 22 audio-timing records and the six game logs.
- The encoder log's blocks that start in the span (`native_video_alpha.span.log`).
- The audit rows and HTTP log rows for the span.
- The companion journal from 17:48Z (`journal_privyhub_companion.span.txt`).
- The EPG grabber logs to the same journal; it has no lines in the span (see §1).
- `wan_sessions.jsonl` was last written 10-19 13:58Z, before the span; WAN telemetry is not adopted.

**Host, now** (`state_now/host_state_now.txt`, 18:27Z):
- Up 27 days; load 0.27; 11.5 GB available; swap on with 681 MB used (system-wide); disk 34 %.
- The companion has run since 17:47:59Z (CL-B7's end restart): RSS 77 MB (HWM 77 MB), 2 threads, 5 fds, VmSwap 0.
  The unit's cgroup holds 129 MB, with a peak of 319.5 MB.
- No RetroArch, no encoder, no grab running. `active (running)`, not restarted.
- Journal since 17:48Z: 2,018 lines, **0 at warning or worse**, 0 "error" / "warn" / "traceback".

**The onn, now** (`state_now/onn_*.txt|jsonl`). adb was connected by hand on the pinned port; the endpoint was never
printed.
- **Uptime 4 h 05 m: cold-booted ~14:22Z today, after the session.** Boot reason `cold`.
- **The state at the session's end is therefore gone.** At the evening's start the onn had been up ~11 h 27 m, since
  CL-B7's power-cycle (~16:52Z by CL-B7's uptime reads), unless it was power-cycled again in between. The files cannot
  say; the user can.
- PrivyHub is not running. Busy 6 %; thermal status 0; cpu-thermal 41.7-42.0 °C.
- MemAvailable 808 MB of 1.93 GB; swap 407 MB used of 941 MB (at idle, 4 h after boot).
- `getprop debug.privyhub.opus_decode` is empty, as expected.
- `cl_b7_onn_threads.py state_now` returned "PrivyHub not running".

**Also read:**
- `--check`: ok on eight, adb true, **APK CONFIRMED** (`93d29b4a…`), no RetroArch / encoder (`state_now/check_now.json`).
- HEAD `d3a8ee3`; `git status` in `state_now/git_status.txt` and `logs/ux_r1_git_status.txt`.

## 1. The timeline

`ux_r1_timeline.py` reads the copies only. Its output is `timeline.txt` / `timeline.json`.

**The evening.** The client opened at 04:12:46Z (`token_issued`, `sig_v` 3 / opus, `routing_evidence` **lan**). Nothing
streamed between 17:48Z and 04:19Z. Five games:

| start (UTC) | system / core | title | client sessions | minutes |
| --- | --- | --- | ---: | ---: |
| 04:19:15 | PS1 / Beetle PSX HW | Disney's The Emperor's New Groove | **16** | 16.0 |
| 04:38:53 | PS1 / Beetle PSX HW | King's Field II | 1 | 11.4 |
| 04:51:03 | **SNES / snes9x** | SimCity | 1 | 3.5 |
| 04:55:13 | **SNES / snes9x** | Super Mario RPG | 1 | 15.9 |
| 05:11:44 | **SNES / snes9x** | Zelda: A Link to the Past | 1 | 10.2 |

- **The 16 short sessions in Emperor's New Groove are the user's Load States.** The game log has 17 "Loading state"
  lines.
  - Each load ended the client session (`session_ended`, state PLAYING) and started a new one 6-21 s later.
  - The host saw a 6-17-s control gap each time; these are the "ctrl > 1 s" of 04:21-04:37.
  - That is a gameplay cost on every load. It runs from the first minutes; it does not grow with time.
- **Recovery rows:** 05:10:03 `client_output_silence` → `encoder_restart` → resumed 5.2 s; 05:21:06
  `client_output_silence` → resumed 6.3 s (no restart). No `gave_up_saved`, no desync otherwise.
- **The ladder:** `live`, **7000 throughout**. One acted step, 7000 → 6000 `capacity_mild` at 05:11:01, 10 s before a
  session ended; it reset to 7000 at the next start. 502 `state` rows, all at 7000.
- **The grabs:** **no** `/plugins/epg/refresh` or grabber line in the span. Grabs did not run during the evening.
- **`wan` class:** not available. WAN telemetry is built and not adopted.

**Per minute** (heartbeat deltas; the full table is in `timeline.txt`). Rendered fps reads 59.5-60.0 in clean minutes.
Steady-state minutes:
- **04:19-04:55:** post-FEC loss 0-53 / min, FEC-recovered 4-18, concealed underruns 15-134.
- **From 04:56:** FEC-recovered 15-101 (mostly 20-40), concealed 75-505.
- **Three bursts, in both directions at once:**

| minute | post-FEC loss | FEC rec | unrec groups | underruns | concealed | audio arrival gap max | host ctrl gaps > 1 s (max) | fps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 05:06 | 489 | 62 | 42 | 133 | 1,940 | 543 ms | 3 (1,296 ms) | 57.2 |
| 05:10 | **5,398** | 78 | 65 | 305 | 2,338 | 843 ms | 3 (1,732 ms) | **47.0** |
| 05:20 | 279 | 70 | 26 | 91 | 1,317 | 831 ms | 2 (3,232 ms) | 58.1 |
| 05:21 | 899 | 101 | 63 | 326 | 2,612 | 1,287 ms | 1 (1,539 ms) | 55.7 |

The host's control gaps are the onn's uplink, about 70 packets/s. They fall silent in the same minutes the downlink
loses video and audio.

**The first 5 minutes against the rest** (heartbeat, per minute):

| | first 5 min (04:19-04:24) | after (04:24-05:22) |
| --- | ---: | ---: |
| rendered fps | 59.88 | 59.24 |
| post-FEC loss / min | **26.1** | **173.2** |
| FEC recovered / min | 5.7 | 23.2 |
| FEC unrecoverable groups / min | 5.45 | 9.67 |
| resyncs | 0 | 17 |
| underruns / min | **3.86** | **39.42** |
| concealed underruns / min | **37.3** | **327.8** |
| prolonged starvation / min | 4.5 | 27.2 |
| audio packets lost (net) / min | 0 | 1.18 |
| audio arrival gap max | 142 ms | 1,434 ms |
| wire kbit/s (frame-size log) | 6,267 | 6,700 |
| frames ≥ 40 packets / min | 116 | 232 |
| frames ≥ 80 packets | 0 | 0 |
| encoder / RetroArch CPU % | 48.4 / 34.3 | 32.1 / 19.6 |

**Per report**, with the decode queue and the spikes:
- The first three reports: underruns 3.2 / min; decode queue depth max 29, wait max 265 ms (all in the first 108 s;
  then 13-23 / 53-81 ms); output gap max 259 ms.
- The rest: 43.9 / min; depth max **64**, wait max **287 ms**; output gap max **4,923 ms**.
- Opus decode average is flat across the evening (3.1-3.7 ms, first to last); the decoder did not slow.
- Spikes ≥ 50 ms / min: 6-11 in the long sessions, not rising. Thermal status 0 in every report (zones unreadable).

**SNES against PS1** (all SNES minutes are the last 31; the comparison is confounded with time):

| | PS1 (26.9 min) | SNES (29.0 min) | of which SimCity (04:51-04:54) |
| --- | ---: | ---: | ---: |
| fps | 59.68 | 58.90 | 59.70 |
| post-FEC loss / min | 33.0 | **280.8** | 29.4 |
| FEC recovered / min | 8.2 | 34.5 | 8.3 |
| underruns / min | 41.7 (68.9 in ENG: a 1,062-underrun burst inside an 8-s load session) | 31.9 | 1.1 |
| concealed / min | 114.7 | **481.1** | 106.9 |
| loss per frame ≥ 40 packets | 0.15 | 1.23 | 0.12 |
| encoder CPU % | 39.8 | 27.5 | 26.8 |

**SimCity, the first SNES game, read clean.** The step came one minute into Super Mario RPG (04:56) and held into
Zelda. King's Field II (PS1, 04:39-04:50) had the **heaviest** frame-size tail of the evening (327 frames ≥ 40 / min)
and the **lowest** loss (22 / min).

**Does the loss follow the frame-size tail?** No (Spearman over 50 full minutes):

| pair | ρ |
| --- | ---: |
| post-FEC loss vs frames ≥ 40 | −0.134 |
| post-FEC loss vs max packets | 0.003 |
| FEC recovered vs frames ≥ 40 | −0.08 |
| post-FEC loss vs minute of the evening | **0.516** |
| concealed underruns vs minute of the evening | **0.684** |
| concealed underruns vs post-FEC loss | **0.826** |

MEMORY.md's transfer function (frame-size tail → loss; P5 / P6) does not explain tonight. The cap held (0 frames
≥ 80, max 77-79 packets every minute). The loss rose with time, and the audio followed the loss.

**The host over the evening:**
- Load 0.6-3.1.
- Encoder CPU 36-51 % (PS1) and 27-28 % (SNES).
- Host temperature 43-57.6 °C, the same plateau as D-BASE-S2.
- The stream processes held no swap.
- Wire ~7,000 kbit/s in full minutes.
- Nothing trends with the loss.

**The onn over the evening:** no reads were taken (the task assumed ~1 h of uptime at the start; it was ~11 h 27 m).
The 20 reports carry thermal status only, 0 throughout.

**Against the week's windows** (clean 10-minute PS1 windows, Opus unless noted, from their records):

| | CL-B5 B / L | G-A2 | CL-B6 1 | CL-B7 PCM / today / lean | **tonight, first 5 min** | **tonight, after** |
| --- | --- | --- | --- | --- | --- | --- |
| onn uptime | n/r | 5 sessions in | 7-17 min | 9-54 min | ~11.5 h | ~11.6-12.5 h |
| underruns / 10 min (session) | 11 / 13 | 78 | 22 | 16 / 25 / 12 | ~32 | ~440 |
| video loss / min (post-FEC) | 25.2 / 48.5 | 24.2 | 12.9 | 14.6 / 27.7 / 48.3 | 20.9 | 200.9 |
| decode queue depth / wait max (ms) | 19 / 185; 20 / 87 | 36 / 167 | 20 / 82 | —; 45 / 218; 15 / 80 | 29 / 265 | 64 / 287 |
| max output gap ms | 227 / 310 | 351 | 261 | 242 / 260 / 405 | 259 | 4,923 |
| ctrl gaps > 1 s in play | 0 / 1 | 2 | 0 | 1 / 0 / 0 | 0 | 9 in the SNES play (+ the load gaps) |
| rendered fps | 59.85 | 59.69 | 59.92 | 59.93 / 59.85 / 59.82 | 59.57 | 59.06 |

G4-S3 (off-site, 4000) had 34 underruns in the window, across three starts.

- **The day-level aggregates of 10-15..19 are not a baseline.** They include the G8 impairment cells, which inject
  loss. They are in `timeline.txt` for completeness and are not read here.

**Against the last extended session on record:** D-BASE-S2 (2026-09-21 05:51-08:51Z, 3.00 h) is the closest match.
It is not like for like: attract mode with zero input, PCM, and before every October adoption.
- Per-minute fps by 30-minute block: 59.528 / 59.714 / 59.619 / 59.710 / 58.779 / 56.828.
- **Flat for 150 minutes; then the link degraded in the last 30.** There were five natural desync pauses and one
  encoder restart during a 78-s outage.
- **The same shape as tonight, a late-session link failure.** Tonight it began at ~37 minutes instead of ~150.
- No user-played extended session before October is on record with these instruments. The user's "earlier" session
  has no files to compare.

## 2. What changed since the earlier session (dated; from CURRENT.md and the records; no judgement)

| date | change | kill switch (as recorded) |
| --- | --- | --- |
| 10-01 | `ADAPTIVE_BITRATE_MODE=live` (C3-L4-D1); also the PS1 source at 1920×1080 / 4x internal (C5-M4A) | delete `adaptive.conf` + `daemon-reload` + restart; the 4x revert is in `TOOLS.md` |
| 10-07 | `EPG_GUIDE_INDEX=cached` (E3-S6A) | delete `epg-index.conf` + `daemon-reload` + restart |
| 10-07 | `SNES_CORE=snes9x` (E3-A2) | delete `snes-core.conf` + `daemon-reload` + restart (bsnes back) |
| 10-09 | `RECOVERY_TRIGGER=v2` (E3-A3 / A3B) | delete `recovery.conf` + `daemon-reload` + restart |
| 10-15 | `SNES_CAPTURE_FIX=output_rate` (E4-S5D) | delete `snes-capture.conf` + `daemon-reload` + restart |
| 10-16 | `OVERLAY_PROVIDER=tailscale`, `SESSION_IDENTITY=v2` (G-A1); `identity_v2` on in the client | delete the drop-in(s) + `daemon-reload` + restart, and the name(s) out of `e1_suite.ADOPTED` |
| 10-19 | `AUDIO_CODEC=opus` (G-A2) | delete `audio-codec.conf` + `daemon-reload` + restart, and `AUDIO_CODEC` out of `e1_suite.ADOPTED` |
| 10-16..19 | APKs: CL-B2 / B3 (identity, hardened), CL-B4 / B5 (Opus decode, its own thread; `043891e1…`), **CL-B7 `93d29b4a…` (lean flag absent = CL-B5's drain)** | reinstall the predecessor APK |

- **The memory floor / swap:** E4-S3B (10-10) closed with a 1 G floor, swap off, as a measured row. **Swap is on
  now** (681 MB used). The record names no persistent host change in force.
- **The link watch is stopped** (E4-S4C). Nothing watched the link tonight.
- **The deferral flag is NOT adopted** (`PRIVYHUB_EPG_DEFER_WHILE_STREAMING`, E4-S4): grabs can still run during a
  stream. **Tonight none did.**
- **The Opal:** no hand change is named in CURRENT.md, MEMORY.md or KNOWN_ISSUES. It is read-only from this project.
- **The onn's own state:** ~11 h 27 m up at the first frame (from CL-B7's power-cycle, if not cycled since) and
  ~12 h 30 m at the last. **20 client sessions in 63 minutes.** CL-B6's watch item was underruns against the onn's
  session count and uptime.

## 3. Hypotheses, ranked by what §1 shows (each with its test; nothing run)

**H1 — the receive path degraded over the evening: the link, or the onn's receive side. The files rank this first;
they cannot split it.**
- *Points at it:*
  - FEC-recovered single losses stepped from ~5 to 20-40 / min at 04:56 and stayed through a game change.
  - Post-FEC loss went 26 → 173 / min; post-FEC loss rose with the minute of the evening (ρ 0.52).
  - Three bursts (05:06, 05:10, 05:20-21) hit the downlink and the onn's control uplink in the same minutes. Two
    ended in `client_output_silence`, one with an encoder restart.
  - Loss is not explained by the tail (ρ −0.13; cap held) or by the host (flat), and the wire rate is flat.
  - The audio follows the loss (ρ 0.83).
  - D-BASE-S2 failed the same way late in a session, before October.
- *Against it, or unknown:*
  - Nothing read either end during the evening.
  - MEMORY.md (P5, S3): the onn's UDP socket dropped 0 datagrams in 40 min and in 3 h. That favours the air, but it
    was not read tonight.
- *The test:* **one evening, the user playing the same games for ≥ 60 min, with both ends read every 5 minutes.**
  - The onn: `/proc/net/udp6` `drops` (P5's instrument), `cl_b6_onn_read.py`, `cl_b7_onn_threads.py`.
  - The Opal: per-station tx retries / signal / MCS, read-only (O1's read), or the link watch resumed for the evening.
  - The host clock beside the user's narration.
  - If `udp6` drops move with the loss step, it is the onn. If they stay 0 while the Opal's station counters move,
    it is the air.
  - Power-cycle the onn at the start (its uptime then becomes play time; this also tests H2).

**H2 — the onn's state with time and sessions (uptime ~11.5-12.5 h, 20 sessions, one app process).**
- *Points at it:*
  - CL-B6's precedent (G-A2's 78 after five sessions, against 22 on a fresh onn).
  - The decode queue reached depth 64 / wait 287 ms late, above anything on file (CL-B7: 45 / 218).
  - Concealed underruns rose with time (ρ 0.68).
  - The control uplink stalled in the bursts; a stalled onn would stall it too.
  - The onn was cold-booted afterwards. If the user did that because it felt bad, that is a datum.
- *Against it:*
  - The first 5 minutes were clean at ~11.5 h of uptime, so uptime alone does not do it.
  - The Opus decode average stayed flat (3.1-3.7 ms).
  - Spikes ≥ 50 ms did not rise; thermal status was 0 throughout.
- *The test:* the same instrumented evening as H1, after a power-cycle. If the step comes at the same play-minute
  with `udp6` drops or the PrivyHub thread CPU rising, it is the onn's state.

**H3 — SNES (snes9x since 10-07, `output_rate` since 10-15).**
- *Points at it:* the two worst games are SNES; SNES concealed 481 / min against PS1's 115; loss per large frame 1.23
  against 0.15.
- *Against it:* SimCity (SNES) was clean at 04:51-04:54; every SNES minute is also one of the last 31, so system and
  time are confounded.
- *The test:* one evening with the order reversed: SNES first for 30 min, then PS1. If SNES is clean first and PS1 bad
  late, it is time. If SNES is bad first, bisect with its kill switches (`snes-capture.conf`, then `snes-core.conf`),
  one per evening, the user playing.

**H4 — Opus (G-A2, adopted 10-19, the newest change).**
- *Points at it:*
  - The newest adoption, the same day.
  - It costs the onn ~0.31 core (CL-B7).
  - The decode queue grew late.
- *Against it:*
  - The concealment tracks arrival loss, not decode time; the decoder average is flat.
  - Four clean Opus windows this week (CL-B5 B / L, CL-B6 1, CL-B7 today / lean).
  - The PCM-era D-BASE-S2 failed late as well.
- *The test:* the kill switch for one evening (`audio-codec.conf` removed: PCM, ~+2.9 Mbit/s on the wire), the user
  playing, after H1's evening. A bisect step, not a first test.

**H5 — Load State restarts the stream (a gameplay cost, not a trend).**
- *Points at it:* 16 loads in 19 minutes, each ending the client session with 6-21 s to the next start.
- *Against it:* it explains no part of "worse as time went on"; it was there from the first minutes.
- *The test:* read whether a September game log / recovery log shows the same end-and-restart on a load (a read,
  not a run), then time one load on the current build. If it is new since October, it is its own item.

**Ruled out by the files:**
- **the host**: CPU, load, temperatures flat; companion 77 MB; no swap in the stream processes;
- **the grabs**: none ran;
- **the ladder**: held 7000 and neither caused nor relieved the bursts;
- **the frame-size tail**: the cap held, ρ −0.13.

The files do not read clean, so this is not an instrumentation-gap verdict. **But the files cannot tell link from
client.** That is why the first test is the user's evening with both ends instrumented.

## 4. Record

- This file.
- `ux_r1_2026-10-20/`:
  - `session/` (the copies) and `state_now/`;
  - `ux_r1_preserve.py`, `ux_r1_timeline.py`, `timeline.txt`, `timeline.json`;
  - `redact_check.txt`, `manifest.sha256`.
- `docs/KNOWN_ISSUES.md`: a new OPEN item at the top.
- `logs/ux_r1_git_status.txt`.
- `CURRENT.md` Next Action.

Constraints held:
- No sudo, no nft. The Opal was not touched. adb was used for state reads only.
- Nothing fetched, deleted or moved. No restart, no power-cycle, no run.
- No change outside `docs/` and `logs/`. Nothing adopted; nothing committed.
