#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_3_orphan_reference_audit_v1"
CLASSIFICATION = "B4_3_ORPHAN_REFERENCE_AUDIT_CAPTURED"

MAIN_REL = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "MainActivity.kt"
)
MANIFEST_REL = "PrivyHub/app/src/main/AndroidManifest.xml"
GAMES_REL = "companion/plugins/games.py"
STREAM_MANAGER_REL = "companion/games/stream_manager.py"

HELPERS = (
    "buildStreamHostMessage",
    "setGameStreamHost",
)

LEGACY_TERMS = (
    "sunshine",
    "moonlight",
    "limelight",
    "games.stream_manager",
    "streammanager",
    "stream_manager",
    "stream_host",
)

PRODUCTION_ROOTS = (
    "companion",
    "PrivyHub/app/src/main",
)

SCRIPT_ROOTS = (
    "scripts",
)

TOOL_ROOTS = (
    "tools",
)

IGNORE_PREFIXES = (
    "archive/",
    "docs/",
    "logs/",
    "runtime/",
    ".git/",
)

TEXT_SUFFIXES = {
    ".py",
    ".kt",
    ".kts",
    ".xml",
    ".ps1",
    ".bat",
    ".cmd",
    ".json",
    ".toml",
    ".ini",
    ".conf",
    ".cfg",
    ".txt",
    ".md",
}

