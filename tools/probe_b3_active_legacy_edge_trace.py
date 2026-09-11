#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b3_active_legacy_edge_trace_v1"
CLASSIFICATION = "B3_ACTIVE_LEGACY_EDGE_TRACE_CAPTURED"

GAMES_REL = "companion/plugins/games.py"
STREAM_MANAGER_REL = "companion/games/stream_manager.py"
MAIN_ACTIVITY_REL = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "MainActivity.kt"
)
MANIFEST_REL = "PrivyHub/app/src/main/AndroidManifest.xml"

LEGACY_TERMS = (
    "sunshine",
    "moonlight",
    "com.limelight",
    "games.stream_manager",
    "streammanager",
)

REFERENCE_TOKENS = {
    "games.stream_manager": "games.stream_manager",
    "StreamManager": "StreamManager",
    "runtime/streaming/sunshine": "runtime/streaming/sunshine",
    "setup_sunshine_portable.ps1": "setup_sunshine_portable.ps1",
    "open_sunshine_web_ui.ps1": "open_sunshine_web_ui.ps1",
    "install_moonlight_onn.ps1": "install_moonlight_onn.ps1",
    "com.limelight": "com.limelight",
    "sunshine.exe": "sunshine.exe",
}

TEXT_SUFFIXES = {
    ".py",
    ".ps1",
    ".kt",
    ".kts",
    ".java",
    ".xml",
    ".json",
    ".bat",
    ".cmd",
    ".sh",
    ".ini",
    ".cfg",
    ".properties",
}

SKIP_PREFIXES = (
    "archive/",
    "logs/",
    "docs/",
    "runtime/",
    ".git/",
    "PrivyHub/app/build/",
    "PrivyHub/build/",
)

