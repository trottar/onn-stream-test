---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: fa79d4f5feba6797a6993a6fcdcdaff673812da3
---

# Curated Project Memory

This file contains current durable facts and rules only. Detailed chronology,
superseded state, raw runtime evidence, dated work history and patch history live
in their dedicated files. When this file conflicts with newer validated local
source or runtime evidence, the newer evidence wins.

## Mission and architecture direction

PrivyHub is a local-first, privacy-preserving, modular smart-home/media
experiment. The current prototype uses a Windows companion/server and an
inexpensive onn Android TV client on an isolated secondary network.

The architecture is intended to evolve toward inexpensive Linux-capable server
hardware and additional clients without mandatory cloud, subscriptions or
proprietary infrastructure.

Local deterministic control is the baseline. Optional external AI providers may
be added later only as explicit user-configured integrations with data
minimization and no silent fallback.

## Current development position

- Phase A — Games / emulator subsystem: **COMPLETE / PUSHED**
- Phase B — Diagnostics + clean native baseline: **COMPLETE / PUSHED**
- Phase C — Adaptive native streaming: **ACTIVE**
- Current technical item: **C1 explicit stream profiles**
- C1 inventory: **COMPLETE**
- Next technical classification: `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

The completed C1 inventory is checkpointed. Do not rerun it unless source changes
invalidate its evidence.

Current docs/memory cleanup is an administrative preservation task before C1
production implementation. It does not change runtime behavior.

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

- `companion/games/native/native_stream.py` — capture/session setup, quality
  constants, encoder policy, RTP/FEC/session ports.
- `companion/games/native/native_fec_relay.py` — relay/FEC behavior and part of
  the duplicated transport contract.
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt`
  — duplicated width/height/fps and endpoint constants.
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/RtpH264Receiver.kt`
  — receive/FEC buffering.

Likely portable profile fields:

- `id`
- `width`
- `height`
- `fps`
- `bitrate_kbps`
- `max_bitrate_kbps`
- `gop_frames`
- `bframes`
- optional `fec_group_size`

Keep outside the portable profile unless later evidence requires otherwise:

- NVENC codec/preset/tune/RC/buffer policy;
- RTP payload type and packet size;
- ports;
- capture backend;
- audio implementation;
- controller/input protocol;
- telemetry cadence.

First profile concept: `native_game_720p60_reference`.

The first C1 implementation is a behavior-preserving static extraction. Do not
add a GUI selector, adaptive controller or generalized streaming framework in
that first patch.

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

## Linux and resource direction

Roadmap v3 is Linux-first:

- D — Media Library / VOD / Live TV UX
- E — Linux Migration / Native Linux Baseline
- F — Linux Core Resource Characterization & Optimization
- G — Extended Emulation & User-Content Import
- H — Home Infrastructure / Client / Plugin Expansion
- I — Local Intelligence / Voice / Privacy-Aware AI

The HP EliteDesk 805 G6 Mini Ryzen 5 PRO 4650G / 16 GB / 256 GB machine is the
reference Linux prototype, not the minimum target.

Phase F sizing is intentionally limited to PS1-and-below before selecting
cheaper Prototype 2 hardware.

Future removable-media import validates/hashes/copies user-supplied
ROM/ISO/BIOS/firmware/keys into the runtime layout while keeping that content
out of Git and support bundles.

## Deferred and known debt

The severe UDP burst/gap/duplication investigation from the Windows/current
network test environment is deferred to representative Linux/network
infrastructure unless it becomes a blocker again. Do not encode quirks of the
current test environment into product architecture without representative
evidence.

Security/privacy debt for the isolated prototype includes Android cleartext /
exported diagnostic surfaces and companion network exposure without mature
authentication. Address that in a dedicated threat-model/auth/encryption/privacy
phase rather than mixing it into unrelated streaming or documentation work.

Maintainability debt remains in large files such as `MainActivity.kt`,
`emulator_manager.py` and `games.py`. Avoid broad refactors while behavior is
stable.
