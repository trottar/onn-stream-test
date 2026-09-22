#!/usr/bin/env python3
"""C5 - resync-to-IDR and resync-to-first-render distribution.

A copy of the loader shape used by
`evidence/group_a_2026-09-20/a2_rescore_decoder_sessions.py`, extended for
the per-discontinuity lists. **The Group A script is not modified.**

Per-discontinuity data (`stream_discontinuities`,
`first_idr_after_discontinuity`) exists only in reports written by the
`C3.L2b` build and later; older reports carry the whole-session
`max_resync_to_idr_ms` and are reported separately, because a session with
more than one resync cannot attribute its maximum to one of them.

resync-to-first-render is **not instrumented**. The proxy used here is the
first retained slow-event row at or after the discontinuity's `elapsed_ms`,
which exists only when that frame was slow enough to be recorded; it is a
lower bound on the population and is labelled as such.

Usage: python3 c5_resync_idr_distribution.py --repo /path/to/onn-stream-test
"""
from __future__ import annotations
import argparse, glob, json, os, statistics as st

GOP_MS = 250.0  # GOP 15 at 60 fps


def pct(values, q):
    if not values:
        return None
    v = sorted(values)
    i = (len(v) - 1) * q / 100.0
    lo, hi = int(i), min(int(i) + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 1)


def describe(name, values):
    if not values:
        return {"metric": name, "n": 0}
    return {
        "metric": name,
        "n": len(values),
        "p50": pct(values, 50),
        "p90": pct(values, 90),
        "max": round(max(values), 1),
        "min": round(min(values), 1),
        "mean": round(st.mean(values), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--since", default="2026-09-16")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    outdir = a.out or os.path.dirname(os.path.abspath(__file__))

    per_disc = []          # one row per discontinuity, post-C3.L2b reports
    session_only = []      # whole-session max, pre-C3.L2b reports
    sessions = 0
    with_lists = 0

    for path in sorted(
        glob.glob(
            os.path.join(
                a.repo, "logs", "games", "decoder_sessions", "*.json"
            )
        )
    ):
        doc = json.load(open(path))
        received = doc.get("received_at_utc") or ""
        if received < a.since:
            continue
        rep = doc["report"]
        dec = rep.get("decoder") or {}
        vid = rep.get("video") or {}
        if not dec:
            continue
        dur = rep.get("duration_ms") or 0
        if dur < 15_000:
            continue
        sessions += 1

        disc = rep.get("stream_discontinuities")
        idrs = rep.get("first_idr_after_discontinuity")
        slow = rep.get("slow_events_ge_50_ms") or []
        slow_elapsed = sorted(e[0] for e in slow)

        if disc is None or idrs is None:
            if vid.get("sequence_resyncs"):
                session_only.append(
                    {
                        "file": os.path.basename(path),
                        "resyncs": vid.get("sequence_resyncs"),
                        "ssrc_changes": vid.get("ssrc_changes"),
                        "max_resync_to_idr_ms": vid.get(
                            "max_resync_to_idr_ms"
                        ),
                    }
                )
            continue

        with_lists += 1

        # The two lists are appended in the same order and bounded the same
        # way, so index i of one is the discontinuity of index i of the other
        # for as long as both are within their bounds.
        for i, d in enumerate(disc):
            row = {
                "file": os.path.basename(path),
                "received": received,
                "type": d.get("type"),
                "jump_packets": d.get("jump_packets"),
                "disc_elapsed_ms": d.get("elapsed_ms"),
                "resync_to_idr_ms": None,
                "au_complete": None,
                "au_fec_recovered": None,
                "au_fec_unrecoverable_group": None,
                "first_slow_after_ms": None,
            }
            if i < len(idrs):
                e = idrs[i]
                row["resync_to_idr_ms"] = e.get("resync_to_idr_ms")
                row["au_complete"] = e.get("au_complete")
                row["au_fec_recovered"] = e.get("au_fec_recovered")
                row["au_fec_unrecoverable_group"] = e.get(
                    "au_fec_unrecoverable_group"
                )
            start = d.get("elapsed_ms")
            if start is not None:
                later = [x for x in slow_elapsed if x >= start]
                if later:
                    row["first_slow_after_ms"] = later[0] - start
            per_disc.append(row)

    idr = [
        r["resync_to_idr_ms"]
        for r in per_disc
        if r["resync_to_idr_ms"] is not None
    ]
    by_type = {}
    for t in ("sequence_resync", "ssrc_change"):
        vals = [
            r["resync_to_idr_ms"]
            for r in per_disc
            if r["type"] == t and r["resync_to_idr_ms"] is not None
        ]
        by_type[t] = describe(t, vals)
        by_type[t]["over_one_gop_250ms"] = sum(1 for v in vals if v > GOP_MS)
        by_type[t]["over_two_gop_500ms"] = sum(1 for v in vals if v > 2 * GOP_MS)

    render = [
        r["first_slow_after_ms"]
        for r in per_disc
        if r["first_slow_after_ms"] is not None
    ]

    out = {
        "selection": {
            "since": a.since,
            "sessions_ge15s": sessions,
            "sessions_with_per_discontinuity_lists": with_lists,
            "discontinuities": len(per_disc),
            "pre_c3l2b_sessions_with_resyncs": len(session_only),
        },
        "resync_to_idr_ms_all": describe("resync_to_idr_ms", idr),
        "resync_to_idr_ms_by_type": by_type,
        "over_one_gop_250ms_all": sum(1 for v in idr if v > GOP_MS),
        "au_complete_counts": {
            str(k): sum(1 for r in per_disc if r["au_complete"] is k)
            for k in (True, False, None)
        },
        "au_fec_recovered_counts": {
            str(k): sum(1 for r in per_disc if r["au_fec_recovered"] is k)
            for k in (True, False, None)
        },
        "first_slow_event_after_discontinuity_ms": describe(
            "first_slow_after_ms (proxy, lower bound)", render
        ),
        "pre_c3l2b_whole_session_max": session_only,
        "per_discontinuity": per_disc,
    }

    with open(
        os.path.join(outdir, "c5_resync_idr_result.json"), "w"
    ) as fh:
        json.dump(out, fh, indent=1, default=str)

    print(
        json.dumps(
            {
                k: out[k]
                for k in (
                    "selection",
                    "resync_to_idr_ms_all",
                    "resync_to_idr_ms_by_type",
                    "over_one_gop_250ms_all",
                    "au_complete_counts",
                    "au_fec_recovered_counts",
                    "first_slow_event_after_discontinuity_ms",
                )
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
