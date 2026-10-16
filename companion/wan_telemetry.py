"""G5-S1: WAN-aware telemetry classification (ROADMAP §G5).

Behind `PRIVYHUB_WAN_TELEMETRY=1`. **Absent = today**: the companion never
imports this module, builds nothing, starts no thread and adds no field.

It reuses Phase C's telemetry (ROADMAP §G5: "Reuse Phase C telemetry/adaptation
instead of creating a parallel WAN streamer"):

- the stream telemetry the client's health report already produces;
- the live ladder's transitions;
- the recovery state's pauses;
- the heartbeat's FEC and resync counters;
- G1-S1's overlay provider.

From these it reports §G5's eleven measures, each with its source field.
It classifies every 10-s window (5 reports, the ladder's own evidence
window) and the whole session.

The thresholds are §1 of
`docs/memory/evidence/G5_S1_WAN_TELEMETRY_CLASSIFICATION_2026-10-16.md`,
each from an existing record; nothing is invented. A measure with no
recorded threshold is reported and "not classified; G5-S2". **Nothing
here adapts anything** (that is G5-S2; the rules are in
`docs/WAN_ADAPTATION_RULES.md`).
"""

from __future__ import annotations

import json
import statistics
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

FLAG_ENV = "PRIVYHUB_WAN_TELEMETRY"
SCHEMA = "privyhub_wan_telemetry_v1"

# ---- thresholds (record §1; each with its source) ----------------------------
REPORT_INTERVAL_S = 2.0          # adaptive_bitrate.REPORT_INTERVAL_MS: the client's report cadence
WINDOW_REPORTS = 5               # adaptive_bitrate.WINDOW_REPORTS: "10 s of evidence for a decrease"
LOSS_PER_MIN_AT_LEAST = 10.0     # D-BASE close-out: post-FEC video loss < 10 / min
STALE_PER_MIN_AT_LEAST = 20.0    # D-BASE close-out: stale output drops < 20 / min
CAPACITY_FPS_BELOW = 50.0        # C3-L4-N1 capacity: fps < 50 on all 5 ...
CAPACITY_LOSS_AT_LEAST, CAPACITY_LOSS_OF = 50, 3          # ... and >= 50 lost on >= 3 of 5
CAPACITY_MILD_FPS_BELOW, CAPACITY_MILD_FPS_OF = 57.0, 4   # C3-L4-N2 capacity_mild: < 57 on >= 4 of 5
QUEUE_AT_LEAST, QUEUE_OF = 1, 3  # adaptive_bitrate ROUTINE queue clause: >= 1 on >= 3 of 5
GAP_ABOVE_MS, GAP_OF = 250, 2    # adaptive_bitrate FALLBACK gap clause: > 250 on >= 2 of 5

CLASSES = ("path-changed", "latency-limited", "starved", "capacity-limited", "lossy", "clean")
# Priority (ROADMAP §G5's order): session correctness, runaway latency,
# starvation, capacity, loss.
PRIORITY = {name: i for i, name in enumerate(CLASSES)}

NOT_CLASSIFIED = "not classified; G5-S2"


@dataclass
class Report:
    """One client report, from the stream-telemetry schema (no address)."""
    elapsed_ms: int | None
    fps: float | None
    queue: int | None
    gap_ms: int | None
    lost: int | None
    packets: int | None
    mbps: float | None
    jitter_ms: float | None
    rtt_ms: int | None
    stale: int | None
    waiting_for_idr: bool | None
    queue_delta: int | None
    fec_recovered: int | None = None
    fec_unrecoverable: int | None = None
    sender_avg_us: float | None = None
    sender_max_us: float | None = None
    sender_errors: int | None = None
    sent_bytes: int | None = None


@dataclass
class Event:
    elapsed_s: float
    kind: str        # overlay_path | recovery_pause | recovery_resume | ladder_transition | stream_resync
    detail: str = ""


