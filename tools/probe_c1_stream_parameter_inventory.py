#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCHEMA = "privyhub_c1_stream_parameter_inventory_v1"

SOURCES = {
    "host": "companion/native_stream.py",
    "fec": "companion/native_fec_relay.py",
    "session_io": "companion/native_session_io.py",
    "capture": "companion/native_wgc_bridge.py",
    "android": "PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt",
}

HOST_REQUIRED = {
    "WIDTH": 1280,
    "HEIGHT": 720,
    "FPS": 60,
    "GOP_FRAMES": 15,
    "BITRATE_KBPS": 7000,
    "PAYLOAD_TYPE": 96,
    "DEFAULT_PORT": 48100,
    "FEC_INPUT_PORT": 48110,
    "FEC_GROUP_SIZE": 8,
    "AUDIO_PORT": 48101,
    "INPUT_PORT": 48102,
}

FEC_REQUIRED = {
    "FEC_VERSION": 1,
    "DEFAULT_GROUP_SIZE": 8,
    "DEFAULT_LOCAL_PORT": 48110,
}

ANDROID_REQUIRED = {
    "CONTROL_PORT": 8765,
    "VIDEO_PORT": 48100,
    "AUDIO_PORT": 48101,
    "INPUT_PORT": 48102,
    "VIDEO_WIDTH": 1280,
    "VIDEO_HEIGHT": 720,
    "VIDEO_FPS": 60,
    "EXPECTED_HOST_ALPHA": "0.7",
    "CLIENT_PROFILER_VERSION": "0.12.2",
    "CLIENT_HEALTH_INTERVAL_MS": 2000,
}

FFMPEG_REQUIRED = {
    "codec": "h264_nvenc",
    "preset": "p1",
    "tune": "ull",
    "zerolatency": "1",
    "delay": "0",
    "rc_lookahead": "0",
    "rc": "cbr",
    "bufsize": "1000k",
    "bframes": "0",
    "pix_fmt": "yuv420p",
    "packet_size": 1200,
    "scale_flags": "fast_bilinear",
    "pad_color": "black",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(root: Path, rel: str) -> str:
    p = subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return p.stdout.strip() if p.returncode == 0 else ""


def literal_assignments(source: str, *, class_name: str | None = None) -> dict[str, Any]:
    tree = ast.parse(source)
    nodes: list[ast.stmt]

    if class_name is None:
        nodes = list(tree.body)
    else:
        target = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == class_name
            ),
            None,
        )
        if target is None:
            return {}
        nodes = list(target.body)

    out: dict[str, Any] = {}

    for node in nodes:
        name = None
        value_node = None

        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            value_node = node.value

        if not name or value_node is None:
            continue

        try:
            value = ast.literal_eval(value_node)
        except Exception:
            continue

        if isinstance(value, bytes):
            value = {
                "type": "bytes",
                "hex": value.hex(),
            }

        if name.isupper():
            out[name] = value

    return out


def normalize_kotlin_value(raw: str) -> Any:
    value = raw.strip().rstrip(";").strip()

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    numeric = value.replace("_", "")
    if numeric.endswith(("L", "l", "F", "f")):
        numeric = numeric[:-1]

    try:
        if "." in numeric:
            return float(numeric)
        return int(numeric)
    except ValueError:
        return value


def kotlin_constants(source: str) -> dict[str, Any]:
    pattern = re.compile(
        r"(?:private\s+)?const\s+val\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
        r"(\"(?:[^\"\\]|\\.)*\"|[-+]?[0-9][0-9_]*(?:\.[0-9_]+)?[LlFf]?)"
    )
    return {
        name: normalize_kotlin_value(value)
        for name, value in pattern.findall(source)
    }


