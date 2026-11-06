# B42 — design, written before code: the screen-loss hold and stable slots on by default

The user's decisions 2026-11-06: **G-A11 yes** (the hold on by default), **G-A12 yes** (stable slots on by default),
after HOME-2's C1' / C4' were met on `0132b944…` (CONFIRMED). The form is B13 / B19 / B25 / B27's: only the flag
object's `parse` and its failed-read `catch` change. Every consumer reads the flag through these two functions, so no
consumer changes.

## 1. `debug.privyhub.surface_hold` (`SurfaceHoldFlag`, `SurfaceHold.kt`)

| value | `0132b944…` (today) | B42 |
| --- | --- | --- |
| absent / empty | off (null) | **ON, 12 000 ms** |
| `1` | 12 000 | 12 000 |
| an integer 10 000-30 000 | that bound | that bound |
| `0` | off | **off** (today's absent) |
| `off` | off | **off** (as `pad_slots`'s word; see §3) |
| junk (`yes`, `9999`, `30001`, `-5`, …) | off | **ON, 12 000 ms** (junk = on, as B25 / B27) |
| a failed property read (the JVM) | off | **ON, 12 000 ms** (B25's catch: `parse(null)`) |

## 2. `debug.privyhub.pad_slots` (`PadSlotsFlag`, `PadSlots.kt`)

| value | `0132b944…` (today) | B42 |
| --- | --- | --- |
| absent / empty | off | **stable** |
| `stable` | stable | stable |
| `off` | off | **off** (today's first-input order: no object) |
| `0` | off | **off** (B27's convention: `0` is the old absent) |
| junk (`1`, `Stable`, `junk`, …) | off | **stable** |
| a failed read | off | **stable** |

## 3. The off words

- `0` turns either flag off, as B13 / B19 / B25 / B27.
- **`off` also turns either flag off.** The queue names `off` for `pad_slots`. Accepting it for `surface_hold` too
  means the same word works on both properties: a person typing `off` should never get a hold. Both are matched after
  `trim()`, lower-case exact. `OFF` / `Off` count as junk, so on (the same rule as B25: one exact off word).

## 4. What does not change

- **B32 / B34 / B38 / B39:** no line outside the two flag objects changes. The hold, the slot assignment, the device
  test and the report refresh are exactly as built.
- **The player prompt** (`debug.privyhub.player_prompt`, B41) stays opt-in. It is not touched here.
- **The host:** it reads neither property. It acts on the client's keys: `surface_lost` on the heartbeat; `pad_slots`
  on the start query and the heartbeat (B34). With this APK every session sends `pad_slots`, so on every session:
  - the host writes a `pad_slots` recovery row at each start (and on a change);
  - B38's changed-only counter turns on: the heartbeat row's `updates_by_player` is the change count, and
    `packets_by_player` carries the old per-packet count;
  - `/status` gains `changes_by_player`; its `updates_by_player` stays per-packet (the `tools/` probes).
  - The report carries `surface_hold` and `pad_slots_mode` / `pad_slots` on every session.
  No host code changes; this is stated in the record for the readers (B36's keeper reads both rows already).

## 5. Tests (JVM, `HoldAndSlotsDefaultOnTest`, new)

- absent → on (the hold 12 000; slots stable); empty → on; junk → on (each listed value);
- `0` and `off` → off;
- `1` / `20000` / `stable` as before;
- `fromSystem()` on the JVM (no `SystemProperties`) → on for both (the catch);
- **the off path is today's absent:** for every input the old parse read as off, the new parse of `0` / `off` gives the
  same result (null / false) — the consumers then build no object, as `0132b944…` with no property.
- **Edited existing lines (disclosed, as B13 / B19 / B25):** `SurfaceHoldTest`'s flag test (the absent / empty / junk
  lines and `fromSystem()` → off), `PadSlotsTest`'s flag test (the `null` / `""` / `1` / `Stable` / `junk` → false line
  and `fromSystem()` → false), `VirtualRemoteNoSlotTest`'s absent lines (`null` / `""` / `1` → false). Each moves to
  the new meaning; `0` keeps the old assertion.

## 6. Proof (`proof_zero_is_today.md` / `.py`)

- The diff of the two main files touches only `SurfaceHoldFlag` and `PadSlotsFlag` (their doc comments, `parse`, the
  `catch`), checked by locating every changed line inside those objects' spans.
- `0` / `off` → the same value the old parse gave for absent, so every consumer takes today's null / false branch.
- **Mutation:** the old parse restored → the new tests fail.
