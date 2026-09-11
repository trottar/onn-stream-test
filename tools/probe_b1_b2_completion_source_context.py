#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_b2_completion_source_context_v1"
CLASSIFICATION = "B1_B2_COMPLETION_SOURCE_CONTEXT_CAPTURED"

TARGETS = {
    "diagnostics_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "diagnostics/DiagnosticsActivity.kt"
    ),
    "health_model": "companion/diagnostics/health_model.py",
    "runtime_health": "companion/diagnostics/runtime_health.py",
    "client_feedback": "companion/diagnostics/client_feedback.py",
    "companion_service": "companion/privyhub_service.py",
    "debug_bundle": "tools/privyhub_debug_bundle.py",
    "debug_harness": "tools/run_privyhub_debug.ps1",
}

SEARCH_ROOTS = (
    "tools",
    "companion",
    "PrivyHub/app/src/main/java",
)

EXCLUDED_PARTS = {
    "archive",
    "build",
    ".gradle",
    "__pycache__",
    "logs",
    "docs",
}

ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)

METHOD_PATTERNS = {
    "diagnostics_build_content": re.compile(
        r"^\s*private\s+fun\s+buildContent\s*\(",
        re.MULTILINE,
    ),
    "diagnostics_refresh_health": re.compile(
        r"^\s*private\s+fun\s+refreshHealth\s*\(",
        re.MULTILINE,
    ),
    "diagnostics_format_self_test": re.compile(
        r"^\s*private\s+fun\s+formatSelfTest\s*\(",
        re.MULTILINE,
    ),
    "debug_bundle_main": re.compile(
        r"^\s*def\s+main\s*\(",
        re.MULTILINE,
    ),
}

SAFE_KEYWORDS = (
    "diagnostics",
    "health",
    "event",
    "history",
    "bundle",
    "share_me",
    "storage",
    "writable",
    "adb",
    "controller",
    "audio",
    "retroarch",
    "client_feedback",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )


def redact(line: str) -> str:
    line = ADDRESS_RE.sub(
        "<redacted-address>",
        line,
    )
    return MAC_RE.sub(
        "<redacted-address>",
        line,
    )


def balanced_brace_excerpt(
    text: str,
    match_start: int,
    *,
    max_lines: int = 360,
) -> dict[str, Any]:
    lines = text.splitlines()
    char_line = text[:match_start].count("\n")
    start_index = max(0, char_line)

    depth = 0
    started = False
    collected = []

    for index in range(start_index, len(lines)):
        line = lines[index]
        collected.append(
            {
                "line": index + 1,
                "text": redact(line),
            }
        )

        for char in line:
            if char == "{":
                depth += 1
                started = True
            elif char == "}" and started:
                depth -= 1

        if (
            started
            and depth <= 0
            and index > start_index
        ):
            break

        if len(collected) >= max_lines:
            break

    return {
        "start_line": collected[0]["line"] if collected else None,
        "end_line": collected[-1]["line"] if collected else None,
        "truncated": len(collected) >= max_lines,
        "lines": collected,
    }


def context_excerpt(
    text: str,
    line_numbers: list[int],
    *,
    radius: int = 5,
    max_blocks: int = 12,
) -> list[dict[str, Any]]:
    lines = text.splitlines()
    blocks = []
    occupied: list[tuple[int, int]] = []

    for line_no in line_numbers:
        if len(blocks) >= max_blocks:
            break

        start = max(1, line_no - radius)
        end = min(len(lines), line_no + radius)

        if any(
            not (end < prior_start or start > prior_end)
            for prior_start, prior_end in occupied
        ):
            continue

        occupied.append((start, end))
        blocks.append(
            {
                "start_line": start,
                "end_line": end,
                "lines": [
                    {
                        "line": idx,
                        "text": redact(lines[idx - 1]),
                    }
                    for idx in range(start, end + 1)
                ],
            }
        )

    return blocks


def matching_lines(
    text: str,
    terms: tuple[str, ...],
) -> list[int]:
    folded_terms = tuple(
        term.casefold()
        for term in terms
    )
    result = []

    for index, line in enumerate(
        text.splitlines(),
        1,
    ):
        folded = line.casefold()
        if any(term in folded for term in folded_terms):
            result.append(index)

    return result


def inspect_target(
    root: Path,
    rel: str,
) -> dict[str, Any]:
    path = root / rel

    if not path.is_file():
        return {
            "path": rel,
            "exists": False,
        }

    text = read_text(path)
    return {
        "path": rel,
        "exists": True,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "lines": len(text.splitlines()),
    }


