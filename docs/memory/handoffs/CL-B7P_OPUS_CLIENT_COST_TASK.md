---
memory_schema: 1
as_of: 2026-10-19
status: TASK HANDOFF — CL-B7P (session B, software only, in parallel with session A's G8-S5): locate, from the client's code and a bench on the recorded reports, where the Opus path's ~0.2 core on the onn goes (CL-B6: the PrivyHub process 107 % of a core with Opus against 85 % with PCM; decoder spikes ≥ 20 ms 105 vs 61 per min on the LAN), build the one cheapest change behind a client-side build flag (absent = today byte for byte), pin the APK, do NOT install it. The install and the paired A/B are CL-B7, session A, later. No stream, no adb, no companion edits; no gradle build or bench while A's unit is active
---

# CL-B7P — the Opus path's cost on the client, located and a candidate built

Read first: `CL_B6_AB_REPEAT_AFTER_RESTART_2026-10-19.md` §3-4 (the onn's `top`: PrivyHub 107 % vs 85 % of a core, the onn 51 vs 46 % busy of 4 cores; spikes 104.7 vs 61.4 /min, ≥ 50 ms 2.9 vs 2.2; decode queue depth max 20, wait max 82 ms), `CL_B5_OPUS_DECODE_THREAD_AB_2026-10-18.md` (the decode thread: a bounded queue, `OpusDecodePipeline.kt`, the release order; MediaCodec `c2.android.opus.decoder`; the health report's decode fields), `CL_B4_…` (the first Opus client), `G4_W2_…` (the host side: 10-ms frames, 128 kbit/s, 2/4 duplication — **host code is not touched in this task**), `G4_S3_…` §6 (at 4000 the spikes read ~45/min; the three session reports in `g4_s3_2026-10-19/session_reports_audio.json`), `android/` (the receive thread, the Opus pipeline, the video decode and render path, the audio output).

**The user's decision (2026-10-19):** Opus stays adopted; the spikes / underruns are a watch item; this task is the engineering behind it, not a blocker.

## 1. The location, from code (the record §1 before any change)

- **The thread map, from the code:** every thread the client runs during a stream (receive, Opus decode, video decode / render, audio output, heartbeat, control), what each does per packet or per frame, and its priority (`Process.setThreadPriority` / `Thread.priority` / none) — a table.
- **The per-second work with Opus, counted from the code:** per 10-ms frame the socket read, the dedupe, the queue hand-off, the MediaCodec `dequeueInputBuffer` / `queueInputBuffer` / `dequeueOutputBuffer` / `releaseOutputBuffer` round trip, the PCM copy to the audio sink; 100 frames/s, 200 datagrams/s with the duplicate. State which of these the PCM path does not do (PCM: 400 datagrams/s and no codec), so the net is counted both ways.
- **The hypothesis, stated once:** the likely owner of the ~0.2 core — e.g. the framework's per-buffer cost at 100 round trips/s, a tight wait loop in the decode thread, the copy — chosen from the code with the reason, and **how CL-B7 will test it on the onn: `top -H` of the PrivyHub process over adb (per-thread CPU), the script written here** (`tools/cl_b7_onn_threads.py`: adb state reads only; masks nothing it does not need; not run in this task).
- **Why the video decoder's spikes would follow:** the mechanism by which audio-side CPU shows as ≥ 20-ms video output gaps on a 4-core device — stated from the code (shared cores and priorities), as a hypothesis.

## 2. The one change, behind a client-side flag

- **The flag:** a build-time or runtime client setting, named `privyhub.opus_decode=<mode>` or the project's convention, **absent = today's path byte for byte** (the same test discipline as the PCM path's in CL-B5: the existing unit tests unchanged and green).
- **The change:** the cheapest one the §1 reading predicts to move the thread's CPU — pick ONE of: the decode thread's priority (if the reading shows it above the video path's), a larger decode batch (two 10-ms frames per MediaCodec buffer — only if the frame boundary allows it without touching the host), the `dequeueOutputBuffer` timeout / wait strategy, or libopus through JNI in place of MediaCodec **only if the NDK is available offline on the host — check first; if not, say so and choose another**. Design before code, hashed; the diff; unit tests for the flag and for the mode; the PCM path untouched.
- **The bench, on the host, no stream:** the client's Opus decode path driven from a recorded packet sequence is not available on the host, so the bench is **what can be measured on the host**: the host-side unit tests' timing of the pipeline's queue and copy under the two modes with a synthetic 100-frame/s feed, if the test harness allows; else stated as not benchable off-device and left to CL-B7. No claim about the onn's CPU from the host.
- **The APK:** the debug APK built offline, its sha256 pinned beside the CONFIRMED `043891e1…` in the record — **not installed**; A installs it in CL-B7 with the per-thread reads and a paired A/B after an onn power-cycle (CL-B6's shape, three arms if cheap: PCM, Opus today, Opus with the change).

## 3. Coordination with session A (hard)

- **Before any gradle build, bench or test run longer than a minute:** `systemctl --user is-active privyhub-g8-s5` must be `inactive` / not found; if active, wait (poll every 60 s) — A is measuring the encoder on the hub and a build would load the host. Code reading, design and small edits may proceed meanwhile.
- **Never touched:** `companion/`, `tools/e1_suite.py`, `tools/e1_remote.py`, `tools/e3_state.py`, the drop-ins, the companion service, the audit log, the onn (no adb at all in this task), `logs/`. The `/tmp/b_*` copy holds `android/` only.

## 4. The record

`evidence/CL_B7P_OPUS_CLIENT_COST_2026-10-19.md` + `cl_b7p_2026-10-19/` (the thread map, the count, the hypothesis and its test plan, the design + hash, the diff, the test output, the APK hash, `redact_check.txt`, `manifest.sha256`); `tools/cl_b7_onn_threads.py`; `patches/CL-B7P_…md`; `docs/KNOWN_ISSUES.md` (the spikes item: the hypothesis added, the candidate built, CL-B7 pending); `logs/cl_b7p_git_status.txt`; `SESSION_B_STATUS.txt`; `SESSION_B_DONE_2026-10-19.md` (ten lines, with the CL-B7 task sketched: install, `top -H` reads, the three-arm A/B). Nothing adopted; nothing installed; nothing committed.

No sudo, no nft, the Opal read-only, no adb, no addresses or identifiers; nothing fetched, nothing deleted; nothing in `logs/` written by tests.
