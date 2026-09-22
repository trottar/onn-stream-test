---
memory_schema: 1
as_of: 2026-09-20
status: TASK HANDOFF — battery item C5, receiver resync and IDR-acceptance policy read; analysis only, no code change; authorized 2026-09-20 for an unattended run
---

# C5 task handoff — receiver resync and IDR-acceptance read

Analysis only. **No production code change, no build, no install.** Run only after `D-BASE-P1` is recorded in docs/memory/CURRENT.md (check first; stop and say so if it is not).

The question, from docs/memory/investigations/SEAMLESS_LOCAL_PLAY_TEST_BATTERY.md §C5: the receiver's resync path is untouched since `C3.L0`. `C3.L2a` and `C3.L3a` Part 1 measured ordinary sequence resyncs at **195-332 ms** against **18-65 ms** for actuator-driven IDRs. The GOP is 15 frames, so an IDR arrives within 250 ms of any point; a resync that waits 195-332 ms is therefore waiting for about one full GOP, which is the worst case, every time — or it is waiting for something other than the next IDR. Which?

Read first: docs/memory/CURRENT.md, the battery §C5, docs/memory/evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md, C3_L3A_P1_LADDER_TRANSITION_RUNTIME_2026-09-19.md, GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md (the resync / discontinuity numbers across the corpus), D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md, then the code: PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt (`beginStreamResync`, the discontinuity and IDR-wait logic, SPS/PPS handling), AvcLowLatencyDecoder.kt (what happens to the codec on resync — flush? reconfigure? nothing?), and the FU-A / NAL reassembly path. On the host: companion/native_stream.py and the encoder command (`-g 15`, `-bf 0`, whether SPS/PPS repeat on every IDR, `-x264-params`/VAAPI equivalents in force).

**Deliver, in docs/memory/investigations/C5_RESYNC_IDR_ACCEPTANCE_READ_<date>.md:**

1. **The resync path as it is**, step by step, from the first out-of-window sequence number to the first rendered frame after it: what is discarded, what the receiver waits for (an IDR? SPS+PPS then IDR? a marker? a full access unit?), whether the decoder is flushed or reconfigured, and where each of the 195-332 ms can go. Cite line numbers.
2. **Why an actuator IDR is accepted in 18-65 ms and an ordinary resync in 195-332 ms**, from the code. The actuator restart delivers fresh SPS/PPS + IDR immediately; an ordinary resync gets the next in-GOP IDR. Check specifically: (a) whether SPS/PPS are re-sent with every IDR by the encoder on this build — if not, an ordinary resync may be waiting for parameter sets that only come with the next *actuator* restart, and the wait is bounded by nothing; (b) whether the receiver discards a complete IDR that arrives before it has re-armed; (c) whether the first frames after resync are decoded but stale-dropped (> 60 ms) — in which case the "resync time" includes frames the decoder produced and threw away.
3. **The corpus numbers.** From all decoder reports since 2026-09-16 (`stream_discontinuities`, `first_idr_after_discontinuity`, the resync-marked slow-event rows), the distribution of resync-to-first-IDR and resync-to-first-render: p50 / p90 / max, and how many resyncs exceed one GOP (250 ms). Reuse `evidence/group_a_2026-09-20/a2_rescore_decoder_sessions.py` where it already parses these; extend a copy under evidence/c5_<date>/, do not modify the Group A script.
4. **One narrow hypothesis and one probe.** State the single most likely cause of the 195-332 ms and the one diagnostic (client counters, or a host-side `ffprobe` of SPS/PPS repetition on the live stream) that would confirm or falsify it. Do not implement the probe; it needs authorization.
5. **What a fix would touch** and what it must not: the resync path is on the "do not disturb" list for unrelated work, so say what the minimal change is and what runtime evidence would be needed to accept it.

Update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy), handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, and the battery file's C5 status. Nothing else changes. No IP addresses, ADB endpoints or device identifiers in any memory file.
