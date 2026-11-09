# B65 — design, written before any B65 code (the N64 first start that never got ready)

Queue: `handoffs/QUEUE_2026-11-09X.md` §B65. Baseline `9e77af1e` (HOME-8 committed). Built in `/tmp/b_q16x_work`;
host part inside `PRIVYHUB_N64=1`. T6 is HOME-7's label; no title here.

## 0. Settled — the queue's hypothesis does not hold; the cause is the link plus the client's latched gate

Read in place: `home8_2026-11-08/c24/first_start_not_ready.txt`, the companion's journal (HTTP lines), the recovery
log, the ladder log, the frame-size log, the host samples, the onn's decoder report for that session (and the next
one's for comparison).

| UTC | what |
| --- | --- |
| 23:40:59 | `launch` (`players_joined=3`) → 200; the paused handoff (RetroArch pauses the core; B59 launch) |
| 23:41:03 | `load-state?slot=1` (the onn's Continue) → 200. **`load_state` refuses unless the manager holds the game paused** (`"Load State requires the game to be paused"`, every system), so the load went into a **paused** core. RetroArch sat at **2.9 % CPU** (paused) at 23:41:33 |
| 23:41:04 | `native-stream-start` → 200; the host then sent a **steady 60 frames and 789-834 packets every second** to the end (`native_frame_sizes`) |
| 23:41:07-23:41:21 | **link loss:** the ladder log's `lost_packets_delta` 30, 384, 700, 168, 136, 254, 113, 102 per 2-s report. The onn's report: **1,887 lost packets (7 %), 4 sequence resyncs (the largest a 403-packet jump), 19 forward gaps, 66 dropped frames**, rendering ~25-30 fps |
| ≈23:41:20 | **the onn's stabilization gate times out** (`STABILIZATION_TIMEOUT_MS` 15 s from the start; it needs 6 clean ticks: no new drop, ≥ 45 fps, an output gap ≤ 120 ms). It **latches** `stabilizationFailed` ("Game stream isn't ready"); only a *recovery* re-arms |
| 23:41:23-23:41:38 | **the link clean** (`lost_packets_delta` 0 on every report), but the gate stays failed; the user backs out (bye 23:41:38) |
| 23:41:43 | the second start, on the same RetroArch, still paused and answering: 9 lost packets in 91 s, ready in 8 s, played |

- **The Continue load was not the B61 hazard:** it cannot be sent into a running core (the manager's `_paused` check),
  and the core stayed paused and answering (the second start resumed it).
- **PS1 is the same:** any start whose first 15 s carry this much loss latches the same message. Nothing here is
  N64's.
- **No server-side "launching" status exists in the protocol.** The gate's phases ("Starting encoder" … "Checking
  stability") are the onn's own. The give-up is the onn's 15-s timeout. It is not built; the client fix below makes
  it unnecessary.

## 1. The fix the evidence names

1. **The cause — client, built in B67's APK (item 5), disclosed here:**
   - a *start* gate that times out while frames keep arriving re-arms instead of latching, at most until 60 s from the
     start (four 15-s windows); then it fails as today;
   - it re-arms only while the decoder renders new frames (frames flowing, as at 23:41:23-38); a start with no frames
     still fails at 15 s;
   - `debug.privyhub.start_gate_rearm=0` = today.
   - **Not in this item's diff** (B67's).
2. **The queue's guard, host, inside `PRIVYHUB_N64=1`** (defence in depth for the B61 hazard; it changes nothing on
   the evidence above):
   - an N64 `load_state` confirms, right before its `LOAD_STATE_SLOT`, that RetroArch answers `GET_STATUS PAUSED`
     within **1.5 s**: the manager's `_paused` flag and the core cannot disagree unseen;
   - otherwise it refuses, with a recovery row `continue_skipped` (`reason` `n64: core not paused <state>` or `n64:
     command port silent`, `slot`), and never sends the load. The onn's existing load-failure path follows (the
     title stays paused at its fresh start; Resume plays it);
   - a successful N64 load logs `continue_load` (`slot`, `status_ms`, `load_ms`) for A's reads.
3. **Absent = today:**
   - every hook keys on B61's `_n64_core` (an N64 session only);
   - PS1 / SNES / PS2 loads byte for byte (no extra `GET_STATUS`, no row).

## 2. Tests (`tests/b65_n64_continue/`; a fake command port; temp dirs removed)

- **N64:**
  - `PAUSED` answered → the check then `LOAD_STATE_SLOT 0` in that order, and `continue_load`;
  - a core answering `PAUSED` late (0.8 s) → the load waits and goes;
  - a silent port (no answer in 1.5 s) → no load sent, `continue_skipped` "command port silent", `EmulatorError`;
  - `PLAYING` → no load, `continue_skipped` "core not paused PLAYING".
- **PS1:** the same fake → no `GET_STATUS` before the load, no row (today).
- **Absent:** a fresh manager (`_n64_core` None) → today's path.
- **Mutations:** the check removed; the bound ignored; the guard on every system.
