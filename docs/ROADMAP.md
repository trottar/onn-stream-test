# PrivyHub / Safe IoT Project Roadmap

## Overview

This roadmap tracks the current development sequence for PrivyHub, from completion of the existing Windows + onn gaming prototype through cleanup, streaming generalization, and eventual Linux/resource testing.

| Phase | Purpose | Current Status |
|---|---|---|
| **A — Emulator Completion** | Finish Games as a polished, normal-use subsystem | **Nearly complete** |
| **B — Clean Baseline** | Remove Sunshine/Moonlight and prove native Games independence | **Not started** |
| **C — Streaming Architecture** | Generalize native streaming and add explicit quality profiles | **Not started** |
| **D — Resource Testing / Linux** | Benchmark the finished architecture and test/migrate to cheap Linux-capable hardware tiers | **Not started formally** |

---

# Phase A — Emulator Completion

The goal of Phase A is to finish the Games subsystem until it feels complete and stable enough to stop treating it as an experimental prototype.

## A1 — Controller Mapping / Analog Support

**Status: COMPLETE / RUNTIME VALIDATED**

Completed:

- Android sends digital buttons and real analog axes.
- Windows receives analog input through two ViGEm Xbox controllers.
- NES/SNES/Genesis support analog-stick-to-D-pad convenience behavior.
- PS1 supports genuine analog behavior where appropriate.
- Per-game PS1 controller profiles are supported.
- DualShock behavior is working where required.
- Two-player control remains working.

---

## A2 — Save / Load

**Status: COMPLETE / RUNTIME VALIDATED**

Completed:

- Save slots 1/2/3.
- Load slots 1/2/3.
- Per-game state identity.
- Slot metadata in the UI.
- Persistent RetroArch save/state directories.
- Graceful shutdown so SRAM and memory-card data can flush.
- Zero-byte savestate failure fixed.
- Save validation requires stable, nonzero content.
- Hash verification prevents false-success copies.
- RetroArch's actual state-loader behavior is observed rather than trusting acknowledgements alone.
- Save and Load validated across multiple games.
- Comprehensive game-session diagnostics added.

---

## A3 — Pause / Resume

**Status: COMPLETE / RUNTIME VALIDATED**

Current behavior:

```text
Fullscreen gameplay
        ↓ Back
capture final rendered frame
        ↓
leave stream
        ↓
RetroArch pauses
        ↓
A/V/FEC stops
        ↓
Game Session banner
```

Returning:

```text
click frozen frame
        ↓
native streaming starts
        ↓
RetroArch resumes
        ↓
fullscreen gameplay
```

Also completed:

- Fail-closed pause behavior.
- Game process remains alive outside fullscreen.
- Controller infrastructure remains alive.
- Frozen gameplay-frame banner.
- Save / Load / End controls integrated into the paused Game Session UI.

---

## A4 — Host Coexistence

**Status: COMPLETE / RUNTIME VALIDATED**

Goal:

```text
onn player: uninterrupted game
Windows user: free to use PC normally
```

Completed:

- RetroArch can run without dominating the Windows desktop.
- Host focus can be restored.
- RetroArch can remain behind other windows.
- Windows Graphics Capture continues to target the game window.
- Host and onn usage can coexist without forcing the PC user into the emulator window.

---

## A5 — Direct Launch UX

**Status: COMPLETE / RUNTIME VALIDATED**

Completed:

- Game launches through the companion.
- Native stream readiness is integrated into the launch flow.
- The UX can proceed directly into gameplay rather than requiring unnecessary intermediate steps.
- Failure handling preserves a safe paused/session state rather than blindly continuing.

---

## A6 — Game Organization / Metadata / Box Art

**Status: COMPLETE / RUNTIME VALIDATED**

Completed architecture includes:

- game catalog;
- stable game IDs;
- system identification;
- per-game metadata;
- launch/session state;
- per-game save identity;
- game titles integrated into state UI;
- artwork/metadata support;
- user-content structure;
- library organization and presentation improvements.

Artwork remains metadata/cache and does not alter canonical ROM content.

---

## A7 — Cheats / Mods

