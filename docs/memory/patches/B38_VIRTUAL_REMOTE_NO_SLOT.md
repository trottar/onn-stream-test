---
memory_schema: 1
as_of: 2026-11-02
baseline_commit: e0155d1c
---

# B38 — the onn's virtual remote takes no player slot; `updates_by_player` counts the pad that moved

**Result: SETTLED + BUILT; JVM `VirtualRemoteNoSlotTest` 5 new, 189 / 189; host `tests/pad_slots_changes` 7 new ×3;
B34's suites unedited and green; every suite as the baseline; 2 mutations caught; absent = today PROVEN; no live run.**
Record: `evidence/B38_VIRTUAL_REMOTE_NO_SLOT_2026-11-02.md`. Diff: `evidence/b38_2026-11-02/b38.diff`. Nothing
committed.

- **Settled:**
  - HOME-1 C4's slot 0 was the onn's "virtual-remote" (KEYBOARD | DPAD | GAMEPAD, controller number 1, not
    `isVirtual()`, no stick or hat axis). It passed B34's button test and held slot 0 by controller-number order.
  - `updates_by_player` counts packets: the sender sends all four players every tick.
- **Built, inside `debug.privyhub.pad_slots=stable`:** `PadSlots.eligible()` also needs a face button (A / B / X / Y)
  and stick or hat axes, so the onn's key-only devices take no slot. No identifier is compared.
- **Built, host, turned on only by that client's `pad_slots` key:** the bridge counts a slot only when its state
  changed.
  - The heartbeat row's `updates_by_player` = the changes; `packets_by_player` = today's counts.
  - `/status` `changes_by_player`.
  - (`native_session_io.py` +13 insertions, `pad_slots.py`, `plugins/games.py` +2, `native_stream_heartbeat.py` one
    whitelist line.)
- **Apply:** `git apply evidence/b38_2026-11-02/b38.diff` from the repo root. The client half needs the APK (B5 … B25 +
  B32 + B34 + B35 + B38 + B39). The host half acts only when a client sends `pad_slots`.
- **Rollback:** the property empty (today's slots, no key, the counter off); or `git apply -R` the diff.