SKIP_NAMES = {
    "__pycache__",
    ".gradle",
    "build",
    "out",
    "dist",
}

ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)
KOTLIN_FUN_RE = re.compile(
    r"^\s*(?:(?:private|public|internal|protected|override|open|final|suspend)\s+)*"
    r"fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def redact(text: str) -> str:
    value = ADDRESS_RE.sub(
        "<redacted-address>",
        text,
    )
    value = MAC_RE.sub(
        "<redacted-address>",
        value,
    )
    return value


def safe_read(path: Path) -> str:
    data = path.read_bytes()

    for encoding in (
        "utf-8-sig",
        "utf-16",
        "cp1252",
    ):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue

    return data.decode(
        "utf-8",
        errors="replace",
    )


def source_line(
    lines: list[str],
    line_no: int,
) -> str:
    if (
        line_no < 1
        or line_no > len(lines)
    ):
        return ""

    return redact(
        lines[line_no - 1].strip()
    )[:700]


class GamesVisitor(ast.NodeVisitor):
    def __init__(
        self,
        lines: list[str],
    ) -> None:
        self.lines = lines
        self.function_stack: list[str] = []
        self.imports: list[dict[str, Any]] = []
        self.stream_constructors: list[dict[str, Any]] = []
        self.calls: list[dict[str, Any]] = []
        self.references: list[dict[str, Any]] = []

    def _function(
        self,
    ) -> str:
        return (
            self.function_stack[-1]
            if self.function_stack
            else "<module>"
        )

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> Any:
        self.function_stack.append(
            node.name
        )
        self.generic_visit(node)
        self.function_stack.pop()
        return None

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> Any:
        self.function_stack.append(
            node.name
        )
        self.generic_visit(node)
        self.function_stack.pop()
        return None

    def visit_ImportFrom(
        self,
        node: ast.ImportFrom,
    ) -> Any:
        module = node.module or ""

        if (
            module == "games.stream_manager"
            or module.endswith(
                ".stream_manager"
            )
        ):
            self.imports.append(
                {
                    "line": node.lineno,
                    "module": module,
                    "names": [
                        alias.name
                        for alias in node.names
                    ],
                    "text": source_line(
                        self.lines,
                        node.lineno,
                    ),
                }
            )

        self.generic_visit(node)
        return None

    def visit_Assign(
        self,
        node: ast.Assign,
    ) -> Any:
        for target in node.targets:
            if (
                isinstance(
                    target,
                    ast.Attribute,
                )
                and isinstance(
                    target.value,
                    ast.Name,
                )
                and target.value.id == "self"
                and target.attr == "_stream"
            ):
                constructor = ""

                if isinstance(
                    node.value,
                    ast.Call,
                ):
                    func = node.value.func

                    if isinstance(
                        func,
                        ast.Name,
                    ):
                        constructor = func.id
                    elif isinstance(
                        func,
                        ast.Attribute,
                    ):
                        constructor = func.attr

                self.stream_constructors.append(
                    {
                        "line": node.lineno,
                        "function": self._function(),
                        "constructor": constructor,
                        "text": source_line(
                            self.lines,
                            node.lineno,
                        ),
                    }
                )

        self.generic_visit(node)
        return None

    def visit_Call(
        self,
        node: ast.Call,
    ) -> Any:
        func = node.func

        if (
            isinstance(
                func,
                ast.Attribute,
            )
            and isinstance(
                func.value,
                ast.Attribute,
            )
            and isinstance(
                func.value.value,
                ast.Name,
            )
            and func.value.value.id == "self"
            and func.value.attr in {
                "_stream",
                "_native_stream",
            }
        ):
            self.calls.append(
                {
                    "object": func.value.attr,
                    "method": func.attr,
                    "line": node.lineno,
                    "function": self._function(),
                    "text": source_line(
                        self.lines,
                        node.lineno,
                    ),
                }
            )

        self.generic_visit(node)
        return None

    def visit_Attribute(
        self,
        node: ast.Attribute,
    ) -> Any:
        if (
            isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id == "self"
            and node.attr in {
                "_stream",
                "_native_stream",
            }
        ):
            self.references.append(
                {
                    "object": node.attr,
                    "line": node.lineno,
                    "function": self._function(),
                    "text": source_line(
                        self.lines,
                        node.lineno,
                    ),
                }
            )

        self.generic_visit(node)
        return None


def trace_games(
    root: Path,
) -> dict[str, Any]:
    path = root / GAMES_REL
    text = safe_read(path)
    lines = text.splitlines()

    tree = ast.parse(
        text,
        filename=GAMES_REL,
    )

    visitor = GamesVisitor(
        lines
    )
    visitor.visit(tree)

    stream_calls = [
        row
        for row in visitor.calls
        if row["object"] == "_stream"
    ]

    native_calls = [
        row
        for row in visitor.calls
        if row["object"] == "_native_stream"
    ]

    start_methods = {
        "ensure_running",
        "start",
        "start_host",
    }

    stop_methods = {
        "stop",
        "shutdown",
        "close",
    }

    status_methods = {
        "status",
        "get_status",
    }

    return {
        "path": GAMES_REL,
        "sha256": sha256(
            path
        ),
        "imports": visitor.imports,
        "stream_constructors": visitor.stream_constructors,
        "legacy_stream_calls": stream_calls,
        "native_stream_calls": native_calls,
        "legacy_stream_reference_count": sum(
            1
            for row in visitor.references
            if row["object"] == "_stream"
        ),
        "native_stream_reference_count": sum(
            1
            for row in visitor.references
            if row["object"] == "_native_stream"
        ),
        "legacy_start_calls": [
            row
            for row in stream_calls
            if row["method"] in start_methods
        ],
        "legacy_stop_calls": [
            row
            for row in stream_calls
            if row["method"] in stop_methods
        ],
        "legacy_status_calls": [
            row
            for row in stream_calls
            if row["method"] in status_methods
        ],
        "legacy_call_methods": dict(
            sorted(
                Counter(
                    row["method"]
                    for row in stream_calls
                ).items()
            )
        ),
        "native_call_methods": dict(
            sorted(
                Counter(
                    row["method"]
                    for row in native_calls
                ).items()
            )
        ),
    }


def trace_stream_manager(
    root: Path,
) -> dict[str, Any]:
    path = root / STREAM_MANAGER_REL
    text = safe_read(path)
    lines = text.splitlines()

    tree = ast.parse(
        text,
        filename=STREAM_MANAGER_REL,
    )

    public_methods: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and not node.name.startswith(
                "_"
            )
        ):
            public_methods.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "text": source_line(
                        lines,
                        node.lineno,
                    ),
                }
            )

    executable_refs = []

    for line_no, line in enumerate(
        lines,
        1,
    ):
        folded = line.casefold()

        if any(
            term in folded
            for term in (
                "sunshine.exe",
                "setup_sunshine_portable.ps1",
                "runtime",
                "sunshine.conf",
            )
        ):
            executable_refs.append(
                {
                    "line": line_no,
                    "text": redact(
                        line.strip()
                    )[:700],
                }
            )

    return {
        "path": STREAM_MANAGER_REL,
        "sha256": sha256(
            path
        ),
        "public_methods": sorted(
            public_methods,
            key=lambda row: (
                row["line"],
                row["name"],
            ),
        ),
        "sunshine_runtime_references": executable_refs,
    }


