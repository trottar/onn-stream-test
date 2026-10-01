# PrivyHub / Safe IoT Roadmap — Linux-First + Remote-Foundation Revision

**Revision date:** 2026-09-14 (position marker updated 2026-09-22)
**Predecessor synchronized checkpoint:** C1.1 + native-status privacy checkpoint `0c31c100ec721d687aff6aedbd79bc0cf9343810`
**Roadmap status:** Accepted project plan, **still authoritative and unchanged in structure**. Future secure remote access remains promoted to Phase G after Linux optimization.

---

## 0. Where the work actually is — 2026-09-22

**The roadmap below is not restructured; only this marker moves.**
Authority for the current position is `docs/memory/CURRENT.md`.

- **Phase D is ACTIVE.** The Linux host runs the companion and the games
  path; D4 PS1 multitap parity is the open functional item.
- **Phase C RESUMED 2026-09-23.** The inserted investigation, **`D-BASE`
  baseline stream health, is CLOSED — BASELINE MET**
  (`docs/memory/evidence/D_BASE_CLOSEOUT_2026-09-23.md`; decision
  `docs/memory/decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`, closed).
  Next: `C3.L3a` Part 2 (fix its probe's three defects first), then
  `C3.L4`; C1 is done. **2026-09-28: `C3.L3a` complete (four sessions
  pooled); `C3.L4` AUTHORIZED, single transition per event; live mode
  BUILT (`C3-L4-L1`: SILENT on a clean link, decrease proven on injection,
  increase rule unreachable in attract mode — the user's call; `nft` night
  next); C4 closed (8+1 stays); D7 complete on the adopted build; C5: 1080p60 NOT CAPABLE (stream) at parity, capability-gated; C5-M2's follow-up arms INCONCLUSIVE (link); C5-M3's low rungs screened (720p/4000 passes transport). **2026-10-01: C5 reopened by the user's reading (1080p60 through the ladder); C5-M4 Part 1 measured the PS1 source at native 1080p (4x holds 60; proposal not applied).**
- **`D-BASE`'s loss column is closed.** The wireless-hop packet loss was
  traced to the encoder's per-frame burst and fixed by a 90,000-byte frame
  cap, now a declared field of `native_game_720p60_reference`
  (`D-BASE-P6`, `P6a`, `S3`). The residual correlates with nothing
  measured.
- **Done since:** the headless host (`H2`), the companion as a systemd
  unit (`H3`), link-drop recovery validated on real loss (`R3`-`R3d`),
  the audio cushion (12/17) and audio redundancy (2/4) adopted. **The
  roadmap's own order resumes: remaining Phase C on Linux, then Phase E.**

---

## 1. Current project position

| Phase | Purpose | Status |
|---|---|---|
| **A — Emulator Subsystem** | Finish Games/emulation as a normal-use subsystem | **COMPLETE / PUSHED** |
| **B — Diagnostics & Clean Native Baseline** | Make PrivyHub self-diagnosing and remove active Sunshine/Moonlight legacy | **COMPLETE / PUSHED** |
| **C — Adaptive Streaming Architecture** | Portable profile/telemetry/readiness foundation complete enough for Windows; automatic adaptation continues on Linux | **RESUMED 2026-09-23** at C3 (`D-BASE` closed, baseline met) |
| **D — Linux Migration / Native Linux Baseline** | Move the core server to the HP EliteDesk Linux prototype and restore normal-use parity | **ACTIVE** |
| **E — Linux Core Resource Characterization & Optimization** | Optimize and measure the Linux core with PS1-and-below only; select Prototype 2 from evidence | **PLANNED AFTER D** |
| **F — Media Library, VOD & Live TV UX** | Finish local media polish plus substantial Live TV/channel/guide work on Linux | **PLANNED AFTER E** |
| **G — Secure Remote Access / Portable Client Foundation** | Establish overlay/provider abstraction, portable trusted-LAN access, WAN session identity/auth, and off-site PS1-and-below validation | **FUTURE AFTER F** |
| **H — Extended Emulation & User-Content Import** | Build safe user-content ingestion, then characterize N64, GameCube, and PS2 on the established local/remote foundation | **FUTURE AFTER G** |
| **I — Home Infrastructure / Broader Plugin Expansion** | Home Assistant/devices, cameras/microphones, storage, broader clients and provider expansion | **FUTURE** |
| **J — Local Intelligence / Voice / Privacy-Aware AI** | Deterministic local automation, small local models, optional user-supplied cloud AI providers, bounded adaptive optimization | **FUTURE** |

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

**Status: RESUMED 2026-09-23 — see §0.** The baseline-stream-health target
table was met (`D-BASE` close-out); Phase C continues on Linux at C3.

Phase C turns the current proven native game stream into a reusable, measurable,
adaptive streaming platform.

**The Windows/GTX 970 reference host language below is historical.** Linux
migration has happened: the companion runs on the HP EliteDesk host with
`h264_vaapi`, wired directly into the Opal since `D-BASE-B2`. Measurements
are still intended to validate streaming architecture and client
capability, **not** to establish the eventual Linux minimum hardware
requirement.

### Phase C remote-readiness constraint

Phase C remains a local-streaming implementation phase, but its outputs are
critical prerequisites for future secure remote operation.

Design Phase C so that later WAN work can reuse, rather than replace:

- named stream profiles and capability gates;
- transport/FEC telemetry;
- RTT/jitter/loss/goodput/queue measurements;
- adaptation reason codes and bounded fallback behavior;
- source/capture -> profile/encoder -> transport/FEC -> decoder boundaries;
- status/session contracts that do not become more dependent on source address
  as durable client identity.

Do **not** add Tailscale, travel-router logic, WAN authentication, or remote
session routing in Phase C. Those belong to Phase G after the Linux core is
migrated and characterized.

Future WAN adaptation should protect interactivity first: reduce quality or
bitrate before allowing queue/buffer growth to create runaway latency. Random
loss and capacity pressure must remain distinguishable so FEC is not increased
blindly during congestion.

The current reference session is not just a 7 Mbps video stream. PCM16 stereo
audio is about 1.536 Mbps before packet/tunnel overhead, and 8+1 video FEC adds
parity overhead. Use roughly 10-11 Mbps outbound per reference session as a
planning estimate for later WAN testing without changing the stable PCM audio
path in Phase C.

## C1 — Explicit stream profiles

Convert current hard-coded behavior into named, inspectable profiles without
changing the validated 720p60 behavior.

Reference profile:

```text
Native Game 720p60
1280x720 @ 60
H.264
NVENC (Windows) / VAAPI (Linux, current)
~7 Mbps target
P1 / ultra-low-latency
GOP 15
no B-frames
max frame size 90,000 bytes   (Linux h264_vaapi, adopted 2026-09-22)
audio queue 12 / 17 packets   (5 ms each; adopted 2026-09-23)
audio redundancy 2 copies, 4-packet offset (adopted 2026-09-23)
RTP-sized UDP, 1200-byte packets
8 data + 1 XOR parity
payload type 96
```

The frame-size cap is a **transport** parameter: it bounds the per-frame
burst that meets the wireless queue, and adopting it cut packet loss 7-9x
at no measurable cost in bitrate, frame rate or encoder time
(`docs/memory/decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`). It is honoured
by the Linux `h264_vaapi` path only; the NVENC path ignores it.

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

The contract should remain useful on both local and future overlay/WAN paths; later Phase G may add overlay/path-state fields without replacing the Phase C core.

## C3 — Adaptive bitrate

Change bitrate first while keeping resolution and 60 fps fixed.

Required behavior:

- bounded min/max;
- fast decrease / slow increase;
- hysteresis;
- congestion hold-down;
- no rapid oscillation;
- explicit diagnostics/reason codes;
- safe fallback to a known profile;
- protect latency before image quality: degrade quality before queue growth is allowed to run away.

**C3-F1 (2026-09-25):** recovery's encoder restart is level-preserving at
every ladder level, measured WORKING at 5000 / 5500 / 6000 / 7000. This is
the `C3.L4` precondition from `C6-D1` finding 7
(`docs/memory/evidence/C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`).

**C3 status, 2026-09-28:** `C3.L3a` **complete** — four pre-registered
sessions pooled; at W 5.0 ramps marked 15/20 (29 marks vs 8.52 chance),
jumps 6/20 (6 vs 3.21), decoys at or below chance
(`docs/memory/evidence/C3_L3A_R4_SESSION4_2026-09-28.md`). **`C3.L4`
AUTHORIZED, single transition per event; live build pending** — the
user's reading: one restart per adaptation event straight to the target,
the existing hold-downs as minimum spacing, no ramps; no live run before a
fault-injection night with the user's `nft`
(`docs/memory/decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`).

**`C3-L4-L1` (2026-09-28): the live mode is BUILT**, behind
`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by default.

- **Tests and replays.** 43 live and 21 shadow tests pass; the shadow is
  unchanged. Parity with the shadow night is zero actions. On the
  recorded loss nights there is at most 1 transition in any 10 minutes.
- **Session A** (30 min, clean link): **SILENT**.
- **Session B** (injected FALLBACK): **PARTIAL (B6)**.
  - Met: one transition 7000 → 5000, a 171 ms gap, the blackout, and the
    second trigger refused by the hold-down.
  - Not met: the increase path never fired. The pre-registered rule, 90
    *consecutive* clean reports, is not reachable in attract mode (the
    clean counter peaked at 21 / 32).
- **Next.** The user's call on the increase rule, then the user's `nft`
  night, with the hand-step list in
  `docs/memory/evidence/C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`.

**`C3-L4-L2` (2026-09-29): the increase rule is the user's blend**
(`docs/memory/evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md`).

- **The rule.** "Clean" means fps ≥ 57, queue ≤ 1 and gap ≤ 150. The
  stream steps up one rung when ≥ 85 of the last 90 reports since the
  last SSRC change are clean.
- **Session B2 climbed 5000 → 5500 → 6000 → 7000**, one rung per event,
  and held 7000 for 14 min.
  - There was 0 loss at the four transitions.
  - The session scored **PARTIAL (W4)**: the pre-registered close-out
    loss row was missed on two non-transition bursts at 7000.
- **Also built:** per-report sample rows in live, and the user's `nft`
  harness `tools/c3_l4_nft_night.py`, dry-run tested.
- **Next**: the user's `nft` night.

**`C3-L4-N1` (2026-09-29): the first `nft` night, then the user's two
new rules.**

- **Night 1 is NOT "WORKS UNDER LOSS".** Under the capacity cap the
  controller never stepped down.
  - The client drops frames rather than queueing them, so the shadow's
    queue/gap triggers only met their bar inside freezes, which recovery
    owned.
  - Recovery restarted at 7000 nine times in F1.
  - F2 (loss alone), the recovery interlock and the kill switch all
    held.
  - Record: `docs/memory/evidence/C3_L4_NFT_NIGHT1_2026-09-29.md`.
- **The user approved two rules**, live only:
  - **the capacity trigger**: fps < 50 on 5/5 and lost ≥ 50 on ≥ 3/5 →
    FALLBACK 5000;
  - **the recovery-escalation backstop**: two recovery restarts at one
    level within 180 s → one FALLBACK after PLAYING.
- **Built and checked.**
  - Tests: 85 live, 21 shadow, 23 harness.
  - Replays: night 1's caps fire capacity at +13.6 / +16.7 / +19.7 s,
    and nothing fires on any clean-link series (the stop rule PASS).
  - A 30-min live hold was SILENT.
  - Record: `docs/memory/evidence/C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`.
- **Next**: the user's `nft` night 2,
  `tools/c3_l4_nft_night.py --only F1,F3`, under its written
  pre-registration.

**`C3-L4-N2` (2026-09-29): night 2, then the user's mild rule.**

- **Night 2 is WORKS UNDER LOSS (F1, F3)**
  (`docs/memory/evidence/C3_L4_NFT_NIGHT2_2026-09-29.md`).
  - Capacity acted at +14 s; the blend climbed to 6000.
  - The recovery restart held 5000 on real loss.
  - **But 6000 under the cap sat degraded for 4 min**, under every bar.
- **The user approved `capacity_mild`**: ROUTINE one rung down on fps <
  57 on ≥ 4/5 and lost ≥ 50 on ≥ 3/5.
- **Built and checked** (102 live tests; the stop rule PASS).
  - On night 2's samples it steps 6000 → 5500 at 119 s into the rung,
    after the reversal hold-down.
  - A 30-min live hold made 0 transitions, but missed the close-out loss
    row on link bursts.
  - Record: `docs/memory/evidence/C3_L4_N2_MILD_CAPACITY_2026-09-29.md`.
- **Next**: the user's `nft` night 3, `--only F1`.

**`C3.L4` CLOSED (2026-09-30): live VALIDATED UNDER REAL LOSS.**

- Night 3 was **WORKS UNDER LOSS (F1)** with the pre-registered shape:
  capacity at +15.5 s, the climb to 6000, `capacity_mild` back at 121 s,
  then HOLD `oscillation` at 5500
  (`docs/memory/evidence/C3_L4_NFT_NIGHT3_2026-09-30.md`).
- The controller as built is authorized
  (`docs/memory/decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, the
  close; the rules tabled in `architecture/ADAPTIVE_BITRATE.md`).
