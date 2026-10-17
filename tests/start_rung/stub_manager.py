"""G8-S2: a `NativeStreamManager` whose `_start_linux_locked` runs for real against stubs.

Nothing is spawned (the module's `subprocess.Popen` is replaced while it runs), no
socket is opened (the FEC relay and session I/O are recorders), no X11 / VAAPI is
read, the log goes to a temp directory, and the 0.75-s startup watch runs on a fake
clock. Every stub call is recorded, so two modules (HEAD's and today's) can be
compared call for call. The managed process is this process (its /proc entry
exists); the window id is a fixed fixture.
"""

from __future__ import annotations

import os
import tempfile
import types
from pathlib import Path
from typing import Any


class Recorder:
    def __init__(self, calls: list, name: str, ret: Any = None):
        self.calls, self.name, self.ret = calls, name, ret

    def __call__(self, *a, **kw):
        self.calls.append((self.name, [str(x) for x in a], sorted((k, str(v)) for k, v in kw.items())))
        return self.ret() if callable(self.ret) else self.ret


class FakeProc:
    def __init__(self, argv):
        self.argv = list(argv)
        self.pid = 1

    def poll(self):
        return None


def stub_manager(mod: Any, calls: list) -> Any:
    tmp = Path(tempfile.mkdtemp(prefix="g8_s2_stub_"))
    M = mod.NativeStreamManager
    m = object.__new__(M)
    m._apply_profile_selection()
    m.project_root = tmp
    m.data_dir = tmp / "data"
    m.log_dir = tmp / "logs"
    m.log_path = m.log_dir / "native_video_alpha.log"
    m._process = None
    m._capture_process = None
    m._log_handle = None
    m._client_port = None
    m._active_bitrate_kbps = m.BITRATE_KBPS
    m._active_width, m._active_height = m.WIDTH, m.HEIGHT
    m._capture_target = None
    m._encoder_command = None
    m._last_capture_target = None
    m._linux_host = lambda: True
    m._find_ffmpeg = lambda: Path("/fixture/ffmpeg")
    m._linux_display = lambda: ":0"
    m._linux_xdotool = lambda: "/fixture/xdotool"
    m._linux_vaapi_device = lambda: "/fixture/renderD128"
    m._kill_managed_process = Recorder(calls, "kill")
    m._host_telemetry = types.SimpleNamespace(stop=Recorder(calls, "host_telemetry.stop"))
    m._fec_relay = types.SimpleNamespace(stop=Recorder(calls, "fec.stop"), start=Recorder(calls, "fec.start"),
                                         running=True)
    m._session_io = types.SimpleNamespace(stop_stream=Recorder(calls, "session_io.stop_stream"),
                                          start=Recorder(calls, "session_io.start"),
                                          audio=types.SimpleNamespace(set_redundancy=Recorder(calls, "audio.redundancy")))
    m._select_capture_target = lambda managed_process_id: {"_window_id": 4242, "pid": managed_process_id,
                                                           "width": 879, "height": 720, "title": "fixture"}
    m._public_capture_target = lambda t: {"backend": (t or {}).get("backend")}
    m.status = lambda: {"bitrate_kbps": m._active_bitrate_kbps, "source_bitrate_kbps": m._active_bitrate_kbps,
                        "encoder_command": list(m._encoder_command or ())}
    return m


def run_start(mod: Any, target: str, calls: list | None = None) -> dict[str, Any]:
    """`_start_linux_locked(target, 48100, <this pid>)` on a stubbed manager; the argv, level, payload, calls."""
    calls = [] if calls is None else calls
    m = stub_manager(mod, calls)
    spawned: list[FakeProc] = []
    t = {"now": 0.0}
    saved = (mod.subprocess, mod.time)
    mod.subprocess = types.SimpleNamespace(Popen=lambda argv, **k: spawned.append(FakeProc(argv)) or spawned[-1],
                                           DEVNULL=-3, STDOUT=-2)
    mod.time = types.SimpleNamespace(monotonic=lambda: t.__setitem__("now", t["now"] + 0.1) or t["now"],
                                     sleep=lambda s: None)
    try:
        payload = m._start_linux_locked(client_ip=target, port=48100, managed_process_id=os.getpid())
    finally:
        mod.subprocess, mod.time = saved
        if m._log_handle is not None:
            m._log_handle.close()
    log = m.log_path.read_text() if m.log_path.exists() else ""
    return {"argv": spawned[0].argv if spawned else None, "active_bitrate_kbps": m._active_bitrate_kbps,
            "payload": payload, "calls": calls, "log": log, "manager": m}
