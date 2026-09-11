---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: a6dbf627dd32af7da975bf01a679350810026ca3
---

# Roadmap Status

## Current position

| Phase | Status | Current meaning |
| --- | --- | --- |
| A — Games / Emulator Subsystem | **COMPLETE / PUSHED** | Runtime-validated native game, controller, Save/Load, profile and PS1 multitap baseline |
| B — Diagnostics & Clean Native Baseline | **COMPLETE / PUSHED** | Diagnostics/Self-Test/support bundle/retention complete; Sunshine/Moonlight product dependency removed; native regression passed |
| C — Adaptive Native Streaming | **ACTIVE** | C1 explicit stream profiles |
| D — Media Library / VOD / Live TV UX | PLANNED | Media-library and substantial Live TV/EPG/guide work |
| E — Linux Migration / Native Linux Baseline | PLANNED | Move core server path to Linux reference prototype |
| F — Linux Core Resource Characterization & Optimization | PLANNED | Optimize and size PS1-and-below on Linux |
| G — Extended Emulation & User-Content Import | PLANNED | Safe content import, then N64/GameCube/PS2 feasibility |
| H — Home Infrastructure / Client / Plugin Expansion | FUTURE | Broader smart-home/storage/client/plugin work |
| I — Local Intelligence / Voice / Privacy-Aware AI | FUTURE | Local-first intelligence with optional explicit external providers |

`docs/ROADMAP.md` roadmap v3 is authoritative for phase definitions.

## Active item: C1 explicit stream profiles

### Inventory

**COMPLETE**

Result:

`C1_INVENTORY_COMPLETE`

Reference stream:
- 1280x720;
- 60 fps;
- 7000 kbps;
- GOP 15;
- B-frames 0;
- 8+1 XOR FEC;
- H.264 NVENC over the native RTP-sized UDP path;
- Android hardware AVC decode.

### Next

`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`

The first profile patch should:
1. name the existing reference behavior explicitly;
2. separate portable profile semantics from backend/wire/session mechanics;
3. make the active profile inspectable;
4. preserve current stream behavior exactly;
5. avoid a GUI selector or adaptive controller until the static profile is
   runtime validated.

Likely portable fields:
- `id`
- `width`
- `height`
- `fps`
- `bitrate_kbps`
- `max_bitrate_kbps`
- `gop_frames`
- `bframes`
- optional `fec_group_size`

Backend/session details remain outside the portable schema unless later evidence
requires otherwise.

## C1 acceptance gate

Before C2:
- explicit reference profile is active and visible to diagnostics/status;
- stream remains 720p60 / 7000 kbps / GOP15 / 8+1 FEC;
- normal picture/audio/controller operation passes;
- Pause/Resume, Save/Load and End/teardown pass;
- no regression in existing game/profile behavior.

## Post-C direction

Accepted continuation:

`D -> E -> F -> G -> H -> I`

Constraints:
- Live TV is not considered finished; Phase D contains remaining channel/EPG UX work.
- HP EliteDesk 805 G6 is the Linux reference prototype, not the minimum target.
- Choose cheaper Prototype 2 hardware from measured Phase F evidence.
- Phase F core sizing is intentionally PS1-and-below.
- Phase G establishes safe user-content import before later-console feasibility work.
- OpenBIOS is not a dedicated project phase.
- Local deterministic control remains the baseline for later intelligence work.
