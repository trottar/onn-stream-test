#!/usr/bin/env python3
"""C3.L3a — gameplay acceptance probe. The C3.L4 gate, made performable.

Diagnostic-only. **This probe authorizes nothing and is not a controller.**
It follows a schedule generated up front from a seeded RNG; it never reads
telemetry and decides a target. A sequencer that observes conditions and
picks a bitrate *is* `C3.L4` and would have skipped its own gate. Telemetry
is read only to *record* how long it takes to settle; nothing it returns
changes what fires or when.

It answers three separate questions and keeps them separate:

1. Are repeated, unannounced bitrate transitions perceptible during play, and
   does the *shape* of a transition change that? A **jump** (one cycle, full
   2000 kbps delta) against a **ramp** (three cycles, one rung each). Scored
   against **decoys** — moments where nothing fires — which give the operator's
   false-alarm rate. Without that baseline a mark rate means nothing.
2. Do the destination bitrates *look* acceptable? Announced park-and-judge at
   each rung, asked once, after the session, on an anchored 1-10 scale.
3. What would a `C3.L4` controller need to know that nothing has measured?
   Per-transition cost at n>>1, cumulative lifecycle effect, and how long
   telemetry takes to settle after a transition — a controller that samples
   inside the settling window is reading noise.

The probe encodes **no acceptance threshold**. It records; the user judges.

Scoring (C3-L3A-P2R1, 2026-09-23). A sequence's window runs from its first
fire to `end + W`, where `end` is when the last transition call returned.
Decoys are scored through two windows, reported separately: jump-matched
`[decoy, decoy + W]` and ramp-matched `[decoy, decoy + ramp_span + W]`,
`ramp_span` being the run's median ramp `end - at`. Every class reports its
exposure seconds beside the session's chance rate (marks / phase-A seconds).
W is reported at 2.5, 5.0 and 8.0 s side by side, whatever the primary.
Marks are then put on the decoder's clock (Phase-A fires matched in order to
the first `ssrc_change` discontinuities) and checked against
`stream_discontinuities` — the gate's requirement 4.

Usage:

    python3 tools/probe_c3_l3a_gameplay_acceptance.py --plan
    python3 tools/probe_c3_l3a_gameplay_acceptance.py
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --finalize
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --finalize \\
        --state <state.json> --decoder <native_decoder_*.json>
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --aggregate

Run, play, then finalize once the client has posted a decoder session.
`--finalize` never writes the state file; re-scoring a retained run is safe.
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

from datetime import datetime
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
PARK_LEVELS = (6000, 5500, 5000)

STREAM_ROOT = Path("logs/streaming")
RUNS_ROOT = STREAM_ROOT / "c3_l3a_runs"
STATE_PATH = STREAM_ROOT / "c3_l3a_gameplay_acceptance_state.json"
TEXT_LOG = STREAM_ROOT / "c3_l3a_gameplay_acceptance.txt"
JSON_LOG = STREAM_ROOT / "c3_l3a_gameplay_acceptance.json"
AGG_TEXT = STREAM_ROOT / "c3_l3a_aggregate.txt"
AGG_JSON = STREAM_ROOT / "c3_l3a_aggregate.json"
DECODER_ROOT = Path("logs/games/decoder_sessions")

STATE_SCHEMA = "privyhub_c3_l3a_gameplay_acceptance_v2"
ANALYSIS_SCHEMA = "privyhub_c3_l3a_analysis_v2"

# A mark always lags the event it refers to by the operator's reaction time,
# so every window is asymmetric. Primary W = 5.0 s from 2026-09-23: the
# 2026-09-20 marks lagged their fires by 2.9-4.3 s, past the 2.5 s that was
# pre-registered for that run (and stays primary for re-scoring it, because
# its state file records it). All three are always reported.
DEFAULT_WINDOW_S = 5.0
REPORT_WINDOWS_S = (2.5, 5.0, 8.0)

# Telemetry settling. The client posts a report every `sample_interval_ms`
# (2000 ms on 2026-09-23); the endpoint re-serves the latest one until the
# next arrives, so "two samples" means two distinct `session_elapsed_ms`.
SETTLE_BUDGET_S = 12.0
SETTLE_POLL_S = 0.5
SETTLE_POLL_TIMEOUT_S = 2.0
SETTLE_MIN_FPS = 54.0
SETTLE_MIN_INTERVALS = 3

# Schedule planning. One transition call returned in 0.98-1.43 s on
# 2026-09-20; 1.3 s is the planning figure, not a measurement.
TRANSITION_EST_S = 1.3
DECOY_GUARD_S = 3.0

# Clock alignment: fire-to-SSRC-change offsets whose spread exceeds this mean
# the fires were paired with the wrong discontinuities.
ALIGN_MAX_SPREAD_S = 1.0
SLOW_EVENT_WINDOW_S = 1.0

RATING_SCALE: dict[str, Any] = {
    "low": 1,
    "high": 10,
    "anchors": {
        "10": "looks the same as 7000",
        "5": "clearly softer, still playable",
        "1": "unplayable",
    },
}

# Runs recorded before the scale was stored. The 2026-09-20 prompt showed a
# bare "[1-5]"; the user answered out of 10 and said so (memory 2026-09-20).
# The answers are kept as stated, never rescaled.
LEGACY_RATING_SCALES: dict[str, dict[str, Any]] = {
    "20260920_010023": {
        "low": 1,
        "high": 10,
        "anchors": None,
        "note": "1-10 (prompt showed 1-5; user's stated scale)",
    },
}

LAG_BINS_S = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 15.0, 30.0, 60.0)

# The rerun's design, pre-registered 2026-09-23 (evidence
# C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md). `--aggregate` pools a
# run only if its state is v2 and its config matches every field here; a
# smoke run or a re-scored older session is listed as SKIPPED with the
# field that differs. The CLI defaults are these values.
PREREGISTERED_CONFIG: dict[str, float] = {
    "traversals": 10,
    "dwell_min_s": 55.0,
    "dwell_max_s": 90.0,
    "window_s": 5.0,
    "ramp_gap_s": 4.0,
    "park_seconds": 45,
}


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
    except (urllib.error.URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(
            f"companion is not reachable on the control port: {reason}"
        ) from exc


def _status() -> dict[str, Any]:
    return _request_json("/plugins/games/native-stream-status")


def _telemetry(timeout: float = 6.0) -> dict[str, Any]:
    return _request_json("/diagnostics/stream-telemetry", timeout=timeout)


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


def _r(value: float | None, places: int = 3) -> float | None:
    return None if value is None else round(float(value), places)


# --------------------------------------------------------------------------
# schedule
# --------------------------------------------------------------------------


def ramp_span_plan(ramp_gap: float) -> float:
    """Planned first-fire-to-last-return span of a three-rung ramp."""
    return 2.0 * ramp_gap + 3.0 * TRANSITION_EST_S


def decoy_constraint(window_s: float, ramp_gap: float) -> dict[str, float]:
    """The placement rule every dwell must satisfy.

    The decoy comes after settling (which can overrun its budget by at most
    one poll timeout), and its ramp-matched window — at the widest window
    that will be reported — must end `DECOY_GUARD_S` before the next
    sequence fires. The previous sequence's window (`end + W`) is inside
    settling, because the settling budget exceeds every reported W.
    """
    guard_window = max((float(window_s),) + REPORT_WINDOWS_S)
    earliest = SETTLE_BUDGET_S + SETTLE_POLL_TIMEOUT_S
    span = ramp_span_plan(ramp_gap)
    return {
        "earliest_offset_s": earliest,
        "ramp_span_plan_s": span,
        "window_for_placement_s": guard_window,
        "guard_s": DECOY_GUARD_S,
        "min_dwell_s": earliest + span + guard_window + DECOY_GUARD_S,
    }


def build_schedule(
    *,
    traversals: int,
    dwell_min: float,
    dwell_max: float,
    ramp_gap: float,
    window_s: float,
    seed: int,
) -> list[dict[str, Any]]:
    """Pre-generate the whole session.

    The ladder alternates ends, so shape is the only free choice per
    traversal. Order is randomized inside the run: drift in the operator's
    attention over a long session must not correlate with shape.

    Every dwell carries exactly one decoy. Its offset from the sequence end
    is fixed here, between the end of settling and the latest point at which
    its ramp-matched window still ends `DECOY_GUARD_S` before the next fire
    (`decoy_constraint`). A dwell too short for that is refused, not
    squeezed: overlapping decoy and sequence windows score one mark twice.
    """
    rule = decoy_constraint(window_s, ramp_gap)

    if dwell_min < rule["min_dwell_s"]:
        raise ValueError(
            f"--dwell-min {dwell_min:.1f}s cannot hold settling + a "
            f"ramp-matched decoy window + the guard before the next fire; "
            f"it needs >= {rule['min_dwell_s']:.1f}s at W "
            f"{rule['window_for_placement_s']:.1f}s"
        )

    rng = random.Random(seed)

    shapes = ["jump", "ramp"] * ((traversals + 1) // 2)
    shapes = shapes[:traversals]
    rng.shuffle(shapes)

    schedule: list[dict[str, Any]] = []
    position = REFERENCE_KBPS
    tail = (
        rule["ramp_span_plan_s"]
        + rule["window_for_placement_s"]
        + rule["guard_s"]
    )

    for index, shape in enumerate(shapes):
        destination = BOTTOM_KBPS if position == REFERENCE_KBPS else REFERENCE_KBPS

        if shape == "jump":
            steps = [destination]
        else:
            rungs = [r for r in LADDER if min(position, destination) <= r <= max(position, destination)]
            rungs = [r for r in rungs if r != position]
            steps = sorted(rungs, reverse=position > destination)

        dwell = rng.uniform(dwell_min, dwell_max)
        # A fraction of the placeable span, not an absolute offset, so decoys
        # spread across the dwell rather than bunching after settling.
        decoy_fraction = rng.uniform(0.15, 0.85)
        earliest = rule["earliest_offset_s"]
        latest = dwell - tail
        decoy_offset = earliest + decoy_fraction * (latest - earliest)
        window_end = decoy_offset + rule["ramp_span_plan_s"] + rule["window_for_placement_s"]
        slack = dwell - window_end

        if slack < rule["guard_s"] - 1e-9 or decoy_offset < earliest - 1e-9:
            raise ValueError(f"decoy placement failed on dwell {index}")

        schedule.append(
            {
                "index": index,
                "shape": shape,
                "from_kbps": position,
                "steps": steps,
                "ramp_gap_s": ramp_gap if shape == "ramp" else 0.0,
                "dwell_s": dwell,
                "decoy_fraction": decoy_fraction,
                "decoy_offset_s": decoy_offset,
                "decoy_window_end_s": window_end,
                "decoy_slack_s": slack,
            }
        )

        position = destination

    return schedule


# --------------------------------------------------------------------------
# preflight
# --------------------------------------------------------------------------


def preflight() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
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

    # Settling is part of what the run records. If it cannot be measured the
    # run would repeat the 2026-09-20 defect, so it does not start.
    telemetry: dict[str, Any] = {}

    try:
        payload = _telemetry()
    except RuntimeError:
        problems.append("stream telemetry endpoint unreachable")
    else:
        interval = _num(payload.get("sample_interval_ms"))
        telemetry = {
            "available": payload.get("available"),
            "fresh": payload.get("fresh"),
            "age_ms": payload.get("age_ms"),
            "sample_interval_ms": interval,
            "session_elapsed_ms": payload.get("session_elapsed_ms"),
        }

        if payload.get("fresh") is not True:
            problems.append("stream telemetry is not fresh")

        if interval is None:
            problems.append("telemetry carries no sample_interval_ms")
        elif SETTLE_BUDGET_S * 1000.0 < SETTLE_MIN_INTERVALS * interval:
            problems.append(
                f"settling budget {SETTLE_BUDGET_S:.0f}s is under "
                f"{SETTLE_MIN_INTERVALS} client intervals ({interval:.0f} ms)"
            )

    return status, telemetry, problems


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
    budget_s: float = SETTLE_BUDGET_S,
    interval_s: float = SETTLE_POLL_S,
) -> dict[str, Any]:
    """How long after a transition does telemetry become trustworthy?

    A `C3.L4` controller polls this surface to decide. If it samples inside
    the settling window it is reading the restart, not the network.

    The endpoint (`companion/diagnostics/stream_telemetry.py`) serves the
    latest client report: top-level `fresh`, `age_ms`, `session_elapsed_ms`,
    `sample_interval_ms`; `receiver.recent_fps`, `receiver.recent_mbps`,
    `receiver.waiting_for_idr`; `latency.output_gap_ms`;
    `decoder.queue_depth`. Polling faster than the client posts re-reads the
    same report, so only a snapshot whose `session_elapsed_ms` advanced
    counts, and the first snapshot read never counts (it may predate the
    transition).

    Settled = two consecutive distinct snapshots, both `fresh`,
    `waiting_for_idr` not true, `recent_fps` >= 54.
    """
    started = time.monotonic()
    samples: list[dict[str, Any]] = []
    settled_at: float | None = None
    consecutive = 0
    distinct = 0
    errors = 0
    interval_ms: float | None = None
    baseline: float | None = None
    last: float | None = None
    seen: list[float] = []

    while True:
        elapsed = time.monotonic() - started
        remaining = budget_s - elapsed

        if remaining <= 0:
            break

        try:
            payload = _telemetry(
                timeout=max(0.2, min(SETTLE_POLL_TIMEOUT_S, remaining))
            )
        except RuntimeError:
            errors += 1
            time.sleep(interval_s)
            continue

        read_at = time.monotonic() - started
        receiver = _dict(payload.get("receiver"))
        latency = _dict(payload.get("latency"))
        decoder = _dict(payload.get("decoder"))
        snapshot = _num(payload.get("session_elapsed_ms"))
        fps = _num(receiver.get("recent_fps"))
        waiting = receiver.get("waiting_for_idr")
        fresh = payload.get("fresh") is True

        if interval_ms is None:
            interval_ms = _num(payload.get("sample_interval_ms"))

        new = False

        if snapshot is not None:
            if baseline is None:
                baseline = snapshot
                seen.append(snapshot)
            elif last is not None and snapshot > last:
                new = True
                seen.append(snapshot)

            last = snapshot if last is None else max(last, snapshot)

        good = (
            fresh
            and waiting is not True
            and fps is not None
            and fps >= SETTLE_MIN_FPS
        )

        samples.append(
            {
                "at_s": round(read_at, 3),
                "session_elapsed_ms": snapshot,
                "new_snapshot": new,
                "fresh": fresh,
                "age_ms": payload.get("age_ms"),
                "fps": _r(fps, 2),
                "mbps": _r(_num(receiver.get("recent_mbps")), 3),
                "waiting_for_idr": waiting,
                "output_gap_ms": latency.get("output_gap_ms"),
                "queue_depth": decoder.get("queue_depth"),
                "good": good,
            }
        )

        if new:
            distinct += 1
            consecutive = consecutive + 1 if good else 0

            if consecutive >= 2:
                settled_at = read_at
                break

        time.sleep(interval_s)

    cadence = [b - a for a, b in zip(seen, seen[1:])]

    return {
        "settled_s": _r(settled_at),
        "budget_s": budget_s,
        "poll_s": interval_s,
        "rule": (
            "two consecutive distinct snapshots (session_elapsed_ms "
            "advanced), both fresh, waiting_for_idr not true, "
            f"recent_fps >= {SETTLE_MIN_FPS:g}"
        ),
        "sample_interval_ms": interval_ms,
        "budget_intervals": (
            None
            if not interval_ms
            else round(budget_s * 1000.0 / interval_ms, 2)
        ),
        "budget_ok": (
            None
            if not interval_ms
            else budget_s * 1000.0 >= SETTLE_MIN_INTERVALS * interval_ms
        ),
        "snapshot_cadence_ms": (
            None if not cadence else round(statistics.median(cadence), 1)
        ),
        "baseline_session_elapsed_ms": baseline,
        "distinct_snapshots": distinct,
        "request_errors": errors,
        "samples": samples,
    }


# --------------------------------------------------------------------------
# restore
# --------------------------------------------------------------------------


def restore_reference(note: str) -> dict[str, Any]:
    """Put the stream back at 7000. Called on success, on error and on SIGINT.

    `transitioned` is true when a transition was fired — each one is an SSRC
    change the decoder session must account for.
    """
    result: dict[str, Any] = {
        "note": note,
        "ok": False,
        "transitioned": False,
        "detail": "",
    }

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
    result["transitioned"] = result["ok"]
    result["detail"] = f"{current} -> {REFERENCE_KBPS}"
    return result


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------


def _rating_anchors() -> dict[int, str]:
    return {int(k): v for k, v in RATING_SCALE["anchors"].items()}


def run_session(args: argparse.Namespace) -> int:
    status, telemetry, problems = preflight()

    if problems:
        print("PREFLIGHT FAILED")

        for problem in problems:
            print("  -", problem)

        return 2

    seed = args.seed if args.seed is not None else random.randrange(1, 2**31)

    try:
        schedule = build_schedule(
            traversals=args.traversals,
            dwell_min=args.dwell_min,
            dwell_max=args.dwell_max,
            ramp_gap=args.ramp_gap,
            window_s=args.window,
            seed=seed,
        )
    except ValueError as exc:
        print(f"SCHEDULE REFUSED: {exc}")
        return 2

    run_id = time.strftime("%Y%m%d_%H%M%S")
    decoder_before = sorted(p.name for p in DECODER_ROOT.glob("*.json"))

    total_cycles = sum(len(item["steps"]) for item in schedule)
    estimate_s = sum(
        item["dwell_s"] + len(item["steps"]) * (TRANSITION_EST_S + item["ramp_gap_s"])
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
    restores: list[dict[str, Any]] = []
    aborted: str | None = None

    def _handle_sigint(_signum: int, _frame: Any) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _handle_sigint)

    capture.start()
    session_started = time.monotonic()

    def now_s() -> float:
        return time.monotonic() - session_started

    def restore(note: str) -> dict[str, Any]:
        at = now_s()
        result = restore_reference(note)
        result["at_s"] = round(at, 3)
        restores.append(result)
        return result

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
                    "returned_at_s": round(now_s(), 3),
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

            # The decoy's offset was fixed by the schedule. Settling can
            # overrun by at most one poll timeout, which the schedule's
            # earliest offset already allows for; lateness is recorded
            # rather than hidden. Nothing fires at a decoy.
            decoy_due = sequence_end + item["decoy_offset_s"]
            late = now_s() - decoy_due

            if late < 0:
                time.sleep(-late)

            events.append(
                {
                    "kind": "decoy",
                    "index": item["index"],
                    "at_s": round(now_s(), 3),
                    "planned_at_s": round(decoy_due, 3),
                    "late_s": round(max(0.0, late), 3),
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

    restore("after phase A")

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

        for level in PARK_LEVELS:
            print("")
            print(f"  -> parking at {level} kbps for {args.park_seconds}s")
            fired_at = now_s()

            try:
                payload = _transition(level)
            except RuntimeError as exc:
                park.append(
                    {"kbps": level, "fired_at_s": round(fired_at, 3), "error": str(exc)}
                )
                continue

            if not bool(payload.get("ok", False)):
                park.append(
                    {
                        "kbps": level,
                        "fired_at_s": round(fired_at, 3),
                        "error": str(payload)[:200],
                    }
                )
                continue

            time.sleep(args.park_seconds)
            park.append(
                {
                    "kbps": level,
                    "fired_at_s": round(fired_at, 3),
                    "parked_s": args.park_seconds,
                }
            )

        restore("after phase B")
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
            # The answer typed at input() is not echoed into a teed log, so
            # without these the anchors and the next question would land on
            # the previous prompt's line.
            print("")
            entry["rating"] = ask_int(
                f"  Rate {level} kbps picture quality",
                low=RATING_SCALE["low"],
                high=RATING_SCALE["high"],
                default=None,
                anchors=_rating_anchors(),
            )
            print("")

    state = {
        "schema": STATE_SCHEMA,
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
            "report_windows_s": list(REPORT_WINDOWS_S),
        },
        "decoy_constraint": decoy_constraint(args.window, args.ramp_gap),
        "rating_scale": RATING_SCALE,
        "aborted": aborted,
        "phase_a_end_s": round(phase_a_end, 3),
        "telemetry_preflight": telemetry,
        "conditions_before": conditions_snapshot(status),
        "conditions_after": conditions_snapshot(_status()),
        "events": events,
        "transitions": transitions,
        "marks": [m.as_dict() for m in capture.marks()],
        "park": park,
        "restores": restores,
        "restore": restores[-1] if restores else None,
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
# scoring
# --------------------------------------------------------------------------


def _union_seconds(intervals: list[tuple[float, float]]) -> float:
    total = 0.0
    current: list[float] | None = None

    for start, end in sorted(intervals):
        if current is None or start > current[1]:
            if current is not None:
                total += current[1] - current[0]
            current = [start, end]
        else:
            current[1] = max(current[1], end)

    if current is not None:
        total += current[1] - current[0]

    return total


def _score_class(
    windows: list[dict[str, Any]],
    marks: list[float],
    chance_rate: float | None,
) -> dict[str, Any]:
    """Score one class. Each class is scored on its own: a mark inside a
    decoy's ramp-matched window and a sequence's window counts in both."""
    inside: set[int] = set()
    marked = 0

    for window in windows:
        hits = [
            i
            for i, at in enumerate(marks)
            if window["start_s"] <= at <= window["end_s"]
        ]
        window["marks_s"] = [round(marks[i], 3) for i in hits]

        if hits:
            marked += 1

        inside.update(hits)

    exposure = _union_seconds(
        [(w["start_s"], w["end_s"]) for w in windows]
    )

    return {
        "events": len(windows),
        "marked": marked,
        "marks": len(inside),
        "exposure_s": round(exposure, 3),
        "marks_per_s": None if not exposure else round(len(inside) / exposure, 4),
        "chance_expected_marks": (
            None
            if chance_rate is None
            else round(chance_rate * exposure, 2)
        ),
        "windows": windows,
        "_inside": inside,
    }


def score_window(
    sequences: list[dict[str, Any]],
    decoys: list[dict[str, Any]],
    marks: list[float],
    window_s: float,
    ramp_span_s: float,
    chance_rate: float | None,
) -> dict[str, Any]:
    classes: dict[str, dict[str, Any]] = {}

    for shape in ("jump", "ramp"):
        classes[shape] = _score_class(
            [
                {
                    "index": s["index"],
                    "start_s": s["at_s"],
                    "end_s": s["end_s"] + window_s,
                }
                for s in sequences
                if s["shape"] == shape
            ],
            marks,
            chance_rate,
        )

    classes["decoy_jump_matched"] = _score_class(
        [
            {"index": d["index"], "start_s": d["at_s"], "end_s": d["at_s"] + window_s}
            for d in decoys
        ],
        marks,
        chance_rate,
    )
    classes["decoy_ramp_matched"] = _score_class(
        [
            {
                "index": d["index"],
                "start_s": d["at_s"],
                "end_s": d["at_s"] + ramp_span_s + window_s,
            }
            for d in decoys
        ],
        marks,
        chance_rate,
    )

    in_sequence = classes["jump"]["_inside"] | classes["ramp"]["_inside"]

    for data in classes.values():
        data.pop("_inside")

        for window in data["windows"]:
            window["start_s"] = round(window["start_s"], 3)
            window["end_s"] = round(window["end_s"], 3)

    return {
        "window_s": window_s,
        "classes": classes,
        "not_in_any_sequence_window": len(marks) - len(in_sequence),
    }


def score_as_installed(
    events: list[dict[str, Any]],
    marks: list[float],
    window_s: float,
) -> dict[str, Any]:
    """The pre-P2R1 attribution, kept only to print the old column beside
    the corrected one: window `[sequence start, start + W]`, each mark given
    to the most recent anchor containing it."""
    anchors = sorted(
        (
            {
                "shape": e["shape"] if e["kind"] == "sequence" else "decoy",
                "at_s": e["at_s"],
                "marks": 0,
            }
            for e in events
            if e["kind"] in ("sequence", "decoy")
        ),
        key=lambda a: a["at_s"],
    )
    unattributed = 0

    for at in marks:
        chosen = None

        for anchor in anchors:
            if anchor["at_s"] <= at <= anchor["at_s"] + window_s:
                chosen = anchor

        if chosen is None:
            unattributed += 1
        else:
            chosen["marks"] += 1

    buckets = {}

    for shape in ("jump", "ramp", "decoy"):
        rows = [a for a in anchors if a["shape"] == shape]
        buckets[shape] = {
            "events": len(rows),
            "marked": sum(1 for a in rows if a["marks"]),
            "marks": sum(a["marks"] for a in rows),
        }

    return {
        "window_s": window_s,
        "buckets": buckets,
        "unattributed_marks": unattributed,
    }


def _nearest_preceding(at: float, times: list[float]) -> float | None:
    before = [t for t in times if t <= at]
    return None if not before else max(before)


def _histogram(values: list[float | None]) -> list[dict[str, Any]]:
    edges = list(LAG_BINS_S) + [float("inf")]
    rows = []

    for low, high in zip(edges, edges[1:]):
        rows.append(
            {
                "bin_s": f"{low:g}-{high:g}" if high != float("inf") else f"{low:g}+",
                "count": sum(
                    1 for v in values if v is not None and low <= v < high
                ),
            }
        )

    rows.append(
        {"bin_s": "none before", "count": sum(1 for v in values if v is None)}
    )
    return rows


def _stats(values: list[float | None]) -> dict[str, Any]:
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


# --------------------------------------------------------------------------
# decoder session
# --------------------------------------------------------------------------


def expected_transitions(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Every transition the run fired, in order — each is one SSRC change.

    Phase A, the restore after it (if the stream was off-reference), the
    Phase B parks, and the restore after them. Pre-v2 state files kept only
    the last restore, so the Phase-A restore is derived from where Phase A
    left the stream. The final safety restore in `main()` runs after the
    state is written and fires only if an earlier restore failed; it is not
    counted.
    """
    rows: list[dict[str, Any]] = []

    for t in state.get("transitions", []):
        rows.append(
            {
                "phase": "A",
                "label": f"{t['shape']} seq {t['sequence_index']} step {t['step_index']}",
                "to_kbps": t.get("to_kbps"),
                "fired_at_s": t.get("fired_at_s"),
            }
        )

    restores = state.get("restores")

    if restores is None:
        # v1: derive the Phase-A restore; the retained `restore` is the last.
        ending = (
            state["transitions"][-1].get("to_kbps")
            if state.get("transitions")
            else REFERENCE_KBPS
        )
        derived = []

        if ending != REFERENCE_KBPS:
            derived.append(
                {"note": "after phase A (derived)", "transitioned": True, "at_s": None}
            )

        last = _dict(state.get("restore"))
        parks_ran = bool(state.get("park"))

        if parks_ran and last.get("ok") and "->" in str(last.get("detail", "")):
            derived.append(
                {"note": str(last.get("note")), "transitioned": True, "at_s": None}
            )

        restores = derived
        phase_a_restores = [r for r in restores if "phase A" in r["note"]]
        other_restores = [r for r in restores if "phase A" not in r["note"]]
    else:
        phase_a_restores = [r for r in restores if r.get("note") == "after phase A"]
        other_restores = [r for r in restores if r.get("note") != "after phase A"]

    for r in phase_a_restores:
        if r.get("transitioned"):
            rows.append(
                {"phase": "restore", "label": r["note"], "to_kbps": REFERENCE_KBPS, "fired_at_s": r.get("at_s")}
            )

    for p in state.get("park", []):
        if "error" not in p:
            rows.append(
                {"phase": "B", "label": f"park {p['kbps']}", "to_kbps": p["kbps"], "fired_at_s": p.get("fired_at_s")}
            )

    for r in other_restores:
        if r.get("transitioned"):
            rows.append(
                {"phase": "restore", "label": r["note"], "to_kbps": REFERENCE_KBPS, "fired_at_s": r.get("at_s")}
            )

    return rows


