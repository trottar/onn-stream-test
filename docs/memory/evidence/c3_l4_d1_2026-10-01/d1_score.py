#!/usr/bin/env python3
"""C3-L4-D1 B3 -- score the injection session (I) and the 30-minute hold (H) by the pre-registration
(c3_l4_d1_preregistration.txt). Read-only.

    d1_score.py [--json out.json]
"""
import collections, json, os, re, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
LIVE = "PRIVYHUB_ADAPTIVE_BITRATE_MODE=live"
ACTING = ("transition", "would_act", "refused", "hold")


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def j(p):
    return json.load(open(p)) if os.path.exists(p) else {}


def index():
    idx = {}
    for line in open(os.path.join(R, "index.txt")):
        f = line.split()
        if len(f) >= 2 and f[1] in ("B", "H"):
            ts = TS.findall(line)
            idx[f[0]] = (ts[0], ts[1])
    return idx


def client(h):
    rep = j(os.path.join(R, f"report_{h}.json")).get("report")
    if not rep:
        return None
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    s = rep["duration_ms"] / 1000.0
    m = s / 60.0
    return dict(minutes=m, spikes=d["spike_20_ms"] / m, fps=d["rendered_frames"] / s,
                stale=d["stale_output_drops"] / m, aund=(a.get("underruns") or 0) / m,
                loss=v["lost_packets"] / m, maxgap=d["max_output_gap_ms"])


