# PrivyHub / Safe IoT Project Roadmap — v2

**As of:** 2026-09-10
**Current checkpoint:** `e65e8f89604ce325e6e3e0537d0287070b8996c5`
**Checkpoint meaning:** Phase A emulator subsystem complete and pushed.

## 1. Project mission

PrivyHub is a local-first, privacy-preserving, modular smart-home and media
infrastructure experiment. The current prototype uses a Windows companion/server,
an inexpensive onn Android TV client, and an isolated secondary network. The
architecture is intended to evolve toward inexpensive Linux-capable server
hardware, additional clients, broader media/smart-home services, and optional
remote access without making cloud services, subscriptions, or proprietary
infrastructure mandatory.

The project develops incrementally:

```text
prove one narrow subsystem
        ↓
runtime-validate it
        ↓
preserve it as a stable boundary
        ↓
add the next modular capability
```

The local working tree remains authoritative between checkpoints. GitHub is the
checkpoint/history layer.

---

## 2. Current project position

| Phase | Purpose | Status |
|---|---|---|
| **A — Emulator Subsystem** | Finish Games/emulation as a normal-use subsystem | **COMPLETE / PUSHED** |
| **B — Diagnostics & Clean Native Baseline** | Make PrivyHub self-diagnosing, then remove Sunshine/Moonlight legacy | **NEXT** |
| **C — Adaptive Streaming Architecture** | Explicit profiles, dynamic bitrate/network adaptation, 1080p, generalized native streaming | **PLANNED** |
| **D — Media Library / VOD UX** | Poster art, metadata, recursive VOD presentation, local-first library polish | **PLANNED** |
| **E — Resource Scaling / Linux** | Benchmark the architecture, test inexpensive Linux tiers, capability scaling | **PLANNED** |
| **F — Open Platform / Firmware Portability** | Evaluate OpenBIOS and other open replacements without sacrificing compatibility | **OPTIONAL / PARALLEL AFTER B** |
| **G — Smart-Home & Client Expansion** | Cameras, devices, handhelds, remote PC gaming, broader home infrastructure | **FUTURE** |

The phase letters express the preferred development sequence. Phase F is
explicitly non-blocking and may be pulled forward when it is useful for Linux or
distribution work.

---

# Phase A — Emulator Subsystem

**Status: COMPLETE / CHECKPOINTED**

Checkpoint:

```text
e65e8f89604ce325e6e3e0537d0287070b8996c5
Checkpoint: complete Phase A emulator subsystem
```

Phase A established Games as a mature subsystem rather than a streaming proof of
concept.

## A1 — Controller / analog

**COMPLETE / RUNTIME VALIDATED**

Validated capabilities include:

- Android digital and analog controller state;
- persistent ViGEm/XInput devices on Windows;
- PHI1 full-state controller transport;
- analog-stick-to-D-pad convenience for appropriate systems;
- genuine PS1 analog behavior;
- four physical controller assignment;
- exact P1→1, P2→2, P3→3, P4→4 routing;
- RetroArch ports 1–4 through XInput;
- clean neutral release and teardown.

PHI1 remains version 1. The four-player extension did not require a protocol
format change.

## A2 — Save / Load

**COMPLETE / RUNTIME VALIDATED**

Includes:

- three save-state slots;
- slot metadata;
- stable game identity;
- persistent RetroArch save/state directories;
- SRAM/memory-card flush behavior;
- nonzero/stable savestate verification;
- actual load-result observation rather than acknowledgement-only success;
- cheat/mod profile isolation.

## A3 — Pause / Resume

**COMPLETE / RUNTIME VALIDATED**

Current user model:

```text
gameplay
   ↓ Back
freeze final frame
   ↓
pause RetroArch
stop A/V/FEC
   ↓
Game Session UI

click frozen frame
   ↓
native stream readiness
   ↓
resume RetroArch
   ↓
gameplay
```

Save, Load and End remain available from the paused session UI.

## A4 — Host coexistence / audio lifecycle

**COMPLETE / RUNTIME VALIDATED**