def _parse_time(text: Any) -> datetime | None:
    if not isinstance(text, str) or not text:
        return None

    for fmt in ("%Y-%m-%dT%H:%M:%S%z",):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def select_decoder_session(
    state: dict[str, Any],
    expected: int,
) -> tuple[Path | None, str]:
    """The earliest decoder session posted after this run that can cover it.

    Not in `decoder_sessions_before`, `received_at_utc` after the run's
    `generated` time, and `ssrc_changes` >= the expected count. The newest
    file is the wrong choice for any re-score: later sessions exist.
    """
    known = set(state.get("decoder_sessions_before", []))
    generated = _parse_time(state.get("generated"))
    candidates: list[tuple[datetime, Path]] = []
    rejected = 0

    for path in DECODER_ROOT.glob("*.json"):
        if path.name in known:
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rejected += 1
            continue

        received = _parse_time(payload.get("received_at_utc"))
        changes = _num(_dict(_dict(payload.get("report")).get("video")).get("ssrc_changes"))

        if received is None or generated is None or received <= generated:
            rejected += 1
            continue

        if changes is None or changes < expected:
            rejected += 1
            continue

        candidates.append((received, path))

    if not candidates:
        return None, f"no candidate ({rejected} rejected)"

    candidates.sort()
    return (
        candidates[0][1],
        f"auto: earliest of {len(candidates)} candidate(s) posted after the run "
        f"with ssrc_changes >= {expected}",
    )