def main():
    idx = index()
    night = open(os.path.join(HERE, "c3_l4_d1_night.log")).read()
    out = {}
    print("C3-L4-D1 B3 -- live from the default (the drop-in)")

    # ---- I: the injection session -------------------------------------------------------------
    if "I" in idx:
        dl = jl(os.path.join(R, "decision_log_I.jsonl"))
        ev = collections.Counter(r.get("event") for r in dl)
        inj = [r for r in dl if r.get("event") == "inject"]
        tr = [r for r in dl if r.get("event") == "transition"]
        done = [r for r in dl if r.get("event") == "transition_done"]
        ssrc = [r for r in dl if r.get("event") == "ssrc_change"]
        ac, se, st = (j(os.path.join(R, f"{k}_I.json")) for k in ("armcheck", "status_end", "status"))
        after = re.search(r"after I \(I4\): manager PRIVYHUB_\* '([^']*)'.*?environ PRIVYHUB_\* '([^']*)'", night)
        route = re.search(r"after I \(I4\): inject route HTTP (\d+)", night)
        i1 = (len(inj) == 1 and len(tr) == 1 and tr[0].get("class") == "FALLBACK" and tr[0].get("acted") is True
              and len(done) == 1 and done[0].get("from_kbps") == 7000 and done[0].get("to_kbps") == 5000
              and done[0].get("injected") is True and len(ssrc) >= 1
              and (ssrc[0].get("at_utc", "") >= done[0].get("at_utc", "")))
        i2 = ((ac.get("encoder_overrides") or {}).get("any_override") is False
              and (se.get("encoder_overrides") or {}).get("any_override") is False)
        i3 = (st.get("adaptive_bitrate") or {}).get("level") == 7000 and st.get("bitrate_kbps") == 7000 \
            and any(r.get("event") == "session_ended_reset" and (r.get("before") or {}).get("level_kbps") == 5000
                    and r.get("level_kbps") == 7000 for r in dl)
        i4 = bool(after) and after.group(1) == "" and after.group(2) == LIVE and bool(route) and route.group(1) == "403"
        rows = {"I1 one FALLBACK on the injection, acted 7000 -> 5000, transition_done, ssrc_change": i1,
                "I2 any_override false at PLAYING and at the end": i2,
                "I3 after BACK level 7000 (session_ended_reset 5000 -> 7000), stream 7000": i3,
                "I4 inject flag absent (manager none, environ exactly the drop-in's name), route 403": i4}
        print(f"\nI ({idx['I'][0]} .. {idx['I'][1]}): decision-log events {dict(ev)}")
        if done:
            print(f"  transition_done {done[0].get('from_kbps')} -> {done[0].get('to_kbps')} at {done[0].get('at_utc')}, "
                  f"actuation {done[0].get('actuation_ms')} ms; ssrc_change at {[r.get('at_utc') for r in ssrc]}")
        print(f"  status_end level {(se.get('adaptive_bitrate') or {}).get('level')} stream {se.get('bitrate_kbps')}; "
              f"after BACK level {(st.get('adaptive_bitrate') or {}).get('level')} stream {st.get('bitrate_kbps')}")
        if after:
            print(f"  after I: manager '{after.group(1)}', environ '{after.group(2)}', inject route {route.group(1) if route else '?'}")
        for k, v in rows.items():
            print(f"  {'PASS' if v else 'FAIL'}  {k}")
        verdict = "PASS" if all(rows.values()) else "NOT PASS AS PRE-REGISTERED"
        # Diagnosis, reported beside the rows; it does not change them (written after the data).
        rep = (j(os.path.join(R, "report_I.json")).get("report") or {})
        blackout = [r for r in dl if r.get("event") == "sample" and r.get("disposition") == "blackout"]
        print("  diagnosis (after the data; the rows above stand):")
        print(f"    I1: ssrc_change rows in the decision log {len(ssrc)} -- the live controller emits that row only "
              f"from note_recovery_restart (recovery restarts), never for its own transition; the client report: "
              f"ssrc_changes {rep.get('video', {}).get('ssrc_changes')}, discontinuities "
              f"{[(d.get('type'), d.get('elapsed_ms')) for d in rep.get('stream_discontinuities') or []]}; "
              f"blackout samples after transition_done {len(blackout)}")
        print(f"    I3: status after BACK read level {(st.get('adaptive_bitrate') or {}).get('level')}, transitions "
              f"{(st.get('adaptive_bitrate') or {}).get('transitions_this_session')}, state "
              f"{(st.get('adaptive_bitrate') or {}).get('state')}, but active {st.get('active')} and bitrate "
              f"{st.get('bitrate_kbps')}: the read (09:36:16 local) preceded the client's native-stream-stop "
              f"(09:36:17, companion_I.log), whose stop path resets the active bitrate to the profile's 7000; no "
              f"native-stream-status read was taken between the stop and the companion's restart")
        print(f"  => I {verdict}")
        out["I"] = {"verdict": verdict, "rows": rows, "events": dict(ev), "client": client("I")}
    else:
        print("\nI: NOT RUN")

    # ---- H: the 30-minute hold on the default -------------------------------------------------
    if "H" in idx:
        t0, t1 = idx["H"]
        dl = jl(os.path.join(R, "decision_log_H.jsonl"))
        ev = collections.Counter(r.get("event") for r in dl)
        acting = [r for r in dl if r.get("event") in ACTING or r.get("acted") is True]
        holds = [r for r in dl if r.get("event") == "state" and r.get("to") == "HOLD"]
        samples = [r for r in dl if r.get("event") == "sample"]
        c = client("H")
        ac = j(os.path.join(R, "armcheck_H.json"))
        loc = datetime.strptime(t0, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) + timedelta(hours=-4)
        crows = {"spikes/min < 200": c["spikes"] < 200, "rendered fps >= 59.5": c["fps"] >= 59.5,
                 "stale/min < 20": c["stale"] < 20, "audio underruns/min < 5": c["aund"] < 5}
        silent = not acting and not holds
        verdict = "SILENT" if silent and all(crows.values()) else "NOT SILENT"
        print(f"\nH ({t0} .. {t1}; local {loc:%Y-%m-%d %H:%M} EDT): mode {(ac.get('adaptive_bitrate') or {}).get('mode')} "
              f"configured {(ac.get('adaptive_bitrate') or {}).get('configured_mode')}, any_override "
              f"{(ac.get('encoder_overrides') or {}).get('any_override')}")
        print(f"  decision-log events {dict(ev)}; sample rows {len(samples)}; clean "
              f"{sum(1 for r in samples if r.get('clean'))}; acting rows {len(acting)}; HOLD states {len(holds)}")
        print(f"  client: {c['minutes']:.2f} min, spikes {c['spikes']:.1f}/min, fps {c['fps']:.2f}, stale "
              f"{c['stale']:.2f}/min, underruns {c['aund']:.2f}/min")
        for k, v in crows.items():
            print(f"  {'PASS' if v else 'FAIL'}  {k}")
        print(f"  controller: {'0 transitions / would_act / hold / refused' if silent else 'FIRED: ' + str([(r.get('event'), r.get('class'), r.get('reason'), r.get('at_utc')) for r in acting + holds])}")
        print(f"  reported: loss {c['loss']:.2f}/min ({'meets' if c['loss'] < 10 else 'misses'} < 10), max gap "
              f"{c['maxgap']} ms ({'meets' if c['maxgap'] <= 100 else 'misses'} <= 100); Part A was MIXED, so no "
              f"window to place it in (local hour {loc.hour})")
        print(f"  => H {verdict}")
        out["H"] = {"verdict": verdict, "client": c, "events": dict(ev), "acting": acting, "holds": holds,
                    "local": f"{loc:%Y-%m-%d %H:%M}", "client_rows": crows}
    else:
        print("\nH: NOT RUN")
    if "--json" in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
