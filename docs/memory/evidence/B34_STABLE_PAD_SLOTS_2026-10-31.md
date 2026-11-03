---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8 (companion/ tools/ tests/ PrivyHub/ clean at the start; B34 uncommitted, built in /tmp/b_q31l_b34)
---

# B34 — stable player slots, gamepads only (`debug.privyhub.pad_slots=stable`); the slot map at the host; the PS1 pad setup settled

**Classification: BUILT** behind `debug.privyhub.pad_slots=stable` (client), with the host's rows keyed on the
client's own `pad_slots` key; **SETTLED** (the PS1 config, read-only, nothing changed).
- **Tests:** JVM `PadSlotsTest` 7 green, the JVM suite **168 / 168** (161 + 7). `tests/pad_slots` 5 green. Every
  host suite is as at the queue-L baseline, plus the new suite.
- **Mutations:** three, all caught.
- **Proof:** absent = today, PROVEN.
- **Not done:** NOT INSTALLED (the coordinator's APK carries it); no live run; nothing committed.

Design `b34_2026-10-31/design_written_before_code.md`, sha256 `28fceb64…4e6b`, hashed **17:37:41Z, before any B34
code**. The facts are TRIP-R2 §3:
- `NativeControllerSender.kt:447-474` gives out slots in first-input order;
- it clears them at every `start()` / `stop()`;
- the motion filter takes any device with stick or hat axes.

## 1. Built (`b34.diff`)

**The client: `streaming/PadSlots.kt` (new).**
- **`PadSlotsFlag`:** `stable` only (trimmed). Anything else, or a failed read, means today.
- **`PadDevice`:** the reads the slots need. `AndroidPadDevice(InputDevice)` is the onn's adapter, and `connected()`
  reads the system's device list. Fakes stand in on the JVM.
- **Eligible devices:**
  - not virtual;
  - `SOURCE_GAMEPAD` or `SOURCE_JOYSTICK`;
  - **and** at least one of `BUTTON_A/B/X/Y/L1/R1/START/SELECT` in `hasKeys`.
  - The remote and an air mouse, or a pad's motion or touchpad device with axes and no button, are not eligible.
    Their events are not taken and go to the system as today's non-controller events do.
- **The key and the class:**
  - the key is 6 hex of `sha256(vendor:product:descriptor)`; the descriptor never leaves the class;
  - the class comes from the vendor id only (`sony` / `microsoft` / `nintendo` / `8bitdo` / `logitech` / `google` /
    `gamepad`). No names.
- **`PadSlots`, one per process** (`PadSlotsProcess.slots`, which outlives the activity: a self-restart and a
  recreation keep it; **a new process starts empty**):
  - **`beginStart(connected)`** runs at every sender `start()`, so at every `native-stream-start`, a self-restart
    included. Connected eligible pads without a slot take the lowest free slots **in the system's controller-number
    order**, with the key as tie-break. So the slots do not depend on which pad presses first.
  - **`slotFor`:** a pad keeps its slot. A later pad takes the lowest free slot. If all four are held, it takes the
    slot of the lowest pad that is no longer connected; otherwise none, as today's fifth device.
  - A pad that leaves keeps its slot.
- **`NativeControllerSender.kt` (+11):**
  - `padSlots` and `connectedPads`, null / empty by default;
  - `start()` calls `padSlots?.beginStart(...)`;
  - `playerForDevice` returns `padSlots.slotFor(...)` when it is set.
  - Today's `devicePlayers` path is untouched.
- **`NativeStreamActivity.kt` (+15, one line changed):**
  - `padSlots` is a lazy (`PadSlotsFlag.fromSystem()`), handed to the sender before its start;
  - the report gets `pad_slots_mode: "stable"` and `pad_slots` (`[{slot, pad, class}]`);
  - the heartbeat and the `native-stream-start` query get `&pad_slots=<slot:pad:class,…>` through `padSlotsQuery()`,
    which is `""` with no object.

**The host: `companion/pad_slots.py` (new).**
- **No host flag:** the client's key is the switch. An old or flag-absent client sends no key, and then nothing
  imports the module.
- **`plugins/games.py` (+14):** two guarded blocks, `if "pad_slots" in query:`. One is in the heartbeat handler,
  before the fields check. The other is in the start handler, after B28's call.
- **`games/native_stream_heartbeat.py` (+5):** three keys are copied onto the row when present.
- **Rows:**
  - **at each start**, from the start query: one recovery-log row `pad_slots`, `when: "start"`, with `slots` and
    `count`;
  - **on each heartbeat** with the key: the heartbeat row gets `pad_slots` (the list) and **`updates_by_player`**,
    the controller bridge's per-slot counters (`native_session_io.py:2719`, kept until now only in the live
    `/status`). So a record can say which pad held which slot and which slot was sending.
  - **a change row** `pad_slots`, `when: "change"`, with `heartbeat_sequence`, when the map moves (a pad joins).
- **A malformed value** is dropped, and `pad_slots_bad: true` is written instead. The raw value is never written.
  The check is strict: ≤ 4 entries of `[0-3]:[0-9a-f]{6}:[a-z0-9]{2,12}`, with distinct slots.