**Status: COMPLETE / RUNTIME VALIDATED**

### A7.1 — User-Content Catalog

**COMPLETE**

Managed user-content structure:

```text
data/games/user_content/<game_id>/
```

Used as the extensible location for game-specific content.

---

### A7.2 — Cheat Provider Updater

**COMPLETE / RUNTIME VALIDATED**

Completed:

- libretro cheat provider ingestion;
- catalog/cache generation;
- cheat matching;
- ambiguity handling;
- invalid/provider-unavailable detection.

---

### A7.3 — Cheat Selection, Activation, Profiles, Isolation, GUI

**COMPLETE / RUNTIME VALIDATED**

Completed:

- cheat catalog in GUI;
- explicit cheat selection;
- exact runtime activation;
- persistent cheat profiles;
- deterministic profile identity;
- profile-specific save/state isolation;
- existing-profile reopen flow;
- overwrite confirmation;
- normal save namespace protected;
- changing cheat set creates a distinct profile;
- no automatic cheat-profile-to-normal-save contamination.

---

### A7.4 — Mods / Softpatch Profiles

**COMPLETE / RUNTIME VALIDATED**

Completed:

- managed mod catalog;
- persistent mod profiles;
- deterministic mod-profile identity;
- isolated save/state namespace;
- existing-profile reopen;
- GUI launch flow;
- profile overwrite protection;
- normal ROM remains untouched.

Supported initial formats:

- `.ips`
- `.bps`
- `.ups`
- `.xdelta`

Initial supported systems:

- NES / FCEUmm
- SNES / bsnes
- Genesis / BlastEm

PS1 currently fails closed because the active Beetle PSX HW path does not support frontend softpatching.

### Deterministic IPS Runtime

Runtime testing showed RetroArch could accept an IPS argument without visibly applying the patch.

PrivyHub now handles `.ips` patches deterministically:

```text
canonical ROM
    +
IPS patch
    ↓
PrivyHub-generated derived ROM
    ↓
verified SHA-256
    ↓
mod profile launch
```

Properties:

- original ROM remains untouched;
- standard IPS records supported;
- RLE records supported;
- growth/truncation handled;
- malformed/oversized patches rejected;
- derived content SHA-256 verified;
- generated content reused only when metadata and bytes still match;
- original ROM filename/stem preserved inside the profile so existing save/state behavior remains stable.

Runtime validation:

- Donkey Kong Country mirrored IPS mod successfully applied;
- visible gameplay changes confirmed;
- Save works;
- Load works;
- existing mod profile reopening works.

BPS/UPS/XDelta remain available through RetroArch and should be individually investigated only if a real runtime failure appears.

---

## A8 — Input Mapping & Profiles

**Status: NEXT**

This is the immediate new addition before Phase A is closed.

Goal:

```text
Physical Controller
        ↓
PrivyHub Input Profile
        ↓
Per-game assignment
        ↓
RetroPad mapping
        ↓
Core
```

Planned capabilities:

- remap buttons from the Android GUI;
- create named reusable input profiles;
- assign one profile to multiple games;
- per-game profile assignment;
- duplicate profiles;
- rename profiles;
- edit profiles;
- reset to defaults;
- preserve the existing known-good default controller behavior;
- keep the stored schema PrivyHub-owned instead of exposing raw RetroArch config;
- allow later expansion to per-player profile assignment if useful.

Potential example profiles:

```text
Default
SNES Traditional
Genesis 6-Button
PS1 DualShock
Arcade Layout
Racing
Custom Profile
```

The implementation should preserve the existing stable input transport and generate session-specific RetroArch overrides rather than modifying the global baseline.

---

## A9 — Emulator-Focused Checkpoint

**Status: PENDING**

After A8:

- full emulator regression test;
- game launch;
- two controllers;
- analog behavior;
- pause/resume;
- Save/Load;
- End;
- frozen preview;
- host coexistence;
- direct-launch behavior;
- library organization;
- cheats;
- mods;
- input profiles;
- repository audit;
- clean checkpoint commit/push.

At that point the Games subsystem should be considered essentially finished for normal use while the rest of PrivyHub evolves.

---

