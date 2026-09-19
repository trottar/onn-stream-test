#!/usr/bin/env python3
"""Shared helpers for PrivyHub manual checkout probes.

Factors out the prompt/answer idiom and the report shape that every manual
checkout probe in `tools/` currently re-implements, and adds the one piece
none of them have: non-blocking in-session mark capture.

**Existing probes are deliberately not migrated to this module.** They are
runtime-validated and other probes grep their reports for exact substrings;
changing them is its own work item with its own evidence. This module is
additive. `probe_c3_l3a_gameplay_acceptance.py` is its first and only caller.

The report shape matches the existing convention exactly, because it is
load-bearing: `probe_phase_a_a9_emulator_checkpoint.py` and
`probe_ps1_multitap_onoff_runtime.py` are validated by other probes that
check for literal substrings in their output.

Import from a sibling `tools/` script:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from manual_checkout import Report, yes, MarkCapture

Privacy: nothing here collects, formats or prints a network address.
"""

from __future__ import annotations

import sys
import threading
import time

from pathlib import Path
from typing import Any, Callable


__all__ = [
    "yes",
    "ask_int",
    "Report",
    "MarkCapture",
    "Mark",
]


def yes(prompt: str) -> bool:
    """Ask a yes/no question. Default is No.

    Byte-for-byte the idiom the existing checkout probes use, so answers and
    transcripts stay comparable across probes.
    """
    value = input(prompt + " [y/N]: ").strip().casefold()
    return value in {"y", "yes"}


def ask_int(
    prompt: str,
    *,
    low: int,
    high: int,
    default: int | None = None,
) -> int | None:
    """Ask for an integer in [low, high]. Empty input returns `default`.

    Re-asks on invalid input rather than raising: a tester answering a
    debrief should not lose a session's worth of answers to a typo.
    """
    suffix = f" [{low}-{high}]"

    if default is not None:
        suffix += f" (enter = {default})"

    while True:
        raw = input(prompt + suffix + ": ").strip()

        if not raw:
            return default

        try:
            value = int(raw)
        except ValueError:
            print(f"  not a number: {raw!r}")
            continue

        if low <= value <= high:
            return value

        print(f"  out of range: {value}")


class Mark:
    """One operator observation, timestamped against the session clock."""

    __slots__ = ("elapsed_s", "severity", "raw")

    def __init__(
        self,
        elapsed_s: float,
        severity: int | None,
        raw: str,
    ) -> None:
        self.elapsed_s = float(elapsed_s)
        self.severity = severity
        self.raw = raw

    def as_dict(self) -> dict[str, Any]:
        return {
            "elapsed_s": round(self.elapsed_s, 3),
            "severity": self.severity,
        }

    def __repr__(self) -> str:
        return f"Mark({self.elapsed_s:.3f}s, severity={self.severity})"


class MarkCapture:
    """Non-blocking stdin capture of operator marks during a live session.

    The tester presses Enter the instant they notice something. Nothing is
    asked and nothing blocks, because a blocking prompt mid-session would
    itself telegraph that an event just fired — which is exactly what the
    `C3.L4` gate's blinding requirement forbids.

    An optional single digit typed before Enter is kept as a severity, since
    the tester is already at the keyboard and it costs nothing. Bare Enter
    records severity `None`.

    Timestamps are `time.monotonic()` deltas from `start()`, the same clock
    the caller must use for its own event log so the two are directly
    comparable.

    The reader runs on a daemon thread. It is never joined: `input()` on a
    terminal cannot be interrupted portably, so the thread is left blocked
    and the process exits regardless.
    """

    def __init__(self) -> None:
        self._marks: list[Mark] = []
        self._lock = threading.Lock()
        self._started_at: float | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return

        self._started_at = time.monotonic()
        self._running = True
        self._thread = threading.Thread(
            target=self._read_loop,
            name="mark-capture",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop accepting marks. The reader thread is left to die with the
        process; it may be blocked in a read that cannot be cancelled."""
        self._running = False

    def _read_loop(self) -> None:
        while self._running:
            try:
                line = sys.stdin.readline()
            except Exception:
                return

            if line == "":
                # stdin closed
                return

            if not self._running:
                return

            now = time.monotonic()
            raw = line.strip()
            severity: int | None = None

            if raw[:1].isdigit():
                try:
                    candidate = int(raw[0])
                except ValueError:
                    candidate = -1

                if 1 <= candidate <= 9:
                    severity = candidate

            with self._lock:
                started = self._started_at

                if started is None:
                    continue

                self._marks.append(
                    Mark(now - started, severity, raw)
                )

    def marks(self) -> list[Mark]:
        with self._lock:
            return list(self._marks)

    def count(self) -> int:
        with self._lock:
            return len(self._marks)


class Report:
    """A manual-probe report in the established `tools/` convention.

    Header order and wording match the existing probes so downstream
    substring checks keep working:

        <title>
        Generated: <iso8601>
        Classification: <classification>
        Production files modified by probe: NONE
        Network addresses collected/logged: NONE
    """

    def __init__(
        self,
        title: str,
        *,
        modified_production_files: str = "NONE",
        network_addresses: str = "NONE",
    ) -> None:
        self.title = title
        self.modified_production_files = modified_production_files
        self.network_addresses = network_addresses
        self._lines: list[str] = []

    def line(self, text: str = "") -> "Report":
        self._lines.append(text)
        return self

    def lines(self, texts: list[str]) -> "Report":
        self._lines.extend(texts)
        return self

    def section(self, name: str) -> "Report":
        if self._lines and self._lines[-1] != "":
            self._lines.append("")

        self._lines.append(f"=== {name} ===")
        return self

    def field(self, key: str, value: Any) -> "Report":
        self._lines.append(f"{key}: {value}")
        return self

    def table(
        self,
        headers: list[str],
        rows: list[list[Any]],
        *,
        align_right: set[int] | None = None,
    ) -> "Report":
        """Fixed-width table. Plain text, no markdown — these reports are
        read in a terminal and grepped, not rendered."""
        right = align_right or set()
        cells = [[str(h) for h in headers]] + [
            [str(c) for c in row] for row in rows
        ]
        widths = [
            max(len(row[i]) for row in cells)
            for i in range(len(headers))
        ]

        for index, row in enumerate(cells):
            parts = []

            for i, cell in enumerate(row):
                parts.append(
                    cell.rjust(widths[i])
                    if i in right
                    else cell.ljust(widths[i])
                )

            self._lines.append("  " + "  ".join(parts).rstrip())

            if index == 0:
                self._lines.append(
                    "  " + "  ".join("-" * w for w in widths)
                )

        return self

    def render(self, classification: str) -> str:
        header = [
            self.title,
            f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
            f"Classification: {classification}",
            "Production files modified by probe: "
            + self.modified_production_files,
            "Network addresses collected/logged: "
            + self.network_addresses,
        ]
        return "\n".join(header + self._lines) + "\n"

    def write(
        self,
        path: Path,
        classification: str,
        *,
        printer: Callable[[str], None] = print,
    ) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.render(classification),
            encoding="utf-8",
        )
        printer(classification)
        printer(f"Log: {path}")
        return path
