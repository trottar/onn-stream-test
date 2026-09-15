---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Curated Project Memory


<!-- PRIVYHUB_D079_MEMORY_CHECKPOINT_LINUX_ONN_STREAM_DIAGNOSIS_2026_09_15:MEMORY:BEGIN -->
## Linux migration — integrated onn streaming facts (2026-09-15)

- The normal Linux RetroArch launch/save/controller/capture path has crossed the
  first integrated onn E2E boundary. Managed RetroArch launches, prior saves
  load, the exact owned X11 window is discovered by the native Linux backend,
  and VAAPI encodes near 60 fps.
- Android's current auto-open handoff is not Linux-neutral: it still requires
  the old Windows-only `host_window_policy.window_found`. On Linux this can be
  false even when native exact-window discovery subsequently succeeds. Treat
  the resulting `Game ready, stream not opened` popup as a confirmed handoff
  compatibility bug, not proof that the Linux capture backend failed.
- The current stream blocker is transport stability after native-stream start.
  Representative runs show Linux UDP `SndbufErrors`/`RcvbufErrors`, long video
  send-call stalls, and thousands of failed sends from the separate nonblocking
  RT audio sender. Interface `tx_dropped`/`tx_errors` staying flat means ordinary
  NIC statistics do not account for the loss.
- Increasing Linux socket ceilings so the relay obtains its requested 2 MiB
  buffers did not fix the failure. Do not encode a larger socket buffer as the
  product solution.
- The current Linux Wi-Fi device is a USB RTL8822BU using `rtw_8822bu`, at
  SuperSpeed, with USB runtime autosuspend disabled. Kernel logs repeatedly show
  `firmware failed to leave lps state`; disabling ordinary mac80211/NetworkManager
  powersave suppresses those warnings but does not remove the UDP failure.
  Therefore LPS is a genuine secondary driver defect but not yet the primary
  transport root cause.
- Preserve the existing standalone UDP diagnostics through Linux migration.
  The next accepted diagnostic is Linux -> onn idle synthetic UDP before any
  further production-stream tuning.
- Privacy remains strict: diagnostics may discover the onn address locally but
  must not print, persist in shareable evidence, or ask the user to provide it.

<!-- PRIVYHUB_D079_MEMORY_CHECKPOINT_LINUX_ONN_STREAM_DIAGNOSIS_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D078_MEMORY -->
## Linux companion media-server launcher

D-078 establishes the platform rule for the companion-owned HTTP media server: Windows retains the PowerShell wrapper, while non-Windows hosts launch `companion/range_server.py` directly with `sys.executable`. Do not reintroduce a PowerShell requirement into normal Linux companion startup. Live-source PowerShell runners remain a separate portability seam.

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
- C2 stream telemetry v1 implementation: **COMPLETE / RUNTIME VALIDATED / CHECKPOINTED / PUSHED**

The completed C1 inventory should not be rerun unless source changes invalidate
its evidence.

Next: `C3_ACTUATOR_CONTINUITY_PROBE` under D-059/D-060/D-062.

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
CHECKPOINTED / PUSHED**.

The live `privyhub_stream_telemetry_v1` contract passed all automated runtime
gates, and representative gameplay passed picture, process audio, controller,
Pause/Resume, Save/Load and End/teardown.

C3 adaptive bitrate is the next development step after this validated state is
checkpointed and pushed.

## C3 adaptive bitrate durable rules

C3 is active after the runtime-validated C2 checkpoint.

D-062:
- reuse the 2-second telemetry cadence;
- keep 1280x720/60/GOP15/B-frames0/FEC8 fixed;
- separate controller from a backend-neutral bitrate actuator;
- current FFmpeg CLI path has no live bitrate setter;
- first probe one unchanged-7000 video-actuator cycle;
- stale/unavailable/resync telemetry freezes adaptation;
- do not invent the production minimum/ladder before characterization;
- C4 adaptive FEC remains separate.

Next technical step: `C3_ACTUATOR_CONTINUITY_PROBE`.

## C3 actuator diagnostic implementation state

`C3_ACTUATOR_CONTINUITY_PROBE` is **RUNTIME VALIDATED** and the
backend-neutral `video_only_restart` strategy is accepted for the initial C3
implementation path. The installed Windows probe remains development
infrastructure until checkpointed and incorporated into the production actuator.

The diagnostic:
- stays at 7000 kbps;
- cycles WGC capture + FFmpeg only;
- keeps FEC/audio/controller ownership alive;
- is loopback-triggered only;
- reuses C2 telemetry and the existing Android decoder-session report;
- adds no Android sampler or adaptive controller.

