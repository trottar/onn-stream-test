"""G8-S4: the encoder's per-second rate headroom, a named rate-control profile.

`PRIVYHUB_ENCODER_RC=<profile>`. **Absent (or empty) = today**: nothing imports this
module; the encoder command is byte for byte as before (`-b:v T -maxrate T -bufsize T`,
ffmpeg's `auto` -> the driver's CBR over a 1-s VBV window). The design is
`docs/memory/evidence/g8_s4_2026-10-18/design_written_before_code.md` (hashed before
this code).

- `tight`    -> `-rc_mode CBR`, `-maxrate T`,        `-bufsize T x 0.25` (a 250-ms window)
- `headroom` -> `-rc_mode VBR`, `-maxrate T x 1.10`, `-bufsize T x 0.25`
- anything else -> logged once, ignored (today's command).

T is each built command's own `-b:v` target, so the profile follows the start, every
live rung change (the actuator rebuilds the argv with the same builder) and the sized
rung. The frame cap (`-max_frame_size`), the GOP, `-bf` and the rest are untouched.
The host's driver (radeonsi) offers CQP, CBR and VBR only.
"""

from __future__ import annotations

import os
import threading
from typing import Any, Mapping

FLAG_ENV = "PRIVYHUB_ENCODER_RC"
BUFSIZE_OVERRIDE_ENV = "PRIVYHUB_ENC_BUFSIZE_K"     # native_stream's diagnostic knob

PROFILES: dict[str, dict[str, Any]] = {
    "tight": {"rc_mode": "CBR", "maxrate_x": 1.00, "bufsize_s": 0.25},
    "headroom": {"rc_mode": "VBR", "maxrate_x": 1.10, "bufsize_s": 0.25},
}


def parse(raw: Any) -> str | None:
    text = str(raw or "").strip().lower()
    return text if text in PROFILES else None


def rate_options(profile: str, target_kbps: int) -> dict[str, Any]:
    p = PROFILES[profile]
    t = int(target_kbps)
    return {"rc_mode": p["rc_mode"], "maxrate_kbps": int(round(t * p["maxrate_x"])),
            "bufsize_kbits": max(1, int(round(t * p["bufsize_s"])))}


def apply_to(command: list[str], profile: str, target_kbps: int) -> list[str]:
    """A copy of `command` with the profile's `-maxrate` / `-bufsize` values and `-rc_mode`
    right after the `-bufsize` value. A command without those options comes back unchanged."""
    out = list(command)
    try:
        i_max = out.index("-maxrate")
        i_buf = out.index("-bufsize")
    except ValueError:
        return out
    opts = rate_options(profile, target_kbps)
    out[i_max + 1] = f"{opts['maxrate_kbps']}k"
    out[i_buf + 1] = f"{opts['bufsize_kbits']}k"
    if "-rc_mode" in out:
        out[out.index("-rc_mode") + 1] = opts["rc_mode"]
    else:
        out[i_buf + 2:i_buf + 2] = ["-rc_mode", opts["rc_mode"]]
    return out


class EncoderRc:
    def __init__(self, raw: Any, log: Any = print, environ: Mapping[str, str] | None = None) -> None:
        self.raw = str(raw or "").strip()
        self.profile = parse(raw)
        self._log = log
        self._logged: set[str] = set()
        self._lock = threading.Lock()
        self._environ = os.environ if environ is None else environ
        self.applied = 0
        self.last: dict[str, Any] | None = None
        if self.profile is None:
            self._once("invalid", f"ignored ({self.raw!r} is not one of {sorted(PROFILES)}); the encoder "
                                  "command stays as today")

    def _once(self, key: str, text: str) -> None:
        if key not in self._logged:
            self._logged.add(key)
            try:
                self._log(f"PrivyHub encoder rate control ({FLAG_ENV}): {text}")
            except Exception:
                pass

    def apply(self, command: list[str], target_kbps: int) -> list[str]:
        if self.profile is None:
            return command
        if (self._environ.get(BUFSIZE_OVERRIDE_ENV) or "").strip():
            self._once("bufsize", f"{BUFSIZE_OVERRIDE_ENV} is set; the {self.profile} profile's -bufsize "
                                  "replaces it")
        out = apply_to(command, self.profile, target_kbps)
        with self._lock:
            self.applied += 1
            self.last = {"profile": self.profile, "target_kbps": int(target_kbps),
                         **rate_options(self.profile, target_kbps)}
        self._once("active", f"{self.profile}: " + ", ".join(
            f"{k} {v}" for k, v in rate_options(self.profile, target_kbps).items()) + f" at {int(target_kbps)} kbps")
        return out

    def status(self) -> dict[str, Any]:
        return {"flag": FLAG_ENV, "profile": self.profile, "raw_valid": self.profile is not None,
                "applied": self.applied, "last": self.last}


_SHARED: EncoderRc | None = None
_SHARED_LOCK = threading.Lock()


def shared_from_environ(environ: Mapping[str, str]) -> EncoderRc | None:
    """The one instance the hook uses; None when the flag is absent or empty."""
    global _SHARED
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    with _SHARED_LOCK:
        if _SHARED is None:
            _SHARED = EncoderRc(raw)
        return _SHARED


def from_environ_fresh(environ: Mapping[str, str] = os.environ, log: Any = print) -> EncoderRc | None:
    """A new instance (tests and harnesses)."""
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    return EncoderRc(raw, log=log, environ=environ)