The onn can continue playing while the Windows host remains usable. Capture
targets the managed game window rather than requiring the emulator to dominate
the desktop. Game audio is process-specific.

## A5 — Direct launch

**COMPLETE / RUNTIME VALIDATED**

Normal library launch proceeds directly into native gameplay when readiness is
satisfied. Readiness failures fail closed rather than blindly resuming a broken
session.

## A6 — Library / metadata / game artwork

**COMPLETE / RUNTIME VALIDATED**

Includes:

- stable game IDs;
- system identification;
- game metadata;
- box-art/library presentation;
- search/organization;
- per-game save identity;
- user-content structure.

Artwork remains metadata/cache and never mutates canonical game content.

## A7 — Cheats / mods

**COMPLETE / RUNTIME VALIDATED**

Includes:

- provider-backed cheat catalogs;
- explicit cheat selection;
- persistent isolated cheat profiles;
- isolated save/state namespaces;
- managed mod profiles;
- deterministic IPS-derived ROM generation;
- hash verification;
- original ROM protection.

## A8 — Input profiles

**COMPLETE / RUNTIME VALIDATED**

Named PrivyHub-owned gameplay profiles support Players 1–4 while preserving the
known-good canonical controller transport.

Profile mapping is applied between canonical XUSB semantics and RetroArch
session bindings. Save/Load/Pause/End remain outside gameplay remapping.

## A9 — Emulator regression / checkpoint

**COMPLETE FOR AVAILABLE LIBRARY**

Final classification:

```text
PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS
```

Current runtime coverage:

- **SNES:** runtime exercised;
- **PS1:** extensively runtime exercised, including 1P/2P/4P, lifecycle,
  Save/Load, profiles, cheats, mods where applicable, and multitap;
- **NES:** supported/configured but no local game fixture was present;
- **Genesis:** supported/configured but no local game fixture was present.

NES and Genesis are **not** claimed runtime validated. When content is added for
either family, run that system's normal launch/input/teardown regression and
upgrade its status then.

## A10 — PS1 four-player topology

**COMPLETE / RUNTIME VALIDATED**

PrivyHub's supported PS1 local-player ceiling is four.

User-facing behavior:

```text
Multitap: Off
Multitap: On
```

`On` means:

```text
Beetle PSX HW Port 1 multitap = enabled
Beetle PSX HW Port 2 multitap = disabled
```

Port 2/Both are intentionally not product options.

Crash Bash and Crash Team Racing both validated four-player exposure and
independent P1–P4 gameplay.

## A11 — Wireless ADB build/install recovery

**COMPLETE / RUNTIME VALIDATED**

The build/install helper now tolerates transient paired-wireless-ADB discovery
loss through bounded recovery and a private last-known target cache outside the
repository. Network-bearing target values are not printed or committed.

---

# Phase B — Diagnostics & Clean Native Baseline

**Status: NEXT**

Phase B combines two related objectives:

1. make PrivyHub capable of explaining its own state and failures;
2. remove the obsolete Sunshine/Moonlight architecture with that observability
   available.

The diagnostics work comes first because every later phase becomes more dynamic
and harder to troubleshoot.

---

## B1 — Unified diagnostics substrate

**Status: NEXT**

PrivyHub already has substantial instrumentation, but it is spread across
subsystem-specific logs and probes. Consolidate it into a common diagnostic
contract.

Target architecture:

```text
Companion/service ─┐
Capture/source ────┤
Encoder ───────────┤
Transport/FEC ─────┤
Decoder ───────────┤
Audio ─────────────┤
Controllers ───────┤
Games/RetroArch ───┤
Media ─────────────┤
Android/client ────┤
ADB/tooling ───────┘
         ↓
PrivyHub diagnostic state/event model
         ↓
 ┌────────────────┬────────────────────┐
 │ GUI diagnostics│ local diagnostics  │
 │ / self-test    │ / support bundle   │
 └────────────────┴────────────────────┘
```

### B1 requirements

Define a stable structured diagnostic record containing, where appropriate:

- timestamp;
- session/run identifier;
- subsystem;
- severity;
- stable error/event code;
- human-readable summary;
- raw measurements;
- classifier/result;
- causal predecessor/reference;
- remediation hint;
- privacy classification.

Raw measurements and classifier conclusions must remain distinct. A classifier
must never overwrite contradictory measurements.

Example stable codes:

```text
GAME-LAUNCH-001
GAME-INPUT-003
VIDEO-CAPTURE-002
VIDEO-DECODE-007
AUDIO-SESSION-004
NET-LOSS-002
ADB-DISCOVERY-001
MEDIA-CATALOG-003
```

The exact taxonomy should be designed from current real failure classes, not
invented wholesale before inventorying existing instrumentation.

### B1.1 — Existing instrumentation inventory

Inventory the current:

- game diagnostics;
- decoder session JSON;
- native video logs;
- controller probes;
- save/state probes;
- transport probes;
- ADB recovery diagnostics;
- companion logs;
- Android stream diagnostics.

Classify each as:

- durable production telemetry;
- diagnostic probe;
- redundant;
- superseded;
- privacy-sensitive;
- candidate for the unified model.

### B1.2 — Health snapshot

Add one machine-readable current health snapshot covering major subsystems.

Conceptual output:

```text
Companion            HEALTHY
Capture              HEALTHY
Encoder              NVENC / 720p60
Transport            HEALTHY
Decoder              HARDWARE AVC / HEALTHY
Audio                HEALTHY
Controllers          4 / 4
Game session         ACTIVE
RetroArch            HEALTHY
Last error           NONE
```

The underlying representation should be structured JSON. Human-readable text is
a presentation layer.

### B1.3 — Diagnostic event history

Maintain a bounded local event/ring history rather than unbounded logging.

Important events include:

- capture readiness changes;
- encoder start/reconfigure/failure;
- transport loss/recovery;
- FEC recovery/unrecoverable loss;
- decoder starvation/stale drops;
- audio start/stop/failure;
- controller attach/assign/drop;
- RetroArch lifecycle;
- save/load verification;
- companion/API failure;
- ADB recovery state.

No network addresses should be required in ordinary diagnostics.

---

## B2 — GUI Diagnostics / Self-Test

Expose the diagnostics substrate through the onn GUI without making the GUI the
only way to access it.

Potential Diagnostics page:

```text
SYSTEM
  Companion                 Healthy
  Native streaming          Healthy
  Network path              Good
  Last session error        None

CURRENT STREAM
  Source                    Game
  Resolution                1280x720 @ 60
  Encoder target            7 Mbps
  Recent wire rate          ~8 Mbps
  Packet loss               0.0%
  FEC recoveries            2
  Unrecoverable groups      0
  Stale video drops         0

GAME
  RetroArch                 Running
  Controllers               4
  XInput slots              1,2,3,4
```

The 7 Mbps encoder target and roughly 8 Mbps observed network rate are not
contradictory: 8+1 FEC and protocol overhead raise wire traffic above the encoded
video target.

### B2.1 — Self-test

Provide bounded, non-destructive checks for:

- companion reachability;
- control API;
- native stream readiness;
- decoder availability;
- audio path;
- controller bridge;
- emulator/runtime prerequisites;
- storage writability;
- ADB/development tooling when applicable.

A self-test should classify what it actually measured and avoid changing
production state unless the user explicitly asks.

### B2.2 — One-click sanitized diagnostics bundle

From GUI and/or companion tooling:

```text
Collect Diagnostics
        ↓
sanitized bundle
        ↓
summary + machine-readable measurements
```

The bundle should:

- automatically redact/exclude addresses and secrets;
- include a manifest and hashes;
- include relevant bounded recent telemetry;
- identify software/runtime versions;
- identify the failing subsystem when evidence supports it;
- remain useful without access to any chat history.

This becomes the preferred support/debug handoff.

---

## B3 — Sunshine / Moonlight dependency inventory

**Status: PENDING AFTER B1/B2 FOUNDATION**

