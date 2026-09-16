#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import stat
import subprocess
import time
from pathlib import Path
from typing import Any

EXPECTED_HEAD = "7c029de7ff7d569bce07d26c23f0bcfbb1147e8d"
SOURCE_MARKER = "PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE_V1"
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def uuid_tag(uuid: str) -> str:
    return hashlib.sha256(
        uuid.encode("utf-8")
    ).hexdigest()[:12]


def git_head(repo: Path) -> str:
    return run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()


def flatten_block_devices(
    devices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def walk(
        item: dict[str, Any],
    ) -> None:
        out.append(
            item
        )

        children = item.get(
            "children"
        )

        if isinstance(
            children,
            list,
        ):
            for child in children:
                if isinstance(
                    child,
                    dict,
                ):
                    walk(
                        child
                    )

    for item in devices:
        if isinstance(
            item,
            dict,
        ):
            walk(
                item
            )

    return out


def load_lsblk(
) -> list[dict[str, Any]]:
    p = run(
        [
            "lsblk",
            "-J",
            "-p",
            "-o",
            "NAME,TYPE,MAJ:MIN,FSTYPE,MOUNTPOINTS",
        ]
    )

    obj = json.loads(
        p.stdout
    )

    devices = obj.get(
        "blockdevices",
        [],
    )

    if not isinstance(
        devices,
        list,
    ):
        raise RuntimeError(
            "lsblk returned an invalid device list"
        )

    return devices


def backing_block_device(
    path: Path,
) -> dict[str, Any]:
    # D-096R1: do not trust findmnt SOURCE here.  systemd automounts may
    # report the synthetic source "systemd-1".  stat() gives the device
    # number of the filesystem that actually backs the accessed file.
    st = path.stat()

    device_id = (
        f"{os.major(st.st_dev)}:"
        f"{os.minor(st.st_dev)}"
    )

    for item in flatten_block_devices(
        load_lsblk()
    ):
        if (
            str(
                item.get(
                    "maj:min"
                )
                or ""
            )
            == device_id
        ):
            return item

    raise RuntimeError(
        "Could not map VOD filesystem device number "
        f"{device_id} to lsblk"
    )


def current_mountpoint(
    device: dict[str, Any],
    path: Path,
) -> Path:
    raw = device.get(
        "mountpoints"
    )

    if not isinstance(
        raw,
        list,
    ):
        raw = []

    candidates: list[Path] = []

    for item in raw:
        if not item:
            continue

        mountpoint = Path(
            str(item)
        )

        try:
            path.relative_to(
                mountpoint
            )
        except ValueError:
            continue

        candidates.append(
            mountpoint
        )

    if not candidates:
        # Fall back to findmnt constrained to the real block device rather
        # than asking findmnt which source owns the path.
        source = str(
            device.get(
                "name"
            )
            or ""
        )

        if source:
            p = run(
                [
                    "findmnt",
                    "-rn",
                    "-S",
                    source,
                    "-o",
                    "TARGET",
                ],
                check=False,
            )

            for raw_target in p.stdout.splitlines():
                target = raw_target.strip()

                if not target:
                    continue

                mountpoint = Path(
                    target
                )

                try:
                    path.relative_to(
                        mountpoint
                    )
                except ValueError:
                    continue

                candidates.append(
                    mountpoint
                )

    if not candidates:
        raise RuntimeError(
            "Could not identify the current mountpoint for the "
            "backing VOD block device"
        )

    # Deepest matching mountpoint is the filesystem actually containing path.
    return max(
        candidates,
        key=lambda item: len(
            item.parts
        ),
    )


def filesystem_uuid(
    source: str,
) -> str:
    p = run(
        [
            "blkid",
            "-s",
            "UUID",
            "-o",
            "value",
            source,
        ]
    )

    uuid = p.stdout.strip()

    if not uuid:
        raise RuntimeError(
            "Backing filesystem has no UUID"
        )

    return uuid


def derive_vod_relative_root(
    *,
    repo: Path,
    symlink: Path,
    resolved_target: Path,
    current_mount: Path,
) -> Path:
    media_root = (
        repo / "media"
    ).resolve(
        strict=False
    )

    logical = symlink.relative_to(
        media_root
    )

    if (
        not logical.parts
        or logical.parts[0] != "vod"
    ):
        raise RuntimeError(
            "Selected symlink is not beneath logical media/vod"
        )

    target_relative = (
        resolved_target.relative_to(
            current_mount
        )
    )

    suffix = logical.parts[1:]

    if suffix:
        if (
            len(target_relative.parts)
            < len(suffix)
            or tuple(
                target_relative.parts[
                    -len(suffix):
                ]
            )
            != tuple(suffix)
        ):
            raise RuntimeError(
                "External symlink target does not preserve the "
                "logical VOD suffix"
            )

        root_parts = (
            target_relative.parts[
                :-len(suffix)
            ]
        )
    else:
        root_parts = (
            target_relative.parts
        )

    return Path(
        *root_parts
    )


def managed_fstab_block(
    *,
    uuid: str,
    mountpoint: Path,
    fstype: str,
    uid: int,
    gid: int,
) -> str:
    base = [
        "ro",
        "nofail",
        "x-systemd.automount",
        "x-systemd.device-timeout=3s",
        "x-gvfs-hide",
        "nosuid",
        "nodev",
        "noexec",
    ]

    if fstype.casefold() in {
        "exfat",
        "vfat",
        "ntfs",
        "ntfs3",
        "fuseblk",
    }:
        base.extend(
            [
                f"uid={uid}",
                f"gid={gid}",
                "fmask=0022",
                "dmask=0022",
            ]
        )

    options = ",".join(
        base
    )

    return (
        f"{MANAGED_BEGIN}\n"
        f"UUID={uuid}\t{mountpoint}\t{fstype}\t"
        f"{options}\t0\t0\n"
        f"{MANAGED_END}\n"
    )


def replace_managed_fstab_block(
    text: str,
    block: str,
) -> str:
    begin = text.find(
        MANAGED_BEGIN
    )

    end = text.find(
        MANAGED_END
    )

    if (begin < 0) != (end < 0):
        raise RuntimeError(
            "Existing PrivyHub fstab block is malformed"
        )

    if begin >= 0:
        end = (
            end
            + len(
                MANAGED_END
            )
        )

        if (
            end < len(text)
            and text[
                end:end + 1
            ]
            == "\n"
        ):
            end += 1

        text = (
            text[:begin]
            + text[end:]
        )

    return (
        text.rstrip()
        + "\n\n"
        + block
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


def companion_running() -> bool:
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
    )


def current_user_ids(
) -> tuple[int, int, str]:
    uid = int(
        os.environ.get(
            "SUDO_UID",
            os.getuid(),
        )
    )

    gid = int(
        os.environ.get(
            "SUDO_GID",
            os.getgid(),
        )
    )

    user = pwd.getpwuid(
        uid
    ).pw_name

    return (
        uid,
        gid,
        user,
    )


def start_automount(
    mountpoint: Path,
) -> None:
    unit = run(
        [
            "systemd-escape",
            "--path",
            "--suffix=automount",
            str(
                mountpoint
            ),
        ]
    ).stdout.strip()

    run(
        [
            "systemctl",
            "daemon-reload",
        ]
    )

    run(
        [
            "systemctl",
            "restart",
            unit,
        ]
    )


def trigger_mount(
    mountpoint: Path,
) -> None:
    list(
        mountpoint.iterdir()
    )


def same_uuid_at_mount(
    mountpoint: Path,
    expected_uuid: str,
) -> bool:
    device = backing_block_device(
        mountpoint
    )

    source = str(
        device.get(
            "name"
        )
        or ""
    )

    if not source.startswith(
        "/dev/"
    ):
        return False

    return (
        filesystem_uuid(
            source
        )
        == expected_uuid
    )


def self_test() -> int:
    fake_devices = [
        {
            "name": "/dev/sdb",
            "type": "disk",
            "maj:min": "8:16",
            "children": [
                {
                    "name": "/dev/sdb1",
                    "type": "part",
                    "maj:min": "8:17",
                    "fstype": "exfat",
                    "mountpoints": [
                        "/media/user/disk"
                    ],
                }
            ],
        }
    ]

    flat = flatten_block_devices(
        fake_devices
    )

    assert len(
        flat
    ) == 2

    device = next(
        item
        for item in flat
        if item.get(
            "maj:min"
        )
        == "8:17"
    )

    assert (
        current_mountpoint(
            device,
            Path(
                "/media/user/disk/library/media/vod/movies"
            ),
        )
        == Path(
            "/media/user/disk"
        )
    )

    fake_repo = Path(
        "/srv/privyhub"
    )

    symlink = (
        fake_repo
        / "media/vod/movies"
    )

    target = Path(
        "/media/user/disk/library/media/vod/movies"
    )

    rel = derive_vod_relative_root(
        repo=fake_repo,
        symlink=symlink,
        resolved_target=target,
        current_mount=Path(
            "/media/user/disk"
        ),
    )

    assert (
        rel.as_posix()
        == "library/media/vod"
    )

    block = managed_fstab_block(
        uuid="TEST-UUID",
        mountpoint=DEFAULT_MOUNTPOINT,
        fstype="exfat",
        uid=1000,
        gid=1000,
    )

    assert (
        "x-systemd.automount"
        in block
    )

    first = replace_managed_fstab_block(
        "# test\n",
        block,
    )

    second = replace_managed_fstab_block(
        first,
        block,
    )

    assert (
        first == second
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
        "--symlink",
        default="media/vod/movies",
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
            "Run this storage configurator with sudo."
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
            "Git HEAD is not the D-093R2 synchronized checkpoint."
        )
        return 22

    source_text = (
        repo
        / "companion/privyhub_service.py"
    ).read_text(
        encoding="utf-8"
    )

    if SOURCE_MARKER not in source_text:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "D-096 production patch is not installed."
        )
        return 23

    if companion_running():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Stop PrivyHub companion/range-server processes first."
        )
        return 24

    uid, gid, user = (
        current_user_ids()
    )

    config_path = (
        repo / CONFIG_REL
    )

    fstab_path = Path(
        "/etc/fstab"
    )

    if not fstab_path.is_file():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "/etc/fstab not found."
        )
        return 25

    if config_path.is_file():
        try:
            cfg = json.loads(
                config_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            cfg = {}

        configured_root = cfg.get(
            "vod_root"
        )

        fstab_text = (
            fstab_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        if (
            isinstance(
                configured_root,
                str,
            )
            and configured_root
            and MANAGED_BEGIN
            in fstab_text
            and Path(
                configured_root
            ).is_dir()
        ):
            print(
                "INSTALLED SUCCESSFULLY"
            )
            print(
                "D-096 storage boundary is already configured."
            )
            print(
                f"Stable mountpoint: {mountpoint}"
            )
            print(
                "Raw filesystem UUID logged: NO"
            )
            return 0

        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "data/storage.json already exists but is not a valid "
            "D-096 configured state."
        )
        return 26

    symlink = (
        repo / args.symlink
    )

    if not symlink.is_symlink():
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            f"Expected existing VOD symlink: {args.symlink}"
        )
        return 27

    raw_link_target = os.readlink(
        symlink
    )

    try:
        resolved_target = (
            symlink.resolve(
                strict=True
            )
        )
    except FileNotFoundError:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Current VOD symlink target is unavailable. "
            "Mount the external disk first."
        )
        return 28

    device = backing_block_device(
        resolved_target
    )

    source = str(
        device.get(
            "name"
        )
        or ""
    )

    fstype = str(
        device.get(
            "fstype"
        )
        or ""
    )

    if not source.startswith(
        "/dev/"
    ):
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Backing VOD filesystem is not a local block device."
        )
        return 29

    if not fstype:
        print(
            "FAILED BEFORE MODIFICATION"
        )
        print(
            "Backing VOD filesystem type is unavailable."
        )
        return 30

    current_mount = current_mountpoint(
        device,
        resolved_target,
    )

    uuid = filesystem_uuid(
        source
    )

    uuid_hash = uuid_tag(
        uuid
    )

    vod_relative_root = (
        derive_vod_relative_root(
            repo=repo,
            symlink=symlink,
            resolved_target=resolved_target,
            current_mount=current_mount,
        )
    )

    stable_vod_root = (
        mountpoint
        / vod_relative_root
    )

    fstab_before = (
        fstab_path.read_bytes()
    )

    fstab_mode = stat.S_IMODE(
        fstab_path.stat().st_mode
    )

    config_before = (
        config_path.read_bytes()
        if config_path.exists()
        else None
    )

    stamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = (
        repo
        / "archive/patch_backups"
        / (
            "PrivyHub_D096R1_storage_setup_"
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
        fstab_before
    )

    receipt: dict[str, Any] = {
        "patch": (
            "PrivyHub_D096R1_storage_setup"
        ),
        "status": "STARTED",
        "durable_memory_updated": True,
        "filesystem_uuid_hash": (
            uuid_hash
        ),
        "raw_filesystem_uuid_logged": False,
        "stable_mountpoint": str(
            mountpoint
        ),
        "storage_config": str(
            CONFIG_REL
        ),
        "pre_fstab_sha256": (
            sha256_bytes(
                fstab_before
            )
        ),
        "backing_device_discovery": (
            "stat_major_minor_to_lsblk"
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

    unmounted_original = False
    stable_mounted = False
    symlink_removed = False

    try:
        current_fstab = (
            fstab_before.decode(
                "utf-8"
            )
        )

        outside_managed = current_fstab

        if (
            MANAGED_BEGIN
            in current_fstab
            and MANAGED_END
            in current_fstab
        ):
            begin = current_fstab.find(
                MANAGED_BEGIN
            )
            end = (
                current_fstab.find(
                    MANAGED_END
                )
                + len(
                    MANAGED_END
                )
            )
            outside_managed = (
                current_fstab[:begin]
                + current_fstab[end:]
            )

        if (
            f"UUID={uuid}"
            in outside_managed
        ):
            raise RuntimeError(
                "This filesystem UUID already has a non-PrivyHub "
                "/etc/fstab entry."
            )

        block = managed_fstab_block(
            uuid=uuid,
            mountpoint=mountpoint,
            fstype=fstype,
            uid=uid,
            gid=gid,
        )

        fstab_after_text = (
            replace_managed_fstab_block(
                current_fstab,
                block,
            )
        )

        mountpoint.mkdir(
            parents=True,
            exist_ok=True,
        )

        run(
            [
                "umount",
                str(
                    current_mount
                ),
            ]
        )

        unmounted_original = True

        still_mounted = run(
            [
                "findmnt",
                "-rn",
                "-S",
                source,
                "-o",
                "TARGET",
            ],
            check=False,
        )

        if still_mounted.stdout.strip():
            for target in (
                still_mounted.stdout.splitlines()
            ):
                run(
                    [
                        "umount",
                        target.strip(),
                    ]
                )

        write_atomic(
            fstab_path,
            fstab_after_text.encode(
                "utf-8"
            ),
            fstab_mode,
        )

        start_automount(
            mountpoint
        )

        trigger_mount(
            mountpoint
        )

        stable_mounted = True

        if not same_uuid_at_mount(
            mountpoint,
            uuid,
        ):
            raise RuntimeError(
                "Stable mount UUID validation failed."
            )

        if not stable_vod_root.is_dir():
            raise RuntimeError(
                "Derived stable VOD root is not a directory: "
                + str(
                    stable_vod_root
                )
            )

        config_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        config_payload = {
            "version": 1,
            "vod_root": str(
                stable_vod_root
            ),
        }

        config_path.write_text(
            json.dumps(
                config_payload,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        os.chown(
            config_path,
            uid,
            gid,
        )

        symlink.unlink()

        symlink_removed = True

        stored = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )

        if (
            stored.get(
                "vod_root"
            )
            != str(
                stable_vod_root
            )
        ):
            raise RuntimeError(
                "Stored VOD root validation failed."
            )

        if not stable_vod_root.is_dir():
            raise RuntimeError(
                "Stable VOD root disappeared during validation."
            )

        receipt["status"] = (
            "INSTALLED SUCCESSFULLY"
        )

        receipt[
            "post_fstab_sha256"
        ] = sha256_bytes(
            fstab_path.read_bytes()
        )

        receipt[
            "vod_root"
        ] = str(
            stable_vod_root
        )

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
            "D-096R1 deterministic VOD storage mount: CONFIGURED"
        )
        print(
            "Backing device discovery: stat major:minor -> lsblk"
        )
        print(
            "Filesystem UUID hash: "
            + uuid_hash
        )
        print(
            "Raw filesystem UUID logged: NO"
        )
        print(
            "Stable mountpoint: "
            + str(
                mountpoint
            )
        )
        print(
            "Configured VOD root: "
            + str(
                stable_vod_root
            )
        )
        print(
            "Desktop-path VOD symlink: REMOVED"
        )
        print(
            f"Backup/receipt: {backup}"
        )
        return 0

    except Exception as exc:
        rollback_errors: list[str] = []

        try:
            if symlink_removed:
                os.symlink(
                    raw_link_target,
                    symlink,
                )
        except Exception as rex:
            rollback_errors.append(
                "symlink: "
                + str(
                    rex
                )
            )

        try:
            if config_before is None:
                config_path.unlink(
                    missing_ok=True
                )
            else:
                config_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                config_path.write_bytes(
                    config_before
                )
                os.chown(
                    config_path,
                    uid,
                    gid,
                )
        except Exception as rex:
            rollback_errors.append(
                "storage config: "
                + str(
                    rex
                )
            )

        try:
            if stable_mounted:
                run(
                    [
                        "umount",
                        str(
                            mountpoint
                        ),
                    ],
                    check=False,
                )

            write_atomic(
                fstab_path,
                fstab_before,
                fstab_mode,
            )

            run(
                [
                    "systemctl",
                    "daemon-reload",
                ],
                check=False,
            )
        except Exception as rex:
            rollback_errors.append(
                "fstab: "
                + str(
                    rex
                )
            )

        try:
            if unmounted_original:
                current_mount.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                run(
                    [
                        "mount",
                        source,
                        str(
                            current_mount
                        ),
                    ],
                    check=False,
                )
        except Exception as rex:
            rollback_errors.append(
                "original mount: "
                + str(
                    rex
                )
            )

        exact_fstab = (
            fstab_path.read_bytes()
            == fstab_before
        )

        receipt["status"] = (
            "ROLLED BACK"
            if (
                exact_fstab
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
            31
            if receipt["status"]
            == "ROLLED BACK"
            else 32
        )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
