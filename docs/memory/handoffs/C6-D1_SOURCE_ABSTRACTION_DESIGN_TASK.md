---
memory_schema: 1
as_of: 2026-09-25
status: TASK HANDOFF — C6-D1: establish the generalized native source contract (source/capture → profile/encoder → transport/FEC → client decoder) as an architecture record and an interface module that production code does not yet import; no behavioural change; authorized by the user 2026-09-25
---

# C6-D1 — the generalized source contract, on paper and as an interface

**Why.** `docs/ROADMAP.md` C6 / C7: "generalized source contract
established" is a Phase C acceptance item; nothing on disk states the
contract. The games source is the only native source today
(`companion/native_stream.py`, 78 KB, with capture, encoder, transport,
audio and lifecycle in one place), and Phase C's later work (`C3.L4`
live, C4's scheme, C5's 1080p profile) and Phase G's remote transport all
sit on the seams C6 is meant to name. Naming them now, without moving
production code, is the safe unattended version of C6.

Read first: `docs/ROADMAP.md` §C6 and §C7, `architecture/ADAPTIVE_BITRATE.md`
(the actuator contract and the C3.L4 shadow section — a source contract
must carry the actuator capability), `companion/native_stream.py`,
`native_fec_relay.py`, `native_session_io.py`, `native_stream_profiles.py`,
`native_host_telemetry.py`, `process_audio/`, `diagnostics/stream_telemetry.py`,
`decisions/D114_STREAM_IDENTITY_POLICY.md`, `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`,
`decisions/D-101_BROWSER_CAMERA_C6_RECLASSIFICATION.md` (what C6 was
reclassified to cover).

**Scope.** Documentation plus one new module
(`companion/native_source_contract.py`) defining the interfaces with
docstrings and type signatures only — **imported by nothing in production**
and exercised by a unit test that instantiates a games-source adapter
**description** (not a running source) against it. No production file
changes. No session. No companion restart.

## Do

1. **Read the seams out of the code.** For the games source, list where
   each stage begins and ends today, by function and line range: capture
   (x11grab window, the DP dummy, the paused-frame capture), profile /
   encoder (the profile fields incl. cap, cushion, redundancy; the FFmpeg
   argv build; the encoder-only restart primitive), transport / FEC (RTP
   out, the relay, the audio path with its redundancy, the controller
   transport in the other direction), client decoder (the receiver, the
   report, telemetry), lifecycle (start/ready/stop/pause, recovery),
   diagnostics (status, heartbeat, telemetry), adaptation (the shadow
   controller's inputs and the actuator capability). Note every place a
   stage reaches across another stage's boundary — those are C6's
   findings.
2. **Write the contract** in `architecture/NATIVE_SOURCE_CONTRACT.md`:
   the four stages, the lifecycle states shared by every source, what a
   source must declare (capabilities: actuator class per `C3-L2`, audio
   model, capture backend, supported profiles), what is source-specific
   and stays outside the contract (capture, audio buffering, input), what
   the transport owes every source (FEC scheme by wire version, telemetry
   contract, diagnostics fields with no address identity), and how the
   Phase G remote transport would plug in **without** implementing it.
   Say which existing decisions it preserves (D114, C3-L2, C1's explicit
   profile, D-019) and what the games source would have to move to
   conform — as a migration list with sizes, not as a change.
3. **The interface module**: `Protocol`/ABC classes for
   `NativeSource`, `SourceProfile`, `Transport`, `ClientFeedback`, with the
   lifecycle enum and the capability record; a `GamesSourceDescription`
   that fills the capability record from today's constants (read from
   `native_stream_profiles.py`, not duplicated); a unit test that checks
   the description validates and that the module imports nothing from
   `native_stream.py` (so it cannot drag production in).
4. **C7 accounting**: append to `docs/ROADMAP.md` §C7 a status table of
   its acceptance items as of today with the record each rests on
   (profiles ✓ C1; telemetry ✓ C2; adaptive bitrate — shadow built, live
   gated on `C3.L3a`; adaptive FEC — decision record, arm `C4-M1`;
   1080p60 — open, needs a profile; source contract — this record; Games
   regression — `D7-R1`; reusable by Phase G — stated in the contract;
   checkpoint — pending), and the same in `docs/PROJECT_STATUS.md`.

## Record and memory

`evidence/C6_D1_SOURCE_CONTRACT_<date>.md` (the seam map, the
cross-boundary findings, the migration list, the test output), the
architecture record, the module and test; `patches/C6-D1_*.md` (new files
only, hashes); `PATCH_INDEX.md`; `CURRENT.md` one line;
`investigations/ACTIVE.md`; the daily file. No addresses. Nothing
committed.
