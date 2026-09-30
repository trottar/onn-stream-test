#!/usr/bin/env python3
"""C5-M1 golden: the Linux encoder argv and the profile/override fields the
companion would use, from the real NativeStreamManager code, with nothing
spawned. Run before the patch (golden_before.txt) and after it with the
selector unset (golden_after_unset.txt, must be byte-identical to before)
and set (golden_after_candidate.txt).

The manager is created with object.__new__ (no __init__: no relay, no
session I/O, no files); after the patch, the selection step __init__ runs
(_apply_profile_selection) is called explicitly. The display, the VAAPI
node and the window id are fixed stand-ins so the argv is comparable."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "companion"))
import native_stream as ns  # noqa: E402
M = ns.NativeStreamManager
M._linux_display = staticmethod(lambda: ":0")
M._linux_vaapi_device = staticmethod(lambda: Path("/dev/dri/renderD128"))
m = object.__new__(M)
if hasattr(m, "_apply_profile_selection"):
    m._apply_profile_selection()
argv = m._build_linux_ffmpeg_command(Path("/usr/bin/ffmpeg"), {"_window_id": 12345})
print("PRIVYHUB_* in env:", sorted(k for k in os.environ if k.startswith("PRIVYHUB_")))
print("argv:", " ".join(argv))
print("profile:", json.dumps(m.PROFILE.to_dict(), sort_keys=True))
print("WIDTH HEIGHT FPS GOP BITRATE MAX BF FEC:", m.WIDTH, m.HEIGHT, m.FPS, m.GOP_FRAMES,
      m.BITRATE_KBPS, m.MAX_BITRATE_KBPS, m.BFRAMES, m.FEC_GROUP_SIZE)
ov = m.encoder_overrides()
print("encoder_overrides.any_override:", ov["any_override"])
print("encoder_overrides.max_frame_size:", ov["max_frame_size_bytes"], ov["max_frame_size_source"])
