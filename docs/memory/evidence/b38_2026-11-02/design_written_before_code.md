# B38 — design, written before any B38 code (QUEUE_2026-11-02M)

## Settled first (HOME-1 C4's rows, `home1_2026-11-02/c4/`, and the code at e0155d1c)

- **The controller-number-1 device is the onn's "virtual-remote":** sources KEYBOARD | DPAD | GAMEPAD (plus the MIC and
  EXTERNAL flags `dumpsys input` prints), vendor class `google`, no stick or hat axes (no JOYSTICK source). It is the
  input device the system's remote service creates (the remote's keys, the voice key, a phone-app remote), not a pad.
- **Why it passed B34's test:** B34 admits `!isVirtual() && (GAMEPAD or JOYSTICK source) && hasKeys(any of A, B, X, Y,
  L1, R1, START, SELECT)`.
  - `isVirtual()` is true only for the built-in virtual keyboard (id −1). This device is a real kernel / uinput device
    flagged EXTERNAL, so `isVirtual()` is false.
  - It declares the GAMEPAD source.
  - Its key-layout answers `hasKeys` true for gamepad buttons (a remote-service device declares a wide key set; the
    generic layout maps BUTTON_* codes). Inference: the record shows the slot, not the `hasKeys` answer. Either way a
    face-button test alone cannot exclude it, so the rule below does not rely on it.
- **Why slot 0 both times:** B34 assigns the connected eligible devices at each start in the system's
  controller-number order; the virtual-remote has number 1, the two pads 2 and 3. So it took slot 0, deterministically,
  and the pads became slots 1 and 2 (players 2 and 3).
- **Why `updates_by_player` rose on all four slots equally (+318 each in 3 s):** the sender sends one full-state packet
  for **every** player 0-3 on every ~8-ms tick, whatever pads exist (CTRL-L1;
  `NativeControllerSender.sendLoop`). The host's `NativeControllerBridge._apply_report` does
  `self._updates_by_player[player] += 1` per packet applied (`native_session_io.py` ~2367). So it counts ticks, not
  pads. What it should count is a slot whose state **changed** in that tick (buttons, sticks or triggers differ from
  that player's previous report).

## The design (client), inside `debug.privyhub.pad_slots=stable` (absent / empty / other = today: no PadSlots object)

`PadSlots.eligible(d)` becomes: **all of**
1. `!d.isVirtual`;
2. the GAMEPAD or JOYSTICK source;
3. **a face button:** `hasKeys(BUTTON_A, BUTTON_B, BUTTON_X, BUTTON_Y)` any (the PS face buttons map to these codes);
4. **stick or hat axes:** a JOYSTICK motion range for `AXIS_X`/`AXIS_Y` or `AXIS_HAT_X`/`AXIS_HAT_Y` — **this is how
   the onn's own input devices are identified, by class, with no identifier:**
   - the virtual-remote, the "Onn-Remote Keyboard" and gpio-keys are key-only devices (no joystick axis);
   - every real pad, a D-pad-only pad included, reports its stick or hat as joystick axes.
   - No vendor / product / name is compared or written. The rule's limit: a pad in a keyboard-emulation mode (no axes)
     takes no slot. That is stated, and it is not a gamepad then.
- `PadDevice` gains `hasFaceButton` and `hasStickOrHat` with **default getters** (`hasFaceButton` = `hasGamepadButton`;
  `hasStickOrHat` = the JOYSTICK source bit), so B34's fakes and tests compile and pass unedited.
  `AndroidPadDevice` overrides both from the real `InputDevice`.
- Nothing else changes: the key, the classes, the order, the holder, the map, the rows.

## The design (host): `updates_by_player` counts changes, only for a stable-slot client

- `NativeControllerBridge` gets a class attribute `_changes_by_player = None` (today: never set, nothing counted, the
  status unchanged).
- In `_apply_report`, beside today's `+= 1`: `if self._changes_by_player is not None and report != previous:` `+= 1`
  (`previous` is `_last_reports[player]` before the write; the report dict is the clamped buttons / sticks / triggers).
- `start()` zeroes it when it is not None.
- **Enabled only by the client's own `pad_slots` key** (a B34-stable client), from `pad_slots.py`:
  - at the start query (`SlotsLog.start`, via a new `enable_changes(controller)`, one guarded line in the B34 start
    block in `plugins/games.py`);
  - and at the heartbeat (`updates_by_player(controller)` enables it too).
- **What a stable-slot client's heartbeat row then carries:**
  - `updates_by_player` = the **changed-only** counts;
  - `packets_by_player` = today's per-packet counts.
- `/status` gains `changes_by_player` only when enabled. Its own `updates_by_player` / `vigem_*` keys stay per-packet:
  four probes in `tools/` read them as packet counts.
- **Absent:** an old or flag-absent client sends no `pad_slots` key. Nothing calls `enable_changes`, the attribute stays
  None, and every row and the status are today's byte for byte. The one added check per applied report is
  `is not None`.

## Tests

**JVM** (`PadSlotsTest` unedited; a new `VirtualRemoteNoSlotTest`):
- the virtual-remote as C4 described (KEYBOARD | DPAD | GAMEPAD, controller number 1, face buttons true, no axes) →
  no slot, and the two pads (2, 3) → slots 0 and 1 in either press order and across a restart;
- a virtual device → none; a pad without face buttons → none; a hat-only pad → a slot;
- the flag absent → `PadSlotsFlag.parse` false (today: no object), and B34's tests unchanged.

**Host** (`tests/pad_slots_changes/`):
- with the real `NativeControllerBridge._apply_report` (no gamepad write: a stub sink), four players fed 300 identical
  ticks with one press on player 1 → `changes_by_player` [0, 2, 0, 0] (press, release) while `updates_by_player`
  [300 × 4];
- not enabled → no `changes_by_player`, status keys identical to a base run;
- the heartbeat with a `pad_slots` key → row `updates_by_player` = changes, `packets_by_player` = per-packet;
- without the key → row identical to today.

**Mutations:** the axes term removed (the virtual-remote test fails); `report != previous` replaced by True (the host
change test fails).
