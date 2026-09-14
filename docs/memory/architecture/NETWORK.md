---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# Network Architecture

## Current architectural trust boundary

The ordinary household router/Wi-Fi is upstream Internet infrastructure only.
It is **not** the PrivyHub trust domain.

The home Opal defines the PrivyHub network/trust domain. Current and future
PrivyHub server/client/device infrastructure belongs behind that boundary,
including:

- the future Linux hub;
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

## Future remote topology

Phase G will establish a portable trusted-LAN model:

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
future Linux hub behind the home Opal
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

Future Phase G must separate:

- client identity;
- session identity;
- reachable media/audio/controller endpoints;
- overlay/path state;
- application authorization.

Source/request IP is not durable client identity.

Remote access must not flatten or expose the ordinary household LAN.

## Deferred UDP evidence gate

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
