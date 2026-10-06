#!/usr/bin/env python3
"""E3-S5 probe: a PS1 stream (E1-PS1-STREAM's launch, via tools/e1_suite.py's own functions) PLAYING, 60 s settle,
then 180 s of the companion's per-thread context switches / schedstat / syscall modes (tools/e3_probe.py threads) and
the audio sender's own counters (packets sent, duplicates) read from the companion's status before and after; then
E1's teardown. Writes probe_threads.json and probe_run.json here. Optional argv[1]: a drop-in KEY=VAL for a smoke."""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = load("e1s", "tools/e1_suite.py")
P = load("e3p", "tools/e3_probe.py")


def audio_counters():
    out = {}

    def walk(x, p=""):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, p + "." + k)
        elif isinstance(x, (int, float)) and any(s in p for s in ("packets_sent", "duplicates_sent", "underflow",
                                                                  "send_errors")):
            out[p] = x
    walk(E.games_status(), "games")
    walk(E.stream_status(), "stream")
    return out


def main():
    tag = sys.argv[2] if len(sys.argv) > 2 else "probe"
    kv = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    rec = {"tag": tag, "started_utc": E.utc(), "preflight": E.preflight()}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    before = set(os.listdir(E.SESSDIR))
    try:
        if kv:
            E.DROPIN.write_text(f"[Service]\nEnvironment={kv}\n")
            E.sh(["systemctl", "--user", "daemon-reload"], 60)
        rec["restart"] = E.restart_unit()
        E.http("POST", f"/plugins/games/launch?id={E.TEKKEN['id']}", 90)
        for _ in range(20):
            if E.games_status().get("active"):
                break
            time.sleep(1)
        rec["stream"] = E.open_stream()
        if not rec["stream"]["ok"]:
            raise RuntimeError("stream did not reach PLAYING")
        time.sleep(60)
        a, ta = audio_counters(), time.monotonic()
        rec["threads"] = P.threads(os.path.join(HERE, f"{tag}_threads.json"), 180)
        b, tb = audio_counters(), time.monotonic()
        rec["audio_counters"] = {"before": a, "after": b, "secs": round(tb - ta, 1),
                                 "per_s": {k: round((b[k] - a[k]) / (tb - ta), 2) for k in b if k in a}}
    finally:
        td = {}
        if "NativeStreamActivity" in E.top_activity():
            td["report"] = E.back_and_report(before)
            td["report_fields"] = E.report_fields(td["report"])
        td["stopped"] = E.stop_game()
        td["banner"] = E.banner_clear()
        E.teardown_flags({"dropin": [kv]} if kv else {}, td)
        td["apk"] = "CONFIRMED" if E.apk_hash() == E.EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = E.ps1_files_identical()
        td["retroarch_left"], td["encoder_left"] = len(E.retroarch_pids()), len(E.encoder_pids())
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
        json.dump(rec, open(os.path.join(HERE, f"{tag}_run.json"), "w"), indent=1, default=str)
    rr = [t for t in rec["threads"]["threads"] if t["policy"] == 2]
    print(json.dumps({"sender": rr, "audio_per_s": rec["audio_counters"]["per_s"], "teardown": {k: v for k, v in td.items() if k != "report_fields"}}, indent=1))


if __name__ == "__main__":
    main()