def extract_methods(
    root: Path,
) -> dict[str, Any]:
    result = {}

    activity_path = root / TARGETS["diagnostics_activity"]
    if activity_path.is_file():
        text = read_text(activity_path)

        for key in (
            "diagnostics_build_content",
            "diagnostics_refresh_health",
            "diagnostics_format_self_test",
        ):
            match = METHOD_PATTERNS[key].search(text)
            result[key] = (
                balanced_brace_excerpt(
                    text,
                    match.start(),
                )
                if match
                else None
            )

    bundle_path = root / TARGETS["debug_bundle"]
    if bundle_path.is_file():
        text = read_text(bundle_path)
        match = METHOD_PATTERNS["debug_bundle_main"].search(text)
        result["debug_bundle_main"] = (
            balanced_brace_excerpt(
                text,
                match.start(),
                max_lines=300,
            )
            if match
            else None
        )

    return result


def integration_context(
    root: Path,
) -> dict[str, Any]:
    queries = {
        "service_diagnostics_routes": (
            TARGETS["companion_service"],
            (
                "/diagnostics",
                "client-health",
                "client_health",
                "health",
            ),
        ),
        "health_event_construction": (
            TARGETS["health_model"],
            (
                "event_code",
                "_component(",
                "components",
                "overall",
            ),
        ),
        "runtime_health_builder": (
            TARGETS["runtime_health"],
            (
                "build",
                "health",
                "client_feedback",
                "games",
            ),
        ),
        "client_feedback_store": (
            TARGETS["client_feedback"],
            (
                "submit",
                "update",
                "snapshot",
                "feedback",
                "lock",
            ),
        ),
        "bundle_entrypoints": (
            TARGETS["debug_bundle"],
            (
                "main(",
                "argparse",
                "SHARE_ME",
                "manifest",
                "zip",
                "output",
            ),
        ),
    }

    result = {}

    for name, (rel, terms) in queries.items():
        path = root / rel

        if not path.is_file():
            result[name] = {
                "path": rel,
                "exists": False,
                "blocks": [],
            }
            continue

        text = read_text(path)
        lines = matching_lines(
            text,
            tuple(terms),
        )

        result[name] = {
            "path": rel,
            "exists": True,
            "blocks": context_excerpt(
                text,
                lines,
                radius=4,
                max_blocks=10,
            ),
        }

    return result


def repo_candidates(
    root: Path,
) -> dict[str, Any]:
    categories = {
        "adb": (
            "adb",
            "wireless debugging",
        ),
        "storage": (
            "writable",
            "write test",
            "disk_usage",
            "free space",
            "statvfs",
        ),
        "bundle": (
            "privyhub_debug_bundle",
            "share_me",
            "collect diagnostics",
        ),
        "event_history": (
            "event_history",
            "diagnostic_event",
            "deque(",
            "maxlen=",
        ),
    }

    suffixes = {
        ".py",
        ".ps1",
        ".kt",
        ".kts",
        ".xml",
        ".json",
        ".md",
    }

    output: dict[str, Any] = {
        key: []
        for key in categories
    }

    for rel_root in SEARCH_ROOTS:
        search_root = root / rel_root
        if not search_root.exists():
            continue

        for path in search_root.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in suffixes:
                continue

            if any(
                part.casefold() in EXCLUDED_PARTS
                for part in path.parts
            ):
                continue

            try:
                text = read_text(path)
            except OSError:
                continue

            folded = text.casefold()

            for category, terms in categories.items():
                hits = [
                    term
                    for term in terms
                    if term.casefold() in folded
                ]

                if not hits:
                    continue

                try:
                    rel = path.relative_to(root).as_posix()
                except ValueError:
                    continue

                output[category].append(
                    {
                        "path": rel,
                        "sha256": sha256(path),
                        "hits": hits,
                        "lines": matching_lines(
                            text,
                            tuple(hits),
                        )[:16],
                    }
                )

    for category in output:
        output[category].sort(
            key=lambda item: (
                -len(item["hits"]),
                item["path"].casefold(),
            )
        )
        output[category] = output[category][:30]

    return output


def semantic_assessment(
    methods: dict[str, Any],
    candidates: dict[str, Any],
) -> dict[str, Any]:
    self_test = methods.get(
        "diagnostics_format_self_test"
    )

    self_test_text = ""

    if isinstance(self_test, dict):
        self_test_text = "\n".join(
            row["text"]
            for row in self_test.get(
                "lines",
                []
            )
            if isinstance(row, dict)
        )

    folded = self_test_text.casefold()

    generic_component_loop = (
        "components.length()" in self_test_text
        and "components.optJSONObject" in self_test_text
        and 'item.optString(' in self_test_text
        and '"component"' in self_test_text
        and 'item.optString(' in self_test_text
        and '"severity"' in self_test_text
    )

    explicit_storage = any(
        token in folded
        for token in (
            "writable",
            "storage",
            "write test",
        )
    )

    explicit_adb = "adb" in folded

    return {
        "self_test_generically_checks_all_health_components":
            generic_component_loop,
        "audio_controller_retroarch_need_duplicate_explicit_checks":
            False if generic_component_loop else None,
        "dedicated_storage_check_present":
            explicit_storage,
        "dedicated_adb_check_present":
            explicit_adb,
        "adb_candidate_files_found":
            len(candidates.get("adb", [])),
        "storage_candidate_files_found":
            len(candidates.get("storage", [])),
        "bundle_candidate_files_found":
            len(candidates.get("bundle", [])),
        "event_history_candidate_files_found":
            len(candidates.get("event_history", [])),
    }