def kotlin_functions(
    lines: list[str],
) -> list[
    tuple[int, str]
]:
    result = []

    for index, line in enumerate(
        lines,
        1,
    ):
        match = KOTLIN_FUN_RE.match(
            line
        )

        if match:
            result.append(
                (
                    index,
                    match.group(1),
                )
            )

    return result


def enclosing_kotlin_function(
    declarations: list[
        tuple[int, str]
    ],
    line_no: int,
) -> str:
    current = "<class-or-lambda>"

    for declaration_line, name in declarations:
        if declaration_line > line_no:
            break

        current = name

    return current


def trace_android(
    root: Path,
) -> dict[str, Any]:
    path = root / MAIN_ACTIVITY_REL
    text = safe_read(
        path
    )
    lines = text.splitlines()
    declarations = kotlin_functions(
        lines
    )

    occurrences = []

    for line_no, line in enumerate(
        lines,
        1,
    ):
        folded = line.casefold()
        matched = [
            term
            for term in (
                "sunshine",
                "moonlight",
                "com.limelight",
            )
            if term in folded
        ]

        if not matched:
            continue

        function = enclosing_kotlin_function(
            declarations,
            line_no,
        )

        occurrences.append(
            {
                "line": line_no,
                "function": function,
                "terms": matched,
                "text": redact(
                    line.strip()
                )[:700],
            }
        )

    legacy_functions = sorted(
        {
            row["function"]
            for row in occurrences
            if row["function"]
            not in {
                "<class-or-lambda>",
            }
        }
    )

    call_sites = []

    for function in legacy_functions:
        pattern = re.compile(
            rf"\b{re.escape(function)}\s*\("
        )

        declaration_lines = {
            line_no
            for line_no, name
            in declarations
            if name == function
        }

        for line_no, line in enumerate(
            lines,
            1,
        ):
            if line_no in declaration_lines:
                continue

            if pattern.search(
                line
            ):
                call_sites.append(
                    {
                        "target_function": function,
                        "line": line_no,
                        "caller_function": (
                            enclosing_kotlin_function(
                                declarations,
                                line_no,
                            )
                        ),
                        "text": redact(
                            line.strip()
                        )[:700],
                    }
                )

    moonlight_launch_functions = sorted(
        {
            row["function"]
            for row in occurrences
            if (
                "com.limelight"
                in row["terms"]
                or "moonlight"
                in row["terms"]
            )
        }
    )

    return {
        "path": MAIN_ACTIVITY_REL,
        "sha256": sha256(
            path
        ),
        "legacy_occurrences": occurrences,
        "legacy_functions": legacy_functions,
        "legacy_function_call_sites": call_sites,
        "moonlight_launch_functions": moonlight_launch_functions,
        "start_activity_present": (
            "startActivity("
            in text
        ),
    }


def trace_manifest(
    root: Path,
) -> dict[str, Any]:
    path = root / MANIFEST_REL
    text = safe_read(
        path
    )
    lines = text.splitlines()

    matches = []

    for line_no, line in enumerate(
        lines,
        1,
    ):
        if (
            "com.limelight"
            in line.casefold()
        ):
            matches.append(
                {
                    "line": line_no,
                    "text": redact(
                        line.strip()
                    )[:700],
                }
            )

    return {
        "path": MANIFEST_REL,
        "sha256": sha256(
            path
        ),
        "limelight_queries": matches,
    }