Do not begin by deleting files.

Audit the exact current tree for:

- Sunshine/Moonlight services/process assumptions;
- firewall rules;
- scheduled tasks;
- install/setup/removal scripts;
- Android package queries;
- Android intents;
- `StreamManager` or legacy streaming classes;
- Games plugin references;
- status/UI remnants;
- portable runtime/configuration;
- documentation that describes obsolete active behavior.

Classify every occurrence as:

```text
ACTIVE DEPENDENCY
DEAD COMPATIBILITY CODE
INSTALL/UNINSTALL ARTIFACT
DOCUMENTATION/HISTORY
SAFE TO REMOVE
MUST PRESERVE
```

---

## B4 — Remove legacy streaming infrastructure

Make one coherent removal series based on B3 evidence.

Do not disturb the stable native paths:

- Windows Graphics Capture;
- NVENC;
- native audio;
- UDP/FEC video transport;
- Android hardware decoder;
- PHI1/ViGEm controllers;
- game lifecycle/meta controls.

Remove Sunshine/Moonlight only where native PrivyHub has already superseded it.

---

## B5 — Native-only regression

Prove Games independently after legacy removal:

```text
library launch
   ↓
native capture/encode/transport/decode
   ↓
audio
   ↓
controller input
   ↓
pause/resume
   ↓
Save/Load
   ↓
cheat/mod/profile path
   ↓
End/teardown
```

This should be a focused dependency-removal regression, not a full repeat of
every Phase A exploratory diagnostic.

---

## B6 — Clean-native checkpoint

Acceptance:

- unified diagnostics substrate established;
- GUI/self-test path usable;
- sanitized diagnostic bundle available;
- Sunshine/Moonlight active dependencies removed;
- native Games regression passes;
- repository audit clean;
- checkpoint/push.

At this point the architectural statement should be:

> PrivyHub native streaming is the only active Games streaming architecture.

---

# Phase C — Adaptive Streaming Architecture

**Status: PLANNED**

Phase C turns the current proven game streamer into a reusable, measurable,
adaptive native streaming platform.

---

## C1 — Explicit stream profiles

Convert implicit constants into named, inspectable profiles.

Current validated reference:

```text
Profile: Native Game 720p60
Capture: 1280x720 @ 60
Codec: H.264
Encoder: NVENC
Encoder target: ~7 Mbps
Latency mode: P1 / ultra-low-latency
GOP: 15
B-frames: none
Transport: RTP-sized UDP
FEC: 8 data + 1 XOR parity
```

The profile system should separate:

- capture resolution/framerate;
- codec/encoder;
- bitrate bounds;
- GOP;
- latency tuning;
- FEC policy;
- audio policy;
- source type.

Do not make one universal profile for every source.

---

## C2 — End-to-end transport telemetry contract

Adaptive behavior must be driven by the actual path, not assumptions about the
router.

For local streaming:

```text
PC/server
   ↓
GL-iNet / isolated LAN / Wi-Fi
   ↓
onn/client
```

The relevant capacity is the real **LAN/Wi-Fi end-to-end path**. The router's
Internet/WAN speed is not the limiting variable for a local stream.

For future remote streaming, WAN capacity and Internet path behavior become
additional constraints.

Measure or derive:

- recent delivered bitrate/goodput;
- packet loss;
- FEC recoveries;
- unrecoverable FEC groups;
- packet inter-arrival jitter;
- RTT/echo latency where useful;
- sender pacing;
- queue/buffer growth indicators;
- decoder starvation;
- decoder stale drops;
- rendered-frame continuity.

Instrumentation from B should make every adaptation decision explainable.

---

## C3 — Adaptive bitrate controller

**Primary dynamic-network feature**

The first adaptive implementation should change **bitrate only** while holding
resolution and 60 fps stable.

Conceptual behavior:

```text
path degrades
    ↓
reduce target bitrate quickly
    ↓
protect latency / continuity

path remains healthy
    ↓
raise bitrate slowly
    ↓
recover image quality
```

