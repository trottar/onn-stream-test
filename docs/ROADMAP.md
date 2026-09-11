# PrivyHub / Safe IoT Roadmap — Merged Linux-First Revision

**Draft date:** 2026-09-11
**Predecessor implementation checkpoint:** Phase B clean-native checkpoint `ae616352897d418360dc740ef37343ea72e88098`
**Roadmap status:** Accepted project plan. Phase C is the active next phase.

---

## 1. Current project position

| Phase | Purpose | Status |
|---|---|---|
| **A — Emulator Subsystem** | Finish Games/emulation as a normal-use subsystem | **COMPLETE / PUSHED** |
| **B — Diagnostics & Clean Native Baseline** | Make PrivyHub self-diagnosing and remove active Sunshine/Moonlight legacy | **COMPLETE / PUSHED** |
| **C — Adaptive Streaming Architecture** | Explicit profiles, telemetry, adaptive bitrate/FEC, 1080p characterization, generalized native streaming | **NEXT** |
| **D — Media Library, VOD & Live TV UX** | Local media polish plus a substantial Live TV/channel/guide rebuild | **PLANNED** |
| **E — Linux Migration / Native Linux Baseline** | Move the core server to the HP EliteDesk Linux prototype and restore normal-use parity | **PLANNED** |
| **F — Linux Core Resource Characterization & Optimization** | Optimize and measure the Linux core with PS1-and-below only; select Prototype 2 from evidence | **PLANNED** |
| **G — Extended Emulation & User-Content Import** | Build safe user-content ingestion, then characterize N64, GameCube, and PS2 | **FUTURE AFTER F** |
| **H — Home Infrastructure / Client / Plugin Expansion** | Handhelds, Home Assistant/devices, cameras/microphones, storage, remote access, Steam/external compute | **FUTURE** |
| **I — Local Intelligence / Voice / Privacy-Aware AI** | Deterministic local automation, small local models, optional user-supplied cloud AI providers, bounded adaptive optimization | **FUTURE** |

### Retired roadmap item

The former OpenBIOS/Open Platform phase is removed from the main roadmap.

PrivyHub will not provide, download, redistribute, or silently substitute ROMs,
ISOs, BIOS/firmware, keys, or equivalent copyrighted/proprietary game content.

Where an emulator requires user-provided firmware/content, PrivyHub will provide
safe import/integration tooling instead.

Open/local dependencies remain an architectural preference when they provide a
practical benefit, but there is no dedicated OpenBIOS phase or Track O.

---

# Phase A — Emulator Subsystem

**Status: COMPLETE / PUSHED**

The existing Phase A implementation and evidence remain authoritative.

Core validated architecture includes:

- NES/SNES/Genesis/PS1 scope;
- RetroArch-managed emulator lifecycle;
- saves/states;
- cheats/mod profiles;
- input profiles;
- four-controller architecture;
- PS1 Port-1 multitap behavior;
- local metadata/art;
- normal End/teardown;
- native PrivyHub streaming/client path.

Do not reopen Phase A unless later platform migration produces new evidence.

---

# Phase B — Diagnostics & Clean Native Baseline

**Status: COMPLETE / PUSHED**

Checkpoint:

```text
ae616352897d418360dc740ef37343ea72e88098
```

Phase B established:

- unified health/diagnostic model;
- event history;
- Self-Test;
- GUI diagnostics;
- sanitized support bundle;
- retention controls;
- Android/client health feedback;
- Sunshine/Moonlight dependency inventory and removal;
- removal of the Moonlight Android package;
- native-only Games regression;
- clean repository/build checkpoint.

Architectural statement:

> PrivyHub native streaming is the only active Games streaming architecture.

---

# Phase C — Adaptive Streaming Architecture

**Status: NEXT**

Phase C turns the current proven native game stream into a reusable, measurable,
adaptive streaming platform.

The current Windows/GTX 970 system remains a valid development/reference host
for this phase because Linux migration has not happened yet. Measurements here
are intended to validate streaming architecture and client capability, **not**
to establish the eventual Linux minimum hardware requirement.

## C1 — Explicit stream profiles

Convert current hard-coded behavior into named, inspectable profiles without
changing the validated 720p60 behavior.

Reference profile:

```text
Native Game 720p60
1280x720 @ 60
H.264
NVENC
~7 Mbps target
P1 / ultra-low-latency
GOP 15
no B-frames
RTP-sized UDP
8 data + 1 XOR parity
```

Profiles should separate:

- capture resolution/framerate;
- codec/encoder;
- bitrate bounds;
- GOP;
- latency tuning;
- FEC policy;
- audio policy;
- source type.

## C2 — End-to-end transport telemetry contract

Formalize the measurements that future adaptation consumes:

- delivered bitrate/goodput;
- packet loss;
- FEC recoveries;
- unrecoverable groups;
- jitter/inter-arrival behavior;
- RTT/echo latency where useful;
- sender pacing;
- queue/buffer growth;
- decoder starvation;
- stale-frame drops;
- rendered-frame continuity.

Every adaptation decision must be explainable from recorded measurements.

## C3 — Adaptive bitrate

Change bitrate first while keeping resolution and 60 fps fixed.

Required behavior:

- bounded min/max;
- fast decrease / slow increase;
- hysteresis;
- congestion hold-down;
- no rapid oscillation;
- explicit diagnostics/reason codes;
- safe fallback to a known profile.

## C4 — Adaptive FEC

Only after bitrate adaptation is stable.

Distinguish random packet loss from capacity pressure. Do not blindly increase
parity during congestion.

If fixed 8+1 remains the better engineering choice, explicitly defer dynamic FEC
with evidence rather than adding complexity for its own sake.

## C5 — 1080p60 capability characterization

Characterize 1080p60 using the current development host and onn client.

This is a **stream/client capability test**, not a future Linux resource-sizing
benchmark.

1080p60 should become capability-gated rather than universally assumed.

## C6 — Generalized native source abstraction

Create reusable boundaries for:

```text
source/capture
    ↓
profile/encoder
    ↓
transport/FEC
    ↓
client decoder
```

Games, browser/app, cameras/live sources, and later sources may share lifecycle,
transport, diagnostics, profile selection, and adaptation while preserving
source-specific capture/audio/buffering requirements.

## C7 — Phase C checkpoint

Acceptance:

- explicit profiles;
- transport telemetry contract;
- adaptive bitrate runtime validated;
- adaptive FEC validated or explicitly deferred;
- 1080p60 characterized;
- generalized source contract established;
- Games regression passes;
- clean checkpoint/push.

---

# Phase D — Media Library, VOD & Live TV UX

**Status: PLANNED**

Phase D now covers both local media-library polish and a deliberate Live TV
cleanup/rebuild.

The existing Live TV playback path should be preserved where it is stable, but
the current channel organization and guide behavior should **not** be treated as
finished architecture.

## D1 — Recursive VOD artwork

Support local sidecar art and directory-oriented movie layouts without rewriting
canonical media.

Priority may include:

1. exact video-stem artwork;
2. `poster.*`;
3. `folder.*`;
4. cached provider art;
5. generated local thumbnail;
6. generic tile.

## D2 — VOD metadata cache

Potential fields:

- title/year/runtime;
- genre/description;
- poster;
- resolution/codecs;
- audio/subtitle information.

External lookup remains optional and cacheable. Normal browsing/playback must
remain local-first.

## D3 — Playback-state UX

Potential layers:

- resume position;
- watched/unwatched;
- recently played;
- favorites;
- collections/series;
- sort/filter/search;
- future per-user state.

Canonical media files remain untouched.

## D4 — Live TV channel normalization

Treat the current channel catalog as data that needs normalization rather than
as a finished list.

Goals:

- stable canonical channel identity;
- duplicate detection/merging;
- consistent display names;
- group/category normalization;
- source/provider provenance;
- hidden-channel state that remains recoverable;
- favorites;
- search/filter;
- deterministic sorting;
- pagination that behaves like pagination rather than artificial channel-number
  groups;
- graceful handling of dead/unavailable streams.

Do not bind user state to unstable provider ordering.

## D5 — EPG / guide foundation

Rebuild the guide around explicit identity/matching rather than best-effort UI
assumptions.

Required areas:

- XMLTV/provider ingestion where used;
- channel matching using stable IDs first and normalized-name fallback second;
- timezone handling;
- program start/end normalization;
- cache/refresh policy;
- stale-data behavior;
- no-guide fallback;
- diagnostics explaining unmatched channels;
- deterministic handling of multiple candidate matches.

The guide must remain optional to basic channel playback.

## D6 — Live TV guide UX

Once the underlying EPG data is trustworthy:

- current/next program;
- timeline/grid view where practical;
- channel details;
- jump to current time;
- category/favorites filters;
- clear "guide unavailable" behavior;
- responsive onn-TV navigation.

Do not hide data-quality failures behind empty UI.

## D7 — Media/TV checkpoint

Acceptance:

- recursive VOD library remains stable;
- metadata/art work offline after caching;
- Live TV channel list is normalized and manageable;
- guide matching/refresh behavior is diagnosable;
- normal channel playback does not depend on guide success;
- checkpoint/push.

---

# Phase E — Linux Migration / Native Linux Baseline

**Status: PLANNED AFTER D**

Prototype 1 Linux server:

```text
HP EliteDesk 805 G6 Mini
Ryzen 5 PRO 4650G
16 GB RAM
256 GB NVMe
```

The system was intentionally purchased with more headroom than the expected
PS1-and-below requirement so migration can be separated from minimum-hardware
optimization.

Windows installed on the machine is not a project target.

## E1 — Linux appliance baseline

Select and install a stable Linux base with:

- minimal unnecessary services;
- reproducible packages/runtime;
- local-first networking;
- predictable PrivyHub service ownership;
- clean boot/start/stop;
- current data/source-control boundaries;
- diagnostics from the beginning.

Record hardware details relevant to later measurement, including RAM topology,
storage, firmware, thermals, and network interfaces.

## E2 — Migrate platform-neutral companion responsibilities

Preserve established contracts:

- source catalog;
- control API;
- session lifecycle;
- diagnostics/events;
- game identity;
- save/state ownership;
- user-content boundaries;
- plugin/provider contracts;
- capability reporting.

Linux should replace implementation details without needlessly changing these
contracts.

## E3 — Replace Windows-specific backends

Replace behind explicit platform boundaries:

```text
Windows Graphics Capture → Linux capture backend
NVENC                   → generic encoder API + Linux AMD hardware path
WASAPI process audio     → Linux source/process audio
ViGEm                    → Linux virtual input/uinput/evdev path
Windows lifecycle        → Linux service/process lifecycle
```

Preserve behavior, not Windows APIs.

## E4 — Restore PS1-and-below Games on Linux

Required scope:

```text
NES
SNES
Genesis
PS1
```

Preserve:

- discovery/launch;
- video/audio/input;
- four-player architecture where applicable;
- PS1 multitap behavior;
- saves/states;
- pause/resume;
- cheats/mod profiles;
- input profiles;
- metadata/art;
- teardown/recovery.

## E5 — Restore media/server functionality

Migrate the post-Phase-D server functions without broadening scope:

- companion/control API;
- VOD;
- Live TV/EPG;
- browser/live source where active;
- camera source where active;
- diagnostics/Self-Test;
- Phase C profile/adaptation infrastructure;
- Phase D media state/cache.

## E6 — Replay deferred UDP investigation

Rerun the saved forward/reverse transport acceptance suite on the representative
Linux host.

Classify whether the prior packet timing/duplication pathology was:

- specific to the old Windows/test environment;
- reproduced on the new representative host/network path;
- or indicative of a broader transport issue.

Do not reopen beyond evidence.

## E7 — Native Linux regression

Minimum normal-use regression:

```text
server boot/start
client discovery/control
media
Games launch
video/audio/controller
pause/resume
Save/Load
profiles/cheats/mod state
End/teardown
restart/recovery
```

## E8 — Linux baseline checkpoint

Acceptance:

- Linux is sufficient for normal core server operation;
- PS1-and-below works through Linux-native A/V/input paths;
- onn client remains functional;
- media/Live TV remain functional;
- deferred UDP suite replayed/reclassified;
- no minimum-hardware claim yet;
- clean checkpoint/push.

Architectural statement:

> PrivyHub has a working Linux-native core suitable for formal resource characterization.

---

# Phase F — Linux Core Resource Characterization & Optimization

**Status: PLANNED AFTER E**

