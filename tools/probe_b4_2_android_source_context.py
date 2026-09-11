#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_2_android_source_context_v1"
CLASSIFICATION = "B4_2_ANDROID_SOURCE_CONTEXT_CAPTURED"

MAIN_REL = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "MainActivity.kt"
)
MANIFEST_REL = (
    "PrivyHub/app/src/main/AndroidManifest.xml"
)

TARGET_FUNCTIONS = {
    "buildGameCatalogMessage",
    "openGameStreamClient",
    "showGameDetails",
    "launchGameOnCompanion",
}

LEGACY_TERMS = (
    "sunshine",
    "moonlight",
    "com.limelight",
)

ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)

FUN_RE = re.compile(
    r"^\s*(?:(?:private|public|internal|protected|override|open|final|suspend)\s+)*"
    r"fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)


def sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def detect_text(
    data: bytes,
) -> tuple[
    str,
    str,
    str,
]:
    bom = "NONE"

    if data.startswith(
        b"\xef\xbb\xbf"
    ):
        bom = "UTF8_BOM"
        data = data[3:]

    newline = (
        "CRLF"
        if b"\r\n" in data
        else "LF"
    )

    return (
        data.decode(
            "utf-8"
        ),
        bom,
        newline,
    )


def safe_line(
    text: str,
) -> tuple[
    str,
    bool,
]:
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


def brace_delta(
    line: str,
) -> int:
    # Good enough for source-context boundaries; strings in these functions are
    # still preserved verbatim and the result is checked against known targets.
    return (
        line.count(
            "{"
        )
        - line.count(
            "}"
        )
    )


def function_ranges(
    lines: list[str],
) -> dict[
    str,
    tuple[
        int,
        int,
    ],
]:
    starts = []

    for index, line in enumerate(
        lines,
        1,
    ):
        match = FUN_RE.match(
            line
        )

        if match:
            starts.append(
                (
                    index,
                    match.group(
                        1
                    ),
                )
            )

    result = {}

    for start, name in starts:
        depth = 0
        opened = False
        end = start

        for line_no in range(
            start,
            len(
                lines
            )
            + 1,
        ):
            line = lines[
                line_no - 1
            ]
            delta = brace_delta(
                line
            )

            if "{" in line:
                opened = True

            depth += delta
            end = line_no

            if (
                opened
                and depth <= 0
            ):
                break

        result[
            name
        ] = (
            start,
            end,
        )

    return result


def extract_block(
    lines: list[str],
    start: int,
    end: int,
) -> dict[
    str,
    Any,
]:
    rendered = []
    redacted = False

    for line in lines[
        start - 1:
        end
    ]:
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

    raw = "\n".join(
        lines[
            start - 1:
            end
        ]
    ).encode(
        "utf-8"
    )

    return {
        "start_line": start,
        "end_line": end,
        "raw_segment_sha256": sha256_bytes(
            raw
        ),
        "redaction_applied": redacted,
        "text": "\n".join(
            rendered
        ),
    }


def build_report(
    root: Path,
) -> dict[
    str,
    Any,
]:
    main_path = (
        root
        / MAIN_REL
    )
    manifest_path = (
        root
        / MANIFEST_REL
    )

    main_data = main_path.read_bytes()
    manifest_data = manifest_path.read_bytes()

    main_text, main_bom, main_newline = (
        detect_text(
            main_data
        )
    )
    manifest_text, manifest_bom, manifest_newline = (
        detect_text(
            manifest_data
        )
    )

    main_lines = main_text.splitlines()
    manifest_lines = manifest_text.splitlines()

    ranges = function_ranges(
        main_lines
    )

    missing_targets = sorted(
        TARGET_FUNCTIONS
        - set(
            ranges
        )
    )

    if missing_targets:
        raise RuntimeError(
            "Target Android functions missing: "
            + repr(
                missing_targets
            )
        )

    function_blocks = {}

    for name in sorted(
        TARGET_FUNCTIONS
    ):
        start, end = ranges[
            name
        ]
        function_blocks[
            name
        ] = extract_block(
            main_lines,
            start,
            end,
        )

    legacy_occurrences = []

    for line_no, line in enumerate(
        main_lines,
        1,
    ):
        folded = line.casefold()
        terms = [
            term
            for term in LEGACY_TERMS
            if term in folded
        ]

        if not terms:
            continue

        containing = [
            name
            for name, (
                start,
                end,
            )
            in ranges.items()
            if start <= line_no <= end
        ]

        safe, changed = safe_line(
            line.strip()
        )

        legacy_occurrences.append(
            {
                "line": line_no,
                "terms": terms,
                "functions": sorted(
                    containing
                ),
                "redaction_applied": changed,
                "text": safe,
            }
        )

    call_sites = []

    for target in (
        "buildGameCatalogMessage",
        "openGameStreamClient",
    ):
        pattern = re.compile(
            rf"\b{re.escape(target)}\s*\("
        )

        declaration_line = ranges[
            target
        ][0]

        for line_no, line in enumerate(
            main_lines,
            1,
        ):
            if line_no == declaration_line:
                continue

            if not pattern.search(
                line
            ):
                continue

            callers = [
                name
                for name, (
                    start,
                    end,
                )
                in ranges.items()
                if start <= line_no <= end
            ]

            safe, changed = safe_line(
                line.strip()
            )

            call_sites.append(
                {
                    "target": target,
                    "line": line_no,
                    "callers": sorted(
                        callers
                    ),
                    "redaction_applied": changed,
                    "text": safe,
                }
            )

    manifest_hits = []

    for line_no, line in enumerate(
        manifest_lines,
        1,
    ):
        if "com.limelight" not in line.casefold():
            continue

        safe, changed = safe_line(
            line.strip()
        )

        manifest_hits.append(
            {
                "line": line_no,
                "redaction_applied": changed,
                "text": safe,
            }
        )

    # Capture a bounded manifest context around every hit.
    manifest_contexts = []

    for index, hit in enumerate(
        manifest_hits,
        1,
    ):
        start = max(
            1,
            hit[
                "line"
            ]
            - 4,
        )
        end = min(
            len(
                manifest_lines
            ),
            hit[
                "line"
            ]
            + 4,
        )

        block = extract_block(
            manifest_lines,
            start,
            end,
        )
        block[
            "block"
        ] = index
        manifest_contexts.append(
            block
        )

    return {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "main_activity": {
            "path": MAIN_REL,
            "sha256": sha256_bytes(
                main_data
            ),
            "bytes": len(
                main_data
            ),
            "lines": len(
                main_lines
            ),
            "bom": main_bom,
            "newline": main_newline,
        },
        "manifest": {
            "path": MANIFEST_REL,
            "sha256": sha256_bytes(
                manifest_data
            ),
            "bytes": len(
                manifest_data
            ),
            "lines": len(
                manifest_lines
            ),
            "bom": manifest_bom,
            "newline": manifest_newline,
        },
        "function_blocks": function_blocks,
        "legacy_occurrences": legacy_occurrences,
        "call_sites": call_sites,
        "manifest_hits": manifest_hits,
        "manifest_contexts": manifest_contexts,
    }


def format_text(
    report: dict[
        str,
        Any,
    ],
) -> str:
    main = report[
        "main_activity"
    ]
    manifest = report[
        "manifest"
    ]

    lines = [
        "PrivyHub B4.2 exact Android Moonlight source-context audit",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== MAIN ACTIVITY SOURCE ===",
        f"Path: {main['path']}",
        f"SHA-256: {main['sha256']}",
        f"Bytes: {main['bytes']}",
        f"Lines: {main['lines']}",
        f"BOM: {main['bom']}",
        f"Newline: {main['newline']}",
        "",
        "=== MANIFEST SOURCE ===",
        f"Path: {manifest['path']}",
        f"SHA-256: {manifest['sha256']}",
        f"Bytes: {manifest['bytes']}",
        f"Lines: {manifest['lines']}",
        f"BOM: {manifest['bom']}",
        f"Newline: {manifest['newline']}",
        "",
        "=== LEGACY OCCURRENCES ===",
    ]

    for item in report[
        "legacy_occurrences"
    ]:
        lines.append(
            f"line={item['line']} "
            f"terms={','.join(item['terms'])} "
            f"functions={','.join(item['functions']) or '<none>'} | "
            f"{item['text']}"
        )

    lines += [
        "",
        "=== DIRECT CALL SITES ===",
    ]

    for item in report[
        "call_sites"
    ]:
        lines.append(
            f"line={item['line']} "
            f"target={item['target']} "
            f"callers={','.join(item['callers']) or '<none>'} | "
            f"{item['text']}"
        )

    lines += [
        "",
        "=== EXACT FUNCTION BLOCKS ===",
    ]

    for name in sorted(
        report[
            "function_blocks"
        ]
    ):
        block = report[
            "function_blocks"
        ][
            name
        ]

        lines += [
            "",
            (
                f"--- FUNCTION {name} "
                f"LINES {block['start_line']}-{block['end_line']} "
                f"SHA256 {block['raw_segment_sha256']} "
                f"REDACTED {block['redaction_applied']} ---"
            ),
            block[
                "text"
            ],
            f"--- END FUNCTION {name} ---",
        ]

    lines += [
        "",
        "=== MANIFEST HITS ===",
    ]

    for hit in report[
        "manifest_hits"
    ]:
        lines.append(
            f"line={hit['line']} | {hit['text']}"
        )

    lines += [
        "",
        "=== EXACT MANIFEST CONTEXTS ===",
    ]

    for block in report[
        "manifest_contexts"
    ]:
        lines += [
            "",
            (
                f"--- MANIFEST BLOCK {block['block']} "
                f"LINES {block['start_line']}-{block['end_line']} "
                f"SHA256 {block['raw_segment_sha256']} "
                f"REDACTED {block['redaction_applied']} ---"
            ),
            block[
                "text"
            ],
            f"--- END MANIFEST BLOCK {block['block']} ---",
        ]

    lines += [
        "",
        "=== DISPOSITION ===",
        "USE_EXACT_ANDROID_FUNCTION_AND_MANIFEST_CONTEXT_FOR_B4_2_REBUILD",
        "Do not remove Moonlight runtime/download/setup artifacts yet.",
    ]

    return (
        "\n".join(
            lines
        )
        + "\n"
    )


def self_test() -> int:
    sample = [
        "private fun openGameStreamClient() {",
        '    val x = "com.limelight"',
        "}",
        "",
        "private fun caller() {",
        "    openGameStreamClient()",
        "}",
    ]

    ranges = function_ranges(
        sample
    )

    assert ranges[
        "openGameStreamClient"
    ] == (
        1,
        3,
    )
    assert ranges[
        "caller"
    ] == (
        5,
        7,
    )

    value, redacted = safe_line(
        ".".join(
            (
                "192",
                "0",
                "2",
                "5",
            )
        )
    )
    assert redacted is True
    assert value == "<redacted-address>"

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

    for relative in (
        MAIN_REL,
        MANIFEST_REL,
    ):
        if not (
            root
            / relative
        ).is_file():
            raise SystemExit(
                f"Missing current Android source: {relative}"
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

    text_path = (
        out_dir
        / "b4_2_android_source_context.txt"
    )
    json_path = (
        out_dir
        / "b4_2_android_source_context.json"
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