Required control properties:

- bounded minimum and maximum bitrate;
- fast decrease / slow increase;
- hysteresis;
- hold-down period after congestion;
- no oscillation around thresholds;
- explicit reason for each change;
- fail-safe return to a known profile;
- source-specific bounds.

NVENC supports runtime encoder reconfiguration for bitrate control, but the
PrivyHub implementation must still validate that its current encoder wrapper and
session lifecycle expose that behavior safely.

### C3 acceptance

Under controlled impairment:

- congestion causes bitrate reduction before prolonged decode starvation;
- queue/stale-frame behavior improves or remains bounded;
- gameplay remains responsive;
- bitrate recovers gradually after the path stabilizes;
- adaptation decisions are visible in diagnostics;
- healthy-network behavior does not regress.

---

## C4 — Adaptive FEC policy

Only after dynamic bitrate is stable.

Possible later control:

```text
clean path        → lower FEC overhead
lossy path        → stronger bounded FEC
severe congestion → lower bitrate first; do not blindly add parity
```

FEC adaptation must distinguish random packet loss from congestion. Adding more
parity during a capacity shortage can worsen the shortage.

Do not change bitrate and FEC simultaneously in the first experiment unless the
individual effects are already measurable.

---

## C5 — 1080p60 profile and capability test

Test the existing Windows/GTX 970 reference system and onn decoder.

Measure:

- encoder utilization;
- host CPU/GPU;
- bitrate requirements;
- packet behavior;
- latency;
- decoder queue/render behavior;
- thermal/stability behavior;
- visual quality.

1080p60 should become a capability-gated profile, not an assumption that every
future host/client can sustain it.

---

## C6 — Generalized native source abstraction

Once Games streaming is clean and observable:

```text
Game window ───────┐
Browser/app ───────┤
Camera/live source ├→ Source/Capture abstraction
Other source ──────┘
                         ↓
                 Native encoder/profile
                         ↓
                  Transport / FEC
                         ↓
                    Client decoder
```

Shared infrastructure may include:

- session lifecycle;
- transport;
- decoder;
- diagnostics;
- profile selection;
- adaptation.

Source-specific behavior may still differ:

- latency target;
- capture API;
- audio source;
- buffering;
- resolution;
- bitrate;
- FEC.

The goal is reuse, not forced uniformity.

---

## C7 — Streaming architecture checkpoint

Acceptance:

- explicit profiles;
- transport telemetry;
- adaptive bitrate validated;
- adaptive FEC decision either validated or explicitly deferred;
- 1080p60 characterized;
- generalized native source contract established;
- Games remains stable;
- checkpoint/push.

---

# Phase D — Media Library / VOD UX

**Status: PLANNED**

This phase improves locally stored media without making metadata services a
playback dependency.

---

## D1 — Recursive VOD artwork

Apply game-library-style visual organization to movies under:

```text
media/vod/
```

including subdirectories.

Support local sidecar conventions such as:

```text
Movie Name (Year).mkv
Movie Name (Year).jpg
```

and directory-oriented layouts such as:

```text
Movie Name (Year)/
    Movie Name (Year).mkv
    poster.jpg
```

Suggested local-art priority:

1. exact `<video-stem>.jpg/.png/.webp`;
2. `poster.jpg/.png/.webp`;
3. `folder.jpg/.png/.webp`;
4. cached metadata-provider poster;
5. generated local frame thumbnail;
6. generic VOD tile.

Do not rewrite or relocate canonical media merely to obtain artwork.

---

## D2 — VOD metadata cache

Potential fields:

- title;
- year;
- runtime;
- genre;
- description;
- poster;
- resolution;
- video codec;
- audio format/language;
- subtitle availability.

External metadata lookup should be optional. Once acquired, useful metadata and
art should be cached locally so normal browsing/playback remains local-first.

Ambiguous matches must be reviewable rather than silently attaching incorrect
metadata.

---

## D3 — Playback-state UX

Potential later additions:

