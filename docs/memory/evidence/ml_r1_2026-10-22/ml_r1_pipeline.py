#!/usr/bin/env python3
"""ML-R1 -- the hitch early-warning detector, run as pre-registered (ml_r1_preregistration.txt; refuses to run unless the
file matches its .sha256). Stages, each writing the status line (~/privyhub_ml_r1/status.txt) and honouring STOP and the
cap (CAP_UTC in the pre-registration):
  1 copy      every source copy of the six logs + the client reports -> inputs/ (gzip, masked), inputs/manifest.json
  2 merge     inputs/ -> ~/privyhub_ml_r1/work/merged/ (identical rows de-duplicated, sorted); outside the repo
  3 inventory the client sessions, their eligibility, system, driver cell / evening, profile, flags -> inventory.md/.json
  4 labels    ux_r3_seconds.py's `evening` (exec'd unedited) over the merged copies -> hitch seconds; label_counts.md
  5 features  the per-second table (host's view, past only) -> features.npz, features_columns.txt
  6 models    5-fold grouped CV, the fits, the thresholds, the rules, every metric -> results.json/.md, importance.md,
              lead_times.md, model_logreg.json, model_hgb.json, scores_heldout.npz
  7 selftest  tools/hitch_predictor.py --selftest (pure python) -> selftest.txt
    python3 -B ml_r1_pipeline.py [--until <stage>]
"""
import gzip, hashlib, json, os, re, statistics, subprocess, sys, time, glob, math
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
REPO = HERE.parents[3]
PRE = HERE / "ml_r1_preregistration.txt"
WATCH = Path.home() / "privyhub_ml_r1"
WORK = WATCH / "work"
MERGED = WORK / "merged"
INPUTS = HERE / "inputs"
UX = EV / "ux_r3_2026-10-21" / "ux_r3_seconds.py"
UX_SHA = "e9b2b3f79286bdd320a9bf530d76c0381ca6d89ded6f1adfe3c4d3f3ba8b59b4"
LOGS = {"native_stream_heartbeat.log": "received_at_utc", "native_stream_ctrl_gaps.log": "start_utc",
        "native_stream_recovery.log": "at_utc", "native_frame_sizes.jsonl": "at_utc",
        "adaptive_bitrate_shadow.jsonl": "at_utc"}
GAP_COVER = ("2026-10-10T10:25:59", "2026-10-22T04:26:26")
EVENINGS = {"ux_r1": ("2026-10-20T04:19:00", "2026-10-20T05:23:00"), "ux_r2": ("2026-10-21T04:42:00", "2026-10-21T05:27:00")}
UX2_CLEAN = ("2026-10-21T04:42:00", "2026-10-21T05:27:00")
UX2_EXCL = [("2026-10-21T04:54:50", "2026-10-21T04:55:05"), ("2026-10-21T05:08:58", "2026-10-21T05:09:21"),
            ("2026-10-21T05:22:54", "2026-10-21T05:23:06")]
EVENTS = {"sunday_0506_burst": ("ux_r1", "2026-10-20T05:06:00", "2026-10-20T05:06:59"),
          "death_045455": ("ux_r2", "2026-10-21T04:54:55", None)}
KS = (1, 2, 3)
WINS = (2, 5, 10, 30)
EXCL_START = 15
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX = re.compile(r"\b[0-9a-fA-F]{32,}\b")
VER = re.compile(r"(Beetle PSX HW |snes9x |bsnes |RetroArch )(\d+(?:\.\d+){1,3})")
UNTIL = sys.argv[sys.argv.index("--until") + 1] if "--until" in sys.argv else None
T0 = time.time()


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def ts(v):
    v = str(v).rstrip("Z")
    return datetime.fromisoformat(v).replace(tzinfo=timezone.utc).timestamp()


