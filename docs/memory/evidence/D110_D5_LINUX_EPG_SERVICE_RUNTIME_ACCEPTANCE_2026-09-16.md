# D-110 — D5 Linux EPG service runtime acceptance — 2026-09-16

**Status:** runtime validated

D-110's Linux companion EPG plugin/cache seam passed runtime validation.

## Bootstrap

Initial status:

- HTTP 200;
- ready: false;
- bootstrap in progress: false.

Explicit bootstrap:

- HTTP 200;
- ok: true;
- elapsed: 140.079 seconds.

Final status:

- ready: true;
- portable Node: 24.21.0;
- pinned upstream EPG commit:
  `78e94adb76841a63d94a53e80dbd0d52bb7c2c5c`;
- persistent toolchain footprint: 626,714,586 bytes.

## Guide acquisition

Representative refreshes:

- `10Bold.au@Sydney`
  - HTTP 200;
  - 65 programmes;
  - source `i.mjh.nz`;
  - uncached elapsed 19.538 seconds.
- `5Cops.us@UK`
  - HTTP 200;
  - 13 programmes;
  - source `i.mjh.nz`;
  - uncached elapsed 9.105 seconds.

Cache recheck for `10Bold.au@Sydney`:

- HTTP 200;
- cached: true;
- 65 programmes;
- elapsed: 0.001 seconds.

## Acceptance

Classification:

`D110_EPG_PLUGIN_RUNTIME_VALIDATED`

The Linux EPG acquisition/cache seam is accepted for D5 development.

The ~627 MB persistent toolchain footprint remains a future low-cost-Linux
optimization concern, not a blocker for Prototype-1 functional integration.

D-111 may now connect the Android EPG repository to the companion endpoint while
preserving the existing onn SQLite cache and fallback behavior.