- **Live stays behind `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by
  default. Adoption, meaning live on by default, is pending the user.**
- **ADOPTED 2026-10-01 (`C3-L4-D1`): live is the default**, through the
  unit's drop-in `privyhub-companion.service.d/adaptive.conf`. The user's
  authorization, 2026-09-30: "do the loss row look first and then the
  live default".
  - The harness preflights now accept that one name.
  - Kill switches: delete the drop-in (off), or the disable route (shadow
    for one session).
  - Records: `docs/memory/decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`
    and `docs/memory/evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`.
- Open, the user's: the ROUTINE reversal hold-down (~120 s) bounds the
  mild step's delay.

**The C3 required behaviour, and the record that shows each item:**

| item | shown by |
| --- | --- |
| bounded min/max | the ladder 5000-7000 (`LADDER_KBPS`). Decreases refuse `at_floor` at 5000 and increases stop at 7000. The nights never left it (`C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`; nights 2-3). |
| fast decrease / slow increase | capacity 7000 → 5000 at +14-16 s under a cap (nights 2 and 3); increases one rung per ≥ 93 reports (186 s), 111 / 93 on night 3 (`C3_L4_NFT_NIGHT3_2026-09-30.md`; B2 in `C3_L4_L2_INCREASE_RULE_2026-09-29.md`). |
| hysteresis and congestion hold-down | the blend's 85-of-90 window and the hold-down table. Night 3's two `hold_down` refusals of the mild step (`C3_L4_NFT_NIGHT3_2026-09-30.md`). |
| no rapid oscillation | the oscillation guard: night 3's third direction change became HOLD at 5500 for the session. The rate limit was never reached. |
| explicit diagnostics / reason codes | `trigger` and reason on every decision row; one `sample` row per report; `escalation_armed` rows (`C3_L4_L2_…`, `C3_L4_N1_…`). |
| safe fallback to a known profile | FALLBACK → 5000 on the reference profile; BACK resets to 7000; the disable route on night 1's K; recovery level-preserving (`C3_F1_…`, `C3_L4_NFT_NIGHT1_2026-09-29.md`). |
| protect latency before image quality | decreases act on fps and loss before any queue grows (queue ≥ 1 on ≤ 2 % of the reports under a cap on any night). Under the cap, recovery restarted 9 times on night 1 and 0 times on nights 2-3 (the three night records). |

## C4 — Adaptive FEC

Only after bitrate adaptation is stable.

Distinguish random packet loss from capacity pressure. Do not blindly increase
parity during congestion.

If fixed 8+1 remains the better engineering choice, explicitly defer dynamic FEC
with evidence rather than adding complexity for its own sake.

**C4-D1 (2026-09-24), the pre-registered rule applied to the stored
adopted-build corpus: BUILD (static k+2 first). Adaptive FEC is not
supported.** 8+1 leaves ~9.1 lost/min at the median, mostly two-packet gaps
inside one group. k+2 would restore at most 7.7/min (upper bound), point
estimate ~3.1, at 32 % parity against 16 %. No load column moves with the
loss. C4 moves to a design task, queued behind C3; its first step is a
measured k+2 / 8+1 arm, not an adoption
(`docs/memory/decisions/C4_ADAPTIVE_FEC_2026-09-24.md`).

**C4-M1 (2026-09-25): the measured arm (8+2, `xor8_2`, behind an override)
did NOT SHOW a post-FEC gain.** It won 1 of 3 pairs, with the A median at
69 % of B's. It did recover more, but raised pre-FEC loss 2-3×. The cost
rows were within noise. Nothing was adopted; the profile stays 8+1
(`docs/memory/evidence/C4_M1_FEC_ARM_2026-09-25.md`).

**C4 closed for Phase C (2026-09-28, the user's call: agreed, no
adoption).** `xor8_1` 8+1 stays; the 8+2 arm remains in the tree behind
`PRIVYHUB_FEC_SCHEME`, dormant
(`docs/memory/decisions/C4_ADAPTIVE_FEC_2026-09-24.md`, appended).

## C5 — 1080p60 capability characterization

**Current status — the user's reading of 2026-10-01: C5 is reopened.
1080p60 is a Phase C deliverable, delivered through the adaptive ladder
as a rung above 7000, not only a characterization.** C5-M1 and C5-M2
characterized the stream on a source with 720p detail (the 879×720
window, upscaled 1.5×) and on an unsettled link. C5-M4 is the
source-side step, with the PS1 source rendering natively at 1080p. The
rung itself is Part 2, after the user's link work: the 40 MHz change on
the Opal and the LINK-L1 re-run. PS1 comes first, because it maps onto
PS2-class emulation later.

**C5-M4 Part 1 (2026-10-01): the PS1 source at native 1080p — measured
and proposed, nothing adopted.**

- The window becomes 1920×1080 through RetroArch fullscreen, with the 4:3
  picture pillarboxed. The companion's argv is unchanged.
- Beetle PSX HW offers 1x, 2x, 4x and 8x (no 3x).
- **1x, 2x and 4x hold 60** with no stream, with the adopted 7000 stream
  and with the c3 1080p arm. 8x misses by one 256-frame interval.
- **The candidate is 4x**: GPU 21 % against 15 % with the stream.
- Offline, on the 3D demo segment, content SSIM against the 4x reference
  as shown:
  - today 0.838;
  - **the 4x source through today's 720p/7000 0.873** (the quick win, at
    the same link cost);
  - 1080p/12,600/90 KB 0.902 (parity 0.912; GOP 30 0.908).
- The 1080p arms pulse at the IDR rate under the 90 KB cap.
- The proposed source config (a PS1 core override plus internal
  resolution 4x) is written, not applied. The rung's needs are listed for
  Part 2: ~15.4 Mbit/s on the wire, and the actuator's size change.
- `docs/memory/evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md`.

Characterize 1080p60 using the current development host and onn client.

This is a **stream/client capability test**, not a future Linux resource-sizing
benchmark.

1080p60 should become capability-gated rather than universally assumed.

**C5-M1 (2026-09-28): 1080p60 characterized — NOT CAPABLE (stream) at the
parity candidate** (15,750 kbps, cap 200,000 B). The onn's decoder is
capable (1920x1080 delivered, no client change) and so is the host encoder
(59.99 fps). Over the 5 GHz hop, all three candidate holds missed spikes
and post-FEC video loss, from the per-frame burst at 2.25× the frame
size. The candidate stays behind `PRIVYHUB_NATIVE_PROFILE_ID`, never the
default; nothing is adopted
(`docs/memory/evidence/C5_M1_1080P60_PROFILE_2026-09-28.md`,
`docs/memory/decisions/C5_1080P60_CAPABILITY_2026-09-28.md`).

**C5-M2 (2026-09-29/30): the three 1080p follow-up arms — INCONCLUSIVE
(link), twice.**

- The arms: parity with the 90 KB cap; 80 % with a scaled cap; 80 % with
  the 90 KB cap.
- In both screening nights the adopted 720p B holds missed the baseline
  on loss (3/4, then 4/4). The confirmation night was NOT RUN.
- No arm met the targets on either night.
- `docs/memory/evidence/C5_M2_1080P60_FOLLOWUP_2026-09-29.md`.

**C5-M3 (2026-09-30): the low rungs for Phase G.**

- Offline, content SSIM: 7000 0.994 … 4000 0.990, 3000 0.988, 540p/3500
  0.987. No 4 Hz IDR pulse at any rung.
- Transport, on the conclusive re-run:
  - **720p/4000 passes** (5.0 Mbit/s on the wire), and met every row on
    both nights;
  - 720p/3000 and 540p/3500 do not.
- Nothing joins the live ladder.
- `docs/memory/evidence/C5_M3_LOW_RUNG_SCREENING_2026-09-29.md`.

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

### D-071 Windows stop boundary

The Windows implementation is not required to complete an NVENC-specific
automatic bitrate/FEC controller before Linux migration.

Portable Windows results retained for Linux reuse include explicit profiles,
C2 telemetry, startup stabilization/readiness, fixed-bitrate evidence, and the
backend-neutral actuator capability model.

`video_only_restart` is bidirectionally functional but produces roughly one
second of gameplay interruption and is not accepted for seamless automatic
adaptation.

Automatic bitrate/FEC continuation, Linux bitrate-envelope revalidation, and
backend actuation classification move to Phase D/E.

Acceptance:

- explicit profiles;
- transport telemetry contract;
- adaptive bitrate runtime validated;
- adaptive FEC validated or explicitly deferred;
- 1080p60 characterized;
- generalized source contract established;
- Games regression passes;
- Phase C artifacts are explicitly reusable by future Phase G remote/WAN work without implementing remote transport here;
- clean checkpoint/push.

**C7 status, 2026-09-25 (`C6-D1`)** — each acceptance item and the record it rests on:

| item | status | record |
| --- | --- | --- |
| explicit profiles | ✓ | C1 (`native_stream_profiles.py`; cap, cushion, redundancy adopted) |
| transport telemetry contract | ✓ | C2 (`privyhub_stream_telemetry_v1`, heartbeat v3, decoder report v2) |
| adaptive bitrate runtime validated | ✓ **`C3.L4` CLOSED 2026-09-30: live VALIDATED UNDER REAL LOSS on three `nft` nights (1 NOT → capacity + backstop; 2 WORKS UNDER LOSS → `capacity_mild`; 3 WORKS UNDER LOSS, the pre-registered HOLD shape); live behind its flag; **live ON BY DEFAULT since 2026-10-01 (`C3-L4-D1`, the unit drop-in; the user's authorization 2026-09-30).** History: shadow built and SILENT; live AUTHORIZED 2026-09-28 (single transition per event); **live BUILT (`C3-L4-L1`): SILENT on a clean link, decrease proven on injection; the increase rule replaced by the user's blend (`C3-L4-L2`: climb 5000→7000 shown on injection); `nft` night 1 (2026-09-29): no decrease under a cap → the user's capacity trigger + recovery-escalation backstop built (`C3-L4-N1`: replays PASS, 30-min live hold SILENT); `nft` night 2 WORKS UNDER LOSS (2026-09-29) → the user's `capacity_mild` built (`C3-L4-N2`: stop rule PASS, 30-min hold 0 transitions); night 3 WORKS UNDER LOSS (2026-09-30)** | `C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`; `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`; `C3_L4_NFT_NIGHT3_2026-09-30.md`; the decision's close; `C3-L4-S1`; `C3.L3a` sessions 1-4; `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`; `C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`; `C3_L4_NFT_NIGHT1_2026-09-29.md`; `C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`; `C3_L4_NFT_NIGHT2_2026-09-29.md`; `C3_L4_N2_MILD_CAPACITY_2026-09-29.md` |
| adaptive FEC validated or explicitly deferred | ✓ **explicitly deferred** (2026-09-28, the user's call): adaptive not supported; static 8+2 NOT SHOWN; 8+1 stays; arm dormant | `decisions/C4_ADAPTIVE_FEC_2026-09-24.md`, `C4_M1_FEC_ARM_2026-09-25.md` |
| 1080p60 characterized → **delivered through the ladder** (the user's reading, 2026-10-01) | **open (reopened 2026-10-01)**: 1080p60 is a Phase C deliverable as a ladder rung above 7000, not only a characterization. Done so far: characterized on a 720p-detail source (C5-M1 NOT CAPABLE at parity; C5-M2 INCONCLUSIVE (link) twice); **C5-M4 Part 1 (2026-10-01): the PS1 source at native 1080p measured — 4x HOLDS 60, proposal written, not applied**. Remaining: the user's picture decision on the source config, the link work (40 MHz, LINK-L1 re-run), then Part 2 (the rung). Low rungs screened for Phase G (C5-M3: 720p/4000 passes transport) | `C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md`; `C5_M1_1080P60_PROFILE_2026-09-28.md`, `decisions/C5_1080P60_CAPABILITY_2026-09-28.md` |
| generalized source contract established | ✓ on paper and as an unused interface | `architecture/NATIVE_SOURCE_CONTRACT.md` (`C6-D1`) |
| Games regression passes | ✓ all 9 scripted rows PASS (D7-R2); the user's hands-on rows reported fine (2026-09-28) | `D7_R1_LINUX_REGRESSION_2026-09-25.md` §R3 |
| reusable by Phase G remote/WAN | stated in the contract (a remote transport is another `Transport`; nothing implemented) | `architecture/NATIVE_SOURCE_CONTRACT.md` |
| clean checkpoint/push | **pending the user's commit** (Code commits nothing); the checkpoint record and the git status file are ready | `C7_D8_CHECKPOINT_2026-09-30.md`; `logs/c7_d8_git_status_2026-09-30.txt` |

**CL-B1 APK ADOPTED (2026-09-30)** by its pre-registered rule, as the
user authorized. The onn now carries **`de072762…835e`**
(`docs/memory/evidence/CL_B1_APK_ADOPTION_2026-09-30.md`,
`docs/memory/decisions/CL-B1_APK_ADOPTION_2026-09-30.md`). The history
follows.

**CL-B1 (2026-09-25):** the client's decoder report can travel as a POST
body, so the request line is no longer its ceiling. The companion accepts
both forms and raises the cap to 128,000, and the slow-event rings grew to
256 + 1,024. Built and tested; the adopted APK is reinstalled; adoption
waits for the user
(`docs/memory/evidence/CL_B1_DECODER_REPORT_BODY_2026-09-25.md`).

---

# Phase D — Linux Migration / Native Linux Baseline

**Status: ACTIVE — D5 complete/runtime accepted; D7 native Linux regression next; D6 remains deferred unless new evidence reopens it**

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

## D1 — Linux appliance baseline

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

## D2 — Migrate platform-neutral companion responsibilities

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

## D3 — Replace Windows-specific backends

Replace behind explicit platform boundaries:

```text
Windows Graphics Capture → Linux capture backend
NVENC                   → generic encoder API + Linux AMD hardware path
WASAPI process audio     → Linux source/process audio
ViGEm                    → Linux virtual input/uinput/evdev path
Windows lifecycle        → Linux service/process lifecycle
```

Preserve behavior, not Windows APIs.

## D4 — Restore PS1-and-below Games on Linux

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

### D4 controller parity checkpoint — 2026-09-16

Runtime validated on Linux:
- integrated gameplay controls across three different games;
- three different input profiles;
- default/autoconfig and named-profile controller paths after D-084/D-085.

Still required inside D4 before normal-use Games parity is complete:
- PS1 multiplayer / multitap Linux parity;
- representative multiplayer regression after the multitap boundary is fixed;
- remaining D4 normal-use regression/acceptance.

The Windows Phase-A multitap result is the behavior reference. Do not redesign
the feature until a Linux diagnostic identifies the first divergent boundary.

### D4 multiplayer checkpoint — 2026-09-16

Runtime validated on Linux:
- PS1 Port-1 multitap in Crash Bash;
- Players 3/4 available;
- four independent remotes/controllers;
- D-087 XDG/user Config-root portability fix;
- D-087R1 external Config-path metadata fix.

The dedicated multiplayer blocker is closed.

Still required inside D4 before normal-use Games parity is complete:
- representative final normal-use regression/acceptance across the required
  Games lifecycle and feature paths.

After D4 acceptance, continue to D5 media/server restoration.

### D4 final Linux acceptance — 2026-09-16

**D4 status: COMPLETE / RUNTIME ACCEPTED WITH EXPLICIT NO-FIXTURE SKIPS.**

Final representative regression passed:
- Games library/search/art;
- SNES normal launch, video/audio/input, analog-to-D-pad convenience, End and
  uinput cleanup;
- PS1 normal launch, video/audio/input, pause/frozen preview, Save/Load, resume,
  End and uinput cleanup;
- cheat profile;
- IPS mod profile;
- named A8 input profile;
- fresh launch/recovery after repeated teardown;
- previously validated PS1 four-player Port-1 multitap.

Coverage-aware exclusions:
- NES had zero local fixtures and is not claimed as Linux runtime validated;
- Genesis had zero local fixtures and is not claimed as Linux runtime validated.

Final classification:
`D4_FINAL_GAMES_REGRESSION_CONFIRMED_WITH_NO_FIXTURE_SKIPS`

Proceed to D5 media/server restoration.

## D5 — Restore media/server functionality

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:ROADMAP:BEGIN -->
### D5 external-VOD runtime checkpoint — 2026-09-16

D-092 is runtime validated through the normal onn path.

Confirmed:
- scanner-generated external-storage-backed VOD source-start;
- normal movie playback;
- Continue Watching.

Checkpoint-installer history:
- D-093 rolled back because its transformer expected the wrong D5 heading level;
- D-093R1 rolled back because its post-write validation expected a roadmap
  marker that its inserted roadmap block did not contain;
- D-093R2 corrects that installer-only consistency defect.

The temporary symlink is not the final storage architecture.

**Next D5 task:** first-class configurable bulk-media root, preserving the
repo-local default and clean unavailable-storage behavior.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:ROADMAP:END -->

Restore the currently working media/server functions at the Linux migration boundary without broadening scope:

- companion/control API;
- VOD;
- Live TV/EPG;
- browser/live source where active;
- camera source where active;
- diagnostics/Self-Test;
- Phase C profile/telemetry/stabilization infrastructure;
- existing media state/cache and working playback paths.

### D5 Prototype-1 bulk-media storage constraint

The current Linux Prototype 1 has limited internal disk capacity relative to the
VOD/movie library. During this phase, bulk VOD content may live on an external
hard drive.

D5 must preserve a configurable media-storage boundary:

- do not require bulk VOD assets to be copied into the PrivyHub project or
  internal system disk;
- keep small catalog/metadata/cache/configuration state internal where practical;
- treat an unavailable/unmounted external media root as storage unavailable,
  not as authoritative deletion of the user's library;
- do not hard-code a specific external mount path or removable-storage quirk;
- preserve a migration path from the temporary external disk to later dedicated
  server/storage infrastructure without redesigning VOD/library identity.

This is a deployment/architecture constraint, not a requirement that future
PrivyHub systems use removable storage.

### D5 final closeout — 2026-09-17

**D5 status: COMPLETE / RUNTIME VALIDATED.**

Final focused automated regression passed after the schema-v2 diagnostic
projection repair, followed by a clean manual onn smoke for Live TV playback,
Favorites/guide navigation, and VOD playback.

D5's validated Linux media/server baseline now includes external VOD, Live TV,
EPG, durable Linux TV state, guide UX/status, and responsive TV/Favorites
navigation.

D6 remains deferred. Proceed to D7 native Linux regression, then D8 Linux
baseline checkpoint.

## D6 — Replay deferred UDP investigation

Rerun the saved forward/reverse transport acceptance suite on the representative
Linux + home Opal + onn path.

Classify whether the prior packet timing/duplication pathology was:

- specific to the old Windows/test environment;
- reproduced on the representative Linux + home Opal + onn path;
- or indicative of a broader transport issue.

Do not reopen beyond evidence.

**D6-R1 (2026-09-24): REPLAYED; NOT REPRODUCED in either direction →
specific to the old environment.** Three valid runs each way, idle, on the
host-wired → Opal → onn path:
- same-stamp duplication 0-4 per run, against 476-2,626 on 2026-09-15;
- transformation ~14-20× lower; host UDP errors +0.

The 2026-09-15 runs had the host on its USB Wi-Fi adapter.
(`docs/memory/evidence/D6_R1_UDP_SUITE_REPLAY_2026-09-24.md`)

## D7 — Native Linux regression

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

**D7-R1 (2026-09-25): scripted and run twice** (`tools/d7_regression.py`).
- 8 of 10 rows PASS in both passes: boot, discovery, media, launch,
  video/audio/controller (automated part), pause/resume, Save/Load, End.
- restart/recovery VALIDATED (cited: `R3`-`R3d`, `R3c2`).
- profiles/cheats/mod state FAIL as scripted, from a script defect; every
  field read as expected. A next pass scores it directly.
- **NEEDS USER**: controller feel and picture, a ten-minute list
  (`docs/memory/evidence/D7_R1_LINUX_REGRESSION_2026-09-25.md`).

**D7-R2 (2026-09-25)**: the fixed script, in one full pass with a game
active, scored **all 9 scripted rows PASS**, the profiles row included.
restart/recovery is cited.

**D7: complete on the adopted build (2026-09-28)** — 9 scripted PASS,
1 cited (restart/recovery), and the hands-on rows reported fine by the
user with Tekken 3 ("everything ran fine … maybe the smallest of screen
artifacts in the beginning"; `D7_R1_LINUX_REGRESSION_2026-09-25.md` §R3).

## D8 — Linux baseline checkpoint

Acceptance:

- Linux is sufficient for normal core server operation;
- PS1-and-below works through Linux-native A/V/input paths;
- onn client remains functional; **met on D7-R1's scripted rows (2026-09-25)**;
- media/Live TV remain functional;
- deferred UDP suite replayed/reclassified; **met 2026-09-24 (`D6-R1`: not reproduced, specific to the old environment)**;
- no minimum-hardware claim yet;
- clean checkpoint/push.

Architectural statement:

> PrivyHub has a working Linux-native core suitable for formal resource characterization.

---

# Phase E — Linux Core Resource Characterization & Optimization

**Status: PLANNED AFTER D**

Phase E deliberately limits the core emulator workload to:

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

## E1 — Freeze the workload suite

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

## E2 — Whole-system measurements

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

## E3 — Optimization loop

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

## E4 — Core Linux resource envelope

Produce:

- **Known-good reference:** 4650G/16 GB prototype;
- **Measured floor:** lowest demonstrated capability for defined workloads;
- **Recommended alpha:** floor plus reliability/update/concurrency headroom;
- **Optional higher tier:** stronger profiles without redefining Core.

## E5 — Capability detection and graceful scaling

PrivyHub should classify:

- CPU/RAM/storage;
- GPU/iGPU;
- hardware encode/decode;
- validated stream profiles;
- emulator tiers;
- concurrency headroom;
- network capabilities.

Features should enable only where the host/client pair is known to support them.

## E6 — Select Prototype 2 / friend-alpha hardware

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

## E7 — Resource checkpoint

Acceptance:

- repeatable workload suite;
- PS1-and-below scope preserved;
- worthwhile bottlenecks optimized;
- resource/power envelope documented;
- capability model established;
- Prototype 2 class selected from evidence;
- clean checkpoint/push.

---

# Phase F — Media Library, VOD & Live TV UX

**Status: PLANNED AFTER E**

Phase F now covers both local media-library polish and a deliberate Live TV
cleanup/rebuild.

The existing Live TV playback path should be preserved where it is stable, but
the current channel organization and guide behavior should **not** be treated as
finished architecture.

## F1 — Recursive VOD artwork

Support local sidecar art and directory-oriented movie layouts without rewriting
canonical media.

Priority may include:

1. exact video-stem artwork;
2. `poster.*`;
3. `folder.*`;
4. cached provider art;
5. generated local thumbnail;
6. generic tile.

## F2 — VOD metadata cache

Potential fields:

- title/year/runtime;
- genre/description;
- poster;
- resolution/codecs;
- audio/subtitle information.

External lookup remains optional and cacheable. Normal browsing/playback must
remain local-first.

## F3 — Playback-state UX

Potential layers:

- resume position;
- watched/unwatched;
- recently played;
- favorites;
- collections/series;
- sort/filter/search;
- future per-user state.

Canonical media files remain untouched.

## F4 — Live TV channel normalization

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

## F5 — EPG / guide foundation

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

## F6 — Live TV guide UX

Once the underlying EPG data is trustworthy:

- current/next program;
- timeline/grid view where practical;
- channel details;
- jump to current time;
- category/favorites filters;
- clear "guide unavailable" behavior;
- responsive onn-TV navigation.

Do not hide data-quality failures behind empty UI.

## F7 — Media/TV checkpoint

Acceptance:

- recursive VOD library remains stable;
- metadata/art work offline after caching;
- Live TV channel list is normalized and manageable;
- guide matching/refresh behavior is diagnosable;
- normal channel playback does not depend on guide success;
- checkpoint/push.

---

# Phase G — Secure Remote Access / Portable Client Foundation

> **Data waiting for Phase G (C5-M3, 2026-09-30):** three low rungs
> screened on the home link behind the profile selector, never on the live
> ladder. 720p/4000 passed transport at 5.0 Mbit/s on the wire; 720p/3000
> and 540p/3500 did not. The offline SSIM / IDR-pulse table and the
> on-air rates are in
> `docs/memory/evidence/C5_M3_LOW_RUNG_SCREENING_2026-09-29.md`. The remote
> floor is the user's choice when Phase G starts.

**Status: FUTURE AFTER F**

Phase G establishes secure optional remote use on top of the validated,
optimized Linux core before heavier emulator families are introduced.

This ordering is deliberate. Remote work adds NAT/SNAT, overlay routing,
identity/authentication, WAN latency/loss/jitter and portable-client variables.
Those should be characterized against the simplest mature PS1-and-below
workload instead of being mixed with new N64/GameCube/PS2 compatibility and
resource variables.

Local operation remains authoritative and must continue to function when remote
connectivity is absent.

## G0 — Correct trust topology and threat model

Home topology:

```text
Internet / ordinary household upstream
              |
          home Opal
   PrivyHub trust/network domain
      |                   |
