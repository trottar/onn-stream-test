#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

EXPECTED_HEAD = "7c029de7ff7d569bce07d26c23f0bcfbb1147e8d"
MANAGED_BEGIN = "# BEGIN PRIVYHUB D096 VOD STORAGE"
MANAGED_END = "# END PRIVYHUB D096 VOD STORAGE"
MOUNTPOINT = Path("/mnt/privyhub-media")
OUT_REL = Path("logs/d097_vod_appliance_mode_probe.txt")


def run(
    cmd: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def managed_entry(
    text: str,
) -> str:
    begin = text.find(
        MANAGED_BEGIN
    )
    end = text.find(
        MANAGED_END
    )

    if begin < 0 or end < 0:
        return ""

    lines = [
        line
        for line in text[
            begin:end
        ].splitlines()
        if (
            line.strip()
            and not line.lstrip().startswith(
                "#"
            )
        )
    ]

    return (
        lines[0]
        if len(lines) == 1
        else ""
    )


def is_read_only(
    path: Path,
) -> bool:
    return bool(
        os.statvfs(
            path
        ).f_flag
        & os.ST_RDONLY
    )


def automount_unit(
) -> str:
    return run(
        [
            "systemd-escape",
            "--path",
            "--suffix=automount",
            str(
                MOUNTPOINT
            ),
        ]
    ).stdout.strip()


def self_test() -> int:
    sample = (
        MANAGED_BEGIN
        + "\n"
        + "UUID=X /mnt/privyhub-media exfat "
        + "ro,nofail,x-systemd.automount 0 0\n"
        + MANAGED_END
        + "\n"
    )

    entry = managed_entry(
        sample
    )

    assert entry

    options = (
        entry.split()[3].split(
            ","
        )
    )

    assert "ro" in options
    assert (
        "x-systemd.automount"
        in options
    )

    print(
        "SELF-TEST PASS"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--root",
        default="/home/privyhub/Projects/onn-stream-test",
    )

    ap.add_argument(
        "--self-test",
        action="store_true",
    )

    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(
        args.root
    ).resolve()

    out = (
        repo / OUT_REL
    )

    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    head = run(
        [
            "git",
            "-C",
            str(
                repo
            ),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()

    config_path = (
        repo
        / "data/storage.json"
    )

    fstab = Path(
        "/etc/fstab"
    )

    lines = [
        "PrivyHub D-097 VOD appliance-mode probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"Expected checkpoint: {EXPECTED_HEAD}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== CHECKPOINT ===",
        f"Git HEAD: {head}",
        f"Git HEAD expected: {head == EXPECTED_HEAD}",
        "",
        "=== CONFIGURATION ===",
        f"Storage config exists: {config_path.is_file()}",
    ]

    classification = (
        "D097_VOD_APPLIANCE_MODE_NOT_CONFIRMED"
    )

    if (
        head != EXPECTED_HEAD
        or not config_path.is_file()
        or not fstab.is_file()
    ):
        lines += [
            "",
            "=== RESULT ===",
            f"Classification: {classification}",
        ]
        out.write_text(
            "\n".join(
                lines
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            classification
        )
        print(
            "Log:",
            out,
        )
        return 1

    config = json.loads(
        config_path.read_text(
            encoding="utf-8"
        )
    )

    vod_root = Path(
        config.get(
            "vod_root",
            "",
        )
    )

    entry = managed_entry(
        fstab.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    options = (
        entry.split()[3].split(
            ","
        )
        if entry
        and len(
            entry.split()
        ) >= 4
        else []
    )

    auto_unit = automount_unit()

    active = run(
        [
            "systemctl",
            "is-active",
            auto_unit,
        ]
    ).stdout.strip()

    storage_present = (
        vod_root.is_dir()
    )

    read_only = (
        is_read_only(
            vod_root
        )
        if storage_present
        else None
    )

    lines += [
        f"Configured VOD root beneath managed mountpoint: {str(vod_root).startswith(str(MOUNTPOINT) + '/')}",
        f"Managed fstab entry present: {bool(entry)}",
        f"Read-only option present: {'ro' in options}",
        f"Automount option present: {'x-systemd.automount' in options}",
        f"nofail option present: {'nofail' in options}",
        f"Automount active: {active == 'active'}",
        "",
        "=== CURRENT STORAGE ===",
        f"Storage physically available: {storage_present}",
        f"Filesystem read-only: {read_only}",
    ]

    confirmed = (
        bool(
            entry
        )
        and "ro" in options
        and "x-systemd.automount"
        in options
        and "nofail" in options
        and active == "active"
        and str(
            vod_root
        ).startswith(
            str(
                MOUNTPOINT
            )
            + "/"
        )
        and (
            read_only is True
            if storage_present
            else True
        )
    )

    if confirmed:
        classification = (
            "D097_VOD_APPLIANCE_MODE_CONFIRMED"
        )

    lines += [
        "",
        "=== RESULT ===",
        f"Classification: {classification}",
    ]

    out.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        classification
    )
    print(
        "Log:",
        out,
    )

    return (
        0
        if classification
        == "D097_VOD_APPLIANCE_MODE_CONFIRMED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
