---
memory_schema: 1
as_of: 2026-09-25
status: C6 generalized native source contract — ESTABLISHED on paper and as an interface module (companion/native_source_contract.py) that production does not import; no behavioural change (C6-D1)
---

# The generalized native source contract (C6)

Roadmap: `docs/ROADMAP.md` §C6 and §C7 ("generalized source contract
established"). Task: `handoffs/C6-D1_SOURCE_ABSTRACTION_DESIGN_TASK.md`.

**Where things are:**

- the seam map of today's games source, the cross-boundary findings and
  the migration list: `evidence/C6_D1_SOURCE_CONTRACT_2026-09-25.md`;
- the interfaces: `companion/native_source_contract.py`;
- the tests: `tools/test_native_source_contract.py`.

## The four stages

```text
source/capture  ->  profile/encoder  ->  transport/FEC  ->  client decoder
      ^                                                          |
      +--------------- input (reverse path, source-specific) ----+
                       feedback (heartbeat, telemetry, report) ---> adaptation
```

1. **Source/capture** (`NativeSource`) owns what is shown and how it
   reaches the encoder. For games, that is x11grab of the RetroArch window
   on the headless display. **Source-specific, and outside the contract**:
   the capture mechanism, the audio capture and buffering, and the input
   path back into the source.
2. **Profile/encoder** (`SourceProfile`): every stream parameter is
   declared, none is implied (C1). That covers resolution, fps, bitrate
   and max, GOP, B-frames, the FEC group, and the frame cap. A source's
   audio parameters (cushion, redundancy) are profile fields too, because
   they are session decisions measured against the same close-out rows.
   Environment overrides exist for comparison arms only and must show in
   `any_override`.
3. **Transport/FEC** (`Transport`). The transport owes every source:
   - **an FEC scheme identified on the wire** by its version byte, so the
     client selects its decoder from the packet, never from a setting.
     Today that is `PHF1` v1, `xor8_1`: 8 data + 1 XOR parity, groups
     within one frame. New schemes take new versions (`C4-M1`).
   - **a telemetry contract**: `privyhub_stream_telemetry_v1` (C2), the 2 s
     heartbeat `privyhub_native_stream_heartbeat_v3`, and the end-of-session
     report `privyhub_native_decoder_session_v2`.
   - **diagnostics fields with no address identity**: counters, rates and
     schemas only; no source or request address in any status or log
     field.
4. **Client decoder feedback** (`ClientFeedback`): the heartbeat, the
   telemetry snapshot and the session report. **Adaptation reads only
   this**, never a source's internals. The shadow controller already
   does: it reads the `privyhub_stream_telemetry_v1` snapshot.

## Lifecycle shared by every source

`SourceLifecycle`: `IDLE → STARTING → READY → PLAYING ⇄ PAUSED`,
`PLAYING → RECOVERING → PLAYING | STOPPING`, `→ STOPPING → IDLE`, and
`FAILED`, which is terminal for the session with a reason exposed.

- **Recovery is source-defined.** Games resumes a fresh core from a
  saved state (`R3c2`). Any source can enter `RECOVERING` on the same
  signals: client silence and heartbeat staleness.
- **READY is a lifecycle state, not a paused frame.** The games source
  starts capture on a paused core and releases it at
  `native-stream-ready`.

## What a source must declare (`SourceCapabilities`)

- source kind and capture backend;
- **audio model**: none, separate UDP PCM (games), or muxed;
- **actuator class, per `C3-L2`**: `none`, `video_only_restart` (Linux
  today, authorized for fallback and recovery only), or
  `live_bitrate_reconfigure` (not available on Linux);
- the validated bitrate ladder and the reference level (required whenever
  the class is not `none`);
- supported profiles and the FEC schemes it can be sent with (wire
  versions unique);
- the client input path (source-specific);
- `diagnostics_identity_free`, which must be true.

`validate()` enforces the declarable rules. The games description passes.

## Decisions it preserves

- **D114**: keep independent dimensions independent. Transport health is
  not content identity. Here that means transport/FEC health and
  diagnostics never carry, or infer from, source identity or addresses.
- **C3-L2**: the actuator class is declared per source. Automatic
  adaptation during play is not authorized for `video_only_restart`, and
  only FALLBACK could ever act (`ADAPTIVE_BITRATE.md` §C3.L4 shadow).
- **C1**: an explicit profile, every parameter declared, and `any_override`
  shown.
- **D-019**: stale-output shedding alone is informational, never an
  adaptation input.
- **D-101**: browser/app and camera sources return after D8 *through
  this contract*, not through a parallel path.

## Phase G (remote/WAN) plugs in without being built here

A remote transport is another `Transport`:

- the same FEC-by-wire-version rule;
- the same telemetry contract;
- the same identity-free diagnostics.

Its sources and client feedback are unchanged. What changes is the
transport's own capability: RTT, a loss model, and possibly different FEC
schemes. That becomes the transport's declaration beside the source's.
**Nothing about remote transport is implemented** (C7's wording).

## What the games source would have to move to conform

This is a list, not a change. Sizes are today's.

| # | move | from | size |
| --- | --- | --- | --- |
| 1 | Split capture/encoder from transport and session I/O: `NativeStreamManager` builds the relay, audio, controller and host telemetry itself | `native_stream.py` (2,469 lines), `__init__` 96-111, `_start_linux_locked` 1537-1735 | large |
| 2 | Make the bitrate actuator a method of the encoder stage, not a diagnostic module poking `manager._process` / `_fec_relay` / `_active_bitrate_kbps` | `diagnostics/c3_linux_actuator_probe.py` 443-821 (~380 lines) | medium |
| 3 | Give recovery its own restart primitive. Today it borrows the continuity *diagnostic*, which refuses unless the active bitrate is 7000, and a full start silently resets the ladder level | `plugins/games.py` 97-103; `native_stream.py` 2283-2287, 1521, 1659-1662 | small, **correctness** |
| 4 | Stop `plugins/games.py` reaching into `_native_stream._session_io.controller` | `games.py` 106-120 | small |
| 5 | One source for shared constants: the ladder (five copies), the audio packet ms and redundancy max offset, the relay port, `pkt_size`, the heartbeat field whitelist (two copies) | see the evidence | small |
| 6 | Report the actuator class and the FEC scheme in status (only the docs and this module have them) | `native-stream-status` | small |
| 7 | Keep absolute paths, argv, window titles and PIDs out of client-facing diagnostics, or mark them host-only | `native_stream.py` 576-646, relay 913 | small |
| 8 | Status reads must not change lifecycle: `status()` reaps, and the client-health route calls it every 2 s | `native_stream.py` 478-482; `privyhub_service.py` | small |
| 9 | Align the relay's `frames_over_cap` yardstick (`PRIVYHUB_FRAME_BYTE_CAP`) with the profile's cap, or rename it | `native_fec_relay.py` 96, 818-826 | small |