def _num(x: Any) -> float | None:
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def report_from_telemetry(row: Mapping[str, Any]) -> Report | None:
    """A report from a stream-telemetry payload (live) or a recorded row; None if not fresh."""
    if not row.get("fresh"):
        return None
    rec = row.get("receiver") or {}
    dec = row.get("decoder") or {}
    lat = row.get("latency") or {}
    fec = row.get("fec") or {}
    snd = row.get("sender") or {}
    elapsed = row.get("elapsed_ms", row.get("session_elapsed_ms"))
    return Report(
        elapsed_ms=int(elapsed) if _num(elapsed) is not None else None,
        fps=_num(rec.get("recent_fps")),
        queue=_num(dec.get("queue_depth")),
        gap_ms=_num(lat.get("output_gap_ms")),
        lost=_num(rec.get("lost_packets_delta")),
        packets=_num(rec.get("packets_delta")),
        mbps=_num(rec.get("recent_mbps")),
        jitter_ms=_num(rec.get("interarrival_jitter_ms")),
        rtt_ms=_num(lat.get("control_round_trip_ms")),
        stale=_num(dec.get("stale_output_drops_delta")),
        waiting_for_idr=rec.get("waiting_for_idr") if isinstance(rec.get("waiting_for_idr"), bool) else None,
        queue_delta=_num(dec.get("queue_depth_delta")),
        fec_recovered=_num(fec.get("recovered_packets_delta")),
        fec_unrecoverable=_num(fec.get("unrecoverable_groups_delta")),
        sender_avg_us=_num(snd.get("send_call_avg_us")),
        sender_max_us=_num(snd.get("send_call_max_us")),
        sender_errors=_num(snd.get("send_errors_delta")),
        sent_bytes=_num(snd.get("sent_bytes_delta")),
    )


def _vals(reports: Iterable[Report], name: str) -> list[float]:
    return [v for v in (getattr(r, name) for r in reports) if v is not None]


def _pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)


def _measure(value: Any, source: str, **extra: Any) -> dict[str, Any]:
    return {"value": value, "source": source, **extra}