Do not choose `video_only_restart` versus `live_bitrate_reconfigure` until the
runtime evidence and manual gameplay regression are reviewed.

## C3 actuator acceptance rule

D-063:
- accept backend-neutral `video_only_restart` for the initial C3 actuator;
- Windows implementation/runtime evidence is WGC + FFmpeg/NVENC;
- preserve FEC, process audio, persistent controller and game-session ownership
  across a video actuator cycle;
- do not claim the Windows implementation itself is Linux-portable;
- Linux must provide an equivalent backend-specific video actuator and rerun
  continuity validation;
- retain the measured 791 ms max output gap / 800 ms max receive-to-decode
  evidence;
- focused play showed no clear restart-specific disruption, while possible
  slight stutter remained indistinguishable from occasional baseline stutter;
- do not add a minimum bitrate or automatic controller yet.

Next: fixed-bitrate characterization.

## C3 fixed-bitrate characterization rule

C3 characterization proceeds **one candidate at a time**.

First candidate: 6000 kbps.

6000 is diagnostic only until runtime evidence and focused visual-quality
observation are reviewed. Keep 1280x720@60, GOP15, B-frames0 and FEC8 fixed.
Do not sweep multiple levels in one decision because that would obscure the
first quality/capacity boundary.

A normal session still starts at the validated 7000 kbps reference. The
loopback-only characterization action may move the active encoder to 6000; a
normal End/new session resets to the reference.

No automatic controller or production minimum exists yet.

## C3 validated bitrate candidates

D-064:
- 7000 kbps remains the validated reference/max;
- 6000 kbps is the first validated lower candidate;
- 6000 validation keeps 1280x720@60, GOP15, B-frames0 and FEC8 unchanged;
- one decoder drop/queue-overflow event and ~1.0 s maximum restart-associated
  gap are retained as evidence rather than hidden;
- focused movement/gameplay at 6000 was fine;
- audible audio stutter occurred, but detailed receiver evidence shows the
  existing burst/gap queue pathology rather than evidence of insufficient
  average 6000-kbps capacity;
- do not attribute the deferred audio pathology to 6000 without new evidence;
- replay the transport/audio pathology on Linux + Home Opal before product
  architecture changes;
- next bitrate characterization candidate is 5000 kbps;
- production minimum and automatic controller remain unset.

## Installer validation rule — exit code is authoritative

For deterministic patch/install/checkpoint tooling, **command exit code is the
authoritative success/failure signal**.

Never fail a validation merely because stdout or stderr is non-empty. Tools such
as Git can emit benign warnings (including line-ending warnings) while returning
success.

Required behavior:
- capture stdout and stderr separately where practical;
- preserve warnings in the result log;
- fail only on the command's documented nonzero exit status or on a separate
  explicit semantic invariant;
- for `git diff --check`, return code 0 with warnings is PASS;
- package-side regression must cover return code 0 + warning text and nonzero
  return code + diagnostic text.

This rule was added after the failed
`privyhub_c3_fixed_6000_runtime_acceptance_01_2026-09-14` installer incorrectly
rolled back on warning text despite successful `git diff --check`.

## C3 5000 characterization rule

After D-064, C3 proceeds to exactly one lower candidate: 5000 kbps.

Evidence-backed levels before this test:
- 7000 kbps validated reference/max;
- 6000 kbps validated lower candidate.

5000 remains diagnostic until technical continuity and focused visual quality
are reviewed.

Keep 1280x720@60, GOP15, B-frames0 and FEC8 fixed. Start from a normal 7000-kbps
session and use the same backend-neutral video-only restart boundary.

The fixed-bitrate diagnostic implementation is shared internally; do not fork a
new actuator body per bitrate.

The known audio burst/gap pathology remains deferred to representative Linux +
Home-Opal replay. Report its detailed counters during characterization, but do
not reject a bitrate merely because those pre-existing counters are nonzero.
Only new evidence tying a regression specifically to the bitrate may change
that attribution.

No production minimum or automatic bitrate controller exists yet.

## C3 5000 disposition and bitrate bracket

D-065:
- 7000 kbps remains the validated reference/max;
- 6000 kbps remains a validated lower candidate;
- 5000 kbps is runtime tested but **not accepted** as a ladder candidate;
- 5000 produced a subjectively clearer image and clean restart recovery, but
  steady-state visual stutters were definitely more frequent than at the
  validated settings;
- smoothness/interactive quality takes precedence over apparent image clarity
  for bitrate acceptance;
