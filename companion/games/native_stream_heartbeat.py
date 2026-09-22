"""D-BASE-R2 piece 2: a host-side trace of a terminal client stall.

A stall that never ends posts no decoder session report, so today the host
keeps no record that the session existed at all. The client posts a small
fixed payload every two seconds while a session is open; this module appends
each one to a single JSON-lines log and can read the newest one back for
`native-stream-status`.

Trace only. Nothing here acts on a heartbeat, or on its absence — automatic
recovery is a separate item and is not authorized.

No addresses are recorded: only the counters the client sends, plus host
time.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from games.log_rotation import append_line


# v2 (D-BASE-R5): the receiver's cumulative loss counters ride along, so a
# per-minute loss series is readable from this log alone.
# v3 (D-BASE-P7): the audio counters ride along too, so
# `prolonged_starvation_events` can be read per tick against the audio
# arrival gap that the same tick measured.
SCHEMA = "privyhub_native_stream_heartbeat_v3"

# The client's core counters, plus its own sequence and interval. Anything
# else in the query is ignored rather than recorded.
FIELDS = (
    "sequence",
    "interval_ms",
    "last_output_age_ms",
    "rendered_frames",
    "queued_frames",
    "rx_packets",
    "elapsed_ms",
)

# D-BASE-P7: the audio side, cumulative and read from the same
# `audioReceiver.snapshot()` the end-of-session report reads, plus the
# per-tick maximum inter-arrival gap. Each is optional and **absent rather
# than zero** when the client does not send it -- the `D-BASE-P4` rule.
#   audio_max_arrival_gap_ms          this tick's window, reset on read
#   audio_session_max_arrival_gap_ms  the whole session, never reset
AUDIO_FIELDS = (
    "audio_prolonged_starvation_events",
    "audio_lost_packets",
    "audio_rx_packets",
    "audio_concealed_underruns",
    "audio_concealed_loss_packets",
    "audio_underruns",
    "audio_queue_depth",
    "audio_queue_ms",
    "audio_max_arrival_gap_ms",
    "audio_session_max_arrival_gap_ms",
)

# D-BASE-T1 piece 1: the onn's own thermal state, when the device reports
# it. Each is optional and absent rather than faked when the device does
# not: a missing field is the finding.
#   thermal_status    int, the 0-6 PowerManager NONE..SHUTDOWN scale
#   thermal_headroom  float, NaN-free (the client omits it when NaN)
#   thermal_zones_c   str, "zone=c,zone=c" from /sys/class/thermal
THERMAL_FIELDS = (
    "thermal_status",
    "thermal_headroom",
    "thermal_zones_c",
)

# D-BASE-R5: the receiver's own cumulative counters, the same ones the
# end-of-session report reads. Passed through unchanged — nothing here
# derives, smooths or resets them, so a delta between any two heartbeats of
# one session is exact. Each is optional: a client that does not send one
# (an older build) records nothing for it rather than a zero.
LOSS_FIELDS = (
    "lost_packets",
    "lost_packets_in_resyncs",
    "forward_gap_events",
    "max_forward_gap_packets",
    "stream_resyncs",
    "fec_recovered_packets",
    "fec_unrecoverable_groups",
)

# One line is ~200 bytes before D-BASE-R5, ~370 after, and ~620 since
# D-BASE-P7 added the audio block; a session writes ~30 per minute.
MAX_TAIL_BYTES = 8_192

# D-BASE-R5: `loss_per_min_recent` needs a whole 60 s window, which at ~370
# bytes a line and 30 lines a minute will not fit in MAX_TAIL_BYTES. This
# reads far enough back to hold ~3 minutes.
LOSS_WINDOW_TAIL_BYTES = 64 * 1024
LOSS_WINDOW_SECONDS = 60.0

# D-BASE-R4 item 4. At ~360 KB per hour of play, 4 MB is roughly eleven
# hours of streaming per file and 44 hours across the set.
MAX_LOG_BYTES = 4 * 1024 * 1024
KEEP_ROTATED = 3


def heartbeat_log_path(
    project_root: Path,
) -> Path:
    return (
        Path(project_root)
        / "logs"
        / "games"
        / "native_stream_heartbeat.log"
    )


def append_native_stream_heartbeat(
    project_root: Path,
    values: dict[str, int],
) -> dict[str, Any]:
    received_at = datetime.now(
        timezone.utc
    )

    record: dict[str, Any] = {
        "schema": SCHEMA,
        "received_at_utc": (
            received_at
            .isoformat(
                timespec="milliseconds"
            )
            .replace(
                "+00:00",
                "Z",
            )
        ),
    }

    for field in FIELDS:
        if field in values:
            record[field] = values[field]

    for field in LOSS_FIELDS:
        if field in values:
            record[field] = values[field]

    for field in AUDIO_FIELDS:
        if field in values:
            record[field] = values[field]

    for field in THERMAL_FIELDS:
        if field in values:
            record[field] = values[field]

    path = heartbeat_log_path(
        project_root
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rotated = append_line(
        path,
        json.dumps(
            record,
            sort_keys=False,
        ),
        max_bytes=MAX_LOG_BYTES,
        keep=KEEP_ROTATED,
    )

    return {
        "ok": True,
        "recorded": True,
        "rotated": bool(rotated),
        "log_path": (
            path.relative_to(
                Path(project_root)
            ).as_posix()
        ),
        "heartbeat": record,
    }


def latest_native_stream_heartbeat(
    project_root: Path,
) -> dict[str, Any] | None:
    """The newest heartbeat on disk, or None if there is none.

    Reads only the tail of the log, so this stays cheap as the file grows.
    A truncated or malformed final line is treated as absent rather than
    raising: a status call must not fail because a log line is torn.
    """

    path = heartbeat_log_path(
        project_root
    )

    try:
        size = path.stat().st_size
    except OSError:
        return None

    if size <= 0:
        return None

    try:
        with path.open(
            "rb",
        ) as handle:
            if size > MAX_TAIL_BYTES:
                handle.seek(
                    size - MAX_TAIL_BYTES
                )

            tail = handle.read()
    except OSError:
        return None

    for line in reversed(
        tail.splitlines()
    ):
        text = line.strip()

        if not text:
            continue

        try:
            record = json.loads(
                text.decode(
                    "utf-8",
                    "replace",
                )
            )
        except json.JSONDecodeError:
            continue

        if isinstance(
            record,
            dict,
        ):
            return record

    return None


def _tail_records(
    project_root: Path,
    tail_bytes: int,
) -> list[dict[str, Any]]:
    """Parsed heartbeat records from the tail of the log, oldest first.

    Torn or malformed lines are skipped rather than raised on: a status
    call must not fail because a log line is half-written.
    """

    path = heartbeat_log_path(
        project_root
    )

    try:
        size = path.stat().st_size
    except OSError:
        return []

    if size <= 0:
        return []

    try:
        with path.open("rb") as handle:
            if size > tail_bytes:
                handle.seek(
                    size - tail_bytes
                )
                handle.readline()

            raw = handle.read()
    except OSError:
        return []

    records: list[dict[str, Any]] = []

    for line in raw.splitlines():
        text = line.strip()

        if not text:
            continue

        try:
            record = json.loads(
                text.decode(
                    "utf-8",
                    "replace",
                )
            )
        except json.JSONDecodeError:
            continue

        if isinstance(record, dict):
            records.append(record)

    return records


def loss_per_min_recent(
    project_root: Path,
    window_seconds: float = LOSS_WINDOW_SECONDS,
) -> dict[str, Any] | None:
    """D-BASE-R5: loss per minute over the last `window_seconds` of the
    current session, for watching a live session.

    Uses the client's own `elapsed_ms` as the clock, so it measures the
    session and not the wall time between a restart and now, and a
    heartbeat whose `elapsed_ms` goes backwards ends the window — that is a
    new session and its counters restart from zero.

    Returns None when there is no session on disk, when the client is too
    old to send the counters, or when the window holds fewer than two
    heartbeats. None is "not measurable", never 0.
    """

    records = [
        r for r in _tail_records(
            project_root,
            LOSS_WINDOW_TAIL_BYTES,
        )
        if "lost_packets" in r
        and "elapsed_ms" in r
    ]

    if len(records) < 2:
        return None

    newest = records[-1]

    try:
        end_elapsed = float(
            newest["elapsed_ms"]
        )
    except (TypeError, ValueError):
        return None

    window_ms = window_seconds * 1000.0
    session: list[dict[str, Any]] = []

    # walk back while still inside this session and inside the window
    for record in reversed(records):
        try:
            elapsed = float(
                record["elapsed_ms"]
            )
        except (TypeError, ValueError):
            break

        if elapsed > end_elapsed:
            # a later session's line; everything older belongs to it too
            break

        session.append(record)

        if end_elapsed - elapsed >= window_ms:
            break

    session.reverse()

    if len(session) < 2:
        return None

    first, last = session[0], session[-1]

    try:
        span_ms = (
            float(last["elapsed_ms"])
            - float(first["elapsed_ms"])
        )
        lost = (
            int(last["lost_packets"])
            - int(first["lost_packets"])
        )
    except (TypeError, ValueError, KeyError):
        return None

    if span_ms <= 0:
        return None

    def delta(field: str) -> int | None:
        try:
            return (
                int(last[field])
                - int(first[field])
            )
        except (TypeError, ValueError, KeyError):
            return None

    return {
        "window_seconds": round(
            span_ms / 1000.0,
            3,
        ),
        "heartbeats": len(session),
        "lost_packets": lost,
        "loss_per_min": round(
            lost / (span_ms / 60_000.0),
            2,
        ),
        "forward_gap_events": delta(
            "forward_gap_events"
        ),
        "stream_resyncs": delta(
            "stream_resyncs"
        ),
        "fec_recovered_packets": delta(
            "fec_recovered_packets"
        ),
        "rx_packets": delta("rx_packets"),
        "session_elapsed_ms": int(
            end_elapsed
        ),
    }