# Phase B — Clean Baseline

**Status: NOT STARTED**

Phase B begins only after Emulator Completion.

## B1 — Completely Remove Sunshine / Moonlight

This means removing the legacy architecture comprehensively, not merely deleting launch scripts.

Inventory and remove:

- Sunshine/Moonlight services and processes;
- scheduled tasks;
- setup/removal scripts;
- firewall rules;
- Android package/query dependencies;
- Android intents;
- `StreamManager`;
- Games plugin references;
- UI/status references;
- configuration;
- portable runtime directories;
- obsolete helper scripts.

Known legacy examples historically included:

```text
scripts/install_moonlight_onn.ps1
scripts/install_sunshine_firewall.ps1
scripts/open_sunshine_web_ui.ps1
scripts/remove_sunshine_firewall.ps1
scripts/setup_sunshine_portable.ps1
```

Native PrivyHub streaming has superseded this architecture.

---

## B2 — Verify Native Games Independently

After Sunshine/Moonlight removal, verify:

- launch;
- native video;
- native audio;
- controllers;
- analog;
- pause/resume;
- Save/Load;
- cheats;
- mods;
- input profiles;
- End;
- diagnostics;
- game library UI.

Nothing should depend on Sunshine/Moonlight.

---

## B3 — Clean Checkpoint

Audit and checkpoint the repository with only the native PrivyHub architecture remaining.

---

# Phase C — Streaming Architecture

**Status: NOT STARTED**

The goal is to stop treating native streaming as merely the Games streamer.

## C1 — Explicit 720p / 1080p Profiles

Current stable 720p baseline:

```text
720p60
H.264 NVENC
7 Mbps
P1
GOP 15
no B-frames
8+1 XOR FEC
```

This should become an explicit profile rather than an implicit hardcoded baseline.

Planned:

- explicit 720p60 profile;
- explicit 1080p60 profile;
- source-specific profile selection where appropriate;
- reusable profile/config architecture.

---

## C2 — Test 1080p60

Only after Phase B.

Test the current reference path:

```text
Windows PC + GTX 970
        ↓
isolated network
        ↓
onn hardware decoder
```

Measure:

- host CPU;
- GPU/NVENC usage;
- bitrate;
- decode behavior;
- latency;
- stability;
- packet behavior;
- onn capability.

---

## C3 — Generalize Native Capture / Transport / Decoder Infrastructure

Target architecture:

```text
Game window
Browser
Camera
Other live source
      │
      ▼
capture/source abstraction
      │
      ▼
native streaming infrastructure
      │
      ▼
onn hardware decoder
```

Potential shared sources:

- Games;
- live browser;
- camera;
- other live/application sources.

Different sources may still use different:

- latency targets;
- quality targets;
- resolution;
- bitrate;
- audio behavior;
- buffering.

The goal is common infrastructure, not one inflexible profile.

---

## C4 — Streaming Architecture Checkpoint

Checkpoint once:

- Games use generalized native streaming;
- browser/live application streaming is integrated;
- camera/native sources are integrated where appropriate;
- 720p and 1080p profiles are understood and explicit.

---

# Phase D — Resource Testing / Linux

**Status: NOT STARTED FORMALLY**

Phase D is deliberately postponed until the architecture is mature enough to benchmark meaningfully.

## D1 — Establish Representative Workloads

Potential workloads:

```text
720p60 game streaming
1080p60 game streaming
camera streaming
browser streaming
media server activity
multiple background services
```

The exact formal suite should come from the finished A–C architecture.

---

## D2 — Measure the Windows Reference System

The current Windows PC becomes the formal reference baseline.

Measure:

- CPU;
- GPU;
- RAM;
- encoder usage;
- storage activity;
- network;
- concurrent-service behavior;
- latency/stability.

Existing telemetry is useful precursor data but is not yet the formal Phase-D benchmark suite.

---

## D3 — Test Inexpensive Linux-Capable Hardware Tiers

Determine empirically what inexpensive hardware can support.

Example outcome structure:

```text
Tier A
  720p60 game streaming
  basic server duties

Tier B
  1080p60
  broader media/smart-home workload

Tier C
  heavier concurrent workloads
```

