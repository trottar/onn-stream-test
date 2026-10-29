#!/usr/bin/env python3
"""B28: G4-S4's sessions and the home LAN sessions through the start-rung and ladder readers, at the old (the four lines
explicit, as G4-S4's drop-in) and the new (`PRIVYHUB_REMOTE=1`), read-only.
Each session's class is from the record: every G4-S4 session ran over the overlay (remote, path direct where sampled);
every home session of 2026-10-27/28 (CL-B14, G-A7, CL-B15) ran on the LAN (the client's class lan in every cell record). The readers
are the companion's own (`start_rung.StartRung`, `remote_ladder.RemoteLadder`, `remote_umbrella.RemoteUmbrella`) on
addresses built from integers; nothing is spawned, nothing written but this script's outputs.
    python3 -B replay_remote_umbrella.py <repo root> <out dir>"""
import csv, ipaddress, json, sys, types
from pathlib import Path

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT / "companion"))
import remote_ladder as rl  # noqa: E402
import start_rung as sr  # noqa: E402
import remote_umbrella as ru  # noqa: E402

OVERLAY = str(rl.OVERLAY_NETWORKS[0][77])
LAN = str(ipaddress.ip_address(0xC0A80117))
BASE = (5000, 5500, 6000, 7000)
G4 = ROOT / "docs/memory/evidence/g4_s4_2026-10-24"
HOME_SINCE = "2026-10-27T00:00:00"           # the home LAN of 2026-10-27/28: CL-B14, G-A7, CL-B15


def old(target):
    """G4-S4's drop-in: the four explicit, read at import (both shared objects)."""
    ladder = rl.RemoteLadder()
    live = types.SimpleNamespace(REMOTE_LADDER=ladder, REMOTE_CAP=None)
    sys.modules["adaptive_bitrate_live"] = live
    rec = sr.StartRung("floor", log=lambda *_: None).choose(target)
    ladder.note_stream_start(target)
    return {"kbps": rec["kbps"], "source": rec["source"], "list": rec["active_list"],
            "ladder": list(ladder.ladder_for(BASE)), "path_class": ladder.path_class}


def new(target, path):
    live = types.SimpleNamespace(REMOTE_LADDER=None, REMOTE_CAP=None, START_RUNG=None)
    native = types.SimpleNamespace(START_RUNG=None)
    sys.modules["adaptive_bitrate_live"] = live
    rows = []
    u = ru.RemoteUmbrella(types.SimpleNamespace(_log=lambda e, **k: rows.append(dict(k, event=e))), {},
                          live=live, native=native, service=lambda: None, probe=lambda: types.SimpleNamespace(),
                          overlay_path=lambda: path, threaded=False)
    u.note_stream_start(target)
    if native.START_RUNG is None:            # today's call site: no rung object, the profile's 7000
        out = {"kbps": 7000, "source": "today", "list": None}
    else:
        rec = native.START_RUNG.choose(target)
        out = {"kbps": rec["kbps"], "source": rec["source"], "list": rec["active_list"]}
    if live.REMOTE_LADDER is not None:
        live.REMOTE_LADDER.note_stream_start(target)
        out["ladder"], out["path_class"] = list(live.REMOTE_LADDER.ladder_for(BASE)), live.REMOTE_LADDER.path_class
    else:
        out["ladder"], out["path_class"] = list(BASE), None
    out["remote_config_class"] = rows[-1]["class"] if rows else None
    return out


# G4-S4: the record's 13 sessions and its ladder log's start rows (the five under the four)
sessions = list(csv.DictReader(open(G4 / "sessions.tsv"), delimiter="\t"))
starts = []
for line in open(G4 / "copies/logs/games/adaptive_bitrate_shadow.jsonl"):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if "start_rung" in r:
        starts.append((r["at_utc"][:19], r["start_rung"]))
rows = []
for s in sessions:
    lines = int(s["lines"])
    actual = next((st for t, st in starts if t[:16] >= s["start"][:16] and t <= s["end"]), None) if lines == 14 else None
    path = "direct" if "direct" in s["paths"] else "unread"
    o, n = old(OVERLAY), new(OVERLAY, path)
    rows.append({"set": "G4-S4", "n": s["n"], "start": s["start"], "lines": lines, "class": "remote",
                 "actual_kbps": actual["kbps"] if actual else int(s["levels_kbps"].split("→")[0].split("…")[0]),
                 "actual_source": actual["source"] if actual else "ten lines, no start rung",
                 "old": o, "new": n,
                 "same": (o["kbps"], o["source"], o["list"], o["ladder"]) == (n["kbps"], n["source"], n["list"], n["ladder"])})

# home LAN sessions since CL-B15: the ladder log's session resets and each session's first sample's stream rate
home = []
logs = sorted((ROOT / "logs/games/stream_log_archive").glob("adaptive_bitrate_shadow.jsonl.*"), reverse=True)
logs.append(ROOT / "logs/games/adaptive_bitrate_shadow.jsonl")
pending = None
for p in logs:
    for line in open(p):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if (r.get("at_utc") or "") < HOME_SINCE:
            continue
        if r.get("event") == "session_ended_reset":
            pending = r["at_utc"][:19]
        elif r.get("event") == "sample" and pending and r.get("stream_kbps"):
            home.append((pending, r["stream_kbps"]))
            pending = None
for t, kbps in home:
    o, n = old(LAN), new(LAN, "none")
    rows.append({"set": "home LAN", "start": t, "class": "lan", "actual_kbps": kbps, "old": o, "new": n,
                 "new_is_today": n["kbps"] == kbps == 7000 and n["path_class"] is None})

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "replay_output.json").write_text(json.dumps(rows, indent=1) + "\n")
L = ["# B28 — the replay: the start-rung and ladder readers at the old (the four explicit) and the new (`PRIVYHUB_REMOTE=1`)",
     "", "| set | session | start (UTC) | class | actual | old: rung / source / ladder | new: rung / source / ladder | remote_config | same / today |",
     "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for r in rows:
    o, n = r["old"], r["new"]
    L.append(f"| {r['set']} | {r.get('n', '')} | {r['start']} | {r['class']} | {r['actual_kbps']} | "
             f"{o['kbps']} / {o['source']} / {o['ladder'][0]}-{o['ladder'][-1]} | "
             f"{n['kbps']} / {n['source']} / {n['ladder'][0]}-{n['ladder'][-1]} | {n['remote_config_class']} | "
             f"{('same' if r['same'] else 'DIFFERENT') if 'same' in r else ('today' if r['new_is_today'] else 'NOT today')} |")
g4 = [r for r in rows if r["set"] == "G4-S4"]
hl = [r for r in rows if r["set"] == "home LAN"]
L += ["", f"- G4-S4: {len(g4)} sessions; the old and the new readers agree in **{sum(r['same'] for r in g4)} / {len(g4)}** "
      f"(rung, source, list, ladder). The five under the four lines actually started at "
      f"{sorted({r['actual_kbps'] for r in g4 if r['lines'] == 14})} floor.",
      f"- Home LAN 2026-10-27/28 (CL-B14, G-A7, CL-B15): {len(hl)} session starts (a Home return logs two); the new reader gives today's 7000 with no class in "
      f"**{sum(r['new_is_today'] for r in hl)} / {len(hl)}**; the old (the four explicit) would have started them at "
      f"{sorted({r['old']['kbps'] for r in hl})} (the LAN list's floor)."]
(OUT / "replay_table.md").write_text("\n".join(L) + "\n")
print("\n".join(L[-2:]))
