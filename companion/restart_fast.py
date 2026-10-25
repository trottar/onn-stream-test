"""B22: `PRIVYHUB_RESTART_FAST=1` -- a guarded client restart's start answered before the old session's teardown.

CL-B12 cell 1: the host's `native-stream-start?…&guard_end=1` ran 2.0-2.2 s from its entry to its response. Inside
it, `_stop_locked()` tore down the old audio (~0.7 s: joins, the capture's wait, two `pactl` calls) *before* it touched
the encoder; then the encoder's exit, the relay, xdotool and the new `Popen` (~0.45 s); then a fixed 0.75-s startup
check and the new audio. Here, for an eligible start (`guard_end=1`, Linux, an old encoder running):
- the request answers with a `status()` snapshot of the running session (the same profile, window and client) and
  `"restart_fast": {"armed": true, "old_stream_active": true}` -- after a worker thread holds the manager's lock;
- the worker kills the old encoder first (on Linux the encoder is the capture: x11grab in the same ffmpeg), stops the
  old audio beside the new encoder, starts the new encoder as today's start does, runs today's 0.75-s check (at least
  once), then `AUDIO_CODEC.prepare` and the new audio;
- the ready's `status()` waits on the same lock, so nothing resumes before the new encoder and audio are up.
Absent = today: nothing imports this module. Design: `docs/memory/evidence/b22_2026-10-24/design_written_before_code.md`
(hashed before this code).
"""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_RESTART_FAST"
STARTUP_CHECK_S = 0.75   # today's startup check (`_start_linux_locked`), unchanged
LOCK_WAIT_S = 2.0


