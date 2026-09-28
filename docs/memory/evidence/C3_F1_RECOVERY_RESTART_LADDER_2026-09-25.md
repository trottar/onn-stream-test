---
memory_schema: 1
as_of: 2026-09-25
status: C3-F1 DONE — WORKING (pre-registered): recovery's encoder restart is now level-preserving; at 7000 it is the unchanged C3.L1 continuity cycle, off 7000 a same-level encoder-only restart; four sessions (7000/6000/5500/5000): HTTP 200, bitrate kept at the level (client 7.04/6.04/5.59/5.05 Mbps), exactly one ssrc_change at the restart, first IDR 0-2 ms, no full start, lifecycle clean; restart gaps 197/178/189/132 ms vs S1's 186.5 median (not a gate); 8/8 unit tests; the continuity diagnostic keeps its 7000 guard; the loss-triggered state machine not exercised (needs nft)
---

# C3-F1 — recovery's encoder restart at any ladder level

Task: `handoffs/PHASE_C_PRECONDITIONS_2026-09-25_TASK.md` §1 (authorized
by the user 2026-09-25). This answers `C6_D1_SOURCE_CONTRACT_2026-09-25.md`
finding 7. Patch: `../patches/C3-F1_RECOVERY_RESTART_LADDER.md`. Evidence:
`c3_f1_2026-09-25/` (manifest `sha256_manifest.txt`).

## 1. The guard's purpose (read before touching it)

The continuity diagnostic (`diagnostic_c3_actuator_continuity_cycle` →
`run_c3_linux_actuator_continuity_cycle`) is `C3.L1`'s same-bitrate
encoder-only cycle. It was built to prove that replacing only the encoder
preserves the relay, the audio, the controller and the emulator **at the
reference bitrate**.

- Its spawn calls `_build_linux_ffmpeg_command` **with no bitrate**, which
  means the profile's 7000.
- Its payload asserts `target_bitrate_kbps: 7000` and mode
  `encoder_only_restart_same_bitrate`.

So the 7000 guard (`native_stream.py` and `c3_linux_actuator_probe.py`
113-121) is what keeps that claim true. Off 7000 the cycle would silently
reset the level while reporting "same bitrate".

**What the code shows is that purpose, and nothing else.** The guard is
kept.

## 2. The change: two callers split

- **`NativeStreamManager.recovery_restart_encoder()`** (new) is recovery's
  restart:
  - at 7000 it **calls the continuity cycle unchanged**, the path
    `R3`-`R3d` validated on real loss;
  - off 7000 (Linux) it calls
    `c3_linux_actuator_probe.run_c3_linux_recovery_restart`.
- **`run_c3_linux_recovery_restart`** runs `_run_c3_linux_bitrate_cycle`
  with a new `same_level_restart` mode:
  - target = `_active_bitrate_kbps`, which must be a validated level and
    equal to the current one;
  - the same kill, RTP baseline, spawn at `_build_linux_ffmpeg_command(...,
    bitrate_kbps=level, max_bitrate_kbps=level)`, resume poll and 0.75 s
    stability window as a ladder transition;
  - schema `privyhub_c3_recovery_restart_v1`, mode
    `encoder_only_restart_at_active_level`.
  - The relay, audio, controller transport and client session are
    untouched.
- **`plugins/games.py`**:
  - recovery's `restart_encoder` is now `recovery_restart_encoder`;
  - a **loopback-only** diagnostic route `c3-recovery-restart` calls the
    same callable, so the primitive can be exercised without the loss that
    normally triggers it.
- **Unchanged**: the continuity diagnostic and its guard; the transition
  and characterization paths (a same-level transition is still a no-op
  error, and characterization still requires 7000); the shadow controller.
- **`_active_bitrate_kbps` is the single source of truth for the level.**
  A full start still resets to 7000. That is C1's explicit-profile rule,
  not a defect.

## 3. Unit tests: 8/8 (`unit_tests.txt`), no session

The real cycle and the real argv builder ran against a fake manager: fake
encoder, relay and session I/O, nothing spawned. The tests check that:

- at 5000, 5500, 6000 and 7000 the argv's `-b:v` and `-maxrate` are that
  level, the level stays active, and the schema and mode are the recovery
  ones;
- only the encoder is replaced (the relay and session I/O are only read,
  never stopped or started);
- an unvalidated level is refused;
- the manager dispatches to the continuity cycle at 7000 and to the
  level-preserving restart off 7000;
- the continuity diagnostic still refuses off 7000 and still runs at 7000;
- the transition and characterization paths are unchanged;
- recovery is wired to the new primitive;
- the shadow controller does not reference it.