- possible slightly worse input lag at 5000 was uncertain and is not required
  for the rejection decision;
- audio burst/gap pathology remains separate and deferred to Linux + Home Opal;
- usable-floor characterization is bracketed to 5000–6000 kbps;
- next single candidate is 5500 kbps;
- production minimum and automatic controller remain unset.

## C3 5500 midpoint characterization rule

After D-065, the lower fixed-bitrate boundary is bracketed at 5000–6000 kbps.

5500 kbps is the single midpoint candidate.

Before this test:
- 7000 kbps validated;
- 6000 kbps validated;
- 5000 kbps runtime tested / not accepted due definite increased steady-state
  visual stuttering.

Keep 1280x720@60, GOP15, B-frames0 and FEC8 fixed. Use the same shared
backend-neutral video-only restart implementation and require focused
steady-state smoothness observation.

Acceptance priority remains:
**interactive smoothness/continuity before subjective image clarity.**

The known audio burst/gap pathology remains separately deferred to
representative Linux + Home-Opal replay. Report its detailed counters but do not
treat pre-existing nonzero audio metrics as a bitrate failure without new
bitrate-specific causal evidence.

No production minimum or automatic bitrate controller exists yet.

## C3 fixed bitrate envelope — D-066

Windows C3 fixed-bitrate characterization is complete.

Validated controller ladder:
- 7000 kbps — reference/max;
- 6000 kbps — middle;
- 5500 kbps — lower/current Windows floor.

Not accepted:
- 5000 kbps — technically viable but showed definitely more steady-state visual
  stutters during focused extended play.

5500 acceptance:
- focused play had a short initial lag, recovered after a few seconds, then ran
  very well;
- six fresh post-cycle telemetry intervals from 5.5–15.5 seconds added 638
  rendered frames with zero decoder-drop and zero queue-overflow deltas;
- final whole-session decoder report still contained 57 drops/overflows. Preserve
  this fact; do not invent a timestamp/location for those drops outside the
  sampled interval.

For the adaptive controller, use discrete levels 5500/6000/7000 rather than
continuing to optimize the floor in the current test environment.

The 5500 floor is a Windows C3 validation result, not a universal backend
constant. Linux migration must revalidate the actuator and fixed envelope.

The known audio burst/gap pathology remains separately deferred to Linux + Home
Opal.

Automatic bitrate control is still not implemented.

## Startup stabilization and shared game stream status — D-067

Use the existing paused emulator launch as an evidence-driven native-stream
startup gate, not as a playback buffer.

Rules:
- `native-stream-start` keeps gameplay paused;
- Android explicitly calls `native-stream-ready` only after local readiness;
- readiness uses consecutive clean receiver/decoder evidence, not fixed sleep;
- timeout/error leaves game paused;
- gameplay controller input is blocked while stabilizing except Back;
- startup UI shows game title, resolution/FPS, bitrate, FEC and
  video/audio/controller state;
- no network address, endpoint, port, SSRC or packet identifier is exposed;
- Back preserves the validated paused-frame exit;
- MainActivity reuses the same in-process status snapshot in Game Session UI;
- automatic adaptation is frozen while stabilizing/paused and is not enabled by
  this patch.

Initial development thresholds: six clean 500-ms checks, recent FPS >=45,
output gap <=120 ms, rx-to-decode <=150 ms, zero queue depth, no new
drop/overflow counters, and a 15-second fail-closed ceiling.

## Companion restart requirement for Python runtime validation — D-068

When companion Python source changes, the running companion service must be
restarted before runtime validation. Installing new `.py` bytes does not
hot-reload the existing Python process.

A stale companion can create false mixed-version failures: the Android APK may
exercise new client behavior while the old Python process still implements old
plugin actions/lifecycle.

This was proven during D-067 validation:
- RetroArch really entered PAUSED;
- stale predecessor `native-stream-start` later resumed it;
- the new Android client attempted `native-stream-ready`;
- the stale companion did not provide the new contract;
- UI reported release failure;
- restarting the companion fixed the same installed source.

D-067 startup stabilization is runtime validated after restart, and the user
reported no initial gameplay lag.

## Bidirectional actuator validation rule — D-069

Before automatic C3 bitrate policy is enabled, the backend-neutral actuator must
be runtime validated in both directions.

Existing evidence covers unchanged-7000 continuity and downward fixed-bitrate
transitions. The missing proof is upward recovery from an already-lowered
encoder.

Use exactly one focused diagnostic sequence:
`7000 -> 6000 -> 7000`.

Reuse the same video-only restart body. Do not create a second actuator path.

