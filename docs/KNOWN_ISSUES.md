# Known issues and deferred work

Status as of 2026-09-07.

| Issue | Status | Blocks current prototype? | Resume when |
| --- | --- | --- | --- |
| Bidirectional UDP burst/gap distortion and duplication in current network path | Deferred after deep isolation | No | Dedicated Linux/network infrastructure is available, or the issue appears on representative hardware |
| `companion/games/` source was unintentionally ignored | Fix in this checkpoint | Yes for fresh-clone reproducibility until committed | This checkpoint |
| Sunshine/Moonlight legacy integration and scripts | Deferred cleanup | No | After transport work is frozen / before Linux-native host work expands |
| Native streaming host is Windows-specific | Expected prototype limitation | No | Linux infrastructure phase |
| WGC/FFmpeg runtime bootstrap is not fully represented by the pushed tree | Portability debt | No for current machine | Linux/bootstrap work or clean-machine reproducibility pass |
| Automated CI coverage is minimal | Deferred | No | Before productization or multi-platform expansion |

## UDP transport pathology

### Symptom

Production game audio can underrun despite healthy process-audio callbacks and nominal 5 ms packet pacing. Synthetic probes reproduced large arrival bursts/gaps without production video/audio load.

### Current conclusion

The dominant timing distortion is outside the application layers. It has been observed in both directions across the prototype's network path.

The investigation does **not** establish which individual network component is at fault. Remaining possibilities include endpoint Wi-Fi firmware/driver behavior, USB Wi-Fi internals, access-point/router behavior, bridging/routing/offload behavior, RF scheduling, or an interaction among the current consumer-network devices.

### Product decision

Do not encode this test environment's measured jitter or duplicate rate into the product architecture yet. Preserve the diagnostic suite and retest on the dedicated Linux infrastructure.

Full record: `investigations/2026-09-07-udp-transport.md`.

## `companion/games/` source tracking defect

The tracked `companion/plugins/games.py` imports:

- `games.emulator_manager`;
- `games.stream_manager`;
- `games.decoder_session_log`.

Python resolves those modules from `companion/games/` when the companion is launched from `companion/privyhub_service.py`. A direct import-resolution check on the development machine confirmed:

- `games` -> `companion/games/__init__.py`;
- `games.emulator_manager` -> `companion/games/emulator_manager.py`;
- `games.stream_manager` -> `companion/games/stream_manager.py`;
- `games.decoder_session_log` -> `companion/games/decoder_session_log.py`.

The files existed locally but were hidden from Git because `.gitignore` contained an unanchored `games/` rule. In Git ignore syntax that matched both the intended repository-root ROM/content directory and `companion/games/`.

This checkpoint changes only that rule to the anchored `/games/` form. Root game content remains ignored while `companion/games/` application source becomes eligible for normal tracking.

Before committing, the repository audit must show the required `companion/games/*.py` files as present. They should be included in the checkpoint commit; repository-root `/games/` content must remain ignored.

## Sunshine / Moonlight legacy

The baseline still contains Sunshine setup/firewall/UI scripts and the Games plugin still constructs and invokes a legacy `StreamManager` path around game launch/status. Native streaming should eventually become the sole game-stream path, but remove legacy pieces in a dedicated cleanup after this diagnostic checkpoint is safely committed.
