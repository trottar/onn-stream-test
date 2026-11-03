---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# Network Architecture

> **Status (2026-11-03):** the trust boundary, the local service model and the LAN path are current and unchanged.
> The overlay boundary is now built and adopted (provider `tailscale`, G-A1, 2026-10-16; remote-class sessions,
> G-A9) — see "The overlay boundary (adopted)" below. The UDP gate is closed (D6-R1). Current source:
> `docs/REMOTE_TRUST.md`, `docs/memory/CURRENT.md`.

## Current architectural trust boundary

The ordinary household router/Wi-Fi is upstream Internet infrastructure only.
It is **not** the PrivyHub trust domain.

The home Opal defines the PrivyHub network/trust domain. Current and future
PrivyHub server/client/device infrastructure belongs behind that boundary,
including:

- the Linux hub;
- home onn clients;
- game/provider hosts when integrated as PrivyHub providers;
- cameras/microphones;
- Home Assistant/device infrastructure;
- storage and other PrivyHub/IoT components.

Older Prototype-1 evidence that describes the Windows companion on an ordinary
household-LAN side and the onn on a routed secondary side is historical test
topology, not the current product architecture. Preserve that evidence as
historical evidence; do not let it redefine the current trust model.

## Local service model

Current logical service separation remains:

- control API: TCP 8765;
- media serving: TCP 8000;
- native game video: UDP 48100;
- native game audio: UDP 48101;
- native controller input: UDP 48102.

The current local prototype may derive reachable media/audio/controller targets
from the source of a control request. That is a routing convenience only, not a
durable client-identity contract.

## Remote topology (Phase G)

Phase G establishes a portable trusted-LAN model (as designed 2026-09-14; the travel-router part is not yet
recorded as validated):

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
Linux hub behind the home Opal
```

The travel router owns visited-network uplink changes. Portable clients remain
configured to the travel router's trusted LAN.

The home Linux hub can terminate the home-side overlay. Replacing the home Opal
is not required merely to add a first Tailscale prototype.

Tailscale is the preferred first overlay candidate, not a permanent
architecture dependency. The provider boundary must permit alternatives such as
direct WireGuard or a future self-hosted/local-first coordination layer.

A secure overlay protects transport. It does **not** replace PrivyHub
application authentication/authorization.

Phase G separates (built: `docs/REMOTE_TRUST.md` §5):

- client identity;
- session identity;
- reachable media/audio/controller endpoints;
- overlay/path state;
- application authorization.

Source/request IP is not durable client identity.

Remote access must not flatten or expose the ordinary household LAN.

## The overlay boundary (adopted)

- **Provider:** `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`overlay.conf`, adopted line 6, G-A1, 2026-10-16). The
  contract is `companion/overlay/provider.py`; providers `none` (the default) and `tailscale`, which only reads the
  installed binary's status / netcheck and never installs it or brings it up. The path is reported as `direct` /
  `relayed` / `no-peer`. The overlay endpoint is opaque: status shows `present` / `absent` and a short hash only.
- **Routing classes, not identity:** each request source is classed `local`, `lan`, `overlay` or `unknown`; only
  the class is logged. Client and session identity come from pairing and signed setup (`PRIVYHUB_SESSION_IDENTITY=v2`,
  line 7, G-A1), and the hub streams to the declared endpoint whose class matches the request's (the overlay address
  off-site, the LAN address at home). An unpaired legacy client is accepted only from the hub's LAN, never over the
  overlay. Do not put a reverse proxy or `tailscale serve` in front of the companion.
- **Remote-class sessions:** with `PRIVYHUB_REMOTE=1` (line 13, G-A9, 2026-10-29) a stream start from an overlay
  address (path direct / relayed / unknown) gets the remote ladder, the 4000 floor start, the 7000 cap and the WAN
  telemetry.
- **The LAN is unchanged:** on a LAN session none of those four acts; it is today's path, 7000 from the start.
- Local operation does not depend on the overlay; overlay absent means remote access absent, local unchanged.

Details, the off switches and the records: `docs/REMOTE_TRUST.md` §3-§5, §8, §14.

## Deferred UDP evidence gate

**Closed 2026-09-24 (D6-R1):** the saved suite was replayed on the Linux hub + home Opal + onn path and did NOT
reproduce the old signature in either direction (`../investigations/DEFERRED.md`,
`../evidence/D6_R1_UDP_SUITE_REPLAY_2026-09-24.md`). The text below is the gate as written.

The severe bidirectional burst/gap/duplication behavior observed in the older
Windows/current-network Prototype-1 environment remains unresolved.

Do not tune product buffering around that historical environment.

After Linux migration, replay the saved synthetic transport suite on the
representative:

`Linux hub + home Opal + onn`

path.

If that representative local path is clean, proceed with greater confidence to
WAN characterization. If it reproduces the pathology, investigate that local
representative path before layering WAN jitter/loss on top.

Never ask the user to paste network addresses. Shareable diagnostics must redact
network identifiers and unnecessary private paths.