- resume position;
- watched/unwatched;
- recently played;
- favorites;
- collections/series;
- sort/filter/search;
- per-user state if a future multi-user model requires it.

Keep these as metadata/state layers; canonical media files remain untouched.

---

## D4 — Media-library checkpoint

Acceptance:

- recursive VOD discovery remains stable;
- local artwork works without Internet;
- optional metadata lookup fails gracefully;
- cached metadata survives provider unavailability;
- browsing remains responsive on the onn;
- checkpoint/push.

---

# Phase E — Resource Scaling / Linux

**Status: PLANNED**

Do formal hardware sizing only after diagnostics and streaming behavior are
explicit enough to benchmark meaningfully.

---

## E1 — Representative workload suite

Build a repeatable suite from the mature architecture.

Candidate workloads:

```text
720p60 game streaming
adaptive 720p60 under impairment
1080p60 streaming
VOD serving
camera/live source streaming
multiple background services
concurrent media + smart-home activity
```

Each workload should have pass/fail and measurement criteria.

---

## E2 — Windows reference benchmark

The current Windows machine becomes the reference implementation.

Measure:

- CPU;
- GPU;
- hardware encoder load;
- RAM;
- storage I/O;
- network goodput/loss/jitter;
- server event-loop/service load;
- client decode behavior;
- latency/stability;
- concurrent workload behavior.

This establishes what the architecture costs before hardware substitution.

---

## E3 — Cheap Linux-capable host tiers

Test inexpensive Linux-capable systems empirically.

Do not start with arbitrary product tiers. Derive them from measurements.

Possible resulting model:

```text
Tier A
  local services
  VOD
  720p60 where hardware encode permits

Tier B
  broader 720p60 / selected 1080p
  media + smart-home concurrency

Tier C
  stronger 1080p / heavier concurrent workload
  optional modern PC relay functions
```

A CPU-only host may still be useful even if it cannot replace the game encoder.
Capabilities should be modular.

---

## E4 — Capability detection / scaling

PrivyHub should eventually probe:

- CPU architecture/performance class;
- RAM;
- GPU/iGPU;
- encoder availability;
- decoder availability where relevant;
- storage;
- network interfaces/path;
- supported profiles;
- measured benchmark class.

Then:

```text
hardware probe
    ↓
capability profile
    ↓
enabled PrivyHub features / stream profiles
```

The product should degrade gracefully rather than assuming one development PC.

---

## E5 — Linux service migration

Migrate companion/server responsibilities incrementally.

Preserve platform-neutral contracts:

- source catalog;
- control API;
- session lifecycle;
- diagnostics schema;
- transport;
- metadata;
- storage layout;
- capability model.

Keep Windows-only capture/encoder modules isolated behind interfaces rather than
forcing them into Linux.

---

## E6 — Replay deferred UDP acceptance suite

Replay the saved forward/reverse transport diagnostics on representative Linux
and network hardware.

Compare:

- sender pacing;
- burst/gap behavior;
- Android kernel arrival;
- loopback;
- reverse path;
- duplicate arrival;
- packet loss/jitter;
- FEC;
- decoder starvation/stale drops.

Only then decide whether the earlier pathology was:

- specific to the Windows/USB-Wi-Fi test environment;
- general consumer-network behavior;
- or an architectural transport issue.

Do not encode a quirk of the original test environment into the product without
representative evidence.

---

## E7 — Linux/resource checkpoint

Acceptance:

- representative workloads defined;
- Windows reference measured;
- at least one inexpensive Linux tier tested;
- capability profile implemented or concretely specified;
- deferred transport question replayed where representative;
- next hardware target selected from evidence;
- checkpoint/push.

---

# Phase F — Open Platform / Firmware Portability

**Status: OPTIONAL / PARALLEL AFTER B**

This track reduces proprietary dependencies where doing so improves portability,
distribution, inspectability, or control **without sacrificing validated
compatibility**.

It is not a requirement to replace a working proprietary component merely
because an open alternative exists.

---

## F1 — PS1 OpenBIOS evaluation