The diagnostic transition endpoint is loopback-only and accepts only the
validated 5500/6000/7000 ladder. 5000 remains excluded.

Do not attempt the upshift until fresh C2 receiver/decoder evidence has recovered
after the downshift.

Automatic adaptation remains disabled until this probe is accepted.

## Video-only restart actuator disposition — D-070

The C3 `video_only_restart` actuator is bidirectionally functional but is not
the seamless automatic bitrate actuator.

Validated D-069 sequence:
`7000 -> 6000 -> 7000`.

Measured encoder-restart gaps:
- downshift first RTP resume: 952.789 ms;
- upshift first RTP resume: 837.313 ms.

Focused play observed a roughly one-second freeze during a transition. Final
decoder evidence recorded a 1,059-ms max output gap.

Rule:
do not build automatic fast-down/slow-up policy on `video_only_restart` during
active gameplay.

Retain the restart actuator for diagnostic transitions, startup/manual recovery,
fallback, and backends that cannot reconfigure live.

Next investigate live bitrate reconfiguration without replacing the encoder
process. Automatic adaptation remains disabled.

## Linux-first phase order and Windows adaptation boundary — D-071

Current live roadmap order after Phase C:
**D Linux Migration -> E Linux Characterization/Optimization -> F Media/VOD/Live TV -> G Remote**.

The previous D/E/F labels are superseded:
- old D Media/VOD/Live TV = new F;
- old E Linux Migration = new D;
- old F Linux Characterization = new E.

Reason:
finish the platform migration before investing further in media/VOD/EPG polish.

Windows C3 portable results remain valid evidence:
- explicit stream profile;
- end-to-end telemetry;
- startup stabilization/readiness;
- fixed 5500/6000/7000 test-environment evidence;
- 5000 rejection;
- backend-neutral actuator capability boundary;
- restart actuation is too disruptive for seamless automatic play.

Do not implement an NVENC-specific live controller merely to finish Windows C3.

Phase D Linux must preserve currently working media/server behavior. Phase F
later improves media UX on Linux.

Phase E Linux characterization must inventory actual encoder actuation and
revalidate bitrate levels before production adaptation is finalized.

Adaptive FEC and transport-sensitive tuning also wait for representative
Linux + home Opal + onn evidence.

## Phase C pause/resume sequencing — D-072

Phase C is paused at the Windows portability boundary, not complete.

Do Phase D Linux migration next. Once the Linux-native baseline is working,
return to the unfinished Phase C items on Linux before starting Phase E.

Remaining Phase C:
- C3 automatic bitrate controller;
- C4 adaptive FEC or explicit evidence-backed deferral;
- C5 1080p60 capability characterization;
- C6 generalized native source abstraction;
- C7 final Phase C acceptance/checkpoint.

Execution order:
`D -> remaining C on Linux -> E -> F -> G`.

Do not treat the Windows 5500/6000/7000 ladder as a Linux product constant.
Revalidate actuator and bitrate envelope on Linux.

## Linux native baseline architectural facts — D-073

Phase D established the Linux host architecture on Debian 13 with the Ryzen
Renoir iGPU.

Durable Linux backend facts:

- Renoir `amdgpu` exposes working H.264 VAAPI encoding through
  `/dev/dri/renderD128`.
- Stock Debian FFmpeg is sufficient for the current baseline.
- Exact X11 window capture with `x11grab -window_id` works for real RetroArch
  gameplay and feeds VAAPI H.264 successfully.
- The target RetroArch window must remain mapped. Minimizing/unmapping it kills
  exact-window capture. Covering/occluding a still-mapped window does not.
- PulseAudio is the validated desktop audio stack. A dedicated sink plus monitor
  capture can isolate application audio.
- Linux uinput can expose four simultaneous PrivyHub virtual gamepads.
- RetroArch enumerates all four when they exist before frontend startup.
- Local udev autoconfig matching works for the validated PrivyHub virtual-pad
  capability set.
- Preserve PHI1 v1 and replace only the Windows ViGEm output backend with
  Linux uinput.
- The project-owned RetroArch 1.22.2 Linux AppImage and all four required Linux
  cores load successfully.
- Real SNES video/audio/content lifecycle is validated.
- Existing `EmulatorManager` readiness, launch, loopback control, save flush,
  and shutdown lifecycle work on Linux without source changes.
- `EmulatorManager` is therefore not a Linux-porting blocker. Do not replace it
  without new regression evidence.
- `NativeStreamManager` constructs safely on Linux, but its current capture,
  encoder, audio, controller, and telemetry status remains Windows-specific.
  Preserve the manager/control surface and substitute platform backends.
