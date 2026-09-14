---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# Secure Remote Access / Portable Client Architecture

**Roadmap status:** PLANNED — Phase G after Linux migration/optimization.

This file defines accepted future architecture. It does not claim that remote
operation is implemented or runtime validated.

## Home trust topology

```text
Internet / ordinary household upstream
              |
          home Opal
   PrivyHub trust/network domain
      |                   |
future Linux hub      local PrivyHub clients/devices
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
future Linux hub behind home Opal
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

Current reference stream components include approximately:

- 7 Mbps H.264 video target;
- 8+1 video XOR parity;
- about 1.536 Mbps PCM16 stereo audio before packet/tunnel overhead;
- control and overlay/packet overhead.

Use roughly 10-11 Mbps outbound per reference session as a planning estimate for
future WAN testing. It is not a fixed Internet requirement and does not justify
changing the stable PCM audio path now.

## Linux/network evidence gate

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
