#!/usr/bin/env python3
"""E3-S7B §1 -- the spacing probe. With the stream idle (no game, no session), one forced grab of one channel
(CNBCUK.uk@SD, E3-S6's / S7's) at each setting, in this order: today (no flag), PRIVYHUB_EPG_GRAB_NET=paced with
PRIVYHUB_EPG_GRAB_DELAY_MS=1000, 1500, 4000 (the E3 drop-in per setting, removed after; the adopted environ checked).
Per grab: eno1 rx/tx bytes and packets every 100 ms (/proc/net/dev) from 5 s before to 5 s after, the grabber child's
presence every 100 ms (the grab's node processes), the grab's own elapsed_seconds. Requests are counted from the byte
bursts (the grabber's stdout is not kept by the companion): a burst = 100-ms bins with rx bytes > the pre-grab
baseline's p95 + 2 kB, bins < 300 ms apart merged; counted while the child lives. -> spacing/<setting>.json,
spacing_table.md/.json"""
import importlib.util
import json
import os
import statistics
import subprocess
import threading
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("e1s", os.path.join(REPO, "tools/e1_suite.py"))
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
CH = "CNBCUK.uk@SD"
SETTINGS = [("today", []), ("1000", ["PRIVYHUB_EPG_GRAB_NET=paced", "PRIVYHUB_EPG_GRAB_DELAY_MS=1000"]),
            ("1500", ["PRIVYHUB_EPG_GRAB_NET=paced", "PRIVYHUB_EPG_GRAB_DELAY_MS=1500"]),
            ("4000", ["PRIVYHUB_EPG_GRAB_NET=paced", "PRIVYHUB_EPG_GRAB_DELAY_MS=4000"])]
OUT = os.path.join(HERE, "spacing")


def netdev():
    for l in open("/proc/net/dev"):
        if l.strip().startswith("eno1:"):
            f = l.split(":", 1)[1].split()
            return int(f[0]), int(f[1]), int(f[8]), int(f[9])
    return None


DELAY_SEEN = set()


def grab_children():
    out = subprocess.run(["pgrep", "-af", "commands/epg/grab"], capture_output=True, text=True).stdout.splitlines()
    # only the grabber's own tree (npm / sh / node), never a shell or python that merely mentions the path
    # (first pass, spacing_first_pass/: the tool shell running the probe matched, so the child looked alive throughout)
    keep = []
    for l in out:
        try:
            comm = open(f"/proc/{l.split()[0]}/comm").read().strip()
        except OSError:
            continue
        if comm in ("node", "npm", "sh", "npm run grab") or comm.startswith("npm"):
            keep.append(l)
    out = keep
    for l in out:
        DELAY_SEEN.update(t for t in l.split() if t.startswith("--delay"))
        if "--delay" not in l:
            DELAY_SEEN.add("(no --delay)")
    return len(out)


def sampler(rows, stop):
    prev = netdev()
    while not stop.is_set():
        t0 = time.time()
        time.sleep(0.1)
        cur = netdev()
        rows.append({"t": round(time.time(), 3), "rx_b": cur[0] - prev[0], "rx_p": cur[1] - prev[1],
                     "tx_b": cur[2] - prev[2], "tx_p": cur[3] - prev[3], "child": grab_children()})
        prev = cur


def bursts(rows, thr):
    out, cur = [], None
    for r in rows:
        if r["rx_b"] > thr:
            if cur and r["t"] - cur[1] < 0.3 + 1e-6:
                cur[1] = r["t"]
                cur[2] += r["rx_b"]
            else:
                if cur:
                    out.append(cur)
                cur = [r["t"] - 0.1, r["t"], r["rx_b"]]
    if cur:
        out.append(cur)
    return out