## 2. Tests (`tests_pad_slots_jvm.xml`, `tests_jvm.txt`, `tests_pad_slots_host.txt`, `tests_regression_after.txt`, `tests_mutations.txt`)

- **JVM, fake devices (7):**
  - two pads give the same slots whichever is listed first and whichever presses first (4 orders);
  - a restart (the same process object, a new start, B pressing first) gives the same slots and the same map;
  - a remote (keyboard + dpad) and an air mouse (joystick axes, no button) get no slot, so the real pad is P1; a
    virtual device is not eligible;
  - a pad that leaves keeps P1, and a new pad takes the lowest free slot;
  - a fifth pad with four connected gets none; with one of the four gone it gets that pad's slot;
  - the map string is `slot:6hex:class` only, with no descriptor;
  - the flag is `stable` only, and off the device it reads absent.
- **Host (5), a real `LinkDropRecovery` on a temp root, a fake controller:**
  - the start key writes one `start` row;
  - heartbeats put the map and `updates_by_player` on the row, and write a `change` row only on a change;
  - a bad value is dropped and counted, never written; other malformed shapes return None;
  - **no key:** no row, no key, no `_pad_slots_log`;
  - **a fresh process without the key does not import `pad_slots`.**
- **Every host suite** (`tests_regression_after.txt`): the queue-L baseline's outcomes line for line, plus
  `tests/pad_slots` OK. The four `tools/` tests fail in a copy as at every baseline.
- **JVM 168 / 168.**
- **Mutations (3 / 3 caught):**
  - `beginStart` a no-op (slots by first input): 5 JVM tests fail, the either-order test among them;
  - the gamepad-button test removed: the remote / air-mouse test fails;
  - a change row on every heartbeat: the host change test fails.

## 3. Absent = today (`proof_flag_absent.py`, `proof_flag_absent_output.txt`)

- **The edited files without B34's lines equal the base bytes.** The diff takes out the added lines and puts back the
  one changed line (the start query's `+ padSlotsQuery()`). B34 adds code; it removes and reorders nothing.
- **Every added line is listed**, and each runs only through a null `padSlots` or a `pad_slots` key:
  - `padSlots?.…`, `padSlotsQuery()` = `""`, the declarations;
  - `if "pad_slots" in query`, `if field in values`.
- **The flag:** `padSlots` exists only when `PadSlotsFlag.parse` is true, which is `stable` only (JVM).
- **The host with no key:** the two no-key tests pass.
- **Disclosed:** with no flag the sender still holds two new fields (a null and an empty lambda). They are allocated
  and never read.
- **PROVEN.**

## 4. Settled, read-only (`config_settle.md`; nothing changed)

- **The device type** is one per title (`controller_profile`, else the system default `digital` = "PlayStation
  Controller"). Port 2 always gets port 1's type (`--device` for ports 1-2, `emulator_manager.py:5485-5508`).
- **Multitap** is per title, `off` or `port1`. Port 2's tap is always forced off. The analog toggle is `disabled` in
  every Beetle options file and is not set per title.
- **Friday's four changes to the football title** (the client's four requests; the next launches' log lines):
  1. 01:15:33 multitap **on** (port 1);
  2. 01:17:33 multitap **off**;
  3. 01:17:40 **DualShock**;
  4. 01:22:44 back to **digital**.
  TRIP-R2 counted 2 and 3 as one. The analog toggle was `disabled` throughout, as a core option; Friday did not
  change it.
- **The final state** is the default setup: `{ps1_multitap: off}`, digital on ports 1 and 2, multitap off. That is
  what the 35-min 03:34Z session ran.
- **Right for a two-player PS1 title without multitap:**
  - multitap **off**;
  - the same type on both ports: **digital** unless the title needs analog (with the toggle disabled the pad cannot
    switch modes itself);
  - **the two real pads on P1 and P2** (the uinput P1 / P2 go to ports 1 / 2), which is B34's job on the client.
- **Nothing in the config needs changing.**

## 5. Files

- **`b34_2026-10-31/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` (four files), `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design, `design.sha256`, `design_hashed_at.txt`;
  - `b34.diff` (`git apply --check` OK on the tree);
  - `proof_flag_absent.py`, `proof_flag_absent_output.txt`;
  - the test files above, `config_settle.md`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere (in the copy only, for the coordinator to apply):**
  - `companion/pad_slots.py` (new), `companion/plugins/games.py`, `companion/games/native_stream_heartbeat.py`;
  - `PrivyHub/…/streaming/PadSlots.kt` (new), `NativeControllerSender.kt`, `NativeStreamActivity.kt`;
  - `PrivyHub/app/src/test/…/PadSlotsTest.kt` (new), `tests/pad_slots/` (new);
  - `patches/B34_STABLE_PAD_SLOTS.md`.
- **Left in /tmp:** `b_q31l_b34` (the copy) and `b_q31l_b34_scratch/` (`mut/`, the JVM consoles).
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft;
  - the trip keeper and `trip_2026-10-30/` untouched; the trip read's copies only read; the config only read;
  - nothing fetched, deleted, adopted or committed; no address or identifier written.
