from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_git(root: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout.rstrip()


def is_tracked(root: Path, relative: str) -> bool:
    code, _ = run_git(root, "ls-files", "--error-unmatch", "--", relative)
    return code == 0


def file_state(root: Path, relative: str) -> dict[str, object]:
    full = root / Path(relative)
    exists = full.is_file()
    return {
        "path": relative,
        "exists": exists,
        "tracked": is_tracked(root, relative) if exists else False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PrivyHub checkpoint source tracking and repo hygiene")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent
    if not (root / ".git").exists():
        raise SystemExit(f"Repository .git directory not found at {root}")

    code, head = run_git(root, "rev-parse", "HEAD")
    if code != 0:
        raise SystemExit(f"Unable to resolve git HEAD: {head}")
    head = head.strip()

    code, status_text = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if code != 0:
        raise SystemExit(f"git status failed: {status_text}")
    status_lines = [line for line in status_text.splitlines() if line]

    diff_code, diff_text = run_git(root, "diff", "--check")
    cached_code, cached_text = run_git(root, "diff", "--cached", "--check")

    code, tracked_text = run_git(root, "ls-files")
    if code != 0:
        raise SystemExit(f"git ls-files failed: {tracked_text}")
    tracked = [line for line in tracked_text.splitlines() if line]

    critical_paths = [
        "companion/plugins/games.py",
        "companion/games/__init__.py",
        "companion/native_stream.py",
        "companion/native_session_io.py",
        "companion/native_fec_relay.py",
        "companion/native_wgc_bridge.py",
        "companion/process_audio/Program.cs",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeAudioReceiver.kt",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeControllerSender.kt",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt",
    ]
    critical = [file_state(root, p) for p in critical_paths]

    diagnostic_paths = [
        "companion/diagnostics/udp_transport_probe.py",
        "companion/diagnostics/udp_reverse_transport_probe.py",
        "tools/run_udp_transport_probe.ps1",
        "tools/run_udp_loopback_probe.ps1",
        "tools/run_udp_reverse_transport_probe.ps1",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/diagnostics/UdpTransportProbeActivity.kt",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/diagnostics/UdpLoopbackProbeActivity.kt",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/diagnostics/UdpReverseTransportProbeActivity.kt",
    ]
    diagnostics = [file_state(root, p) for p in diagnostic_paths]

    game_imports: list[dict[str, object]] = []
    games_plugin = root / "companion/plugins/games.py"
    if games_plugin.is_file():
        text = games_plugin.read_text(encoding="utf-8", errors="replace")
        modules = re.findall(r"(?m)^from\s+games\.([A-Za-z0-9_]+)\s+import\s+", text)
        seen: set[str] = set()
        for module in modules:
            if module in seen:
                continue
            seen.add(module)
            relative = f"companion/games/{module}.py"
            state = file_state(root, relative)
            game_imports.append(
                {
                    "module": f"games.{module}",
                    "expected_path": relative,
                    "exists": state["exists"],
                    "tracked": state["tracked"],
                }
            )

    tracked_runtime_artifacts = [
        p for p in tracked if re.match(r"^(runtime|logs|archive|data)/", p)
    ]
    tracked_game_content_candidates = [
        p
        for p in tracked
        if p.startswith("games/")
        and not p.endswith(".py")
        and not re.match(r"^games/README(?:\.md)?$", p)
    ]
    legacy_refs = [p for p in tracked if re.search(r"sunshine|moonlight", p, re.I)]

    errors: list[str] = []
    warnings: list[str] = []

    if diff_code != 0:
        errors.append("git diff --check reported whitespace/errors")
    if cached_code != 0:
        errors.append("git diff --cached --check reported whitespace/errors")
    if any(not item["exists"] or not item["tracked"] for item in critical):
        errors.append("one or more critical pushed-baseline source paths are missing or untracked")
    if any(not item["exists"] or not item["tracked"] for item in game_imports):
        warnings.append("companion/games modules imported by the tracked plugin are missing or untracked")
    if any(item["exists"] and not item["tracked"] for item in diagnostics):
        warnings.append("diagnostic source exists locally but is not tracked")
    if tracked_runtime_artifacts:
        warnings.append("generated runtime/log/archive/data paths are tracked")
    if tracked_game_content_candidates:
        warnings.append("possible game/media content under games/ is tracked")
    if legacy_refs:
        warnings.append("Sunshine/Moonlight legacy files remain tracked (expected deferred cleanup)")

    report = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head": head,
        "clean_worktree": not status_lines,
        "git_status": status_lines,
        "diff_check_ok": diff_code == 0,
        "diff_check_output": diff_text,
        "cached_diff_check_ok": cached_code == 0,
        "cached_diff_check_output": cached_text,
        "critical_source": critical,
        "games_import_modules": game_imports,
        "diagnostic_source": diagnostics,
        "tracked_runtime_artifacts": tracked_runtime_artifacts,
        "tracked_game_content_candidates": tracked_game_content_candidates,
        "legacy_sunshine_moonlight_files": legacy_refs,
        "errors": errors,
        "warnings": warnings,
    }

    log_root = root / "logs/repo_audit"
    log_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = log_root / f"repo_audit_{stamp}.json"
    text_path = log_root / f"repo_audit_{stamp}.txt"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines: list[str] = [
        "PrivyHub repository checkpoint audit",
        f"HEAD: {head}",
        f"Working tree clean: {report['clean_worktree']}",
        f"git diff --check: {report['diff_check_ok']}",
        f"git diff --cached --check: {report['cached_diff_check_ok']}",
        "",
        f"Errors: {len(errors)}",
    ]
    lines.extend(f"  ERROR: {item}" for item in errors)
    lines.append(f"Warnings: {len(warnings)}")
    lines.extend(f"  WARN: {item}" for item in warnings)
    lines += ["", "companion/games imported modules:"]
    lines.extend(
        f"  {item['module']} -> {item['expected_path']} exists={item['exists']} tracked={item['tracked']}"
        for item in game_imports
    )
    lines += ["", "Diagnostic source:"]
    lines.extend(
        f"  {item['path']} tracked={item['tracked']}"
        for item in diagnostics
        if item["exists"]
    )
    lines += [
        "",
        f"Tracked runtime/log/archive/data paths: {len(tracked_runtime_artifacts)}",
        *[f"  {item}" for item in tracked_runtime_artifacts],
        f"Tracked game-content candidates: {len(tracked_game_content_candidates)}",
        *[f"  {item}" for item in tracked_game_content_candidates],
        "",
        "Git status:",
        *[f"  {item}" for item in status_lines],
        "",
        f"Saved JSON: {json_path}",
        f"Saved text: {text_path}",
    ]
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.json_only:
        print(json.dumps(report, indent=2))
    else:
        print("\n".join(lines))

    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
