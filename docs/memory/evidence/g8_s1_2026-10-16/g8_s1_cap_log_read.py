#!/usr/bin/env python3
"""G8-S1 final record: the companion's journal over the four cap cells (17-20), read once and reduced to what the
record uses -- per client session (a heartbeat `sequence=1` starts one): the first and last heartbeat's counters, the
setup / start / stop lines, and every non-HTTP line. Addresses and ids are masked before anything is written.
Input: `journalctl --user -u privyhub-companion -o short-iso` over the cells' span (stdin). Output: stdout."""
import re
import sys
from urllib.parse import parse_qsl

MASK = [(re.compile(r"\d+\.\d+\.\d+\.\d+(:\d+)?"), "<addr>"), (re.compile(r"[0-9a-f]{16,}"), "<id>"),
        (re.compile(r"id=game_ps1_\S+"), "id=game_ps1_<id>"), (re.compile(r"/home/\S+?/Projects/onn-stream-test"), "<repo>")]
KEEP = ("rendered_frames", "queued_frames", "rx_packets", "lost_packets", "stream_resyncs", "fec_recovered_packets",
        "fec_unrecoverable_groups", "last_output_age_ms", "elapsed_ms", "forward_gap_events", "max_forward_gap_packets")
SKIP = re.compile(r'"GET |Endpoints:|  (GET|POST) /|root:|Catalog:|VOD |Control API|Dynamic media|Logs:|Listening on|'
                  r'Stop with|Starting the PrivyHub|PrivyHub companion service$|Project root|Media root')


def mask(s):
    for rx, rep in MASK:
        s = rx.sub(rep, s)
    return s


def main():
    sess, out = None, []

    def close():
        if sess:
            f, l = sess["first"], sess["last"]
            out.append(f"  session {sess['at']}: heartbeats {sess['n']}; first " +
                       " ".join(f"{k}={f.get(k)}" for k in KEEP) + "\n    last  " + " ".join(f"{k}={l.get(k)}" for k in KEEP))
    for line in sys.stdin:
        line = line.rstrip("\n")
        m = re.search(r"native-stream-heartbeat\?(\S+)", line)
        ts = line.split(" ", 1)[0]
        if m:
            q = dict(parse_qsl(m.group(1)))
            if q.get("sequence") == "1":
                close()
                sess = {"at": ts, "n": 0, "first": q}
            if sess is not None:
                sess["n"] += 1
                sess["last"] = q
            continue
        if SKIP.search(line):
            continue
        close() if "native-stream-stop" in line else None
        if "native-stream-stop" in line:
            sess = None
        parts = line.split(" ", 3)
        out.append(mask(f"{ts} {parts[3] if len(parts) > 3 else ''}")[:260])
    close()
    print("\n".join(out))


if __name__ == "__main__":
    main()