Phase F deliberately limits the core emulator workload to:

```text
NES
SNES
Genesis
PS1
```

N64/GameCube/PS2 are excluded until the optimized core baseline exists.

The goal is not merely to benchmark the EliteDesk. It is to **optimize the Linux
implementation as far as worthwhile, measure the complete system, and derive a
lower-cost Prototype 2 from evidence**.

## F1 — Freeze the workload suite

Representative workloads should include, where present:

- idle Linux + PrivyHub;
- Live TV;
- VOD;
- browser/live source;
- camera/live source;
- NES/SNES/Genesis;
- PS1 local emulation;
- PS1 + native streaming;
- 720p60 reference profile;
- higher Phase-C profiles where applicable;
- metadata/storage work;
- representative concurrent core workloads.

## F2 — Whole-system measurements

Measure:

- total/per-core CPU;
- process CPU;
- RAM/working sets;
- swap;
- iGPU/render utilization;
- hardware video engine utilization;
- encoder headroom;
- storage latency/throughput;
- network/FEC/decoder telemetry;
- end-to-end latency;
- temperatures/throttling;
- wall/idle power where practical;
- concurrency behavior.

Do not infer lower-tier hardware requirements from one aggregate CPU percentage.

## F3 — Optimization loop

Use:

```text
measured bottleneck
      ↓
narrow hypothesis
      ↓
one optimization
      ↓
fresh benchmark
      ↓
accept / reject
```

Potential areas:

- unnecessary services;
- scheduling/priorities;
- memory footprint;
- avoidable copies;
- capture path;
- hardware encoder path;
- buffering;
- storage/cache behavior;
- plugin lifecycle;
- idle/background work;
- network pacing/buffers;
- concurrency policies.

Optimize before deriving the hardware floor.

## F4 — Core Linux resource envelope

Produce:

- **Known-good reference:** 4650G/16 GB prototype;
- **Measured floor:** lowest demonstrated capability for defined workloads;
- **Recommended alpha:** floor plus reliability/update/concurrency headroom;
- **Optional higher tier:** stronger profiles without redefining Core.

## F5 — Capability detection and graceful scaling

PrivyHub should classify:

- CPU/RAM/storage;
- GPU/iGPU;
- hardware encode/decode;
- validated stream profiles;
- emulator tiers;
- concurrency headroom;
- network capabilities.

Features should enable only where the host/client pair is known to support them.

## F6 — Select Prototype 2 / friend-alpha hardware

Select from measured evidence, considering:

- price/availability;
- Linux compatibility;
- idle power;
- thermals/noise;
- hardware video acceleration;
- storage/RAM practicality;
- network reliability;
- margin above the measured floor.

Do not select the absolute cheapest machine merely because it has a superficially
similar benchmark score.

## F7 — Resource checkpoint

Acceptance:

- repeatable workload suite;
- PS1-and-below scope preserved;
- worthwhile bottlenecks optimized;
- resource/power envelope documented;
- capability model established;
- Prototype 2 class selected from evidence;
- clean checkpoint/push.

---

# Phase G — Extended Emulation & User-Content Import

**Status: FUTURE AFTER F**

This phase adds the user-owned content pipeline before introducing heavier
console workloads.

PrivyHub will **not** provide or fetch ROMs, ISOs, BIOS/firmware, keys, or similar
game content.

## G0 — User-content import contract

Define a removable-media import layout, for example:

```text
PrivyHub-Import/
    bios/
        ps1/
        ps2/
        ...
    roms/
        n64/
        ...
    isos/
        gamecube/
        ps2/
        ...
    artwork/
    metadata/
```

Exact system folders should match emulator/storage requirements rather than this
example blindly.

The import system should:

- support ordinary USB mass storage;
- inspect before copying;
- provide a dry-run/manifest;
- hash files;
- detect duplicates;
- validate allowed extensions/types;
- perform stronger format/signature validation where practical;
- map content to the existing PrivyHub user-data layout;
- copy atomically;
- verify copied bytes;
- be safely repeatable/idempotent;
- never delete source USB files by default;
- preserve user saves/states separately;
- reject ambiguous/unknown files instead of guessing;
- keep ROM/ISO/BIOS content out of Git and support bundles;
- log sanitized import results without exposing private filenames/content where
  not required.

