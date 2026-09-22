"""D-BASE-P2b analysis: drift vs side effect, plus the incidental C5 read."""
import json
import os
import sys

SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"
S = os.path.dirname(os.path.abspath(__file__))


def load(fname):
    return json.load(open(os.path.join(SESS, fname)))["report"]


def metrics(label, arm, fname):
    r = load(fname)
    a, v = r["audio"], r["video"]
    dur_min = r["duration_ms"] / 60000.0
    return {
        "label": label,
        "arm": arm,
        "report": fname,
        "duration_ms": r["duration_ms"],
        "starvation": a.get("prolonged_starvation_events"),
        "underruns": a.get("underruns"),
        "concealed": a.get("concealed_underruns"),
        "avg_queue_res_ms": round(a.get("avg_queue_residence_ms") or 0, 2),
        "max_queue_res_ms": a.get("max_queue_residence_ms"),
        "startup_wait_ms": a.get("startup_wait_ms"),
        "startup_wait_timed_out": a.get("startup_wait_timed_out"),
        "first_write_ms": a.get("first_write_elapsed_ms"),
        "video_lost_pm": round(v["lost_packets"] / dur_min, 1),
        "fps": round(v["recent_fps"], 2),
        "discontinuities": len(r["stream_discontinuities"]),
    }


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            rk[order[k]] = avg
        i = j + 1
    return rk


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((x - mb) ** 2 for x in rb) ** 0.5
    return num / (da * db) if da and db else float("nan")


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def main():
    rows = []
    for line in open(os.path.join(S, "accepted.txt")):
        p = line.split()
        if len(p) == 3 and p[2] != "NONE_ACCEPTED":
            rows.append(metrics(p[0], p[1], p[2]))

    print("== accepted sessions, in run order ==")
    cols = ["label", "arm", "starvation", "underruns", "concealed",
            "avg_queue_res_ms", "max_queue_res_ms", "startup_wait_ms",
            "first_write_ms", "video_lost_pm", "fps", "discontinuities"]
    print(",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))

    if not rows:
        return

    idx = list(range(1, len(rows) + 1))
    starv = [r["starvation"] for r in rows]
    print()
    print("Spearman(starvation, run index), pooled: %.3f" % spearman(starv, idx))
    for arm in ("off", "on"):
        a = [r for r in rows if r["arm"] == arm]
        if len(a) > 2:
            print("  %s arm: n=%d starvation %s median %.1f; Spearman vs index %.3f"
                  % (arm, len(a), [r["starvation"] for r in a],
                     median([r["starvation"] for r in a]),
                     spearman([r["starvation"] for r in a],
                              list(range(1, len(a) + 1)))))

    offs = [r for r in rows if r["arm"] == "off"]
    ons = [r for r in rows if r["arm"] == "on"]
    print()
    print("== pairs (off, on) in order ==")
    wins = 0
    pairs = min(len(offs), len(ons))
    for i in range(pairs):
        d = ons[i]["starvation"] - offs[i]["starvation"]
        if d > 0:
            wins += 1
        print("  pair %d: off=%d on=%d  on-off=%+d  queue_res off=%.2f on=%.2f"
              % (i + 1, offs[i]["starvation"], ons[i]["starvation"], d,
                 offs[i]["avg_queue_res_ms"], ons[i]["avg_queue_res_ms"]))
    print("  sign test: hold-on above hold-off in %d of %d pairs" % (wins, pairs))
    for key in ("starvation", "underruns", "concealed", "avg_queue_res_ms",
                "max_queue_res_ms", "first_write_ms", "fps", "video_lost_pm"):
        print("  median %s: off=%.2f on=%.2f"
              % (key, median([r[key] for r in offs]), median([r[key] for r in ons])))


if __name__ == "__main__":
    main()