- Windows durable RetroArch state migrated byte-for-byte to Linux: 129 files,
  manifest SHA-256
  `6de3fa8b67d5a0ee21ace20af9347b5cf0f5997f3a9d410fcd23d6410b18280c`.
- The migrated backup had no files under `system/`; do not assume PS1 BIOS
  availability from the migration.
- Never use the user's global `~/.config/retroarch` as production state.
  PrivyHub owns `data/games/retroarch/`.

Remaining Phase D production seams:

1. platform-aware RetroArch runtime/config selection;
2. Linux X11/VAAPI native-video backend;
3. Linux PulseAudio native-audio backend;
4. PHI1-to-uinput controller backend — D-076/R1/R2 host-side managed runtime validated; onn E2E pending;
5. Linux host telemetry;
6. durable service-user/device permissions;
7. migrated save/state/cheat/mod/profile regression validation.

Windows bitrate values remain reference evidence only. Linux bitrate, FEC, and
actuation behavior must be characterized independently.

## Linux native-video implementation boundary — D-074

The Linux production video backend uses the manager-owned RetroArch PID as the
capture identity. AppImage `/proc/<pid>/exe` paths are temporary mount paths and
must not be treated as durable project identity.

Linux video is intentionally single-process:
`exact X11 window -> FFmpeg x11grab -> VAAPI H.264 -> loopback RTP -> existing
NativeVideoFecRelay`.

Do not create a Linux WGC-equivalent raw-frame bridge. Preserve the existing
Android RTP/H.264/FEC contract.

The Windows WGC/NVENC path remains a separate validated backend and must not be
changed by Linux implementation work.

## Linux native-audio implementation boundary — D-075

Linux process-audio isolation uses the EmulatorManager-owned RetroArch PID to
identify exactly one PulseAudio sink-input. The stream is moved into a temporary
dedicated PrivyHub null sink at 48 kHz stereo and captured from that sink's
monitor.

The existing Android PHA1 contract is preserved: PCM S16LE stereo at 48 kHz,
240 frames / 5 ms per packet, 16-byte `PHA1` v1 header.

A plain Python sleep-based pacer is explicitly rejected because Baseline 33
showed paired late intervals and catch-up bursts despite zero PCM underflows.
Baseline 34 validated the hybrid monotonic pacer: coarse 1 ms sleep, scheduler
yield, then a final <=0.25 ms spin.

Do not replace the PulseAudio route because of Baseline 33; the failure was
isolated to pacing. Do not change Android audio for the Linux migration unless
new E2E evidence requires it.
## Linux native-audio scheduler boundary — D-075R1

**Authoritative over the original D-075 pacing conclusion.** The D-075
PulseAudio architecture remains valid, but Baseline 34's stable idle-host pacer
was not representative once RetroArch was active.

Baselines 39-41 establish that the Linux PHA1 sender needs thread-local
`SCHED_RR` priority 1 under active RetroArch. Baseline 41 verified that promoting
only the sender thread leaves the companion main thread at `SCHED_OTHER` and
restores stable 5 ms sender cadence.

Production rule: Linux native audio must verify `SCHED_RR/1` on the sender thread
before emitting PHA1. If the policy cannot be acquired, fail the Linux audio
subpath rather than silently running the known-jittery `SCHED_OTHER` pacer.
Never grant `CAP_SYS_NICE` to the general Python interpreter for this purpose.
The preferred persistent deployment boundary is service-scoped
`LimitRTPRIO=1`/equivalent, with no production `sudo` invocation.

## Linux controller implementation boundary — D-076

Baselines 42-45 are authoritative for the Linux controller mapping. Canonical
PHI1/XUSB remains the host-independent transport contract. Linux converts that
state to four `evdev.UInput` pads; Windows continues to use ViGEm VX360 pads.

Linux production mapping:

- A/B/X/Y -> BTN_SOUTH/BTN_EAST/BTN_WEST/BTN_NORTH;
- L1/R1 -> BTN_TL/BTN_TR;
- Back/Start/L3/R3 -> BTN_SELECT/BTN_START/BTN_THUMBL/BTN_THUMBR;
- LX/LY -> ABS_X/ABS_Y, with XInput-positive Y inverted for Linux;
- RX/RY -> ABS_RX/ABS_RY, with the same Y inversion;
- LT/RT -> ABS_Z/ABS_RZ, 0..255;
- D-pad -> ABS_HAT0X/ABS_HAT0Y.