def measures(reports: list[Report], events: list[Event], overlay: Mapping[str, Any] | None,
             heartbeat: Mapping[str, Any] | None = None, span_s: float | None = None) -> dict[str, Any]:
    """§G5's eleven measures over a span of reports, each with its source.

    `span_s`: the span the rates are over (the session's elapsed span); default
    the reports' count × the report interval."""
    span_s = span_s or len(reports) * REPORT_INTERVAL_S
    per_min = (lambda total: round(total * 60.0 / span_s, 2)) if span_s else (lambda total: None)
    lost = _vals(reports, "lost")
    rec = _vals(reports, "fec_recovered")
    unrec = _vals(reports, "fec_unrecoverable")
    hb = heartbeat or {}
    if not rec and hb.get("fec_recovered_packets") is not None:
        rec = [hb["fec_recovered_packets"]]
        unrec = [hb.get("fec_unrecoverable_groups") or 0]
        fec_source = "heartbeat fec_recovered_packets / fec_unrecoverable_groups (deltas over the span)"
    else:
        fec_source = "fec.recovered_packets_delta / fec.unrecoverable_groups_delta"
    mbps = _vals(reports, "mbps")
    queue = _vals(reports, "queue")
    jitter = _vals(reports, "jitter_ms")
    rtt = _vals(reports, "rtt_ms")
    stale = _vals(reports, "stale")
    ov = overlay or {}
    return {
        "delivered_goodput_kbps": _measure(
            round(statistics.fmean(mbps) * 1000.0, 1) if mbps else None, "receiver.recent_mbps (mean)"),
        "packet_loss_per_min": _measure(
            {"post_fec": per_min(sum(lost)) if lost else None,
             "pre_fec": per_min(sum(lost) + sum(rec)) if lost and rec else "not recorded"},
            "receiver.lost_packets_delta (+ FEC recovered for pre-FEC)"),
        "fec_groups": _measure(
            {"recovered_packets": sum(rec) if rec else "not recorded",
             "unrecoverable_groups": sum(unrec) if unrec else "not recorded"},
            fec_source, classified=NOT_CLASSIFIED),
        "jitter_ms": _measure(
            {"p50": _pct(jitter, 0.5), "p95": _pct(jitter, 0.95)},
            "receiver.interarrival_jitter_ms (client running estimate; no per-packet arrival times carried)",
            classified=NOT_CLASSIFIED),
        "rtt_ms": _measure(
            {"p50": _pct(rtt, 0.5), "p95": _pct(rtt, 0.95)},
            "latency.control_round_trip_ms (the client's control echo)", classified=NOT_CLASSIFIED),
        "sender_pacing": _measure(
            {"send_call_avg_us": _pct(_vals(reports, "sender_avg_us"), 0.5),
             "send_call_max_us": max(_vals(reports, "sender_max_us"), default=None),
             "send_errors": sum(_vals(reports, "sender_errors")) if _vals(reports, "sender_errors") else None}
            if _vals(reports, "sender_avg_us") or _vals(reports, "sender_max_us") else "not recorded",
            "sender.send_call_avg_us / send_call_max_us / send_errors_delta"),
        "queue_depth": _measure(
            {"max": max(queue) if queue else None,
             "trend": (queue[-1] - queue[0]) if len(queue) > 1 else None},
            "decoder.queue_depth"),
        "decoder_starvation": _measure(
            {"stale_drops_per_min": per_min(sum(stale)) if stale else None,
             "waiting_for_idr_reports": sum(1 for r in reports if r.waiting_for_idr),
             "audio_prolonged_starvation_events": hb.get("audio_prolonged_starvation_events", "not recorded")},
            "decoder.stale_output_drops_delta, receiver.waiting_for_idr, heartbeat audio_prolonged_starvation_events"),
        "overlay_path": _measure(ov.get("path", "none"), "overlay provider state().path (G1-S1)"),
        "mtu_fragmentation": _measure(
            {"mtu": ov.get("mtu"), "oversize_drops": "not observed (no oversize-drop counter exists)"},
            "overlay provider state().mtu", classified=NOT_CLASSIFIED),
        "path_change_events": _measure(
            {"count": len(events),
             "events": [{"t_s": round(e.elapsed_s, 1), "kind": e.kind, "detail": e.detail} for e in events]},
            "overlay transitions, recovery pauses / resumes, ladder transitions, heartbeat stream_resyncs"),
    }


def classify_window(reports: list[Report], events: list[Event]) -> dict[str, Any]:
    """The classes one window meets (record §1), and its primary class."""
    span_s = len(reports) * REPORT_INTERVAL_S
    met: list[str] = []
    fps = [r.fps for r in reports]
    lost = [r.lost for r in reports]
    queue = [r.queue for r in reports]
    gap = [r.gap_ms for r in reports]
    n = len(reports)
    if events:
        met.append("path-changed")
    if (sum(1 for q in queue if q is not None and q >= QUEUE_AT_LEAST) >= QUEUE_OF
            or sum(1 for g in gap if g is not None and g > GAP_ABOVE_MS) >= GAP_OF):
        met.append("latency-limited")
    stale = _vals(reports, "stale")
    if stale and span_s and sum(stale) * 60.0 / span_s >= STALE_PER_MIN_AT_LEAST:
        met.append("starved")
    lost_hits = sum(1 for x in lost if x is not None and x >= CAPACITY_LOSS_AT_LEAST)
    capacity = (n == WINDOW_REPORTS and all(f is not None and f < CAPACITY_FPS_BELOW for f in fps)
                and lost_hits >= CAPACITY_LOSS_OF)
    mild = (sum(1 for f in fps if f is not None and f < CAPACITY_MILD_FPS_BELOW) >= CAPACITY_MILD_FPS_OF
            and lost_hits >= CAPACITY_LOSS_OF)
    if capacity or mild:
        met.append("capacity-limited")
    lv = [x for x in lost if x is not None]
    if lv and span_s and sum(lv) * 60.0 / span_s >= LOSS_PER_MIN_AT_LEAST:
        met.append("lossy")
    if not met:
        met.append("clean")
    return {"classes": met, "primary": min(met, key=PRIORITY.__getitem__)}