def current_reference_graph(
    root: Path,
) -> list[
    dict[str, Any]
]:
    result = []

    for path in sorted(
        root.rglob("*"),
        key=lambda value:
            value.as_posix().casefold(),
    ):
        if not path.is_file():
            continue

        try:
            relative = (
                path.relative_to(
                    root
                ).as_posix()
            )
        except ValueError:
            continue

        if relative == (
            "tools/probe_b3_active_legacy_edge_trace.py"
        ):
            continue

        if any(
            relative.startswith(
                prefix
            )
            for prefix in SKIP_PREFIXES
        ):
            continue

        if any(
            part in SKIP_NAMES
            for part in path.parts
        ):
            continue

        if (
            path.suffix.casefold()
            not in TEXT_SUFFIXES
        ):
            continue

        try:
            text = safe_read(
                path
            )
        except OSError:
            continue

        for line_no, line in enumerate(
            text.splitlines(),
            1,
        ):
            folded = line.casefold()

            matched = [
                label
                for label, token
                in REFERENCE_TOKENS.items()
                if token.casefold()
                in folded
            ]

            if not matched:
                continue

            result.append(
                {
                    "path": relative,
                    "line": line_no,
                    "tokens": matched,
                    "text": redact(
                        line.strip()
                    )[:700],
                }
            )

    return result


def footprint(
    root: Path,
    relative: str,
) -> dict[str, Any]:
    path = root / relative

    if not path.exists():
        return {
            "path": relative,
            "exists": False,
            "files": 0,
            "bytes": 0,
        }

    if path.is_file():
        return {
            "path": relative,
            "exists": True,
            "files": 1,
            "bytes": path.stat().st_size,
        }

    files = [
        item
        for item in path.rglob("*")
        if item.is_file()
    ]

    return {
        "path": relative,
        "exists": True,
        "files": len(
            files
        ),
        "bytes": sum(
            item.stat().st_size
            for item in files
        ),
    }


