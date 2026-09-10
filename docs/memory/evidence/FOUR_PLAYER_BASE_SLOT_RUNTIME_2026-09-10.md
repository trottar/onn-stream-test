---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Four-Player Base-Slot Runtime Validation — 2026-09-10

## Result

`FOUR_PLAYER_BASE_SLOTS_CONFIRMED`

The development four-player base patch is runtime validated at the PHI1/ViGEm/XInput slot layer.

## Raw measurements

- Bridge `MAX_PLAYERS`: 4.
- PHI1 packet size: 36 bytes; protocol version/layout unchanged.
- Host had no occupied XInput slots before the isolated bridge start.
- Four XInput slots appeared after bridge start: 1, 2, 3, 4.
- Synthetic routing was exact: P1 -> slot 1/A, P2 -> slot 2/B, P3 -> slot 3/X, P4 -> slot 4/Y.
- ViGEm updates by player: `[30, 30, 30, 30]`.
- Packets received: 120.
- Lost/rejected/bad packets: 0 / 0 / 0.
- All slots returned neutral after synthetic release.
- All four temporary slots disappeared after bridge stop.

The exact returned probe output is retained in `evidence/raw/four_player_controller_probe_2026-09-10.txt`.

## Interpretation boundary

This proves the four-player base transport/device layer and clean teardown. It does **not** yet prove four distinct physical Android controllers, RetroArch port assignment, P3/P4 A8 profile/editor behavior, multitap/core behavior, or four-player gameplay.

## Next evidence

Run the real Android physical-controller assignment probe while a normal PrivyHub game session is active. It must show four distinct physical controllers reaching four distinct XInput slots. Preserve the raw per-controller slot observations even if first-touch ordering differs.