@dataclass
class SessionClassifier:
    """Feeds reports and events; produces per-window and per-session output."""
    reports: list[Report] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    def add_report(self, r: Report) -> bool:
        if self.reports and r.elapsed_ms is not None and r.elapsed_ms == self.reports[-1].elapsed_ms:
            return False                      # a repeated snapshot (e1_suite's dedupe)
        self.reports.append(r)
        return True

    def add_event(self, e: Event) -> None:
        self.events.append(e)

    def _t(self, r: Report) -> float | None:
        return r.elapsed_ms / 1000.0 if r.elapsed_ms is not None else None

    def windows(self) -> list[dict[str, Any]]:
        out = []
        for i in range(0, len(self.reports) - WINDOW_REPORTS + 1, WINDOW_REPORTS):
            chunk = self.reports[i:i + WINDOW_REPORTS]
            t0, t1 = self._t(chunk[0]), self._t(chunk[-1])
            lo = (t0 - REPORT_INTERVAL_S) if t0 is not None else None
            evs = [e for e in self.events if lo is not None and t1 is not None and lo < e.elapsed_s <= t1]
            c = classify_window(chunk, evs)
            lost = [x for x in (r.lost for r in chunk) if x is not None]
            out.append({
                "t_s": [t0, t1], "primary": c["primary"], "classes": c["classes"],
                "loss_per_min": round(sum(lost) * 60.0 / (len(chunk) * REPORT_INTERVAL_S), 1) if lost else None,
                "fps_min": min(_vals(chunk, "fps"), default=None),
                "queue_max": max(_vals(chunk, "queue"), default=None),
                "gap_max_ms": max(_vals(chunk, "gap_ms"), default=None),
                "events": [e.kind for e in evs],
            })
        return out

    def session(self, overlay: Mapping[str, Any] | None = None,
                heartbeat: Mapping[str, Any] | None = None) -> dict[str, Any]:
        wins = self.windows()
        counts = {name: sum(1 for w in wins if name in w["classes"]) for name in CLASSES}
        primaries = {name: sum(1 for w in wins if w["primary"] == name) for name in CLASSES}
        lost = _vals(self.reports, "lost")
        stale = _vals(self.reports, "stale")
        el = [r.elapsed_ms for r in self.reports if r.elapsed_ms is not None]
        span_min = (el[-1] - el[0]) / 60000.0 if len(el) > 1 else None   # e1_suite.telemetry_figures' span
        loss_pm = round(sum(lost) / span_min, 2) if lost and span_min else None
        stale_pm = round(sum(stale) / span_min, 2) if stale and span_min else None
        met = []
        if self.events:
            met.append("path-changed")
        if counts["latency-limited"]:
            met.append("latency-limited")
        if stale_pm is not None and stale_pm >= STALE_PER_MIN_AT_LEAST:
            met.append("starved")
        if counts["capacity-limited"]:
            met.append("capacity-limited")
        if loss_pm is not None and loss_pm >= LOSS_PER_MIN_AT_LEAST:
            met.append("lossy")
        if not met:
            met.append("clean")
        return {
            "schema": SCHEMA,
            "reports": len(self.reports),
            "windows": len(wins),
            "class": min(met, key=PRIORITY.__getitem__),
            "classes": met,
            "window_counts": counts,
            "window_primary_counts": primaries,
            "loss_per_min_post_fec": loss_pm,
            "stale_per_min": stale_pm,
            "measures": measures(self.reports, self.events, overlay, heartbeat,
                                 span_s=span_min * 60.0 if span_min else None),
        }


# ---- replay: recorded runs (the fixtures are redacted to counters) ---------------