Beside them, the shadow (21), FEC (9) and contract (7) suites all pass in
one run, 45/45. The run did surface one isolation fragility in `C6-D1`'s
contract test: it checked `sys.modules` in-process. It now checks in a
fresh interpreter (`tools/test_native_source_contract.py`). `py_compile`
passes.

## 4. The four sessions (`c3_f1_sessions.py` → `sessions.json`, `c3_f1_sessions.log`)

The rules were written at 06:43Z, before any session
(`c3_f1_preregistration.txt`).

- **Setup.** The companion was restarted through its unit (MainPID owned
  8765 in 1.1 s, profile adopted, no `PRIVYHUB_*`). There were four
  attract-mode sessions, 06:46-06:52Z, with no controller mode set and
  `any_override` false at every PLAYING.
- **Per session**:
  1. transition to the level through the loopback route (7000 needs
     none), and settle (two distinct fresh snapshots);
  2. `POST c3-recovery-restart`;
  3. settle, then return to 7000 through the route;
  4. BACK (the report is stored), stop.

| level | HTTP | schema / path | bitrate before → after | client recent_mbps after | ssrc_change near the restart (total) | first IDR ms | restart gap ms | first RTP resume ms | full start | session started / ended |
| ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| 7000 | 200 | continuity cycle (C3.L1) | 7000 → 7000 | 7.04 | 1 (1) | 2 | 197 | 619 | no | 1 / 1 |
| 6000 | 200 | recovery restart (new) | 6000 → 6000 | 6.04 | 1 (3) | 0 | 178 | 418 | no | 1 / 1 |
| 5500 | 200 | recovery restart (new) | 5500 → 5500 | 5.59 | 1 (3) | 1 | 189 | 428 | no | 1 / 1 |
| 5000 | 200 | recovery restart (new) | 5000 → 5000 | 5.05 | 1 (3) | 1 | 132 | 418 | no | 1 / 1 |

- The totals of 3 off 7000 are the transition to the level, the restart,
  and the return.
- The restart gap is the largest `output_gap_ms` within 1 s after its
  `ssrc_change`, S1's transition-cost measure.
- "No full start" means: no recovery `encoder_restart method=full_start`,
  and one `native-stream-start` (the client's) per session.
- The manager's log shows each cycle's own label: `C3.L1 … same-bitrate`
  at 7000, and `C3-F1 … recovery restart at the active level: L → L`
  off 7000.

**Rule outcome: WORKING.** All four restarts succeeded and came back at
their level, each with exactly one `ssrc_change` and no full start.

- **Output gap** (not a gate): 132-197 ms, against S1's 186.5 ms median
  (n = 60). None is more than double.
- **First RTP resume** was 418-428 ms off 7000, against 619 ms for the
  continuity cycle at 7000. These are the two paths' own host-side
  timings. Both reach the client as one ~130-200 ms gap.

## What this does and does not show

- **It shows** the primitive link-drop recovery calls now restarts the
  encoder at whatever validated level is active and keeps it, at all four
  levels, with the continuity path at 7000 unchanged.
- **It does not exercise the loss-triggered state machine.** That needs
  real link loss (`nft`), which is never used unattended. Its trigger
  logic is unchanged: `R3`-`R3d` validated it at 7000, and it now calls
  the level-preserving primitive.
- **The C3.L4 precondition is met.** A live controller that moves the
  ladder no longer disables recovery.

## Teardown

- The companion is under systemd, with the profile adopted and no
  `PRIVYHUB_*`.
- The stream is inactive at `bitrate_kbps` 7000, and no game is active.
- The launcher banner is cleared. The driver does not reopen the launcher
  after its last stop, so a fresh launcher start was needed for it to
  poll.
- No samplers were started.

## Files (`c3_f1_2026-09-25/`)

- **Pre-registration and tests**: `c3_f1_preregistration.txt` and
  `unit_tests.txt`.
- **Driver and sessions**: `c3_f1_sessions.py`, `c3_f1_sessions.log` and
  `sessions.json`; per level `report_<L>.json` and `heartbeat_<L>.jsonl`.
- **Analysis**: `c3_f1_analyze.py` and `c3_f1_analysis.txt`.
- **Journal**: `companion_journal_redacted.txt` (heartbeat, status and
  telemetry lines dropped; 4 `c3-recovery-restart` POSTs).
- **Patch**: `c3_f1_patch.diff`, `pre_patch_sha256.txt` and
  `post_patch_sha256.txt`.

`h2_prep_redact.py --check` reports 0 residual matches on every file
except the decoder-report byte copies, which carry the known core-version
false positive. The loopback literal in the diff is written `<ipv4>`. No
address or device identifier appears in any file.
