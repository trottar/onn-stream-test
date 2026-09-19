#!/usr/bin/env python3
"""C3.L3a — gameplay acceptance probe. The C3.L4 gate, made performable.

Diagnostic-only. **This probe authorizes nothing and is not a controller.**
It follows a schedule generated up front from a seeded RNG; it never reads
telemetry and decides a target. A sequencer that observes conditions and
picks a bitrate *is* `C3.L4` and would have skipped its own gate.

It answers three separate questions and keeps them separate:

1. Are repeated, unannounced bitrate transitions perceptible during play, and
   does the *shape* of a transition change that? A **jump** (one cycle, full
   2000 kbps delta) against a **ramp** (three cycles, one rung each). Scored
   against **decoys** — moments where nothing fires — which give the operator's
   false-alarm rate. Without that baseline a mark rate means nothing.
2. Do the destination bitrates *look* acceptable? Announced park-and-judge at
   each rung, asked once, after the session.
3. What would a `C3.L4` controller need to know that nothing has measured?
   Per-transition cost at n>>1, cumulative lifecycle effect, and how long
   telemetry takes to settle after a transition — a controller that samples
   inside the settling window is reading noise.

The probe encodes **no acceptance threshold**. It records; the user judges.

Usage:

    python3 tools/probe_c3_l3a_gameplay_acceptance.py
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --finalize
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --aggregate
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --plan

Run, play, then finalize once the client has posted a decoder session.
Runs pool: several shorter sessions beat one long one, because attention
drifts and drift correlated with shape order would fake a result.

Privacy: loopback only. No network address is collected, formatted or
printed. No production file is modified.
"""

from __future__ import annotations

import argparse
import json
import random
import signal
import statistics
import sys
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from manual_checkout import (  # noqa: E402
    MarkCapture,
    Report,
    ask_int,
    yes,
)


CONTROL_BASE = "http://127.0.0.1:8765"
PROFILE_ID = "native_game_720p60_reference"

REFERENCE_KBPS = 7000
BOTTOM_KBPS = 5000
LADDER = (5000, 5500, 6000, 7000)

STREAM_ROOT = Path("logs/streaming")
RUNS_ROOT = STREAM_ROOT / "c3_l3a_runs"
STATE_PATH = STREAM_ROOT / "c3_l3a_gameplay_acceptance_state.json"
TEXT_LOG = STREAM_ROOT / "c3_l3a_gameplay_acceptance.txt"
JSON_LOG = STREAM_ROOT / "c3_l3a_gameplay_acceptance.json"
AGG_TEXT = STREAM_ROOT / "c3_l3a_aggregate.txt"
AGG_JSON = STREAM_ROOT / "c3_l3a_aggregate.json"
DECODER_ROOT = Path("logs/games/decoder_sessions")

# A mark always lags the event it refers to by the operator's reaction time,
# so the association window is asymmetric. Decoys are scored through the
# identical window, which is what keeps the comparison fair.
DEFAULT_WINDOW_S = 2.5


# --------------------------------------------------------------------------
# companion control
# --------------------------------------------------------------------------