The import tooling should integrate content **into the existing infrastructure**
rather than create a second game-library path.

## G1 — N64

Evaluate representative N64 emulation, controllers, saves, local rendering,
native streaming, CPU/iGPU cost, latency, and compatibility.

Question:

> Does the optimized core/alpha hardware already have enough margin for N64?

## G2 — GameCube

Evaluate bounded representative titles:

- native/default rendering first;
- modest upscale only after baseline;
- CPU/iGPU pressure;
- stream/encoder interaction;
- latency/stability;
- thermals;
- compatibility outliers.

## G3 — PS2

Evaluate representative easy/moderate/heavy titles:

- CPU thread pressure;
- iGPU pressure;
- hardware renderer;
- native/default resolution first;
- streaming overhead;
- game-specific compatibility;
- sustained thermal behavior.

User-supplied PS2 BIOS should enter only through the G0 import boundary.

## G4 — Extended-emulation tiers

Possible evidence-driven outcome:

```text
CORE
  NES / SNES / Genesis / PS1

EXTENDED
  + N64

ENHANCED
  + selected GameCube / PS2
```

The actual boundaries come from runtime evidence.

## G5 — Extended-emulation checkpoint

Acceptance:

- content import pipeline validated;
- no project-supplied ROM/ISO/BIOS requirement;
- N64 characterized;
- GameCube characterized;
- PS2 characterized;
- incremental resource costs compared with Phase F;
- compatibility claims limited to tested evidence;
- base Core hardware remains independent unless evidence strongly justifies a
  change;
- clean checkpoint/push.

---

# Phase H — Home Infrastructure / Client / Plugin Expansion

**Status: FUTURE**

PrivyHub expands from TV/media/games into a private local home-coordination
layer.

## H1 — First-class plugin/provider architecture

Capabilities should be exposed once and callable from GUI, remote/control API,
automation, voice, or AI:

```text
games.launch()
vod.play()
tv.channel()
camera.show()
home.light.set()
home.scene.activate()
timer.create()
steam.launch()
```

Interfaces should invoke registered capabilities rather than duplicate device
logic.

## H2 — Handheld client

Evaluate X28-class Android handheld:

- reuse Android client;
- hardware AVC decoding;
- 720p60 behavior;
- built-in controls;
- Games/VOD/TV browsing;
- session/pause UI;
- battery/network behavior;
- discovery;
- optional dock/TV use.

## H3 — Existing-PC / Steam provider

Use an existing gaming PC/laptop as optional external compute.

PrivyHub should provide discovery, readiness, library/orchestration, permissions,
and session UX.

Prefer a direct PC→client media path when the external provider already solves it
better than routing video through the Linux hub.

## H4 — Home Assistant / device provider

Integrate mature local-first smart-home infrastructure rather than recreating
every protocol.

Potential capabilities:

- lights/switches;
- sensors;
- climate;
- scenes;
- blinds;
- Matter/Zigbee devices exposed by the home stack;
- automation state.

## H5 — Camera and microphone infrastructure

Treat cameras/microphones as explicit private device classes:

- local registration;
- live access;
- local recording where applicable;
- retention;
- local event/motion/audio metadata;
- explicit per-device permissions;
- no mandatory vendor cloud;
- intelligence layer separated from raw device access.

Microphones should support local deterministic/voice workflows without requiring
cloud transmission.

## H6 — Storage / larger media server

Expand household storage:

- indexed media;
- larger DVD/VOD libraries;
- storage health;
- backup/maintenance;
- optional remote streaming.

Storage capacity and compute sizing remain separate questions.

## H7 — Secure optional remote access

Possible targets:

- VOD;
- cameras;
- home controls;
- game/session control.

Local operation must remain functional when remote connectivity is absent.

---

# Phase I — Local Intelligence / Voice / Privacy-Aware AI

**Status: FUTURE**

PrivyHub intelligence should be layered from deterministic/local to optional
external providers. No cloud AI provider is mandatory.

## I1 — Deterministic local automation first

Simple home behavior should remain explicit and inspectable:

```text
sensor/event
   ↓
local rule
   ↓
registered PrivyHub action
```

Examples:

- lights;
- timers;
- scenes;
- media controls;
- camera display;
- scheduled routines.

