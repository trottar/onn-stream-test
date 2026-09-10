#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

XINPUT_A = 0x1000
EXPECTED_SLOTS = [0, 1, 2, 3]


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_uint32),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


@dataclass
class CaptureResult:
    slot: int
    press_snapshot: dict[int, int]
    released: bool
    ambiguous: bool
    slots_stable: bool


def load_xinput():
    if os.name != "nt":
        raise RuntimeError("Windows XInput measurement is Windows-only")

    errors: list[str] = []
    for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            dll = ctypes.WinDLL(name)
            fn = dll.XInputGetState
            fn.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_STATE)]
            fn.restype = ctypes.c_uint
            return fn, name
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    raise RuntimeError("Unable to load XInputGetState: " + "; ".join(errors))


def xinput_states(get_state) -> dict[int, int]:
    result: dict[int, int] = {}
    for index in range(4):
        state = XINPUT_STATE()
        if int(get_state(index, ctypes.byref(state))) == 0:
            result[index] = int(state.Gamepad.wButtons)
    return result


def wait_for_four_slots(
    reader: Callable[[], dict[int, int]],
    timeout: float,
) -> dict[int, int]:
    deadline = time.monotonic() + timeout
    latest: dict[int, int] = {}
    while time.monotonic() < deadline:
        latest = reader()
        if sorted(latest) == EXPECTED_SLOTS:
            return latest
        time.sleep(0.05)
    return latest


def stable_a_neutral(
    reader: Callable[[], dict[int, int]],
    timeout: float,
    stable_samples: int = 5,
    poll_interval: float = 0.01,
) -> tuple[bool, bool]:
    deadline = time.monotonic() + timeout
    neutral = 0
    slots_stable = True

    while time.monotonic() < deadline:
        states = reader()
        if sorted(states) != EXPECTED_SLOTS:
            slots_stable = False
            neutral = 0
        elif all((states[slot] & XINPUT_A) == 0 for slot in EXPECTED_SLOTS):
            neutral += 1
            if neutral >= stable_samples:
                return True, slots_stable
        else:
            neutral = 0
        time.sleep(poll_interval)

    return False, slots_stable


def capture_a_press(
    reader: Callable[[], dict[int, int]],
    timeout: float,
) -> CaptureResult:
    neutral, slots_stable = stable_a_neutral(reader, timeout)
    if not neutral:
        return CaptureResult(-1, {}, False, False, slots_stable)

    deadline = time.monotonic() + timeout
    press_snapshot: dict[int, int] = {}
    observed_slot = -1
    ambiguous = False

    while time.monotonic() < deadline:
        states = reader()
        if sorted(states) != EXPECTED_SLOTS:
            slots_stable = False
            time.sleep(0.01)
            continue

        active = [
            slot
            for slot in EXPECTED_SLOTS
            if states[slot] & XINPUT_A
        ]
        if len(active) > 1:
            press_snapshot = dict(states)
            ambiguous = True
            break
        if len(active) == 1:
            press_snapshot = dict(states)
            observed_slot = active[0]
            break
        time.sleep(0.01)

    if observed_slot < 0 or ambiguous:
        return CaptureResult(
            observed_slot,
            press_snapshot,
            False,
            ambiguous,
            slots_stable,
        )

    released, release_slots_stable = stable_a_neutral(reader, timeout)
    return CaptureResult(
        observed_slot,
        press_snapshot,
        released,
        ambiguous,
        slots_stable and release_slots_stable,
    )


def format_slots(states: dict[int, int]) -> str:
    if not states:
        return "none"
    return ", ".join(str(slot + 1) for slot in sorted(states))


def format_snapshot(states: dict[int, int]) -> str:
    if not states:
        return "none"
    return ", ".join(
        f"slot {slot + 1}=0x{states.get(slot, 0) & 0xFFFF:04X}"
        for slot in EXPECTED_SLOTS
    )


def write_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def self_test() -> int:
    samples = (
        [{0: 0, 1: 0, 2: 0, 3: 0}] * 5
        + [{0: 0, 1: 0, 2: XINPUT_A, 3: 0}]
        + [{0: 0, 1: 0, 2: 0, 3: 0}] * 5
    )
    index = 0

    def reader() -> dict[int, int]:
        nonlocal index
        if index < len(samples):
            value = samples[index]
            index += 1
            return dict(value)
        return dict(samples[-1])

    result = capture_a_press(reader, timeout=0.2)
    assert result.slot == 2
    assert result.released
    assert not result.ambiguous
    assert result.slots_stable
    assert result.press_snapshot[2] & XINPUT_A

    distinct = [0, 3, 1, 2]
    assert len(set(distinct)) == 4
    assert set(distinct) == set(EXPECTED_SLOTS)
    assert distinct != EXPECTED_SLOTS

    print("SELF-TEST PASSED")
    return 0


