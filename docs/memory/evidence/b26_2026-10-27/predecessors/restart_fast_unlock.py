"""B24: `PRIVYHUB_RESTART_FAST_UNLOCK=1`, inside the adopted `PRIVYHUB_RESTART_FAST=1` (G-A5) -- the ready answers at the
new encoder's check, the old audio's stop runs after it outside the lock, the old encoder's frames stop at the kill.

CL-B13 cell 1: return 1's picture came back at 3.12 s because the old audio's stop ran 2,088 ms in the worker (the old
capture's SIGTERM `wait(timeout=2)` expiring; 203-352 ms otherwise) while the ready's `status()` waited on the lock
until `done`; at returns 3-4 the old encoder's flushed frames were forwarded to +0.35 / +0.39 s because the relay was
stopped only after its 471 / 421-ms exit. Here (`RestartFastUnlock`, the adopted class with its worker replaced; the
request half inherited unchanged):
- under the lock: the old audio's stop started first (its first act silences the old sender), **the relay stopped**,
  the old encoder SIGTERMed, the capture target selected meanwhile, SIGKILL after a 100-ms grace, the new encoder
  spawned as G-A5's `_spawn_locked` does it, `prepare`, today's 0.75-s check (>= once) -> **the lock released**;
- beside it (a watchdog thread): the old capture SIGKILLed if alive 300 ms after the stop began;
- after the lock: the old audio's stop joined (cap 10 s) and logged (`restart_fast_audio_stop`), then the new audio
  (the session checked under the lock before and after).
Absent = the adopted G-A5 worker: nothing imports this module. Design:
`docs/memory/evidence/b24_2026-10-26/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Any

from restart_fast import RestartFast, STARTUP_CHECK_S

FLAG_ENV = "PRIVYHUB_RESTART_FAST_UNLOCK"
KILL_GRACE_S = 0.10         # the old encoder's SIGTERM grace before SIGKILL (its frames go nowhere: the relay is closed)
CAPTURE_BOUND_S = 0.30      # the old audio capture SIGKILLed if alive this long after the stop began (not 2 s)
AUDIO_JOIN_CAP_S = 10.0     # the old audio's stop joined at most this long (the code's own bounds sum to ~10 s)


def enabled(environ: Any) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


class RestartFastUnlock(RestartFast):
    def config(self) -> dict[str, Any]:
        return {"kill_grace_s": KILL_GRACE_S, "capture_bound_s": CAPTURE_BOUND_S, "audio_join_cap_s": AUDIO_JOIN_CAP_S,
                "startup_check_s": STARTUP_CHECK_S}

    def _run(self, manager: Any, ns: Any, ffmpeg: Any, client_ip: str, port: int, process_id: int, t0: float,
             timings: dict[str, Any], locked: threading.Event) -> None:
        m = manager
        tail: dict[str, Any] = {}
        m._lock.acquire()
        try:
            timings["lock_ms"] = self._ms(t0)
            locked.set()
            try:
                self._restart_unlock_locked(m, ns, ffmpeg, client_ip, port, process_id, t0, timings, tail)
                ok = True
            except Exception as exc:
                try:
                    m._stop_locked()
                except Exception:
                    pass
                timings["failed_ms"] = self._ms(t0)
                ok = False
                error = f"{type(exc).__name__}: {str(exc)[:200]}"
            timings["unlocked_ms"] = self._ms(t0)
        finally:
            m._lock.release()
        self.last = dict(timings, ok=ok)
        if ok:
            self._log("restart_fast_done", **timings)
        else:
            self._log("restart_fast_failed", error=error, **timings)
        self._tail(m, ns, ffmpeg, client_ip, process_id, t0, tail, ok)

    def _restart_unlock_locked(self, m: Any, ns: Any, ffmpeg: Any, client_ip: str, port: int, process_id: int,
                               t0: float, timings: dict[str, Any], tail: dict[str, Any]) -> None:
        # the old audio first: its stop's first act silences the old sender; the capture noted for its bound
        capture = getattr(m._session_io.audio, "_process", None)
        stop_at = self._clock()
        ended: dict[str, float] = {}

        def stop_old_audio() -> None:
            try:
                m._session_io.stop_stream()
            finally:
                ended["at"] = self._clock()

        audio_stop = threading.Thread(target=stop_old_audio, name="PrivyHub-Restart-Fast-Audio", daemon=True)
        audio_stop.start()
        killed = threading.Event()
        tail.update(audio_stop=audio_stop, capture=capture, stop_at=stop_at, killed=killed, ended=ended)
        threading.Thread(target=self._capture_watchdog, args=(audio_stop, capture, stop_at, killed),
                         name="PrivyHub-Restart-Fast-Capture", daemon=True).start()
        m._host_telemetry.stop()
        # the relay first: the old encoder's frames stop being forwarded here, whatever it still flushes
        m._fec_relay.stop()
        timings["relay_stopped_ms"] = self._ms(t0)
        # the old encoder: SIGTERM, the next capture target meanwhile, SIGKILL after the grace
        old, old_capture = m._process, m._capture_process
        for p in (old, old_capture):
            if p is not None and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        target_error: Exception | None = None
        try:
            target = m._select_capture_target(managed_process_id=process_id)
        except Exception as exc:   # raised after the old encoder's end, as G-A5's spawn would
            target, target_error = None, exc
        deadline = self._clock() + KILL_GRACE_S
        for p in (old, old_capture):
            if p is None:
                continue
            while p.poll() is None and self._clock() < deadline:
                time.sleep(0.005)
            if p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass
            try:
                p.wait(timeout=5)
            except Exception:
                pass
        timings["released_ms"] = self._ms(t0)
        # today's other field resets (G-A5's worker)
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
        if target_error is not None:
            raise ns.NativeStreamError(f"Unable to start Linux native video: {target_error}") from target_error
        self._spawn_with_target_locked(m, ns, ffmpeg, client_ip, port, process_id, target)
        timings["spawned_ms"] = self._ms(t0)
        spawned_at = self._clock()
        m._client_port = port
        if ns.AUDIO_CODEC is not None and (refusal := ns.AUDIO_CODEC.prepare(m._session_io.audio, client_ip)):
            raise ns.NativeStreamError(refusal)
        check_deadline = spawned_at + STARTUP_CHECK_S
        while True:
            if m._process is None or m._process.poll() is not None or not m._fec_relay.running:
                log_tail = m._tail_log()
                raise ns.NativeStreamError("Linux native video exited during startup."
                                           + (f"\n\nFFmpeg log:\n{log_tail}" if log_tail else ""))
            if self._clock() >= check_deadline:
                break
            time.sleep(0.05)
        timings["checked_ms"] = self._ms(t0)
        tail["proc"] = m._process

    @staticmethod
    def _spawn_with_target_locked(m: Any, ns: Any, ffmpeg: Any, client_ip: str, port: int, process_id: int,
                                  target: Any) -> None:
        """G-A5's `_spawn_locked` from the capture target on, unchanged in content (the target selected earlier)."""
        capture_target = dict(target)
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

    def _capture_watchdog(self, audio_stop: threading.Thread, capture: Any, stop_at: float,
                          killed: threading.Event) -> None:
        """The old capture SIGKILLed if it still lives CAPTURE_BOUND_S after the stop began (its SIGTERM wait is 2 s)."""
        while audio_stop.is_alive() and self._clock() - stop_at < CAPTURE_BOUND_S:
            audio_stop.join(0.01)
        if audio_stop.is_alive() and capture is not None and capture.poll() is None:
            try:
                capture.kill()
                killed.set()
            except Exception:
                pass

    def _tail(self, m: Any, ns: Any, ffmpeg: Any, client_ip: str, process_id: int, t0: float, tail: dict[str, Any],
              ok: bool) -> None:
        """After the lock: the old capture bounded, the old audio's stop joined and logged, then the new audio."""
        audio_stop = tail.get("audio_stop")
        if audio_stop is None:
            return
        capture, stop_at = tail.get("capture"), tail.get("stop_at", self._clock())
        audio_stop.join(max(0.0, AUDIO_JOIN_CAP_S - (self._clock() - stop_at)))
        joined = not audio_stop.is_alive()
        end = tail["ended"].get("at", self._clock())
        self._log("restart_fast_audio_stop", restart_fast_audio_stop_ms=round((end - stop_at) * 1000.0, 1),
                  restart_fast_audio_stop_end_ms=round((end - t0) * 1000.0, 1),
                  capture_returncode=(capture.poll() if capture is not None else None),
                  capture_killed_at_bound=tail["killed"].is_set(), joined=joined)
        if not ok:
            self._log("restart_fast_audio", started=False, why="the restart failed")
            return
        proc = tail.get("proc")
        with m._lock:
            current = proc is not None and m._process is proc and proc.poll() is None
        if not current:
            self._log("restart_fast_audio", started=False, why="the session changed before the new audio")
            return
        redundancy = m.audio_redundancy()
        m._session_io.audio.set_redundancy(copies=redundancy["copies"], offset_packets=redundancy["offset_packets"])
        m._session_io.start(ffmpeg=ffmpeg, client_ip=client_ip, audio_port=m.AUDIO_PORT, input_port=m.INPUT_PORT,
                            process_id=process_id)
        with m._lock:
            still = m._process is proc and proc.poll() is None
            if not still:
                m._session_io.stop_stream()
        self._log("restart_fast_audio", started=still, new_audio_ms=self._ms(t0),
                  why=None if still else "the session changed during the new audio's start: stopped again")
