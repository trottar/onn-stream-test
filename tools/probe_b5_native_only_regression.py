#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

SCHEMA = "privyhub_b5_native_only_regression_v1"
PASS = "B5_NATIVE_ONLY_REGRESSION_RUNTIME_CONFIRMED"
FAIL = "B5_NATIVE_ONLY_REGRESSION_NOT_CONFIRMED"

BASE_URL = "http://127.0.0.1:8765"

MAIN_REL = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "MainActivity.kt"
)
MANIFEST_REL = "PrivyHub/app/src/main/AndroidManifest.xml"
GAMES_REL = "companion/plugins/games.py"

EXPECTED_MAIN_SHA = (
    "394d2b839fdb01f2988a0054b42e139e419e02207728f914e1713287992733cc"
)
EXPECTED_MANIFEST_SHA = (
    "ab1140c3230582f9dbbbf3c179d8fa08363971d9289e08442487f3849c7ac8a2"
)
EXPECTED_GAMES_SHA = (
    "f1271c865cdf88b971da4116d7eb887bf9855864ce1ae848baafc7a3452e0f9c"
)

LEGACY_TARGETS = (
    "runtime/streaming/sunshine",
    "runtime/downloads/sunshine",
    "runtime/downloads/moonlight",
    "data/games/sunshine",
    "scripts/setup_sunshine_portable.ps1",
    "scripts/install_sunshine_firewall.ps1",
    "scripts/remove_sunshine_firewall.ps1",
    "scripts/open_sunshine_web_ui.ps1",
    "scripts/install_moonlight_onn.ps1",
)

RUNTIME_MEMORY_PRE = {'docs/memory/CURRENT.md': 'e9e185135f7e5fc60ba83638e400ccf9e2fc46faafc82fa4bed54b17c9d335a2', 'docs/memory/MEMORY.md': 'c18debd515a591942b6809a900c158ceae1ab4e19dc0c2ed00e02edba003f867', 'docs/memory/handoffs/CURRENT_HANDOFF.md': '6339a6cf0d36a66ed26946473d2ea00ed447b3d72361cff750e0ca3bcf91cef0', 'docs/memory/investigations/ACTIVE.md': '17ecb14708210bb6c296ca647ef2035e796318dc73f5ddf9b31042c1a54c9ed5', 'docs/memory/roadmap/STATUS.md': '7a02e7f4655f749ac0a12c72df066ef2e5917c878d88e5e2b1d87b451521e07e', 'docs/memory/memory/2026-09-11.md': 'af7024adb7f83272ed665cee246c73f5aacf114b44da7ef3f6e15a0487fd99a4'}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def get_status() -> tuple[bool, dict[str, Any], str]:
    request = urllib.request.Request(
        BASE_URL + "/plugins/games/status",
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5.0,
        ) as response:
            raw = response.read(1024 * 1024)
    except Exception as exc:
        return False, {}, type(exc).__name__

    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        return False, {}, "INVALID_JSON"

    if not isinstance(value, dict):
        return False, {}, "NON_OBJECT_JSON"

    return True, value, ""


def native_summary(
    status: dict[str, Any],
) -> dict[str, Any]:
    native = status.get("native_stream")
    if not isinstance(native, dict):
        native = {}

    return {
        "game_active": bool(status.get("active", False)),
        "native_ready": bool(native.get("ready", False)),
        "native_active": bool(native.get("active", False)),
        "kind": native.get("kind", ""),
        "capture_backend": native.get("capture_backend", ""),
        "encoder": native.get("encoder", ""),
        "transport": native.get("transport", ""),
    }


def native_ok(summary: dict[str, Any]) -> bool:
    return (
        summary["game_active"]
        and summary["native_ready"]
        and summary["native_active"]
        and summary["kind"] == "native_stream_host"
        and summary["capture_backend"]
        == "windows_graphics_capture"
        and summary["encoder"] == "h264_nvenc"
        and summary["transport"] == "rtp_udp_xor_fec"
    )