FUN_RE = re.compile(
    r"^\s*(?:(?:private|public|internal|protected|override|open|final|suspend)\s+)*"
    r"fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)

ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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

    return value, redacted


def function_ranges(
    lines: list[str],
) -> dict[str, tuple[int, int]]:
    starts: list[tuple[int, str]] = []

    for index, line in enumerate(lines, 1):
        match = FUN_RE.match(line)
        if match:
            starts.append(
                (
                    index,
                    match.group(1),
                )
            )

    result: dict[str, tuple[int, int]] = {}

    for start, name in starts:
        depth = 0
        opened = False
        end = start

        for line_no in range(
            start,
            len(lines) + 1,
        ):
            line = lines[line_no - 1]

            if "{" in line:
                opened = True

            depth += (
                line.count("{")
                - line.count("}")
            )
            end = line_no

            if opened and depth <= 0:
                break

        result[name] = (start, end)

    return result


def helper_report(
    main_path: Path,
) -> dict[str, Any]:
    data = main_path.read_bytes()
    text = data.decode("utf-8-sig")
    lines = text.splitlines()
    ranges = function_ranges(lines)

    helpers: dict[str, Any] = {}

    for helper in HELPERS:
        helper_range = ranges.get(helper)

        definition = None
        if helper_range is not None:
            start, end = helper_range
            raw = "\n".join(
                lines[start - 1:end]
            ).encode("utf-8")

            rendered = []
            redacted = False

            for line in lines[start - 1:end]:
                safe, changed = safe_line(line)
                rendered.append(safe)
                redacted = redacted or changed

            definition = {
                "start_line": start,
                "end_line": end,
                "sha256": hashlib.sha256(
                    raw
                ).hexdigest(),
                "redaction_applied": redacted,
                "text": "\n".join(rendered),
            }

        call_pattern = re.compile(
            rf"\b{re.escape(helper)}\s*\("
        )

        declaration_line = (
            helper_range[0]
            if helper_range is not None
            else None
        )

        call_sites = []

        for line_no, line in enumerate(
            lines,
            1,
        ):
            if (
                declaration_line is not None
                and line_no == declaration_line
            ):
                continue

            if not call_pattern.search(line):
                continue

            callers = [
                name
                for name, (start, end)
                in ranges.items()
                if start <= line_no <= end
            ]

            safe, changed = safe_line(
                line.strip()
            )

            call_sites.append(
                {
                    "line": line_no,
                    "callers": sorted(callers),
                    "redaction_applied": changed,
                    "text": safe,
                }
            )

        helpers[helper] = {
            "definition_present": (
                helper_range is not None
            ),
            "definition": definition,
            "call_site_count": len(call_sites),
            "call_sites": call_sites,
        }

    return {
        "main_sha256": hashlib.sha256(
            data
        ).hexdigest(),
        "helpers": helpers,
    }


def iter_text_files(
    root: Path,
    prefix: str,
):
    base = root / prefix

    if not base.exists():
        return

    for path in base.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(root).as_posix()

        if any(
            rel.startswith(ignore)
            for ignore in IGNORE_PREFIXES
        ):
            continue

        if path.suffix.casefold() not in TEXT_SUFFIXES:
            continue

        yield rel, path


def scan_group(
    root: Path,
    prefixes: tuple[str, ...],
) -> list[dict[str, Any]]:
    results = []

    for prefix in prefixes:
        for rel, path in iter_text_files(
            root,
            prefix,
        ) or ():
            try:
                text = path.read_text(
                    encoding="utf-8-sig"
                )
            except (
                UnicodeError,
                OSError,
            ):
                continue

            for line_no, line in enumerate(
                text.splitlines(),
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

                safe, changed = safe_line(
                    line.strip()
                )

                results.append(
                    {
                        "path": rel,
                        "line": line_no,
                        "terms": sorted(set(terms)),
                        "redaction_applied": changed,
                        "text": safe,
                    }
                )

    return results


def stream_manager_importers(
    production_refs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []

    legacy_constructor = re.compile(
        r"(?<![A-Za-z0-9_])StreamManager\s*\("
    )

    for item in production_refs:
        path = item["path"]

        if path == STREAM_MANAGER_REL:
            continue

        text = item["text"]

        if (
            "games.stream_manager" in text
            or legacy_constructor.search(text)
        ):
            result.append(item)

    return result


def artifact_group(
    root: Path,
    rel: str,
) -> dict[str, Any]:
    path = root / rel

    if not path.exists():
        return {
            "path": rel,
            "exists": False,
            "files": 0,
            "bytes": 0,
        }

    if path.is_file():
        return {
            "path": rel,
            "exists": True,
            "files": 1,
            "bytes": path.stat().st_size,
        }

    file_count = 0
    total = 0

    for item in path.rglob("*"):
        if item.is_file():
            file_count += 1
            try:
                total += item.stat().st_size
            except OSError:
                pass

    return {
        "path": rel,
        "exists": True,
        "files": file_count,
        "bytes": total,
    }


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
        sample = [
            "private fun buildStreamHostMessage(json: JSONObject): String {",
            '    return "x"',
            "}",
            "",
            "private fun caller() {",
            "    println(\"native\")",
            "}",
        ]
        ranges = function_ranges(sample)
        assert ranges["buildStreamHostMessage"] == (1, 3)

        safe, redacted = safe_line(
            ".".join(
                (
                    "192",
                    "0",
                    "2",
                    "9",
                )
            )
        )
        assert redacted
        assert safe == "<redacted-address>"
        return 0

    root = Path(args.root).resolve()

    main_path = root / MAIN_REL
    manifest_path = root / MANIFEST_REL
    games_path = root / GAMES_REL
    manager_path = root / STREAM_MANAGER_REL

    for path in (
        main_path,
        manifest_path,
        games_path,
        manager_path,
    ):
        if not path.is_file():
            raise SystemExit(
                f"Required current file missing: {path.relative_to(root)}"
            )

    helpers = helper_report(main_path)
    production_refs = scan_group(
        root,
        PRODUCTION_ROOTS,
    )
    script_refs = scan_group(
        root,
        SCRIPT_ROOTS,
    )
    tool_refs = scan_group(
        root,
        TOOL_ROOTS,
    )

    manager_importers = stream_manager_importers(
        production_refs
    )

    manifest_text = manifest_path.read_text(
        encoding="utf-8-sig"
    )

    main_text = main_path.read_text(
        encoding="utf-8-sig"
    )

    b41_games_text = games_path.read_text(
        encoding="utf-8-sig"
    )

    artifact_paths = (
        "companion/games/stream_manager.py",
        "runtime/streaming/sunshine",
        "runtime/downloads/sunshine",
        "runtime/downloads/moonlight",
        "scripts/setup_sunshine_portable.ps1",
        "scripts/install_sunshine_firewall.ps1",
        "scripts/remove_sunshine_firewall.ps1",
        "scripts/open_sunshine_web_ui.ps1",
        "scripts/install_moonlight_onn.ps1",
    )

    artifacts = [
        artifact_group(
            root,
            rel,
        )
        for rel in artifact_paths
    ]

    helper_orphans = {
        name: (
            item["definition_present"]
            and item["call_site_count"] == 0
        )
        for name, item
        in helpers["helpers"].items()
    }

    product_client_edge_clean = (
        "sunshine" not in main_text.casefold()
        and "moonlight" not in main_text.casefold()
        and "com.limelight" not in main_text.casefold()
        and "com.limelight" not in manifest_text.casefold()
    )

    server_edge_clean = (
        "games.stream_manager" not in b41_games_text
        and "self._stream" not in b41_games_text
        and len(manager_importers) == 0
    )

    active_production_refs = [
        item
        for item in production_refs
        if (
            item["path"]
            not in {
                STREAM_MANAGER_REL,
            }
            and not (
                item["path"] == MAIN_REL
                and any(
                    helper in item["text"]
                    for helper in HELPERS
                )
            )
        )
    ]

    clean_cut = (
        product_client_edge_clean
        and server_edge_clean
        and all(helper_orphans.values())
    )

    disposition = (
        "B4_3_ORPHANS_CONFIRMED_PREPARE_CLEANUP_PATCH"
        if clean_cut
        else "B4_3_REMAINING_ACTIVE_REFERENCE_INSPECT_BEFORE_CLEANUP"
    )

    report = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "exact_source_hashes": {
            "main_activity": sha256(main_path),
            "manifest": sha256(manifest_path),
            "games_b4_1": sha256(games_path),
            "stream_manager": sha256(manager_path),
        },
        "helper_analysis": helpers,
        "helper_orphans": helper_orphans,
        "product_client_edge_clean": product_client_edge_clean,
        "server_edge_clean": server_edge_clean,
        "stream_manager_importers": manager_importers,
        "production_reference_count": len(production_refs),
        "active_production_reference_candidates": active_production_refs,
        "script_reference_count": len(script_refs),
        "script_references": script_refs,
        "tool_reference_count": len(tool_refs),
        "tool_references": tool_refs,
        "artifacts": artifacts,
        "disposition": disposition,
    }

    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        out_dir
        / "b4_3_orphan_reference_audit.json"
    )
    text_path = (
        out_dir
        / "b4_3_orphan_reference_audit.txt"
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

    lines = [
        "PrivyHub B4.3 orphan-reference audit",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== EXACT SOURCE HASHES ===",
        f"MainActivity: {report['exact_source_hashes']['main_activity']}",
        f"AndroidManifest: {report['exact_source_hashes']['manifest']}",
        f"B4.1 games.py: {report['exact_source_hashes']['games_b4_1']}",
        f"stream_manager.py: {report['exact_source_hashes']['stream_manager']}",
        "",
        "=== ANDROID HELPER ORPHANS ===",
    ]

    for name in HELPERS:
        item = helpers["helpers"][name]
        lines += [
            f"{name}: definition_present={item['definition_present']} "
            f"call_site_count={item['call_site_count']} "
            f"orphan={helper_orphans[name]}"
        ]

        definition = item["definition"]

        if definition is not None:
            lines += [
                (
                    f"--- HELPER {name} "
                    f"LINES {definition['start_line']}-{definition['end_line']} "
                    f"SHA256 {definition['sha256']} "
                    f"REDACTED {definition['redaction_applied']} ---"
                ),
                definition["text"],
                f"--- END HELPER {name} ---",
            ]

        for call in item["call_sites"]:
            lines.append(
                f"CALL line={call['line']} "
                f"callers={','.join(call['callers']) or '<none>'} | "
                f"{call['text']}"
            )

    lines += [
        "",
        "=== PRODUCT EDGE STATUS ===",
        f"Android Moonlight/Sunshine edge clean: {product_client_edge_clean}",
        f"Games -> stream_manager edge clean: {server_edge_clean}",
        f"stream_manager importers outside manager file: {len(manager_importers)}",
        f"Production legacy-reference count: {len(production_refs)}",
        f"Remaining active production reference candidates: {len(active_production_refs)}",
    ]

    for item in active_production_refs:
        lines.append(
            f"  {item['path']}:{item['line']} "
            f"terms={','.join(item['terms'])} | {item['text']}"
        )

    lines += [
        "",
        "=== SCRIPT REFERENCES ===",
        f"Script legacy-reference count: {len(script_refs)}",
    ]

    for item in script_refs:
        lines.append(
            f"  {item['path']}:{item['line']} "
            f"terms={','.join(item['terms'])} | {item['text']}"
        )

    lines += [
        "",
        "=== DIAGNOSTIC / TOOL REFERENCES ===",
        f"Tool legacy-reference count: {len(tool_refs)}",
        "Tool references are diagnostic/historical unless separately proven product-active.",
    ]

    for item in tool_refs[:80]:
        lines.append(
            f"  {item['path']}:{item['line']} "
            f"terms={','.join(item['terms'])} | {item['text']}"
        )

    if len(tool_refs) > 80:
        lines.append(
            f"  ... {len(tool_refs) - 80} additional tool references omitted from text; retained in JSON."
        )

    lines += [
        "",
        "=== GROUPED ARTIFACT FOOTPRINT ===",
    ]

    for item in artifacts:
        lines.append(
            f"{item['path']}: "
            f"exists={item['exists']} "
            f"files={item['files']} "
            f"bytes={item['bytes']}"
        )

    lines += [
        "",
        "=== DISPOSITION ===",
        disposition,
        "",
        "Cleanup rule:",
        "Delete only helpers/artifacts classified orphaned by this audit. "
        "Preserve RetroArch moonlight-named metadata/shaders and archives as non-targets.",
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(CLASSIFICATION)
    print("Disposition:", disposition)
    print("Text:", text_path)
    print("JSON:", json_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
