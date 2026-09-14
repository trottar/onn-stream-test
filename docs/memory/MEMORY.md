---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Curated Project Memory

This file contains current durable facts and rules only. Detailed chronology,
superseded state, raw runtime evidence, dated work history and patch history live
in their dedicated files. When this file conflicts with newer validated local
source or runtime evidence, the newer evidence wins.

## Mission and architecture direction

PrivyHub is a local-first, privacy-preserving, modular smart-home/media
experiment.

The home Opal is the PrivyHub network/trust domain. The ordinary household
router/Wi-Fi is upstream connectivity only, not the PrivyHub trust domain.
Trusted PrivyHub server/client/device infrastructure belongs behind the Opal.
Older split-network Prototype-1 evidence is historical test topology.

The current implementation uses a Windows companion and inexpensive onn Android
TV client. The architecture evolves toward inexpensive Linux-capable server
hardware, portable trusted-LAN clients and additional home infrastructure
without mandatory cloud, subscriptions or proprietary infrastructure.

Local deterministic control is the baseline. Optional external AI providers may
be added later only as explicit user-configured integrations with data
minimization and no silent fallback.

## Current development position

- Phase A — Games / emulator subsystem: **COMPLETE / PUSHED**
- Phase B — Diagnostics + clean native baseline: **COMPLETE / PUSHED**
- Phase C — Adaptive native streaming: **ACTIVE**
- C1 inventory: **COMPLETE**
- C1 minimal schema design: **COMPLETE / CHECKPOINTED**
- C1.1 static reference profile extraction: **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**
- Native-stream public-status privacy hotfix: **LIVE ENDPOINT VALIDATED / CHECKPOINTED / PUSHED**
- Remote-foundation architecture/roadmap update: **CHECKPOINTED / PUSHED**
- C2.1 telemetry inventory: **COMPLETE**
- C2.2 minimal telemetry contract design: **COMPLETE / CHECKPOINTED / PUSHED**
- C2 stream telemetry v1 implementation: **COMPLETE / RUNTIME VALIDATED / CHECKPOINT PENDING**

The completed C1 inventory should not be rerun unless source changes invalidate
its evidence.

Next: `C2_IMPLEMENT_STREAM_TELEMETRY_V1` under D-059/D-060.

## C1 reference stream

Validated native game path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference behavior:

- 1280x720
- 60 fps
- 7000 kbps target bitrate
- GOP 15
- B-frames 0
- FEC group size 8
- RTP payload type 96
- packet size 1200 bytes

Current encoder backend also uses NVENC `p1`, ultra-low-latency tuning, CBR, a
1000k buffer and yuv420p. Those are backend policy, not automatically portable
profile semantics.

Current ownership:

- `companion/native_stream.py` — capture/session setup, quality
  constants, encoder policy, RTP/FEC/session ports.
- `companion/native_fec_relay.py` — relay/FEC behavior and part of
  the duplicated transport contract.
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt`
  — duplicated width/height/fps and endpoint constants.
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/RtpH264Receiver.kt`
  — receive/FEC buffering.

Reference profile `native_game_720p60_reference` is design-fixed as:

- `id`: `native_game_720p60_reference`
- `width`: 1280
- `height`: 720
- `fps`: 60
- `bitrate_kbps`: 7000
- `max_bitrate_kbps`: 7000
- `gop_frames`: 15
- `bframes`: 0
- `fec_group_size`: 8

Do not add `min_bitrate_kbps` in C1.1 because the validated baseline has no existing lower-bound behavior to preserve.

`fec_group_size` is portable C1 profile data and must validate to 1-8 because the current PHF1 marker mask is one byte.

Keep NVENC codec/preset/tune/RC/buffer/pixel-format policy, RTP payload type, packet size, ports, capture backend, audio, controller protocol and telemetry cadence outside the portable C1.1 profile.

C1.1 is companion-only static extraction. Preserve Android constants/startup ordering; keep existing top-level host status fields and add inspectable `profile_id` plus nested profile data. No selector, adaptation, generalized backend framework, capture/audio/input redesign or wire-format change.

## Stable runtime boundaries

Preserve these paths unless new evidence requires change:

- WGC native capture;
- H.264 NVENC low-latency encoding;
- process-specific game audio;
- UDP/FEC transport;
- Android hardware AVC decoding;
- PHI1/ViGEm P1-P4 controller chain;
- Save / Load / Pause / Resume / End lifecycle;
- A8 controller profiles;
- PS1 Port-1-only multitap;
- Phase B diagnostics / Self-Test / support-bundle pipeline.

Representative C1 regression must preserve picture, audio, controller input,
Pause/Resume, Save/Load, End/teardown and prior game/profile behavior.

## Games and emulator state

RetroArch is the managed emulator frontend.

Configured cores:

- NES — FCEUmm
- SNES — bsnes
- Genesis — BlastEm
- PS1 — Beetle PSX HW

