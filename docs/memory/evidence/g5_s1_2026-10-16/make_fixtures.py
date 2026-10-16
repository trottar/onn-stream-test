#!/usr/bin/env python3
"""G5-S1: replay fixtures from three recorded runs, redacted at the boundary.

Kept: only counters and numbers.
- the stream telemetry rows inside the run's 20-min window (`summary.json`
  window, the rows `e1_suite.telemetry_figures` counts), with
  `receiver` / `decoder` / `latency` fields allow-listed by name;
- the live ladder's `acted` rows and the recovery events, as
  `{t_s, kind, detail}`, with `t_s` on the session's elapsed clock;
- for runs the companion's heartbeat log covers, the deltas of its FEC /
  resync / audio-starvation counters over the window.

Dropped: everything else. No timestamp, address, host name or identifier
reaches a fixture.

    python3 docs/memory/evidence/g5_s1_2026-10-16/make_fixtures.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EV = ROOT / "docs" / "memory" / "evidence"
OUT = ROOT / "tests" / "wan_telemetry" / "fixtures"
HEARTBEAT_LOG = ROOT / "logs" / "games" / "native_stream_heartbeat.log"

RUNS = {
    "e4_s4b_run3_lossy": EV / "e4_s4b_2026-10-10/runs/E1-PS1-STREAM/run3",
    "e4_s4b_run2_cleanest": EV / "e4_s4b_2026-10-10/runs/E1-PS1-STREAM/run2",
    "cl_b2_flag_run1": EV / "cl_b2_2026-10-16/runs/E1-PS1-STREAM_flag/run1",
}
KEEP = {
    "receiver": ("recent_mbps", "recent_fps", "packets_delta", "lost_packets_delta",
                 "late_or_reordered_packets_delta", "forward_gap_events_delta",
                 "interarrival_jitter_ms", "waiting_for_idr"),
    "decoder": ("queue_depth", "queue_depth_delta", "queued_frames_delta", "rendered_frames_delta",
                "dropped_frames_delta", "queue_overflow_drops_delta", "stale_output_drops_delta"),
    "latency": ("control_round_trip_ms", "receive_to_decode_ms", "output_gap_ms"),
}
HB_COUNTERS = ("fec_recovered_packets", "fec_unrecoverable_groups", "stream_resyncs",
               "audio_prolonged_starvation_events", "lost_packets")


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hb_rows = []
    if HEARTBEAT_LOG.exists():
        for line in HEARTBEAT_LOG.read_text().splitlines():
            try:
                hb_rows.append(json.loads(line))
            except ValueError:
                continue
    for name, rd in RUNS.items():
        summary = json.loads((rd / "summary.json").read_text())
        t0, t1 = summary["window"]["from"], summary["window"]["to"]
        rows, seen, offsets = [], set(), []
        for line in (rd / "telemetry.jsonl").read_text().splitlines():
            r = json.loads(line)
            if r.get("fresh") and t0 <= r["at_utc"] <= t1 and r.get("elapsed_ms") not in seen:
                seen.add(r.get("elapsed_ms"))
                offsets.append(ts(r["at_utc"]) - r["elapsed_ms"] / 1000.0)
                row = {"fresh": True, "elapsed_ms": r["elapsed_ms"]}
                for block, keys in KEEP.items():
                    row[block] = {k: (r.get(block) or {}).get(k) for k in keys if k in (r.get(block) or {})}
                rows.append(row)
        offsets.sort()
        offset = offsets[len(offsets) // 2]          # session start on the wall clock (median)
        events = []
        for line in (rd / "decisions.jsonl").read_text().splitlines():
            d = json.loads(line)
            if d.get("acted") and t0 <= d.get("at_utc", "") <= t1:
                events.append({"t_s": round(ts(d["at_utc"]) - offset, 3), "kind": "ladder_transition",
                               "detail": f"{d.get('reason')}:{d.get('stream_kbps')}->{d.get('level_kbps')}"})
        rec_path = rd / "recovery.jsonl"
        for line in (rec_path.read_text().splitlines() if rec_path.exists() else []):
            e = json.loads(line)
            if t0 <= e.get("at_utc", "") <= t1 and e.get("event") in ("desync_pause", "resumed"):
                events.append({"t_s": round(ts(e["at_utc"]) - offset, 3),
                               "kind": "recovery_pause" if e["event"] == "desync_pause" else "recovery_resume",
                               "detail": str(e.get("trigger") or e.get("from_state") or "")})
        events.sort(key=lambda e: e["t_s"])
        hb = [h for h in hb_rows if t0 <= h.get("received_at_utc", "") <= t1]
        heartbeat = None
        if len(hb) > 1:
            heartbeat = {"rows": len(hb), "span_s": round(ts(hb[-1]["received_at_utc"]) - ts(hb[0]["received_at_utc"]), 1)}
            for k in HB_COUNTERS:
                if k in hb[0] and k in hb[-1]:
                    heartbeat[k] = hb[-1][k] - hb[0][k]
        fixture = {
            "name": name,
            "source": str(rd.relative_to(ROOT)),
            "window_s": round(ts(t1) - ts(t0), 1),
            "recorded_loss_per_min": (summary.get("key") or {}).get("telemetry", {}).get("receiver_lost_packets_per_min"),
            "telemetry": rows,
            "events": events,
            "heartbeat": heartbeat,
        }
        (OUT / f"{name}.json").write_text(json.dumps(fixture, indent=1, sort_keys=True) + "\n")
        print(f"{name}: {len(rows)} reports, {len(events)} events, heartbeat {'yes' if heartbeat else 'not covered'},"
              f" recorded loss {fixture['recorded_loss_per_min']}/min")


if __name__ == "__main__":
    main()
