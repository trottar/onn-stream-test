# PrivyHub / Safe IoT Roadmap — Linux-First + Remote-Foundation Revision

**Revision date:** 2026-09-14 (position marker updated 2026-09-22, 2026-10-05)
**Predecessor synchronized checkpoint:** C1.1 + native-status privacy checkpoint `0c31c100ec721d687aff6aedbd79bc0cf9343810`
**Roadmap status:** Accepted project plan, **still authoritative and unchanged in structure**. Future secure remote access remains promoted to Phase G after Linux optimization.

---

## 0. Where the work actually is — 2026-09-22 (marker moved 2026-10-05)

**The roadmap below is not restructured; only this marker moves.**
Authority for the current position is `docs/memory/CURRENT.md`.

- **2026-10-05: Phase C CLOSED** (C5-CLOSE, the user's decisions: the
  1080p rung and the `remaster` preset not adopted, the 4x PS1 source
  stays). **Phase E ACTIVE since 2026-10-05: E1 FROZEN (E1-S1, the suite in
  `docs/memory/architecture/E1_WORKLOAD_SUITE.md`; the VOD row added
  2026-10-05); **E2 MEASURED 2026-10-06 (E2-S1)**; E3 next — the user picks
  the first optimization from E2's ordered list.**

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
  next); C4 closed (8+1 stays); D7 complete on the adopted build; C5: 1080p60 NOT CAPABLE (stream) at parity, capability-gated; C5-M2's follow-up arms INCONCLUSIVE (link); C5-M3's low rungs screened (720p/4000 passes transport). **2026-10-01: C5 reopened by the user's reading (1080p60 through the ladder); C5-M4 Part 1 measured the PS1 source at native 1080p (4x holds 60); C5-M4A adopted the 4x PS1 source (1920×1080 window) through today's 720p/7000 stream. 2026-10-03: C5-M5 built the 1080p rung on the live ladder behind its flag (off by default, not adopted); the night WORKS AS A RUNG. 2026-10-03/04: C5-M5B set the rung's entry to 415 of 450 from the recorded data (no loss leave met its conditions) and put the PS1 look behind `PRIVYHUB_PS1_LOOK` (`remaster` holds 60 at 720p); not adopted.**
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
| **C — Adaptive Streaming Architecture** | Portable profile/telemetry/readiness foundation complete enough for Windows; automatic adaptation continues on Linux | **CLOSED 2026-10-05** (C5-CLOSE; resumed 2026-09-23 at C3 after `D-BASE`) |
| **D — Linux Migration / Native Linux Baseline** | Move the core server to the HP EliteDesk Linux prototype and restore normal-use parity | **ACTIVE** |
| **E — Linux Core Resource Characterization & Optimization** | Optimize and measure the Linux core with PS1-and-below only; select Prototype 2 from evidence | **ACTIVE** — E1 FROZEN (E1-S1, VOD added); E2 MEASURED 2026-10-06 (E2-S1); E3 next (the user's pick) |
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

**Status: CLOSED 2026-10-05** (C5-CLOSE, the user's decisions). Phase C
delivered explicit stream profiles, the C2 telemetry contract, live
adaptive bitrate on by default (validated under real loss), the FEC
decision (8+1, adaptive deferred), 1080p60 characterized and built as a
ladder rung behind its flag (not adopted), the 4x PS1 source, and the
generalized source contract — the reusable base for Phase G.
`docs/memory/evidence/C5_CLOSE_2026-10-05.md`. Earlier: RESUMED
2026-09-23 on Linux at C3 after `D-BASE` (baseline met).

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

**Current status — C5 CLOSED 2026-10-05 (C5-CLOSE), on the user's look
and decisions ("Yep agreed").** The user's words: Look 1 (the adopted 4x
source, 720p) and Look 3 (the same at the 1080p rung) *"looked the best,
little difference between them"*; Look 2 (`remaster`) *"was the worst, a
bit less smooth"*.

- **The 1080p rung: NOT ADOPTED.** Built and validated mechanically
  (C5-M5/M5B), it buys nothing visible on PS1 at the TV while costing
  ~1.8× the wire rate, the switch gaps (287-649 ms) and the onn's 1080p
  decode jitter (~300 spikes ≥ 20 ms/min). It stays behind
  `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, off, for a 1080p-detail source
  (PS2-class, Phase H). Since C5-CLOSE its window skips reports while
  recovery is not PLAYING (S2b).
- **The `remaster` preset: NOT ADOPTED** (stays behind
  `PRIVYHUB_PS1_LOOK`). **The 4x PS1 source stays adopted** (C5-M4A).
- **Look 3, from the logs:** the first try was not at 1080p (its injected
  entry came 6.6 s in, and the 60-s session-age guard refused it).
  **The user repeated it the same night (C5-CLOSE-A): the entry acted
  132 s after PLAYING, and the stream ran ~1.5 min at 1920×1080 / 12600**
  (entry gap 329 ms). The user's words: *"Looked the same and loading the
  game still says 720"*. So the user has looked at the rung's picture and
  saw no difference from the 4x 720p stream, and the decision's grounds
  include the look. The on-screen 720 is the client's constant
  (`NativeStreamActivity.kt:66-67`), not the live size.
- What would reopen it: a 1080p-detail source or a different client.
- `docs/memory/evidence/C5_CLOSE_2026-10-05.md`;
  `docs/memory/decisions/C5_1080P60_CAPABILITY_2026-09-28.md` (the close).

**Earlier status — the user's reading of 2026-10-01: C5 was reopened.
1080p60 is a Phase C deliverable, delivered through the adaptive ladder
as a rung above 7000, not only a characterization.** C5-M1 and C5-M2
characterized the stream on a source with 720p detail (the 879×720
window, upscaled 1.5×) and on an unsettled link. C5-M4 is the
source-side step, with the PS1 source rendering natively at 1080p. The
rung itself, Part 2, is C5-M5 (built behind its flag, below). PS1 comes first, because it maps onto
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

**C5-M4A (2026-10-01): the quick win ADOPTED.** The PS1 source now
renders at 4x into a 1920×1080 window: a Beetle PSX HW core override,
plus internal resolution 4x in the base and the six per-title `.opt`.
This was the user's authorization ("Yes apply the 4x config"), adopted by
the pre-registered rows.

- The adopted 720p/7000 stream carries the 4x source.
- A 20-min hold met every row: RetroArch 59.999, client 59.94 fps, 27
  spikes/min, 0 transitions.
- The D7 regression passed 9/9 on the retry.
- The 2D cores are untouched.
- **Next: the rung (Part 2)**, after the 40 MHz change and the LINK-L1
  re-run.
- `docs/memory/decisions/C5-M4_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`.

**C5-M5 (2026-10-02/03): the 1080p rung — BUILT, SHOWN, behind its flag,
NOT adopted.** It sits on the live ladder behind
`PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, off by default.

- **The level**: 12,600 kbps at 1920×1080, the c3 arm's argv.
- **Entry**: from 7000, after ≥ 435 clean of the last 450 reports.
- **Leave**: the existing triggers; the mild bar goes to 7000 / 720p.
- **Holds**: a 10-min re-entry hold; leave-entry-leave → HOLD.
- **What it showed:**
  - **The mid-session size change needs no client change** (R0a). R0b is
    not met as pre-registered on two clauses (record).
  - Tests 119/119, mutations 10/10. With the flag absent, the decisions
    are identical to the closed controller's (377 series).
  - The injection session passed.
  - The 2-h night (01:06) **WORKS AS A RUNG**, with one entry at 111.5
    min and 8.5 min at 1080p.
  - The 30-min daytime hold did not reach the entry (431 of 450).
- **What the replays say:** on this link the entry is rarely reached, and
  the mild bar does not catch the 1080p's bursty loss.
- **Next**: the user's picture look at 1080p (the gate), then the user's
  call on adopting the flag, and the rung's `nft` capacity night.
- `docs/memory/evidence/C5_M5_1080P_RUNG_2026-10-03.md`.

**C5-M5B (2026-10-03/04): the rung's rules from the data, and the PS1
look — behind flags, NOT adopted.** The selection criteria were
pre-registered before the replays.

- **Entry: ≥ 415 of 450** (E415), the strictest candidate that enters
  within 20 min on ≥ 7 of 10 real-input holds. It entered on 8.
- **Leave: unchanged.** No loss-based candidate met the conditions: the
  1080p loss here comes as rare, large bursts.
- Tests 120/120, mutations 14/14, stop rule 0 differences (386 series).
- S1b injection PASSES. S2b daytime is NOT RUNG SHOWN: recovery paused the
  game, then the guards refused the entry.
- S3b night: **DOES NOT WORK AS A RUNG by its rows.** One entry by its own rule at 15.1 min (434 of 450, one short of the old 435), then 104.9 min at 1080p with no leave, no oscillation and 0 recovery (fps 60.18, stale 0.70/min, loss 2.82/min). The miss is the session's spikes: 317.9/min against < 200, the 1080p decode's known rate on the onn (C5-M4's 1080p holds 328-607/min). The entry switch's gap was 649 ms.
- **The look**: `PRIVYHUB_PS1_LOOK=remaster` (4x + bilinear + dither off +
  PGXP) holds 60 at 720p, at +3.8 GPU points.
  - xBR and JINC2 miss 60, and MSAA is not offered (Vulkan-only).
  - At the rung the full preset drops one frame in 4.8 min, so
    `remaster-1080p` is not offered.
  - `tools/ps1_look.sh` is the user's one command per look.
- **Then**: the user's look on the TV and the user's calls — made
  2026-10-05 (C5-CLOSE, above).
- `docs/memory/evidence/C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md`.

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

**C7 status, 2026-09-25 (`C6-D1`), re-read 2026-10-05 after C5's close** — each acceptance item and the record it rests on:

| item | status | record |
| --- | --- | --- |
| explicit profiles | ✓ | C1 (`native_stream_profiles.py`; cap, cushion, redundancy adopted) |
| transport telemetry contract | ✓ | C2 (`privyhub_stream_telemetry_v1`, heartbeat v3, decoder report v2) |
| adaptive bitrate runtime validated | ✓ **`C3.L4` CLOSED 2026-09-30: live VALIDATED UNDER REAL LOSS on three `nft` nights (1 NOT → capacity + backstop; 2 WORKS UNDER LOSS → `capacity_mild`; 3 WORKS UNDER LOSS, the pre-registered HOLD shape); live behind its flag; **live ON BY DEFAULT since 2026-10-01 (`C3-L4-D1`, the unit drop-in; the user's authorization 2026-09-30).** History: shadow built and SILENT; live AUTHORIZED 2026-09-28 (single transition per event); **live BUILT (`C3-L4-L1`): SILENT on a clean link, decrease proven on injection; the increase rule replaced by the user's blend (`C3-L4-L2`: climb 5000→7000 shown on injection); `nft` night 1 (2026-09-29): no decrease under a cap → the user's capacity trigger + recovery-escalation backstop built (`C3-L4-N1`: replays PASS, 30-min live hold SILENT); `nft` night 2 WORKS UNDER LOSS (2026-09-29) → the user's `capacity_mild` built (`C3-L4-N2`: stop rule PASS, 30-min hold 0 transitions); night 3 WORKS UNDER LOSS (2026-09-30)** | `C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`; `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`; `C3_L4_NFT_NIGHT3_2026-09-30.md`; the decision's close; `C3-L4-S1`; `C3.L3a` sessions 1-4; `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`; `C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`; `C3_L4_NFT_NIGHT1_2026-09-29.md`; `C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`; `C3_L4_NFT_NIGHT2_2026-09-29.md`; `C3_L4_N2_MILD_CAPACITY_2026-09-29.md` |
| adaptive FEC validated or explicitly deferred | ✓ **explicitly deferred** (2026-09-28, the user's call): adaptive not supported; static 8+2 NOT SHOWN; 8+1 stays; arm dormant | `decisions/C4_ADAPTIVE_FEC_2026-09-24.md`, `C4_M1_FEC_ARM_2026-09-25.md` |
| 1080p60 characterized → **delivered through the ladder** (the user's reading, 2026-10-01) | ✓ **C5 CLOSED 2026-10-05 (C5-CLOSE, the user's decisions)**: 1080p60 characterized (C5-M1 NOT CAPABLE at parity; C5-M2 INCONCLUSIVE (link) twice) and **built as a ladder rung behind `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`** (C5-M5/M5B: no client change for the size switch, entry 415 of 450, 105 min at 1080p overnight; the window skips non-PLAYING reports since C5-CLOSE) — **NOT ADOPTED** on the user's look (no visible gain on PS1; cost: ~1.8× wire rate, 287-649 ms switches, the onn's 1080p decode jitter); the `remaster` preset NOT ADOPTED; **the 4x PS1 source ADOPTED** (C5-M4A). Low rungs screened for Phase G (C5-M3: 720p/4000 passes transport). Look 3's first try was at 720p (the entry refused by the 60-s age guard); **the repeated Look 3 was at 1080p (~1.5 min, C5-CLOSE-A) and "looked the same"**: the decision's grounds include the look | `C5_CLOSE_2026-10-05.md`; `decisions/C5_1080P60_CAPABILITY_2026-09-28.md`; `C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md`; `C5_M5_1080P_RUNG_2026-10-03.md`; `C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md`; `C5_M1_1080P60_PROFILE_2026-09-28.md` |
| generalized source contract established | ✓ on paper and as an unused interface | `architecture/NATIVE_SOURCE_CONTRACT.md` (`C6-D1`) |
| Games regression passes | ✓ all 9 scripted rows PASS (D7-R2); the user's hands-on rows reported fine (2026-09-28) | `D7_R1_LINUX_REGRESSION_2026-09-25.md` §R3 |
| reusable by Phase G remote/WAN | stated in the contract (a remote transport is another `Transport`; nothing implemented) | `architecture/NATIVE_SOURCE_CONTRACT.md` |
| clean checkpoint/push | **pending the user's commit of C5-CLOSE** (Code commits nothing); the checkpoint record (appended 2026-10-05) and the git status file are ready | `C7_D8_CHECKPOINT_2026-09-30.md`; `logs/c5_close_git_status.txt` |

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

**Status: ACTIVE (started 2026-10-05, the user's "let's start E1") — E1
FROZEN (E1-S1; VOD added 2026-10-05); E2 MEASURED (E2-S1, 2026-10-06); E3
CLOSED (2026-10-09, E3-A3); E4 ACTIVE — reference re-measured (E4-S1), the
CPU-time floor (E4-S2) and the memory floor (E4-S3, swap off) measured; grab
deferral (E4-S4) and the SNES capture fix (E4-S5) built behind flags, both
REJECTED by their bars on a lossy link; the memory floor closed at 1.5G swap
off (E4-S3B); the fix's bench and deferral's clean-link rerun INCONCLUSIVE
(E4-S5B, E4-S4B, 2026-10-10); the alpha proposal is the user's call.** (Was: NEXT; PLANNED AFTER D.)

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

**Status: FROZEN 2026-10-05 (E1-S1)** — the suite document is
`docs/memory/architecture/E1_WORKLOAD_SUITE.md` (it changes only by a
dated amendment); the record `docs/memory/evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`.
One command (`tools/e1_suite.py`), one sampler set (`tools/e1_sampler.py`).
Runnable rows, each run twice: idle, PS1 local, SNES streamed, PS1 streamed
(= the 720p60 reference), the 1080p rung (flag, not adopted), the EPG grab
(metadata/storage), PS1 streaming + EPG grabs (concurrency). REPEATABLE: 6
of 7; the concurrency row NOT YET (the stream degrades under the grabs).
ABSENT: Live TV (no unattended channel start), browser and camera sources
(Windows-only; no camera), NES and Genesis (no fixtures). **Amended
2026-10-05 (E2-S1 §1):** E1-VOD added (direct play of a fixed file on the
onn; REPEATABLE); the 1080p-rung row kept by the user.

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

**Status: MEASURED 2026-10-06 (E2-S1)** —
`docs/memory/evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md`: every suite row at
20-min windows (SNES and CONC twice), the table with E1's 5-min means beside,
the known-good reference for this host, and the three pre-registered
answers. **CONC**: during EPG grabs the busiest core rises first and most
(no encoder dup/drop, no host tx drops, relay CPU flat) — hypothesis: the
grab start-up burst delays the stream's send threads. **SNES**: neither
emulator nor encoder starves the other at 20 min; bsnes costs 4.4-5.2 cores
and varies (NOT YET REPEATABLE). **Memory**: the first grab adds ~110 MB
anon to the companion, then steps. Ordered E3 candidates in §8 of the record.

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

**E3 status (QUEUE_2026-10-06, the five items in E2's order, each behind
its own flag, nothing adopted):**

| task | change (flag) | verdict | record |
| --- | --- | --- | --- |
| E3-S1 EPG grab vs stream | grabber at SCHED_IDLE / nice 19 / idle I/O (`PRIVYHUB_EPG_GRAB_PRIORITY=idle`) | **INCONCLUSIVE** (control 0.01 fps off-band); loss unmoved | `evidence/E3_S1_EPG_GRAB_PRIORITY_2026-10-06.md` |
| E3-S2 companion memory after a grab | `malloc_trim(0)` after each forced refresh (`PRIVYHUB_EPG_MALLOC_TRIM=1`) | **REJECTED** (PSS 155 MB at the window's end; the parse is live through each grab) | `evidence/E3_S2_COMPANION_GUIDE_RETENTION_2026-10-06.md` |
| E3-S3 grabber cost | node started directly, no `npm run` (`PRIVYHUB_EPG_DIRECT_NODE=1`) | **REJECTED** (3.3 CPU-s per grab vs bar 2.25; the cost is the node grabber's own start-up) | `evidence/E3_S3_GRABBER_COST_2026-10-06.md` |
| E3-S4 SNES core | a lighter core (`PRIVYHUB_SNES_CORE`, prepared, not applied) | **NOT RUN** (no lighter core installed; the fetch was refused by the session's permission policy) | `evidence/E3_S4_SNES_LIGHTER_CORE_2026-10-06.md` |
| E3-S5 streaming's fixed cost | the audio sender's pacer: one timed wait per packet (`PRIVYHUB_AUDIO_SENDER_PACING=frame`) | **REJECTED** (sender 13 → 2.5 % of a core; run 1's loss 106.5/min > 3 × control; run 2 met every clause) | `evidence/E3_S5_AUDIO_SENDER_COST_2026-10-06.md` |

Nothing ACCEPTED; nothing adopted. The queue ran all five, in order, on 2026-10-06.

**Queue B (`QUEUE_2026-10-06B.md`):**

| task | change (flag) | verdict | record |
| --- | --- | --- | --- |
| E3-S5B audio sender, decided | E3-S5's flag, 5 interleaved runs (C F C F F) | **REJECTED** (F2 underruns 18 > 16); loss not burstier (pooled median 10 vs 5, no minute > 100) | `evidence/E3_S5B_AUDIO_SENDER_PACING_DECISIVE_2026-10-06.md` |
| E3-S6 guide-metadata parse | cached slim index (`PRIVYHUB_EPG_GUIDE_INDEX=cached`) | **MEMORY ACCEPTED** (META companion 34 MB vs 161); **STREAM REJECTED** (CONC 773 / 1,273 loss/min; +1 s peak 21-28 vs 56-65) | `evidence/E3_S6_GUIDE_INDEX_2026-10-07.md` |

One item ACCEPTED (E3-S6's memory half); nothing adopted — the user's decision.

**Queue 2026-10-07 (`QUEUE_2026-10-07.md`) — E3's first adoption:**

| task | change (flag) | verdict | record |
| --- | --- | --- | --- |
| E3-S6A guide index adopted | `epg-index.conf`: `PRIVYHUB_EPG_GUIDE_INDEX=cached` (the user: "1. Adopt") | **ADOPTION STANDS** (META 33.6 MB, 257/0 grabs; PS1-STREAM 10.4 % / 59.98 fps; CONC reported 1,312/min) | `evidence/E3_S6A_GUIDE_INDEX_ADOPTION_2026-10-07.md` |
| E3-S5C audio sender, timed wait + final spin | `PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`, 5 interleaved runs | **ACCEPTED** (sender 6 %, companion 17.6 %; underruns 13 / 9 / 5 vs 17 / 14; loss median 4 vs 2.5) — not adopted | `evidence/E3_S5C_AUDIO_SENDER_PACING_SPIN_2026-10-07.md` |
| E3-S4 SNES core, run | Snes9x 1.63 (`PRIVYHUB_SNES_CORE=snes9x`; the core placed by the user) | **ACCEPTED** (RetroArch 8.2 / 9.3 % of a core vs 436 / 517; host 7.4 / 7.9 % vs 43 / 50; REPEATABLE) — not adopted; the look and the licence are the user's | `evidence/E3_S4_SNES_LIGHTER_CORE_2026-10-07.md` (supersedes 2026-10-06's NOT RUN) |

E3-S6A adopted; E3-S5C and E3-S4 ACCEPTED, then decided in E3-A2:

| task | change (flag) | verdict | record |
| --- | --- | --- | --- |
| E3-A2 adopt `frame_spin` and Snes9x | `audio-pacing.conf`, `snes-core.conf` (the user: "Adopt frame_spin if you think helps"; after the look, "Sure it ran smoothly from what I can tell"); verified on PS1-STREAM ×2, SNES-STREAM, META | **Snes9x: ADOPTION STANDS** (RetroArch 8.9 %, host 8.05 %, 60 fps). **`frame_spin`: ADOPTION REVERTED** (valid run 2 underruns 24 > 20 on a noisy link; the replacement 14). One run invalid (recovery pause) and replaced under a hashed addendum | `evidence/E3_A2_FRAME_SPIN_AND_SNES9X_ADOPTION_2026-10-07.md` |

**E3's adoptions after E3-A2: two stood** (the guide index, the Snes9x
core). At E3's close (2026-10-09) three stand, with recovery v2; see
"E3 — CLOSED" below.

**E3's list, by item (E2-S1 §8's order):**

| item | status |
| --- | --- |
| 1. EPG grabs vs the stream (CONC) | the parse's share removed (S6, **adopted** S6A); the child's spawn share: pacing its requests (S7) cut CONC loss ~20× but slowed the guide cycle below the bar — REJECTED; a shorter delay (S7B, 1,500 ms) kept the cycle but not the gain — REJECTED; pacing not adopted |
| 2. the companion's memory after a grab | **solved by the index** (S6/S6A: ~34 MB, not ~160) |
| 3. the grabber's own cost | REJECTED as a launcher change (S3); **the node grabber's start-up remains** (a precompiled grabber, untested) |
| 4. the SNES core | **Snes9x adopted** (S4 ACCEPTED, A2 stands) |
| 5. streaming's fixed cost (the audio sender) | `=frame` REJECTED (S5/S5B); `=frame_spin` ACCEPTED (S5C) then REVERTED (A2, underruns); off |

**Queue 2026-10-08 (`QUEUE_2026-10-08.md`):**

| task | change (flag) | verdict | record |
| --- | --- | --- | --- |
| E3-R1 recovery's false pause | the host's controller-silence trigger at 5 s on two checks (`PRIVYHUB_RECOVERY_TRIGGER=v2`) | **INCONCLUSIVE** (today's rule not faithfully replayable at the records' 1-s resolution; stopped before runs). The probe: the harmful pause is an uplink stall with the client playing, and no exit | `evidence/E3_R1_RECOVERY_FALSE_PAUSE_2026-10-08.md` |
| E3-S7 the grab's spawn share | the grabber paced (`PRIVYHUB_EPG_GRAB_NET=paced`, `--delay=4000`); probe: CPU-off and network-off arms each removed the peak, so network | **REJECTED** (guide cycle 12 refreshes per channel < 20; loss 60-67/min > 3 × control) — but CONC loss 1,312 → ~60/min, 59.8 fps, resyncs 52 → 1-3 | `evidence/E3_S7_CONC_GRAB_SPAWN_2026-10-08.md` |
| E3-R2 the false pause, fixed | v2 threshold + an exit for a `controller_silence` pause (packets back, output fresh) + a silence-gap log (`PRIVYHUB_RECOVERY_TRIGGER=v2`) | **REJECTED** (iii: CONC rendered fps above its cross-night band; v: one gap 41 ms after a log write) — the replay, made faithful, held r1-r4; no recovery pause in 4 runs; a 1,253-ms uplink silence passed. Adoption waits for the user's nft paste | `evidence/E3_R2_RECOVERY_PAUSE_EXIT_2026-10-08.md` |
| E3-S7B the grab paced, shorter | `PRIVYHUB_EPG_GRAB_NET=paced` at `PRIVYHUB_EPG_GRAB_DELAY_MS=1500` (probe: today's request groups go back to back) | **REJECTED** (loss 309 / 346 per min, 59.33 fps, aligned 0-2 s 7.6 / 11.7) — the cycle held (20-21 refreshes, median 10 s), but per-grab cost equals tonight's unpaced grab | `evidence/E3_S7B_GRAB_PACING_SHORT_2026-10-08.md` |

**2026-10-09 (`E3-A3_…`, `E3-A3B_RECOVERY_V2_READOPTION_TASK.md`):**

| task | change | verdict | record |
| --- | --- | --- | --- |
| E3-A3 adopt recovery v2 | `recovery.conf`: `PRIVYHUB_RECOVERY_TRIGGER=v2` (the user: "Adopt", after the nft check passed: real drops unchanged, a 2-s controller drop no pause, an 8-s one resumed via `controller_return` 1.6 s after the clear) | **ADOPTION REVERTED** (ii: no valid run in either row after two replacements — all six windows voided by the client's own output-silence pauses on a poor link; v2 fired no controller pause and no save, and passed 27 silences > 1 s) | `evidence/E3_A3_RECOVERY_V2_ADOPTION_2026-10-09.md` |
| E3-A3B re-adopt recovery v2 | the same `recovery.conf` and state checks (the user: "Code application why not"); the bar judged on controller-trigger events only, client pauses reported | **ADOPTION STANDS** (0 controller pauses, 0 saves; host / companion CPU in band; gap log 0.003 point; two > 1-s silences the old rule would have paused on passed) | `evidence/E3_A3B_RECOVERY_V2_READOPTION_2026-10-09.md` |

### E3 — CLOSED (2026-10-09)

Every E3 item and its final verdict:

| item | verdict | adopted? |
| --- | --- | --- |
| S1 EPG grab priority (idle class) | INCONCLUSIVE | no |
| S2 `malloc_trim` after a grab | REJECTED | no |
| S3 the grabber's node started directly | REJECTED | no |
| S4 the SNES core (Snes9x) | ACCEPTED (S4, 10-07) → **ADOPTED** (A2) | **yes** (`snes-core.conf`) |
| S5 / S5B audio sender `=frame` | REJECTED / REJECTED | no |
| S5C audio sender `=frame_spin` | ACCEPTED → adopted by A2 → **REVERTED** by A2's bar (underruns 24 > 20) | no |
| S6 the cached guide index | MEMORY ACCEPTED → **ADOPTED** (S6A); STREAM REJECTED | **yes** (`epg-index.conf`) |
| S7 / S7B the grab paced (4,000 / 1,500 ms) | REJECTED / REJECTED | no (the user's decision: pacing not adopted) |
| R1 → R2 → A3 → A3B recovery's false pause (v2: gap log, 5-s two-check trigger, controller-return exit) | INCONCLUSIVE → REJECTED (bar defects) → nft check PASSED → adopted, REVERTED (A3's validity clause) → **ADOPTED** (A3B, stands) | **yes** (`recovery.conf`) |

**Three E3 adoptions stand** (the guide index, Snes9x, recovery v2).
**The adopted state at E3's close is four lines**, each through its own
drop-in in `~/.config/systemd/user/privyhub-companion.service.d/`:

- `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` (`adaptive.conf`, from C3-L4);
- `PRIVYHUB_EPG_GUIDE_INDEX=cached` (`epg-index.conf`);
- `PRIVYHUB_SNES_CORE=snes9x` (`snes-core.conf`);
- `PRIVYHUB_RECOVERY_TRIGGER=v2` (`recovery.conf`).

## E4 — Core Linux resource envelope

Produce:

- **Known-good reference:** 4650G/16 GB prototype;
- **Measured floor:** lowest demonstrated capability for defined workloads;
- **Recommended alpha:** floor plus reliability/update/concurrency headroom;
- **Optional higher tier:** stronger profiles without redefining Core.

**Status (2026-10-15, E4-C1): CLOSED on the host side** — the close-out
is `docs/memory/evidence/E4_CLOSEOUT_2026-10-15.md` (the reference, both
floors final, the alpha in two columns with margins, adopted / not adopted,
the link, E7's list). **Open, and not the host's: the link** — 60 stream
runs since 2026-10-09, 0 under D-BASE's loss row (< 10/min; the close-out
held 8.4); the watch (E4-S4D, session A) is the open item. The SNES capture
fix (E4-S5D): in adoption, session A, at the close-out's writing. The alpha
is the user's call (E6).

| item | result (final, E4-C1) | record |
| --- | --- | --- |
| E4-S1 known-good reference | **re-measured on the adopted state** (live, the guide index, Snes9x, recovery v2): idle 1.2 % host CPU / 5.3 W; PS1 streamed 10.9 %, stack 95 % of a core, 354 MB, 20.1 W, 59.53 fps; contended (PS1 + grabs) 21.4 %, stack 172 %, 856 MB, 25.7 W, 58.46 fps; heaviest (1080p rung) 15.3 %, 139 %, 22.0 W. Drift from E2: 14 of 89 metrics, explained by Snes9x (SNES 43-50 → 7.4 % host) and the guide index (META companion 153 → 34 MB). Found: the SNES encoder intermittently outputs 59 fps (a drop per second) | `docs/memory/evidence/E4_S1_REFERENCE_ON_ADOPTED_STATE_2026-10-09.md` |
| CPU-time floor (final) | **CPU-TIME, not slow-core; cgroup, not host.** PS1-STREAM 150 %, SNES-STREAM ≤ 100 %, META ≤ 100 %, CONC 400 % → **the stack 400 % today; 150 % with grab deferral** (CONC + deferral at 150 %: 0 s throttled, host-side gates pass; E4-S4 (d) link-INCONCLUSIVE) | `E4_S2_CPU_MEMORY_FLOOR_2026-10-09.md`, `E4_S4_GRAB_DEFERRAL_2026-10-10.md` |
| memory floor, swap off (final) | PS1-STREAM / SNES-STREAM **≤ 384M** (228 / 197 MB peak), META **1G** (976 MB), CONC **1.5G** (1,166 MB; addendum) → **the stack 1.5G** (between 1G and 1.5G). With swap every row passed at 1G (CONC pinned, 127.5 MB swapped) | `E4_S3_…`, `E4_S3B_MEMORY_FLOOR_1G_SWAPOFF_2026-10-10.md` |
| recommended alpha | **today:** ≥ 6 cores of this speed class (+50 % over 400 %), 1.5 GB stack no swap (+32 % over 1,166 MB; 2 GB to absorb a second activity), 8 GB system, VAAPI H.264 720p60. **With deferral:** ≥ 4 cores (+167 % over 150 %), 1.25 GB stack (~+30 % over 976 MB). **Optional higher tier:** C5's 1080p rung — host 139 % of a core, its floor not measured; limited by the client (onn spike row 317.9/min, switch gaps), not adopted | the user's call (E6); close-out §3 |

**Queue 2026-10-10 (`QUEUE_2026-10-10.md`):**

| task | result | verdict | record |
| --- | --- | --- | --- |
| E4-S3 the memory floor, swap off | `MemoryMax=` 768M / 512M / 384M with `MemorySwapMax=0`: PS1-STREAM and SNES-STREAM **≤ 384M** (228 / 197 MB peak, no pressure); CONC and META **> 768M** (the EPG grabber OOM-killed, the unit restarted); with E4-S2: the stack's memory floor between 768M and 1G, set by the grabber | MEASURED | `docs/memory/evidence/E4_S3_MEMORY_FLOOR_CLOSE_2026-10-10.md` |
| E4-S4 grab deferral while streaming (`PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`) | the deferral works: 0 grabs and 0 grabber processes in every flagged window, drains 6/6 in 33-36 s, the guide serves; CONC + flag at 150 %: every host-side gate passes, **0 s throttled** (E4-S2's CONC: 21 s throttled at 400 %). Stream quality on a lossy link: loss 530 / 364 per min vs the control's 148 | **REJECTED** (a: loss / rendered / resyncs; d: link-INCONCLUSIVE) — not adopted | `docs/memory/evidence/E4_S4_GRAB_DEFERRAL_2026-10-10.md` |
| E4-S5 the SNES 59-fps capture fault | **cause LOCATED**: the encoder adopts x11grab's probed input rate (`tbr`); the SNES window sometimes probes 59 / 59.94. Fix `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` (output `-r 60`): capture 59.97 / 59.99, 0.05-0.1 dup+drop, but no bad probe occurred under it | **REJECTED** (rendered fps on the link) — not adopted | `docs/memory/evidence/E4_S5_SNES_CAPTURE_59FPS_2026-10-10.md` |

**Queue 2026-10-10B (`QUEUE_2026-10-10B.md`):**

| task | result | verdict | record |
| --- | --- | --- | --- |
| E4-S3B the memory floor at 1G, swap off | META **1G PASS** (976 MB peak, 0 events); CONC at 1G **OOM-killed before the window in both runs** (judged INCONCLUSIVE ×2: the kill gates are window-scoped); on a hashed addendum CONC **1536M PASS** (1,166 MB peak, 0 events). **The closed four-row floor, swap off: streams ≤ 384M, META 1G, CONC 1.5G → the stack 1.5G** (CONC's on the addendum). The runner's refresh loop backs off on a refused call (tool patch) | MEASURED (floor closed) | `docs/memory/evidence/E4_S3B_MEMORY_FLOOR_1G_SWAPOFF_2026-10-10.md` |
| E4-S5B the SNES capture fix on bad probes (a bench of 48 × 60-s encoder sessions) | with the flag, 4 / 4 bad probes (59, 59.94 ×3) output 60; the no-flag arm's one bad probe (59.94) output 59.94 but **0 drops**: the bench's `-f null` sink passes frames through, hiding drops in both arms (synthetic check: constant-rate mode drops 58/min at 59, 0 with `-r 60`); the fault live in the companion's own stream that night (59.944 fps); PS1 with the flag unchanged | **INCONCLUSIVE** (the mechanism did not reproduce in arm A) — not adopted | `docs/memory/evidence/E4_S5B_SNES_CAPTURE_PROBE_BENCH_2026-10-10.md` |
| E4-S4B grab deferral on a clean link | the clean-link gate (loss < 10) failed all four controls (426 / 66 / 652 / 109 per min, host-side clean); no flagged run | **INCONCLUSIVE (link)** — E4-S4's REJECTED stands; not adopted | `docs/memory/evidence/E4_S4B_GRAB_DEFERRAL_CLEAN_LINK_2026-10-10.md` |

**Queue 2026-10-10C, and 2026-10-15:**

| task | result | verdict | record |
| --- | --- | --- | --- |
| E4-S5C the capture bench, the companion's sink mode (cfr) | bad probes drop 58 (at 59) / 2-3 (at 59.94) without the flag, 0 with `-r 60`; good probes 0 in both arms. The session then stalled five days; the record written 10-15 | **INCONCLUSIVE** (the 59.94 drop count outside its pre-registered window) — not adopted | `docs/memory/evidence/E4_S5C_SNES_CAPTURE_PROBE_BENCH_CFR_2026-10-10.md` |
| E4-S4C the link watch | never started (the stall) | — | superseded by E4-S4D |
| E4-S5D adopt the SNES capture fix (`snes-capture.conf`; the user, 10-15) | session A | in adoption at E4-C1's writing | session A's record |
| E4-S4D the link watch, detached (`systemd-run --user`, to 2026-10-20T04:00Z) | session A | the open item | session A's record |
| **E4-C1 the close-out** | the reference, both floors final, the alpha in two columns, adopted / not, the link (60 runs since 10-09, 0 under 10/min), E7's list | **E4 CLOSED (host side)** | `docs/memory/evidence/E4_CLOSEOUT_2026-10-15.md` |

## E5 — Capability detection and graceful scaling

**Status (2026-10-15, E5-S1): model DRAFTED, probe v1 runs on the
reference; E5-S2: run on a second machine (the user's choice) and on the
alpha candidate.** The model is `docs/CAPABILITY_MODEL.md` (thresholds from
E4's numbers; "not measured; E5-S2" where none); the probe
`tools/capability_probe.py`; the run
`docs/memory/evidence/E5_S1_CAPABILITY_PROBE_2026-10-15.md` — the reference
`known-good` on all seven classes (storage, decode, NES, Genesis `unknown`).

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

Acceptance (marked 2026-10-15, E4-C1 §6):

- repeatable workload suite — **met, in part** (E1: 6 of 7 rows; SNES on Snes9x; CONC NOT YET);
- PS1-and-below scope preserved — **met** (NES and Genesis rows ABSENT, no fixtures);
- worthwhile bottlenecks optimized — **met** (E3's three adoptions; the SNES capture fix in adoption; grab-vs-stream open: deferral not adopted);
- resource/power envelope documented — **met for this host** (E4-C1; socket watts, wall power ABSENT);
- capability model established — **not met** (DRAFTED, E5-S1; E5-S2 next);
- Prototype 2 class selected from evidence — **not met** (E6, the user's call);
- clean checkpoint/push — **not met** (the tree carries E4-S1..S5C and later uncommitted; the user's commit).

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

**Status (2026-10-15, G1-S1): WRITTEN** — `docs/REMOTE_TRUST.md` (the two
topologies, the threat model, the fail-closed rules; ROADMAP quoted or marked
"G1-S1 proposal"); the source-address audit
`docs/memory/evidence/g1_s1_2026-10-15/source_address_audit.md` (80 lines,
every one categorized for G3). Record:
`docs/memory/evidence/G1_S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_2026-10-15.md`.

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

**Status (2026-10-15, G1-S1): BUILT behind `PRIVYHUB_OVERLAY_PROVIDER=none|tailscale`
(absent = today, byte for byte), NOT ADOPTED** — `companion/overlay/`
(contract, `none`, read-only `tailscale`), 17 tests OK; Tailscale not
installed on the hub (the user's install); the live smoke pending on the
stream (session A).

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

**Status (2026-10-15, G3-S1): HOST SIDE BUILT behind `PRIVYHUB_SESSION_IDENTITY=v2`
(absent = today, byte for byte), NOT ADOPTED** — `companion/session_identity.py`:
LAN pairing window + one-time code, nonce-signed setup, expiring tokens,
declared endpoints (not the source), per-device permissions failing closed,
`logs/session_audit.jsonl` with no addresses; today's client accepted only as
audited `legacy-lan` on the hub's LAN, never over the overlay. 38 tests OK;
the request handler replayed in process byte for byte. Next: G3-S2 (the
client side, an APK change); the live smoke pending on the stream. Record:
`docs/memory/evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md`;
identity model in `docs/REMOTE_TRUST.md` §5.

**G3-S2 (2026-10-16): CLIENT SIDE BUILT behind the client setting `identity_v2`
(default off = today's requests, byte for byte), NOT INSTALLED, NOT ADOPTED**:
device secret in app-private storage, the pairing screen with the hub's code,
nonce-signed setup (HMAC input byte for byte G3-S1's vectors), declared
endpoint, the token on control calls, refresh before expiry, the reason code
shown with one retry. 30 client unit tests OK; the handshake against G3-S1's
host logic 18/18; debug APK `77011eef…` built (release skipped by the user).
Next: CL-B2 (install after the watch; pair by hand; the live G3 smoke on the
LAN). Record: `docs/memory/evidence/G3_S2_SESSION_IDENTITY_CLIENT_SIDE_2026-10-16.md`.

**G3-S3 (2026-10-16): HARDENING AND THE HUB HOST BUILT behind the same flags
(absent / off = today, byte for byte), NOT INSTALLED, NOT ADOPTED.** Host: the
setup signs the audio port and the overlay address (v2 canon; v1 still
accepted), the stream-start ports bound to the signed ones
(`endpoint-port-mismatch`), the media target chosen by the request's routing
class, a per-session media token, the range server gated over the overlay
(the token header or `?media_token=`, checked by the companion on loopback,
audited), `diagnostics` grantable and default on, the status document's
permission set and media-token boolean. Client: "Hub host" (overrides the
companion host while `identity_v2` is on), the overlay interface address
declared, the token on TV-sync, EPG, diagnostics, the player's hub media
requests and artwork, reason codes shown with one retry. 80 host tests (the
handler replay extended: the range server byte for byte), G1 / G5 suites
green, 44 client unit tests, the handshake harness 24/24, debug APK
`59f736d2…` built, not installed. Next: CL-B3 (install, a LAN PS1-STREAM and
a VOD play with the flag and the setting on), then G4-S1 off-site. Record:
`docs/memory/evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`; trust model
`docs/REMOTE_TRUST.md` §8.
**CL-B4 (2026-10-18): `sig_v` 3** in `companion/session_identity.py`: v2's fields plus the client's `audio_codecs`
signed (required under v3; `token_issued` records them); v1 / v2 byte for byte as HEAD's. The APK signs v3 (one v2
fallback for an older host). Live on the companion since 22:00Z. Record:
`docs/memory/evidence/CL_B4_APK_OPUS_DECODE_2026-10-18.md`.

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

**Status (2026-10-16, G4-S1): first off-site session measured: 2 of 3 valid; see the record**
(`docs/memory/evidence/G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md`). Runs 1 and 2 reached PLAYING over the overlay (a
phone hotspot + the Tailscale app on the onn); gates 1-2 met, gate 3 not evaluable (the remote row records no
RetroArch FPS or encoder progress); run 2's hotspot toggle ended the session and the stream came back after a LAN
setup; run 3 not started. Overlay wire rate at 7000: 11.42 Mbit/s.
**Status (2026-10-18, G4-S2): off-site with the remote ladder: 1 of 2 runs, valid.** Run 1 (G5-S3 + G5-S4 cap 4000 +
G8-S2 floor) played over the overlay: start 4000 / `floor` / `path_class` remote, held 4000 (73 up-moves refused by
`remote_cap`, no transition), 7.75 loss/min, 59.92 fps; capture 60.004, dup+drop 0.0, the RetroArch counter not on
the title (gate 3 not evaluable). **Wire rate at 4000: 8.29 Mbit/s (~62 MB/min), not ~4.65** — the excess over the
encoder ~4.3 Mbit/s, as at 7000. Run 2 not run (the user's phone data). Record:
`docs/memory/evidence/G4_S2_OFFSITE_REMOTE_LADDER_2026-10-17.md`.
**G4-W1 (2026-10-18): wire overhead accounted: audio (PCM 2/4) is the largest term** — 3,213 kbit/s at every rung
(400 × 1,004 B), then FEC parity 889 / 1,229 (4000 / 7000), headers 179 / 292, control ~10; no fragmentation; the
overlay's ~69-74 B per packet is on the underlay, not the tailnet counter. The terms close to −0.1 % at 7000. G4-S1's
11.42 is KiB-based (11.70 decimal), so the excess is 4.27 / 4.69, not constant. Proposed: cut audio first (G4-W2).
Record: `docs/memory/evidence/G4_W1_WIRE_OVERHEAD_2026-10-18.md`.
**G4-W2 (2026-10-18): Opus audio path built behind a flag, host side; the APK decode and live test pending.**
`PRIVYHUB_AUDIO_CODEC=opus[,bitrate=<kbps>][,frame=<ms>]` (`companion/audio_codec.py`; absent = today, datagram for
datagram): 128 kbit/s CBR, 10-ms frames, PHA1 v2, today's duplication ~20 ms apart → 200 datagrams/s, 326.4 kbit/s
against PCM 2/4's 3,212.8 (−1.30 GB/h at any rung), +7.5 ms; same audio-ms lost under loss-1/loss-5 within noise, half
the holes. The client declares `audio_codecs` in `/session/setup`; an undeclared client is refused at stream start
(fails closed). Not adopted. Next: the APK's Opus decode (CL-B), a LAN smoke, an off-site run at 4000. Record:
`docs/memory/evidence/G4_W2_OPUS_AUDIO_PATH_2026-10-18.md`.
**CL-B4 (2026-10-18): the APK decodes Opus; the first live Opus session (LAN, 10 min) VALID, host gates held.** APK
`8e10497e…` CONFIRMED (sig_v 3 declares `audio_codecs`; MediaCodec `audio/opus`, in-order release that waits for the
copy). With `PRIVYHUB_AUDIO_CODEC=opus`: 200 datagrams/s, ~326 kbit/s; the LAN interface −2,952 kbit/s against
CL-B3 R1 at 7000 (−2,909 predicted); 0 audio frames lost net (68 recovered). **Underruns 40 against 9**: the decode is
synchronous on the receive thread (avg 3.3 ms, max 84 ms); decoder spikes 178/min against 87 (not located). Off-site
blocker: `audio_codec.py` records the overlay host only for sig_v 2. Flag removed; not adopted. Record:
`docs/memory/evidence/CL_B4_APK_OPUS_DECODE_2026-10-18.md`.

**G4-P2 (2026-10-17): the remote row records gate 3 from G4-S2** — `tools/e1_remote.py`
writes the home row's per-run RetroArch counter override (for the PS1-STREAM fixture),
starts the sampler with `--e2` and keeps `encoder.jsonl`, and reports `retroarch_fps`,
`capture_fps`, `dupdrop_per_min` as the gates' clauses read them (20 tests OK; the home
row byte for byte, by file and masked AST hash). G4-S1's gate 3 stays NOT EVALUABLE from
its files. Record: `docs/memory/evidence/G4_P2_REMOTE_ROW_GATE3_2026-10-17.md`.

**Status (2026-10-16, G4-P1): PREPARED, nothing run off-site** — `tools/e1_suite.py run --remote`
(a PS1-STREAM row over the overlay: both host flags read back, the user's launch, the
endpoint class + hash only, the path every 10 s, adb optional; 13 tests OK); the G4-S1
pre-registration drafted (`handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md`: a phone
hotspot + the Tailscale app on the onn substituting for §G2's router; three gates, the rest
reported); the user's runbook `handoffs/G4_RUNBOOK_HOTSPOT.md`. **Blockers:** CL-B2's pairing,
the overlay flag on the companion, the Tailscale app on the onn (unverified). Record:
`docs/memory/evidence/G4_P1_OFFSITE_TEST_PREP_2026-10-16.md`.

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

**Status (2026-10-16, G5-S1): CLASSIFICATION BUILT behind `PRIVYHUB_WAN_TELEMETRY=1`
(absent = today, byte for byte), NOT ADOPTED** — `companion/wan_telemetry.py`: the
eleven measures below from Phase C's existing telemetry + the overlay path, each
with its source field; per-10-s-window and per-session classes (clean / lossy /
capacity-limited / latency-limited / path-changed / starved) on thresholds from
D-BASE and the live ladder; replays of three recorded runs reproduce their loss
(649.94 / 60.93 / 663.98 per min), none clean. The five priorities below written as
rules in `docs/WAN_ADAPTATION_RULES.md` (G5-S2 implements them). Live smoke pending
on the stream. Record: `docs/memory/evidence/G5_S1_WAN_TELEMETRY_CLASSIFICATION_2026-10-16.md`.

**G5-S2 (2026-10-16): THE RULES BUILT behind `PRIVYHUB_WAN_ADAPTATION=1` (absent =
the ladder exactly as adopted), NOT ADOPTED** — `companion/wan_adaptation.py`
gives the live ladder at most one suggestion per report (hold / step down / no step
up / remote floor 720p/4000), applied only as a constraint through the ladder's own
gates; R4 recorded as no FEC change; every suggestion in `decisions.jsonl` with
`source: wan_rules`. The remote floor is recorded, not actuated (the actuator's
validated ladder ends at 5000). Flag absent: the four named runs' recorded
decisions reproduced exactly and the controller's rows identical to HEAD's;
flag present, open loop, tabulated per rule with no claim of improvement. Live
smoke (LAN, 10 min) and the first off-site run with it (G4-S2) pending on the
stream. Record: `docs/memory/evidence/G5_S2_WAN_ADAPTATION_RULES_2026-10-16.md`.

**G5-S3 (2026-10-17): THE REMOTE LADDER BUILT behind `PRIVYHUB_REMOTE_LADDER=1`
(absent = today, byte for byte), NOT ADOPTED, unvalidated live** —
`companion/remote_ladder.py`: the session's routing class (G3's overlay test over
the class-matched target the gate hands the games plugin) reaches the ladder's
context as `path_class`; on a remote path only, the ladder and the actuator's
validated list gain 720p/4000 (`floor_4000` and the one-rung step from 5000 can
land there; nothing below 4000; refused on the LAN); `path_class` on every
ladder row, each 4000 actuation labelled with its rule and result. Flag absent:
actuator 200/200 cases, the games plugin's stream start and G5-S2's replay
identical. Flag present: no replayed run reaches 4000 — G4-S1 run 1's 2,259
loss/min is one report of 21,407 (the resync after its 24.5-s pause), not
sustained loss. Pending on the stream: the LAN smoke, then G4-S2. Record:
`docs/memory/evidence/G5_S3_REMOTE_LADDER_2026-10-17.md`.

**G5-S4 (2026-10-17): THE REMOTE RUNG CAP BUILT behind
`PRIVYHUB_REMOTE_RUNG_CAP=<kbps>` (needs G5-S3's flag; absent = today, byte for
byte), NOT ADOPTED, unvalidated live** — `companion/remote_cap.py`: the user's data
saver. Valid only at a remote rung (4000-7000); on a remote path the ladder's
target is clamped to it (the stream moves to the cap through the ladder's gates,
after the 60-s guard; never above it; the ladder's own steps below it); on the
LAN nothing; every clamp recorded `source: remote_cap`. Replay over G4-S1's runs:
at either cap about 60 s at 7000, then the cap. Arithmetic, not a result: 4000 is
2.3-3.5 GB/h by the basis, against 5.1 at 7000. Pending on the stream: the first
off-site run with the cap at 4000 (the user judges the picture). Record:
`docs/memory/evidence/G5_S4_REMOTE_RUNG_CAP_2026-10-17.md`.

**G5-S3 / G5-S4 LAN smoke (2026-10-17): PASSED on the LAN.** One 10-min PS1-STREAM with
`PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_REMOTE_RUNG_CAP=4000` and `PRIVYHUB_WAN_TELEMETRY=1`: host gates met;
`path_class` `lan` on every ladder row; the cap's configuration row once, no clamp, no 4000; 7000 held with no acted
decision on a lossy link (646.8 loss/min); companion 24.45 % of a core (CL-B3 W 25.44). Flags removed at teardown.
Not adopted; off-site pending (G4-S2). Record: `docs/memory/evidence/G5_S3_LAN_SMOKE_2026-10-17.md`.
**G5-S3 / G5-S4 off-site (2026-10-18, G4-S2 run 1): the remote floor and the cap held on a real remote path**
(start 4000 `floor` `remote`; 73 clamps as `refused`, `source: remote_cap`; no rung above 4000). G5-S2's rules and the
climb from 4000 off-site: not yet run (G4-S2 run 2 stopped for data).

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

**Status (2026-10-16, G8-P1): HARNESS BUILT; ENVELOPE NOT MEASURED.** A
user-space impairment shim (`companion/impairment.py`) on the loopback video
hop, behind `PRIVYHUB_IMPAIRMENT=<profile>[@pre-fec|@post-fec][,seed=N]`
(absent = today: the FEC sender byte for byte, no port, no thread). The
profiles cover random loss, burst loss, delay, jitter, reordering and a rate
cap with a bounded queue, plus combinations. All eleven passed their tolerance
in process. `@post-fec` is the WAN-like placement; pre-FEC loss is never
FEC-recoverable. Video only; no `nft`, no `sudo`. The shim's own cost is 2.1-7.0 %
of a core, **over the ≤ 1-point bar**. Not adopted. Next proposed: G8-S1, the
envelope. Record: `docs/memory/evidence/G8_P1_IMPAIRMENT_SHIM_2026-10-16.md`.

**Status (2026-10-16, G8-S1): envelope: 5/22 cells measured (partial, 2026-10-16); resume pending.** Cells 1-5
(none off/on, loss-1 off/on, loss-5 off), all valid, every host gate met. The rest are not run. The driver was stopped
by its STOP file at 21:25:52Z. Record: `docs/memory/evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-16.md`.

**Status (2026-10-17, G8-S1 final): envelope measured: 18/22 cells valid; the rate-cap profiles did not reach
PLAYING (open); see the record.** Resumed 00:21Z, all 22 cells done 04:30:30Z; every host gate met in every valid cell.
The four cap cells (cap-6000 / cap-4500, off and on) never reached PLAYING: the stream entered the shim at ~8.25
Mbit/s (the 7000 rung with FEC and audio), the cap held its rate, and 27-45 % was tail-dropped. The rules acted once
(delay-150 on, R2.1, 7000→6000). From cell 6 the companion ran session B's flag-absent G5-S3 / G5-S4 edits (disclosed,
bounded by B's in-process proofs). Record: `docs/memory/evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md`
(supersedes the 10-16 partial).

**G8-S2 (2026-10-17): start rung built behind a flag; the cap cells' live re-run pending.**
`PRIVYHUB_START_RUNG=<floor|cap|kbps>` (`companion/start_rung.py`; absent = today, byte for byte) starts a
stream at the active list's floor (5000 LAN, 4000 remote with G5-S3), at G5-S4's cap, or at a named rung; the
ladder's own increase rule climbs. In process through the real FEC sender and the shim: 5000 under cap-6000
still enters at ~6.1 Mbit/s (1.8-2.4 % tail-dropped); **4000 under cap-4500 enters at ~4.65 Mbit/s (5.5-5.8 %
dropped)** — the floor sits above that cap; no claim about PLAYING. Proposed next: G8-S3, the four cap cells
re-run with the flag. Record: `docs/memory/evidence/G8_S2_START_RUNG_2026-10-17.md`.

**Status (2026-10-17, G8-S3): start rung: PLAYING reached under cap-6000 at the 5000 start (G8-S3); the 5000
rung's live wire rate exceeds 6 Mbit/s; cap-4500 needs a rung below 5000, remote-only today.** 3/3 cells valid.
- Cells 1 and 2 (cap-6000, `START_RUNG=floor`, rules off / on): PLAYING in 9.1 s and 7.1 s, host gates met.
  - The ladder held 5000 for the window: `at_floor` down, no clean reports to go up.
  - The shim's input was 6,039 / 6,028 kbit/s mean, and 6.75 % / 9.18 % was tail-dropped.
  - Cell 1 stayed up for the window at 2,379 loss/min and 53.1 fps. Cell 2 went silent on the client 417 s in;
    recovery gave up after 5 restarts.
- Cell 3 (cap-4500 at 5000): `no_play`, 27.76 % dropped, as predicted.
- The mean wire rate matched G8-S2's bench (~6.1 Mbit/s). The drop is about 3× the bench's and is not explained by the
  mean: it comes with the per-second and frame-size spread.
- Record: `docs/memory/evidence/G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md`.

**G8-S4 (2026-10-18): rate headroom built behind a flag; live test pending.** `PRIVYHUB_ENCODER_RC=<tight|headroom>`
(`companion/encoder_rc.py`; absent = today, byte for byte) narrows the encoder's 1-s CBR VBV: `tight` = CBR, maxrate T,
bufsize T×0.25 (250 ms); `headroom` = VBR, maxrate 1.1 T. Follows live rung changes (one `if` in the builder). Offline on
the host's VAAPI (C5-M3's attract reference, less bursty than live): `tight` at 5000 p95 5,605 → 5,298, max 5,976 →
5,535; through cap-6000 in process the tail drop 4.67 % → 3.42 % (per-second p95 17 % → 8 %), not to 0 — the wire mean
sits at the cap; `headroom` worse (8.72 %). Cost: −0.45 dB PSNR avg, −2.4 to −3.4 dB on the worst frame; CPU unchanged.
Not adopted. Proposed: G8-S5, G8-S3's cell 1 with `tight`. Record:
`docs/memory/evidence/G8_S4_ENCODER_RATE_HEADROOM_2026-10-18.md`.

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
