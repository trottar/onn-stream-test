---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8
---

# B34 — stable player slots, gamepads only (`debug.privyhub.pad_slots=stable`)

**Result: BUILT; JVM `PadSlotsTest` 7 green (168 / 168), `tests/pad_slots` 5 green, every host suite as at the
baseline; 3 mutations caught; absent = today PROVEN; the PS1 config SETTLED read-only (nothing changed); not
installed, no live run.** Record: `evidence/B34_STABLE_PAD_SLOTS_2026-10-31.md`. Diff:
`evidence/b34_2026-10-31/b34.diff`. Nothing committed.

- **The client:** `PadSlots.kt`.
  - Slots by the device's key (6 hex of a hash of vendor / product / descriptor), one object per process, so they are
    kept across starts and self-restarts.
  - Only gamepad / joystick devices with a gamepad button are eligible.
  - At each start the connected pads take the free slots in the system's controller-number order. A later pad takes
    the lowest free slot; a pad that leaves keeps its slot.
  - The map goes in the report (`pad_slots`, `pad_slots_mode`), on the heartbeat and on the start query.
- **The host:** `companion/pad_slots.py`, keyed on the client's `pad_slots`.
  - a `pad_slots` recovery row at each start and at each change;
  - the map and `updates_by_player` on the heartbeat row;
  - no key: nothing imported, today's rows.
- **Apply:** `git apply evidence/b34_2026-10-31/b34.diff`, then build the APK.
- **On the onn:** `adb shell setprop debug.privyhub.pad_slots stable`. A reboot clears it.
- **Rollback:**
  - the property empty (`adb shell setprop debug.privyhub.pad_slots ""`) means today;
  - or revert the eight paths in the diff.