RetroArch uses project-owned udev autoconfig profiles for P1-P4 under
`data/games/retroarch/autoconfig/udev`. Baseline 45 proved project-relative
autoconfig only for a project-root launch; D-076R1 is authoritative for managed
launches and rewrites the generated Linux session config to the validated
absolute project-owned directory. The four pads must exist before RetroArch
initializes input.

D-076/R1/R2 are host-side managed-runtime validated. Full Android/onn E2E and
durable `/dev/uinput` service permission remain pending; production code must not
invoke `sudo`.

## D-076R1 managed RetroArch autoconfig-path correction

D-076 isolated runtime validation passed, but the first real managed RetroArch
probe exposed a session-path issue rather than a controller-mapping failure.
All four Linux uinput pads existed before launch and RetroArch selected the udev
joypad driver, but P1-P4 were reported `not configured`.

Fresh evidence established the cause: the persistent config kept the portable
relative setting `joypad_autoconfig_dir = "data/games/retroarch/autoconfig"`,
while EmulatorManager launches RetroArch with `cwd=executable.parent`. RetroArch
therefore resolved that relative path below the AppImage directory, where no
autoconfig profiles exist. The project-owned autoconfig directory itself was
present and contained all four D-076 profiles.

D-076R1 keeps the persistent config portable. On Linux, only the generated
per-launch session config rewrites the single validated project-relative
`joypad_autoconfig_dir` to its absolute project-owned path. Windows behavior,
PHI1, uinput mapping, Android, video/FEC, audio, and emulator process cwd remain
unchanged.

Authoritative current controller note: D-076R1 supersedes the Baseline-45 project-root relative-path assumption; the generated absolute project-owned autoconfig path passed managed runtime validation.

## D-076R2 missing `sys` import correction

The first D-076R1 managed RetroArch revalidation failed before RetroArch launch.
Linux controller preflight succeeded (`linux_uinput`, four players), but the new
D-076R1 session-config branch referenced `sys.platform` without importing the
standard-library `sys` module. Cleanup removed all virtual pads correctly.

D-076R2 adds only the missing top-level `import sys` to
`companion/games/emulator_manager.py`. The D-076R1 autoconfig path-resolution
logic, D-076 uinput backend/mapping, PHI1, Android, video/FEC, D-075R1 audio,
RetroArch persistent config/profiles, process cwd, and runtime descriptor are
unchanged.

Authoritative current controller note: D-076R2 supersedes the D-076R1 missing-import defect; managed RetroArch host validation passed. The probe final classifier was false only because it accepted `.state.png` and required the non-production controller `quit` chord; raw RetroArch/lifecycle evidence proves Save, Load, and graceful production End.

## D-077 Linux platform-aware RetroArch runtime selection

The tracked emulator descriptor keeps the validated Windows runtime/core mapping
as its base contract and may provide trusted host overrides under `platforms`.
On Linux, D-077 selects the project-owned RetroArch 1.22.2 AppImage,
`runtime/emulators/retroarch/cores-linux`, and the FCEUmm/bsnes/BlastEm/Beetle
PSX HW `.so` cores before readiness, core resolution, or launch.

The selector produces an effective config rather than status-only metadata;
`_resolve_game()` consumes that effective `systems` mapping. A malformed or
incomplete selected-platform override fails closed. Descriptors without a
platform override retain prior behavior. Windows base executable/core entries
remain unchanged.

After a successful D-077 installer run, the normal default `EmulatorManager`
path has passed a live read-only Linux readiness/selection probe. Full onn E2E
remains the next acceptance boundary.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:MEMORY:BEGIN -->
## Representative Linux transport result — idle Test A

The deferred 2026-09 UDP pathology is **reproduced on the representative
Linux + home Opal + onn path**.

Idle Linux -> onn synthetic UDP showed clean ~5 ms host pacing and zero missing
unique packets, yet Android received 2626 same-stamp duplicates on 3993 unique
packets and Android kernel timestamps showed severe burst/gap transformation
(p95 ~18.36 ms, max ~792 ms). Only 7 host `SndbufErrors` and zero
`RcvbufErrors` occurred.

Therefore:

- RetroArch/game load is not required;
- Android application scheduling is not the transformation boundary;
- production Linux socket-buffer failures are an amplification under load;
- the unresolved region remains the external network/radio/driver path between
  host send and Android kernel receive;
- do not normalize the duplicate rate as expected Wi-Fi behavior.

Next accepted discriminator is onn -> Linux idle reverse UDP using the preserved
reverse diagnostic.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:MEMORY:BEGIN -->
## Representative Linux transport — bidirectional result

