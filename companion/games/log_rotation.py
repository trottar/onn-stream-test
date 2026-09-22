"""D-BASE-R4 item 4: bounded append-only diagnostic logs.

`native_stream_heartbeat.log` and `native_stream_recovery.log` are written
one JSON line at a time for the life of the host and nothing trimmed them.
This rotates them in place.

The rotation happens **before** the line is appended, never after, so the
line being written cannot land in a file that is about to be renamed out
from under it: either it goes into the tail of the old file (when that file
is still under the limit) or into the first line of the fresh one.

Rotated files go to a sibling archive directory rather than sitting next to
the live log, so that `tools/diagnostic_retention.py` can bound them with a
directory family without putting unrelated logs — or the decoder session
JSONs — in the same family's reach.
"""

from __future__ import annotations

from pathlib import Path


ARCHIVE_DIRNAME = "stream_log_archive"


def archive_dir(
    log_path: Path,
) -> Path:
    return Path(log_path).parent / ARCHIVE_DIRNAME


def rotated_path(
    log_path: Path,
    index: int,
) -> Path:
    return (
        archive_dir(log_path)
        / f"{Path(log_path).name}.{index}"
    )


def rotate_if_needed(
    log_path: Path,
    *,
    max_bytes: int,
    keep: int,
) -> bool:
    """Roll `log` to `archive/log.1` when it has reached `max_bytes`.

    `log.1` is always the newest rotation; `log.<keep>` the oldest, and
    anything beyond `keep` is removed. Returns True when a rotation
    happened. Any filesystem error is swallowed: a log that cannot be
    rotated must still be writable.
    """

    path = Path(log_path)

    try:
        size = path.stat().st_size
    except OSError:
        return False

    if size < int(max_bytes):
        return False

    keep = max(1, int(keep))
    target_dir = archive_dir(path)

    try:
        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        oldest = rotated_path(path, keep)

        try:
            oldest.unlink()
        except FileNotFoundError:
            pass

        for index in range(keep - 1, 0, -1):
            source = rotated_path(path, index)

            if source.exists():
                source.replace(
                    rotated_path(path, index + 1)
                )

        path.replace(
            rotated_path(path, 1)
        )
    except OSError:
        return False

    return True


def append_line(
    log_path: Path,
    line: str,
    *,
    max_bytes: int,
    keep: int,
) -> bool:
    """Append one line, rotating first if the log has reached its limit."""

    path = Path(log_path)
    rotated = rotate_if_needed(
        path,
        max_bytes=max_bytes,
        keep=keep,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            line
            if line.endswith("\n")
            else line + "\n"
        )

    return rotated
