#!/usr/bin/env python3
"""E5-S1: the capability probe, v1.

Reads the host and prints E5's seven capability classes as one JSON
object, each with the verdict and the threshold that verdict used, per
`docs/CAPABILITY_MODEL.md` (thresholds from E4's measurements; "not
measured; E5-S2" where E4 has none).

Host reads only: /proc, /sys, `lscpu`, `lsblk`, `vainfo`, `ffmpeg
-encoders`, and the repo's own config files. It starts nothing, changes
nothing, and needs no root. It never prints a MAC, an IP address, an
SSID, an interface name, a disk serial or a UUID; run the redactor over
its output anyway (`tools/e3_redact_check.sh`).

Usage: python3 tools/capability_probe.py [--repo <path>] > probe.json
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

PROBE_VERSION = "1"
MODEL_DOC = "docs/CAPABILITY_MODEL.md"

# The reference host (E4-S1). The only per-core speed E4 measured.
REFERENCE_CPU_MODEL = "AMD Ryzen 5 PRO 4650G with Radeon Graphics"
REFERENCE_DRM_DRIVER = "amdgpu"
REFERENCE_VA_DRIVER = "radeonsi"

# E4's numbers (docs/memory/evidence/E4_CLOSEOUT_2026-10-15.md).
ALPHA_CORES_TODAY = 6          # E4-S2 §5: 400 % floor + ~50 %
ALPHA_CORES_DEFERRAL = 4       # E4-S2 §5 / E4-S4: 150 % floor
FLOOR_STACK_PCT_TODAY = 400    # E4-S2, CONC
FLOOR_STREAM_PCT = 150         # E4-S2, PS1-STREAM
FLOOR_SNES9X_PCT = 100         # E4-S2, SNES-STREAM <= 100 %
SYSTEM_RAM_BYTES = 8 * 10**9   # E4-S2 §5: 8 GB system
GIB = 1024**3
MIB = 1024**2
STACK_MEM_TODAY = 1536 * MIB   # E4-S3B: CONC 1536M, 1,166 MB peak
STACK_MEM_DEFERRAL = 1280 * MIB  # E4-S3B §4: 1.25 GB (grab alone 976 MB)
STACK_MEM_STREAM = 384 * MIB   # E4-S3: streams <= 384M
STACK_MEM_SECOND = 2048 * MIB  # E4-S2/S3B: 2 GB absorbs a second activity
WIRE_MBPS_720P = 1.45 * 8      # E2-S1 §6: 1.45 MB/s at 720p/7000
WIRE_MBPS_1080P = 2.26 * 8     # E2-S1 §6: 2.26 MB/s at the 1080p rung

RANK = ["below-floor", "below-alpha", "deferral-only", "known-good"]


def worst(*verdicts: str) -> str:
    ranked = [v for v in verdicts if v in RANK]
    if len(ranked) != len(verdicts) or not ranked:
        return "unknown"
    return min(ranked, key=RANK.index)


def run(argv: list[str], timeout: float = 20) -> tuple[int, str]:
    if shutil.which(argv[0]) is None:
        return 127, ""
    try:
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return cp.returncode, cp.stdout + cp.stderr


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


# ---- 1. CPU / RAM / storage -------------------------------------------------

def lscpu_fields() -> dict[str, str]:
    rc, out = run(["lscpu", "-J"])
    fields: dict[str, str] = {}
    if rc != 0:
        return fields

    def walk(items: list[dict[str, Any]]) -> None:
        for item in items:
            fields[str(item.get("field", "")).rstrip(":")] = str(item.get("data", ""))
            walk(item.get("children", []) or [])

    try:
        walk(json.loads(out).get("lscpu", []))
    except ValueError:
        pass
    return fields


def cpu_info() -> dict[str, Any]:
    f = lscpu_fields()
    model = f.get("Model name")
    try:
        cores = int(f.get("Core(s) per socket", "0")) * int(f.get("Socket(s)", "1"))
    except ValueError:
        cores = 0
    logical = os.cpu_count() or 0
    if not model or not cores:
        # /proc/cpuinfo fallback
        text = read(Path("/proc/cpuinfo")) or ""
        names = re.findall(r"^model name\s*:\s*(.+)$", text, re.M)
        model = model or (names[0].strip() if names else None)
        pairs = set(re.findall(r"^physical id\s*:\s*(\d+)$.*?^core id\s*:\s*(\d+)$", text, re.M | re.S))
        cores = cores or len(pairs)
    try:
        max_mhz = float(f.get("CPU max MHz", "nan"))
    except ValueError:
        max_mhz = float("nan")
    return {
        "model": model,
        "physical_cores": cores,
        "logical_cpus": logical,
        "threads_per_core": f.get("Thread(s) per core"),
        "max_mhz": None if max_mhz != max_mhz else round(max_mhz),
        "speed_class": "reference" if model == REFERENCE_CPU_MODEL else "not measured; E5-S2",
    }


def cpu_verdict(cpu: dict[str, Any]) -> dict[str, Any]:
    cores, logical = cpu["physical_cores"], cpu["logical_cpus"]
    threshold = (
        f"reference speed class ({REFERENCE_CPU_MODEL}); physical cores >= "
        f"{ALPHA_CORES_TODAY} known-good (alpha today: {FLOOR_STACK_PCT_TODAY} % floor + 50 %); "
        f">= {ALPHA_CORES_DEFERRAL} deferral-only (alpha with deferral: {FLOOR_STREAM_PCT} % floor); "
        f"logical CPUs x 100 >= {FLOOR_STREAM_PCT} % below-alpha; else below-floor "
        "(E4-S2, E4-S4; CPU-time, not slow-core)"
    )
    if cores >= ALPHA_CORES_TODAY:
        counted = "known-good"
    elif cores >= ALPHA_CORES_DEFERRAL:
        counted = "deferral-only"
    elif logical * 100 >= FLOOR_STREAM_PCT:
        counted = "below-alpha"
    else:
        counted = "below-floor"
    if cpu["speed_class"] != "reference":
        return {"verdict": "unknown", "if_equally_fast": counted, "threshold": threshold,
                "note": "speed class not measured; E5-S2"}
    return {"verdict": counted, "threshold": threshold}


def meminfo() -> dict[str, int]:
    out: dict[str, int] = {}
    for line in (read(Path("/proc/meminfo")) or "").splitlines():
        m = re.match(r"(\w+):\s+(\d+)\s*kB", line)
        if m:
            out[m.group(1)] = int(m.group(2)) * 1024
    return out


def mem_verdict(mem: dict[str, int]) -> dict[str, Any]:
    total, avail = mem.get("MemTotal", 0), mem.get("MemAvailable", 0)
    threshold = (
        f"system MemTotal >= {SYSTEM_RAM_BYTES} B (8 GB, alpha E4-S2 §5); MemAvailable >= 1.5 GiB "
        "known-good (stack swap-off floor, CONC 1,166 MB peak, E4-S3B); >= 1.25 GiB deferral-only "
        "(grab alone 976 MB, E4-S3B §4); >= 384 MiB below-alpha (a stream alone, E4-S3); else below-floor"
    )
    if avail >= STACK_MEM_TODAY:
        v = "known-good"
    elif avail >= STACK_MEM_DEFERRAL:
        v = "deferral-only"
    elif avail >= STACK_MEM_STREAM:
        v = "below-alpha"
    else:
        v = "below-floor"
    if total < SYSTEM_RAM_BYTES and v in ("known-good", "deferral-only"):
        v = "below-alpha"
    return {"verdict": v, "threshold": threshold}


def storage() -> dict[str, Any]:
    disks: list[dict[str, Any]] = []
    rc, out = run(["lsblk", "-J", "-b", "-d", "-o", "TYPE,SIZE,ROTA,TRAN"])
    if rc == 0:
        try:
            for d in json.loads(out).get("blockdevices", []):
                if d.get("type") == "disk":
                    disks.append({
                        "size_gb": round(int(d.get("size") or 0) / 10**9, 1),
                        "rotational": str(d.get("rota")).lower() in ("1", "true"),
                        "transport": d.get("tran"),
                    })
        except (ValueError, TypeError):
            pass
    return {"disks": disks}


def free_gb(path: Path) -> float | None:
    try:
        st = os.statvfs(path)
    except OSError:
        return None
    return round(st.f_bavail * st.f_frsize / 10**9, 1)


def media_roots(repo: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"media_root_free_gb": free_gb(repo / "media")}
    raw = read(repo / "data" / "storage.json")
    vod = None
    if raw:
        try:
            vod = json.loads(raw).get("vod_root")
        except ValueError:
            vod = None
    if vod:
        p = Path(vod).expanduser()
        out["vod_root_configured"] = True
        out["vod_root_present"] = p.is_dir()
        out["vod_root_free_gb"] = free_gb(p) if p.is_dir() else None
    else:
        out["vod_root_configured"] = False
    return out


# ---- 2. GPU / 3. encode-decode ------------------------------------------------

def drm_nodes() -> list[dict[str, Any]]:
    nodes = []
    for node in sorted(Path("/sys/class/drm").glob("renderD*")):
        drv = node / "device" / "driver"
        nodes.append({
            "driver": drv.resolve().name if drv.exists() else None,
            "dev_rw": os.access(Path("/dev/dri") / node.name, os.R_OK | os.W_OK),
        })
    return nodes


def gpu_verdict(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    threshold = (
        "exactly one usable render node (the companion fails closed otherwise: "
        f"native_stream._linux_vaapi_device); driver {REFERENCE_DRM_DRIVER} (the reference) known-good; "
        "another driver unknown (not measured; E5-S2); none or several below-floor. "
        "iGPU headroom not probed (reference 18-23 % busy at PS1-STREAM, E4-S1)"
    )
    usable = [n for n in nodes if n["dev_rw"]]
    if len(usable) != 1:
        return {"verdict": "below-floor", "threshold": threshold}
    if usable[0]["driver"] == REFERENCE_DRM_DRIVER:
        return {"verdict": "known-good", "threshold": threshold}
    return {"verdict": "unknown", "threshold": threshold, "note": "not measured; E5-S2"}


def vaapi() -> dict[str, Any]:
    rc, out = run(["vainfo"])
    driver = None
    m = re.search(r"Driver version:.*?\((\w+),\s*(\w+)", out)
    if m:
        driver = {"name": m.group(1), "family": m.group(2)}
    mesa = re.search(r"Mesa Gallium driver ([\d.]+)", out)
    pairs = re.findall(r"(VAProfile\w+)\s*:\s*(VAEntrypoint\w+)", out)
    enc = sorted({p for p, e in pairs if e in ("VAEntrypointEncSlice", "VAEntrypointEncSliceLP")})
    dec = sorted({p for p, e in pairs if e == "VAEntrypointVLD"})
    rc2, out2 = run(["ffmpeg", "-hide_banner", "-encoders"])
    ff = sorted(set(re.findall(r"^\s*V\S*\s+(\w+_vaapi)\b", out2, re.M)))
    return {
        "vainfo_present": rc != 127,
        "va_driver": driver,
        "mesa_version": mesa.group(1) if mesa else None,
        "encode_profiles": enc,
        "decode_profiles": dec,
        "ffmpeg_vaapi_encoders": ff,
    }


def encode_verdict(va: dict[str, Any]) -> dict[str, Any]:
    threshold = (
        "H.264 VAEntrypointEncSlice + ffmpeg h264_vaapi + VA driver "
        f"{REFERENCE_VA_DRIVER} (the reference) known-good: the live ladder 720p60 5000-7000 "
        "(C3-L4; encoder 36 % of a core at 720p, 73 % at 1080p, E4-S1); H.264 encode with another "
        "driver unknown (720p60 rate not measured; E5-S2); none below-floor (E4-S2 §5: out of scope)"
    )
    h264 = any(p.startswith("VAProfileH264") for p in va["encode_profiles"])
    if not (h264 and "h264_vaapi" in va["ffmpeg_vaapi_encoders"]):
        return {"verdict": "below-floor", "threshold": threshold}
    if (va["va_driver"] or {}).get("name") == REFERENCE_VA_DRIVER:
        return {"verdict": "known-good", "threshold": threshold}
    return {"verdict": "unknown", "threshold": threshold, "note": "not measured; E5-S2"}


# ---- 4. validated stream profiles (from the repo, not measured) ------------

PROFILE_STATUS = {
    "native_game_720p60_reference": "ADOPTED, the default (D-BASE close-out 2026-09-23); live ladder 5000-7000 (C3-L4)",
    "native_game_1080p60_candidate": "candidate, not adopted (C5-M1; the rung flag, C5-CLOSE)",
    "native_game_1080p60_c1_parity_cap90": "candidate, not adopted (C5-M2)",
    "native_game_1080p60_c2_80pct_cap160": "candidate, not adopted (C5-M2); the 1080p rung's arm (12600 kbps)",
    "native_game_1080p60_c3_80pct_cap90": "candidate, not adopted (C5-M2)",
    "native_game_720p60_4000": "screened, never the default, never on the live ladder (C5-M3, Phase G)",
    "native_game_720p60_3000": "screened, never the default, never on the live ladder (C5-M3, Phase G)",
    "native_game_540p60_3500": "screened, never the default, never on the live ladder (C5-M3, Phase G)",
}


def profile_table(repo: Path) -> list[dict[str, Any]]:
    """Profile ids and sizes, parsed from the source (not imported)."""
    src = read(repo / "companion" / "native_stream_profiles.py") or ""
    rows: list[dict[str, Any]] = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return rows
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None)
        args: dict[str, Any] = {}
        if name == "NativeStreamProfile":
            for kw in node.keywords:
                if kw.arg in ("id", "width", "height", "fps", "bitrate_kbps") and isinstance(kw.value, ast.Constant):
                    args[kw.arg] = kw.value.value
        elif name == "_c5_1080p60" and len(node.args) >= 2:
            vals = [a.value for a in node.args if isinstance(a, ast.Constant)]
            args = {"id": vals[0], "width": 1920, "height": 1080, "fps": 60, "bitrate_kbps": vals[1]}
        elif name == "_c5_low_rung" and len(node.args) >= 4:
            vals = [a.value for a in node.args if isinstance(a, ast.Constant)]
            args = {"id": vals[0], "width": vals[1], "height": vals[2], "fps": 60, "bitrate_kbps": vals[3]}
        if isinstance(args.get("id"), str):
            args["status"] = PROFILE_STATUS.get(args["id"], "not in the model; check its record")
            rows.append(args)
    return rows


# ---- 5. emulator tiers --------------------------------------------------------

def cores_present(repo: Path) -> dict[str, Any]:
    cfg_raw = read(repo / "companion" / "games" / "config" / "emulators.json") or "{}"
    try:
        cfg = json.loads(cfg_raw)
    except ValueError:
        cfg = {}
    rel = (((cfg.get("platforms") or {}).get("linux") or {}).get("retroarch") or {}).get("cores_directory")
    core_dir = (repo / rel) if rel else None
    names = sorted(p.name for p in core_dir.glob("*_libretro.so")) if core_dir and core_dir.is_dir() else []
    return {"cores_directory_found": bool(core_dir and core_dir.is_dir()), "cores": names}


def adopted_lines() -> list[str]:
    d = Path.home() / ".config" / "systemd" / "user" / "privyhub-companion.service.d"
    lines = []
    for f in sorted(d.glob("*.conf")) if d.is_dir() else []:
        for m in re.finditer(r"PRIVYHUB_[A-Z0-9_]+=[\w.:-]+", read(f) or ""):
            lines.append(m.group(0))
    return lines


def emulator_tiers(cores: list[str], cpu: dict[str, Any], cpu_v: dict[str, Any],
                   mem: dict[str, int]) -> dict[str, Any]:
    ref = cpu["speed_class"] == "reference"
    logical_pct = cpu["logical_cpus"] * 100
    avail = mem.get("MemAvailable", 0)

    def tier(core: str, cpu_pct: int, threshold: str) -> dict[str, Any]:
        if core not in cores:
            return {"core": core, "present": False, "verdict": "below-floor", "threshold": threshold}
        if not ref:
            return {"core": core, "present": True, "verdict": "unknown", "threshold": threshold,
                    "note": "speed class not measured; E5-S2"}
        ok = logical_pct >= cpu_pct and avail >= STACK_MEM_STREAM
        return {"core": core, "present": True, "verdict": "known-good" if ok else "below-floor",
                "threshold": threshold}

    ps1 = tier("mednafen_psx_hw_libretro.so", FLOOR_STREAM_PCT,
               "core present; CPU time >= 150 % (PS1-STREAM floor, E4-S2); memory >= 384M (E4-S3); reference speed class")
    snes = tier("snes9x_libretro.so", FLOOR_SNES9X_PCT,
                "core present; CPU time >= 100 % (SNES-STREAM <= 100 %, E4-S2); memory >= 384M (E4-S3); reference speed class")
    bsnes_t = ("RetroArch alone 436-517 % of a core (E2-S1), no floor measured: known-good only on the reference "
               f"speed class with >= {ALPHA_CORES_TODAY} physical cores; else unknown")
    if "bsnes_libretro.so" not in cores:
        bsnes = {"core": "bsnes_libretro.so", "present": False, "verdict": "below-floor", "threshold": bsnes_t}
    elif ref and cpu["physical_cores"] >= ALPHA_CORES_TODAY:
        bsnes = {"core": "bsnes_libretro.so", "present": True, "verdict": "known-good", "threshold": bsnes_t}
    else:
        bsnes = {"core": "bsnes_libretro.so", "present": True, "verdict": "unknown", "threshold": bsnes_t}
    nm = "not measured; E5-S2 (no fixtures, E1-S1)"
    nes = {"core": "fceumm_libretro.so", "present": "fceumm_libretro.so" in cores, "verdict": "unknown", "threshold": nm}
    gen = {"core": "blastem_libretro.so", "present": "blastem_libretro.so" in cores, "verdict": "unknown", "threshold": nm}
    return {
        "verdict": worst(ps1["verdict"], snes["verdict"]),
        "threshold": "the worse of PS1 and SNES (Snes9x); bsnes, NES and Genesis reported, not counted",
        "tiers": {"ps1_4x": ps1, "snes_snes9x": snes, "snes_bsnes": bsnes, "nes": nes, "genesis": gen},
    }


# ---- 6. concurrency headroom ---------------------------------------------------

def concurrency(cpu: dict[str, Any], mem: dict[str, int]) -> dict[str, Any]:
    cores, avail = cpu["physical_cores"], mem.get("MemAvailable", 0)
    threshold = (
        f"grabs under a stream: stack {FLOOR_STACK_PCT_TODAY} % (CONC, E4-S2) + margin -> >= {ALPHA_CORES_TODAY} "
        "physical cores at the reference speed class and MemAvailable >= 1.5 GiB known-good; "
        f">= {ALPHA_CORES_DEFERRAL} cores and >= 1.25 GiB deferral-only (stack floor 150 % with deferral, E4-S4); "
        "second activity: MemAvailable >= 2 GiB for the stack (E4-S2/S3B)"
    )
    if cores >= ALPHA_CORES_TODAY and avail >= STACK_MEM_TODAY:
        v = "known-good"
    elif cores >= ALPHA_CORES_DEFERRAL and avail >= STACK_MEM_DEFERRAL:
        v = "deferral-only"
    elif cpu["logical_cpus"] * 100 >= FLOOR_STREAM_PCT and avail >= STACK_MEM_STREAM:
        v = "below-alpha"
    else:
        v = "below-floor"
    out: dict[str, Any] = {
        "logical_cpus_pct": cpu["logical_cpus"] * 100,
        "stack_floor_pct_today": FLOOR_STACK_PCT_TODAY,
        "stack_floor_pct_with_deferral": FLOOR_STREAM_PCT,
        "mem_available_gib": round(avail / GIB, 2),
        "second_activity": avail >= STACK_MEM_SECOND,
        "grabs_under_stream": {"known-good": "allowed", "deferral-only": "defer while streaming"}.get(v, "no"),
        "threshold": threshold,
    }
    if cpu["speed_class"] != "reference":
        out.update(verdict="unknown", if_equally_fast=v, note="speed class not measured; E5-S2")
    else:
        out["verdict"] = v
    return out


# ---- 7. network (no names, no addresses) -------------------------------------

def default_route_iface() -> str | None:
    for line in (read(Path("/proc/net/route")) or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) > 2 and parts[1] == "00000000":
            return parts[0]
    return None


def network() -> dict[str, Any]:
    iface = default_route_iface()
    threshold = (
        f"wired, up, link speed >= {WIRE_MBPS_720P:.1f} Mb/s known-good for the 720p reference "
        f"(wire rate 1.45 MB/s, E2-S1 §6; the reference host wired, D-BASE); >= {WIRE_MBPS_1080P:.1f} Mb/s "
        "also carries the 1080p rung (2.26 MB/s); wireless unknown (not measured; E5-S2); down or slower below-floor"
    )
    loss_row = ("post-FEC video loss < 10/min on the client's link (D-BASE 8.67 / 8.40): not measurable by a "
                "host probe; 0 of 60 stream runs met it since 2026-10-09 (E4-C1 §5); the link watch E4-S4D")
    if iface is None:
        return {"default_route": False, "verdict": "below-floor", "threshold": threshold, "loss_row": loss_row}
    base = Path("/sys/class/net") / iface
    wireless = (base / "wireless").exists() or (base / "phy80211").exists()
    try:
        speed = int(read(base / "speed") or "-1")
    except ValueError:
        speed = -1
    state = read(base / "operstate")
    out: dict[str, Any] = {
        "default_route": True,
        "type": "wireless" if wireless else "wired",
        "operstate": state,
        "link_speed_mbps": speed if speed > 0 else None,
        "duplex": read(base / "duplex"),
        "carries_1080p_rung": speed >= WIRE_MBPS_1080P,
        "threshold": threshold,
        "loss_row": loss_row,
    }
    if wireless:
        out.update(verdict="unknown", note="not measured; E5-S2")
    elif state == "up" and speed >= WIRE_MBPS_720P:
        out["verdict"] = "known-good"
    else:
        out["verdict"] = "below-floor"
    return out


# ---- main ---------------------------------------------------------------------

def stream_live() -> bool:
    """Whether a native stream encoder is running now (reported, not changed)."""
    for p in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            cmd = p.read_bytes()
        except OSError:
            continue
        if b"ffmpeg" in cmd and b"h264_vaapi" in cmd:
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    repo = Path(ap.parse_args().repo).resolve()

    cpu = cpu_info()
    cpu_v = cpu_verdict(cpu)
    mem = meminfo()
    mem_v = mem_verdict(mem)
    nodes = drm_nodes()
    va = vaapi()
    enc_v = encode_verdict(va)
    cores = cores_present(repo)

    classes: dict[str, Any] = {
        "cpu_ram_storage": {
            "verdict": worst(cpu_v["verdict"], mem_v["verdict"]),
            "threshold": "the worse of cpu and ram; storage not measured; E5-S2",
            "cpu": {**cpu, **{"check": cpu_v}},
            "ram": {
                "mem_total_gib": round(mem.get("MemTotal", 0) / GIB, 2),
                "mem_available_gib": round(mem.get("MemAvailable", 0) / GIB, 2),
                "swap_total_gib": round(mem.get("SwapTotal", 0) / GIB, 2),
                "check": mem_v,
            },
            "storage": {**storage(), **media_roots(repo), "verdict": "unknown",
                        "threshold": "not measured; E5-S2"},
        },
        "gpu": {"render_nodes": len(nodes), "drivers": [n["driver"] for n in nodes], **gpu_verdict(nodes)},
        "hw_encode_decode": {**va, **enc_v,
                             "decode": {"verdict": "unknown", "threshold": "not measured; E5-S2"}},
        "validated_stream_profiles": {
            "source": "companion/native_stream_profiles.py (repo, not measured)",
            "profiles": profile_table(repo),
            "verdict": enc_v["verdict"],
            "threshold": "the encode class's verdict: the profiles were validated on the reference only",
            "enabled_by_default": (["native_game_720p60_reference", "live ladder 5000-7000"]
                                   if enc_v["verdict"] == "known-good" else []),
            "flag_only": ["the 1080p rung (PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p), client-limited (C5-CLOSE)"],
        },
        "emulator_tiers": {**cores, **emulator_tiers(cores["cores"], cpu, cpu_v, mem)},
        "concurrency_headroom": concurrency(cpu, mem),
        "network": network(),
    }
    numbered = {k: v["verdict"] for k, v in classes.items()}
    print(json.dumps({
        "probe": "tools/capability_probe.py",
        "probe_version": PROBE_VERSION,
        "model": MODEL_DOC,
        "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host_reads_only": True,
        "stream_live_at_probe": stream_live(),
        "adopted_lines": adopted_lines(),
        "summary": numbered,
        "classes": classes,
    }, indent=2))


if __name__ == "__main__":
    main()