Do not predefine the tiers and force the product into them; derive them from measured capability.

---

## D4 — Capability / Resource Scaling

Eventually PrivyHub should detect:

- CPU;
- architecture;
- RAM;
- GPU/iGPU;
- hardware encoder availability;
- hardware decoder availability;
- network interfaces;
- storage;
- possibly benchmark/probe results.

Then expose only the profiles/features appropriate for that host.

Conceptually:

```text
PrivyHub capability probe
        ↓
Host capability profile
        ↓
available streaming/features
```

---

## D5 — Replay UDP Diagnostic / Acceptance Suite

The current transport/Wi-Fi pathology remains deferred here unless it becomes an immediate blocker.

Replay the existing saved forward/reverse transport probes on Linux and representative infrastructure.

Compare against Prototype 1 evidence, including:

- sender pacing;
- burst/gap behavior;
- Android kernel arrival;
- loopback behavior;
- reverse duplicate arrival;
- Windows receive behavior;
- FEC behavior;
- packet loss/jitter;
- decoder starvation and stale-frame behavior.

The goal is to determine whether the current pathology is:

- specific to the Windows/USB-Wi-Fi development environment;
- broader consumer-network behavior;
- or reproducible in representative final infrastructure.

Do not reopen this investigation prematurely without new blocking evidence.

---

# Current Project Position

```text
PHASE A — Emulator Completion
│
├─ A1 Controller / analog                  COMPLETE
├─ A2 Save / Load                          COMPLETE
├─ A3 Pause / Resume                       COMPLETE
├─ A4 Host coexistence                     COMPLETE
├─ A5 Direct launch UX                     COMPLETE
├─ A6 Organization / metadata / art        COMPLETE
├─ A7 Cheats / mods                        COMPLETE
│    ├─ A7.1 User-content catalog          COMPLETE
│    ├─ A7.2 Cheat provider updater        COMPLETE
│    ├─ A7.3 Cheat profiles                COMPLETE
│    └─ A7.4 Mod profiles                  COMPLETE
├─ A8 Input Mapping & Profiles             NEXT
└─ A9 Emulator checkpoint                  PENDING

PHASE B — Clean Baseline
├─ Remove Sunshine/Moonlight               NOT STARTED
├─ Native-only regression                  NOT STARTED
└─ Clean checkpoint                        NOT STARTED

PHASE C — Streaming Architecture
├─ Explicit 720p/1080p profiles            NOT STARTED
├─ 1080p60 testing                         NOT STARTED
├─ Generalized source abstraction          NOT STARTED
├─ Browser/native application streaming    NOT STARTED
├─ Camera/native source streaming          NOT STARTED
└─ Checkpoint                              NOT STARTED

PHASE D — Resource Testing / Linux
├─ Representative workloads                NOT STARTED
├─ Windows reference benchmark             NOT STARTED FORMALLY
├─ Cheap Linux hardware tiers              NOT STARTED
├─ Capability/profile checker              NOT STARTED
├─ UDP acceptance-suite replay             DEFERRED HERE
└─ Hardware tier conclusions               NOT STARTED
```

---

# Immediate Development Sequence

```text
Current A7 state
      ↓
checkpoint / push
      ↓
A8 Input Mapping & Profiles
      ↓
A9 Full emulator regression + checkpoint
      ↓
Phase B — Clean Baseline
      ↓
Phase C — Streaming Architecture
      ↓
Phase D — Resource Testing / Linux
```

## Guiding Principles

Throughout all phases:

- local working tree remains authoritative between checkpoints;
- preserve stable subsystems unless a change specifically requires touching them;
- use one narrow hypothesis → one targeted diagnostic → fresh evidence → one coherent patch;
- prefer durable diagnostics over ad-hoc troubleshooting;
- protect canonical ROMs and normal save namespaces;
- reuse proven code paths instead of creating parallel implementations;
- keep the system local-first, modular, hardware-agnostic, and free of mandatory cloud/proprietary dependencies;
- fail closed where readiness or safety cannot be proven;
- defer environment-specific transport optimization until representative infrastructure exists unless it becomes a blocker.