Runtime coverage:

- PS1: strongest coverage; 1P/2P/4P routing, Crash Bash and CTR Port-1-only
  multitap, Save/Load, pause/resume, cheats/mods, A8 profiles and teardown.
- SNES: runtime exercised.
- NES: supported/configured but had no local A9 fixture.
- Genesis: supported/configured but had no local A9 fixture.

A family with no local fixture is not runtime validated merely because its
configuration exists. When content is later added, run the normal
launch/input/teardown regression before upgrading its status.

PrivyHub's PS1 local-player ceiling is four. The supported user-facing multitap
control is On/Off only. On means Beetle PSX HW Port 1 enabled and Port 2
disabled. Do not auto-enable multitap from current metadata.

Canonical ROMs and normal save namespaces are protected. Cheat/mod profiles
remain isolated.

## Controller architecture

Validated controller path:

`Android controller state -> PHI1 UDP full-state packet -> Windows NativeControllerBridge -> persistent ViGEm VX360 devices -> RetroArch ports`

PHI1 v1 supports the validated four-player implementation. All intended virtual
controllers must exist before RetroArch initializes input.

A8 mapping sits after canonical XUSB/ViGEm semantics and before
RetroArch/libretro gameplay bindings. Save/Load/Pause/End are meta controls
outside gameplay remapping.

Do not reopen lower controller layers because of a game-specific topology issue
unless fresh evidence contradicts the validated transport/device path.

## Diagnostics and evidence model

Phase B is complete and runtime/manual validated. It provides:

- unified health/resource model;
- read-only diagnostics health endpoint;
- 2-second Android client feedback reusing the existing metrics cadence;
- corrected decoder/network classifier semantics;
- bounded common event history;
- Diagnostics / Self-Test GUI;
- sanitized support-bundle collection;
- manual bounded diagnostic retention;
- Sunshine/Moonlight production-edge and artifact removal;
- native-only regression after legacy removal.

Raw measurements outrank classifiers when they disagree.

Stale-output shedding alone is informational in the low-latency decoder path.
Direct decoder-local drops, queue overflow and hardware-decoder failure remain
failure/degradation signals.

Do not create duplicate hot-loop samplers when existing instrumentation can
answer the question.

## Repository and evidence boundaries

Commit:

- source;
- configuration;
- durable engineering memory;
- reusable diagnostics;
- curated/sanitized evidence.

Keep operational/user/runtime data out of Git, including:

- ROMs/ISOs;
- saves/states;
- emulator runtime trees;
- media libraries;
- ordinary logs;
- patch backups;
- APK/build output;
- private ADB target cache;
- raw network-bearing data.

`docs/memory/evidence/raw/` is local working evidence and remains ignored.
Curated immutable evidence belongs under the existing evidence/snapshot
structure.

`manifest.json` must not contain a conventional self-hash entry. All other
registered durable-memory files are strictly hash/byte validated.

## Durable-memory roles and trust order

Use these roles:

- `CURRENT.md` — active state and immediate next step.
- `MEMORY.md` — current durable facts/rules; curated, not append-only.
- `memory/YYYY-MM-DD.md` — detailed dated work history.
- `handoffs/CURRENT_HANDOFF.md` — new-chat continuation.
- `decisions/` — decisions and supersession status.
- `evidence/` — runtime/E2E validation records.
- `investigations/` — active/closed/deferred investigations.
- `patches/` — patch/install protocol and history.
- `architecture/` — subsystem architecture.
- `roadmap/` — current development position.
- `history/` — superseded deep-memory snapshots/reference only.

Trust order:

1. current local source and fresh runtime evidence;
2. current specific evidence/decision/architecture records;
3. `CURRENT.md` / `CURRENT_HANDOFF.md` / current `MEMORY.md`;
4. dated history and patch records;
5. `history/` superseded deep memory.

Never let a superseded history snapshot override newer validated state.

## Development workflow

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**

Before modifying code or durable memory:

1. inspect exact current local state;
2. establish exact predecessor state/hash;
3. make one coherent change;
4. avoid unrelated cleanup;
5. update durable memory in the same work.

A diagnostic/probe and a production patch are separate steps when behavior is
uncertain. Inspect the fresh result before the next patch.

Do not infer success from `git status` alone when a specific installer/probe log
can establish the result.

## Patch and checkpoint rules

Meaningful ZIPs must:

- verify expected predecessor state;
- reject wrong state before modification;
- back up changed files under `archive/patch_backups`;
- preserve newline/BOM where relevant;
- validate actual installed/generated output;
- run applicable compile/build checks;
- run scoped `git diff --check`;
- restore exact predecessor bytes if post-write validation fails;
- support safe idempotence when practical;
- update relevant durable-memory files;
- declare `durable_memory_updated: true`.

Installer results are explicit:

- `INSTALLED SUCCESSFULLY`
- `FAILED BEFORE MODIFICATION`
- `ROLLED BACK`

Do not combine installation and checkpoint/push until installed state has been
independently validated.

Build final checkpoint staging from a reviewed allowlist. Never use broad
`git add .` to decide checkpoint scope.

On Windows, LF/CRLF conversion warnings from Git are advisory when the relevant
Git command returns exit code 0. A nonzero exit code remains a hard validation
failure.

## Privacy and network handling

Never ask the user to provide or paste IP addresses.

Network-bearing target data stays outside the repository and shareable
diagnostics. Use placeholders/redaction unless an address is absolutely required
inside a private local operation.

Wireless ADB recovery is an expected lifecycle. The validated build/install path
uses bounded recovery without printing or persisting discovered network targets
in durable memory.

## TV and media direction

Existing TV/media work is useful but unfinished. Future Phase D work includes:

- stable channel identity/deduplication;
- favorites/search/pagination;
- EPG matching/cache/timezone diagnostics;
- guide UX;
- unmatched-channel handling;
- recursive/local-first VOD artwork and metadata behavior.

Playback must not depend on guide or external metadata success.

## Linux, remote and resource direction

Roadmap v4:

- D — Media Library / VOD / Live TV UX
- E — Linux Migration / Native Linux Baseline
- F — Linux Core Resource Characterization & Optimization
- G — Secure Remote Access / Portable Client Foundation
- H — Extended Emulation & User-Content Import
- I — Home Infrastructure / Broader Plugin Expansion
- J — Local Intelligence / Voice / Privacy-Aware AI

The HP EliteDesk 805 G6 Mini Ryzen 5 PRO 4650G / 16 GB / 256 GB machine is the
reference Linux prototype, not the minimum target.

Phase F sizing is intentionally limited to PS1-and-below before selecting
cheaper Prototype 2 hardware.

Phase G establishes the remote/portable-client contract before heavier emulator
families. Tailscale is the preferred first overlay candidate, not a permanent
dependency. The future Linux hub can terminate the home-side overlay without
requiring replacement of the home Opal.

Phase H adds removable-media import and later-console characterization.
User-supplied ROM/ISO/BIOS/firmware/keys remain outside Git/support bundles.

Remote security has separate transport and application-authorization layers.
Source/request IP is not durable client identity.

Future WAN adaptation degrades quality before allowing queue/buffer growth to
create runaway latency.

## Deferred and known debt

The severe UDP burst/gap/duplication investigation from the older Windows/current
network test environment is deferred to the representative Linux + home Opal + onn
path unless it becomes a blocker again. Do not encode quirks of the
current test environment into product architecture without representative
evidence.

Security/privacy debt for the isolated prototype includes Android cleartext /
exported diagnostic surfaces and companion network exposure without mature
authentication. Address that in a dedicated threat-model/auth/encryption/privacy
phase rather than mixing it into unrelated streaming or documentation work.

Maintainability debt remains in large files such as `MainActivity.kt`,
`emulator_manager.py` and `games.py`. Avoid broad refactors while behavior is
stable.

## Secure remote foundation

Accepted architecture is documented in `architecture/REMOTE_ACCESS.md`.

Durable rules:

- home Opal is the PrivyHub trust/network domain;
- ordinary household network is upstream only;
- future travel router provides a portable trusted client LAN;
- Tailscale is the first-provider candidate, not a permanent dependency;
- overlay transport and PrivyHub application authorization are separate;
- source/request IP is not durable client identity;
- no permanent travel-router model is selected yet;
- Phase C is designed for future WAN reuse without implementing WAN plumbing;
- representative UDP replay target is Linux + home Opal + onn;
- remote runtime status remains planned only.

## C2 telemetry contract

Reuse the existing 2-second `privyhub_client_health_v1` path.

The companion assembles a measurement-only
`privyhub_stream_telemetry_v1` snapshot from receiver feedback and native host
status.

First implementation adds only:
- RFC-3550-style receiver inter-arrival jitter;
- control-path round-trip timing from the existing health POST;
- signed decoder queue-depth change;
- FEC-relay send-call/byte/error timing.

No second sampler or pacing scheduler.

No explicit decoder-starvation counter is required initially; existing
render/FPS/output-gap/queue measurements are sufficient raw inputs for C3.

C2 contains measurements only. C3 owns adaptation policy.

## C2 implementation status

`C2_IMPLEMENT_STREAM_TELEMETRY_V1` is **COMPLETE / RUNTIME VALIDATED /
CHECKPOINT PENDING**.

The live `privyhub_stream_telemetry_v1` contract passed all automated runtime
gates, and representative gameplay passed picture, process audio, controller,
Pause/Resume, Save/Load and End/teardown.

C3 adaptive bitrate is the next development step after this validated state is
checkpointed and pushed.
