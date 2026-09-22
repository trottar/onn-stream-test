import json, sys, os
SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"


def row(label, arm, fname):
    r = json.load(open(os.path.join(SESS, fname)))["report"]
    a = r["audio"]
    v = r["video"]
    dur = r["duration_ms"] / 60000.0
    disc = r["stream_discontinuities"]
    early = [d for d in disc if d["elapsed_ms"] < 30000]
    return {
        "label": label,
        "arm": arm,
        "report": fname,
        "duration_ms": r["duration_ms"],
        "starvation": a.get("prolonged_starvation_events"),
        "underruns": a.get("underruns"),
        "concealed": a.get("concealed_underruns"),
        "avg_queue_res_ms": a.get("avg_queue_residence_ms"),
        "max_queue_res_ms": a.get("max_queue_residence_ms"),
        "startup_wait_ms": a.get("startup_wait_ms"),
        "startup_wait_timed_out": a.get("startup_wait_timed_out"),
        "first_write_ms": a.get("first_write_elapsed_ms"),
        "audio_lost": a.get("lost_packets"),
        "video_lost_pm": round(v["lost_packets"] / dur, 1),
        "fps": round(v["recent_fps"], 2),
        "discontinuities": len(disc),
        "early_discontinuities": len(early),
    }


if __name__ == "__main__":
    out = []
    for line in open(sys.argv[1]):
        p = line.split()
        if len(p) == 3:
            out.append(row(p[0], p[1], p[2]))
    for d in out:
        print(json.dumps(d))