## I2 — Local voice foundation

Default path:

```text
wake word
   ↓
local speech/phrase recognition
   ↓
deterministic command registry
   ↓
validated plugin action
   ↓
local response/TTS
```

Core household commands must not require a cloud API.

## I3 — Small local intent model

A very small local model may map fuzzy language to constrained registered
actions.

Example:

```text
"make the living room a little darker"
        ↓
light.set_brightness(living_room, ...)
```

The model:

- sees a bounded action vocabulary;
- returns structured output;
- has no shell/device/network authority;
- fails safely;
- requires confirmation for sensitive actions;
- remains optional where deterministic matching is sufficient.

## I4 — Optional external AI provider abstraction

Allow a user to supply credentials for providers such as:

- OpenAI;
- Anthropic/Claude;
- other commercial APIs;
- user-hosted compatible endpoints;
- future local high-capability inference.

Potential provider capabilities:

```text
speech.transcribe()
language.interpret()
vision.describe()
vision.detect()
speech.synthesize()
```

Providers are plugins, not core dependencies.

## I5 — Privacy boundary / data-minimization policy

Cloud capability is **explicit opt-in** and should maximize local privacy even
when enabled.

Required principles:

- no silent local-failure → cloud-upload fallback;
- user-controlled API credentials;
- secrets stored separately from normal config/logging;
- per-provider and preferably per-device permissions;
- disclose what data type crosses the boundary;
- minimize payload before transmission;
- prefer local feature/event extraction over raw continuous media where
  sufficient;
- send only the minimum temporal/spatial/audio segment needed;
- redact/suppress unnecessary metadata;
- do not include unrelated household context;
- local-only modes remain available;
- provider outage never disables core home control;
- sensitive actions pass through the same local validation/permission layer;
- cloud models never receive arbitrary shell/device authority;
- AI/provider actions are auditable.

Possible user policies:

```text
home control       local only
basic voice        local only
general assistant  cloud allowed
camera analysis    off / event-only / explicit request
microphone cloud   off / push-to-talk / explicit request
```

## I6 — Privacy-aware camera/microphone intelligence

Preferred order:

```text
local deterministic event detection
        ↓
small local classifier/intent model
        ↓
optional external analysis of minimized selected data
```

Continuous microphone/camera feeds should not be exported merely because a cloud
provider is configured.

## I7 — Future first-party local LLM

Defer larger local open-weight inference until actual usage justifies the
hardware/cost.

It should plug into the same provider interface rather than create a parallel
control architecture.

## I8 — Local adaptive resource optimizer

Use machine telemetry to choose among bounded validated actions/profiles.

Progression:

```text
deterministic rules
      ↓
rolling statistics / adaptive thresholds
      ↓
simple lightweight models where useful
      ↓
more sophisticated ML only if evidence justifies it
```

Inputs may include CPU/RAM, hardware video engine, network/FEC, decoder state,
storage I/O, thermal state, active services, client capabilities, and concurrent
workloads.

Every adaptive decision remains diagnosable.

---

# Cross-cutting architecture rules

## Local-first, not necessarily local-only

Core operation must not require:

- cloud availability;
- subscription;
- metadata provider;
- external AI;
- remote authentication;
- vendor smart-home cloud.

Optional external providers are explicit additions.

## User-owned content boundary

PrivyHub does not supply copyrighted/proprietary game content.

User ROMs/ISOs/BIOS/firmware remain runtime/user data:

- outside Git;
- outside support bundles;
- imported through explicit tooling;
- not silently fetched;
- not silently replaced.

## Privacy boundary is explicit

A local failure must never silently send microphone audio, camera images,
household state, filenames, or other private data to an external provider.

## Models request actions; they do not control the machine

Local or cloud models may request registered PrivyHub actions.

The local policy/permission layer remains authoritative.

## Diagnostics first

Dynamic behavior must explain why it changed.

Use:

```text
one narrow hypothesis
      ↓
one targeted diagnostic
      ↓
fresh evidence
      ↓
inspect raw measurements
      ↓
one coherent change
```

## Preserve validated subsystems

Do not disturb stable video/audio/controller/storage/media paths for unrelated
work.

## Capability-driven architecture

Avoid hard-coding assumptions about one PC/router/client.