The deferred UDP transport pathology is now reproduced **bidirectionally** on
the representative Linux + home Opal + onn environment while idle.

Test A, Linux -> onn:
- 3993 successful unique sends;
- 0 unique loss;
- 2626 same-stamp duplicate Android arrivals;
- severe burst/gap distortion already at Android kernel receive.

Test B, onn -> Linux:
- 4000/4000 Android sends successful;
- 3894 unique Linux arrivals;
- 106 unique packets missing;
- 476 same-stamp duplicates;
- severe receive burst/gap distortion;
- Linux sender-side `SndbufErrors` not involved in this reverse result.

Therefore the problem is not a Linux-only transmit implementation and does not
require RetroArch/native-stream load. The shared unresolved region is the
network infrastructure / endpoint radio-driver path. Production-stream socket
errors under game load are an amplification of an already abnormal idle path.

The next accepted localization step is router-side dual-boundary observation if
the home Opal exposes a usable packet-capture interface.

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:MEMORY:BEGIN -->
## Home Opal diagnostic access

On the representative Linux host, the Opal/default gateway is reachable on SSH
port 22. Batch authentication is not configured, so authenticated router
diagnostics require an interactive local login. Never ask the user to provide
the router password or gateway address; commands should discover the gateway
locally and prompt for credentials directly in SSH.

Router-side packet capture remains the next localization target after
bidirectional idle UDP reproduction.

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:MEMORY:BEGIN -->
## Opal SSH compatibility

The Opal SSH server currently offers only an `ssh-rsa` host key to the Linux
OpenSSH client. Modern OpenSSH does not include `ssh-rsa` in its default host-key
algorithm set, so router diagnostics must opt in per invocation with
`HostKeyAlgorithms=+ssh-rsa`.

This is host-key negotiation, not user public-key authentication. Keep the
compatibility exception local to the router diagnostic command; do not change
system-wide SSH policy.

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:MEMORY:BEGIN -->
## Opal authenticated diagnostics

Authenticated root SSH to the home Opal is available from the Linux host when
`ssh-rsa` is enabled only for that invocation. The router currently has `iw`
but not `tcpdump`. Its LAN bridge is `br-lan` and its wireless interfaces are
`wlan0` and `wlan1`.

Do not change router package/configuration state merely to continue diagnosis.
Inspect package-manager/feed compatibility and writable space first. If a
capture package is installed later, treat it as a temporary diagnostic change
and record/install/remove it explicitly.

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:MEMORY:BEGIN -->
## Opal capture topology

The home Opal LAN bridge `br-lan` contains `eth0.1`, `wlan0`, and `wlan1`.
`wlan0` is the 2.4-GHz AP (channel 1); `wlan1` is the 5-GHz AP (channel 40).

The router has `opkg`, `libpcap`, and ample overlay space, but no `tcpdump` and
no cached package indexes. An empty `opkg` cache does not prove package
unavailability. If package lookup is needed, use a temporary `opkg update` and
restore the prior empty list cache afterward before deciding whether to install
anything.

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:MEMORY:BEGIN -->
## Opal SSH invocation rule

For this Opal/OpenSSH combination, authenticated quoted remote commands are
validated. Supplying the remote script over SSH stdin/heredoc produced exit 255
and should not be used for diagnostics.

Validated per-command SSH requirements:

- `HostKeyAlgorithms=+ssh-rsa`;
- interactive password authentication locally;
- quoted remote command;
- no global SSH policy change.

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:MEMORY:BEGIN -->
## Opal radio mapping

On the representative home Opal, Linux is associated with `wlan0` and onn with
`wlan1`; both are bridged through `br-lan`. Both `tcpdump-mini` and `tcpdump`
are available from configured feeds.

Use the D080 dual-boundary probe to determine whether UTP1 duplication is
already present at the Linux-facing boundary, appears between Opal radio
boundaries, or only appears downstream of the onn-facing boundary.

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:MEMORY:BEGIN -->
## D080 classifier rule

A router boundary must never be described as clean unless the capture actually
contains substantial matching UTP1 traffic.

The first D080 run produced zero matched UTP1 packets on both Opal radio PCAPs,
so its downstream-of-router classification is invalid despite Android receiving
the test traffic.

D080R1 makes the analyzer fail closed for zero/insufficient router UTP1
coverage and exposes total PCAP record count/linktype to distinguish an empty
capture from a parser/link-layer mismatch.

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:MEMORY:BEGIN -->
## Empty Opal radio captures

