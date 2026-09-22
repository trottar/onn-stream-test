#!/usr/bin/env python3
"""Redact the H2-PREP raw inventory before any of it reaches a memory file.

The raw output carries four things the project's privacy rule keeps out of
`docs/memory/`:

  * the monitor's **EDID hex block**, which encodes its serial number in the
    0xff descriptor -- the vendor and model string are kept, the serial is
    not, so the block is replaced wholesale and the model re-stated by hand;
  * the **root filesystem UUID** from /proc/cmdline;
  * **IPv4/IPv6 addresses and MACs** from `ss`, `adb devices` and anywhere
    else, replaced by stable per-run labels;
  * the **adb device serial**.

Stdin to stdout. `--check` exits non-zero if anything still matches, so the
redactor can be run twice and the second run proves the first.
"""

from __future__ import annotations

import re
import sys


# The EDID is printed by `xrandr --verbose` as indented 32-hex-digit lines.
EDID_LINE = re.compile(r"^\s+[0-9a-f]{32}\s*$")

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # root=UUID=... and any bare UUID
    (re.compile(r"\bUUID=[0-9a-fA-F-]{36}\b"), "UUID=<root-uuid>"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<uuid>"),
    # MAC addresses
    (re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"), "<mac>"),
    # IPv4, but not a bare version number: require four octets
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ipv4>"),
    # IPv6: `::` or four or more colons, never a bare HH:MM:SS timestamp
    (re.compile(r"\b(?=[0-9a-fA-F:]*::|"
                r"(?:[0-9a-fA-F]{1,4}:){4,})[0-9a-fA-F:]{4,}\b"), "<ipv6>"),
    # adb device serials: a long alphanumeric token before a device state
    (re.compile(r"^\S{8,}\t(device|offline|unauthorized)\b", re.M),
     r"<onn>\t\1"),
]


def redact(text: str) -> str:
    out: list[str] = []
    dropped = 0

    for line in text.splitlines():
        if EDID_LINE.match(line):
            dropped += 1
            continue

        if dropped:
            out.append(
                f"\t\t<EDID hex block: {dropped} lines removed; it carries "
                "the panel serial. Vendor/model recorded by hand.>"
            )
            dropped = 0

        for pattern, replacement in PATTERNS:
            line = pattern.sub(replacement, line)

        out.append(line)

    if dropped:
        out.append(f"\t\t<EDID hex block: {dropped} lines removed>")

    return "\n".join(out) + "\n"


def main() -> int:
    raw = sys.stdin.read()

    if "--check" in sys.argv[1:]:
        bad: list[str] = []

        for number, line in enumerate(raw.splitlines(), 1):
            if EDID_LINE.match(line):
                bad.append(f"{number}: EDID hex line")
                continue

            for pattern, _ in PATTERNS:
                if pattern.search(line):
                    bad.append(f"{number}: {pattern.pattern[:40]}")

        for item in bad:
            print(item, file=sys.stderr)

        print(f"{len(bad)} residual matches", file=sys.stderr)
        return 1 if bad else 0

    sys.stdout.write(redact(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