def closeout_rows(report: dict[str, Any]) -> dict[str, Any]:
    """The close-out table's rows for this session
    (`evidence/D_BASE_CLOSEOUT_2026-09-23.md`, same source counters).
    Context for a session with deliberate restarts, not a gate."""
    decoder = _dict(report.get("decoder"))
    video = _dict(report.get("video"))
    duration = _num(report.get("duration_ms"))

    if not duration:
        return {}

    minutes = duration / 60000.0
    seconds = duration / 1000.0

    def per_min(value: Any) -> float | None:
        number = _num(value)
        return None if number is None else round(number / minutes, 2)

    rendered = _num(decoder.get("rendered_frames"))
    return {
        "duration_min": round(minutes, 2),
        "spikes_20_per_min": per_min(decoder.get("spike_20_ms")),
        "rendered_fps": None if rendered is None else round(rendered / seconds, 2),
        "stale_output_drops_per_min": per_min(decoder.get("stale_output_drops")),
        "video_lost_per_min_post_fec": per_min(video.get("lost_packets")),
        "max_output_gap_ms": decoder.get("max_output_gap_ms"),
    }


def decoder_view(
    report: dict[str, Any],
    expected: list[dict[str, Any]],
    marks: list[float],
    windows: list[float],
    primary: float,
) -> dict[str, Any]:
    """Requirement 4: the marks and the decoder's clock on one axis."""
    discontinuities = [_dict(d) for d in report.get("stream_discontinuities") or []]
    first_idr = [_dict(d) for d in report.get("first_idr_after_discontinuity") or []]
    columns = list(report.get("slow_event_columns") or [])
    slow = report.get("slow_events_ge_50_ms") or []

    idx_elapsed = columns.index("elapsed_ms") if "elapsed_ms" in columns else None
    idx_gap = columns.index("output_gap_ms") if "output_gap_ms" in columns else None
    idx_codec = columns.index("codec_ms") if "codec_ms" in columns else None
    slow_rows = [
        (
            row[idx_elapsed],
            row[idx_gap],
            row[idx_codec] if idx_codec is not None and len(row) > idx_codec else None,
        )
        for row in slow
        if idx_elapsed is not None
        and idx_gap is not None
        and isinstance(row, list)
        and len(row) > max(idx_elapsed, idx_gap)
    ]

    retained = _num(report.get("slow_event_retained"))
    capacity = _num(report.get("slow_event_capacity"))
    saturated = (
        retained is not None and capacity is not None and retained >= capacity
    )
    coverage_start_ms = (
        min(r[0] for r in slow_rows) if saturated and slow_rows else 0.0
    )

    coverage = {
        "retained": report.get("slow_event_retained"),
        "capacity": report.get("slow_event_capacity"),
        "retained_marked": report.get("slow_event_retained_marked"),
        "capacity_marked": report.get("slow_event_capacity_marked"),
        "retained_recent": report.get("slow_event_retained_recent"),
        "capacity_recent": report.get("slow_event_capacity_recent"),
        "saturated": saturated,
        "covered_from_decoder_ms": coverage_start_ms,
    }

    ssrc = [
        (i, d) for i, d in enumerate(discontinuities)
        if str(d.get("type")) == "ssrc_change"
    ]
    phase_a = [e for e in expected if e["phase"] == "A"]
    n = len(phase_a)
    view: dict[str, Any] = {
        "slow_event_coverage": coverage,
        "discontinuity_count": len(discontinuities),
        "ssrc_change_count": len(ssrc),
    }

    if n == 0 or len(ssrc) < n:
        view["alignment"] = {
            "ok": False,
            "reason": f"{len(ssrc)} ssrc_change discontinuities for {n} Phase-A fires",
        }
        return view

    offsets = [
        _num(d.get("elapsed_ms")) / 1000.0 - float(e["fired_at_s"])
        for e, (_, d) in zip(phase_a, ssrc[:n])
    ]
    offset = statistics.median(offsets)
    spread = max(offsets) - min(offsets)
    alignment = {
        "ok": spread <= ALIGN_MAX_SPREAD_S,
        "pairs": n,
        "offset_s": round(offset, 3),
        "spread_s": round(spread, 3),
        "max_abs_residual_s": round(max(abs(o - offset) for o in offsets), 3),
        "rule": (
            "Phase-A fires matched in order to the first N ssrc_change "
            f"entries; spread over {ALIGN_MAX_SPREAD_S:g} s means the pairing is wrong"
        ),
    }
    view["alignment"] = alignment
    coverage["covered_from_probe_s"] = round(coverage_start_ms / 1000.0 - offset, 3)

    if not alignment["ok"]:
        alignment["reason"] = (
            f"spread {spread:.3f} s > {ALIGN_MAX_SPREAD_S:g} s: the pairing is "
            "wrong; the per-mark decoder view is NOT computed"
        )
        return view

    def idr_after(index: int, elapsed: float) -> Any:
        if index < len(first_idr):
            candidate = first_idr[index]
            at = _num(candidate.get("elapsed_ms"))

            if at is not None and at >= elapsed:
                return candidate.get("resync_to_idr_ms")

        later = [
            f for f in first_idr
            if (_num(f.get("elapsed_ms")) or -1) >= elapsed
        ]
        return None if not later else later[0].get("resync_to_idr_ms")

    def max_gap(start_ms: float) -> tuple[str, tuple[Any, Any, Any] | None]:
        """Coverage — `full`, `partial` (coverage begins inside the window;
        the gap is from the covered part only) or `none` — and the largest
        gap in the window as (output_gap_ms, codec_ms, ms after start)."""
        end_ms = start_ms + SLOW_EVENT_WINDOW_S * 1000.0

        if start_ms >= coverage_start_ms:
            covered = "full"
        elif end_ms > coverage_start_ms:
            covered = "partial"
        else:
            return "none", None

        inside = [r for r in slow_rows if start_ms <= r[0] <= end_ms]

        if not inside:
            return covered, None

        worst = max(inside, key=lambda r: r[1])
        return covered, (worst[1], worst[2], round(worst[0] - start_ms))

    per_transition = []
    labels_ok = len(ssrc) == len(expected)

    for k, (disc_index, disc) in enumerate(ssrc):
        elapsed = _num(disc.get("elapsed_ms")) or 0.0
        row: dict[str, Any] = {
            "ssrc_elapsed_ms": elapsed,
            "jump_packets": disc.get("jump_packets"),
            "first_idr_ms": idr_after(disc_index, elapsed),
        }

        if k < n:
            fire = float(phase_a[k]["fired_at_s"])
            row.update(
                {
                    "label": phase_a[k]["label"],
                    "to_kbps": phase_a[k]["to_kbps"],
                    "fired_at_s": fire,
                    "residual_s": round(elapsed / 1000.0 - fire - offset, 3),
                }
            )
        else:
            known = expected[k] if labels_ok else {}
            fired = _num(known.get("fired_at_s"))
            row.update(
                {
                    "label": known.get("label", f"unlabelled ssrc {k}"),
                    "to_kbps": known.get("to_kbps"),
                    "fired_at_s": fired,
                    "at_probe_s_est": round(elapsed / 1000.0 - offset, 3),
                    "residual_s": (
                        None
                        if fired is None
                        else round(elapsed / 1000.0 - fired - offset, 3)
                    ),
                }
            )

        # Every row — Phase A, parks, restores — anchors its window on its
        # own matched ssrc_change: that is when the decoder saw the restart.
        # `fire + offset` misses it by the row's residual (0.227 s on the
        # 2026-09-24 6000 park, which put the session's worst gap outside).
        covered, worst = max_gap(elapsed)
        row["window_from"] = "ssrc_change"
        row["slow_events_covered"] = covered
        row["covered_from_s_into_window"] = (
            round((coverage_start_ms - elapsed) / 1000.0, 3)
            if covered == "partial"
            else None
        )
        row["max_output_gap_ms_in_1s"] = None if worst is None else worst[0]
        row["max_gap_codec_ms"] = None if worst is None else worst[1]
        row["max_gap_after_ssrc_ms"] = None if worst is None else worst[2]
        per_transition.append(row)

    view["per_transition"] = per_transition
    view["labels_match_expected"] = labels_ok

    per_mark = []
    disc_times = [
        ((_num(d.get("elapsed_ms")) or 0.0) / 1000.0, str(d.get("type")), d.get("jump_packets"))
        for d in discontinuities
    ]

    for at in marks:
        at_dec = at + offset
        before = [d for d in disc_times if d[0] <= at_dec]
        nearest = max(before, key=lambda d: d[0]) if before else None
        lag = None if nearest is None else at_dec - nearest[0]
        per_mark.append(
            {
                "mark_s": round(at, 3),
                "mark_decoder_s": round(at_dec, 3),
                "nearest_preceding_type": None if nearest is None else nearest[1],
                "nearest_preceding_jump_packets": None if nearest is None else nearest[2],
                "lag_s": _r(lag),
                "within": {
                    f"{w:g}": lag is not None and lag <= w for w in windows
                },
                "within_primary": lag is not None and lag <= primary,
            }
        )

    view["per_mark"] = per_mark
    return view