def previous_b3(
    root: Path,
) -> dict[str, Any]:
    path = (
        root
        / "logs/diagnostics/"
        "b3_sunshine_moonlight_inventory.json"
    )

    if not path.is_file():
        return {
            "available": False,
        }

    try:
        value = json.loads(
            safe_read(
                path
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "available": False,
        }

    system_state = (
        value.get(
            "system_state"
        )
        if isinstance(
            value,
            dict,
        )
        else None
    )

    if not isinstance(
        system_state,
        dict,
    ):
        system_state = {}

    system_counts = {}

    for key in (
        "processes",
        "services",
        "scheduled_tasks",
        "firewall_rules",
        "installed_software",
    ):
        row = system_state.get(
            key
        )

        system_counts[key] = (
            int(
                row.get(
                    "count",
                    0,
                )
            )
            if isinstance(
                row,
                dict,
            )
            else None
        )

    counts = value.get(
        "classification_counts"
    )

    if not isinstance(
        counts,
        dict,
    ):
        counts = {}

    return {
        "available": True,
        "classification": value.get(
            "classification"
        ),
        "previous_classification_counts": counts,
        "system_counts": system_counts,
        "system_legacy_state_zero": all(
            number == 0
            for number
            in system_counts.values()
            if number is not None
        ),
    }


def disposition(
    games: dict[str, Any],
    android: dict[str, Any],
    manifest: dict[str, Any],
) -> str:
    server_start = bool(
        games[
            "legacy_start_calls"
        ]
    )

    android_launch = bool(
        android[
            "moonlight_launch_functions"
        ]
    )

    manifest_query = bool(
        manifest[
            "limelight_queries"
        ]
    )

    if (
        server_start
        and android_launch
        and manifest_query
    ):
        return (
            "B3_ACTIVE_CUT_SET_CONFIRMED_"
            "SPLIT_B4_SERVER_ANDROID_ARTIFACTS"
        )

    if server_start:
        return (
            "B3_SERVER_LEGACY_EDGE_CONFIRMED_"
            "TRACE_BEFORE_B4"
        )

    if (
        android_launch
        or manifest_query
    ):
        return (
            "B3_ANDROID_LEGACY_EDGE_CONFIRMED_"
            "TRACE_BEFORE_B4"
        )

    return (
        "B3_NO_NORMAL_START_EDGE_IDENTIFIED_"
        "REVIEW_TRACE"
    )


def format_text(
    report: dict[str, Any],
) -> str:
    games = report[
        "games_plugin"
    ]

    android = report[
        "android"
    ]

    manifest = report[
        "manifest"
    ]

    previous = report[
        "previous_b3"
    ]

    lines = [
        "PrivyHub Phase B3.1 active legacy edge trace",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Files deleted by probe: 0",
        "Network addresses collected/logged: NONE",
        "",
        "=== PREVIOUS B3 SIGNAL ===",
        f"B3 inventory JSON available: {previous.get('available', False)}",
        f"Windows legacy system state all zero: {previous.get('system_legacy_state_zero', False)}",
        "",
        "=== EXACT CURRENT SOURCE HASHES ===",
        f"games_plugin: {games['sha256']} | {games['path']}",
        f"stream_manager: {report['stream_manager']['sha256']} | {report['stream_manager']['path']}",
        f"main_activity: {android['sha256']} | {android['path']}",
        f"manifest: {manifest['sha256']} | {manifest['path']}",
        "",
        "=== GAMES -> LEGACY STREAMMANAGER EDGE ===",
        f"StreamManager imports: {len(games['imports'])}",
        f"StreamManager constructors: {len(games['stream_constructors'])}",
        f"Legacy _stream calls: {len(games['legacy_stream_calls'])}",
        f"Legacy start/ensure calls: {len(games['legacy_start_calls'])}",
        f"Legacy status calls: {len(games['legacy_status_calls'])}",
        f"Legacy stop/shutdown calls: {len(games['legacy_stop_calls'])}",
        f"Native _native_stream calls: {len(games['native_stream_calls'])}",
        "Legacy call methods: "
        + json.dumps(
            games[
                "legacy_call_methods"
            ],
            sort_keys=True,
        ),
        "Native call methods: "
        + json.dumps(
            games[
                "native_call_methods"
            ],
            sort_keys=True,
        ),
    ]

    for row in games[
        "stream_constructors"
    ]:
        lines.append(
            f"  CONSTRUCT line={row['line']} function={row['function']} constructor={row['constructor']} | {row['text']}"
        )

    for row in games[
        "legacy_stream_calls"
    ]:
        lines.append(
            f"  LEGACY_CALL line={row['line']} function={row['function']} method={row['method']} | {row['text']}"
        )

    lines += [
        "",
        "=== ANDROID MOONLIGHT EDGE ===",
        f"Legacy occurrence count: {len(android['legacy_occurrences'])}",
        "Legacy functions: "
        + ", ".join(
            android[
                "legacy_functions"
            ]
        ),
        "Moonlight/com.limelight functions: "
        + ", ".join(
            android[
                "moonlight_launch_functions"
            ]
        ),
        f"Legacy function call sites: {len(android['legacy_function_call_sites'])}",
        f"Manifest com.limelight queries: {len(manifest['limelight_queries'])}",
    ]

    for row in android[
        "legacy_occurrences"
    ]:
        lines.append(
            f"  ANDROID_REF line={row['line']} function={row['function']} terms={','.join(row['terms'])} | {row['text']}"
        )

    for row in android[
        "legacy_function_call_sites"
    ]:
        lines.append(
            f"  CALL_SITE line={row['line']} caller={row['caller_function']} target={row['target_function']} | {row['text']}"
        )

    for row in manifest[
        "limelight_queries"
    ]:
        lines.append(
            f"  MANIFEST_REF line={row['line']} | {row['text']}"
        )

    lines += [
        "",
        "=== CURRENT-TREE LEGACY REFERENCE GRAPH ===",
    ]

    for row in report[
        "current_reference_graph"
    ]:
        lines.append(
            f"  {row['path']}:{row['line']} | tokens={','.join(row['tokens'])} | {row['text']}"
        )

    lines += [
        "",
        "=== GROUPED LEGACY ARTIFACT FOOTPRINT ===",
    ]

    for row in report[
        "artifact_footprint"
    ]:
        lines.append(
            f"  {row['path']}: exists={row['exists']} files={row['files']} bytes={row['bytes']}"
        )

    lines += [
        "",
        "=== NOISE / NON-TARGET RULES ===",
        "archive/**: historical backup evidence; never use as current execution edges.",
        "runtime/streaming/sunshine/**: treat as one legacy runtime payload group, not one active dependency per file.",
        "runtime/emulators/**/moonlight_libretro.info: RetroArch distribution/name collision; not the Moonlight Android client.",
        "runtime/emulators/**/stellabialek-moonlight-sillyness.*: shader name collision; not the Moonlight Android client.",
        "B3 package ZIP filenames: diagnostic artifact names; not production dependencies.",
        "",
        "=== DISPOSITION ===",
        report[
            "disposition"
        ],
        "",
        "=== RECOMMENDED B4 CUT ORDER ===",
        "1. Server edge: remove proven legacy StreamManager import/constructor/calls from current Games plugin while preserving NativeStreamManager.",
        "2. Android edge: remove Moonlight/com.limelight launch UI and manifest package visibility only after exact function/caller review.",
        "3. Artifact edge: remove Sunshine/Moonlight setup/download/runtime payloads only after current production reference graph is clean.",
        "4. Run focused native-only Games regression (B5) before the clean-native checkpoint.",
        "",
        "Return this file before any B4 removal patch.",
    ]

    return (
        "\n".join(
            lines
        )
        + "\n"
    )


def self_test() -> int:
    source = """
from games.stream_manager import StreamManager

class X:
    def __init__(self):
        self._stream = StreamManager()
        self._native_stream = object()

    def start(self):
        self._stream.ensure_running()
        self._native_stream.start_game_session()

    def status(self):
        return self._stream.status()
"""

    lines = source.splitlines()

    visitor = GamesVisitor(
        lines
    )

    visitor.visit(
        ast.parse(
            source
        )
    )

    assert len(
        visitor.imports
    ) == 1

    assert len(
        visitor.stream_constructors
    ) == 1

    methods = [
        row[
            "method"
        ]
        for row in visitor.calls
        if row[
            "object"
        ] == "_stream"
    ]

    assert methods == [
        "ensure_running",
        "status",
    ]

    sample_address = ".".join(
        (
            "192",
            "0",
            "2",
            "9",
        )
    )

    assert redact(
        "endpoint="
        + sample_address
    ) == "endpoint=<redacted-address>"

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

    required = (
        GAMES_REL,
        STREAM_MANAGER_REL,
        MAIN_ACTIVITY_REL,
        MANIFEST_REL,
    )

    for relative in required:
        if not (
            root
            / relative
        ).is_file():
            raise SystemExit(
                f"Required current source missing: {relative}"
            )

    games = trace_games(
        root
    )

    stream_manager = trace_stream_manager(
        root
    )

    android = trace_android(
        root
    )

    manifest = trace_manifest(
        root
    )

    graph = current_reference_graph(
        root
    )

    previous = previous_b3(
        root
    )

    footprints = [
        footprint(
            root,
            relative,
        )
        for relative in (
            "runtime/streaming/sunshine",
            "runtime/downloads/sunshine",
            "runtime/downloads/moonlight",
            "scripts/setup_sunshine_portable.ps1",
            "scripts/install_sunshine_firewall.ps1",
            "scripts/remove_sunshine_firewall.ps1",
            "scripts/open_sunshine_web_ui.ps1",
            "scripts/install_moonlight_onn.ps1",
        )
    ]

    report = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "files_deleted_by_probe": 0,
        "network_addresses_collected_or_logged": "NONE",
        "previous_b3": previous,
        "games_plugin": games,
        "stream_manager": stream_manager,
        "android": android,
        "manifest": manifest,
        "current_reference_graph": graph,
        "artifact_footprint": footprints,
        "noise_rules": [
            "archive/** is historical, not current execution state",
            "runtime/streaming/sunshine/** is grouped as one runtime payload",
            "runtime/emulators/**/moonlight_libretro.info is not Moonlight Android client integration",
            "runtime/emulators/**/stellabialek-moonlight-sillyness.* is a shader-name collision",
            "B3 package ZIP names are diagnostic artifacts",
        ],
        "disposition": disposition(
            games,
            android,
            manifest,
        ),
    }

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
        / "b3_active_legacy_edge_trace.json"
    )

    text_path = (
        out_dir
        / "b3_active_legacy_edge_trace.txt"
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
