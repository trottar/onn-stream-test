---
memory_schema: 1
as_of: 2026-11-02
baseline_commit: e0155d1c (plus A's uncommitted G-A10 tools edits; B38 uncommitted, built in /tmp/b_q02m_b38)
---

# B38 — the onn's virtual remote takes no player slot; `updates_by_player` counts the pad that moved

**Classification: SETTLED + BUILT** inside `debug.privyhub.pad_slots=stable` (client) and that client's own
`pad_slots` key (host). No new flag.
- **Tests:**
  - JVM: `VirtualRemoteNoSlotTest` 5 new; B34's `PadSlotsTest` 7 unedited and green; the whole suite 189 / 189
    (184 + 5).
  - Host: `tests/pad_slots_changes` 7 new, green ×3; B34's `tests/pad_slots` 5 unedited and green; every suite in the
    copy (`tests_regression_after.txt`).
  - Two mutations caught.
- **Proof:** absent = today, PROVEN.
- NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b38_2026-11-02/design_written_before_code.md`, sha256 `b7ad7523…82d8e5`, hashed **02:58:25Z, before any B38
code**. Precondition (checked by the coordinator first): G-A10's record present; only the companion and `privyhub-diag`
active.

## 0. Settled (HOME-1 C4's rows `home1_2026-11-02/c4/`; the code)

- **The controller-number-1 device is the onn's "virtual-remote".**
  - Its sources are KEYBOARD | DPAD | **GAMEPAD**, with MIC and EXTERNAL printed beside them. Its vendor class is
    `google`.
  - It has no stick or hat axis (no JOYSTICK source).
  - It is the input device the system's remote service creates (the remote's keys, the voice key, a phone-app
    remote), not a pad.
- **Why it passed B34's test.** B34 admitted `!isVirtual() && (GAMEPAD or JOYSTICK) && hasKeys(any of A, B, X, Y, L1,
  R1, START, SELECT)`:
  - `isVirtual()` is true only for the built-in virtual keyboard (id −1). This device is a real one, flagged EXTERNAL,
    so the test read false.
  - It declares GAMEPAD.
  - Its key layout answers the gamepad buttons as present. *Inference:* the record has the slot, not the `hasKeys`
    answer.
  - So **a button test alone cannot exclude it**; B38's rule does not lean on it.
- **Why slot 0 both times.** B34 assigns at each start in the system's controller-number order. The virtual-remote is
  number 1 and the pads are 2 and 3, so the result was deterministic: slot 0 the remote, slots 1 / 2 the pads (players
  2 / 3). In a two-player PS1 title without multitap that is Friday's E3 hazard, now every time.
- **Why `updates_by_player` rose equally on all four slots** (C4: +318 each in 3 s):
  - the sender sends one full-state packet for **every** player 0-3 on every ~8-ms tick (CTRL-L1;
    `NativeControllerSender.sendLoop`);
  - the host's `NativeControllerBridge._apply_report` counts `_updates_by_player[player] += 1` per packet;
  - **so it counts ticks, not pads.** To say which pad was used, the host must count a slot only when its state
    (buttons, sticks, triggers) **changed** in that tick.

## 1. Built (`b38.diff`)

**Client (`PadSlots.kt` only; +23 lines, one line extended).** `eligible()` also requires:
- **a face button** (`hasKeys` A / B / X / Y; the PS buttons map to these codes);
- **stick or hat axes:** a JOYSTICK motion range for `AXIS_X` / `AXIS_Y` / `AXIS_HAT_X` / `AXIS_HAT_Y`.

The onn's own input devices are identified **by class, with no identifier**:
- the virtual-remote, the "Onn-Remote Keyboard" and gpio-keys are key-only, so they never take a slot;
- every real pad, a D-pad-only one included, reports its stick or hat as joystick axes;
- **the limit:** a pad in a keyboard-emulation mode (no axes) takes no slot. It is not a gamepad then.

No vendor, product or name is compared. `PadDevice` gains `hasFaceButton` / `hasStickOrHat` with default getters, so
B34's fakes and tests are unedited. Nothing else changes: the key, the classes, the order, the holder, the map, the rows.

**Host:**
- **`native_session_io.py` (+13, insertions only):**
  - `NativeControllerBridge._changes_by_player = None` (a class attribute);
  - in `_apply_report`, `+= 1` when enabled **and** the clamped report differs from that player's previous one;
  - `start()` zeroes it when enabled;
  - `status()` gains `changes_by_player` only when enabled. Its own `updates_by_player` / `vigem_*` stay per-packet,
    because four `tools/` probes read them as packet counts.
- **`pad_slots.py`:**
  - `enable_changes(controller)` (idempotent; False with no bridge);
  - `updates_by_player()` turns it on and returns `{changes, packets}`;
  - `SlotsLog.heartbeat` writes **`updates_by_player` = the changes** and **`packets_by_player` = today's per-packet
    counts**.
- **`plugins/games.py` (+2):** inside B34's start block, `enable_changes` at the start query, so a session counts from
  its first tick.
- **`games/native_stream_heartbeat.py`:** `packets_by_player` added to B34's whitelist of row keys.
  - **Disclosed:** the design named the row field but not this whitelist line; the first host test run found it.

**Enabled only by a stable-slot client's `pad_slots` key.** An old or flag-absent client sends none, so nothing changes.

## 2. Tests (`tests_jvm.txt`, `jvm/`, `tests_pad_slots_changes.txt`, `tests_mutations.txt`, `tests_regression_after.txt`)

**JVM `VirtualRemoteNoSlotTest`** (fakes with the B38 fields set explicitly):
- **the virtual-remote as C4 described it** (KEYBOARD | DPAD | GAMEPAD, number 1, face buttons answered present, no
  axes) → no slot. Among virtual-remote, remote keyboard, pad A (2), its touchpad and pad B (3), only the two pads hold
  slots 0 and 1;
- **two pads in either press order** → pad A 0, pad B 1; a restart in the same process keeps them; two entries;
- a virtual device, a pad without face buttons, a key-only "gamepad", the remote keyboard and the touchpad → none;
  a pad → eligible;
- a hat-only pad → eligible;
- **absent:** `PadSlotsFlag.parse` false for null / "" / "1" (no object: B34's absent, today's first-input order),
  true for `stable`.

**Host `tests/pad_slots_changes`** (the real `_apply_report`, the gamepad write stubbed; `plugins/games.py` with a real
LinkDropRecovery):
- 300 ticks × 4 players, player 1 pressing A for 10 ticks:
  - `changes_by_player` [0, 2, 0, 0] (the press and the release);
  - `updates_by_player` / `vigem_*` [300 × 4], unchanged;
- an axis 0 → 1000 → 2000 with holds → 2 changes;
- **not enabled:** no `changes_by_player`; the status keys a never-fed bridge's;
- enable is idempotent (no reset) and refused with no bridge;
- **a start + heartbeat with `pad_slots`:**
  - on from the start;
  - the row's `updates_by_player` [2, 0, 0, 0], `packets_by_player` [200 × 4];
- **no key:** none of `pad_slots` / `updates_by_player` / `packets_by_player` / `pad_slots_bad` on the row; the
  counter off;
- **a fresh process without the key:** `pad_slots` not imported, the attribute None.

**Mutations** (`tests_mutations.txt`):
- **M1 (client):** the axes term removed from `eligible()` → 3 of 5 `VirtualRemoteNoSlotTest` fail; B34's 7 still
  pass (they never had such a device);
- **M2 (host):** `report != previous` → `True` → 4 of 7 fail.

**Every suite in the copy:** the queue M baseline's outcomes plus `tests/pad_slots_changes`. The four `tools/` tests
fail in a copy as at every baseline.

## 3. Proof: absent = today (`proof_flag_absent.py`, `proof_flag_absent_output.txt`): **PROVEN**

- **`native_session_io.py` and `plugins/games.py`:** insertions only; removing them gives the base bytes (13 and 2
  lines).
- **`native_stream_heartbeat.py`:** the one widened whitelist tuple, with a key only the `pad_slots` path sets.
- **Behaviour with no key**, the same scripted run (a bridge fed 120 ticks with a press; a plugin start and heartbeat)
  in a fresh process from the base and the new copy:
  - the bridge status, the heartbeat row (times masked) and the recovery rows are identical;
  - `pad_slots` is not imported; no `changes_by_player`.
- **Client:** `PadSlots.kt` is the only main file changed. Its object exists only when the property reads `stable`
  (B34's absent, PROVEN there).

## 4. For HOME-2 (C4')

- **Do:** with the new APK, `adb shell setprop debug.privyhub.pad_slots stable`; two pads paired; a two-player PS1
  title. Press pad B first, then exit, relaunch, press pad A first. In one session press only pad A for ~5 s, then only
  pad B.
- **Pass:**
  - **both starts:** recovery rows `"event": "pad_slots", "when": "start"` with **`count` 2**, slots 0 and 1, both
    `class: sony` (no `google` entry), the same two `pad` hashes both times; the lower controller number of the two pads
    is slot 0;
  - **the heartbeat rows** carry `pad_slots` (two entries) and **`updates_by_player`** rising on pad A's slot only
    while A is pressed, then on pad B's only (the others +0 or a few from stick drift), with `packets_by_player` rising
    equally on all four;
  - `/status` `controller.changes_by_player` likewise.
- **Off:** `adb shell setprop debug.privyhub.pad_slots ""`. Then no `pad_slots` row or key, and no
  `packets_by_player`.

## 5. Files

- **`b38_2026-11-02/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` (the six edited files' base bytes + `native_stream_heartbeat.py`), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b38.diff`, `proof_flag_absent.py` / `_output.txt`;
  - `tests_jvm.txt`, `jvm/` (the two XMLs), `tests_pad_slots_changes.txt`, `tests_mutations.txt`,
    `tests_regression_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere (in the coordinator's integration):**
  - `PrivyHub/.../streaming/PadSlots.kt`, `PrivyHub/.../test/.../VirtualRemoteNoSlotTest.kt` (new);
  - `companion/native_session_io.py`, `companion/pad_slots.py`, `companion/plugins/games.py`,
    `companion/games/native_stream_heartbeat.py`, `tests/pad_slots_changes/` (new);
  - `patches/B38_VIRTUAL_REMOTE_NO_SLOT.md`.
- **Left in /tmp:** `b_q02m_b38` (the copy), `b_q02m_b38_scratch/` (`mut1/`, `mut2/`, consoles).
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched; nothing of A's touched;
  - nothing fetched, adopted or committed.
- **Disclosed:** a stray `rm -rf /dev/null` was typed inside one mutation command line. As a non-root user it failed
  and removed nothing: `/dev/null` was checked afterwards, unchanged (`crw-rw-rw-`, root, its original date). Nothing
  was deleted.