The first D080 Opal radio captures were genuinely empty: both PCAPs were exactly
24-byte global headers with zero packet records while the synthetic endpoint
traffic was active.

This means:

- UTP1 parser/linktype mismatch is ruled out for that run;
- the per-radio libpcap/tcpdump observation boundary did not see the bridged
  traffic at all;
- no architectural localization may be inferred from those empty captures.

The leading *capture-blindness* hypothesis is Opal acceleration/fast-path
forwarding, but this is not yet established as the cause of UDP duplication.

Read acceleration/offload state before changing it.

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:MEMORY:BEGIN -->
## Opal acceleration state

Broken-path measured state: software flow offloading=1, hardware flow
offloading=1, with `sfhnat` and `cls_flow` loaded.

Do not infer causality from correlation. D081 is the controlled test: disable
both UCI offload flags temporarily, repeat D080, then restore exact prior state.

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:MEMORY:BEGIN -->
## Opal acceleration-off falsification

On the representative Opal, disabling both
`firewall.@defaults[0].flow_offloading` and
`flow_offloading_hw` did not fix the transport pathology and did not make
per-radio tcpdump see the bridged packets.

The test still produced thousands of Android duplicates plus unique loss, while
both router PCAPs remained 24-byte headers with zero records.

`sfhnat` remained loaded during the test.

Therefore:
- do not productize acceleration-off as a workaround;
- do not assume the GL.iNet/OpenWrt UCI switches control the full Siflower
  forwarding path;
- inspect Siflower vendor modules/control surfaces next.

The original acceleration state was restored to 1/1.

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:MEMORY:BEGIN -->
## Siflower vendor stack on Opal

The representative Opal is running a proprietary Siflower networking stack,
including both FMAC Wi-Fi drivers, RF support, Ethernet switch, netlink, and
HNAT modules:

`sf16a18_hb_fmac`, `sf16a18_lb_fmac`, `sf16a18_rf`, `sf_eswitch`,
`sfax8_factory_read`, `sfax8_netlink`, `sfhnat`.

`sfhnat` has no exposed module parameters on this firmware.

The first package-name probe was malformed and is not evidence. Determine
package ownership from the loaded module files directly before considering any
vendor-module experiment.

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:MEMORY:BEGIN -->
## Siflower module ownership and bridge-boundary rule

`sfhnat`, `sf_eswitch`, and `sfax8_netlink` are package-owned loadable vendor
modules. The FMAC/RF/factory side is more tightly coupled to the Wi-Fi stack.

Do not unload the FMAC/RF stack for transport diagnosis.

Before considering any vendor-module toggle, test visibility at `br-lan`.
D082 does exactly that with the existing UTP1 synthetic forward probe.

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:MEMORY:BEGIN -->
## Opal bridge capture is also blind

D082 proved `br-lan` tcpdump is header-only/zero-record during active
Linux->onn UTP1 traffic.

Therefore all tested ordinary Linux observation points are blind:
- `wlan0`;
- `wlan1`;
- `br-lan`.

Use D083 netdev counter deltas only as aggregate accounting evidence, not packet
identity evidence.

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:MEMORY:BEGIN -->
## D083 sampler lifetime rule

The first D083 run is invalid because the remote background sampler did not
persist long enough after the SSH setup session and the runner masked the
analyzer failure.

For SSH-launched finite background diagnostics on this Opal, explicitly detach
the process (`nohup`, stdin detached) and fail closed on minimum evidence and
analysis exit status.

Do not interpret the first D083 run as netdev accounting evidence.

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:MEMORY:END -->

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:MEMORY:BEGIN -->
## Diagnostic evidence discipline — D083 closeout

D083/D083R1 are invalid as networking evidence.

Durable rules reinforced by this incident:

1. Raw measurements override derived classifiers. The smoke probe printed
   `tmp_noexec=YES`, but `/proc/mounts` showed `/tmp` without `noexec`; the
   classifier is invalid.
2. Do not promote a diagnostic hypothesis to fact before the targeted probe
   confirms it. The claim that the original D083 sampler died specifically
   because its SSH session closed was not proven.
3. Preflight every external command used by old/minimal router firmware before
   building a diagnostic around it. This Opal/LEDE image has neither a `nohup`
   executable nor a BusyBox `nohup` applet.
4. Do not suppress startup stderr when process startup is the hypothesis under
   test.
5. Diagnostic runners must fail closed when collection or analysis fails.
6. Do not spend open-ended time reverse engineering a test-environment/vendor
   datapath unless the result has clear product-level value.

Last valid transport evidence is D082, not D083/D083R1.

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:MEMORY:END -->