def format_excerpt(
    label: str,
    excerpt: dict[str, Any] | None,
) -> list[str]:
    lines = [
        label
    ]

    if not isinstance(excerpt, dict):
        lines.append("<not found>")
        return lines

    lines.append(
        f"Lines {excerpt.get('start_line')}-{excerpt.get('end_line')} "
        f"truncated={excerpt.get('truncated', False)}"
    )

    for row in excerpt.get("lines", []):
        lines.append(
            f"{row['line']:05d}: {row['text']}"
        )

    return lines


def format_blocks(
    label: str,
    item: dict[str, Any],
) -> list[str]:
    lines = [label]

    blocks = item.get("blocks", [])
    if not blocks:
        lines.append("<none>")
        return lines

    for index, block in enumerate(blocks, 1):
        lines.append(
            f"-- block {index} lines "
            f"{block['start_line']}-{block['end_line']} --"
        )
        for row in block["lines"]:
            lines.append(
                f"{row['line']:05d}: {row['text']}"
            )

    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sample = """
        val components = root.optJSONArray("components")
        for (index in 0 until components.length()) {
            val item = components.optJSONObject(index)
            check(
                item.optString("component", "unknown"),
                item.optString("severity", "info"),
                item.optString("event_code", "<none>")
            )
        }
        """
        fake = {
            "diagnostics_format_self_test": {
                "lines": [
                    {
                        "line": index,
                        "text": line,
                    }
                    for index, line in enumerate(
                        sample.splitlines(),
                        1,
                    )
                ]
            }
        }
        assessment = semantic_assessment(
            fake,
            {
                "adb": [],
                "storage": [],
                "bundle": [],
                "event_history": [],
            },
        )
        assert assessment[
            "self_test_generically_checks_all_health_components"
        ] is True
        return 0

    root = Path(args.root).resolve()

    targets = {
        name: inspect_target(root, rel)
        for name, rel in TARGETS.items()
    }
    methods = extract_methods(root)
    context = integration_context(root)
    candidates = repo_candidates(root)
    assessment = semantic_assessment(
        methods,
        candidates,
    )

    report = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "targets": targets,
        "methods": methods,
        "integration_context": context,
        "repo_candidates": candidates,
        "semantic_assessment": assessment,
        "next_step": (
            "DESIGN_ONE_COHERENT_B1_B2_COMPLETION_PATCH_FROM_EXACT_CONTEXT"
        ),
    }

    out_dir = root / "logs/diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "b1_b2_completion_source_context.json"
    text_path = out_dir / "b1_b2_completion_source_context.txt"

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
        "PrivyHub Phase B1/B2 completion source-context audit",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== EXACT SOURCE HASHES ===",
    ]

    for name, item in targets.items():
        if not item.get("exists", False):
            lines.append(
                f"{name}: MISSING path={item['path']}"
            )
        else:
            lines.append(
                f"{name}: sha256={item['sha256']} "
                f"bytes={item['bytes']} lines={item['lines']} "
                f"path={item['path']}"
            )

    lines += [
        "",
        "=== SEMANTIC SELF-TEST ASSESSMENT ===",
    ]

    for key, value in assessment.items():
        lines.append(
            f"{key}: {value}"
        )

    lines += [
        "",
        *format_excerpt(
            "=== DIAGNOSTICS buildContent ===",
            methods.get("diagnostics_build_content"),
        ),
        "",
        *format_excerpt(
            "=== DIAGNOSTICS refreshHealth ===",
            methods.get("diagnostics_refresh_health"),
        ),
        "",
        *format_excerpt(
            "=== DIAGNOSTICS formatSelfTest ===",
            methods.get("diagnostics_format_self_test"),
        ),
        "",
        *format_excerpt(
            "=== DEBUG BUNDLE main ===",
            methods.get("debug_bundle_main"),
        ),
        "",
    ]

    for key, item in context.items():
        lines += [
            *format_blocks(
                f"=== CONTEXT {key} ===",
                item,
            ),
            "",
        ]

    for category, items in candidates.items():
        lines.append(
            f"=== REPO CANDIDATES {category.upper()} ==="
        )

        if not items:
            lines.append("<none>")
        else:
            for item in items:
                lines.append(
                    f"{item['path']} | sha256={item['sha256']} | "
                    f"hits={','.join(item['hits'])} | "
                    f"lines={','.join(str(v) for v in item['lines'])}"
                )
        lines.append("")

    lines += [
        "=== NEXT STEP ===",
        "DESIGN_ONE_COHERENT_B1_B2_COMPLETION_PATCH_FROM_EXACT_CONTEXT",
        "",
        "Return this file before production implementation.",
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(CLASSIFICATION)
    print("Text:", text_path)
    print("JSON:", json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