def classifier_from_fixture(fx: Mapping[str, Any]) -> SessionClassifier:
    """A fixture: {"telemetry": [rows], "events": [{t_s, kind, detail}], "heartbeat": {...}}."""
    sc = SessionClassifier()
    for row in fx.get("telemetry", []):
        r = report_from_telemetry(row)
        if r is not None:
            sc.add_report(r)
    for e in fx.get("events", []):
        sc.add_event(Event(float(e["t_s"]), str(e["kind"]), str(e.get("detail", ""))))
    return sc


# ---- live (only with the flag) ------------------------------------------------------

class WanTelemetry:
    """Fed once per client health report; read by /status and the stream telemetry."""

    def __init__(self, project_root: Path, overlay_state: Callable[[], Mapping[str, Any]] | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self._log_path = Path(project_root) / "logs" / "wan_sessions.jsonl"
        self._overlay_state = overlay_state
        self._clock = clock
        self._lock = threading.Lock()
        self._session = SessionClassifier()
        self._last_kbps: Any = None
        self._last_path: Any = None
        self._last_recovery: Any = None
        self._last_report_at: float | None = None

    def _overlay(self) -> dict[str, Any]:
        if self._overlay_state is None:
            return {"path": "none", "mtu": None}
        try:
            return dict(self._overlay_state())
        except Exception:
            return {"path": "none", "mtu": None, "reason": "error"}

    def observe(self, telemetry: Mapping[str, Any], native_status: Mapping[str, Any] | None = None,
                recovery_state: str | None = None) -> None:
        r = report_from_telemetry(telemetry)
        if r is None:
            return
        ov = self._overlay()
        with self._lock:
            if self._session.reports and r.elapsed_ms is not None and \
                    self._session.reports[-1].elapsed_ms is not None and r.elapsed_ms < self._session.reports[-1].elapsed_ms:
                self._close_session_locked(ov)           # a new stream session began
            if not self._session.add_report(r):
                return
            self._last_report_at = self._clock()
            t = (r.elapsed_ms or 0) / 1000.0
            kbps = (native_status or {}).get("bitrate_kbps")
            if self._last_kbps is not None and kbps is not None and kbps != self._last_kbps:
                self._session.add_event(Event(t, "ladder_transition", f"{self._last_kbps}->{kbps}"))
            self._last_kbps = kbps if kbps is not None else self._last_kbps
            path = ov.get("path")
            if self._last_path is not None and path != self._last_path:
                self._session.add_event(Event(t, "overlay_path", f"{self._last_path}->{path}"))
            self._last_path = path
            if recovery_state is not None and recovery_state != self._last_recovery:
                if self._last_recovery is not None:
                    kind = "recovery_resume" if recovery_state == "PLAYING" else "recovery_pause"
                    self._session.add_event(Event(t, kind, recovery_state))
                self._last_recovery = recovery_state

    def _close_session_locked(self, ov: Mapping[str, Any]) -> None:
        if self._session.reports:
            doc = self._session.session(overlay=ov)
            doc["closed_unix_s"] = round(self._clock(), 3)
            try:
                self._log_path.parent.mkdir(parents=True, exist_ok=True)
                with self._log_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(doc, sort_keys=True) + "\n")
            except OSError:
                pass
        self._session = SessionClassifier()
        self._last_kbps = self._last_path = self._last_recovery = None

    FRESH_S = WINDOW_REPORTS * REPORT_INTERVAL_S

    def status_field(self) -> dict[str, Any] | None:
        """The `wan` object while a stream is reporting (a report within one window); else None."""
        with self._lock:
            if self._last_report_at is None or self._clock() - self._last_report_at > self.FRESH_S:
                return None
        ov = self._overlay()
        with self._lock:
            doc = self._session.session(overlay=ov)
            wins = self._session.windows()
        doc["last_window"] = wins[-1] if wins else None
        return doc


def from_environ(environ: Mapping[str, str], project_root: Path,
                 overlay_state: Callable[[], Mapping[str, Any]] | None = None) -> WanTelemetry | None:
    if (environ.get(FLAG_ENV) or "").strip() != "1":
        return None
    return WanTelemetry(project_root, overlay_state=overlay_state)
