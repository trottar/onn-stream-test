#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_1_games_source_context_v1"
CLASSIFICATION = "B4_1_GAMES_SOURCE_CONTEXT_CAPTURED"
GAMES_REL = "companion/plugins/games.py"

ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_text(data: bytes) -> tuple[str, str, str]:
    bom = "NONE"

    if data.startswith(b"\xef\xbb\xbf"):
        bom = "UTF8_BOM"
        data = data[3:]

    newline = (
        "CRLF"
        if b"\r\n" in data
        else "LF"
    )

    return (
        data.decode("utf-8"),
        bom,
        newline,
    )


def safe_line(text: str) -> tuple[str, bool]:
    redacted = False

    value, count = ADDRESS_RE.subn(
        "<redacted-address>",
        text,
    )
    if count:
        redacted = True

    value, count = MAC_RE.subn(
        "<redacted-address>",
        value,
    )
    if count:
        redacted = True

    return (
        value,
        redacted,
    )


def source_segment(
    lines: list[str],
    start: int,
    end: int,
) -> tuple[str, bool]:
    selected = lines[
        start - 1:
        end
    ]

    rendered = []
    redacted = False

    for line in selected:
        safe, changed = safe_line(
            line
        )
        rendered.append(
            safe
        )
        redacted = (
            redacted
            or changed
        )

    return (
        "\n".join(
            rendered
        ),
        redacted,
    )


