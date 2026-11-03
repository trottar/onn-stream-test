---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# Secure Remote Access / Portable Client Architecture

> **Status (2026-11-03):** the G track is under way and the remote foundation is built and adopted on the host (below).
> The topology, overlay-provider and identity principles in this file are current; the 2026-09-14 "planned" framing,
> the PCM planning envelope and the UDP gate are superseded. Current source: `docs/REMOTE_TRUST.md` (§4-§15, each
> adoption and its off switch), `docs/memory/CURRENT.md`, `docs/ROADMAP.md` Phase G.

**Roadmap status:** ~~PLANNED — Phase G after Linux migration/optimization.~~ **G track under way (Phase E active);
the host side of the remote foundation is adopted.** The text after "What is still pending" is the accepted
architecture as written 2026-09-14.

## What is implemented and adopted (2026-11-03)

Each item is one adopted line (`tools/e1_suite.py` `ADOPTED`), a drop-in under the companion unit; deleting the
drop-in, `daemon-reload` and a companion restart turns it off (`docs/REMOTE_TRUST.md`).

- **The overlay provider** `tailscale` (line 6) and **session identity v2** (line 7): G-A1, 2026-10-16
  (`../evidence/G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`). Pairing once on the home LAN, a signed
  nonce-bound setup and token, declared endpoints matched to the routing class, the permission set and the media
  token (G3-S1..S3); the client's `identity_v2` is on (CL-B3). Unpaired legacy clients only from the hub's LAN.
- **Opus audio** (line 8, G-A2, 2026-10-19): 128 kbit/s, 10-ms frames, declared in the signed setup; a client that did
  not declare it is refused at stream start.
- **The client's link report** (line 9, G-A3, 2026-10-23): Wi-Fi link fields in each heartbeat, diagnostics only.
- **The link-recovery stack** (line 10, G-A4, 2026-10-24): input hold, state save and resume on a real stall.
- **The fast restart** (line 11, G-A5, 2026-10-26) and **its unlock** (line 12, G-A7, 2026-10-27).
- **The WAN lines on a remote-class session** (line 13, G-A9, 2026-10-29, `../evidence/TRIP_PREP_2026-10-29.md`):
  the remote ladder, the 4000 floor start, the 7000 cap and the WAN telemetry, only on an overlay-address session;
  the LAN as before.
- **The step in place** (line 14, G-A10, 2026-11-02, `../evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`): each
  ladder step spliced onto the same stream at one IDR, no SSRC change, with a 2-s fallback to the restart.
- **Off-site play on the onn:** G4-S1 (2026-10-16, the first sessions over the overlay; a phone hotspot stood in
  for the travel router), G4-S2..S4 (2026-10-17 to 10-24) and the trip of 2026-10-30/31 (TRIP-R2: 36 client
  sessions of 9 titles, every one remote-direct on the four WAN lines); closed and read by HOME-1 (2026-11-02).
- **The adverse-network envelope:** G8-S1 measured 18 of 22 cells; the four rate-cap cells never reached PLAYING
  (open, `docs/KNOWN_ISSUES.md`).

## What is still pending (per `docs/ROADMAP.md` Phase G)

- **G2, the travel-router trusted-LAN baseline:** no travel router is recorded as selected or validated.
- **G6, the portable handheld:** pending representative hardware; its absence does not block the onn-based
  foundation (ROADMAP §G6), and G9 accepts it "explicitly pending".
- **G7, Steam / existing-PC external compute:** deferred; no G7 step is recorded. G9 accepts it "integrated or
  explicitly deferred with a preserved provider contract".
- **G9, the remote-foundation checkpoint:** not recorded as reached.
- The open items and the live queue: `docs/memory/CURRENT.md`, `docs/KNOWN_ISSUES.md`.

## Home trust topology

```text
Internet / ordinary household upstream
              |
          home Opal
   PrivyHub trust/network domain
      |                   |
Linux hub             local PrivyHub clients/devices
```

The ordinary household router/Wi-Fi is upstream only.

## Portable topology

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
Linux hub behind home Opal
```

The travel router absorbs visited-network changes. Portable clients remain on
the portable trusted LAN.

No permanent travel-router model is selected yet.

## Overlay provider contract

First prototype candidate: Tailscale.

Tailscale is not the permanent product contract. The overlay layer must remain
replaceable by direct WireGuard, a self-hosted/local-first coordinator, or
another provider satisfying the same security/session needs.

The future Linux hub can terminate the home-side overlay. The home Opal need not
be replaced solely to support the first overlay prototype.

## Identity and authorization

Do not equate network source address with client identity.

Phase G must model independently:

- client identity;
- session identity;
- reachable video/audio/controller endpoints;
- overlay/path state;
- permissions/authorization.

A secure overlay provides transport protection. PrivyHub application
authentication/authorization remains separately required and must fail closed.

Remote access must not flatten the ordinary household LAN.

## Phase C dependency

Phase C is a prerequisite for Phase G.

Build Phase C profiles, telemetry, adaptation, FEC classification and
source/profile/transport/decoder boundaries so they can be reused on WAN paths.

Do not implement WAN plumbing in Phase C.

Remote adaptation principle:

**degrade quality before allowing queue/buffer growth to create runaway
latency.**

Distinguish random packet loss from capacity pressure before changing FEC.

## Reference-session planning envelope

**Superseded in part (G-A2, 2026-10-19):** audio is now Opus, ~326 kbit/s on the wire instead of PCM 2/4's
~3,213 (`docs/REMOTE_TRUST.md` §9). The 2026-09-14 estimate follows as written.

Current reference stream components include approximately:

- 7 Mbps H.264 video target;
- 8+1 video XOR parity;
- about 1.536 Mbps PCM16 stereo audio before packet/tunnel overhead;
- control and overlay/packet overhead.

Use roughly 10-11 Mbps outbound per reference session as a planning estimate for
future WAN testing. It is not a fixed Internet requirement and does not justify
changing the stable PCM audio path now.

## Linux/network evidence gate

**Closed 2026-09-24 (D6-R1):** the suite did not reproduce the old signature on the Linux + home Opal + onn path
(`../investigations/DEFERRED.md`). The gate as written:

Before Phase G WAN characterization, replay the deferred UDP suite on the
representative Linux + home Opal + onn path.

Do not encode the old Windows/test-network anomaly into WAN buffering unless
representative evidence reproduces it.

## Phase G scope summary

Phase G should establish:

- corrected topology/threat model;
- overlay provider abstraction;
- travel-router trusted-LAN baseline;
- WAN-aware session identity;
- application auth/authorization;
- real off-site onn PS1-and-below validation;
- Phase-C telemetry/adaptation under WAN conditions;
- handheld validation when representative hardware exists;
- Steam/external-compute provider integration or explicit deferral;
- adverse-network characterization;
- clean remote-foundation checkpoint.

Heavier N64/GameCube/PS2 work follows in Phase H and should regress over the
already-established remote contract rather than redesign it.
