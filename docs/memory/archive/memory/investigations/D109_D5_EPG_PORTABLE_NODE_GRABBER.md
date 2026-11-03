# D-109 — D5 EPG portable-Node grabber diagnostic

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:D109_RESULT:BEGIN -->
## Result — 2026-09-16

D-109 passed.

Classification:
`D109_PORTABLE_NODE_LOCAL_GRABBER_VIABLE_MULTI_SITE`.

Portable runtime:
- Node 24.21.0;
- npm 11.19.0;
- official checksum verified;
- runtime removed after probe.

Refreshed D-108 measured:
- 91 configured candidate sites;
- 77.42 second upstream setup;
- 445,831,397 byte disposable toolchain tree.

Successful programme grabs:
- i.mjh.nz: 33;
- pluto.tv: 32;
- plex.tv: 1.

Decision:
local acquisition is viable. Move to a persistent rebuildable Linux
acquisition/cache service seam; do not repeat npm setup per guide request and do
not install Node system-wide.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:D109_RESULT:END -->

**Status:** diagnostic-only / runtime evidence next

## Narrow question

Does D-108's local-grabber test succeed when the missing Node/npm environment is
supplied temporarily without installing anything on the Linux appliance?

## Predecessor evidence

D-108 stopped cleanly at the environment gate:

`D108_ENVIRONMENT_NODE_UNSUPPORTED`

No upstream checkout, npm dependency installation, or EPG acquisition attempt
occurred.

## Portable runtime

D-109 uses official Node.js v24.21.0 Linux tarballs.

Pinned SHA-256:

- Linux x64:
  `fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6`
- Linux arm64:
  `6ad1325edbdb5649c379b75a237147a666c95d4f9ae8d340fef2d1575d289ad2`

The runtime is downloaded into a temporary directory, checksum-verified,
safely extracted, and prepended to `PATH` only for the D-108 subprocess.

## Reuse boundary

D-109 does not duplicate local EPG acquisition logic.

It verifies the installed D-108 probe's expected Git blob:

`796f2a17ea226e7e5a7ad4027d4911c8ec329b38`

Then it invokes D-108 under the temporary Node/npm environment.

D-108 remains responsible for:

- onn read-only TV snapshot;
- current guide metadata;
- pinned upstream EPG checkout;
- disposable npm install/cache;
- representative multi-site selection;
- XMLTV programme counts;
- cleanup of its own temporary acquisition state.

## Cleanup

When D-109 exits, its portable Node runtime is also removed.

No system package manager, shell profile, service unit, global npm prefix, or
PrivyHub production state is modified.

## Decision boundary

- D-108 multi-site success under portable Node -> local acquisition is
  technically viable; move to a production architecture decision;
- D-108 single-site success -> viable with source-diversity risk;
- upstream npm/setup failure -> inspect that exact toolchain boundary;
- programme acquisition failure -> inspect the first measured site failure;
- checksum/download/runtime failure -> do not bypass verification.