def extract_ffmpeg_policy(source: str) -> dict[str, Any]:
    def option_value(option: str) -> str | None:
        pattern = re.compile(
            rf'"{re.escape(option)}"\s*,\s*"([^"]+)"',
            re.MULTILINE,
        )
        match = pattern.search(source)
        return match.group(1) if match else None

    destination_pkt = re.search(r"\?pkt_size=(\d+)", source)
    scale_flags = re.search(r'"flags=([^",]+),?"', source)
    pad_color = re.search(
        r'"[^"]*\(ow-iw\)/2:\(oh-ih\)/2:([A-Za-z0-9_]+)"',
        source,
    )

    return {
        "codec": option_value("-c:v"),
        "preset": option_value("-preset"),
        "tune": option_value("-tune"),
        "zerolatency": option_value("-zerolatency"),
        "delay": option_value("-delay"),
        "rc_lookahead": option_value("-rc-lookahead"),
        "rc": option_value("-rc"),
        "bufsize": option_value("-bufsize"),
        "bframes": option_value("-bf"),
        "pix_fmt": option_value("-pix_fmt"),
        "packet_size": int(destination_pkt.group(1)) if destination_pkt else None,
        "scale_flags": scale_flags.group(1) if scale_flags else None,
        "pad_color": pad_color.group(1) if pad_color else None,
        "bitrate_source": "NativeStreamManager.BITRATE_KBPS",
        "maxrate_source": "NativeStreamManager.BITRATE_KBPS",
        "gop_source": "NativeStreamManager.GOP_FRAMES",
        "payload_type_source": "NativeStreamManager.PAYLOAD_TYPE",
        "output_size_source": "NativeStreamManager.WIDTH/HEIGHT",
        "framerate_source": "NativeStreamManager.FPS",
    }


def duplicate_map(
    host: dict[str, Any],
    fec: dict[str, Any],
    android: dict[str, Any],
) -> list[dict[str, Any]]:
    pairs = [
        ("video_width", host.get("WIDTH"), android.get("VIDEO_WIDTH")),
        ("video_height", host.get("HEIGHT"), android.get("VIDEO_HEIGHT")),
        ("video_fps", host.get("FPS"), android.get("VIDEO_FPS")),
        ("video_port", host.get("DEFAULT_PORT"), android.get("VIDEO_PORT")),
        ("audio_port", host.get("AUDIO_PORT"), android.get("AUDIO_PORT")),
        ("input_port", host.get("INPUT_PORT"), android.get("INPUT_PORT")),
        ("fec_group_size", host.get("FEC_GROUP_SIZE"), fec.get("DEFAULT_GROUP_SIZE")),
        ("fec_local_port", host.get("FEC_INPUT_PORT"), fec.get("DEFAULT_LOCAL_PORT")),
    ]
    return [
        {
            "parameter": name,
            "left": left,
            "right": right,
            "match": left == right and left is not None,
        }
        for name, left, right in pairs
    ]


def proposed_ownership() -> list[dict[str, str]]:
    return [
        {"parameter": "width/height/fps", "class": "profile_candidate", "reason": "stream presentation/capture envelope"},
        {"parameter": "bitrate/maxrate/bufsize", "class": "profile_candidate", "reason": "quality/capacity policy"},
        {"parameter": "gop/bframes", "class": "profile_candidate", "reason": "latency/recovery policy"},
        {"parameter": "codec/preset/tune/rc/pix_fmt", "class": "encoder_policy_candidate", "reason": "backend-specific encoding policy"},
        {"parameter": "fec enabled/group size", "class": "transport_profile_candidate", "reason": "Phase C later adapts/proves FEC policy"},
        {"parameter": "RTP packet size/payload type", "class": "transport_contract_candidate", "reason": "wire-format behavior, not user quality alone"},
        {"parameter": "video/audio/input ports", "class": "session_transport_invariant", "reason": "endpoint allocation rather than quality profile"},
        {"parameter": "capture backend", "class": "capability/backend", "reason": "Windows now; Linux backend later"},
        {"parameter": "audio implementation", "class": "source_audio_policy", "reason": "process-scoped audio contract must survive Linux migration"},
        {"parameter": "client health interval", "class": "telemetry_contract", "reason": "feeds C2/C3 adaptation but should not be a stream quality knob"},
    ]