# --------------------------------------------------------------------------
# finalize
# --------------------------------------------------------------------------


def rating_scale_of(state: dict[str, Any]) -> dict[str, Any]:
    if isinstance(state.get("rating_scale"), dict):
        scale = dict(state["rating_scale"])
        anchors = scale.get("anchors") or {}
        scale["note"] = f"{scale['low']}-{scale['high']} (anchored: " + ", ".join(
            f"{k} = {anchors[k]}"
            for k in sorted(anchors, key=lambda x: -int(x))
        ) + ")"
        return scale

    legacy = LEGACY_RATING_SCALES.get(str(state.get("run_id")))

    if legacy:
        return dict(legacy)

    return {
        "low": None,
        "high": None,
        "anchors": None,
        "note": "unrecorded (prompt showed 1-5, unanchored)",
    }


def settling_summary(sequences: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []

    for s in sequences:
        settling = _dict(s.get("settling"))
        samples = settling.get("samples") or []
        measured = any(_num(x.get("fps")) is not None for x in samples)
        rows.append(
            {
                "index": s["index"],
                "shape": s["shape"],
                "measured": measured,
                "settled_s": settling.get("settled_s"),
                "distinct_snapshots": settling.get("distinct_snapshots"),
                "sample_interval_ms": settling.get("sample_interval_ms"),
                "snapshot_cadence_ms": settling.get("snapshot_cadence_ms"),
                "budget_ok": settling.get("budget_ok"),
            }
        )

    measured = [r for r in rows if r["measured"]]
    return {
        "sequences": rows,
        "measured": len(measured),
        "unmeasured": len(rows) - len(measured),
        "settled_s": _stats([_num(r["settled_s"]) for r in measured]),
        "never_settled_of_measured": sum(1 for r in measured if r["settled_s"] is None),
    }


def finalize(args: argparse.Namespace) -> int:
    state_path = Path(args.state) if args.state else STATE_PATH

    if not state_path.is_file():
        print(f"No state file at {state_path}. Run a session first.")
        return 2

    # Read-only: nothing below writes `state_path`.
    state = json.loads(state_path.read_text(encoding="utf-8"))
    config = _dict(state.get("config"))
    primary = float(config.get("window_s", DEFAULT_WINDOW_S))
    windows = sorted(set(REPORT_WINDOWS_S) | {primary})

    events = state.get("events", [])
    sequences = [e for e in events if e.get("kind") == "sequence"]
    decoys = [e for e in events if e.get("kind") == "decoy"]
    marks = [float(m["elapsed_s"]) for m in state.get("marks", [])]
    fires = [float(t["fired_at_s"]) for t in state.get("transitions", [])]
    phase_a_s = _num(state.get("phase_a_end_s"))
    chance_rate = None if not phase_a_s else len(marks) / phase_a_s

    ramp_spans = [s["end_s"] - s["at_s"] for s in sequences if s["shape"] == "ramp"]
    ramp_span = (
        statistics.median(ramp_spans)
        if ramp_spans
        else ramp_span_plan(float(config.get("ramp_gap_s", 4.0)))
    )

    scoring = {
        f"{w:g}": score_window(sequences, decoys, marks, w, ramp_span, chance_rate)
        for w in windows
    }
    as_installed = (
        score_as_installed(events, marks, primary)
        if state.get("schema") != STATE_SCHEMA
        else None
    )

    decoy_times = [d["at_s"] for d in decoys]
    lags = []

    for index, at in enumerate(marks):
        fire = _nearest_preceding(at, fires)
        decoy = _nearest_preceding(at, decoy_times)
        severity = state["marks"][index].get("severity")
        lags.append(
            {
                "mark_s": round(at, 3),
                "severity": severity,
                "lag_from_fire_s": None if fire is None else round(at - fire, 3),
                "lag_from_decoy_s": None if decoy is None else round(at - decoy, 3),
                "in_primary": {
                    name: any(
                        at in w["marks_s"] or round(at, 3) in w["marks_s"]
                        for w in data["windows"]
                    )
                    for name, data in scoring[f"{primary:g}"]["classes"].items()
                },
            }
        )

    placement = []

    for d in decoys:
        following = [s for s in sequences if s["at_s"] > d["at_s"]]
        next_fire = min(s["at_s"] for s in following) if following else None
        row = {
            "index": d["index"],
            "decoy_s": d["at_s"],
            "next_fire_s": next_fire,
            "late_s": d.get("late_s"),
        }

        for w in windows:
            end = d["at_s"] + ramp_span + w
            row[f"slack_at_{w:g}"] = None if next_fire is None else round(next_fire - end, 3)

        placement.append(row)

    by_shape: dict[str, dict[str, Any]] = {}

    for shape in ("jump", "ramp"):
        rows = [t for t in state.get("transitions", []) if t["shape"] == shape]
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

    lifecycle = {
        key: sum(int(t.get(key) or 0) for t in state.get("transitions", []))
        for key in (
            "fec_send_errors_delta",
            "audio_send_errors_delta",
            "controller_bad_packets_delta",
        )
    }

    expected = expected_transitions(state)

    if args.decoder:
        decoder_path: Path | None = Path(args.decoder)
        selection = "--decoder given"

        if not decoder_path.is_file():
            print(f"No decoder session at {decoder_path}.")
            return 2
    else:
        decoder_path, selection = select_decoder_session(state, len(expected))

    decoder: dict[str, Any] = {"path": None, "selection": selection}

    if decoder_path is not None:
        payload = json.loads(decoder_path.read_text(encoding="utf-8"))
        report = _dict(payload.get("report"))
        video = _dict(report.get("video"))
        dec = _dict(report.get("decoder"))
        discontinuities = report.get("stream_discontinuities") or []
        first_idr = report.get("first_idr_after_discontinuity") or []
        decoder = {
            "path": str(decoder_path),
            "selection": selection,
            "received_at_utc": payload.get("received_at_utc"),
            "client_profiler_version": report.get("client_profiler_version"),
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
            "expected_ssrc_changes": len(expected),
            "expected_breakdown": {
                "phase_a": sum(1 for e in expected if e["phase"] == "A"),
                "park": sum(1 for e in expected if e["phase"] == "B"),
                "restore": sum(1 for e in expected if e["phase"] == "restore"),
            },
            "closeout_rows": closeout_rows(report),
            "view": decoder_view(report, expected, marks, windows, primary),
        }

    scale = rating_scale_of(state)
    park = []

    for entry in state.get("park", []):
        row = dict(entry)
        row["rating_scale"] = scale["note"]
        park.append(row)

    analysis = {
        "schema": ANALYSIS_SCHEMA,
        "run_id": state["run_id"],
        "seed": state["seed"],
        "state_path": str(state_path),
        "state_schema": state.get("schema"),
        "config": config,
        "primary_window_s": primary,
        "windows_s": windows,
        "aborted": state.get("aborted"),
        "conditions_before": state.get("conditions_before"),
        "conditions_after": state.get("conditions_after"),
        "phase_a_s": phase_a_s,
        "total_marks": len(marks),
        "chance_rate_per_s": _r(chance_rate, 4),
        "ramp_span_s": round(ramp_span, 3),
        "scoring": scoring,
        "as_installed": as_installed,
        "mark_lags": lags,
        "lag_histogram_from_fire": _histogram([m["lag_from_fire_s"] for m in lags]),
        "lag_histogram_from_decoy": _histogram([m["lag_from_decoy_s"] for m in lags]),
        "decoy_placement": placement,
        "by_shape": by_shape,
        "settling": settling_summary(sequences),
        "lifecycle_totals": lifecycle,
        "rating_scale": scale,
        "park": park,
        "expected_transitions": expected,
        "decoder": decoder,
    }

    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(analysis, indent=2, sort_keys=True) + "\n"
    (RUNS_ROOT / f"{state['run_id']}.json").write_text(text, encoding="utf-8")
    JSON_LOG.write_text(text, encoding="utf-8")

    report = _run_report(analysis)
    report.write(RUNS_ROOT / f"{state['run_id']}.txt", _classification(analysis), printer=lambda _: None)
    report.write(TEXT_LOG, _classification(analysis))
    return 0


def _classification(analysis: dict[str, Any]) -> str:
    return (
        "C3_L3A_GAMEPLAY_ACCEPTANCE_ABORTED"
        if analysis.get("aborted")
        else "C3_L3A_GAMEPLAY_ACCEPTANCE_RECORDED"
    )


CLASS_LABELS = (
    ("jump", "jump"),
    ("ramp", "ramp"),
    ("decoy_jump_matched", "decoy, jump-matched"),
    ("decoy_ramp_matched", "decoy, ramp-matched"),
)


def _fmt(value: Any, spec: str = "") -> str:
    if value is None:
        return "-"
    if spec and isinstance(value, (int, float)):
        return format(value, spec)
    return str(value)


def _detection_section(report: Report, analysis: dict[str, Any], *, pooled: bool) -> None:
    primary = analysis.get("primary_window_s")
    report.section("DETECTION - the gate question")
    report.line("Sequence window: first fire .. last transition returned + W.")
    report.line("Decoys fire nothing; each is scored through a jump-matched")
    report.line("[d, d + W] and a ramp-matched [d, d + ramp_span + W] window.")
    report.line("Classes are scored independently: one mark can count in two.")
    report.field("Primary W (s)", primary if not pooled else "per-run")
    report.field("Ramp span (s, median ramp end - first fire)", analysis.get("ramp_span_s"))
    report.field("Phase A (s)", analysis.get("phase_a_s"))
    report.field("Marks total", analysis.get("total_marks"))
    report.field(
        "Chance rate (marks / phase-A s)",
        _fmt(analysis.get("chance_rate_per_s"), ".4f"),
    )

    for key in sorted(analysis["scoring"], key=float):
        block = analysis["scoring"][key]
        tag = " (primary)" if not pooled and float(key) == primary else ""
        report.line("")
        report.line(f"W = {float(key):.1f} s{tag}")
        report.table(
            ["class", "events", "marked", "marks", "exposure s", "marks/s", "chance-expected marks"],
            [
                [
                    label,
                    block["classes"][name]["events"],
                    block["classes"][name]["marked"],
                    block["classes"][name]["marks"],
                    _fmt(block["classes"][name]["exposure_s"], ".1f"),
                    _fmt(block["classes"][name]["marks_per_s"], ".3f"),
                    _fmt(block["classes"][name]["chance_expected_marks"], ".2f"),
                ]
                for name, label in CLASS_LABELS
            ],
            align_right={1, 2, 3, 4, 5, 6},
        )
        report.field("  marks in no sequence window", block["not_in_any_sequence_window"])

    report.line("")
    report.line("NO THRESHOLD IS ENCODED. Read the table; the judgement is yours.")


def _park_section(report: Report, park: list[dict[str, Any]]) -> None:
    report.section("PICTURE QUALITY - announced, separate question")

    if park:
        report.table(
            ["kbps", "acceptable", "rating", "scale"],
            [
                [
                    entry.get("kbps"),
                    entry.get("acceptable", "<not asked>"),
                    entry.get("rating", "<none>"),
                    entry.get("rating_scale", "-"),
                ]
                for entry in park
            ],
            align_right={0, 2},
        )
        report.line("Ratings are printed as answered; they are never rescaled.")
    else:
        report.line("Phase B not run.")


def _run_report(analysis: dict[str, Any]) -> Report:
    report = Report("PrivyHub C3.L3a gameplay acceptance probe")
    primary = analysis["primary_window_s"]

    report.section("RUN")
    report.field("Run id", analysis.get("run_id"))
    report.field("Seed", analysis.get("seed"))
    report.field("State file (read, not written)", analysis.get("state_path"))
    report.field("State schema", analysis.get("state_schema"))
    report.field("Aborted", analysis.get("aborted") or "no")
    report.field("Primary window (s)", primary)
    report.field("Windows reported (s)", ", ".join(f"{w:g}" for w in analysis["windows_s"]))
    report.field("Ramp rung gap (s)", analysis["config"].get("ramp_gap_s"))
    report.field("Rating scale", analysis["rating_scale"]["note"])

    _detection_section(report, analysis, pooled=False)

    old = analysis.get("as_installed")

    if old:
        report.section("AS INSTALLED - the pre-P2R1 scoring, for comparison")
        report.line("Window [sequence start, start + W]; each mark to one anchor.")
        report.table(
            ["shape", "events", "marked", "marks"],
            [
                [shape, old["buckets"][shape]["events"], old["buckets"][shape]["marked"], old["buckets"][shape]["marks"]]
                for shape in ("jump", "ramp", "decoy")
            ],
            align_right={1, 2, 3},
        )
        report.field("Marks attributed to nothing", old["unattributed_marks"])

    report.section("MARK LAGS - probe clock")
    report.table(
        ["mark s", "sev", "lag from fire", "lag from decoy"]
        + [label for _, label in CLASS_LABELS],
        [
            [
                f"{m['mark_s']:.3f}",
                _fmt(m["severity"]),
                _fmt(m["lag_from_fire_s"], ".2f"),
                _fmt(m["lag_from_decoy_s"], ".2f"),
            ]
            + ["x" if m["in_primary"].get(name) else "." for name, _ in CLASS_LABELS]
            for m in analysis["mark_lags"]
        ],
        align_right={0, 1, 2, 3},
    )
    report.line(f"(x = inside that class's window at the primary W {primary:g} s)")
    report.line("")
    report.line("Lag histogram, every mark:")
    report.table(
        ["bin s", "from nearest preceding fire", "from nearest preceding decoy"],
        [
            [a["bin_s"], a["count"], b["count"]]
            for a, b in zip(
                analysis["lag_histogram_from_fire"],
                analysis["lag_histogram_from_decoy"],
            )
        ],
        align_right={1, 2},
    )

    report.section("DECOY PLACEMENT - ramp-matched window vs the next fire")
    report.table(
        ["decoy", "at s", "next fire s", "late s"]
        + [f"slack @W{w:g}" for w in analysis["windows_s"]],
        [
            [
                row["index"],
                f"{row['decoy_s']:.3f}",
                _fmt(row["next_fire_s"], ".3f"),
                _fmt(row["late_s"]),
            ]
            + [_fmt(row[f"slack_at_{w:g}"], ".2f") for w in analysis["windows_s"]]
            for row in analysis["decoy_placement"]
        ],
        align_right=set(range(1, 4 + len(analysis["windows_s"]))),
    )
    report.line(f"Rule for new runs: slack >= {DECOY_GUARD_S:g} s at the widest W.")
    report.line("Negative slack: the decoy window overlaps the next sequence's.")

    decoder = analysis.get("decoder") or {}
    view = decoder.get("view") or {}
    alignment = view.get("alignment") or {}

    report.section("CLOCK ALIGNMENT - probe clock to decoder elapsed_ms")

    if not decoder.get("path"):
        report.line("No decoder session; alignment not possible.")
    else:
        report.field("Rule", alignment.get("rule", "-"))
        report.field("Pairs", alignment.get("pairs"))
        report.field("Median offset (s)", alignment.get("offset_s"))
        report.field("Spread (s)", alignment.get("spread_s"))
        report.field("Max |residual| (s)", alignment.get("max_abs_residual_s"))
        report.field("Alignment", "OK" if alignment.get("ok") else "FAILED")

        if not alignment.get("ok"):
            report.line(f"  {alignment.get('reason')}")

    if view.get("per_transition"):
        coverage = view["slow_event_coverage"]
        report.section("PER-TRANSITION DECODER VIEW")
        report.line(
            f"Slow events (>= 50 ms) retained {coverage['retained']} of "
            f"{coverage['capacity']} ({coverage['retained_marked']} marked + "
            f"{coverage['retained_recent']} recent); "
            + (
                f"saturated, covering decoder {coverage['covered_from_decoder_ms'] / 1000.0:.1f} s "
                f"onward = probe {coverage.get('covered_from_probe_s')} s onward."
                if coverage["saturated"]
                else "not saturated: the whole session is covered."
            )
        )
        if coverage["saturated"]:
            report.line(
                "Before that point only discontinuities exist: 'not covered' "
                "is not 'no gap'; 'partial' is the covered part only."
            )

        report.line("'-' in the gap column means covered and no event >= 50 ms.")
        report.line("")
        report.table(
            ["transition", "to", "fire s", "ssrc ms", "resid s", "jump pk", "1st IDR ms", f"max gap ms in {SLOW_EVENT_WINDOW_S:g}s", "at +ms", "codec ms"],
            [
                [
                    row["label"],
                    _fmt(row.get("to_kbps")),
                    _fmt(row.get("fired_at_s"), ".3f") if row.get("fired_at_s") is not None else f"~{row.get('at_probe_s_est')}",
                    _fmt(row["ssrc_elapsed_ms"], ".0f"),
                    _fmt(row.get("residual_s"), "+.3f"),
                    _fmt(row.get("jump_packets")),
                    _fmt(row.get("first_idr_ms")),
                    (
                        _fmt(row.get("max_output_gap_ms_in_1s"))
                        if row["slow_events_covered"] == "full"
                        else (
                            f"{_fmt(row.get('max_output_gap_ms_in_1s'))} partial "
                            f"(from +{row['covered_from_s_into_window']:.2f} s)"
                        )
                        if row["slow_events_covered"] == "partial"
                        else "not covered"
                    ),
                    _fmt(row.get("max_gap_after_ssrc_ms")),
                    _fmt(row.get("max_gap_codec_ms")),
                ]
                for row in view["per_transition"]
            ],
            align_right={1, 2, 3, 4, 5, 6, 7, 8, 9},
        )
        report.line(
            f"Every row's {SLOW_EVENT_WINDOW_S:g} s window starts at its own matched "
            "ssrc_change (Phase A, parks"
        )
        report.line(
            "and restores alike); the fire time and its residual are beside it. "
            "'at +ms' and"
        )
        report.line("'codec ms' belong to the largest gap in the window.")
        report.line(
            "Pre-v2 state has no probe fire time for parks and restores "
            "('~' = ssrc - offset)."
        )

    if view.get("per_mark"):
        report.section("MARKS ON THE DECODER AXIS - requirement 4")
        report.table(
            ["mark s", "decoder s", "nearest preceding", "jump pk", "lag s"]
            + [f"<=W{w}" for w in view["per_mark"][0]["within"]],
            [
                [
                    f"{m['mark_s']:.3f}",
                    f"{m['mark_decoder_s']:.3f}",
                    _fmt(m["nearest_preceding_type"]),
                    _fmt(m["nearest_preceding_jump_packets"]),
                    _fmt(m["lag_s"], ".2f"),
                ]
                + ["y" if v else "." for v in m["within"].values()]
                for m in view["per_mark"]
            ],
            align_right={0, 1, 3, 4},
        )

    _park_section(report, analysis.get("park", []))

    report.section("C3.L4 READINESS")
    report.line("What an automatic controller would need, and whether it is known.")
    report.line("")

    for shape in ("jump", "ramp"):
        data = analysis["by_shape"].get(shape, {})
        report.field(f"{shape} cycles measured", data.get("cycles", 0))
        report.field(f"  {shape} spawn_ms", data.get("spawn_ms"))
        report.field(f"  {shape} first_rtp_resume_ms", data.get("first_rtp_resume_ms"))
        report.field(f"  {shape} host_verified_ms", data.get("host_verified_ms"))

    settling = analysis["settling"]
    report.line("")
    report.field("Settling measured on sequences", f"{settling['measured']} of {settling['measured'] + settling['unmeasured']}")

    if settling["unmeasured"]:
        report.line(
            f"  {settling['unmeasured']} unmeasured: every fps sample None "
            "(pre-P2R1 field paths). Not 'never settled' - not measured."
        )

    if settling["measured"]:
        report.field("Telemetry settling after a sequence (s)", settling["settled_s"])
        report.field("Measured sequences that never settled in budget", settling["never_settled_of_measured"])
        report.table(
            ["seq", "shape", "settled s", "distinct", "interval ms", "cadence ms", "budget >= 3 intervals"],
            [
                [
                    r["index"], r["shape"], _fmt(r["settled_s"]), _fmt(r["distinct_snapshots"]),
                    _fmt(r["sample_interval_ms"]), _fmt(r["snapshot_cadence_ms"]), _fmt(r["budget_ok"]),
                ]
                for r in settling["sequences"]
                if r["measured"]
            ],
            align_right={0, 2, 3, 4, 5},
        )

    report.line("  -> a controller MUST NOT sample telemetry inside the settling window;")
    report.line("     inside it, it is measuring the restart, not the network.")
    report.line("")
    report.field("Cumulative lifecycle over the whole session", analysis["lifecycle_totals"])
    report.line("  -> all three must be 0. Non-zero means repeated transitions")
    report.line("     degrade a subsystem that a single transition does not.")
    report.line("")
    report.field("Minimum rung spacing exercised (s)", analysis["config"].get("ramp_gap_s"))
    report.field(
        "Transitions in one session (Phase A)",
        sum(analysis["by_shape"].get(s, {}).get("cycles", 0) for s in ("jump", "ramp")),
    )

    report.section("CLIENT DECODER SESSION")

    if decoder.get("path"):
        for key in (
            "path",
            "selection",
            "received_at_utc",
            "client_profiler_version",
            "duration_ms",
            "ssrc_changes",
            "expected_ssrc_changes",
            "expected_breakdown",
            "ssrc_discontinuity_count",
            "discontinuity_count",
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
                f"  WARNING: {expected} transitions fired (Phase A + parks + "
                f"restores) but the client saw {actual} SSRC changes."
            )
            report.line("  The decoder session may not cover the whole probe run.")

        rows = decoder.get("closeout_rows") or {}
        report.section("DECODER SESSION BESIDE THE CLOSE-OUT TABLE - context, not a gate")
        report.line("Rows as evidence/D_BASE_CLOSEOUT_2026-09-23.md defines them.")
        report.line("This session carries deliberate restarts; it is not a baseline session.")

        for key in (
            "duration_min",
            "spikes_20_per_min",
            "rendered_fps",
            "stale_output_drops_per_min",
            "video_lost_per_min_post_fec",
            "max_output_gap_ms",
        ):
            report.field(key, rows.get(key))
    else:
        report.field("selection", decoder.get("selection"))
        report.line("No decoder session found.")
        report.line("Run --finalize again once the client has posted one,")
        report.line("or name it with --decoder.")

    report.section("CONDITIONS")
    report.field("before", analysis.get("conditions_before"))
    report.field("after", analysis.get("conditions_after"))
    report.line("")
    report.line("Transport conditions are not constant between sessions.")
    report.line("Do not compare gap figures across runs without comparing these.")

    _limits_section(report)
    return report


def _limits_section(report: Report) -> None:
    report.section("WHAT THIS DOES NOT ESTABLISH")
    report.line("- Whether C3.L4 is authorized. That is a human judgement on")
    report.line("  the detection table and the picture ratings above.")
    report.line("- Anything at n = one run. Compare marked classes against the")
    report.line("  chance-expected marks and against each other; pool runs.")
    report.line("- Any controller policy: thresholds, hysteresis, sample cadence.")
    report.line("- Behaviour under real network pressure. Every transition here")
    report.line("  fired from a schedule, not from a degraded condition.")


# --------------------------------------------------------------------------
# aggregate
# --------------------------------------------------------------------------


def pool_decision(data: dict[str, Any]) -> list[str]:
    """Why a finalized run may not be pooled; empty means it may."""
    reasons: list[str] = []

    if data.get("schema") != ANALYSIS_SCHEMA:
        reasons.append(
            f"analysis schema {data.get('schema')!r}, not {ANALYSIS_SCHEMA}"
        )
        return reasons

    if data.get("state_schema") != STATE_SCHEMA:
        reasons.append(
            f"state schema {data.get('state_schema')!r}, not {STATE_SCHEMA}"
        )

    config = _dict(data.get("config"))

    for key, want in PREREGISTERED_CONFIG.items():
        have = _num(config.get(key))

        if have is None or abs(have - float(want)) > 1e-9:
            reasons.append(f"{key} {config.get(key)!r} (pre-registered {want:g})")

    return reasons


def aggregate(args: argparse.Namespace) -> int:
    pool_all = bool(getattr(args, "pool_all", False))
    paths = sorted(RUNS_ROOT.glob("*.json"))
    runs = []
    listing: list[dict[str, Any]] = []

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            listing.append({"file": path.name, "pooled": False, "reasons": [f"unreadable: {exc}"]})
            continue

        reasons = pool_decision(data)
        structural = data.get("schema") != ANALYSIS_SCHEMA

        if not reasons or (pool_all and not structural):
            runs.append(data)
            listing.append(
                {"file": path.name, "pooled": True, "reasons": reasons}
            )
        else:
            listing.append(
                {"file": path.name, "pooled": False, "reasons": reasons}
            )

    for row in listing:
        state = "POOLED " if row["pooled"] else "SKIPPED"
        why = "; ".join(row["reasons"]) or "pre-registered"
        print(f"  {state} {row['file']}: {why}")

    window_keys = (
        set.intersection(*(set(r["scoring"]) for r in runs)) if runs else set()
    )
    scoring: dict[str, Any] = {}

    for key in window_keys:
        classes: dict[str, Any] = {}

        for name, _ in CLASS_LABELS:
            blocks = [r["scoring"][key]["classes"][name] for r in runs]
            exposure = sum(b["exposure_s"] for b in blocks)
            marks = sum(b["marks"] for b in blocks)
            expected = [b.get("chance_expected_marks") for b in blocks]
            classes[name] = {
                "events": sum(b["events"] for b in blocks),
                "marked": sum(b["marked"] for b in blocks),
                "marks": marks,
                "exposure_s": round(exposure, 3),
                "marks_per_s": None if not exposure else round(marks / exposure, 4),
                "chance_expected_marks": (
                    None
                    if any(e is None for e in expected)
                    else round(sum(expected), 2)
                ),
            }

        scoring[key] = {
            "window_s": float(key),
            "classes": classes,
            "not_in_any_sequence_window": sum(
                r["scoring"][key]["not_in_any_sequence_window"] for r in runs
            ),
        }

    phase_a = sum(float(r.get("phase_a_s") or 0.0) for r in runs)
    total_marks = sum(int(r.get("total_marks", 0)) for r in runs)
    park = [p for r in runs for p in r.get("park", [])]
    lifecycle = {
        key: sum(int(r.get("lifecycle_totals", {}).get(key, 0)) for r in runs)
        for key in (
            "fec_send_errors_delta",
            "audio_send_errors_delta",
            "controller_bad_packets_delta",
        )
    }
    settled = [
        _num(s.get("settled_s"))
        for r in runs
        for s in r.get("settling", {}).get("sequences", [])
        if s.get("measured")
    ]

    analysis = {
        "schema": "privyhub_c3_l3a_aggregate_v2",
        "pool_rule": {
            "state_schema": STATE_SCHEMA,
            "config": PREREGISTERED_CONFIG,
            "pool_all_override": pool_all,
        },
        "files": listing,
        "run_ids": [r["run_id"] for r in runs],
        "run_count": len(runs),
        "primary_windows_s": {r["run_id"]: r["primary_window_s"] for r in runs},
        "phase_a_s": round(phase_a, 3),
        "total_marks": total_marks,
        "chance_rate_per_s": None if not phase_a else round(total_marks / phase_a, 4),
        "ramp_span_s": {r["run_id"]: r.get("ramp_span_s") for r in runs},
        "scoring": scoring,
        "cycles": {
            shape: sum(r["by_shape"].get(shape, {}).get("cycles", 0) for r in runs)
            for shape in ("jump", "ramp")
        },
        "settling_s": _stats(settled),
        "settling_measured": len(settled),
        "lifecycle_totals": lifecycle,
        "park": park,
    }

    AGG_JSON.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = Report(
        "PrivyHub C3.L3a gameplay acceptance probe - pooled"
        + (" - POOL-ALL OVERRIDE" if pool_all else "")
    )

    if pool_all:
        report.line(
            "WARNING: --pool-all - runs outside the pre-registration are "
            "pooled below; this table is not the pre-registered result."
        )

    report.section("POOL")
    report.line(
        f"Pooled only if state schema is {STATE_SCHEMA} and config is "
        "the pre-registration:"
    )
    report.line(
        "  " + ", ".join(f"{k} {v:g}" for k, v in PREREGISTERED_CONFIG.items())
    )
    report.field("Run files found", len(listing))
    report.field("Pooled", sum(1 for row in listing if row["pooled"]))
    report.field("Skipped", sum(1 for row in listing if not row["pooled"]))

    for label, pooled in (("POOLED", True), ("SKIPPED", False)):
        rows = [row for row in listing if row["pooled"] is pooled]
        report.line("")
        report.line(f"{label}:")

        if not rows:
            report.line("  (none)")

        for row in rows:
            why = "; ".join(row["reasons"]) or "pre-registered"
            report.line(f"  {row['file']}: {why}")

    if not runs:
        report.line("")
        report.line("Nothing pooled: no pre-registered run has been finalized.")
        _limits_section(report)
        report.write(AGG_TEXT, "C3_L3A_GAMEPLAY_ACCEPTANCE_RECORDED")
        return 0

    report.section("RUN")
    report.field("Runs pooled", analysis["run_count"])
    report.field("Run ids", ", ".join(analysis["run_ids"]))
    report.field("Primary W per run (s)", analysis["primary_windows_s"])
    report.field("Ramp span per run (s)", analysis["ramp_span_s"])
    _detection_section(report, analysis, pooled=True)
    _park_section(report, park)
    report.section("C3.L4 READINESS")
    report.field("Cycles pooled", analysis["cycles"])
    report.field("Settling measured on sequences", analysis["settling_measured"])
    report.field("Telemetry settling after a sequence (s)", analysis["settling_s"])
    report.field("Cumulative lifecycle", lifecycle)
    _limits_section(report)
    report.write(AGG_TEXT, "C3_L3A_GAMEPLAY_ACCEPTANCE_RECORDED")
    return 0


# --------------------------------------------------------------------------
# plan
# --------------------------------------------------------------------------


def show_plan(args: argparse.Namespace) -> int:
    seed = args.seed if args.seed is not None else 1

    try:
        schedule = build_schedule(
            traversals=args.traversals,
            dwell_min=args.dwell_min,
            dwell_max=args.dwell_max,
            ramp_gap=args.ramp_gap,
            window_s=args.window,
            seed=seed,
        )
    except ValueError as exc:
        print(f"PLAN REFUSED: {exc}")
        return 2

    rule = decoy_constraint(args.window, args.ramp_gap)
    cycles = sum(len(item["steps"]) for item in schedule)
    estimate = sum(
        item["dwell_s"] + len(item["steps"]) * (TRANSITION_EST_S + item["ramp_gap_s"])
        for item in schedule
    )
    holds = all(item["decoy_slack_s"] >= rule["guard_s"] - 1e-9 for item in schedule)

    print("C3.L3a plan (shape counts only - a real run does not print this)")
    print(f"  seed         : {seed}")
    print(f"  traversals   : {args.traversals}")
    print(f"  jumps        : {sum(1 for i in schedule if i['shape'] == 'jump')}")
    print(f"  ramps        : {sum(1 for i in schedule if i['shape'] == 'ramp')}")
    print(f"  transitions  : {cycles}")
    print(f"  decoys       : {len(schedule)}")
    print(f"  dwell        : {args.dwell_min:g}-{args.dwell_max:g} s")
    print(f"  primary W    : {args.window:g} s (reported: {', '.join(f'{w:g}' for w in REPORT_WINDOWS_S)})")
    print(f"  phase A est. : ~{estimate / 60.0:.1f} min")
    print(f"  phase B est. : ~{len(PARK_LEVELS) * args.park_seconds / 60.0:.1f} min")
    print("")
    print("  Decoy placement rule: decoy >= end + "
          f"{rule['earliest_offset_s']:g} s (settling budget + one poll timeout);")
    print(f"  decoy + ramp span {rule['ramp_span_plan_s']:g} s (planned) + W "
          f"{rule['window_for_placement_s']:g} s (widest reported) must end "
          f">= {rule['guard_s']:g} s before the next fire.")
    print(f"  Minimum dwell for the rule: {rule['min_dwell_s']:.1f} s")
    print("")
    print("  dwell  dwell s  decoy at s  window end s  slack s")

    for item in schedule:
        print(
            f"  {item['index']:5d}  {item['dwell_s']:7.1f}  {item['decoy_offset_s']:10.1f}"
            f"  {item['decoy_window_end_s']:12.1f}  {item['decoy_slack_s']:7.1f}"
        )

    print("")
    print(f"  Constraint holds on every dwell: {'YES' if holds else 'NO'} "
          f"(min slack {min(i['decoy_slack_s'] for i in schedule):.1f} s)")
    return 0 if holds else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument(
        "--traversals", type=int, default=int(PREREGISTERED_CONFIG["traversals"])
    )
    parser.add_argument(
        "--ramp-gap", type=float, default=PREREGISTERED_CONFIG["ramp_gap_s"], dest="ramp_gap"
    )
    parser.add_argument(
        "--dwell-min", type=float, default=PREREGISTERED_CONFIG["dwell_min_s"], dest="dwell_min"
    )
    parser.add_argument(
        "--dwell-max", type=float, default=PREREGISTERED_CONFIG["dwell_max_s"], dest="dwell_max"
    )
    parser.add_argument(
        "--park-seconds",
        type=int,
        default=int(PREREGISTERED_CONFIG["park_seconds"]),
        dest="park_seconds",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=DEFAULT_WINDOW_S,
        help="primary association window W for a new run (s); --finalize "
        "uses the run's recorded W and always reports 2.5, 5.0 and 8.0",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-park", action="store_true", dest="no_park")
    parser.add_argument(
        "--pool-all",
        action="store_true",
        dest="pool_all",
        help="--aggregate: also pool v2 runs outside the pre-registration "
        "(the report header says so); default off",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="--finalize: state file to score (read only; default: the last run's)",
    )
    parser.add_argument(
        "--decoder",
        default=None,
        help="--finalize: decoder session to align against (default: the "
        "earliest posted after the run that has enough SSRC changes)",
    )
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