def sec(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cap():
    for line in PRE.read_text().splitlines():
        if line.startswith("CAP_UTC:"):
            return ts(line.split(":", 1)[1].strip())
    return 0.0


CAP = cap()
STATE = {"stage": "-", "doing": "starting", "done": []}


def log(*a):
    WATCH.mkdir(parents=True, exist_ok=True)
    line = f"[mlr1 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(WATCH / "pipeline.log", "a") as fh:
        fh.write(line + "\n")


def status(**kw):
    STATE.update(kw)
    WATCH.mkdir(parents=True, exist_ok=True)
    tmp = WATCH / "status.tmp"
    tmp.write_text(f"{utc()} | stage {STATE['stage']} | doing: {STATE['doing']} | done: {','.join(STATE['done']) or '-'} | "
                   f"elapsed {round((time.time() - T0) / 60, 1)} min | cap {utc(CAP)} | stop: touch ~/privyhub_ml_r1/STOP\n")
    os.replace(tmp, WATCH / "status.txt")


class Stop(Exception):
    pass


def check():
    if (WATCH / "STOP").exists():
        raise Stop("the stop file")
    if time.time() >= CAP:
        raise Stop("the cap")


def mask(text):
    n = 0
    for rx, rep in ((IP, "<addr>"), (HEX, "<hex>")):
        text, k = rx.subn(rep, text)
        n += k
    text, k = VER.subn(lambda m: m.group(1) + "<version>", text)
    return text, n, k


def jl(p):
    out = []
    op = gzip.open if str(p).endswith(".gz") else open
    with op(p, "rt", errors="replace") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def wjson(p, obj):
    Path(p).write_text(json.dumps(obj, indent=1, default=str) + "\n")


# ------------------------------------------------------------------ 1 copy
def stage_copy():
    INPUTS.mkdir(exist_ok=True)
    srcs = []
    for name in LOGS:
        for p in [REPO / "logs/games" / name] + sorted((REPO / "logs/games/stream_log_archive").glob(name + ".*")):
            if p.exists():
                srcs.append(p)
        for p in sorted(EV.rglob(name + "*")):
            if "ml_r1_" in str(p) or not re.fullmatch(re.escape(name) + r"(\.\d)?", p.name):
                continue
            srcs.append(p)
    man = {"copied_at": utc(), "logs": [], "reports": []}
    for i, p in enumerate(srcs):
        check()
        raw = p.read_bytes()
        text, n, v = mask(raw.decode("utf-8", errors="replace"))
        rel = str(p.relative_to(REPO))
        dest = INPUTS / "logs" / f"{i:03d}__{re.sub(r'[^A-Za-z0-9._-]+', '_', rel)}.gz"
        dest.parent.mkdir(exist_ok=True)
        with open(dest, "wb") as fh:
            with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
                gz.write(text.encode())
        man["logs"].append({"source": rel, "log": next(k for k in LOGS if p.name.startswith(k)), "source_sha256": hashlib.sha256(raw).hexdigest(),
                            "bytes": len(raw), "rows": text.count("\n"), "masked_addr_hex": n, "masked_version": v,
                            "copy": str(dest.relative_to(HERE)), "copy_content_sha256": hashlib.sha256(text.encode()).hexdigest(),
                            "copy_sha256": sha(dest)})
    status(doing=f"copy: {len(srcs)} log files; the client reports")
    lo, hi = GAP_COVER
    reps = {}
    cands = sorted((REPO / "logs/games/decoder_sessions").glob("native_decoder_2026*.json")) + \
        sorted(p for p in EV.rglob("decoder_sessions/native_decoder_2026*.json") if "ml_r1_" not in str(p))
    for p in cands:
        if p.name in reps:
            continue
        check()
        raw = p.read_bytes()
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        r = d.get("received_at_utc", "")
        if not (lo <= r[:19] <= hi):
            continue
        text, n, v = mask(json.dumps(d, sort_keys=True))
        reps[p.name] = (text, {"source": str(p.relative_to(REPO)), "source_sha256": hashlib.sha256(raw).hexdigest(),
                               "received_at_utc": r, "masked_addr_hex": n, "masked_version": v,
                               "content_sha256": hashlib.sha256(text.encode()).hexdigest()})
    dest = INPUTS / "decoder_reports.jsonl.gz"
    with open(dest, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            for name in sorted(reps):
                gz.write((json.dumps({"file": name, "report": json.loads(reps[name][0])}, sort_keys=True) + "\n").encode())
                man["reports"].append({"file": name, **reps[name][1]})
    man["reports_copy"], man["reports_copy_sha256"] = str(dest.relative_to(HERE)), sha(dest)
    wjson(INPUTS / "manifest.json", man)
    log(f"copy: {len(man['logs'])} log files, {len(man['reports'])} reports")


# ------------------------------------------------------------------ 2 merge
def stage_merge():
    man = json.loads((INPUTS / "manifest.json").read_text())
    MERGED.mkdir(parents=True, exist_ok=True)
    (MERGED / "decoder_sessions").mkdir(exist_ok=True)
    counts = {}
    for name, key in LOGS.items():
        check()
        rows = {}
        for e in man["logs"]:
            if e["log"] != name:
                continue
            for d in jl(HERE / e["copy"]):
                if isinstance(d, dict) and d.get(key):
                    rows[json.dumps(d, sort_keys=True)] = d.get(key)
        with open(MERGED / name, "w") as fh:
            for line in sorted(rows, key=lambda x: (rows[x], x)):
                fh.write(line + "\n")
        counts[name] = len(rows)
    n = 0
    for d in jl(INPUTS / "decoder_reports.jsonl.gz"):
        (MERGED / "decoder_sessions" / d["file"]).write_text(json.dumps(d["report"]))
        n += 1
    counts["decoder_sessions"] = n
    wjson(WORK / "merged_counts.json", counts)
    log("merge:", counts)


# ------------------------------------------------------------------ 3 inventory
def driver_spans():
    """Suite runs on file: cells.jsonl rows (start/end) and summary.json windows, with the flags they name."""
    out = []
    fl = re.compile(r"PRIVYHUB_[A-Z0-9_]+=[^\"',\]\s]+")
    for p in sorted(EV.rglob("cells.jsonl")):
        if "ml_r1_" in str(p):
            continue
        for line in open(p):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("start_utc") and r.get("end_utc"):
                prof = r.get("spec") or r.get("profile")
                out.append({"src": str(p.parent.relative_to(EV)), "cell": str(r.get("cell") or r.get("n")), "from": r["start_utc"][:19],
                            "to": r["end_utc"][:19], "profile": prof, "flags": sorted(set(fl.findall(json.dumps(r))))[:12]})
    for p in sorted(EV.rglob("summary.json")):
        if "ml_r1_" in str(p):
            continue
        try:
            s = json.loads(p.read_text())
        except (ValueError, OSError):
            continue
        w = s.get("window") if isinstance(s, dict) else None
        if isinstance(w, dict) and w.get("from") and w.get("to"):
            fs = sorted(set(fl.findall(json.dumps(s))))
            prof = next((f.split("=", 1)[1] for f in fs if f.startswith("PRIVYHUB_IMPAIRMENT=")), None)
            out.append({"src": str(p.parent.relative_to(EV)), "cell": "window", "from": w["from"][:19], "to": w["to"][:19],
                        "profile": prof, "flags": fs[:12], "window": True})
    return out


def game_starts():
    """The game logs' names: local (EDT, -04:00) start time and the system; nothing else of them is read."""
    out = []
    for p in sorted((REPO / "logs/games").glob("2026*-game_*.log")):
        m = re.match(r"(\d{8})-(\d{6})-game_([a-z0-9]+)_", p.name)
        if m:
            t = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=timezone(timedelta(hours=-4))).timestamp()
            out.append((t, m.group(3)))
    return out


def sessions_from(hb):
    sessions, cur = [], []
    for h in hb:
        if cur and (h["sequence"] <= cur[-1]["sequence"] or ts(h["received_at_utc"]) - ts(cur[-1]["received_at_utc"]) > 60):
            sessions.append(cur)
            cur = []
        cur.append(h)
    if cur:
        sessions.append(cur)
    return sessions


def overl(a0, a1, b0, b1):
    return a0 < b1 and b0 < a1


def stage_inventory():
    hb = jl(MERGED / "native_stream_heartbeat.log")
    sess = sessions_from(hb)
    drv = driver_spans()
    games = game_starts()
    bench = {r["cell"]: (ts(r["start_utc"]), ts(r["end_utc"])) for r in
             (json.loads(x) for x in open(EV / "bench_r1_2026-10-22" / "cells.jsonl"))}
    clw = [(ts(d["from"]), ts(d["to"])) for d in drv if d.get("window") and d["src"].startswith(("cl_b5_", "cl_b6_", "cl_b7_"))]
    reps = {}
    for p in (MERGED / "decoder_sessions").glob("*.json"):
        d = json.loads(p.read_text())
        reps[p.name] = (ts(d["received_at_utc"]), d)
    inv = []
    g0, g1 = ts(GAP_COVER[0]), ts(GAP_COVER[1])
    for i, s in enumerate(sess):
        first, last = s[0], s[-1]
        st = ts(first["received_at_utc"]) - (first.get("elapsed_ms") or 0) / 1000
        en = ts(last["received_at_utc"])
        row = {"i": i, "start": utc(st), "end": utc(en), "seconds": round(en - st), "heartbeats": len(s)}
        row["eligible"] = bool(g0 <= st and en <= g1)
        sysv = [g for g in games if g[0] <= st + 5 and st - g[0] < 6 * 3600]
        row["system"] = max(sysv)[1] if sysv else "unknown"
        rep = [v for k, v in reps.items() if en - 5 <= v[0] <= en + 120]
        a = (rep[0][1].get("report") or {}).get("audio") if rep else None
        row["codec"] = (a.get("codec") if isinstance(a, dict) else None) or ("report" if rep else "unknown")
        d = [x for x in drv if overl(st, en, ts(x["from"]), ts(x["to"]))]
        row["driver"] = sorted({f"{x['src']}:{x['cell']}" for x in d})[:6]
        row["profile"] = sorted({x["profile"] for x in d if x.get("profile")})
        row["flags"] = sorted({f for x in d for f in x["flags"]})[:16]
        ev = [k for k, (a0, a1) in EVENINGS.items() if overl(st, en, ts(a0), ts(a1))]
        row["evening"] = ev[0] if ev else None
        row["player"] = "player" if ev else ("driver (no player)" if d else "unknown")
        cell = [c for c, (a0, a1) in bench.items() if overl(st, en, a0, a1)]
        row["bench_cell"] = cell[0] if cell else None
        if row["evening"]:
            row["set"] = "heldout_" + row["evening"]
        elif row["bench_cell"] and row["bench_cell"][:2] in ("05", "08"):
            row["set"] = "heldout_bench" + row["bench_cell"][1]
        else:
            row["set"] = "train"
        row["clean_ref"] = ("train" if (row["bench_cell"] or "").startswith("01") or any(overl(st, en, a0, a1) for a0, a1 in clw)
                            else "heldout" if (row["bench_cell"] or "").startswith("08") or row["evening"] == "ux_r2" else None)
        inv.append(row)
    nogap = []
    for p in sorted(EV.rglob("native_stream_heartbeat.log*")):
        if "ml_r1_" in str(p):
            continue
        if not list(p.parent.glob("native_stream_ctrl_gaps.log*")):
            rows = jl(p)
            if rows:
                a, b = rows[0]["received_at_utc"], rows[-1]["received_at_utc"]
                if b[:19] < GAP_COVER[0] or a[:19] > GAP_COVER[1]:
                    nogap.append({"copy": str(p.relative_to(REPO)), "from": a, "to": b, "reason": "outside the control-gap log's coverage"})
    out = {"sessions": inv, "excluded_copies_without_gap_log": nogap, "gap_cover": GAP_COVER,
           "driver_spans": len(drv), "game_logs": len(games)}
    wjson(HERE / "inventory.json", out)
    el = [r for r in inv if r["eligible"]]
    L = ["# ML-R1 inventory", "", f"Client sessions in the merged heartbeat copies: {len(inv)}; eligible (inside the control-gap "
         f"log's coverage {GAP_COVER[0]}Z..{GAP_COVER[1]}Z): {len(el)}; seconds {sum(r['seconds'] for r in el)}.", "",
         "| set | sessions | seconds |", "| --- | ---: | ---: |"]
    for sname in sorted({r["set"] for r in el}):
        rr = [r for r in el if r["set"] == sname]
        L.append(f"| {sname} | {len(rr)} | {sum(r['seconds'] for r in rr)} |")
    L += ["", "| # | start (UTC) | s | system | codec | player | evening / bench | driver | profile | set | clean ref | eligible |",
          "| ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in inv:
        L.append(f"| {r['i']} | {r['start'][:19]} | {r['seconds']} | {r['system']} | {r['codec']} | {r['player']} | "
                 f"{r['evening'] or r['bench_cell'] or ''} | {'; '.join(r['driver'][:2])} | {'; '.join(r['profile'])} | {r['set']} | "
                 f"{r['clean_ref'] or ''} | {r['eligible']} |")
    L += ["", "Excluded heartbeat copies (no control-gap log, outside its coverage):"] + \
         [f"- `{x['copy']}` {x['from'][:19]}..{x['to'][:19]}" for x in nogap]
    (HERE / "inventory.md").write_text("\n".join(L) + "\n")
    log(f"inventory: {len(inv)} sessions, {len(el)} eligible; excluded copies {len(nogap)}")


# ------------------------------------------------------------------ 4 labels
def stage_labels():
    assert sha(UX) == UX_SHA, "ux_r3_seconds.py changed"
    src = UX.read_text()
    ns = {"__file__": str(UX)}
    exec(compile(src[:src.index("out, L = {}, []")], str(UX), "exec"), ns)
    rows, gaps, cover, play_s = ns["evening"]({"dir": str(MERGED), "start": GAP_COVER[0][:16], "end": "2026-10-22T05:00"})
    hit = {k: r["crit"] for k, r in rows.items() if r.get("score")}
    ctx = {k: r.get("out_gap_report") for k, r in rows.items() if r.get("out_gap_report")}
    wjson(WORK / "hitch_seconds.json", {"hitch": hit, "report_out_gap": ctx, "report_coverage": cover})
    log(f"labels: {len(hit)} hitch seconds over the coverage")


# ------------------------------------------------------------------ 5 features
def stage_features():
    import numpy as np
    inv = json.loads((HERE / "inventory.json").read_text())["sessions"]
    lab = json.loads((WORK / "hitch_seconds.json").read_text())
    hit, repg = lab["hitch"], lab["report_out_gap"]
    hb_all = jl(MERGED / "native_stream_heartbeat.log")
    sess = sessions_from(hb_all)
    gaps = sorted((ts(g["start_utc"]), ts(g["end_utc"])) for g in jl(MERGED / "native_stream_ctrl_gaps.log"))
    gs = np.array([g[0] for g in gaps])
    frames = {}
    for f in jl(MERGED / "native_frame_sizes.jsonl"):
        frames[f["at_utc"][:19]] = f
    lad = sorted(((ts(a["at_utc"]), a) for a in jl(MERGED / "adaptive_bitrate_shadow.jsonl") if a.get("event") == "sample"), key=lambda x: x[0])
    lt = np.array([x[0] for x in lad])
    states = sorted({str(a.get("state")) for _, a in lad})
    base = ["hb_arrivals", "hb_fps", "hb_post_fec", "hb_fec_rec", "hb_unrec", "hb_underruns", "hb_concealed", "hb_prolonged",
            "hb_a_gap_max", "hb_out_age", "hb_age", "ctrl_age_end", "ctrl_max_in_sec", "ctrl_new_gaps",
            "tx_frames", "tx_packets", "tx_kbytes", "tx_max_pk", "tx_ge40",
            "lad_fps", "lad_q", "lad_gap", "lad_loss", "lad_level", "lad_age"] + [f"lad_state_{s}" for s in states]
    SUMS = ["hb_arrivals", "hb_post_fec", "hb_fec_rec", "hb_unrec", "hb_underruns", "hb_concealed", "hb_prolonged", "ctrl_new_gaps",
            "tx_frames", "tx_ge40", "lad_loss"]
    MAXS = ["ctrl_max_in_sec", "ctrl_age_end", "hb_a_gap_max", "hb_out_age", "hb_age", "lad_gap", "lad_q", "tx_max_pk", "tx_kbytes", "lad_age"]
    MINS = ["hb_fps", "lad_fps", "tx_frames"]
    roll = [f"{c}_sum{w}" for w in WINS for c in SUMS] + [f"{c}_max{w}" for w in WINS for c in MAXS] + [f"{c}_min{w}" for w in WINS for c in MINS]
    extra = ["secs_since_start", "sys_snes", "sys_ps1", "sys_other", "has_hb10", "has_frames", "has_lad10"]
    inputs = base + roll + extra
    context = ["ctx_report_out_gap", "ctx_shim_profiled", "ctx_session", "ctx_t"]
    labels = [f"hitch_next_{k}" for k in KS] + ["hitch_now"]
    blocks, meta = [], []
    elig = {r["i"]: r for r in inv if r["eligible"]}
    for i, s in enumerate(sess):
        if i % 50 == 0:
            check()
            status(doing=f"features: session {i}/{len(sess)}")
        r = elig.get(i)
        if not r:
            continue
        st, en = ts(r["start"]), ts(r["end"])
        t0, t1 = int(math.floor(st)), int(math.floor(en))
        n = t1 - t0 + 1
        if n <= EXCL_START + 3:
            continue
        B = {c: np.full(n, np.nan) for c in base}
        for c in ("hb_arrivals", "hb_post_fec", "hb_fec_rec", "hb_unrec", "hb_underruns", "hb_concealed", "hb_prolonged", "ctrl_new_gaps", "lad_loss") + tuple(f"lad_state_{x}" for x in states):
            B[c][:] = 0
        lastv = {}
        for a, b in zip(s, s[1:]):
            j = int(math.floor(ts(b["received_at_utc"]))) - t0
            if not (0 <= j < n):
                continue
            dt = (b["elapsed_ms"] - a["elapsed_ms"]) / 1000
            B["hb_arrivals"][j] += 1
            for c, kk in (("hb_post_fec", "lost_packets"), ("hb_fec_rec", "fec_recovered_packets"), ("hb_unrec", "fec_unrecoverable_groups"),
                          ("hb_underruns", "audio_underruns"), ("hb_concealed", "audio_concealed_underruns"),
                          ("hb_prolonged", "audio_prolonged_starvation_events")):
                B[c][j] += max(0, (b.get(kk) or 0) - (a.get(kk) or 0))
            lastv[j] = ((b["rendered_frames"] - a["rendered_frames"]) / dt if dt > 0 else np.nan,
                        b.get("audio_max_arrival_gap_ms"), b.get("last_output_age_ms"), ts(b["received_at_utc"]))
        cur = None
        for j in range(n):
            if j in lastv:
                cur = lastv[j]
            if cur is not None:
                B["hb_fps"][j], B["hb_a_gap_max"][j], B["hb_out_age"][j] = cur[0], cur[1] if cur[1] is not None else np.nan, cur[2] if cur[2] is not None else np.nan
                B["hb_age"][j] = (t0 + j + 1) - cur[3]
        # control gaps: as known at the end of each second
        B["ctrl_age_end"][:] = 0
        B["ctrl_max_in_sec"][:] = 0
        lo_i = int(np.searchsorted(gs, t0 - 120))
        for gi in range(lo_i, len(gaps)):
            g0, g1 = gaps[gi]
            if g0 > t1 + 1:
                break
            if g1 < t0:
                continue
            for j in range(max(0, int(math.floor(g0)) - t0), min(n, int(math.floor(g1)) - t0 + 1)):
                te = t0 + j + 1
                seen = min(g1, te) - g0
                if seen >= 0.25:
                    B["ctrl_max_in_sec"][j] = max(B["ctrl_max_in_sec"][j], seen)
                    if g1 > te:
                        B["ctrl_age_end"][j] = max(B["ctrl_age_end"][j], seen)
            kt = g0 + 0.25
            jk = int(math.floor(kt)) - t0
            if 0 <= jk < n and g1 - g0 >= 0.25:
                B["ctrl_new_gaps"][jk] += 1
        for j in range(n):
            f = frames.get(sec(t0 + j))
            if f:
                B["tx_frames"][j], B["tx_packets"][j] = f.get("frames"), f.get("packets")
                B["tx_kbytes"][j] = (f.get("payload_bytes") or 0) / 1000
                B["tx_max_pk"][j], B["tx_ge40"][j] = f.get("max_packets"), f.get("frames_ge_40")
        a_i, b_i = int(np.searchsorted(lt, t0 - 30)), int(np.searchsorted(lt, t1 + 1))
        last = None
        k_ = a_i
        for j in range(n):
            te = t0 + j + 1
            while k_ < b_i and lt[k_] < te:
                tt, a = lad[k_]
                jj = int(math.floor(tt)) - t0
                if 0 <= jj < n:
                    B["lad_loss"][jj] += a.get("lost_packets_delta") or 0
                last = (tt, a)
                k_ += 1
            if last is not None and te - last[0] < 120:
                a = last[1]
                for c, kk in (("lad_fps", "fps"), ("lad_q", "queue_depth"), ("lad_gap", "output_gap_ms"), ("lad_level", "level_kbps")):
                    v = a.get(kk)
                    B[c][j] = v if isinstance(v, (int, float)) else np.nan
                B["lad_age"][j] = te - last[0]
                B[f"lad_state_{a.get('state')}"][j] = 1
        X = np.zeros((n, len(inputs)), dtype=np.float32)
        col = {c: i_ for i_, c in enumerate(inputs)}
        for c in base:
            X[:, col[c]] = B[c]
        for w in WINS:
            for c in SUMS:
                v = np.nan_to_num(B[c])
                cs = np.concatenate([[0], np.cumsum(v)])
                idx = np.arange(n)
                X[:, col[f"{c}_sum{w}"]] = cs[idx + 1] - cs[np.maximum(0, idx + 1 - w)]
            for c, fn, nm in [(c, np.fmax, "max") for c in MAXS] + [(c, np.fmin, "min") for c in MINS]:
                v = B[c].copy()
                acc = v.copy()
                for sh in range(1, w):
                    sv = np.full(n, np.nan)
                    sv[sh:] = v[:-sh]
                    acc = fn(acc, sv)
                X[:, col[f"{c}_{nm}{w}"]] = acc
        X[:, col["secs_since_start"]] = np.arange(n) + (t0 - st)
        X[:, col["sys_snes"]] = r["system"] == "snes"
        X[:, col["sys_ps1"]] = r["system"] == "ps1"
        X[:, col["sys_other"]] = r["system"] not in ("snes", "ps1")
        X[:, col["has_hb10"]] = X[:, col["hb_arrivals_sum10"]] > 0
        X[:, col["has_frames"]] = ~np.isnan(B["tx_frames"])
        X[:, col["has_lad10"]] = ~np.isnan(B["lad_age"]) & (np.nan_to_num(B["lad_age"], nan=999) <= 10)
        hnow = np.array([1.0 if sec(t0 + j) in hit else 0.0 for j in range(n)])
        Y = np.full((n, len(labels)), np.nan, dtype=np.float32)
        for ki, k in enumerate(KS):
            for j in range(n - k):
                Y[j, ki] = 1.0 if hnow[j + 1:j + 1 + k].any() else 0.0
        Y[:, -1] = hnow
        C = np.zeros((n, len(context)), dtype=np.float64)
        C[:, 0] = [repg.get(sec(t0 + j)) or 0 for j in range(n)]
        C[:, 1] = 1.0 if r["profile"] else 0.0
        C[:, 2] = r["i"]
        C[:, 3] = t0 + np.arange(n)
        keep = (np.arange(n) + t0) >= st + EXCL_START
        blocks.append((X[keep], Y[keep], C[keep]))
        meta.append({"session": r["i"], "rows": int(keep.sum()), "set": r["set"], "clean_ref": r["clean_ref"]})
    X = np.concatenate([b[0] for b in blocks])
    Y = np.concatenate([b[1] for b in blocks])
    C = np.concatenate([b[2] for b in blocks])
    sets = sorted({m["set"] for m in meta})
    S = np.concatenate([[sets.index(m["set"])] * m["rows"] for m in meta]).astype(np.int8)
    # the clean references (row spans, as the pre-registration names them)
    t = C[:, 3]
    clw = [(ts(d["from"]), ts(d["to"])) for d in driver_spans() if d.get("window") and d["src"].startswith(("cl_b5_", "cl_b6_", "cl_b7_"))]
    ends = {r["i"]: ts(r["end"]) for r in inv}
    in_clw = np.zeros(len(t), bool)
    for a0, a1 in clw:
        in_clw |= (t >= a0) & (t < a1)
    ux2 = (t >= ts(UX2_CLEAN[0])) & (t < ts(UX2_CLEAN[1]))
    for a0, a1 in UX2_EXCL:
        ux2 &= ~((t >= ts(a0)) & (t < ts(a1)))
    ux2 &= np.array([ends[int(s_)] - tt >= 10 for s_, tt in zip(C[:, 2], t)])
    sidx = {v: k for k, v in enumerate(sets)}
    bench1 = [r["i"] for r in inv if (r.get("bench_cell") or "").startswith("01")]
    bench8 = [r["i"] for r in inv if (r.get("bench_cell") or "").startswith("08")]
    CR2 = np.zeros(len(t), np.int8)
    CR2[(np.isin(C[:, 2], bench1) | in_clw) & (S == sidx["train"])] = 1
    CR2[np.isin(C[:, 2], bench8) | (ux2 & (S == sidx.get("heldout_ux_r2", -9)))] = 2
    np.savez_compressed(HERE / "features.npz", X=X, Y=Y, C=C, S=S, CR=CR2)
    (HERE / "features_columns.txt").write_text(
        "# inputs (the model's columns, in order)\n" + "\n".join(inputs) + "\n# labels\n" + "\n".join(labels) +
        "\n# context (excluded from the inputs)\n" + "\n".join(context) + f"\n# S (set index): {json.dumps(sets)}\n"
        "# CR (clean reference): 0 none, 1 training side, 2 held-out side\n")
    wjson(WORK / "features_meta.json", {"sets": sets, "meta": meta, "inputs": inputs, "labels": labels, "context": context})
    # label counts
    L = ["# ML-R1 label counts (rows = seconds after each session's first 15 s)", "",
         "| set | sessions | rows | hitch seconds | rate | pos k=1 | pos k=2 | pos k=3 |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for si, sname in enumerate(sets):
        m_ = S == si
        L.append(f"| {sname} | {sum(1 for m in meta if m['set'] == sname)} | {int(m_.sum())} | {int(Y[m_, -1].sum())} | "
                 f"{Y[m_, -1].mean():.4f} | " + " | ".join(f"{np.nanmean(Y[m_, ki]):.4f}" for ki in range(3)) + " |")
    L.append(f"| clean refs, training side | | {int((CR2 == 1).sum())} | {int(Y[CR2 == 1, -1].sum())} | | | | |")
    L.append(f"| clean refs, held-out side | | {int((CR2 == 2).sum())} | {int(Y[CR2 == 2, -1].sum())} | | | | |")
    L += ["", "Per session: `inventory.json` (seconds) and `label_counts_sessions.json`."]
    per = []
    off = 0
    for m in meta:
        yy = Y[off:off + m["rows"]]
        per.append({**m, "hitch_seconds": int(yy[:, -1].sum()), "pos_rate": [None if np.isnan(np.nanmean(yy[:, ki])) else round(float(np.nanmean(yy[:, ki])), 4) for ki in range(3)]})
        off += m["rows"]
    wjson(HERE / "label_counts_sessions.json", per)
    (HERE / "label_counts.md").write_text("\n".join(L) + "\n")
    log(f"features: {X.shape[0]} rows x {X.shape[1]} inputs; sets {sets}")


# ------------------------------------------------------------------ 6 models
def episodes(alarm, t, sess):
    """Runs of consecutive alarm seconds within a session -> list of (start_idx, end_idx)."""
    import numpy as np
    out = []
    i, n = 0, len(alarm)
    while i < n:
        if alarm[i]:
            j = i
            while j + 1 < n and alarm[j + 1] and sess[j + 1] == sess[i] and t[j + 1] == t[j] + 1:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def fa_rate(alarm, y, t, sess):
    import numpy as np
    eps = episodes(alarm, t, sess)
    false = sum(1 for a, b in eps if not np.nansum(y[a:b + 1]) > 0)
    return false / (len(alarm) / 600.0) if len(alarm) else float("nan"), false, len(eps)


def recall(alarm, hnow, t, sess, k):
    """Hitch-second recall and onset recall: h caught if some row in [h-k, h-1] of the same session alarms."""
    import numpy as np
    pos = {(int(s), int(tt)): i for i, (s, tt) in enumerate(zip(sess, t))}
    caught = tot = oc = ot = 0
    leads = []
    for i in np.nonzero(hnow > 0)[0]:
        s, h = int(sess[i]), int(t[i])
        if (s, h - 1) not in pos:
            continue
        tot += 1
        onset = hnow[pos[(s, h - 1)]] == 0
        ot += onset
        hits = [h - d for d in range(1, k + 1) if (s, h - d) in pos and alarm[pos[(s, h - d)]]]
        if hits:
            caught += 1
            if onset:
                oc += 1
                j = pos[(s, max(hits))]
                while (s, int(t[j]) - 1) in pos and alarm[pos[(s, int(t[j]) - 1)]]:
                    j = pos[(s, int(t[j]) - 1)]
                leads.append(h - int(t[j]))
    return (caught / tot if tot else float("nan")), tot, (oc / ot if ot else float("nan")), ot, leads


def lead_hist(leads):
    bins = [("1", 1, 1), ("2", 2, 2), ("3", 3, 3), ("4-5", 4, 5), ("6-10", 6, 10), ("11-30", 11, 30), (">30", 31, 10 ** 9)]
    return {b: sum(1 for x in leads if lo <= x <= hi) for b, lo, hi in bins}


def stage_models():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import average_precision_score
    from sklearn.inspection import permutation_importance
    D = np.load(HERE / "features.npz")
    X, Y, C, S, CR = D["X"], D["Y"], D["C"], D["S"], D["CR"]
    fm = json.loads((WORK / "features_meta.json").read_text())
    sets, inputs = fm["sets"], fm["inputs"]
    sid = {s: i for i, s in enumerate(sets)}
    sess, t = C[:, 2].astype(int), C[:, 3].astype(int)
    tr = S == sid["train"]
    col = {c: i for i, c in enumerate(inputs)}
    res = {"inputs": len(inputs), "rows": int(len(X)), "train_rows": int(tr.sum()), "sets": sets, "k": {}}
    Xz = np.nan_to_num(X)
    mu, sd = Xz[tr].mean(0), Xz[tr].std(0)
    sd[sd == 0] = 1
    Xs = ((Xz - mu) / sd).astype(np.float32)
    gkf = GroupKFold(n_splits=5)
    rules = {"lan_r1_T4_K2": ((X[:, col["hb_unrec_sum10"]] >= 4) & (np.r_[np.zeros(10), X[:-10, col["hb_unrec_sum10"]]] >= 4)),
             "silence_250": X[:, col["ctrl_max_in_sec"]] >= 0.25, "silence_950": X[:, col["ctrl_max_in_sec"]] >= 0.95}
    # the 10-s shift above must not cross sessions: recompute per row from the same session
    sh = np.full(len(X), np.nan)
    pos = {(int(s), int(tt)): i for i, (s, tt) in enumerate(zip(sess, t))}
    for i in range(len(X)):
        j = pos.get((int(sess[i]), int(t[i]) - 10))
        if j is not None:
            sh[i] = X[j, col["hb_unrec_sum10"]]
    rules["lan_r1_T4_K2"] = (X[:, col["hb_unrec_sum10"]] >= 4) & (np.nan_to_num(sh) >= 4)
    scores_out = {}
    models_out = {}
    detector = None
    for ki, k in enumerate(KS):
        check()
        status(doing=f"models: k={k} cross-validation")
        y = Y[:, ki]
        lab = ~np.isnan(y)
        trl = tr & lab
        Xt, yt, gt = Xs[trl], y[trl], sess[trl]
        folds = list(gkf.split(Xt, yt, gt))
        cv = {"logreg": {}, "hgb": {}}
        for Cc in (0.01, 0.1, 1, 10):
            ap = []
            for a, b in folds:
                m = LogisticRegression(C=Cc, max_iter=2000).fit(Xt[a], yt[a])
                ap.append(average_precision_score(yt[b], m.predict_proba(Xt[b])[:, 1]))
            cv["logreg"][str(Cc)] = round(float(np.mean(ap)), 5)
            log(f"k={k} logreg C={Cc} cv AUPRC {np.mean(ap):.4f}")
            check()
        Xr = X[trl]
        a0, b0 = folds[0]
        for depth in (2, 4):
            for lr in (0.05, 0.1):
                m = HistGradientBoostingClassifier(max_depth=depth, learning_rate=lr, max_iter=300, early_stopping=False,
                                                   random_state=0).fit(Xr[a0], yt[a0])
                st = [average_precision_score(yt[b0], p[:, 1]) for p in m.staged_predict_proba(Xr[b0])]
                rounds = int(np.argmax(st)) + 1
                ap = []
                for a, b in folds:
                    mm = HistGradientBoostingClassifier(max_depth=depth, learning_rate=lr, max_iter=rounds, early_stopping=False,
                                                        random_state=0).fit(Xr[a], yt[a])
                    ap.append(average_precision_score(yt[b], mm.predict_proba(Xr[b])[:, 1]))
                cv["hgb"][f"d{depth}_lr{lr}"] = {"rounds": rounds, "cv_auprc": round(float(np.mean(ap)), 5)}
                log(f"k={k} hgb depth={depth} lr={lr} rounds={rounds} cv AUPRC {np.mean(ap):.4f}")
                check()
        bestC = max(cv["logreg"], key=lambda c: cv["logreg"][c])
        bestH = max(cv["hgb"], key=lambda c: cv["hgb"][c]["cv_auprc"])
        hp = cv["hgb"][bestH]
        depth, lr = int(bestH.split("_")[0][1:]), float(bestH.split("_lr")[1])
        # out-of-fold scores on training (for the threshold), with the chosen hyperparameters
        oof = {"logreg": np.full(len(X), np.nan), "hgb": np.full(len(X), np.nan)}
        idx = np.nonzero(tr)[0]
        gall = sess[tr]
        for a, b in GroupKFold(n_splits=5).split(idx, groups=gall):
            ia, ib = idx[a], idx[b]
            la = ia[lab[ia]]
            m = LogisticRegression(C=float(bestC), max_iter=2000).fit(Xs[la], y[la])
            oof["logreg"][ib] = m.predict_proba(Xs[ib])[:, 1]
            mm = HistGradientBoostingClassifier(max_depth=depth, learning_rate=lr, max_iter=hp["rounds"], early_stopping=False,
                                                random_state=0).fit(X[la], y[la])
            oof["hgb"][ib] = mm.predict_proba(X[ib])[:, 1]
        check()
        status(doing=f"models: k={k} final fits")
        lrm = LogisticRegression(C=float(bestC), max_iter=2000).fit(Xs[trl], y[trl])
        hgm = HistGradientBoostingClassifier(max_depth=depth, learning_rate=lr, max_iter=hp["rounds"], early_stopping=False,
                                             random_state=0).fit(X[trl], y[trl])
        score = {"logreg": lrm.predict_proba(Xs)[:, 1], "hgb": hgm.predict_proba(X)[:, 1]}
        for mname in score:
            score[mname] = np.where(tr, oof[mname], score[mname])     # training rows: out-of-fold scores
        # thresholds on the training clean references (out-of-fold)
        thr = {}
        crt = (CR == 1) & tr
        order = np.lexsort((t[crt], sess[crt]))
        for mname in score:
            sc = score[mname][crt][order]
            yy, tt_, ss = y[crt][order], t[crt][order], sess[crt][order]
            cands = np.unique(np.quantile(sc, np.linspace(0.0, 1.0, 1001)))
            ok = [float(th) for th in cands if fa_rate(sc >= th, yy, tt_, ss)[0] <= 1.0]
            best = min(ok) if ok else None
            thr[mname] = best if best is not None else float(sc.max()) + 1e-9
        out = {"cv": cv, "chosen": {"logreg_C": bestC, "hgb": bestH, "hgb_rounds": hp["rounds"]}, "threshold": thr, "sets": {}}
        alarms = {m: score[m] >= thr[m] for m in score}
        alarms.update({r_: rules[r_] for r_ in rules})
        hnow = Y[:, -1]
        groups = {"train_oof": tr, "heldout_evenings": (S == sid.get("heldout_ux_r1", -9)) | (S == sid.get("heldout_ux_r2", -9)),
                  **{s: S == sid[s] for s in sets if s != "train"}}
        for gname, gm in groups.items():
            o = {}
            g_order = np.nonzero(gm)[0]
            g_order = g_order[np.lexsort((t[g_order], sess[g_order]))]
            for aname, al in alarms.items():
                e = {}
                lm = g_order[lab[g_order]]
                if aname in score:
                    yy = y[lm]
                    e["auprc"] = float(average_precision_score(yy, score[aname][lm])) if yy.sum() > 0 else None
                else:
                    yy = y[lm]
                    e["auprc"] = float(average_precision_score(yy, al[lm].astype(float))) if yy.sum() > 0 else None
                rc, tot, orc, ot, leads = recall(al[g_order], hnow[g_order], t[g_order], sess[g_order], k)
                e.update({"recall": rc, "hitch_seconds": tot, "onset_recall": orc, "onsets": ot, "lead_hist": lead_hist(leads),
                          "lead_median": statistics.median(leads) if leads else None,
                          "alarm_seconds_per_10min": float(al[g_order].sum() / (len(g_order) / 600)) if len(g_order) else None})
                for side, code in (("train_clean", 1), ("heldout_clean", 2)):
                    cm = g_order[CR[g_order] == code]
                    if len(cm):
                        fr, nf, ne = fa_rate(al[cm], y[cm], t[cm], sess[cm])
                        e[f"fa_per_10min_{side}"] = round(fr, 3)
                        e[f"false_alarms_{side}"] = nf
                        e[f"clean_minutes_{side}"] = round(len(cm) / 60, 1)
                o[aname] = e
            out["sets"][gname] = o
        # the named moments
        mom = {}
        for ename, (ev, a, b) in EVENTS.items():
            gm = S == sid.get("heldout_" + ev, -9)
            if b is None:
                E = int(ts(a))
            else:
                hs = [int(tt) for tt, hh, g in zip(t, hnow, gm) if g and hh > 0 and ts(a) <= tt <= ts(b)]
                E = min(hs) if hs else None
            mom[ename] = {"E": sec(E) if E else None}
            if E:
                for aname, al in alarms.items():
                    w = gm & (t >= E - 10) & (t <= E - 2)
                    first = t[w & al]
                    mom[ename][aname] = {"fires_ge2s_before": bool((w & al).any()),
                                         "first_alarm_s_before": int(E - first.min()) if len(first) else None,
                                         "alarm_at": [int(E - x) for x in sorted(t[gm & al & (t >= E - 30) & (t <= E)])][-12:]}
        out["moments"] = mom
        res["k"][str(k)] = out
        scores_out[f"logreg_k{k}"], scores_out[f"hgb_k{k}"] = score["logreg"].astype(np.float64), score["hgb"].astype(np.float64)
        models_out[k] = (lrm, hgm, bestC, bestH, hp["rounds"])
        if k == 2:
            detector = "hgb" if max(v["cv_auprc"] for v in cv["hgb"].values()) > max(cv["logreg"].values()) else "logreg"
            res["detector"] = detector
            # importance (k = 2)
            status(doing="models: importance")
            coef = sorted(zip(inputs, lrm.coef_[0]), key=lambda x: -abs(x[1]))
            gain = np.zeros(len(inputs))
            for it in hgm._predictors:
                for tr_ in it:
                    nd = tr_.nodes
                    for row in nd[~nd["is_leaf"].astype(bool)]:
                        gain[row["feature_idx"]] += row["gain"]
            a, b = folds[0]
            sub = np.random.RandomState(0).choice(b, size=min(len(b), 40000), replace=False)
            pm = HistGradientBoostingClassifier(max_depth=depth, learning_rate=lr, max_iter=hp["rounds"], early_stopping=False,
                                                random_state=0).fit(Xr[a], yt[a])
            pi = permutation_importance(pm, Xr[sub], yt[sub], scoring="average_precision", n_repeats=3, random_state=0, n_jobs=1)
            res["importance_k2"] = {"logreg_coef": [(c, float(v)) for c, v in coef[:30]],
                                    "hgb_gain": sorted([(inputs[i], float(gain[i])) for i in range(len(inputs)) if gain[i] > 0], key=lambda x: -x[1])[:30],
                                    "hgb_permutation": sorted([(inputs[i], float(pi.importances_mean[i])) for i in range(len(inputs))], key=lambda x: -x[1])[:30]}
        log(f"k={k}: thresholds {thr}; heldout_evenings recall " + json.dumps({a: out['sets']['heldout_evenings'][a]['recall'] for a in alarms}))
    # the bar (k = 2)
    o2 = res["k"]["2"]["sets"]["heldout_evenings"]
    det = res["detector"]
    best_rule = max(rules, key=lambda r_: o2[r_]["recall"] if o2[r_]["recall"] == o2[r_]["recall"] else -1)
    mom = res["k"]["2"]["moments"]
    res["bar"] = {"detector": det, "detector_recall": o2[det]["recall"], "best_rule": best_rule, "best_rule_recall": o2[best_rule]["recall"],
                  "margin_points": round(100 * (o2[det]["recall"] - o2[best_rule]["recall"]), 1),
                  "fa_train_clean": res["k"]["2"]["sets"]["train_oof"][det].get("fa_per_10min_train_clean"),
                  "fires_before_sunday_0506": mom["sunday_0506_burst"].get(det, {}).get("fires_ge2s_before"),
                  "fires_before_death": mom["death_045455"].get(det, {}).get("fires_ge2s_before")}
    res["bar"]["met"] = bool(res["bar"]["margin_points"] >= 20 and res["bar"]["fires_before_sunday_0506"] and res["bar"]["fires_before_death"])
    wjson(HERE / "results.json", res)
    np.savez_compressed(HERE / "scores_heldout.npz", **{k_: v for k_, v in scores_out.items()},
                        heldout=(S != sid["train"]))
    # the models as plain numbers
    mlr = {"inputs": inputs, "standardize": {"mean": [float(v) for v in mu], "scale": [float(v) for v in sd]}, "nan_to": 0.0, "k": {}}
    mhg = {"inputs": inputs, "k": {}}
    for k, (lrm, hgm, bestC, bestH, rounds) in models_out.items():
        mlr["k"][str(k)] = {"C": bestC, "intercept": float(lrm.intercept_[0]), "coef": [float(v) for v in lrm.coef_[0]],
                            "threshold": res["k"][str(k)]["threshold"]["logreg"]}
        trees = []
        for it in hgm._predictors:
            nd = it[0].nodes
            trees.append([{"v": float(r["value"]), "f": int(r["feature_idx"]), "thr": float(r["num_threshold"]), "ml": bool(r["missing_go_to_left"]),
                           "l": int(r["left"]), "r": int(r["right"]), "leaf": bool(r["is_leaf"])} for r in nd])
        mhg["k"][str(k)] = {"params": bestH, "rounds": rounds, "baseline": float(np.ravel(hgm._baseline_prediction)[0]), "trees": trees,
                            "threshold": res["k"][str(k)]["threshold"]["hgb"]}
    wjson(HERE / "model_logreg.json", mlr)
    (HERE / "model_hgb.json").write_text(json.dumps(mhg) + "\n")
    write_reports(res)
    log("models: done; bar", json.dumps(res["bar"]))


def pct(x):
    return "—" if x is None or x != x else f"{100 * x:.1f} %"


def write_reports(res):
    names = ["logreg", "hgb", "lan_r1_T4_K2", "silence_250", "silence_950"]
    L = ["# ML-R1 results (as pre-registered; every metric, every baseline, per set, per k)", "",
         f"Rows {res['rows']:,} ({res['train_rows']:,} training), {res['inputs']} inputs. The detector (k = 2, by CV AUPRC): **{res['detector']}**.", "",
         "## The bar (k = 2, held-out evenings pooled)", "", "```", json.dumps(res["bar"], indent=1), "```"]
    for k in map(str, KS):
        o = res["k"][k]
        L += ["", f"## k = {k}", "", f"CV: `{json.dumps(o['cv'])}`", f"Chosen: `{json.dumps(o['chosen'])}`; thresholds `{json.dumps(o['threshold'])}`", ""]
        for gname, g in o["sets"].items():
            L += [f"### {gname}", "", "| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
            for a in names:
                e = g[a]
                L.append(f"| {a} | {'—' if e['auprc'] is None else round(e['auprc'], 4)} | {pct(e['recall'])} | {e['hitch_seconds']} | "
                         f"{pct(e['onset_recall'])} | {e['onsets']} | {e['lead_median']} | {e.get('fa_per_10min_train_clean', '—')} | "
                         f"{e.get('fa_per_10min_heldout_clean', '—')} | {round(e['alarm_seconds_per_10min'], 1) if e['alarm_seconds_per_10min'] is not None else '—'} |")
            L.append("")
        L += ["### the named moments", "", "```", json.dumps(o["moments"], indent=1), "```"]
    (HERE / "results.md").write_text("\n".join(L) + "\n")
    I = ["# ML-R1 importance (k = 2)", "", "## logistic regression: standardized coefficients (top 30 by |coef|)", ""] + \
        [f"- `{c}` {v:+.4f}" for c, v in res["importance_k2"]["logreg_coef"]] + \
        ["", "## gradient-boosted trees: split gain summed per feature (top 30)", ""] + \
        [f"- `{c}` {v:.1f}" for c, v in res["importance_k2"]["hgb_gain"]] + \
        ["", "## gradient-boosted trees: permutation importance, AUPRC drop, one grouped validation fold (top 30)", ""] + \
        [f"- `{c}` {v:+.5f}" for c, v in res["importance_k2"]["hgb_permutation"]]
    (HERE / "importance.md").write_text("\n".join(I) + "\n")
    T = ["# ML-R1 lead times (caught onsets: seconds from the alarm run's first second to the hitch onset)", ""]
    for k in map(str, KS):
        for gname, g in res["k"][k]["sets"].items():
            T += [f"## k = {k}, {gname}", "", "| alarm | " + " | ".join(["1", "2", "3", "4-5", "6-10", "11-30", ">30"]) + " | median |",
                  "| --- |" + " ---: |" * 8]
            for a in names:
                h = g[a]["lead_hist"]
                T.append(f"| {a} | " + " | ".join(str(h[b]) for b in ["1", "2", "3", "4-5", "6-10", "11-30", ">30"]) + f" | {g[a]['lead_median']} |")
            T.append("")
    (HERE / "lead_times.md").write_text("\n".join(T) + "\n")


# ------------------------------------------------------------------ 7 self-test
def stage_selftest():
    r = subprocess.run([sys.executable, "-B", str(REPO / "tools/hitch_predictor.py"), "--selftest", "--dir", str(HERE)],
                       capture_output=True, text=True, timeout=7200)
    (HERE / "selftest.txt").write_text(r.stdout + r.stderr)
    log("selftest:", r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])


STAGES = [("copy", stage_copy), ("merge", stage_merge), ("inventory", stage_inventory), ("labels", stage_labels),
          ("features", stage_features), ("models", stage_models), ("selftest", stage_selftest)]


def main():
    want = PRE.with_suffix(".sha256").read_text().split()[0]
    if sha(PRE) != want:
        print("refusing: the pre-registration does not match its hash")
        return 2
    log("start; cap", utc(CAP))
    why = "all stages done"
    try:
        for name, fn in STAGES:
            check()
            status(stage=name, doing=name)
            t = time.time()
            fn()
            STATE["done"].append(name)
            log(f"stage {name} done in {round(time.time() - t, 1)} s")
            status(doing=f"{name} done")
            if UNTIL == name:
                why = f"--until {name}"
                break
    except Stop as e:
        why = str(e)
        log("stopped:", why)
    status(doing=f"EXITED ({why})")
    log("exit:", why)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        status(doing=f"CRASHED: {repr(e)[:200]}")
        raise
