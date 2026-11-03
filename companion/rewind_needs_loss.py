"""B33: no rewind without loss -- a stall or silence under 1 s with no loss behind it releases with `resume`, not `state`.

Inside the adopted `PRIVYHUB_LINK_RECOVERY=1` (no new adoption line, B26's convention); `PRIVYHUB_REWIND_NEEDS_LOSS=0`
turns it off (today byte for byte), `=1` turns it on without the umbrella. **Absent with no umbrella = today**:
nothing imports this module. Design: `docs/memory/evidence/b33_2026-10-31/design_written_before_code.md` (hashed
before this code).

TRIP-R2 §2: five stall pauses all evening (three in golf) each loaded B9's slot 9 at `stall_end`, ~0.45 s of play and
the presses in it undone. Here, at the release (B9's `Cores.release`, the one place a load happens), the episode
resumes without the load when all hold:
- short: release - onset < 1,000 ms (a silence or stall >= 1 s loads as today);
- evidence: a client heartbeat received in [onset - 2.5 s, release], with a predecessor;
- post-FEC loss 0: no heartbeat in that window shows a rise in `lost_packets` or `fec_unrecoverable_groups`;
- no dark span: no heartbeat in that window shows `audio_max_arrival_gap_ms` >= 250 (audio rides the same downlink);
- the uplink alive: the host's controller-sequence loss counter unchanged from the onset's sample to the release.
The decision cannot wait for the heartbeat that covers the stall itself (up to 2 s after the release): the rule is
"no loss known behind it at the release". The save still happens (B9 / B16, untouched); the pause still happened.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_REWIND_NEEDS_LOSS"
UMBRELLA_ENV = "PRIVYHUB_LINK_RECOVERY"
SHORT_MS = 1000.0           # "a stall or silence under 1 s"
LOOKBACK_S = 2.5            # the client's heartbeat interval (2 s) + margin
DARK_MS = 250               # an audio arrival gap this long = the downlink delivered nothing
RESUME_WHY = "no_loss_under_1s"
KEEP = 8                    # heartbeats kept (16 s at 2 s)


def mode(environ: Mapping[str, str]) -> tuple[bool, str | None]:
    """(on, how). Absent: on iff the umbrella is `1`; `0` off; `1` on; another value as absent, noted."""
    raw = (environ.get(FLAG_ENV) or "").strip()
    umbrella = (environ.get(UMBRELLA_ENV) or "").strip() == "1"
    if raw == "0":
        return False, "explicit 0"
    if raw == "1":
        return True, "explicit 1"
    note = f"; {raw[:32]!r} ignored (not 0 / 1)" if raw else ""
    if umbrella:
        return True, "implied by PRIVYHUB_LINK_RECOVERY=1" + note
    return False, (note[2:] if note else None)


def _int(v: Any) -> int | None:
    try:
        return None if v is None else int(v)
    except (TypeError, ValueError):
        return None


class Rule:
    def __init__(self, controller: Any = None, clock: Callable[[], float] = time.monotonic):
        self.controller = controller
        self._clock = clock
        self._lock = threading.Lock()
        self._hb: deque[dict[str, Any]] = deque(maxlen=KEEP)
        self.resumes = 0
        self.loads = 0

    def _uplink(self) -> int | None:
        v = _int(getattr(self.controller, "_lost_packets", None))
        return v if v is not None and v >= 0 else None

    def note_heartbeat(self, record: Mapping[str, Any], now: float | None = None) -> None:
        """The recovery's note_heartbeat: one sample per heartbeat (its receive time on this clock)."""
        s = {"rx": self._clock() if now is None else now,
             "lost": _int(record.get("lost_packets")),
             "unrec": _int(record.get("fec_unrecoverable_groups")),
             "audio_gap": _int(record.get("audio_max_arrival_gap_ms")),
             "uplink": self._uplink()}
        with self._lock:
            self._hb.append(s)

    def decide(self, onset: float, now: float | None = None) -> tuple[bool, str, dict[str, Any]]:
        """(resume, why, the terms read). `why` is the first failing term, or `no_loss_under_1s`."""
        now = self._clock() if now is None else now
        held_ms = round((now - onset) * 1000.0, 1)
        d: dict[str, Any] = {"held_ms": held_ms}
        if held_ms >= SHORT_MS:
            return False, "long", d
        with self._lock:
            hb = list(self._hb)
        idx = [i for i, h in enumerate(hb) if onset - LOOKBACK_S <= h["rx"] <= now]
        d["heartbeats_in_window"] = len(idx)
        if not idx or idx[0] == 0:
            return False, "no_heartbeat", d
        lost = unrec = 0
        gap = 0
        for i in idx:
            h, p = hb[i], hb[i - 1]
            for key in ("lost", "unrec"):
                if h[key] is None or p[key] is None:
                    if key == "lost":
                        return False, "no_heartbeat", d
                    continue                                   # an older client: no FEC counter
                delta = h[key] - p[key]
                if delta < 0:
                    return False, "counter_reset", d
                if key == "lost":
                    lost += delta
                else:
                    unrec += delta
            if h["audio_gap"] is not None:
                gap = max(gap, h["audio_gap"])
        d.update(window_lost_packets=lost, window_unrecoverable_groups=unrec, window_audio_max_gap_ms=gap)
        if lost > 0 or unrec > 0:
            return False, "loss", d
        if gap >= DARK_MS:
            return False, "dark_span", d
        base = [h for h in hb if h["rx"] <= onset]
        b = (base[-1] if base else hb[idx[0]])["uplink"]
        cur = self._uplink()
        if b is None or cur is None or cur < b:
            return False, "uplink_unknown", d
        d["uplink_lost_packets"] = cur - b
        if cur > b:
            return False, "uplink_loss", d
        return True, RESUME_WHY, d


def wire(cores: Any, recovery: Any, controller: Any, environ: Mapping[str, str]) -> Rule | None:
    """rewind_cores.wire's one call (mode `state`): the rule on B9's Cores and on the recovery's heartbeat."""
    on, how = mode(environ)
    if not on:
        return None
    rule = Rule(controller)
    cores.no_loss = rule
    recovery._rewind_needs_loss = rule
    recovery._log("rewind_needs_loss_config", how=how, short_ms=SHORT_MS, lookback_s=LOOKBACK_S, dark_ms=DARK_MS,
                  uplink_counter=rule._uplink() is not None)
    return rule