Features and stream/emulator tiers should be enabled from measured capability.

## Fail closed

If identity, readiness, save integrity, import integrity, capture scope, or
permission cannot be established, preserve the data/session rather than guessing.

## Checkpoint discipline

At every meaningful milestone:

- update durable memory;
- preserve curated runtime evidence;
- run deterministic validation;
- checkpoint cleanly;
- push only after local state is proven.

---

# Near-term decision gates

## Gate 1 — Phase C telemetry

Do not implement adaptive bitrate until the telemetry can distinguish:

- healthy path;
- capacity pressure;
- random loss;
- burst/jitter pathology;
- decoder starvation.

## Gate 2 — Phase D Live TV data model

Do not polish the guide UI around unreliable channel/EPG identity.

First establish canonical channels, normalization, matching, refresh, and
diagnostics.

## Gate 3 — Linux backend selection

Before Phase E implementation, define the Linux equivalents for capture,
hardware encoding, source audio, input injection, service lifecycle, and
diagnostics while preserving stable behavioral contracts.

## Gate 4 — Linux acceptance

Do not start hardware shrinking until the Linux system is functionally correct
and runtime validated.

## Gate 5 — Resource measurement quality

Do not select Prototype 2 from superficial aggregate CPU percentages.

Use whole-system measurements and hardware-acceleration evidence.

## Gate 6 — User-content import

Before enabling new N64/GameCube/PS2 libraries, validate the USB/removable-media
import path, idempotence, hashing, target mapping, and failure behavior.

## Gate 7 — Extended emulation

Do not allow N64/GameCube/PS2 to raise the Core minimum before incremental cost
is measured against the optimized Phase F baseline.

## Gate 8 — Cloud AI

Do not add an external AI provider without:

- explicit opt-in;
- credential boundary;
- per-capability privacy model;
- data minimization;
- no silent fallback;
- local action validation.

## Gate 9 — Larger local AI

Do not make a substantial local LLM a base hardware requirement without product
evidence that justifies it.

---

# Immediate sequence

```text
A COMPLETE / PUSHED
        ↓
B COMPLETE / PUSHED
        ↓
C Adaptive Streaming
  C1 profiles
  C2 telemetry
  C3 adaptive bitrate
  C4 FEC decision
  C5 1080p characterization
  C6 generalized source abstraction
  C7 checkpoint
        ↓
D Media / VOD / Live TV
  local library polish
  channel normalization
  EPG/guide rebuild
  checkpoint
        ↓
E Linux Migration
  HP 805 G6
  Linux-native A/V/input/server
  PS1-and-below parity
  UDP replay
  checkpoint
        ↓
F Linux Optimization / Resource Characterization
  freeze PS1-and-below
  measure
  optimize
  measure again
  derive capability envelope
  select Prototype 2
        ↓
G User Content + Extended Emulation
  safe USB import
  N64
  GameCube
  PS2
  capability tiers
        ↓
H Home / Clients / Plugins
  handheld
  Steam/external compute
  Home Assistant/devices
  cameras/microphones
  storage
  remote access
        ↓
I Local Intelligence / Voice / AI
  deterministic local control
  local voice
  small local intent model
  optional OpenAI/Claude/other providers
  privacy-aware camera/microphone analysis
  future local LLM
  bounded adaptive optimizer
```

---

## Guiding statement

PrivyHub should be designed around the smallest reliable **Linux-native,
local-first core** that can deliver the validated household experience with
appropriate headroom.

Optional capabilities should scale upward:

```text
CORE
  media / Live TV / local services
  PS1-and-below
  normal native streaming
  deterministic local home control
  basic local voice

EXTENDED
  stronger stream profiles
  N64
  additional concurrency

ENHANCED
  selected GameCube / PS2
  heavier local processing

OPTIONAL EXTERNAL COMPUTE
  existing gaming PC / Steam
  user-enabled cloud AI providers

FUTURE LOCAL AI
  stronger local open-weight inference
```

The HP EliteDesk 805 G6 exists to establish and optimize the Linux reference
with enough headroom to avoid confusing migration failures with minimum-hardware
limits.

Prototype 2 should be selected only after Phase F produces evidence for a
cheaper, appropriately sized alpha appliance.