def _request_json(
    path: str,
    *,
    method: str = "GET",
    timeout: float = 12.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        data=b"" if method == "POST" else None,
        method=method,
        headers={"Cache-Control": "no-cache"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""

        raise RuntimeError(
            f"companion request failed with HTTP {exc.code}: {detail[:300]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"companion is not reachable on the control port: {exc.reason}"
        ) from exc


def _status() -> dict[str, Any]:
    return _request_json("/plugins/games/native-stream-status")


def _telemetry() -> dict[str, Any]:
    return _request_json("/diagnostics/stream-telemetry", timeout=6.0)


def _transition(target_kbps: int) -> dict[str, Any]:
    return _request_json(
        "/plugins/games/c3-validated-bitrate-transition"
        f"?target={int(target_kbps)}",
        method="POST",
        timeout=20.0,
    )


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


# --------------------------------------------------------------------------
# schedule
# --------------------------------------------------------------------------


def build_schedule(
    *,
    traversals: int,
    dwell_min: float,
    dwell_max: float,
    ramp_gap: float,
    seed: int,
) -> list[dict[str, Any]]:
    """Pre-generate the whole session.

    The ladder alternates ends, so shape is the only free choice per
    traversal. Order is randomized inside the run: drift in the operator's
    attention over a long session must not correlate with shape.

    Every dwell carries exactly one decoy at a random offset inside it.
    Decoys cost no session time and give a 1:1 false-alarm baseline.
    """
    rng = random.Random(seed)

    shapes = ["jump", "ramp"] * ((traversals + 1) // 2)
    shapes = shapes[:traversals]
    rng.shuffle(shapes)

    schedule: list[dict[str, Any]] = []
    position = REFERENCE_KBPS

    for index, shape in enumerate(shapes):
        destination = BOTTOM_KBPS if position == REFERENCE_KBPS else REFERENCE_KBPS

        if shape == "jump":
            steps = [destination]
        else:
            rungs = [r for r in LADDER if min(position, destination) <= r <= max(position, destination)]
            rungs = [r for r in rungs if r != position]
            steps = sorted(rungs, reverse=position > destination)

        dwell = rng.uniform(dwell_min, dwell_max)
        # Fraction of the post-settling dwell, not an absolute offset:
        # telemetry settling consumes a variable slice of each dwell, and an
        # absolute offset would pin every decoy just after it, putting decoys
        # in a systematically different part of the timeline from sequences.
        decoy_fraction = rng.uniform(0.15, 0.85)

        schedule.append(
            {
                "index": index,
                "shape": shape,
                "from_kbps": position,
                "steps": steps,
                "ramp_gap_s": ramp_gap if shape == "ramp" else 0.0,
                "dwell_s": dwell,
                "decoy_fraction": decoy_fraction,
            }
        )

        position = destination

    return schedule


# --------------------------------------------------------------------------
# preflight
# --------------------------------------------------------------------------


def preflight() -> tuple[dict[str, Any], list[str]]:
    status = _status()
    problems: list[str] = []

    if not bool(status.get("active", False)):
        problems.append("native stream is not active")

    if not bool(status.get("ready", False)):
        problems.append("native stream is not ready")

    if str(status.get("profile_id", "")) != PROFILE_ID:
        problems.append("unexpected profile id")

    if int(status.get("reference_bitrate_kbps", 0) or 0) != REFERENCE_KBPS:
        problems.append("reference bitrate is not 7000")

    if int(status.get("bitrate_kbps", 0) or 0) != REFERENCE_KBPS:
        problems.append(
            "stream is not at the 7000 kbps reference; "
            "run one transition to 7000 before starting"
        )

    if not bool(_dict(status.get("fec")).get("running", False)):
        problems.append("FEC relay is not running")

    if not bool(_dict(status.get("audio")).get("active", False)):
        problems.append("process audio is not active")

    if not bool(_dict(status.get("controller")).get("active", False)):
        problems.append("controller transport is not active")

    return status, problems


def conditions_snapshot(status: dict[str, Any]) -> dict[str, Any]:
    """Transport conditions at session start.

    Recorded because they are not constant: 2026-09-19 ran 1,089-2,462 lost
    packets per session against 2-425 on 2026-09-18. Gap figures must not be
    compared across sessions without this.
    """
    fec = _dict(status.get("fec"))
    return {
        "fec_rtp_packets": fec.get("rtp_packets"),
        "fec_skipped_packets": fec.get("skipped_packets"),
        "fec_send_errors": fec.get("send_errors"),
        "audio_send_errors": _dict(status.get("audio")).get("send_errors"),
        "controller_lost_packets": _dict(status.get("controller")).get(
            "lost_packets"
        ),
        "controller_bad_packets": _dict(status.get("controller")).get(
            "bad_packets"
        ),
    }


# --------------------------------------------------------------------------
# telemetry settling
# --------------------------------------------------------------------------


def sample_settling(
    *,
    budget_s: float = 12.0,
    interval_s: float = 0.5,
) -> dict[str, Any]:
    """How long after a transition does telemetry become trustworthy?

    A `C3.L4` controller polls this surface to decide. If it samples inside
    the settling window it is reading the restart, not the network. Nothing
    has measured this window before.

    Settled = two consecutive fresh samples with `waiting_for_idr` false and
    `receiver_recent_fps` within 10% of 60.
    """
    started = time.monotonic()
    samples: list[dict[str, Any]] = []
    settled_at: float | None = None
    consecutive = 0

    while time.monotonic() - started < budget_s:
        elapsed = time.monotonic() - started

        try:
            payload = _telemetry()
        except RuntimeError:
            time.sleep(interval_s)
            continue

        measurements = _dict(payload.get("measurements"))
        receiver = _dict(payload.get("receiver"))
        fps = _num(measurements.get("receiver_recent_fps"))
        waiting = receiver.get("waiting_for_idr")
        fresh = bool(payload.get("fresh", False)) or bool(
            _dict(payload.get("checks")).get("fresh", False)
        )

        samples.append(
            {
                "at_s": round(elapsed, 3),
                "fresh": fresh,
                "fps": None if fps is None else round(fps, 2),
                "mbps": _num(measurements.get("receiver_recent_mbps")),
                "output_gap_ms": measurements.get("output_gap_ms"),
                "queue_depth": measurements.get("queue_depth"),
                "waiting_for_idr": waiting,
                "age_ms": measurements.get("age_ms"),
            }
        )

        good = (
            fresh
            and waiting is not True
            and fps is not None
            and abs(fps - 60.0) <= 6.0
        )

        consecutive = consecutive + 1 if good else 0

        if consecutive >= 2 and settled_at is None:
            settled_at = elapsed
            break

        time.sleep(interval_s)

    return {
        "settled_s": None if settled_at is None else round(settled_at, 3),
        "budget_s": budget_s,
        "samples": samples,
    }


# --------------------------------------------------------------------------
# restore
# --------------------------------------------------------------------------


def restore_reference(note: str) -> dict[str, Any]:
    """Put the stream back at 7000. Called on success, on error and on SIGINT.

    Nothing in the repository did this before: a session previously stayed
    parked wherever the last cycle left it.
    """
    result: dict[str, Any] = {"note": note, "ok": False, "detail": ""}

    try:
        status = _status()
    except RuntimeError as exc:
        result["detail"] = f"status unavailable: {exc}"
        return result

    current = int(status.get("bitrate_kbps", 0) or 0)

    if current == REFERENCE_KBPS:
        result["ok"] = True
        result["detail"] = "already at reference"
        return result

    try:
        payload = _transition(REFERENCE_KBPS)
    except RuntimeError as exc:
        result["detail"] = f"restore transition failed: {exc}"
        return result

    result["ok"] = bool(payload.get("ok", False))
    result["detail"] = f"{current} -> {REFERENCE_KBPS}"
    return result


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------


def run_session(args: argparse.Namespace) -> int:
    status, problems = preflight()

    if problems:
        print("PREFLIGHT FAILED")

        for problem in problems:
            print("  -", problem)

        return 2

    seed = args.seed if args.seed is not None else random.randrange(1, 2**31)
    schedule = build_schedule(
        traversals=args.traversals,
        dwell_min=args.dwell_min,
        dwell_max=args.dwell_max,
        ramp_gap=args.ramp_gap,
        seed=seed,
    )

    run_id = time.strftime("%Y%m%d_%H%M%S")
    decoder_before = sorted(p.name for p in DECODER_ROOT.glob("*.json"))

    total_cycles = sum(len(item["steps"]) for item in schedule)
    estimate_s = sum(
        item["dwell_s"] + len(item["steps"]) * (1.3 + item["ramp_gap_s"])
        for item in schedule
    )

    print("C3.L3a gameplay acceptance probe")
    print(f"  run id           : {run_id}")
    print(f"  traversals       : {args.traversals}")
    print(f"  transitions      : {total_cycles}")
    print(f"  ramp rung gap    : {args.ramp_gap:.1f}s")
    print(f"  phase A estimate : ~{estimate_s / 60.0:.1f} min")
    print("")
    print("  The schedule is NOT shown. That is the point.")
    print("  Play normally. Press Enter the moment you notice ANYTHING")
    print("  wrong with the video - a hitch, a blur, a freeze, a jump.")
    print("  Optionally type a digit 1-9 before Enter for severity.")
    print("  Do not try to guess when something is due.")
    print("")
    input("  Press Enter when you are playing and ready to start... ")

    capture = MarkCapture()
    events: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    aborted: str | None = None

    def _handle_sigint(_signum: int, _frame: Any) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _handle_sigint)

    capture.start()
    session_started = time.monotonic()

    def now_s() -> float:
        return time.monotonic() - session_started

    try:
        for item in schedule:
            sequence_start = now_s()
            step_records: list[dict[str, Any]] = []
            position = item["from_kbps"]

            for step_index, target in enumerate(item["steps"]):
                if step_index and item["ramp_gap_s"]:
                    time.sleep(item["ramp_gap_s"])

                fired_at = now_s()

                try:
                    payload = _transition(target)
                except RuntimeError as exc:
                    aborted = f"transition {position} -> {target} failed: {exc}"
                    raise

                if not bool(payload.get("ok", False)):
                    aborted = (
                        f"transition {position} -> {target} returned not-ok: "
                        + str(payload.get("error", ""))[:200]
                    )
                    raise RuntimeError(aborted)

                video = _dict(payload.get("video"))
                record = {
                    "sequence_index": item["index"],
                    "shape": item["shape"],
                    "step_index": step_index,
                    "fired_at_s": round(fired_at, 3),
                    "from_kbps": payload.get("from_bitrate_kbps"),
                    "to_kbps": payload.get("target_bitrate_kbps"),
                    "ffmpeg_spawn_ms": video.get("ffmpeg_spawn_ms"),
                    "first_rtp_resume_ms": video.get("first_rtp_resume_ms"),
                    "rtp_silence_after_spawn_ms": video.get(
                        "rtp_silence_after_spawn_ms"
                    ),
                    "host_verified_ms": video.get("host_verified_ms"),
                    "fec_send_errors_delta": _dict(payload.get("fec")).get(
                        "send_errors_delta"
                    ),
                    "audio_send_errors_delta": _dict(payload.get("audio")).get(
                        "send_errors_delta"
                    ),
                    "controller_bad_packets_delta": _dict(
                        payload.get("controller")
                    ).get("bad_packets_delta"),
                }
                step_records.append(record)
                transitions.append(record)
                position = target

            sequence_end = now_s()

            events.append(
                {
                    "kind": "sequence",
                    "shape": item["shape"],
                    "index": item["index"],
                    "at_s": round(sequence_start, 3),
                    "end_s": round(sequence_end, 3),
                    "cycles": len(item["steps"]),
                    "from_kbps": item["from_kbps"],
                    "to_kbps": item["steps"][-1],
                    "steps": step_records,
                }
            )

            settling = sample_settling()
            events[-1]["settling"] = settling

            # Dwell in two parts, with the decoy between them. Nothing
            # fires at the decoy; it is a logged moment used as the
            # operator's false-alarm baseline.
            settling_done = now_s()
            remaining = max(
                0.0,
                (sequence_end + item["dwell_s"]) - settling_done,
            )
            time.sleep(remaining * float(item["decoy_fraction"]))

            events.append(
                {
                    "kind": "decoy",
                    "index": item["index"],
                    "at_s": round(now_s(), 3),
                }
            )

            time.sleep(
                max(0.0, (sequence_end + item["dwell_s"]) - now_s())
            )

    except KeyboardInterrupt:
        aborted = aborted or "interrupted by operator"
    except Exception as exc:  # noqa: BLE001
        aborted = aborted or f"{type(exc).__name__}: {exc}"

    phase_a_end = now_s()
    capture.stop()

    restore = restore_reference("after phase A")

    print("")
    print(f"  Phase A complete. Marks recorded: {capture.count()}")

    if aborted:
        print(f"  ABORTED: {aborted}")

    # ---- phase B: announced park and judge ----
    park: list[dict[str, Any]] = []

    if not aborted and not args.no_park:
        print("")
        print("  Phase B: picture quality. Each level is announced.")
        print("  Keep playing; judge how the picture LOOKS, not timing.")

        for level in (6000, 5500, 5000):
            print("")
            print(f"  -> parking at {level} kbps for {args.park_seconds}s")

            try:
                payload = _transition(level)
            except RuntimeError as exc:
                park.append({"kbps": level, "error": str(exc)})
                continue

            if not bool(payload.get("ok", False)):
                park.append({"kbps": level, "error": str(payload)[:200]})
                continue

            time.sleep(args.park_seconds)
            park.append({"kbps": level, "parked_s": args.park_seconds})

        restore = restore_reference("after phase B")
        print("")
        print("  Back at 7000 kbps. Debrief:")
        print("")

        for entry in park:
            if "error" in entry:
                continue

            level = entry["kbps"]
            entry["acceptable"] = yes(
                f"  Did {level} kbps look acceptable to play on?"
            )
            entry["rating"] = ask_int(
                f"  Rate {level} kbps picture quality",
                low=1,
                high=5,
                default=None,
            )

    state = {
        "schema": "privyhub_c3_l3a_gameplay_acceptance_v1",
        "run_id": run_id,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "seed": seed,
        "config": {
            "traversals": args.traversals,
            "ramp_gap_s": args.ramp_gap,
            "dwell_min_s": args.dwell_min,
            "dwell_max_s": args.dwell_max,
            "park_seconds": args.park_seconds,
            "window_s": args.window,
        },
        "aborted": aborted,
        "phase_a_end_s": round(phase_a_end, 3),
        "conditions_before": conditions_snapshot(status),
        "conditions_after": conditions_snapshot(_status()),
        "events": events,
        "transitions": transitions,
        "marks": [m.as_dict() for m in capture.marks()],
        "park": park,
        "restore": restore,
        "decoder_sessions_before": decoder_before,
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("")
    print(f"  State written: {STATE_PATH}")
    print("")
    print("  Next: let the client post a decoder session, then run")
    print("    python3 tools/probe_c3_l3a_gameplay_acceptance.py --finalize")

    return 1 if aborted else 0


# --------------------------------------------------------------------------
# finalize
# --------------------------------------------------------------------------


def _attribute(
    events: list[dict[str, Any]],
    marks: list[dict[str, Any]],
    window_s: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach each mark to the most recent event whose window contains it.

    The window is [event, event + window_s] - asymmetric, because a mark
    always lags. Decoys use the identical window.
    """
    anchors = []

    for event in events:
        if event["kind"] == "sequence":
            anchors.append(
                {
                    "kind": "sequence",
                    "shape": event["shape"],
                    "index": event["index"],
                    "at_s": event["at_s"],
                    "marks": [],
                }
            )
        elif event["kind"] == "decoy":
            anchors.append(
                {
                    "kind": "decoy",
                    "shape": "decoy",
                    "index": event["index"],
                    "at_s": event["at_s"],
                    "marks": [],
                }
            )

    anchors.sort(key=lambda a: a["at_s"])
    unattributed: list[dict[str, Any]] = []

    for mark in marks:
        at = mark["elapsed_s"]
        chosen = None

        for anchor in anchors:
            if anchor["at_s"] <= at <= anchor["at_s"] + window_s:
                chosen = anchor

        if chosen is None:
            unattributed.append(mark)
        else:
            chosen["marks"].append(mark)

    return anchors, unattributed


def _newest_decoder_session(before: list[str]) -> Path | None:
    known = set(before)
    fresh = [
        path
        for path in DECODER_ROOT.glob("*.json")
        if path.name not in known
    ]

    if not fresh:
        return None

    return max(fresh, key=lambda p: p.stat().st_mtime)


def _stats(values: list[float]) -> dict[str, Any]:
    clean = [v for v in values if v is not None]

    if not clean:
        return {"n": 0}

    ordered = sorted(clean)
    return {
        "n": len(ordered),
        "min": round(ordered[0], 3),
        "median": round(statistics.median(ordered), 3),
        "max": round(ordered[-1], 3),
        "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3),
    }


def finalize(args: argparse.Namespace) -> int:
    if not STATE_PATH.is_file():
        print("No state file. Run a session first.")
        return 2

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    window = float(state.get("config", {}).get("window_s", DEFAULT_WINDOW_S))

    anchors, unattributed = _attribute(
        state["events"],
        state["marks"],
        window,
    )

    buckets: dict[str, dict[str, int]] = {
        "jump": {"total": 0, "marked": 0, "marks": 0},
        "ramp": {"total": 0, "marked": 0, "marks": 0},
        "decoy": {"total": 0, "marked": 0, "marks": 0},
    }

    for anchor in anchors:
        bucket = buckets[anchor["shape"]]
        bucket["total"] += 1
        bucket["marks"] += len(anchor["marks"])

        if anchor["marks"]:
            bucket["marked"] += 1

    by_shape: dict[str, dict[str, Any]] = {}

    for shape in ("jump", "ramp"):
        rows = [
            t for t in state["transitions"] if t["shape"] == shape
        ]
        by_shape[shape] = {
            "cycles": len(rows),
            "spawn_ms": _stats([_num(r["ffmpeg_spawn_ms"]) for r in rows]),
            "first_rtp_resume_ms": _stats(
                [_num(r["first_rtp_resume_ms"]) for r in rows]
            ),
            "host_verified_ms": _stats(
                [_num(r["host_verified_ms"]) for r in rows]
            ),
        }

    settle_values = [
        _num(e.get("settling", {}).get("settled_s"))
        for e in state["events"]
        if e["kind"] == "sequence"
    ]
    never_settled = sum(
        1
        for e in state["events"]
        if e["kind"] == "sequence"
        and e.get("settling", {}).get("settled_s") is None
    )

    lifecycle = {
        "fec_send_errors_delta": sum(
            int(t.get("fec_send_errors_delta") or 0)
            for t in state["transitions"]
        ),
        "audio_send_errors_delta": sum(
            int(t.get("audio_send_errors_delta") or 0)
            for t in state["transitions"]
        ),
        "controller_bad_packets_delta": sum(
            int(t.get("controller_bad_packets_delta") or 0)
            for t in state["transitions"]
        ),
    }

    decoder_path = _newest_decoder_session(
        state.get("decoder_sessions_before", [])
    )
    decoder: dict[str, Any] = {"path": None}

    if decoder_path is not None:
        payload = json.loads(decoder_path.read_text(encoding="utf-8"))
        report = _dict(payload.get("report"))
        video = _dict(report.get("video"))
        dec = _dict(report.get("decoder"))
        discontinuities = report.get("stream_discontinuities") or []
        first_idr = report.get("first_idr_after_discontinuity") or []
        decoder = {
            "path": str(decoder_path),
            "duration_ms": report.get("duration_ms"),
            "ssrc_changes": video.get("ssrc_changes"),
            "sequence_resyncs": video.get("sequence_resyncs"),
            "lost_packets": video.get("lost_packets"),
            "fec_unrecoverable_groups": video.get("fec_unrecoverable_groups"),
            "max_output_gap_ms": dec.get("max_output_gap_ms"),
            "max_codec_ms": dec.get("max_codec_ms"),
            "rendered_frames": dec.get("rendered_frames"),
            "dropped_frames": dec.get("dropped_frames"),
            "discontinuity_count": len(discontinuities),
            "ssrc_discontinuity_count": sum(
                1
                for d in discontinuities
                if str(_dict(d).get("type")) == "ssrc_change"
            ),
            "resync_to_idr_ms": [
                _dict(entry).get("resync_to_idr_ms") for entry in first_idr
            ],
            "expected_ssrc_changes": len(state["transitions"]),
        }

    analysis = {
        "schema": "privyhub_c3_l3a_analysis_v1",
        "run_id": state["run_id"],
        "seed": state["seed"],
        "config": state["config"],
        "aborted": state.get("aborted"),
        "conditions_before": state.get("conditions_before"),
        "conditions_after": state.get("conditions_after"),
        "buckets": buckets,
        "unattributed_marks": len(unattributed),
        "total_marks": len(state["marks"]),
        "by_shape": by_shape,
        "settling_s": _stats([v for v in settle_values if v is not None]),
        "never_settled": never_settled,
        "lifecycle_totals": lifecycle,
        "park": state.get("park", []),
        "decoder": decoder,
        "anchors": anchors,
    }

    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    (RUNS_ROOT / f"{state['run_id']}.json").write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    JSON_LOG.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    _write_report(analysis, TEXT_LOG, single_run=True)
    return 0


def _rate(bucket: dict[str, int]) -> str:
    if not bucket["total"]:
        return "n/a"

    return f"{bucket['marked']}/{bucket['total']} ({100.0 * bucket['marked'] / bucket['total']:.0f}%)"


def _write_report(
    analysis: dict[str, Any],
    path: Path,
    *,
    single_run: bool,
) -> None:
    buckets = analysis["buckets"]
    report = Report(
        "PrivyHub C3.L3a gameplay acceptance probe"
        + ("" if single_run else " - pooled")
    )

    report.section("RUN")
    report.field("Run id", analysis.get("run_id", "<pooled>"))
    report.field("Seed", analysis.get("seed", "<pooled>"))
    report.field("Aborted", analysis.get("aborted") or "no")
    report.field("Window (s)", analysis["config"].get("window_s"))
    report.field("Ramp rung gap (s)", analysis["config"].get("ramp_gap_s"))

    report.section("DETECTION - the gate question")
    report.line("Binary per sequence: was this event marked at all.")
    report.line("Decoys fire nothing; their rate is the false-alarm baseline.")
    report.line("")
    report.table(
        ["shape", "events", "marked", "rate", "total marks"],
        [
            [
                shape,
                buckets[shape]["total"],
                buckets[shape]["marked"],
                _rate(buckets[shape]),
                buckets[shape]["marks"],
            ]
            for shape in ("jump", "ramp", "decoy")
        ],
        align_right={1, 2, 4},
    )
    report.line("")
    report.field("Marks attributed to nothing", analysis["unattributed_marks"])
    report.field("Marks total", analysis["total_marks"])
    report.line("")
    report.line("NO THRESHOLD IS ENCODED. Read the table; the judgement is yours.")

    report.section("PICTURE QUALITY - announced, separate question")

    if analysis.get("park"):
        report.table(
            ["kbps", "acceptable", "rating 1-5"],
            [
                [
                    entry.get("kbps"),
                    entry.get("acceptable", "<not asked>"),
                    entry.get("rating", "<none>"),
                ]
                for entry in analysis["park"]
            ],
            align_right={0, 2},
        )
    else:
        report.line("Phase B not run.")

    report.section("C3.L4 READINESS")
    report.line("What an automatic controller would need, and whether it is known.")
    report.line("")

    for shape in ("jump", "ramp"):
        data = analysis["by_shape"].get(shape, {})
        report.field(
            f"{shape} cycles measured",
            data.get("cycles", 0),
        )
        report.field(
            f"  {shape} spawn_ms",
            data.get("spawn_ms"),
        )
        report.field(
            f"  {shape} first_rtp_resume_ms",
            data.get("first_rtp_resume_ms"),
        )
        report.field(
            f"  {shape} host_verified_ms",
            data.get("host_verified_ms"),
        )

    report.line("")
    report.field("Telemetry settling after a sequence (s)", analysis["settling_s"])
    report.field("Sequences that never settled in budget", analysis["never_settled"])
    report.line(
        "  -> a controller MUST NOT sample telemetry inside the settling window;"
    )
    report.line("     inside it, it is measuring the restart, not the network.")
    report.line("")
    report.field("Cumulative lifecycle over the whole session", analysis["lifecycle_totals"])
    report.line("  -> all three must be 0. Non-zero means repeated transitions")
    report.line("     degrade a subsystem that a single transition does not.")
    report.line("")
    report.field("Minimum rung spacing exercised (s)", analysis["config"].get("ramp_gap_s"))
    report.field("Transitions in one session", sum(
        analysis["by_shape"].get(s, {}).get("cycles", 0) for s in ("jump", "ramp")
    ))

    report.section("CLIENT DECODER SESSION")
    decoder = analysis.get("decoder") or {}

    if decoder.get("path"):
        for key in (
            "path",
            "duration_ms",
            "ssrc_changes",
            "expected_ssrc_changes",
            "ssrc_discontinuity_count",
            "sequence_resyncs",
            "lost_packets",
            "fec_unrecoverable_groups",
            "max_output_gap_ms",
            "max_codec_ms",
            "rendered_frames",
            "dropped_frames",
        ):
            report.field(key, decoder.get(key))

        report.field("resync_to_idr_ms per discontinuity", decoder.get("resync_to_idr_ms"))

        expected = decoder.get("expected_ssrc_changes")
        actual = decoder.get("ssrc_changes")

        if expected is not None and actual is not None and expected != actual:
            report.line("")
            report.line(
                f"  WARNING: {expected} transitions fired but the client saw "
                f"{actual} SSRC changes."
            )
            report.line(
                "  The decoder session may not cover the whole probe run."
            )
    else:
        report.line("No new decoder session found.")
        report.line("Run --finalize again once the client has posted one.")

    report.section("CONDITIONS")
    report.field("before", analysis.get("conditions_before"))
    report.field("after", analysis.get("conditions_after"))
    report.line("")
    report.line("Transport conditions are not constant between sessions.")
    report.line("Do not compare gap figures across runs without comparing these.")

    report.section("WHAT THIS DOES NOT ESTABLISH")
    report.line("- Whether C3.L4 is authorized. That is a human judgement on")
    report.line("  the detection table and the picture ratings above.")
    report.line("- Any controller policy: thresholds, hysteresis, sample cadence.")
    report.line("- Behaviour under real network pressure. Every transition here")
    report.line("  fired from a schedule, not from a degraded condition.")

    classification = (
        "C3_L3A_GAMEPLAY_ACCEPTANCE_ABORTED"
        if analysis.get("aborted")
        else "C3_L3A_GAMEPLAY_ACCEPTANCE_RECORDED"
    )
    report.write(path, classification)


def aggregate(_args: argparse.Namespace) -> int:
    runs = sorted(RUNS_ROOT.glob("*.json"))

    if not runs:
        print("No runs to pool. Finalize at least one session first.")
        return 2

    pooled = {
        "jump": {"total": 0, "marked": 0, "marks": 0},
        "ramp": {"total": 0, "marked": 0, "marks": 0},
        "decoy": {"total": 0, "marked": 0, "marks": 0},
    }
    park: list[dict[str, Any]] = []
    settle: list[float] = []
    lifecycle = {
        "fec_send_errors_delta": 0,
        "audio_send_errors_delta": 0,
        "controller_bad_packets_delta": 0,
    }
    cycles = {"jump": 0, "ramp": 0}
    unattributed = 0
    total_marks = 0
    run_ids: list[str] = []

    for path in runs:
        data = json.loads(path.read_text(encoding="utf-8"))
        run_ids.append(str(data.get("run_id")))

        for shape in pooled:
            for key in ("total", "marked", "marks"):
                pooled[shape][key] += int(
                    data.get("buckets", {}).get(shape, {}).get(key, 0)
                )

        park.extend(data.get("park", []))
        unattributed += int(data.get("unattributed_marks", 0))
        total_marks += int(data.get("total_marks", 0))

        for key in lifecycle:
            lifecycle[key] += int(
                data.get("lifecycle_totals", {}).get(key, 0)
            )

        for shape in cycles:
            cycles[shape] += int(
                data.get("by_shape", {}).get(shape, {}).get("cycles", 0)
            )

        median = data.get("settling_s", {}).get("median")

        if median is not None:
            settle.append(float(median))

    analysis = {
        "schema": "privyhub_c3_l3a_aggregate_v1",
        "run_ids": run_ids,
        "run_count": len(run_ids),
        "config": {"window_s": "per-run", "ramp_gap_s": "per-run"},
        "aborted": None,
        "buckets": pooled,
        "unattributed_marks": unattributed,
        "total_marks": total_marks,
        "by_shape": {
            shape: {"cycles": cycles[shape]} for shape in cycles
        },
        "settling_s": _stats(settle),
        "never_settled": 0,
        "lifecycle_totals": lifecycle,
        "park": park,
        "decoder": {},
        "conditions_before": "per-run",
        "conditions_after": "per-run",
    }

    AGG_JSON.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(analysis, AGG_TEXT, single_run=False)
    return 0


def show_plan(args: argparse.Namespace) -> int:
    seed = args.seed if args.seed is not None else 1
    schedule = build_schedule(
        traversals=args.traversals,
        dwell_min=args.dwell_min,
        dwell_max=args.dwell_max,
        ramp_gap=args.ramp_gap,
        seed=seed,
    )
    cycles = sum(len(item["steps"]) for item in schedule)
    estimate = sum(
        item["dwell_s"] + len(item["steps"]) * (1.3 + item["ramp_gap_s"])
        for item in schedule
    )

    print("C3.L3a plan (shape counts only - a real run does not print this)")
    print(f"  traversals   : {args.traversals}")
    print(f"  jumps        : {sum(1 for i in schedule if i['shape'] == 'jump')}")
    print(f"  ramps        : {sum(1 for i in schedule if i['shape'] == 'ramp')}")
    print(f"  transitions  : {cycles}")
    print(f"  decoys       : {len(schedule)}")
    print(f"  phase A est. : ~{estimate / 60.0:.1f} min")
    print(f"  phase B est. : ~{3 * args.park_seconds / 60.0:.1f} min")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--traversals", type=int, default=8)
    parser.add_argument("--ramp-gap", type=float, default=4.0, dest="ramp_gap")
    parser.add_argument("--dwell-min", type=float, default=30.0, dest="dwell_min")
    parser.add_argument("--dwell-max", type=float, default=75.0, dest="dwell_max")
    parser.add_argument("--park-seconds", type=int, default=45, dest="park_seconds")
    parser.add_argument("--window", type=float, default=DEFAULT_WINDOW_S)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-park", action="store_true", dest="no_park")
    args = parser.parse_args()

    if args.dwell_min > args.dwell_max:
        print("--dwell-min must not exceed --dwell-max")
        return 2

    if args.plan:
        return show_plan(args)

    if args.aggregate:
        return aggregate(args)

    if args.finalize:
        return finalize(args)

    try:
        return run_session(args)
    finally:
        # Only a real session can leave the stream off-reference.
        try:
            restore_reference("final safety restore")
        except Exception as exc:  # noqa: BLE001
            print(f"  WARNING: final restore failed: {exc}")
            print("  Check the stream bitrate before the next run.")


if __name__ == "__main__":
    raise SystemExit(main())