future Linux hub      local PrivyHub clients/devices
```

The ordinary household router/Wi-Fi is upstream connectivity, not part of the
PrivyHub trust domain.

Remote topology:

```text
remote uplink
   |
travel GL-iNet-class router
portable trusted client LAN
   |
onn / future handheld
   |
secure overlay
   |
future Linux hub on the home Opal domain
```

The travel router owns uplink changes. Portable clients should remain configured
to the travel router's trusted LAN rather than being reconfigured for each
hotel/friend/work network.

Remote access must never flatten or expose the ordinary household LAN.

## G1 — Overlay provider abstraction

Use a provider boundary instead of hard-coding one overlay product into the
PrivyHub session architecture.

First prototype candidate:

- Tailscale terminated on the future Linux hub.

Future/provider alternatives may include:

- direct WireGuard;
- self-hosted/local-first coordination;
- another secure overlay that satisfies the same contract.

Tailscale is the preferred first implementation candidate, not the permanent
architecture contract. The home Opal does not need replacement merely to add
Tailscale if the Linux hub can terminate the home-side overlay.

Useful provider state should include, where available:

- connected/disconnected;
- direct vs relayed path;
- reachable overlay endpoint;
- MTU/path constraints;
- peer/session readiness;
- provider-specific diagnostics kept behind the provider abstraction.

## G2 — Portable trusted-LAN / travel-router baseline

Select and validate a travel GL-iNet-class router only when Phase G begins.

Do not choose the permanent travel-router model now.

Required behavior:

- onn/future handheld stays on the travel router's trusted LAN;
- router can join Ethernet or Wi-Fi uplinks;
- overlay survives ordinary uplink changes;
- client configuration does not depend on the visited network;
- loss of overlay fails closed for remote PrivyHub access;
- local client/router management remains possible without exposing PrivyHub
  services to the visited LAN.

## G3 — WAN session identity and application authorization

The current LAN prototype may derive reachable media/controller targets from the
request source address. That mechanism is not a durable remote identity model
because a portable client may sit behind NAT/SNAT on the travel router.

Phase G must separate:

```text
client identity
session identity
reachable video/audio/controller endpoints
overlay/path state
authorization/permissions
```

Do not use source IP as durable client identity.

Secure overlay membership is transport protection, not sufficient PrivyHub
authorization. Possession of the travel router or access to the overlay must not
grant unrestricted application authority.

Add explicit application authentication/authorization with fail-closed session
setup and auditable permissions.

## G4 — PS1-and-below off-site remote baseline

Use the mature Core workload first:

```text
NES
SNES
Genesis
PS1
```

Minimum real off-site onn validation:

- authenticated control/session setup;
- Games discovery/launch;
- video;
- process audio;
- controller input;
- Pause/Resume;
- Save/Load;
- End/teardown;
- reconnect/recovery;
- local behavior unchanged when overlay is absent.

The current 720p60 reference path should be treated as roughly 10-11 Mbps
outbound per session for planning once video, 8+1 parity, PCM16 stereo audio and
packet/tunnel overhead are considered. Measure the real envelope rather than
turning this estimate into a hard requirement.

## G5 — WAN-aware telemetry and adaptation

Reuse Phase C telemetry/adaptation instead of creating a parallel WAN streamer.

Measure and classify:

- delivered goodput;
- packet loss;
- FEC recovery/unrecoverable groups;
- jitter/inter-arrival behavior;
- RTT/echo latency;
- sender pacing;
- queue/buffer growth;
- decoder starvation/stale drops;
- direct vs relayed overlay path where available;
- MTU/fragmentation symptoms;
- reconnect/path-change events.

Remote adaptation priority:

1. preserve control/session correctness;
2. prevent runaway latency;
3. reduce bitrate/quality when capacity tightens;
4. use FEC only when loss characteristics justify it;
5. recover upward slowly with hysteresis.

Do not hide a bad WAN path with ever-growing buffers.

## G6 — Portable handheld validation

When representative hardware exists, validate an X28-class Android handheld or
similar low-cost client:

- reuse the Android client where practical;
- hardware AVC decode;
- 720p60 baseline;
- built-in controls;
- Games/VOD/TV browsing;
- session/pause UX;
- battery/network behavior;
- travel-router operation;
- optional dock/TV use.

Absence of handheld hardware must not block the onn-based Phase G remote
foundation.

## G7 — Existing-PC / Steam provider over the remote foundation

Use an existing gaming PC/laptop as optional external compute without making it
part of the core server requirement.

PrivyHub owns discovery, readiness, library/orchestration, permissions and
session UX.

Prefer a direct provider-to-client media path when the provider already solves
streaming better than routing media through the Linux hub, while preserving the
same PrivyHub authorization/session boundary.

## G8 — Adverse-network characterization

Exercise bounded representative conditions:

- reduced bandwidth;
- added latency;
- jitter;
- random loss;
- burst loss;
- reordering where practical;
- overlay path changes/direct-vs-relayed conditions.

Record the operating envelope and failure behavior. Avoid claiming a universal
Internet requirement from one ISP/path.

## G9 — Remote foundation checkpoint

Acceptance:

- corrected trust topology documented;
- overlay provider abstraction established;
- first provider path validated;
- travel-router trusted-LAN baseline validated;
- source address separated from durable client/session identity;
- application authentication/authorization validated;
- real off-site onn PS1-and-below session validated;
- Phase C telemetry/adaptation reused under WAN conditions;
- adverse-network envelope documented;
- handheld validated if representative hardware is available, otherwise
  explicitly pending;
- Steam/external-compute provider integrated or explicitly deferred with a
  preserved provider contract;
- ordinary household LAN remains outside the PrivyHub trust domain;
- local operation remains functional without remote connectivity;
- clean checkpoint/push.

---

# Phase H — Extended Emulation & User-Content Import

**Status: FUTURE AFTER G**

This phase adds the user-owned content pipeline before introducing heavier
console workloads. It runs after Phase G has established the reusable secure
remote/client contract so later emulator families can validate locally first and
then regress over that existing remote foundation.

PrivyHub will **not** provide or fetch ROMs, ISOs, BIOS/firmware, keys, or similar
game content.

## H0 — User-content import contract

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

## H1 — N64

Evaluate representative N64 emulation, controllers, saves, local rendering,
native streaming, CPU/iGPU cost, latency, and compatibility.

Question:

> Does the optimized core/alpha hardware already have enough margin for N64?

## H2 — GameCube

Evaluate bounded representative titles:

- native/default rendering first;
- modest upscale only after baseline;
- CPU/iGPU pressure;
- stream/encoder interaction;
- latency/stability;
- thermals;
- compatibility outliers.

## H3 — PS2

Evaluate representative easy/moderate/heavy titles:

- CPU thread pressure;
- iGPU pressure;
- hardware renderer;
- native/default resolution first;
- streaming overhead;
- game-specific compatibility;
- sustained thermal behavior.

User-supplied PS2 BIOS should enter only through the G0 import boundary.

## H4 — Extended-emulation tiers

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

## H5 — Extended-emulation checkpoint

Acceptance:

- content import pipeline validated;
- no project-supplied ROM/ISO/BIOS requirement;
- N64 characterized;
- GameCube characterized;
- PS2 characterized;
- incremental resource costs compared with Phase F;
- local validation is followed by regression over the established Phase G remote contract where representative hardware is available;
- compatibility claims limited to tested evidence;
- base Core hardware remains independent unless evidence strongly justifies a
  change;
- clean checkpoint/push.

---

# Phase I — Home Infrastructure / Broader Plugin Expansion

**Status: FUTURE AFTER H**

PrivyHub expands from TV/media/games into a private local home-coordination
layer. Phase I builds on the secure remote/client foundation from Phase G rather
than inventing a second remote-access path.

## I1 — First-class plugin/provider architecture

Capabilities should be exposed once and callable from GUI, control API,
automation, voice, AI, and authorized remote sessions:

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

## I2 — Home Assistant / device provider

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

## I3 — Camera and microphone infrastructure

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

Remote camera/microphone access, if enabled, must reuse Phase G authentication,
authorization and transport boundaries.

## I4 — Storage / larger media server

Expand household storage:

- indexed media;
- larger DVD/VOD libraries;
- storage health;
- backup/maintenance;
- authorized optional remote streaming through the established Phase G boundary.

Storage capacity and compute sizing remain separate questions.

## I5 — Broader clients and household surfaces

Expand beyond the first onn/travel-client baseline:

- additional TV clients;
- handheld/docked use refinements;
- phone/tablet control surfaces;
- wall/control-panel clients;
- accessibility/alternate-input surfaces.

New clients reuse the established identity/session/permission model.

## I6 — Provider expansion

Expand providers beyond the initial Phase G Steam/external-compute work while
preserving one capability and permission model.

Potential areas:

- additional PCs;
- NAS/media services;
- local automation services;
- future local compute accelerators;
- specialized household devices.

## I7 — Home-infrastructure checkpoint

Acceptance:

- provider/plugin contracts are first-class;
- Home Assistant/device integration works locally;
- camera/microphone permissions are explicit;
- storage expansion preserves local-first behavior;
- broader clients reuse established identity/auth/session contracts;
- remote-capable features reuse Phase G rather than creating parallel exposure;
- clean checkpoint/push.

---

# Phase J — Local Intelligence / Voice / Privacy-Aware AI

**Status: FUTURE**

PrivyHub intelligence should be layered from deterministic/local to optional
external providers. No cloud AI provider is mandatory.

## J1 — Deterministic local automation first

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

## J2 — Local voice foundation

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

## J3 — Small local intent model

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

## J4 — Optional external AI provider abstraction

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

## J5 — Privacy boundary / data-minimization policy

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

## J6 — Privacy-aware camera/microphone intelligence

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

## J7 — Future first-party local LLM

Defer larger local open-weight inference until actual usage justifies the
hardware/cost.

It should plug into the same provider interface rather than create a parallel
control architecture.

## J8 — Local adaptive resource optimizer

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

Remote access is optional. Core local operation must not depend on an overlay,
travel router, WAN path, or remote authentication service being available.

## Network trust and remote authorization boundary

The home Opal defines the PrivyHub network/trust domain. The ordinary household
network is upstream connectivity only.

A secure overlay protects transport; it does not by itself authorize PrivyHub
actions. Remote sessions must pass the local PrivyHub identity/permission layer.

Source/request address is routing evidence, not durable client identity.

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

## Gate 6 — Remote foundation readiness

Do not begin Phase G WAN implementation until:

- Linux-native PS1-and-below core is functionally validated;
- Phase F resource/capability work is complete enough to avoid confusing host
  exhaustion with WAN failure;
- the deferred UDP suite has been replayed on the representative Linux + home
  Opal + onn path;
- Phase C telemetry/adaptation contracts are available for reuse.

Do not treat Tailscale, a specific travel-router model, or source IP as the
permanent architecture contract.

## Gate 7 — User-content import

Before enabling new N64/GameCube/PS2 libraries, validate the USB/removable-media
import path, idempotence, hashing, target mapping, and failure behavior.

## Gate 8 — Extended emulation

Do not allow N64/GameCube/PS2 to raise the Core minimum before incremental cost
is measured against the optimized Phase F baseline.

Run heavier-emulator local validation first, then regress over the established
Phase G remote contract rather than redesigning remote access per emulator.

## Gate 9 — Cloud AI

Do not add an external AI provider without:

- explicit opt-in;
- credential boundary;
- per-capability privacy model;
- data minimization;
- no silent fallback;
- local action validation.

## Gate 10 — Larger local AI

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
  (all designed for future Phase G WAN reuse)
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
  Linux + home Opal + onn UDP replay
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
G Secure Remote Access / Portable Client Foundation
  corrected trust topology
  overlay-provider abstraction
  travel-router trusted LAN
  application auth/session identity
  off-site onn PS1-and-below
  WAN telemetry/adaptation
  handheld when available
  Steam/external compute
  adverse-network characterization
        ↓
H User Content + Extended Emulation
  safe USB import
  N64
  GameCube
  PS2
  local + remote regression
  capability tiers
        ↓
I Home Infrastructure / Broader Plugins
  Home Assistant/devices
  cameras/microphones
  storage
  broader clients
  provider expansion
        ↓
J Local Intelligence / Voice / AI
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
  secure remote/portable-client foundation
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

## D-072 execution sequencing clarification

Phase C is **paused at the Windows boundary, not complete**.

After Phase D establishes the Linux-native baseline, return to the remaining
Phase C work on Linux before Phase E resource characterization:

- C3 automatic bitrate controller using the actual Linux actuator capability;
- C4 adaptive FEC or explicit evidence-backed deferral;
- C5 1080p60 capability characterization;
- C6 generalized native source abstraction;
- C7 final Phase C acceptance/checkpoint.

Authoritative execution order:

`D Linux baseline -> resume remaining C on Linux -> E Linux characterization -> F media/VOD/Live TV -> G remote`

The Windows 5500/6000/7000 ladder and restart-actuator evidence are retained as
development evidence, not universal Linux constants.