def enabled(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def _ns():
    import native_stream   # the companion's module (already imported by the plugin)
    return native_stream


class RestartFast:
    def __init__(self, log: Callable[..., Any], clock: Callable[[], float] = time.monotonic) -> None:
        self._log = log
        self._clock = clock
        self.last: dict[str, Any] | None = None
        self._worker: threading.Thread | None = None

    def config(self) -> dict[str, Any]:
        return {"startup_check_s": STARTUP_CHECK_S, "lock_wait_s": LOCK_WAIT_S}

    @staticmethod
    def eligible(manager: Any) -> bool:
        """Linux and an old encoder running (with `guard_end=1`, checked by the caller); else today's start."""
        if not manager._linux_host():
            return False
        with manager._lock:
            p = manager._process
            return p is not None and p.poll() is None

    def start(self, manager: Any, client_ip: str, port: int, managed_process_id: int | None) -> dict[str, Any]:
        ns = _ns()
        t0 = self._clock()
        client_ip = manager._validated_ipv4(client_ip)
        port = manager._validated_port(int(port))
        try:
            ns.host_resource_sampling.start(manager.project_root)
        except Exception:
            pass
        ffmpeg, process_id = self._preflight(manager, ns, client_ip, managed_process_id)
        snapshot = manager.status()
        timings: dict[str, Any] = {}
        locked = threading.Event()
        self._worker = threading.Thread(
            target=self._run, name="PrivyHub-Restart-Fast", daemon=True,
            args=(manager, ns, ffmpeg, client_ip, port, process_id, t0, timings, locked))
        self._worker.start()
        if not locked.wait(LOCK_WAIT_S):
            self._log("restart_fast_lock_wait", waited_s=LOCK_WAIT_S)
            locked.wait()
        payload = dict(snapshot)
        payload["restart_fast"] = {"armed": True, "old_stream_active": True}
        response_ms = round((self._clock() - t0) * 1000.0, 1)
        self._log("restart_fast", response_ms=response_ms, lock_ms=timings.get("lock_ms"))
        return payload

    @staticmethod
    def _preflight(manager: Any, ns: Any, client_ip: str, managed_process_id: Any) -> tuple[Any, int]:
        """Today's checks, read only (the audio codec's refusal without `prepare`); raise before anything changes."""
        err = ns.NativeStreamError
        try:
            process_id = int(managed_process_id)
        except (TypeError, ValueError) as exc:
            raise err("Linux native video requires the managed RetroArch process ID.") from exc
        from pathlib import Path
        if process_id <= 0 or not Path(f"/proc/{process_id}").is_dir():
            raise err("The managed RetroArch process is no longer active.")
        ffmpeg = manager._find_ffmpeg()
        if ffmpeg is None:
            raise err("FFmpeg was not found on the Linux host.")
        if manager._linux_display() is None:
            raise err("Linux native video requires an active X11 DISPLAY.")
        if manager._linux_xdotool() is None:
            raise err("Linux native video requires xdotool for fail-closed managed-window discovery.")
        if manager._linux_vaapi_device() is None:
            raise err("Linux native video requires exactly one accessible DRM render node.")
        codec = ns.AUDIO_CODEC
        if codec is not None and codec.active and ns._audio_codec.CODEC_OPUS not in codec.declared(client_ip):
            raise err(ns._audio_codec.REFUSAL)
        return ffmpeg, process_id

    def _ms(self, t0: float) -> float:
        return round((self._clock() - t0) * 1000.0, 1)

    def _run(self, manager: Any, ns: Any, ffmpeg: Any, client_ip: str, port: int, process_id: int, t0: float,
             timings: dict[str, Any], locked: threading.Event) -> None:
        with manager._lock:
            timings["lock_ms"] = self._ms(t0)
            locked.set()
            try:
                self._restart_locked(manager, ns, ffmpeg, client_ip, port, process_id, t0, timings)
                self.last = dict(timings, ok=True)
                self._log("restart_fast_done", **timings)
            except Exception as exc:
                try:
                    manager._stop_locked()
                except Exception:
                    pass
                timings["failed_ms"] = self._ms(t0)
                self.last = dict(timings, ok=False)
                self._log("restart_fast_failed", error=f"{type(exc).__name__}: {str(exc)[:200]}", **timings)

    def _restart_locked(self, manager: Any, ns: Any, ffmpeg: Any, client_ip: str, port: int, process_id: int,
                        t0: float, timings: dict[str, Any]) -> None:
        m = manager
        # today's _stop_locked order for the telemetry (a no-op on Linux), then the encoder first: the capture's release
        m._host_telemetry.stop()
        m._kill_managed_process(m._process)
        m._kill_managed_process(m._capture_process)
        timings["released_ms"] = self._ms(t0)
        # the rest of the old teardown beside the new encoder: the old audio
        audio_stop = threading.Thread(target=m._session_io.stop_stream, name="PrivyHub-Restart-Fast-Audio",
                                      daemon=True)
        audio_stop.start()
        # today's _stop_locked field resets (the relay stopped)
        m._fec_relay.stop()
        m._process = None
        m._capture_process = None
        m._encoder_command = None
        m._client_port = None
        m._active_bitrate_kbps = m.BITRATE_KBPS
        m._active_width = m.WIDTH
        m._active_height = m.HEIGHT
        if m._capture_target is not None:
            m._last_capture_target = m._capture_target
        m._capture_target = None
        if m._log_handle is not None:
            try:
                m._log_handle.close()
            except Exception:
                pass
            m._log_handle = None
        try:
            self._spawn_locked(m, ns, ffmpeg, client_ip, port, process_id)
            timings["spawned_ms"] = self._ms(t0)
            spawned_at = self._clock()
        finally:
            audio_stop.join()
            timings["audio_stopped_ms"] = self._ms(t0)
        m._client_port = port
        # today's prepare (now after the old audio stopped); a refusal fails the restart
        if ns.AUDIO_CODEC is not None and (refusal := ns.AUDIO_CODEC.prepare(m._session_io.audio, client_ip)):
            raise ns.NativeStreamError(refusal)
        # today's startup check, 0.75 s from the Popen; at least one check
        deadline = spawned_at + STARTUP_CHECK_S
        while True:
            if m._process is None or m._process.poll() is not None or not m._fec_relay.running:
                log_tail = m._tail_log()
                raise ns.NativeStreamError("Linux native video exited during startup."
                                           + (f"\n\nFFmpeg log:\n{log_tail}" if log_tail else ""))
            if self._clock() >= deadline:
                break
            time.sleep(0.05)
        timings["checked_ms"] = self._ms(t0)
        redundancy = m.audio_redundancy()
        m._session_io.audio.set_redundancy(copies=redundancy["copies"], offset_packets=redundancy["offset_packets"])
        m._session_io.start(ffmpeg=ffmpeg, client_ip=client_ip, audio_port=m.AUDIO_PORT, input_port=m.INPUT_PORT,
                            process_id=process_id)
        timings["done_ms"] = self._ms(t0)

    @staticmethod
    def _spawn_locked(m: Any, ns: Any, ffmpeg: Any, client_ip: str, port: int, process_id: int) -> None:
        """Today's `_start_linux_locked` from the capture target to the `Popen`, unchanged in content."""
        capture_target = m._select_capture_target(managed_process_id=process_id)
        capture_target = dict(capture_target)
        capture_target["backend"] = "x11grab_window"
        m._capture_target = capture_target
        m.data_dir.mkdir(parents=True, exist_ok=True)
        m.log_dir.mkdir(parents=True, exist_ok=True)
        m._log_handle = open(m.log_path, "a", encoding="utf-8", errors="replace", buffering=1)
        m._log_handle.write("\n" + "=" * 72 + "\n")
        m._log_handle.write(f"Starting PrivyHub Linux native-video backend v{m.ALPHA_VERSION}\n")
        m._log_handle.write(f"Profile: {m.PROFILE.id} {m.WIDTH}x{m.HEIGHT}@{m.FPS}, "
                            f"{m.BITRATE_KBPS}/{m.MAX_BITRATE_KBPS} kbps "
                            f"H.264 VAAPI, GOP={m.GOP_FRAMES}, BF={m.BFRAMES}\n")
        m._log_handle.write("Capture backend: exact X11 window via x11grab\n")
        m._log_handle.write("Capture: managed RetroArch window "
                            f"(pid={process_id}, window_id={capture_target['_window_id']}, "
                            f"discovered={capture_target['width']}x{capture_target['height']})\n")
        m._log_handle.write(f"Window title: {capture_target.get('title', '')}\n")
        m._log_handle.write(f"Video FEC: XOR {m.FEC_GROUP_SIZE}+1; FFmpeg RTP -> loopback relay -> onn; "
                            f"encoder={m.BITRATE_KBPS} kbps\n")
        m._log_handle.write("=" * 72 + "\n")
        m._log_handle.flush()
        try:
            m._fec_relay.start(client_ip=client_ip, client_port=port)
            start_kw: dict[str, Any] = {}
            if ns.START_RUNG is not None:   # G8-S2: the session's first target
                start_kw = ns.START_RUNG.encoder_kwargs(client_ip)
                m._active_bitrate_kbps = int(start_kw.get("bitrate_kbps", m.BITRATE_KBPS))
            linux_command = m._build_linux_ffmpeg_command(ffmpeg=ffmpeg, capture_target=capture_target, **start_kw)
            m._encoder_command = list(linux_command)
            m._log_handle.write("encoder argv: " + " ".join(linux_command) + "\n")
            m._log_handle.flush()
            m._process = subprocess.Popen(linux_command, cwd=str(m.project_root), stdin=subprocess.DEVNULL,
                                          stdout=m._log_handle, stderr=subprocess.STDOUT)
        except Exception as exc:
            raise ns.NativeStreamError(f"Unable to start Linux native video: {exc}") from exc
