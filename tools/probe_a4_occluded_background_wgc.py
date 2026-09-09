#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import os
import time
from ctypes import wintypes
from pathlib import Path

META_REL = Path("data/games/native_stream/wgc_capture_meta.json")
OUT_TXT = Path("logs/games/a4_host_coexistence_occlusion_probe.txt")
OUT_JSON = Path("logs/games/a4_host_coexistence_occlusion_probe.json")

WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
SS_CENTER = 0x00000001
SS_CENTERIMAGE = 0x00000200
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
SWP_SHOWWINDOW = 0x0040
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class ProbeError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ProbeError(f"Unable to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProbeError(f"Invalid JSON root: {path}")
    return data


def configured_retroarch(root: Path) -> Path:
    cfg = read_json(root / "companion/games/config/emulators.json")
    retro = cfg.get("retroarch")
    if not isinstance(retro, dict):
        raise ProbeError("RetroArch config missing")
    rel = retro.get("executable")
    if not isinstance(rel, str) or not rel.strip():
        raise ProbeError("RetroArch executable missing")
    exe = (root / rel).resolve()
    try:
        exe.relative_to(root)
    except ValueError as exc:
        raise ProbeError("Configured RetroArch executable escapes project root") from exc
    if not exe.is_file():
        raise ProbeError("Configured RetroArch executable does not exist")
    return exe


def counter(data: dict, key: str) -> int:
    try:
        return int(data.get(key, 0) or 0)
    except Exception:
        return 0


def diag_counter(data: dict, key: str) -> int:
    diag = data.get("diagnostics")
    if not isinstance(diag, dict):
        return 0
    try:
        return int(diag.get(key, 0) or 0)
    except Exception:
        return 0


def window_flag(data: dict, key: str) -> bool:
    win = data.get("window")
    return bool(win.get(key, False)) if isinstance(win, dict) else False


def read_meta(path: Path, fresh: bool = False) -> dict:
    data = read_json(path)
    if data.get("backend") != "windows_graphics_capture":
        raise ProbeError("Active stream is not Windows Graphics Capture")
    if fresh:
        updated = counter(data, "updated_unix_ms")
        age = int(time.time() * 1000) - updated
        if updated <= 0 or age > 12000:
            raise ProbeError(
                "WGC metadata is stale. Open the game fullscreen on the onn before running the probe."
            )
    return data


def summarize(start: dict, end: dict) -> dict:
    return {
        "callbacks_delta": counter(end, "callbacks") - counter(start, "callbacks"),
        "emitted_delta": counter(end, "emitted_frames") - counter(start, "emitted_frames"),
        "duplicates_delta": counter(end, "duplicated_emits") - counter(start, "duplicated_emits"),
        "near_black_delta": diag_counter(end, "near_black_samples")
            - diag_counter(start, "near_black_samples"),
        "black_streak": diag_counter(end, "current_near_black_streak_samples"),
        "captured_exists": window_flag(end, "captured_exists"),
        "captured_visible": window_flag(end, "captured_visible"),
        "captured_iconic": window_flag(end, "captured_iconic"),
    }


def wait_meta(path: Path, seconds: float) -> dict:
    deadline = time.monotonic() + seconds
    latest = None
    while time.monotonic() < deadline:
        try:
            latest = read_meta(path)
        except ProbeError:
            pass
        time.sleep(0.25)
    if latest is None:
        raise ProbeError("WGC metadata disappeared")
    return latest


def win_api():
    if os.name != "nt":
        raise ProbeError("This probe requires Windows")
    u = ctypes.WinDLL("user32", use_last_error=True)
    k = ctypes.WinDLL("kernel32", use_last_error=True)

    u.IsWindow.argtypes = [wintypes.HWND]
    u.IsWindow.restype = wintypes.BOOL
    u.IsIconic.argtypes = [wintypes.HWND]
    u.IsIconic.restype = wintypes.BOOL
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowThreadProcessId.restype = wintypes.DWORD
    u.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u.GetWindowRect.restype = wintypes.BOOL
    u.GetForegroundWindow.argtypes = []
    u.GetForegroundWindow.restype = wintypes.HWND
    u.SetForegroundWindow.argtypes = [wintypes.HWND]
    u.SetForegroundWindow.restype = wintypes.BOOL
    u.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
    ]
    u.CreateWindowExW.restype = wintypes.HWND
    u.DestroyWindow.argtypes = [wintypes.HWND]
    u.DestroyWindow.restype = wintypes.BOOL
    u.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, wintypes.UINT
    ]
    u.SetWindowPos.restype = wintypes.BOOL
    u.UpdateWindow.argtypes = [wintypes.HWND]
    u.UpdateWindow.restype = wintypes.BOOL

    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    k.QueryFullProcessImageNameW.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    k.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    k.GetModuleHandleW.restype = wintypes.HMODULE
    return u, k


def process_path(k, pid: int) -> str:
    h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buf))
        if not k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return ""
        return buf.value
    finally:
        k.CloseHandle(h)


def same_path(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(str(b)))