def run(root: Path, timeout: float) -> int:
    root = root.resolve()
    log_path = root / "logs" / "games" / "four_player_android_assignment_probe.txt"
    lines = [
        "PrivyHub Phase A real Android four-controller assignment probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        "Classification: RUNNING",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== RAW MEASUREMENTS ===",
    ]

    try:
        get_state, dll_name = load_xinput()
        reader = lambda: xinput_states(get_state)

        initial = wait_for_four_slots(reader, timeout)
        lines.append(f"XInput DLL: {dll_name}")
        lines.append(f"Slots present before capture: {format_slots(initial)}")

        if sorted(initial) != EXPECTED_SLOTS:
            raise RuntimeError(
                "Four XInput slots are not active. Start a normal PrivyHub game "
                "session with the four-player base patch before running this probe."
            )

        print("Four XInput slots detected.")
        print("Use four different physical controllers connected to the ONN.")
        print("For each prompt, press and release the physical A button once.")
        print("Do not press A on more than one controller at the same time.")

        captures: list[CaptureResult] = []
        for physical in range(1, 5):
            print("")
            print(
                f"Physical controller #{physical}: press and release A now...",
                flush=True,
            )
            result = capture_a_press(reader, timeout)
            captures.append(result)
            lines.append(
                f"Physical controller {physical} observed slot: "
                + (str(result.slot + 1) if result.slot >= 0 else "none")
            )
            lines.append(
                f"Physical controller {physical} press snapshot: "
                + format_snapshot(result.press_snapshot)
            )
            lines.append(
                f"Physical controller {physical} release confirmed: {result.released}"
            )
            lines.append(
                f"Physical controller {physical} ambiguous simultaneous A: {result.ambiguous}"
            )
            lines.append(
                f"Physical controller {physical} four-slot continuity: {result.slots_stable}"
            )

            if result.slot < 0:
                raise RuntimeError(
                    f"No unambiguous A press was captured for physical controller {physical}."
                )
            if result.ambiguous:
                raise RuntimeError(
                    f"Multiple XInput slots reported A simultaneously during physical controller {physical}."
                )
            if not result.released:
                raise RuntimeError(
                    f"A release was not confirmed for physical controller {physical}."
                )
            if not result.slots_stable:
                raise RuntimeError(
                    f"The four XInput slots changed during physical controller {physical} capture."
                )

        observed = [capture.slot for capture in captures]
        distinct = (
            len(set(observed)) == 4
            and set(observed) == set(EXPECTED_SLOTS)
        )
        first_touch_order = observed == EXPECTED_SLOTS
        final_states = reader()
        final_neutral = (
            sorted(final_states) == EXPECTED_SLOTS
            and all(
                (final_states[slot] & XINPUT_A) == 0
                for slot in EXPECTED_SLOTS
            )
        )

        lines.append(
            "Observed physical-controller mapping: "
            + ", ".join(
                f"physical {index + 1}->slot {slot + 1}"
                for index, slot in enumerate(observed)
            )
        )
        lines.append(f"Four distinct slots observed: {distinct}")
        lines.append(f"First-touch order maps 1->1, 2->2, 3->3, 4->4: {first_touch_order}")
        lines.append(f"Four slots still present after capture: {sorted(final_states) == EXPECTED_SLOTS}")
        lines.append(f"A buttons neutral after capture: {final_neutral}")

        if not distinct:
            raise RuntimeError(
                "Four different physical controllers did not reach four distinct XInput slots."
            )
        if not final_neutral:
            raise RuntimeError("Final XInput A state was not neutral across all four slots.")

        classification = "ANDROID_FOUR_CONTROLLER_ASSIGNMENT_CONFIRMED"
        lines[2] = f"Classification: {classification}"
        write_log(log_path, lines)
        print("")
        print(classification)
        print(f"Log: {log_path}")
        return 0

    except Exception as exc:
        lines.append(f"Error: {exc}")
        lines[2] = "Classification: ANDROID_FOUR_CONTROLLER_ASSIGNMENT_NOT_CONFIRMED"
        write_log(log_path, lines)
        print("ANDROID_FOUR_CONTROLLER_ASSIGNMENT_NOT_CONFIRMED", file=sys.stderr)
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"Log: {log_path}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    return run(args.root, max(5.0, float(args.timeout)))


if __name__ == "__main__":
    raise SystemExit(main())