def one(name, kvs):
    rec = {"setting": name, "flags": kvs, "preflight": E.preflight()}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    w = {"dropin": kvs} if kvs else {}
    try:
        if kvs:
            E.DROPIN.write_text("[Service]\n" + "".join(f"Environment={kv}\n" for kv in kvs))
            E.sh(["systemctl", "--user", "daemon-reload"], 60)
        rec["restart"] = r = E.restart_unit()
        if not (r["mainpid_serves_8765"] and r["environ"] == sorted(E.ADOPTED + kvs) and r["manager"] == []):
            raise RuntimeError(f"unit not as expected after restart: {r}")
        time.sleep(20)
        rows, stop = [], threading.Event()
        DELAY_SEEN.clear()
        th = threading.Thread(target=sampler, args=(rows, stop), daemon=True)
        th.start()
        time.sleep(5)
        t0 = time.time()
        code, d = E.http("POST", f"/plugins/epg/refresh?channel_id={urllib.parse.quote(CH)}", 150)
        t1 = time.time()
        time.sleep(5)
        stop.set()
        th.join()
        src = (d or {}).get("source") or {}
        rec["delay_args_seen"] = sorted(DELAY_SEEN)
        DELAY_SEEN.clear()
        rec.update({"http": code, "ok": bool((d or {}).get("ok")), "cached": (d or {}).get("cached"),
                    "programmes": (d or {}).get("programme_count"), "site": src.get("site"),
                    "elapsed_seconds": src.get("elapsed_seconds"), "request_wall_s": round(t1 - t0, 3),
                    "t_post": t0, "t_done": t1})
        base = [x["rx_b"] for x in rows if x["t"] < t0]
        thr = (sorted(base)[int(0.95 * (len(base) - 1))] if base else 0) + 2048
        alive = [x["t"] for x in rows if x["child"] > 0]
        c0, c1 = (min(alive) - 0.1, max(alive)) if alive else (t0, t1)
        b = [x for x in bursts(rows, thr) if c0 - 0.1 <= x[0] <= c1 + 0.1]
        starts = [x[0] for x in b]
        ss = [round(y - x, 2) for x, y in zip(starts, starts[1:])]
        quiet = [round(y[0] - x[1], 2) for x, y in zip(b, b[1:])]
        rec.update({"baseline_rx_b_p95_plus_2k": thr, "child_wall_s": round(c1 - c0, 2) if alive else None,
                    "requests_by_bursts": len(b), "bursts": [[round(x[0] - c0, 2), round(x[1] - c0, 2), x[2]] for x in b],
                    "start_to_start_s": ss, "quiet_between_s": quiet,
                    "spacing_median_s": statistics.median(ss) if ss else None, "spacing_max_s": max(ss) if ss else None,
                    "rx_bytes_during_child": sum(x["rx_b"] for x in rows if c0 <= x["t"] <= c1),
                    "tx_bytes_during_child": sum(x["tx_b"] for x in rows if c0 <= x["t"] <= c1)})
        json.dump({"rec": rec, "rows": rows}, open(os.path.join(OUT, f"{name}.json"), "w"), indent=1)
    finally:
        td = {}
        E.teardown_flags(w, td)
        if not kvs:
            td["flags_absent"] = E.manager_flags() == [] and E.environ_flags(E.mainpid()) == E.ADOPTED
        rec["teardown"] = td
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    res = [one(n, kv) for n, kv in SETTINGS]
    md = ["| setting | ok | site | programmes | grab elapsed s (companion) | child wall s | requests (bursts) | start-to-start median / max s | quiet between s |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['setting']} | {r['ok']} | {r.get('site')} | {r.get('programmes')} | {r.get('elapsed_seconds')} | "
                  f"{r.get('child_wall_s')} | {r.get('requests_by_bursts')} | {r.get('spacing_median_s')} / {r.get('spacing_max_s')} | "
                  f"{r.get('quiet_between_s')} |")
    open(os.path.join(HERE, "spacing_table.md"), "w").write("\n".join(md) + "\n")
    json.dump(res, open(os.path.join(HERE, "spacing_table.json"), "w"), indent=1, default=str)
    print("\n".join(md))
    print(json.dumps({"final": E.preflight()}))


if __name__ == "__main__":
    main()
