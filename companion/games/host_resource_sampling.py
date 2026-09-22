"""D-BASE-T1 piece 2: run `tools/host_resource_sampler.py` per session.

The companion starts the sampler when a native stream starts and stops it
when the stream stops, so every future session leaves a host temperature
and resource series behind without anyone assembling a harness first.

Three rules, all of them about not disturbing the stream:

  - the sampler is a **separate process at `nice 10`**, so it cannot take
    time from the encoder or the relay;
  - **every failure is swallowed.** If the sampler will not start, the
    session starts anyway and `status` reports the error;
  - start and stop are **idempotent**. The recovery path can call
    `NativeStreamManager.start()` again on a session that is already
    running, and that must not leave a second sampler behind.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading

from pathlib import Path
from typing import Any

SAMPLER_RELATIVE = Path("tools") / "host_resource_sampler.py"

# Matches the sampler's own default; named here so `status` can report it.
DEFAULT_INTERVAL_S = 30

_lock = threading.Lock()
_process: subprocess.Popen[bytes] | None = None
_error: str = ""
_started_for: str = ""


def _sampler_path(
    project_root: Path,
) -> Path:
    return Path(project_root) / SAMPLER_RELATIVE


def start(
    project_root: Path,
    *,
    interval_s: int = DEFAULT_INTERVAL_S,
) -> dict[str, Any]:
    """Start the sampler if it is not already running. Never raises."""

    global _process, _error, _started_for

    with _lock:
        if _process is not None and _process.poll() is None:
            return _status_locked()

        _process = None
        _error = ""

        script = _sampler_path(project_root)

        if not script.is_file():
            _error = f"sampler not found: {SAMPLER_RELATIVE}"
            return _status_locked()

        try:
            _process = subprocess.Popen(
                [
                    sys.executable,
                    str(script),
                    "--interval",
                    str(int(interval_s)),
                    "--project-root",
                    str(project_root),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(project_root),
                start_new_session=True,
                preexec_fn=(
                    (lambda: os.nice(10))
                    if hasattr(os, "nice")
                    else None
                ),
            )
            _started_for = str(project_root)
        except Exception as exc:
            _process = None
            _error = f"{type(exc).__name__}: {exc}"

        return _status_locked()


def stop() -> dict[str, Any]:
    """Stop the sampler if it is running. Never raises."""

    global _process

    with _lock:
        process = _process

        if process is None:
            return _status_locked()

        try:
            if process.poll() is None:
                process.terminate()

                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()

                    try:
                        process.wait(timeout=5)
                    except Exception:
                        pass
        except Exception as exc:
            globals()["_error"] = f"{type(exc).__name__}: {exc}"
        finally:
            _process = None

        return _status_locked()


def status() -> dict[str, Any]:
    with _lock:
        return _status_locked()


def _status_locked() -> dict[str, Any]:
    running = _process is not None and _process.poll() is None

    return {
        "running": running,
        "pid": _process.pid if running and _process else None,
        "interval_s": DEFAULT_INTERVAL_S,
        "error": _error or None,
    }