Current Beetle PSX HW supports PCSX-Redux OpenBIOS as a region-free BIOS path.
OpenBIOS is open source and can be inspected/customized, making it attractive
for a portable/local-first system.

Potential benefits:

- freely redistributable/open firmware path;
- region-free behavior;
- source-level inspectability;
- reproducible builds;
- debugging symbols/development visibility;
- possible custom boot/diagnostic behavior;
- easier appliance-style deployment where a user-supplied retail BIOS would
  otherwise be required.

### What OpenBIOS is not

Do **not** treat OpenBIOS as a game-performance optimization.

The BIOS is primarily boot/runtime firmware support; replacing it is unlikely to
materially improve normal game frame rate or PrivyHub streaming latency.
OpenBIOS also has known compatibility exceptions, so a global replacement would
violate the preserve-working-path rule.

---

## F2 — OpenBIOS audit before implementation

First determine the exact current Beetle behavior:

- whether the active core already carries/falls back to an internal OpenBIOS;
- which BIOS is actually selected in current PrivyHub sessions;
- how the core's BIOS override option interacts with external firmware;
- current known compatibility exceptions;
- save/memory-card behavior;
- region behavior;
- boot timing;
- interaction with game-specific core options.

Do not assume that dropping an arbitrary external `openbios.bin` into the system
directory is equivalent to the current core's internal/fallback behavior.

---

## F3 — Optional BIOS mode

If the audit is favorable, expose something like:

```text
PS1 BIOS
  Compatibility / Existing
  OpenBIOS
```

Potential later extension:

```text
per-game BIOS override
```

Rules:

- existing known-good BIOS path remains available;
- OpenBIOS never silently replaces the compatibility path;
- incompatible titles can fall back;
- selected OpenBIOS build is versioned and hashed;
- any customized build is reproducible;
- normal save/memory-card namespaces remain stable.

---

## F4 — Custom OpenBIOS experiment

Only after stock OpenBIOS compatibility is characterized.

Possible experiments:

- faster/simpler boot presentation;
- PrivyHub-branded boot screen;
- diagnostic boot information;
- development hooks;
- instrumentation useful to emulator research.

Customization should remain optional and should not turn PrivyHub into a fork
that is difficult to update.

---

## F5 — Broader open-dependency audit

As Linux/appliance work progresses, review major dependencies for:

- redistribution;
- licensing;
- architecture support;
- offline operation;
- source availability;
- maintenance activity;
- hardware lock-in.

Replace dependencies only when there is a practical architectural benefit.

---

# Phase G — Smart-Home & Client Expansion

**Status: FUTURE / SEQUENCE INTENTIONALLY FLEXIBLE**

Once the native server/client foundation is observable, portable and scalable,
expand PrivyHub beyond the current TV/games focus.

Candidate tracks:

## G1 — Camera infrastructure

- local camera discovery/registration;
- live native streaming through the generalized source layer;
- local recording;
- retention policy;
- motion/event metadata;
- no mandatory vendor cloud.

## G2 — Smart-home devices

- lights;
- switches;
- sensors;
- other isolated-IoT controls;
- local automation rules;
- explicit device permissions/capabilities.

## G3 — Local storage / media server

- larger VOD/DVD library;
- indexed local storage;
- remote streaming where explicitly enabled;
- no subscription dependency.

## G4 — Remote access

Add secure remote use without making external connectivity mandatory.

Possible targets:

- VOD;
- cameras;
- home controls;
- game sessions.

Remote transport/security should be designed after the local architecture is
stable and measurable.

## G5 — Existing PC modern-game relay

A future optional plugin can use the existing gaming PC as a source while
PrivyHub remains the control/transport/security layer:

```text
PC game
   ↓
PrivyHub capture/stream source
   ↓
PrivyHub server/network policy
   ↓
onn / handheld client
```

This preserves modern PC gaming without requiring the inexpensive Linux server
itself to render the game.

## G6 — Handheld client

Evaluate inexpensive handheld hardware as another PrivyHub client:

- Linux or Android;
- built-in display/controllers;
- optional TV/dock output;
- same source catalog/session concepts;
- hardware capability-driven decoding;
- no separate incompatible ecosystem.

The current onn client remains useful even if additional client classes emerge.

---

# Cross-cutting architecture rules

These apply to every phase.

## Diagnostics first

When behavior is uncertain:

```text
one narrow hypothesis
      ↓
one targeted diagnostic/probe
      ↓
fresh evidence
      ↓
inspect raw measurements
      ↓
one coherent patch
```

Production features that become dynamic should expose why they changed state.

## Preserve validated paths

Do not disturb stable video/audio/controller/storage behavior for unrelated work.

## Local-first

Normal functionality should not require:

- cloud availability;
- a subscription;
- a metadata provider;
- remote authentication;
- proprietary control infrastructure.

Optional Internet features should cache/use graceful local fallback.

## Privacy

Do not require network addresses in routine support workflows. Diagnostics and
checkpoint evidence should exclude/redact addresses and secrets.

## Data/source-control boundary

Git contains:

- source;
- configuration;
- durable engineering memory;
- reusable diagnostics;
- curated evidence;
- sanitized checkpoint evidence snapshots.

Git does not contain normal:

- ROMs/ISOs;
- saves/states;
- media libraries;
- runtime emulator trees;
- logs;
- packet captures;
- private network-bearing state;
- build output;
- backups.

## Capability-driven architecture

Avoid embedding assumptions about the current Windows PC, current Wi-Fi adapter,
current router, or onn model into the core architecture.

## Fail closed

If readiness, identity, save integrity, capture scope, or other safety-sensitive
preconditions cannot be established, preserve the session/data rather than
blindly proceeding.

## Checkpoint discipline

At each meaningful milestone:

- update `docs/memory/`;
- preserve runtime evidence;
- run deterministic validation;
- create a clean checkpoint;
- push only after the local authoritative state is proven.

---

# Immediate development sequence

The preferred next sequence is:

```text
e65e8f8 Phase A checkpoint
        ↓
B1 inventory existing diagnostics
        ↓
B1 unified diagnostic schema + health snapshot
        ↓
B2 GUI Diagnostics / Self-Test / sanitized bundle
        ↓
B3 Sunshine/Moonlight dependency inventory
        ↓
B4 legacy removal
        ↓
B5 native-only regression
        ↓
B6 clean-native checkpoint
        ↓
C1 explicit stream profiles
        ↓
C2 transport telemetry contract
        ↓
C3 adaptive bitrate
        ↓
C4 adaptive FEC decision
        ↓
C5 1080p60 characterization
        ↓
C6 generalized source abstraction
        ↓
C7 streaming checkpoint
        ↓
D VOD/media-library UX
        ↓
E Linux/resource scaling
        ↓
G broader smart-home/client expansion
```

Phase F/OpenBIOS may run in parallel after Phase B when it helps portability,
distribution, or Linux preparation, but it should not block the main sequence.

---

# Near-term decision gates

## Gate 1 — Diagnostics architecture

Before coding B1, answer:

- what existing telemetry should become permanent;
- what the common diagnostic schema is;
- what belongs in GUI vs developer detail;
- what self-test can safely exercise;
- what a sanitized bundle must contain.

## Gate 2 — Adaptive bitrate telemetry

Before coding C3, prove that the measurements selected in C2 can distinguish:

- healthy path;
- capacity pressure;
- random loss;
- burst/jitter pathology;
- decoder-side starvation.

Do not tune bitrate from one noisy metric.

## Gate 3 — VOD metadata scope

Before optional Internet metadata integration, make local sidecar artwork and
recursive library behavior work completely offline.

## Gate 4 — OpenBIOS

Before changing BIOS behavior, compare the current compatibility path and
OpenBIOS using an explicit game/boot/save regression matrix. OpenBIOS remains an
option until evidence justifies any broader default.

## Gate 5 — Linux target selection

Do not buy/design around a final cheap Linux host until the benchmark suite
exists. Let workload measurements determine the hardware tier.