def sunshine_running() -> tuple[bool | None, str]:
    try:
        completed = subprocess.run(
            [
                "tasklist.exe",
                "/FI",
                "IMAGENAME eq sunshine.exe",
                "/FO",
                "CSV",
                "/NH",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=8.0,
            check=False,
        )
    except Exception as exc:
        return None, type(exc).__name__

    if completed.returncode != 0:
        return None, "TASKLIST_FAILED"

    running = any(
        line.strip().casefold().startswith(
            '"sunshine.exe"'
        )
        for line in completed.stdout.splitlines()
    )

    return running, ""


def snapshot_files(root: Path) -> dict[str, dict[str, Any]]:
    if not root.exists():
        return {}

    result: dict[str, dict[str, Any]] = {}

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        result[rel] = {
            "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha_file(path),
        }

    return result


def changed_file_count(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> int:
    keys = set(before) | set(after)
    return sum(
        1
        for key in keys
        if before.get(key) != after.get(key)
    )


def yes_no(
    prompt: str,
    *,
    input_fn: Callable[[str], str] = input,
) -> bool:
    while True:
        value = input_fn(
            prompt + " [y/n]: "
        ).strip().casefold()

        if value in ("y", "yes"):
            return True

        if value in ("n", "no"):
            return False

        print("Please answer y or n.")


def wait_enter(
    prompt: str,
    *,
    input_fn: Callable[[str], str] = input,
) -> None:
    input_fn(prompt + "\nPress Enter when complete: ")


def poll_for(
    predicate: Callable[[dict[str, Any]], bool],
    *,
    attempts: int = 12,
    delay: float = 0.75,
) -> tuple[bool, dict[str, Any], str]:
    last: dict[str, Any] = {}
    error = ""

    for _ in range(attempts):
        ok, status, error = get_status()

        if ok:
            last = status
            if predicate(status):
                return True, status, ""

        time.sleep(delay)

    return False, last, error


def update_memory_on_pass(
    root: Path,
    evidence: dict[str, Any],
) -> tuple[bool, str]:
    for rel, expected in RUNTIME_MEMORY_PRE.items():
        path = root / rel

        if (
            not path.is_file()
            or sha_file(path) != expected
        ):
            return (
                False,
                f"{rel}: runtime durable-memory predecessor mismatch",
            )

    manifest_path = root / "docs/memory/manifest.json"

    try:
        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        return False, f"manifest read failed: {type(exc).__name__}"

    if (
        manifest.get("current_step")
        != "B5 native-only regression runtime validation"
    ):
        return (
            False,
            "durable-memory manifest is not at B5 runtime validation",
        )

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = (
        root
        / "archive"
        / "patch_backups"
        / "privyhub_b5_runtime_evidence"
        / stamp
    )

    originals: dict[str, bytes] = {}

    evidence_rel = (
        "docs/memory/evidence/"
        "B5_NATIVE_ONLY_REGRESSION_2026-09-11.md"
    )
    affected = [
        *RUNTIME_MEMORY_PRE.keys(),
        evidence_rel,
        "docs/memory/manifest.json",
    ]

    for rel in affected:
        path = root / rel

        if path.exists():
            originals[rel] = path.read_bytes()
            target = backup / rel
            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            target.write_bytes(
                originals[rel]
            )

    try:
        evidence_path = root / evidence_rel
        evidence_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        evidence_md = (
            "---\n"
            "memory_schema: 1\n"
            "as_of: 2026-09-11\n"
            "baseline_commit: "
            "6b7c74f417e2ef14e252b9ea19afc16bdefaa50a\n"
            "---\n\n"
            "# B5 native-only regression\n\n"
            f"Classification: `{PASS}`\n\n"
            "Objective evidence:\n"
            f"- native session initial: {evidence['initial_native_ok']};\n"
            f"- post-profile native host status (informational): {evidence['post_profile_native_ok']};\n"
            f"- Sunshine process absent: {evidence['sunshine_absent']};\n"
            f"- savestate files changed after Save: {evidence['savestate_changed_files']};\n"
            f"- cheat/profile storage files present: {evidence['profile_file_count']};\n"
            f"- game inactive after End: {evidence['teardown_game_inactive']};\n"
            f"- native stream inactive after End: {evidence['teardown_native_inactive']}.\n\n"
            "Operator confirmations:\n"
            f"- picture: {evidence['picture_ok']};\n"
            f"- audio: {evidence['audio_ok']};\n"
            f"- controller: {evidence['controller_ok']};\n"
            f"- pause/resume: {evidence['pause_resume_ok']};\n"
            f"- Load restored expected state: {evidence['load_ok']};\n"
            f"- existing cheat/mod/profile path: {evidence['profile_ok']}.\n\n"
            "Conclusion:\n"
            "Games passed the focused post-legacy-removal regression using only "
            "the PrivyHub native streaming architecture. Proceed to B6 clean-native "
            "repository audit/checkpoint.\n"
        )

        evidence_path.write_text(
            evidence_md,
            encoding="utf-8",
            newline="\n",
        )

        appends = {
            "docs/memory/CURRENT.md": (
                "\n## B5 runtime validated / B6 active\n\n"
                "`B5_NATIVE_ONLY_REGRESSION_RUNTIME_CONFIRMED`.\n\n"
                "Focused post-removal regression passed: native launch/stream, "
                "picture, audio, controller, pause/resume, Save/Load, existing "
                "cheat/mod/profile path, and End/teardown.\n\n"
                "Next: B6 clean-native repository audit/checkpoint/push.\n"
            ),
            "docs/memory/MEMORY.md": (
                "\n## B5 clean-native runtime proof\n\n"
                "After complete Sunshine/Moonlight removal, a representative Games "
                "session passed the full focused dependency-removal regression. "
                "Treat the PrivyHub native WGC/NVENC/UDP-FEC path as the only "
                "validated active Games streaming architecture.\n"
            ),
            "docs/memory/handoffs/CURRENT_HANDOFF.md": (
                "\n## B6 next\n\n"
                "B5 native-only regression is runtime validated. Begin B6 repository "
                "audit: verify clean legacy dependency state, diagnostics/memory "
                "consistency, source-control boundary, then checkpoint/push.\n"
            ),
            "docs/memory/investigations/ACTIVE.md": (
                "\n## B5 result\n\n"
                "**COMPLETE / RUNTIME VALIDATED** — focused native-only regression "
                "passed after legacy removal. B6 is next.\n"
            ),
            "docs/memory/roadmap/STATUS.md": (
                "\n## B5 complete\n\n"
                "**RUNTIME VALIDATED** — native-only dependency-removal regression "
                "passed. B6 clean-native checkpoint is now active.\n"
            ),
            "docs/memory/memory/2026-09-11.md": (
                "\n## B5 runtime result\n\n"
                "Focused native-only regression passed after B4 cleanup, including "
                "launch/stream, audio/controller, pause/resume, Save/Load, one "
                "existing cheat/mod/profile path, and End/teardown. Proceed to B6.\n"
            ),
        }

        for rel, extra in appends.items():
            path = root / rel
            path.write_text(
                path.read_text(encoding="utf-8") + extra,
                encoding="utf-8",
                newline="\n",
            )

        entries = {
            item["path"]: item
            for item in manifest.get("files", [])
            if (
                isinstance(item, dict)
                and isinstance(item.get("path"), str)
            )
        }

        changed = [
            *RUNTIME_MEMORY_PRE.keys(),
            evidence_rel,
        ]

        for rel in changed:
            path = root / rel
            memory_rel = rel.replace(
                "docs/memory/",
                "",
                1,
            )
            data = path.read_bytes()
            entries[memory_rel] = {
                "path": memory_rel,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }

        manifest["files"] = [
            entries[key]
            for key in sorted(entries)
        ]
        manifest["as_of"] = "2026-09-11"
        manifest["current_phase"] = "Phase B"
        manifest["current_step"] = (
            "B6 clean-native repository audit/checkpoint"
        )
        manifest["b5_status"] = (
            "B5 native-only regression runtime confirmed"
        )
        manifest["b6_status"] = "ACTIVE"
        manifest["durable_memory_updated"] = True
        manifest["production_behavior_changed"] = False
        manifest["android_behavior_changed"] = False
        manifest["streaming_behavior_changed"] = False

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        return True, ""

    except Exception as exc:
        for rel, data in originals.items():
            path = root / rel
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            path.write_bytes(data)

        evidence_path = root / evidence_rel
        if evidence_rel not in originals:
            evidence_path.unlink(
                missing_ok=True
            )

        return (
            False,
            f"runtime durable-memory update rolled back: {type(exc).__name__}: {exc}",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        assert changed_file_count(
            {"a": {"sha256": "1"}},
            {"a": {"sha256": "2"}},
        ) == 1
        assert changed_file_count({}, {}) == 0
        return 0

    root = Path(args.root).resolve()
    out_dir = root / "logs" / "games"
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    text_path = (
        out_dir
        / "b5_native_only_regression.txt"
    )
    json_path = (
        out_dir
        / "b5_native_only_regression.json"
    )

    evidence: dict[str, Any] = {
        "schema": SCHEMA,
        "classification": FAIL,
        "production_files_modified_by_harness": "NONE",
        "network_addresses_collected_or_logged": "NONE",
    }

    # Exact clean-native source / artifact predecessor.
    source_ok = (
        (root / MAIN_REL).is_file()
        and sha_file(root / MAIN_REL) == EXPECTED_MAIN_SHA
        and (root / MANIFEST_REL).is_file()
        and sha_file(root / MANIFEST_REL)
        == EXPECTED_MANIFEST_SHA
        and (root / GAMES_REL).is_file()
        and sha_file(root / GAMES_REL)
        == EXPECTED_GAMES_SHA
    )
    legacy_absent = all(
        not (root / rel).exists()
        for rel in LEGACY_TARGETS
    )

    evidence["source_hashes_unchanged"] = source_ok
    evidence["legacy_project_artifacts_absent"] = legacy_absent

    sunshine, sunshine_error = sunshine_running()
    evidence["sunshine_absent"] = sunshine is False
    evidence["sunshine_check_error"] = sunshine_error

    if (
        not source_ok
        or not legacy_absent
        or sunshine is not False
    ):
        evidence["failure_stage"] = "clean-native-preflight"
        json_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        text_path.write_text(
            "PrivyHub B5 native-only regression\n"
            f"Classification: {FAIL}\n"
            f"Schema: {SCHEMA}\n"
            "Failure stage: clean-native-preflight\n"
            f"Source hashes unchanged: {source_ok}\n"
            f"Legacy project artifacts absent: {legacy_absent}\n"
            f"Sunshine process absent: {sunshine is False}\n"
            f"Sunshine check error: {sunshine_error or '<none>'}\n",
            encoding="utf-8",
            newline="\n",
        )
        print(FAIL)
        print("Text:", text_path)
        return 1

    print("")
    print("B5 Native-Only Regression")
    print("=========================")
    print(
        "Use one representative game. This is a focused post-removal regression."
    )
    print("")

    wait_enter(
        "From the PrivyHub Games library, launch the representative game normally."
    )

    active_ok, active_status, active_error = poll_for(
        lambda value: native_ok(
            native_summary(value)
        )
    )

    initial = native_summary(active_status)
    evidence["initial_status_error"] = active_error
    evidence["initial_native"] = initial
    evidence["initial_native_ok"] = active_ok and native_ok(initial)

    if not evidence["initial_native_ok"]:
        evidence["failure_stage"] = "library-launch-native-stream"
        json_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        text_path.write_text(
            "PrivyHub B5 native-only regression\n"
            f"Classification: {FAIL}\n"
            f"Schema: {SCHEMA}\n"
            "Failure stage: library-launch-native-stream\n"
            f"Companion status error: {active_error or '<none>'}\n"
            f"Game active: {initial['game_active']}\n"
            f"Native ready: {initial['native_ready']}\n"
            f"Native active: {initial['native_active']}\n"
            f"Kind: {initial['kind']}\n"
            f"Capture: {initial['capture_backend']}\n"
            f"Encoder: {initial['encoder']}\n"
            f"Transport: {initial['transport']}\n",
            encoding="utf-8",
            newline="\n",
        )
        print(FAIL)
        print("Text:", text_path)
        return 1

    evidence["picture_ok"] = yes_no(
        "Is the game picture visible and updating normally in the native fullscreen client?"
    )
    evidence["audio_ok"] = yes_no(
        "Is normal game audio audible?"
    )
    evidence["controller_ok"] = yes_no(
        "Does the controller respond normally in the game?"
    )

    wait_enter(
        "Pause the game through the normal PrivyHub game controls, then resume it."
    )
    evidence["pause_resume_ok"] = yes_no(
        "Did pause and resume both behave normally?"
    )

    state_root = root / "data/games/retroarch/states"
    states_before = snapshot_files(state_root)

    wait_enter(
        "Use the normal PrivyHub Save action to save the current game state to a slot."
    )

    states_after = snapshot_files(state_root)
    state_delta = changed_file_count(
        states_before,
        states_after,
    )
    evidence["savestate_changed_files"] = state_delta
    evidence["save_file_delta_ok"] = state_delta > 0

    wait_enter(
        "Change something visible in the game, then use the normal PrivyHub Load action for the state you just saved."
    )
    evidence["load_ok"] = yes_no(
        "Did Load restore the expected saved state?"
    )

    profile_root = (
        root
        / "data/games/retroarch/cheat_profiles"
    )
    profile_files = snapshot_files(
        profile_root
    )
    evidence["profile_file_count"] = len(
        profile_files
    )
    evidence["profile_storage_present"] = (
        len(profile_files) > 0
    )

    wait_enter(
        "Exercise one existing cheat/mod/profile path. The known isolated cheat profile from Phase A is acceptable. Confirm its expected behavior, then return to an active native game stream."
    )
    evidence["profile_ok"] = yes_no(
        "Did that existing cheat/mod/profile path behave normally without disturbing the normal game path?"
    )

    post_profile_ok, post_profile_status, post_profile_error = poll_for(
        lambda value: native_ok(
            native_summary(value)
        )
    )
    post_profile = native_summary(
        post_profile_status
    )
    evidence["post_profile_status_error"] = post_profile_error
    evidence["post_profile_native"] = post_profile
    evidence["post_profile_native_ok"] = (
        post_profile_ok
        and native_ok(post_profile)
    )

    wait_enter(
        "Use the normal End Game action and wait for the game/client session to close."
    )

    teardown_ok, teardown_status, teardown_error = poll_for(
        lambda value: (
            not bool(value.get("active", False))
            and not bool(
                (
                    value.get("native_stream")
                    if isinstance(
                        value.get("native_stream"),
                        dict,
                    )
                    else {}
                ).get("active", False)
            )
        ),
        attempts=16,
        delay=0.75,
    )

    teardown = native_summary(
        teardown_status
    )
    evidence["teardown_status_error"] = teardown_error
    evidence["teardown"] = teardown
    evidence["teardown_game_inactive"] = (
        not teardown["game_active"]
    )
    evidence["teardown_native_inactive"] = (
        not teardown["native_active"]
    )
    evidence["teardown_ok"] = (
        teardown_ok
        and evidence["teardown_game_inactive"]
        and evidence["teardown_native_inactive"]
    )

    required = {
        "source_hashes_unchanged": source_ok,
        "legacy_project_artifacts_absent": legacy_absent,
        "sunshine_absent": sunshine is False,
        "initial_native_ok": evidence["initial_native_ok"],
        "picture_ok": evidence["picture_ok"],
        "audio_ok": evidence["audio_ok"],
        "controller_ok": evidence["controller_ok"],
        "pause_resume_ok": evidence["pause_resume_ok"],
        "save_file_delta_ok": evidence["save_file_delta_ok"],
        "load_ok": evidence["load_ok"],
        "profile_storage_present": evidence["profile_storage_present"],
        "profile_ok": evidence["profile_ok"],
        "teardown_ok": evidence["teardown_ok"],
    }

    evidence["required_checks"] = required
    functional_pass = all(required.values())

    if functional_pass:
        memory_ok, memory_error = update_memory_on_pass(
            root,
            evidence,
        )
    else:
        memory_ok, memory_error = False, "not attempted because regression checks did not all pass"

    evidence["durable_memory_updated"] = memory_ok
    evidence["durable_memory_error"] = memory_error

    confirmed = functional_pass and memory_ok
    evidence["classification"] = (
        PASS if confirmed else FAIL
    )

    json_path.write_text(
        json.dumps(
            evidence,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    failed = [
        name
        for name, value in required.items()
        if not value
    ]

    lines = [
        "PrivyHub B5 native-only regression",
        f"Classification: {evidence['classification']}",
        f"Schema: {SCHEMA}",
        "Production files modified by harness: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== CLEAN-NATIVE PREDECESSOR ===",
        f"Source hashes unchanged: {source_ok}",
        f"Legacy project artifacts absent: {legacy_absent}",
        f"Sunshine process absent: {sunshine is False}",
        f"Sunshine check error: {sunshine_error or '<none>'}",
        "",
        "=== INITIAL NATIVE SESSION ===",
        f"Game active: {initial['game_active']}",
        f"Native ready: {initial['native_ready']}",
        f"Native active: {initial['native_active']}",
        f"Kind: {initial['kind']}",
        f"Capture backend: {initial['capture_backend']}",
        f"Encoder: {initial['encoder']}",
        f"Transport: {initial['transport']}",
        "",
        "=== OPERATOR-OBSERVED PATHS ===",
        f"Picture normal: {evidence['picture_ok']}",
        f"Audio normal: {evidence['audio_ok']}",
        f"Controller normal: {evidence['controller_ok']}",
        f"Pause/resume normal: {evidence['pause_resume_ok']}",
        f"Load restored expected state: {evidence['load_ok']}",
        f"Cheat/mod/profile path normal: {evidence['profile_ok']}",
        "",
        "=== SAVE / PROFILE EVIDENCE ===",
        f"Savestate files changed after Save: {state_delta}",
        f"Save file delta observed: {evidence['save_file_delta_ok']}",
        f"Cheat/profile storage file count: {evidence['profile_file_count']}",
        f"Profile storage present: {evidence['profile_storage_present']}",
        "",
        "=== POST-PROFILE NATIVE SESSION ===",
        f"Game active: {post_profile['game_active']}",
        f"Native ready: {post_profile['native_ready']}",
        f"Native active: {post_profile['native_active']}",
        f"Kind: {post_profile['kind']}",
        f"Capture backend: {post_profile['capture_backend']}",
        f"Encoder: {post_profile['encoder']}",
        f"Transport: {post_profile['transport']}",
        "",
        "=== END / TEARDOWN ===",
        f"Game inactive: {evidence['teardown_game_inactive']}",
        f"Native stream inactive: {evidence['teardown_native_inactive']}",
        f"Teardown confirmed: {evidence['teardown_ok']}",
        "",
        "=== DURABLE MEMORY ===",
        f"Durable memory updated: {memory_ok}",
        f"Durable memory error: {memory_error or '<none>'}",
        "",
        f"Failed required checks: {failed}",
        "Next step: "
        + (
            "B5_RUNTIME_CONFIRMED_BEGIN_B6_CLEAN_NATIVE_CHECKPOINT"
            if confirmed
            else "INSPECT_B5_FAILED_CHECKS_BEFORE_B6"
        ),
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(evidence["classification"])
    print("Text:", text_path)

    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
