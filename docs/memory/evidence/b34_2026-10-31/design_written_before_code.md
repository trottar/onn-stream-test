# B34 — stable player slots, gamepads only: the design, written before any B34 code

Queue: `handoffs/QUEUE_2026-10-31L.md` §B34. Facts: TRIP-R2 §3 — `NativeControllerSender.kt:447-474` hands out slots
in first-input order, clears them at every `start()` / `stop()` (`:111`, `:136`), and the motion filter (`:278`)
accepts any device with stick or hat axes; so P1 / P2 can swap at every relaunch or restart and a non-pad device can
take a slot and push the second pad to P3 (a PS1 without multitap reads P1-P2 only).

## The flag

`debug.privyhub.pad_slots=stable` (CL-B7P's convention, read through reflection as `RestartGuardFlag`).
`PadSlotsFlag.parse(v) = v?.trim() == "stable"`. Absent / empty / any other value / a failed read = **today**: no
object, the sender's code path as today (first-input order, cleared at start and stop, any stick-axis device), no
report key, no heartbeat key, no start-query key.

## The client (`streaming/PadSlots.kt`, new; small hooks in `NativeControllerSender.kt` and `NativeStreamActivity.kt`)

- **`PadDevice`** (interface; the JVM tests use fakes): `descriptor`, `vendorId`, `productId`, `sources`,
  `controllerNumber`, `hasGamepadButton`, `isVirtual`. `AndroidPadDevice(InputDevice)` is the one adapter
  (`hasGamepadButton` = `hasKeys(BUTTON_A, B, X, Y, L1, R1, START, SELECT)` any true).
- **Eligible** = not virtual AND (`SOURCE_GAMEPAD` or `SOURCE_JOYSTICK` in `sources`) AND `hasGamepadButton`. A remote
  (keyboard / dpad sources) and an air mouse or a pad's touchpad with axes but no gamepad button are not eligible:
  their keys and motions are not taken by the sender and go on to the system as any non-controller event does today.
- **The key** = `sha256("vendor:product:descriptor")`, first 6 hex chars (`pad`); the raw descriptor never leaves
  the object. **The class** (`class`): a vendor class from the vendor id only — `sony`, `microsoft`, `nintendo`,
  `8bitdo`, `logitech`, `google`, else `gamepad`. No device names anywhere.
- **`PadSlots`** (one per process: `PadSlotsProcess.slots`, so it outlives the activity — the six restarts were the
  same instance; a recreation is the same process; **a new process starts empty**, stated):
  - `beginStart(connected)`: at each `NativeControllerSender.start()` (each `native-stream-start`, including a
    self-restart): every connected eligible pad without a slot gets the lowest free slot, **in the system's
    controller-number order** (`getControllerNumber()`, the order Android numbered the pads when they connected, 0
    last), the key as the tie-break — so two pads get the same slots **whichever presses first**; slots already held
    are kept.
  - `slotFor(device, connected)`: a pad with a slot keeps it; an eligible pad seen later takes the lowest free slot;
    if all four are held, the lowest slot whose pad is no longer connected is reused (that pad's entry dropped);
    else none (as today's fifth device). A pad that leaves keeps its slot (nothing is removed at stop or on a
    disconnect).
  - `start()` / `stop()` do **not** clear it (today's `devicePlayers.clear()` stays on the today path).
  - `mapString()` = `slot:pad:class` joined by `,` in slot order, e.g. `0:a1b2c3:sony,1:d4e5f6:sony`;
    `toJson()` = `[{"slot":0,"pad":"a1b2c3","class":"sony"},…]`.
- **The sender:** `var padSlots: PadSlots? = null` (null = today). With it: key events need an eligible device;
  motion events need an eligible device (today's axis test not used); the player = `padSlots.slotFor(...)`; `start()`
  calls `beginStart(connected)`, the per-player state still reset as today. The connected list is read through a
  `() -> List<PadDevice>` given by the activity (`InputDevice.getDeviceIds()`).
- **The activity:** `private val padSlots: PadSlots? by lazy { if (PadSlotsFlag.fromSystem()) PadSlotsProcess.slots
  else null }` set on the sender before `start()`; the report gets `pad_slots` (the JSON array) and
  `pad_slots_mode: "stable"`; the heartbeat gets `&pad_slots=<url-encoded mapString>`; the start query gets the same
  `&pad_slots=…` (the map after `beginStart` — the start runs after the sender's start in `startSession`; if the map
  is empty the key is still sent, empty, so the host can say "no pad").

## The host (`companion/pad_slots.py`, new; one guarded block in `plugins/games.py`'s heartbeat handler and one in
its start handler; two lines in `games/native_stream_heartbeat.py`)

- No host flag: the client's key is the switch. **An old or flag-absent client sends no `pad_slots` key → the host
  imports nothing new and writes byte for byte today** (the import is inside the `if "pad_slots" in query` block).
- `parse(raw)`: strict — up to four `^[0-3]:[0-9a-f]{6}:[a-z0-9]{2,12}$` entries, distinct slots, else the value is
  dropped (`pad_slots_bad` counted on the row, the raw value never written).
- **At each start** (the start query's `pad_slots`): one recovery-log row `pad_slots` with `when: "start"`,
  `slots` (the list of `{slot, pad, class}`), `count`.
- **On each heartbeat** carrying the key: the heartbeat row gets `pad_slots` (the parsed list) and
  `updates_by_player` (the controller bridge's per-slot counters, already kept — `native_session_io.py:2719`), so a
  record can say which pad was which and which slot was sending; and a `pad_slots` recovery row with
  `when: "change"` when the map differs from the last one written (a pad joining).

## Tests

- **JVM (`PadSlotsTest.kt`, fake devices):** two pads, either enumeration and either press order → the same slots;
  a restart (`beginStart` again, the same process object) → the same slots; a pad that leaves keeps its slot and a
  new one takes the lowest free; a stick-axis remote / air mouse (axes, no gamepad button) excluded; a fifth pad with
  all four connected → none, with one gone → the gone pad's slot; the map string / JSON carry no descriptor; the flag
  parse (`stable` only). **Absent → today:** the sender's today path is a pure function extracted as
  `TodaySlots` (first-input order, cleared at start) only if needed — else the absent proof is the AST/text compare of
  the today path. The hash is 6 hex of sha256.
- **Host (`tests/pad_slots/`):** the start key → one `pad_slots` row; heartbeat key → the row's `pad_slots` +
  `updates_by_player`, a change row only on change; a bad value → dropped, counted; no key → the heartbeat row and
  the recovery log byte for byte as today and `pad_slots` not imported (a fresh process).
- **Mutations:** the order by first input instead of controller number (the either-order test fails); the axis test
  instead of the button test (the remote test fails).

## Settle, read-only (no config change)

The Beetle PSX port-2 device type and multitap per title in the tree; Friday's four changes in 17 min (the trip's
game logs and journal copies, read-only) and the final state now; the right setting for a two-player PS1 title
without multitap.