def merge_ranges(
    ranges: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    if not ranges:
        return []

    ordered = sorted(
        ranges
    )
    merged = [
        list(
            ordered[0]
        )
    ]

    for start, end in ordered[1:]:
        current = merged[-1]

        if start <= current[1] + 1:
            current[1] = max(
                current[1],
                end,
            )
        else:
            merged.append(
                [
                    start,
                    end,
                ]
            )

    return [
        (
            int(start),
            int(end),
        )
        for start, end
        in merged
    ]


def call_on_self_stream(
    node: ast.Call,
) -> str | None:
    func = node.func

    if not isinstance(
        func,
        ast.Attribute,
    ):
        return None

    owner = func.value

    if not (
        isinstance(
            owner,
            ast.Attribute,
        )
        and isinstance(
            owner.value,
            ast.Name,
        )
        and owner.value.id == "self"
        and owner.attr == "_stream"
    ):
        return None

    return func.attr


def is_self_stream_target(
    node: ast.AST,
) -> bool:
    return (
        isinstance(
            node,
            ast.Attribute,
        )
        and isinstance(
            node.value,
            ast.Name,
        )
        and node.value.id == "self"
        and node.attr == "_stream"
    )


def string_constants(
    node: ast.AST,
) -> set[str]:
    return {
        child.value
        for child in ast.walk(
            node
        )
        if (
            isinstance(
                child,
                ast.Constant,
            )
            and isinstance(
                child.value,
                str,
            )
        )
    }


def subscript_key(
    node: ast.AST,
) -> str | None:
    if not isinstance(
        node,
        ast.Subscript,
    ):
        return None

    slice_node = node.slice

    if (
        isinstance(
            slice_node,
            ast.Constant,
        )
        and isinstance(
            slice_node.value,
            str,
        )
    ):
        return slice_node.value

    return None


def dict_id(
    node: ast.Dict,
) -> str | None:
    for key, value in zip(
        node.keys,
        node.values,
    ):
        if (
            isinstance(
                key,
                ast.Constant,
            )
            and key.value == "id"
            and isinstance(
                value,
                ast.Constant,
            )
            and isinstance(
                value.value,
                str,
            )
        ):
            return value.value

    return None


class ContextVisitor(ast.NodeVisitor):
    def __init__(
        self,
    ) -> None:
        self.functions: list[str] = []
        self.records: list[dict[str, Any]] = []

    def function_name(
        self,
    ) -> str:
        return (
            self.functions[-1]
            if self.functions
            else "<module>"
        )

    def add(
        self,
        kind: str,
        node: ast.AST,
        *,
        detail: str,
    ) -> None:
        start = int(
            getattr(
                node,
                "lineno",
                0,
            )
        )
        end = int(
            getattr(
                node,
                "end_lineno",
                start,
            )
        )

        self.records.append(
            {
                "kind": kind,
                "function": self.function_name(),
                "start_line": start,
                "end_line": end,
                "detail": detail,
            }
        )

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> Any:
        self.functions.append(
            node.name
        )
        self.generic_visit(
            node
        )
        self.functions.pop()
        return None

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> Any:
        self.functions.append(
            node.name
        )
        self.generic_visit(
            node
        )
        self.functions.pop()
        return None

    def visit_ImportFrom(
        self,
        node: ast.ImportFrom,
    ) -> Any:
        module = node.module or ""

        if (
            module
            == "games.stream_manager"
            or module.endswith(
                ".stream_manager"
            )
        ):
            self.add(
                "legacy_import",
                node,
                detail=module,
            )

        self.generic_visit(
            node
        )
        return None

    def visit_Assign(
        self,
        node: ast.Assign,
    ) -> Any:
        if any(
            is_self_stream_target(
                target
            )
            for target in node.targets
        ):
            self.add(
                "legacy_constructor_assignment",
                node,
                detail="self._stream",
            )

        for target in node.targets:
            key = subscript_key(
                target
            )

            if key in {
                "stream_host",
                "stream_warning",
            }:
                self.add(
                    "legacy_payload_assignment",
                    node,
                    detail=key,
                )

        self.generic_visit(
            node
        )
        return None

    def visit_If(
        self,
        node: ast.If,
    ) -> Any:
        constants = string_constants(
            node.test
        )

        matched = sorted(
            constants.intersection(
                {
                    "stream-status",
                    "stream-start",
                    "stream-stop",
                }
            )
        )

        if matched:
            self.add(
                "legacy_action_if",
                node,
                detail=",".join(
                    matched
                ),
            )

        self.generic_visit(
            node
        )
        return None

    def visit_Dict(
        self,
        node: ast.Dict,
    ) -> Any:
        if dict_id(
            node
        ) == "games_stream_host":
            self.add(
                "legacy_catalog_dict",
                node,
                detail="games_stream_host",
            )

        self.generic_visit(
            node
        )
        return None

    def visit_Try(
        self,
        node: ast.Try,
    ) -> Any:
        methods = {
            call_on_self_stream(
                child
            )
            for child in ast.walk(
                node
            )
            if isinstance(
                child,
                ast.Call,
            )
        }

        handler_names = set()

        for handler in node.handlers:
            if handler.type is None:
                continue

            for child in ast.walk(
                handler.type
            ):
                if isinstance(
                    child,
                    ast.Name,
                ):
                    handler_names.add(
                        child.id
                    )

        if (
            "ensure_running"
            in methods
            and "StreamHostError"
            in handler_names
        ):
            self.add(
                "legacy_launch_try",
                node,
                detail="ensure_running/StreamHostError",
            )

        self.generic_visit(
            node
        )
        return None

    def visit_ExceptHandler(
        self,
        node: ast.ExceptHandler,
    ) -> Any:
        if node.type is not None:
            names = {
                child.id
                for child in ast.walk(
                    node.type
                )
                if isinstance(
                    child,
                    ast.Name,
                )
            }

            if "StreamHostError" in names:
                self.add(
                    "streamhost_exception_handler",
                    node,
                    detail=",".join(
                        sorted(
                            names
                        )
                    ),
                )

        self.generic_visit(
            node
        )
        return None

    def visit_Call(
        self,
        node: ast.Call,
    ) -> Any:
        method = call_on_self_stream(
            node
        )

        if method is not None:
            self.add(
                "legacy_stream_call",
                node,
                detail=method,
            )

        self.generic_visit(
            node
        )
        return None


def build_report(
    root: Path,
) -> dict[str, Any]:
    path = (
        root
        / GAMES_REL
    )

    data = path.read_bytes()
    text, bom, newline = detect_text(
        data
    )
    lines = text.splitlines()

    tree = ast.parse(
        text,
        filename=GAMES_REL,
    )

    visitor = ContextVisitor()
    visitor.visit(
        tree
    )

    records = sorted(
        visitor.records,
        key=lambda row: (
            row[
                "start_line"
            ],
            row[
                "end_line"
            ],
            row[
                "kind"
            ],
        ),
    )

    interesting_lines = []

    for record in records:
        interesting_lines.extend(
            range(
                record[
                    "start_line"
                ],
                record[
                    "end_line"
                ]
                + 1,
            )
        )

    ranges = merge_ranges(
        [
            (
                max(
                    1,
                    line_no - 5,
                ),
                min(
                    len(
                        lines
                    ),
                    line_no + 5,
                ),
            )
            for line_no
            in interesting_lines
        ]
    )

    contexts = []

    for index, (
        start,
        end,
    ) in enumerate(
        ranges,
        1,
    ):
        segment, redacted = source_segment(
            lines,
            start,
            end,
        )

        raw_segment = "\n".join(
            lines[
                start - 1:
                end
            ]
        ).encode(
            "utf-8"
        )

        contexts.append(
            {
                "block": index,
                "start_line": start,
                "end_line": end,
                "raw_segment_sha256": sha256_bytes(
                    raw_segment
                ),
                "redaction_applied": redacted,
                "text": segment,
            }
        )

    counts: dict[
        str,
        int,
    ] = {}

    for record in records:
        kind = str(
            record[
                "kind"
            ]
        )
        counts[
            kind
        ] = (
            counts.get(
                kind,
                0,
            )
            + 1
        )

    return {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "source": {
            "path": GAMES_REL,
            "sha256": sha256_bytes(
                data
            ),
            "bytes": len(
                data
            ),
            "lines": len(
                lines
            ),
            "bom": bom,
            "newline": newline,
        },
        "record_counts": counts,
        "records": records,
        "context_blocks": contexts,
    }


def format_text(
    report: dict[str, Any],
) -> str:
    source = report[
        "source"
    ]

    lines = [
        "PrivyHub B4.1 exact Games source-context audit",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== SOURCE ===",
        f"Path: {source['path']}",
        f"SHA-256: {source['sha256']}",
        f"Bytes: {source['bytes']}",
        f"Lines: {source['lines']}",
        f"BOM: {source['bom']}",
        f"Newline: {source['newline']}",
        "",
        "=== STRUCTURAL RECORD COUNTS ===",
    ]

    for key, value in sorted(
        report[
            "record_counts"
        ].items()
    ):
        lines.append(
            f"{key}: {value}"
        )

    lines += [
        "",
        "=== STRUCTURAL RECORDS ===",
    ]

    for record in report[
        "records"
    ]:
        lines.append(
            f"{record['kind']} "
            f"function={record['function']} "
            f"lines={record['start_line']}-{record['end_line']} "
            f"detail={record['detail']}"
        )

    lines += [
        "",
        "=== EXACT CONTEXT BLOCKS ===",
        "These blocks preserve source indentation. "
        "Any address-like value would be redacted and explicitly marked.",
    ]

    for block in report[
        "context_blocks"
    ]:
        lines += [
            "",
            (
                f"--- BLOCK {block['block']} "
                f"LINES {block['start_line']}-{block['end_line']} "
                f"SHA256 {block['raw_segment_sha256']} "
                f"REDACTED {block['redaction_applied']} ---"
            ),
            block[
                "text"
            ],
            f"--- END BLOCK {block['block']} ---",
        ]

    lines += [
        "",
        "=== DISPOSITION ===",
        "USE_EXACT_AST_SPANS_AND_CAPTURED_CONTEXT_FOR_B4_1_REBUILD",
        "Do not retry the previous B4.1 ZIP.",
    ]

    return (
        "\n".join(
            lines
        )
        + "\n"
    )


def self_test() -> int:
    sample = """
from games.stream_manager import StreamHostError, StreamManager

class X:
    def __init__(self):
        self._stream = StreamManager()

    def handle(self, action):
        if action == "stream-status":
            return self._stream.status()

    def launch(self):
        warning = None
        try:
            self._stream.ensure_running()
        except StreamHostError:
            warning = "x"
        payload = {}
        payload["stream_host"] = self._stream.status()
        payload["stream_warning"] = warning
        return payload
"""

    tree = ast.parse(
        sample
    )
    visitor = ContextVisitor()
    visitor.visit(
        tree
    )

    kinds = [
        item[
            "kind"
        ]
        for item in visitor.records
    ]

    assert "legacy_import" in kinds
    assert "legacy_constructor_assignment" in kinds
    assert "legacy_action_if" in kinds
    assert "legacy_launch_try" in kinds
    assert "legacy_payload_assignment" in kinds
    assert "legacy_stream_call" in kinds
    assert "streamhost_exception_handler" in kinds

    assert safe_line(
        ".".join(
            (
                "192",
                "0",
                "2",
                "4",
            )
        )
    )[1] is True

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        default=".",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(
        args.root
    ).resolve()

    path = (
        root
        / GAMES_REL
    )

    if not path.is_file():
        raise SystemExit(
            "Current games.py is missing"
        )

    report = build_report(
        root
    )

    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        out_dir
        / "b4_1_games_source_context.json"
    )

    text_path = (
        out_dir
        / "b4_1_games_source_context.txt"
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    text_path.write_text(
        format_text(
            report
        ),
        encoding="utf-8",
        newline="\n",
    )

    print(
        CLASSIFICATION
    )
    print(
        "Text:",
        text_path,
    )
    print(
        "JSON:",
        json_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
