#!/usr/bin/env python3
"""Nonblocking presence helpers for configured local removable storage."""

from __future__ import annotations

import os

from pathlib import Path
from typing import Optional


# PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1

def lexical_absolute_path(
    value: Path | str,
) -> Path:
    """Normalize an absolute path without dereferencing the filesystem."""
    return Path(
        os.path.abspath(
            os.path.expanduser(
                str(value)
            )
        )
    )


def _decode_fstab_field(
    value: str,
) -> str:
    return (
        value.replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\134", "\\")
    )


def configured_local_backing_present(
    path: Path,
) -> Optional[bool]:
    """Return local device presence without touching the configured mount path.

    True/False means a recognized local-device systemd automount mapping was
    found in /etc/fstab. None means the caller should use its normal backend
    behavior. Raw device identifiers are never logged here.
    """
    target = os.path.normpath(
        os.path.abspath(
            str(path)
        )
    )

    try:
        text = Path(
            "/etc/fstab"
        ).read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None

    candidates: list[tuple[int, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
        ):
            continue

        fields = line.split()

        if len(fields) < 4:
            continue

        source = _decode_fstab_field(
            fields[0]
        )
        mountpoint = os.path.normpath(
            _decode_fstab_field(
                fields[1]
            )
        )
        options = set(
            fields[3].split(",")
        )

        if (
            not mountpoint.startswith("/")
            or "x-systemd.automount" not in options
        ):
            continue

        try:
            if os.path.commonpath(
                [target, mountpoint]
            ) != mountpoint:
                continue
        except ValueError:
            continue

        candidates.append(
            (len(mountpoint), source)
        )

    if not candidates:
        return None

    _, source = max(candidates)

    device_path: Optional[Path]

    if source.startswith("UUID="):
        device_path = (
            Path("/dev/disk/by-uuid")
            / source[5:]
        )
    elif source.startswith("LABEL="):
        device_path = (
            Path("/dev/disk/by-label")
            / source[6:]
        )
    elif source.startswith("PARTUUID="):
        device_path = (
            Path("/dev/disk/by-partuuid")
            / source[9:]
        )
    elif source.startswith("/dev/"):
        device_path = Path(source)
    else:
        return None

    try:
        return device_path.exists()
    except OSError:
        return False
