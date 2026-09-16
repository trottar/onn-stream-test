#!/usr/bin/env python3
"""
Small HTTP media server with single-range byte request support.

PrivyHub uses this instead of Python's basic SimpleHTTPServer because
Android Media3/ExoPlayer expects reliable HTTP Range behavior for VOD.

The default HTTP namespace is served from --root.  When --vod-root is
provided, the logical /vod/... namespace is served from that separate
physical directory.  This keeps generated live/HLS content on the
internal media root while allowing bulk VOD storage to live elsewhere.

Example:
    python range_server.py \
        --root ../media \
        --vod-root /mnt/privyhub-media/library/vod \
        --host 0.0.0.0 \
        --port 8000
"""

from __future__ import annotations

import argparse
import os
import re

from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Optional
from urllib.parse import unquote, urlsplit

from storage_presence import (
    configured_local_backing_present,
    lexical_absolute_path,
)


RANGE_RE = re.compile(
    r"^bytes=(\d*)-(\d*)$"
)


class RangeRequestHandler(SimpleHTTPRequestHandler):
    server_version = "PrivyHubMedia/0.3"

    def __init__(
        self,
        *args,
        directory: str,
        vod_directory: Optional[str] = None,
        **kwargs,
    ) -> None:
        self._range: Optional[tuple[int, int]] = None
        self._vod_directory = (
            lexical_absolute_path(
                vod_directory
            )
            if vod_directory
            else None
        )

        super().__init__(
            *args,
            directory=directory,
            **kwargs,
        )

    @staticmethod
    def _vod_relative_parts(
        request_path: str,
    ) -> Optional[tuple[str, ...]]:
        decoded = unquote(
            urlsplit(request_path).path
        ).replace("\\", "/")

        parts = tuple(
            part
            for part in PurePosixPath(decoded).parts
            if part not in {"/", "", "."}
        )

        if not parts or parts[0] != "vod":
            return None

        relative_parts = parts[1:]

        if ".." in relative_parts:
            raise ValueError(
                "Unsafe VOD request path"
            )

        return relative_parts

    def translate_path(
        self,
        path: str,
    ) -> str:
        if self._vod_directory is None:
            return super().translate_path(path)

        try:
            relative_parts = (
                self._vod_relative_parts(path)
            )
        except ValueError:
            return str(
                self._vod_directory
                / ".privyhub-invalid-request"
                / "__rejected__"
            )

        if relative_parts is None:
            return super().translate_path(path)

        return str(
            self._vod_directory.joinpath(
                *relative_parts
            )
        )

    def end_headers(self) -> None:
        self.send_header(
            "Accept-Ranges",
            "bytes",
        )

        super().end_headers()

    def send_head(self) -> Optional[BinaryIO]:
        try:
            vod_relative = (
                self._vod_relative_parts(
                    self.path
                )
            )
        except ValueError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "File not found",
            )
            return None

        if (
            vod_relative is not None
            and self._vod_directory is not None
            and configured_local_backing_present(
                self._vod_directory
            ) is False
        ):
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "File not found",
            )
            return None

        path = self.translate_path(self.path)

        if os.path.isdir(path):
            return super().send_head()

        try:
            file_handle = open(path, "rb")
        except OSError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "File not found",
            )
            return None

        try:
            file_size = os.fstat(
                file_handle.fileno()
            ).st_size

            content_type = self.guess_type(path)

            range_header = self.headers.get(
                "Range"
            )

            self._range = None

            if range_header:
                parsed_range = self._parse_range(
                    range_header,
                    file_size,
                )

                if parsed_range is None:
                    file_handle.close()

                    self.send_response(
                        HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE
                    )
                    self.send_header(
                        "Content-Range",
                        f"bytes */{file_size}",
                    )
                    self.send_header(
                        "Content-Length",
                        "0",
                    )
                    self.end_headers()

                    return None

                start, end = parsed_range
                self._range = (start, end)

                self.send_response(
                    HTTPStatus.PARTIAL_CONTENT
                )
                self.send_header(
                    "Content-Type",
                    content_type,
                )
                self.send_header(
                    "Content-Range",
                    f"bytes {start}-{end}/{file_size}",
                )
                self.send_header(
                    "Content-Length",
                    str(end - start + 1),
                )
                self.send_header(
                    "Last-Modified",
                    self.date_time_string(
                        os.fstat(
                            file_handle.fileno()
                        ).st_mtime
                    ),
                )
                self.end_headers()

                file_handle.seek(start)

                return file_handle

            self.send_response(
                HTTPStatus.OK
            )
            self.send_header(
                "Content-Type",
                content_type,
            )
            self.send_header(
                "Content-Length",
                str(file_size),
            )
            self.send_header(
                "Last-Modified",
                self.date_time_string(
                    os.fstat(
                        file_handle.fileno()
                    ).st_mtime
                ),
            )
            self.end_headers()

            return file_handle

        except Exception:
            file_handle.close()
            raise

    @staticmethod
    def _parse_range(
        header: str,
        file_size: int,
    ) -> Optional[tuple[int, int]]:
        match = RANGE_RE.fullmatch(
            header.strip()
        )

        if match is None:
            return None

        start_text, end_text = match.groups()

        if not start_text and not end_text:
            return None

        if not start_text:
            suffix_length = int(end_text)

            if suffix_length <= 0:
                return None

            if suffix_length >= file_size:
                return (0, file_size - 1)

            return (
                file_size - suffix_length,
                file_size - 1,
            )

        start = int(start_text)

        if start >= file_size:
            return None

        if end_text:
            end = int(end_text)

            if end < start:
                return None

            end = min(
                end,
                file_size - 1,
            )
        else:
            end = file_size - 1

        return (start, end)

    def copyfile(
        self,
        source: BinaryIO,
        outputfile,
    ) -> None:
        if self._range is None:
            return super().copyfile(
                source,
                outputfile,
            )

        start, end = self._range
        remaining = end - start + 1

        while remaining > 0:
            chunk = source.read(
                min(
                    64 * 1024,
                    remaining,
                )
            )

            if not chunk:
                break

            outputfile.write(chunk)
            remaining -= len(chunk)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "PrivyHub HTTP media server "
            "with byte-range support."
        )
    )

    parser.add_argument(
        "--root",
        required=True,
        help="Internal media directory to expose over HTTP.",
    )

    parser.add_argument(
        "--vod-root",
        default=None,
        help=(
            "Optional physical directory for the logical /vod namespace. "
            "The directory may be temporarily unavailable."
        ),
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address. Default: 0.0.0.0",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="TCP port. Default: 8000",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    media_root = Path(
        args.root
    ).resolve()

    if not media_root.exists():
        raise FileNotFoundError(
            f"Media root does not exist: {media_root}"
        )

    if not media_root.is_dir():
        raise NotADirectoryError(
            f"Media root is not a directory: {media_root}"
        )

    vod_root = (
        lexical_absolute_path(
            args.vod_root
        )
        if args.vod_root
        else lexical_absolute_path(
            media_root / "vod"
        )
    )

    backing_present = (
        configured_local_backing_present(
            vod_root
        )
    )

    if backing_present is not False:
        try:
            if (
                vod_root.exists()
                and not vod_root.is_dir()
            ):
                raise NotADirectoryError(
                    f"VOD root is not a directory: {vod_root}"
                )
        except OSError:
            pass

    handler = partial(
        RangeRequestHandler,
        directory=str(media_root),
        vod_directory=str(vod_root),
    )

    server = ThreadingHTTPServer(
        (
            args.host,
            args.port,
        ),
        handler,
    )

    print("PrivyHub media server")
    print(f"Root: {media_root}")
    print(f"VOD root: {vod_root}")
    if backing_present is False:
        vod_available = False
    else:
        try:
            vod_available = (
                vod_root.exists()
                and vod_root.is_dir()
            )
        except OSError:
            vod_available = False

    print(
        "VOD available: "
        + str(
            vod_available
        )
    )
    print(
        f"Listening on {args.host}:{args.port}"
    )
    print("Stop with Ctrl+C.")
    print("")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        pass

    finally:
        server.server_close()


if __name__ == "__main__":
    main()
