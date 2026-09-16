#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import time
from pathlib import Path

EXPECTED_HEAD = "7c029de7ff7d569bce07d26c23f0bcfbb1147e8d"
MANAGED_BEGIN = "# BEGIN PRIVYHUB D096 VOD STORAGE"
MANAGED_END = "# END PRIVYHUB D096 VOD STORAGE"
DEFAULT_MOUNTPOINT = Path("/mnt/privyhub-media")
CONFIG_REL = Path("data/storage.json")


def run(
    cmd: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if check and p.returncode != 0:
        raise RuntimeError(
            "$ "
            + " ".join(cmd)
            + "\n"
            + p.stdout
        )

    return p


def git_head(
    repo: Path,
) -> str:
    return run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()


def companion_running(
) -> bool:
    p = run(
        [
            "pgrep",
            "-f",
            r"[p]ython.*companion/(privyhub_service|range_server)\.py",
        ],
        check=False,
    )

    return (
        p.returncode == 0
        and bool(
            p.stdout.strip()
        )
    )


def automount_unit(
    mountpoint: Path,
) -> str:
    return run(
        [
            "systemd-escape",
            "--path",
            "--suffix=automount",
            str(
                mountpoint
            ),
        ]
    ).stdout.strip()


def find_managed_entry(
    text: str,
) -> tuple[int, int, str]:
    begin = text.find(
        MANAGED_BEGIN
    )

    end_marker = text.find(
        MANAGED_END
    )

    if begin < 0 or end_marker < 0:
        raise RuntimeError(
            "PrivyHub managed fstab block not found"
        )

    if end_marker < begin:
        raise RuntimeError(
            "PrivyHub managed fstab block is malformed"
        )

    end = (
        end_marker
        + len(
            MANAGED_END
        )
    )

    block = text[
        begin:end
    ]

    lines = [
        line
        for line in block.splitlines()
        if (
            line.strip()
            and not line.lstrip().startswith(
                "#"
            )
        )
    ]

    if len(lines) != 1:
        raise RuntimeError(
            "PrivyHub managed fstab block must contain exactly one entry"
        )

    return (
        begin,
        end,
        lines[0],
    )


def read_only_entry(
    entry: str,
) -> str:
    fields = entry.split()

    if len(fields) < 4:
        raise RuntimeError(
            "PrivyHub fstab entry is malformed"
        )

    options = [
        item
        for item in fields[3].split(",")
        if item
    ]

    options = [
        item
        for item in options
        if item != "rw"
    ]

    if "ro" not in options:
        options.insert(
            0,
            "ro",
        )

    fields[3] = ",".join(
        options
    )

    return "\t".join(
        fields
    )


def rewrite_managed_entry(
    text: str,
) -> str:
    begin, end, entry = (
        find_managed_entry(
            text
        )
    )

    updated_entry = (
        read_only_entry(
            entry
        )
    )

    block = text[
        begin:end
    ]

    new_block_lines: list[str] = []

    for line in block.splitlines():
        if (
            line.strip()
            and not line.lstrip().startswith(
                "#"
            )
        ):
            new_block_lines.append(
                updated_entry
            )
        else:
            new_block_lines.append(
                line
            )

    return (
        text[:begin]
        + "\n".join(
            new_block_lines
        )
        + text[end:]
    )


def is_read_only(
    path: Path,
) -> bool:
    flags = os.statvfs(
        path
    ).f_flag

    return bool(
        flags & os.ST_RDONLY
    )


def write_atomic(
    path: Path,
    data: bytes,
    mode: int,
) -> None:
    temp = path.with_name(
        path.name
        + ".privyhub.tmp"
    )

    temp.write_bytes(
        data
    )

    os.chmod(
        temp,
        mode,
    )

    os.replace(
        temp,
        path,
    )


def self_test() -> int:
    before = (
        "# test\n"
        + MANAGED_BEGIN
        + "\n"
        + "UUID=TEST\t/mnt/privyhub-media\texfat\t"
        + "nofail,x-systemd.automount,nodev\t0\t0\n"
        + MANAGED_END
        + "\n"
    )

    after = rewrite_managed_entry(
        before
    )

    _, _, entry = (
        find_managed_entry(
            after
        )
    )

    options = entry.split()[3].split(
        ","
    )

    assert "ro" in options
    assert "rw" not in options
    assert "x-systemd.automount" in options

    # Idempotent.
    assert (
        rewrite_managed_entry(
            after
        )
        == after
    )

    print(
        "SELF-TEST PASS"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--repo-root",
        default="/home/privyhub/Projects/onn-stream-test",
    )

    ap.add_argument(
        "--mountpoint",
        default=str(
            DEFAULT_MOUNTPOINT
        ),
    )

    ap.add_argument(
        "--self-test",
        action="store_true",
    )

    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if os.geteuid() != 0:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Run this appliance-mode configurator with sudo."
        )
        return 20

    repo = Path(
        args.repo_root
    ).resolve()

    mountpoint = Path(
        args.mountpoint
    )

    if not mountpoint.is_absolute():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Mountpoint must be absolute."
        )
        return 21

    if git_head(
        repo
    ) != EXPECTED_HEAD:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Git HEAD is not the synchronized D-093R2 checkpoint."
        )
        return 22

    if companion_running():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Stop PrivyHub companion/range-server processes first."
        )
        return 23

    config_path = (
        repo / CONFIG_REL
    )

    if not config_path.is_file():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "D-096 storage config is missing."
        )
        return 24

    try:
        config = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "D-096 storage config is unreadable."
        )
        return 25

    raw_vod_root = config.get(
        "vod_root"
    )

    if (
        not isinstance(
            raw_vod_root,
            str,
        )
        or not raw_vod_root
    ):
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Configured VOD root is invalid."
        )
        return 26

    vod_root = Path(
        raw_vod_root
    )

    try:
        vod_root.relative_to(
            mountpoint
        )
    except ValueError:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Configured VOD root is not beneath the managed mountpoint."
        )
        return 27

    fstab = Path(
        "/etc/fstab"
    )

    if not fstab.is_file():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "/etc/fstab not found."
        )
        return 28

    before = fstab.read_bytes()
    mode = stat.S_IMODE(
        fstab.stat().st_mode
    )

    try:
        before_text = before.decode(
            "utf-8"
        )
        after_text = (
            rewrite_managed_entry(
                before_text
            )
        )
    except Exception as exc:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            str(
                exc
            )
        )
        return 29

    stamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = (
        repo
        / "archive/patch_backups"
        / (
            "PrivyHub_D097_appliance_mode_"
            + stamp
        )
    )

    backup.mkdir(
        parents=True,
        exist_ok=False,
    )

    (
        backup / "fstab.before"
    ).write_bytes(
        before
    )

    receipt = {
        "patch": (
            "PrivyHub_D097_appliance_mode"
        ),
        "status": "STARTED",
        "durable_memory_updated": True,
        "mountpoint": str(
            mountpoint
        ),
        "vod_root": str(
            vod_root
        ),
        "normal_mode": "read_only",
        "automount_policy": (
            "permanently_active"
        ),
    }

    (
        backup / "receipt.json"
    ).write_text(
        json.dumps(
            receipt,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    changed_fstab = False

    try:
        if after_text != before_text:
            write_atomic(
                fstab,
                after_text.encode(
                    "utf-8"
                ),
                mode,
            )

            changed_fstab = True

        run(
            [
                "systemctl",
                "daemon-reload",
            ]
        )

        auto_unit = automount_unit(
            mountpoint
        )

        run(
            [
                "systemctl",
                "start",
                auto_unit,
            ]
        )

        # Access the configured VOD root so automount performs the actual
        # filesystem mount using the updated read-only fstab options.
        # If it is already mounted read-write, remount it read-only first.
        if vod_root.exists():
            if not is_read_only(
                vod_root
            ):
                run(
                    [
                        "mount",
                        "-o",
                        "remount,ro",
                        str(
                            mountpoint
                        ),
                    ]
                )
        else:
            # Trigger an on-demand mount if storage is physically present.
            try:
                list(
                    mountpoint.iterdir()
                )
            except OSError:
                pass

        if vod_root.exists():
            if not is_read_only(
                vod_root
            ):
                raise RuntimeError(
                    "Configured VOD filesystem did not become read-only."
                )

        active = run(
            [
                "systemctl",
                "is-active",
                auto_unit,
            ],
            check=False,
        ).stdout.strip()

        if active != "active":
            raise RuntimeError(
                "PrivyHub automount unit is not active."
            )

        _, _, installed_entry = (
            find_managed_entry(
                fstab.read_text(
                    encoding="utf-8"
                )
            )
        )

        installed_options = (
            installed_entry.split()[3].split(
                ","
            )
        )

        if "ro" not in installed_options:
            raise RuntimeError(
                "Managed fstab entry is not read-only."
            )

        if (
            "x-systemd.automount"
            not in installed_options
        ):
            raise RuntimeError(
                "Managed fstab entry lost x-systemd.automount."
            )

        receipt["status"] = (
            "INSTALLED SUCCESSFULLY"
        )
        receipt[
            "storage_present_during_validation"
        ] = vod_root.exists()
        receipt[
            "read_only_validated"
        ] = (
            is_read_only(
                vod_root
            )
            if vod_root.exists()
            else None
        )
        receipt[
            "automount_active"
        ] = True

        (
            backup / "receipt.json"
        ).write_text(
            json.dumps(
                receipt,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            "INSTALLED SUCCESSFULLY"
        )
        print(
            "D-097 VOD appliance mode: CONFIGURED"
        )
        print(
            "Normal VOD mode: READ-ONLY"
        )
        print(
            "Automount policy: PERMANENTLY ACTIVE"
        )
        print(
            "Desktop/file-manager interaction required for hotplug: NO"
        )

        if vod_root.exists():
            print(
                "Current VOD filesystem read-only validation: PASS"
            )
        else:
            print(
                "Current VOD filesystem absent; read-only mode will apply "
                "on next automount."
            )

        print(
            f"Backup/receipt: {backup}"
        )
        return 0

    except Exception as exc:
        rollback_errors: list[str] = []

        try:
            if changed_fstab:
                write_atomic(
                    fstab,
                    before,
                    mode,
                )

            run(
                [
                    "systemctl",
                    "daemon-reload",
                ],
                check=False,
            )

            auto_unit = automount_unit(
                mountpoint
            )

            run(
                [
                    "systemctl",
                    "start",
                    auto_unit,
                ],
                check=False,
            )

            # If the old entry was normal read-write and storage is mounted,
            # restore that runtime access mode as closely as practical.
            _, _, old_entry = (
                find_managed_entry(
                    before_text
                )
            )

            old_options = (
                old_entry.split()[3].split(
                    ","
                )
            )

            if (
                "ro" not in old_options
                and vod_root.exists()
            ):
                run(
                    [
                        "mount",
                        "-o",
                        "remount,rw",
                        str(
                            mountpoint
                        ),
                    ],
                    check=False,
                )

        except Exception as rex:
            rollback_errors.append(
                str(
                    rex
                )
            )

        exact = (
            fstab.read_bytes()
            == before
        )

        receipt["status"] = (
            "ROLLED BACK"
            if (
                exact
                and not rollback_errors
            )
            else "ROLLBACK INCOMPLETE"
        )
        receipt["error"] = str(
            exc
        )
        receipt[
            "rollback_errors"
        ] = rollback_errors

        (
            backup / "receipt.json"
        ).write_text(
            json.dumps(
                receipt,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            receipt["status"]
        )
        print(
            str(
                exc
            )
        )

        for item in rollback_errors:
            print(
                item
            )

        return (
            30
            if receipt["status"]
            == "ROLLED BACK"
            else 31
        )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
