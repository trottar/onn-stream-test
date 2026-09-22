---
memory_schema: 1
as_of: 2026-09-21
status: TASK HANDOFF — D-BASE-P5, which queue: frame size, the onn's socket drops and the loss series on one clock; diagnostic counters only; authorized by the user 2026-09-21 for an unattended run
---

# D-BASE-P5 task handoff — which queue drops the burst

**Where this stands (from `O1`, 2026-09-21):** the loss is locked to stream position — two 20-minute sessions of the same attract loop lose in the same minutes at Pearson 0.96-0.97 — and it selects the bursty stream over the paced one (video loses 3-7x the rate audio does over the same radio in the same second). The air, the Opal's radio and the Opal's forwarding counters are flat through it. The mechanism is a per-frame micro-burst meeting a queue. Two queues are still live: the AP's per-station wireless queue and the onn's own receive path (socket buffer and receive thread). This run separates them. Read first: docs/memory/evidence/O1_OPAL_AIR_VIEW_2026-09-21.md (§1, §2, §6), D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md, D_BASE_P3_SENDER_PACING_2026-09-21.md (the 8 ms budget clamped exactly the large frames), docs/memory/TOOLS.md, companion/native_fec_relay.py (`_emit_group_locked` sees each frame's packets keyed by RTP timestamp), PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt (the socket, its 2 MiB request, the receive loop and what else runs on that thread).

**Three instruments, all diagnostic, on one clock.**

1. **Frame size, from the relay.** In `native_fec_relay.py`, per RTP timestamp, count the packets of each frame as it completes (the marker packet ends it). Keep, per 1-second bucket of relay time: frame count, mean packets per frame, max packets per frame, the number of frames above 40 packets and above 80, and the largest frame's packet count with its wall-clock time. Expose the bucket series through `relay.status()` as a bounded ring (last 1,800 s) and write it, per session, to `logs/games/native_frame_sizes.jsonl` (one line per second, rotated like the heartbeat log, covered by retention). This is counting only; the forwarding path is untouched and the pacing knob stays at 0.

2. **The onn's socket drops.** `/proc/net/udp` on the onn lists every UDP socket with a `drops` column (the last field: datagrams dropped for a full receive buffer). Over adb, every 2 s during the session, read the rows for the stream's local ports (48100 video, 48101 audio) and record `drops`, `rx_queue`, and the wall time — host-side script, no client change. First confirm the file is readable by the shell user on this device and that the two ports appear while streaming; if `/proc/net/udp` is denied, try `adb shell ss -uan` / `netstat -uan` and say which worked. Also read once, at session start, the socket's granted receive buffer if any of those tools show it, and `adb shell cat /proc/sys/net/core/rmem_max` again for the record.

3. **The loss series**, from the `D-BASE-R5` heartbeat counters: `lost_packets` and `forward_gap_events` per 2 s tick, aligned to host time by the companion's `received_at_utc`.

**Sessions.** Two 20-minute attract-mode sessions of the PS1 reference title, zero input, per TOOLS.md, BACK to end, teardown between, all three instruments running through each. The content-lock is the control: the two sessions' per-minute loss should again agree at Pearson > 0.9, and the per-minute max-frame-size series should agree with itself across sessions at a similar level — report both, because if frame size does not reproduce across sessions while loss does, the frame-size account is wrong.

**Analysis, on 10 s windows (n ≈ 240) and per minute (n = 40):** loss and forward-gap events against max packets-per-frame, frames above 40 and above 80, mean packets per frame, and the onn's `drops` delta and peak `rx_queue`. Spearman for each; the top-quartile loss windows listed with their frame-size and socket readings; and for every window where the onn's `drops` counter advanced, the loss in that window.

**Pre-registered reading, one of three:**

- **The onn's receive path is the queue** if the onn's `drops` delta accounts for most of the loss (sum of drops ≥ 70 % of `lost_packets` over the session, and the two track at |rho| ≥ 0.6 on 10 s windows). Then the fix is on the client: a larger effective receive buffer, a receive thread that does nothing but `recv`, or both — say which the code suggests, do not implement.
- **The AP's wireless queue is the queue** if loss tracks max frame size (|rho| ≥ 0.5) while the onn's `drops` stay at or near zero (< 10 % of loss). Then the fix is upstream: cap the largest frames (encoder VBV/`bufsize` and `-maxrate`, a smaller IDR spike, or a pacing budget that actually spreads a 60-80-packet frame), and the record must give the frame-size distribution the fix has to flatten — p50 / p90 / p99 / max packets per frame.
- **Neither** if loss tracks neither frame size nor socket drops; then say what does distinguish the loss windows in the three series, and stop.

State plainly that choosing the fix is the user's decision, with the latency or bitrate cost each carries.

Build the client only if a counter turns out to need it (it should not); compile the Python, `git diff --check`, restart the companion (D-068) with 8765 checked free. Record raw numbers first in docs/memory/evidence/D_BASE_P5_WHICH_QUEUE_<date>.md with the frame-size series, socket samples, heartbeat slices and reports under evidence/d_base_p5_<date>/ and SHA-256s; classify CHARACTERIZED / INDETERMINATE. Patch record for the relay counters in docs/memory/patches/ and PATCH_INDEX.md; update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy — trim), MEMORY.md (the content-lock and the mechanism, as established), handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, BASELINE_STREAM_HEALTH.md Step 3, KNOWN_ISSUES.md (the UDP burst pathology entry: rewrite it around what is now known), TOOLS.md (the frame-size log and the socket read). Teardown per TOOLS.md. Never retry a failing action more than twice. No addresses or device identifiers in any memory or evidence file.
