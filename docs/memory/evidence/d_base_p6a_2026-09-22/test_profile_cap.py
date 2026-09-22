#!/usr/bin/env python3
"""D-BASE-P6a: the frame cap comes from the profile, and the override wins.

Three states have to be distinguishable, and the third is the one the old
`_env_int` could not express:

  1. no variable set        -> profile's 90,000, `any_override` false
  2. variable set to N      -> N, `any_override` true
  3. variable set to **0**  -> uncapped, argv omits the flag, override true

Run from the repository root:

    PYTHONPATH=companion python3 \
      docs/memory/evidence/d_base_p6a_2026-09-22/test_profile_cap.py
"""
import os
import sys
from pathlib import Path

import native_stream as ns
from native_stream_profiles import NATIVE_GAME_720P60_REFERENCE

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
        print(f"  FAIL {name}: got {got!r}, want {want!r}")
    else:
        print(f"  ok   {name} = {got!r}")


m = ns.NativeStreamManager.__new__(ns.NativeStreamManager)
m.project_root = Path("/home/privyhub/Projects/onn-stream-test")
m._log_handle = None
m._linux_display = lambda: ":0"
m._linux_vaapi_device = lambda: Path("/dev/dri/renderD128")


def build():
    return ns.NativeStreamManager._build_linux_ffmpeg_command(
        m, ffmpeg=Path("/usr/bin/ffmpeg"), capture_target={"_window_id": 1})


def cap_of(argv):
    return argv[argv.index("-max_frame_size") + 1] if "-max_frame_size" in argv else None


def clear():
    for k in ("PRIVYHUB_ENC_MAX_FRAME_SIZE", "PRIVYHUB_ENC_BUFSIZE_K"):
        os.environ.pop(k, None)


print("0. the profile declares the cap")
check("profile field", NATIVE_GAME_720P60_REFERENCE.max_frame_size_bytes, 90000)
check("to_dict carries it",
      NATIVE_GAME_720P60_REFERENCE.to_dict()["max_frame_size_bytes"], 90000)

print("1. no variable set -> the profile's cap, and it is NOT an override")
clear()
argv = build()
ov = ns.NativeStreamManager.encoder_overrides(m)
check("argv cap", cap_of(argv), "90000")
check("max_frame_size_bytes", ov["max_frame_size_bytes"], 90000)
check("source", ov["max_frame_size_source"], "profile")
check("default_max_frame_size_bytes", ov["default_max_frame_size_bytes"], 90000)
check("uncapped", ov["uncapped"], False)
check("any_override", ov["any_override"], False)
check("bufsize untouched", argv[argv.index("-bufsize") + 1], "7000k")

print("2. variable set to N -> N wins, and it IS an override")
os.environ["PRIVYHUB_ENC_MAX_FRAME_SIZE"] = "60000"
argv = build()
ov = ns.NativeStreamManager.encoder_overrides(m)
check("argv cap", cap_of(argv), "60000")
check("source", ov["max_frame_size_source"], "PRIVYHUB_ENC_MAX_FRAME_SIZE")
check("any_override", ov["any_override"], True)
check("default still reported", ov["default_max_frame_size_bytes"], 90000)

print("3. variable set to 0 -> UNCAPPED, the flag is absent")
os.environ["PRIVYHUB_ENC_MAX_FRAME_SIZE"] = "0"
argv = build()
ov = ns.NativeStreamManager.encoder_overrides(m)
check("flag absent", "-max_frame_size" in argv, False)
check("max_frame_size_bytes", ov["max_frame_size_bytes"], None)
check("uncapped", ov["uncapped"], True)
check("source", ov["max_frame_size_source"], "PRIVYHUB_ENC_MAX_FRAME_SIZE")
check("any_override", ov["any_override"], True)

print("4. the uncapped argv is byte for byte the pre-P6 command")
uncapped = list(argv)
clear()
capped = build()
check("capped differs by exactly the two flag tokens",
      [a for a in capped if a not in uncapped] , ["-max_frame_size", "90000"])
check("same length + 2", len(capped), len(uncapped) + 2)

print("5. a malformed value falls back to the profile, it does not raise")
os.environ["PRIVYHUB_ENC_MAX_FRAME_SIZE"] = "ninety thousand"
ov = ns.NativeStreamManager.encoder_overrides(m)
check("argv cap", cap_of(build()), "90000")
check("source", ov["max_frame_size_source"], "profile")
check("any_override", ov["any_override"], False)

print("6. a negative value falls back to the profile too")
os.environ["PRIVYHUB_ENC_MAX_FRAME_SIZE"] = "-1"
check("argv cap", cap_of(build()), "90000")

print("7. the bufsize knob is unchanged and still default off")
clear()
check("default bufsize", build()[build().index("-bufsize") + 1], "7000k")
os.environ["PRIVYHUB_ENC_BUFSIZE_K"] = "117"
argv = build()
check("override bufsize", argv[argv.index("-bufsize") + 1], "117k")
check("cap still from profile", cap_of(argv), "90000")
check("any_override", ns.NativeStreamManager.encoder_overrides(m)["any_override"], True)
clear()

print("8. a profile with the cap at 0 emits no flag")
import dataclasses
m2 = ns.NativeStreamManager.__new__(ns.NativeStreamManager)
m2.project_root = m.project_root
m2._log_handle = None
m2._linux_display = m._linux_display
m2._linux_vaapi_device = m._linux_vaapi_device
m2.PROFILE = dataclasses.replace(NATIVE_GAME_720P60_REFERENCE,
                                 max_frame_size_bytes=0)
argv = ns.NativeStreamManager._build_linux_ffmpeg_command(
    m2, ffmpeg=Path("/usr/bin/ffmpeg"), capture_target={"_window_id": 1})
check("flag absent", "-max_frame_size" in argv, False)

print("9. a negative profile value is rejected at construction")
try:
    dataclasses.replace(NATIVE_GAME_720P60_REFERENCE, max_frame_size_bytes=-5)
    check("rejected", False, True)
except ValueError:
    check("rejected", True, True)

print()
if FAILS:
    print(f"FAILED: {len(FAILS)}")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
