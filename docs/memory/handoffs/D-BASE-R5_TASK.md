---
memory_schema: 1
as_of: 2026-09-21
status: TASK HANDOFF — D-BASE-R5, loss counters in the heartbeat; diagnostic only; authorized by the user 2026-09-21 for an unattended run
---

# D-BASE-R5 task handoff — put the receiver's loss counters in the heartbeat

**Why (from `D-BASE-P4`):** loss on this link is episodic — a 20-minute session lost at 105/min with 14.9-packet bursts while six 2-minute sessions read 1.4-24.6/min — and there is no per-minute loss series because the client's counters are only visible in the end-of-session report. P4 tried to derive one from host-sent minus client-received and found the noise 29x the signal. The receiver already keeps the counters; this task only puts them in the 2 s heartbeat.

Read first: docs/memory/evidence/D_BASE_P4_AIR_TELEMETRY_2026-09-21.md ("Why there is no per-minute loss series"), D_BASE_R2_STALL_VISIBILITY_2026-09-20.md (the heartbeat's fields and cost), docs/memory/TOOLS.md, PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt (heartbeat assembly), RtpH264Receiver.kt (the counters), companion/games/native_stream_heartbeat.py.

**The change, client only, heartbeat payload only.** Add to every heartbeat the receiver's cumulative `lost_packets`, `lost_packets_in_resyncs`, `forward_gap_events`, `max_forward_gap_packets`, `stream_resyncs` (sequence + SSRC), `fec_recovered_packets`, `fec_unrecoverable_groups`, and `rx_packets` if not already there — cumulative session values, read from the same counters the report reads, so a per-tick delta is exact. No new sampling, no new threads, no change to what the receiver counts. The companion's heartbeat writer passes them through unchanged (add the keys to whatever schema/validation it applies; bump the heartbeat schema string). Add `loss_per_min_recent` (last 60 s, from the same counters) to `native-stream-status` so a live session can be watched. Nothing else changes.

Build, install per TOOLS.md, restart the companion (D-068) with 8765 checked free, `git diff --check`.

**Validation.** One 20-minute attract-mode session of the PS1 reference title, zero input, per TOOLS.md, BACK to end. Checks: every heartbeat carries the new fields; the last heartbeat's cumulative values equal the session report's (exact match, or say why not); the per-minute loss series from heartbeat deltas sums to the report's `lost_packets`; the series is presented as 20 numbers with the burst minutes named, and beside it the per-minute RSSI from a `WifiScoreReport` harvest (P4's method, post-session, no cost to the run). Report the heartbeat's payload size before and after and the client's `spike_20_ms`/min against P4's range to show the heartbeat did not get more expensive in any way that shows.

Record raw numbers first in docs/memory/evidence/D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_<date>.md with the report, the heartbeat file and the harvest under evidence/d_base_r5_<date>/ and SHA-256s; RUNTIME VALIDATED only if every check passes. Patch record in docs/memory/patches/ and PATCH_INDEX.md; update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy — trim), MEMORY.md, handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, TOOLS.md (how to get a per-minute loss series from the heartbeat log), KNOWN_ISSUES.md. Teardown per TOOLS.md. Never retry a failing action more than twice. No addresses or device identifiers in any memory or evidence file.