def self_test() -> int:
    py = """
X = 7
class Demo:
    WIDTH = 1280
    TEXT = "ok"
    lower = 1
"""
    assert literal_assignments(py) == {"X": 7}
    assert literal_assignments(py, class_name="Demo") == {"WIDTH": 1280, "TEXT": "ok"}

    kt = """
private const val VIDEO_WIDTH =
    1_280
private const val NAME =
    "alpha"
private const val INTERVAL =
    2_000L
"""
    assert kotlin_constants(kt) == {
        "VIDEO_WIDTH": 1280,
        "NAME": "alpha",
        "INTERVAL": 2000,
    }

    ff = """
destination = "rtp://127.0.0.1:48110" "?pkt_size=1200"
return ["-c:v", "h264_nvenc", "-preset", "p1", "-tune", "ull",
"-zerolatency", "1", "-delay", "0", "-rc-lookahead", "0", "-rc", "cbr",
"-bufsize", "1000k", "-bf", "0", "-pix_fmt", "yuv420p",
"flags=fast_bilinear,", "(ow-iw)/2:(oh-ih)/2:black"]
"""
    got = extract_ffmpeg_policy(ff)
    for key, value in FFMPEG_REQUIRED.items():
        assert got[key] == value, (key, got[key], value)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    missing = [rel for rel in SOURCES.values() if not (root / rel).is_file()]

    if missing:
        print("C1_STREAM_PARAMETER_INVENTORY_INCOMPLETE")
        print("Missing source files:", missing)
        return 2

    host_text = (root / SOURCES["host"]).read_text(encoding="utf-8-sig")
    fec_text = (root / SOURCES["fec"]).read_text(encoding="utf-8-sig")
    session_text = (root / SOURCES["session_io"]).read_text(encoding="utf-8-sig")
    android_text = (root / SOURCES["android"]).read_text(encoding="utf-8-sig")

    host = literal_assignments(host_text, class_name="NativeStreamManager")
    fec = literal_assignments(fec_text)
    audio = literal_assignments(session_text, class_name="NativeAudioStreamer")
    android = kotlin_constants(android_text)
    ffmpeg = extract_ffmpeg_policy(host_text)
    duplicates = duplicate_map(host, fec, android)

    failures: list[str] = []

    for name, value in HOST_REQUIRED.items():
        if host.get(name) != value:
            failures.append(f"host:{name}:{host.get(name)!r}!={value!r}")

    for name, value in FEC_REQUIRED.items():
        if fec.get(name) != value:
            failures.append(f"fec:{name}:{fec.get(name)!r}!={value!r}")

    for name, value in ANDROID_REQUIRED.items():
        if android.get(name) != value:
            failures.append(f"android:{name}:{android.get(name)!r}!={value!r}")

    for name, value in FFMPEG_REQUIRED.items():
        if ffmpeg.get(name) != value:
            failures.append(f"ffmpeg:{name}:{ffmpeg.get(name)!r}!={value!r}")

    for item in duplicates:
        if not item["match"]:
            failures.append(
                "duplicate:"
                + item["parameter"]
                + f":{item['left']!r}!={item['right']!r}"
            )

    capture_contract = {
        "backend": "windows_graphics_capture",
        "bridge": SOURCES["capture"],
        "input_pixel_format": "bgra rawvideo pipe",
        "whole_desktop_fallback": False,
        "target": "project-managed RetroArch window",
    }

    session_contract = {
        "audio": {
            "implementation": "Windows process-loopback helper",
            "timing_probe_version": audio.get("TIMING_PROBE_VERSION"),
            "buffer_architecture": audio.get("AUDIO_BUFFER_ARCHITECTURE"),
            "port": host.get("AUDIO_PORT"),
        },
        "input": {
            "protocol": "PHI1",
            "port": host.get("INPUT_PORT"),
        },
        "video": {
            "port": host.get("DEFAULT_PORT"),
            "fec_input_port": host.get("FEC_INPUT_PORT"),
        },
    }

    source_hashes = {
        key: {
            "path": rel,
            "sha256": sha256(root / rel),
            "git_blob": git_blob(root, rel),
        }
        for key, rel in SOURCES.items()
    }

    payload = {
        "schema": SCHEMA,
        "classification": (
            "C1_STREAM_PARAMETER_INVENTORY_CAPTURED"
            if not failures
            else "C1_STREAM_PARAMETER_INVENTORY_INCOMPLETE"
        ),
        "production_files_modified_by_probe": [],
        "network_addresses_collected_or_logged": False,
        "host_constants": host,
        "fec_constants": fec,
        "audio_constants": audio,
        "android_constants": android,
        "ffmpeg_policy": ffmpeg,
        "capture_contract": capture_contract,
        "session_contract": session_contract,
        "duplicated_ownership": duplicates,
        "ownership_classification": proposed_ownership(),
        "source_hashes": source_hashes,
        "failures": failures,
        "next_step": (
            "C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA"
            if not failures
            else "REVIEW_C1_INVENTORY_BEFORE_PROFILE_SCHEMA"
        ),
    }

    log_dir = root / "logs" / "diagnostics"
    log_dir.mkdir(parents=True, exist_ok=True)

    json_path = log_dir / "c1_stream_parameter_inventory.json"
    text_path = log_dir / "c1_stream_parameter_inventory.txt"

    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "PrivyHub C1 explicit stream profile parameter inventory",
        f"Classification: {payload['classification']}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== CURRENT VALIDATED VIDEO ENVELOPE ===",
        f"Resolution: {host.get('WIDTH')}x{host.get('HEIGHT')}",
        f"FPS: {host.get('FPS')}",
        f"Source bitrate: {host.get('BITRATE_KBPS')} kbps",
        f"GOP: {host.get('GOP_FRAMES')} frames",
        f"FEC: {host.get('FEC_GROUP_SIZE')} data + 1 XOR parity",
        f"RTP payload type: {host.get('PAYLOAD_TYPE')}",
        f"RTP packet size: {ffmpeg.get('packet_size')} bytes",
        "",
        "=== ENCODER POLICY ===",
    ]

    for key in (
        "codec",
        "preset",
        "tune",
        "zerolatency",
        "delay",
        "rc_lookahead",
        "rc",
        "bufsize",
        "bframes",
        "pix_fmt",
        "scale_flags",
        "pad_color",
    ):
        lines.append(f"{key}: {ffmpeg.get(key)}")

    lines += ["", "=== DUPLICATED OWNERSHIP ==="]

    for item in duplicates:
        lines.append(
            f"{item['parameter']}: left={item['left']} right={item['right']} "
            f"match={item['match']}"
        )

    lines += ["", "=== SESSION / BACKEND CONTRACT ==="]
    lines.append("Capture backend: windows_graphics_capture")
    lines.append("Capture target: project-managed RetroArch window")
    lines.append("Whole-desktop fallback: disabled")
    lines.append(
        "Audio: Windows process-loopback helper "
        f"({audio.get('AUDIO_BUFFER_ARCHITECTURE')})"
    )
    lines.append("Input: PHI1")
    lines.append(f"Video port: {host.get('DEFAULT_PORT')}")
    lines.append(f"Audio port: {host.get('AUDIO_PORT')}")
    lines.append(f"Input port: {host.get('INPUT_PORT')}")
    lines.append(
        f"Client health cadence: {android.get('CLIENT_HEALTH_INTERVAL_MS')} ms"
    )

    lines += ["", "=== OWNERSHIP CLASSIFICATION ==="]

    for item in proposed_ownership():
        lines.append(
            f"{item['parameter']}: {item['class']} — {item['reason']}"
        )

    lines += ["", "=== SOURCE HASHES ==="]

    for key, value in source_hashes.items():
        lines.append(
            f"{key}: {value['path']} sha256={value['sha256']} "
            f"git_blob={value['git_blob']}"
        )

    lines += [
        "",
        f"Failures: {failures}",
        f"Next step: {payload['next_step']}",
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("\n".join(lines))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