def classify(base: dict, covered: dict) -> tuple[str, str]:
    b = int(base["callbacks_delta"])
    c = int(covered["callbacks_delta"])
    e = int(covered["emitted_delta"])
    d = int(covered["duplicates_delta"])

    if b < 10:
        return "INCONCLUSIVE_BASELINE", "Visible baseline did not produce enough WGC callbacks."
    if covered["captured_iconic"]:
        return "INCONCLUSIVE_WINDOW_STATE", "RetroArch unexpectedly became minimized."
    if not covered["captured_exists"]:
        return "OCCLUSION_BREAKS_CAPTURE_TARGET", "The captured RetroArch HWND became invalid."
    if int(covered["near_black_delta"]) > 0 or int(covered["black_streak"]) > 0:
        return "OCCLUSION_BLACK_CAPTURE", "Covered-window capture produced near-black content."

    callback_ratio = c / max(1, b)
    duplicate_fraction = d / max(1, e)

    if callback_ratio >= 0.80 and duplicate_fraction <= 0.20:
        return (
            "OCCLUSION_CAPTURE_HEALTHY",
            "WGC continued receiving fresh frames near the visible-window rate while RetroArch was covered and not foreground."
        )
    if c <= 3 and e >= 10 and d >= 5:
        return (
            "OCCLUSION_FREEZES_CAPTURE",
            "Covering RetroArch stopped fresh callbacks; the bridge mainly repeated its last frame."
        )
    return (
        "OCCLUSION_CAPTURE_DEGRADED",
        "WGC remained active while RetroArch was covered, but callback or duplicate behavior degraded materially."
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--stage-seconds", type=float, default=6.25)
    args = p.parse_args()

    if args.stage_seconds < 5.5:
        raise ProbeError("stage-seconds must be >= 5.5")

    root = Path(args.root).resolve()
    meta_path = root / META_REL
    exe = configured_retroarch(root)
    meta0 = read_meta(meta_path, fresh=True)
    hwnd = counter(meta0, "hwnd")
    if hwnd <= 0:
        raise ProbeError("Active WGC metadata has no capture HWND")

    u, k = win_api()
    if not u.IsWindow(hwnd):
        raise ProbeError("Active WGC capture HWND is no longer valid")
    if u.IsIconic(hwnd):
        raise ProbeError("RetroArch is minimized. Restore it first.")

    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    image = process_path(k, int(pid.value))
    if not image or not same_path(image, exe):
        raise ProbeError("Active WGC HWND is not owned by the configured RetroArch executable")

    rect = wintypes.RECT()
    if not u.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ProbeError("Unable to read RetroArch window rectangle")

    left, top = int(rect.left), int(rect.top)
    width = max(64, int(rect.right - rect.left))
    height = max(64, int(rect.bottom - rect.top))

    original_foreground = int(u.GetForegroundWindow())

    print("A4 occlusion probe")
    print("Keep gameplay visibly moving on the onn.")
    print("Stage 1/3: visible baseline...")
    base_start = read_meta(meta_path, fresh=True)
    base_end = wait_meta(meta_path, args.stage_seconds)
    base = summarize(base_start, base_end)

    cover = 0
    covered_end = None
    focus_during_cover = 0

    try:
        print("Stage 2/3: covering RetroArch and moving host focus away from it...")
        cover = int(
            u.CreateWindowExW(
                WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
                "STATIC",
                "PrivyHub A4 Host Coexistence Probe",
                WS_POPUP | WS_VISIBLE | SS_CENTER | SS_CENTERIMAGE,
                left, top, width, height,
                None, None, k.GetModuleHandleW(None), None,
            )
        )
        if cover <= 0:
            raise ProbeError("Unable to create temporary cover window")

        u.SetWindowPos(cover, -1, left, top, width, height, SWP_SHOWWINDOW)
        u.UpdateWindow(cover)
        u.SetForegroundWindow(cover)
        time.sleep(0.75)

        focus_during_cover = int(u.GetForegroundWindow())
        covered_end = wait_meta(meta_path, args.stage_seconds)
        covered = summarize(base_end, covered_end)

    finally:
        if cover > 0:
            try:
                u.DestroyWindow(cover)
            except Exception:
                pass

    if covered_end is None:
        raise ProbeError("Occlusion stage did not complete")

    time.sleep(0.75)

    print("Stage 3/3: cover removed...")
    restored_end = wait_meta(meta_path, args.stage_seconds)
    restored = summarize(covered_end, restored_end)

    verdict, interpretation = classify(base, covered)

    result = {
        "schema": "privyhub_a4_host_coexistence_occlusion_probe_v1",
        "verdict": verdict,
        "interpretation": interpretation,
        "baseline": base,
        "covered": covered,
        "restored": restored,
        "focus": {
            "original_foreground_hwnd": original_foreground,
            "retroarch_hwnd": hwnd,
            "cover_hwnd": cover,
            "foreground_during_cover_hwnd": focus_during_cover,
            "cover_became_foreground": cover > 0 and focus_during_cover == cover,
            "retroarch_not_foreground_during_cover": focus_during_cover != hwnd,
        },
        "privacy": "No network addresses are recorded.",
    }

    out_json = root / OUT_JSON
    out_txt = root / OUT_TXT
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    text = (
        "PrivyHub A4 host coexistence occlusion probe\n\n"
        f"Verdict: {verdict}\n"
        f"{interpretation}\n\n"
        "Baseline visible:\n"
        + json.dumps(base, indent=2)
        + "\n\nRetroArch fully covered, not minimized:\n"
        + json.dumps(covered, indent=2)
        + "\n\nCover removed:\n"
        + json.dumps(restored, indent=2)
        + "\n\nHost focus:\n"
        + json.dumps(result["focus"], indent=2)
        + "\n\nNote: no network addresses are collected by this probe.\n"
    )
    out_txt.write_text(text, encoding="utf-8")

    print()
    print(f"Verdict: {verdict}")
    print(interpretation)
    print()
    print(f"Saved: {OUT_TXT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProbeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
