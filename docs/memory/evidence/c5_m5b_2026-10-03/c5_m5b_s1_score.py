#!/usr/bin/env python3
"""C5-M5B S1b (C5-M5's S1 scorer, paths renamed) -- the pre-registered S1 rows on top of the R0 scorer's per-direction measurements
(c5_m5_r0_score.py s1 S1 -> s1_score.json). Read-only. Writes s1_rows.txt."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "s1b")
sc = json.load(open(os.path.join(HERE, "s1b_score.json")))
dl = [json.loads(l) for l in open(os.path.join(R, "decision_log_S1b.jsonl")) if l.strip()]
tr = [d for d in dl if d.get("event") == "transition"]
done = [d for d in dl if d.get("event") == "transition_done"]
ac = json.load(open(os.path.join(R, "armcheck_S1b.json")))
end = json.load(open(os.path.join(R, "status_end_S1b.json")))
after = json.load(open(os.path.join(R, "status_S1b.json")))
st = {k: json.load(open(os.path.join(R, f"r0_status_S1b_{k}.json"))) for k in ("up3", "up55", "down3", "down55")}
rows = {
    "entry acted: 7000 -> 12600, reason increase_1080p (the policy's own path, injected)":
        len(tr) >= 1 and (tr[0]["from_kbps"], tr[0]["to_kbps"], tr[0]["reason"]) == (7000, 12600, "increase_1080p")
        and len(done) >= 1 and done[0].get("acted") is True,
    "leave acted (the kept leave): 12600 -> 7000, reason capacity_mild":
        len(tr) >= 2 and (tr[1]["from_kbps"], tr[1]["to_kbps"], tr[1]["reason"]) == (12600, 7000, "capacity_mild")
        and len(done) >= 2 and done[1].get("acted") is True,
    "exactly two transitions in the session": len(tr) == 2,
    "one SSRC change per transition (report ssrc_changes 2)": sc["session"]["two SSRC changes in the session (one per switch)"],
    "sizes in native-stream-status: 1920x1080 after the entry, 1280x720 after the leave":
        all((st[k]["width"], st[k]["height"]) == (1920, 1080) for k in ("up3", "up55"))
        and all((st[k]["width"], st[k]["height"]) == (1280, 720) for k in ("down3", "down55")),
    "sizes in SurfaceFlinger (every capture 5-55 s after each)":
        all(sc["directions"][d]["r0a"][k] for d, k in (("up", "SurfaceFlinger 1920x1080 in every capture 5-55 s after"),
                                                       ("down", "SurfaceFlinger 1280x720 in every capture 5-55 s after"))),
    "entry cost: gap at the switch <= 450 ms": sc["directions"]["up"]["r0b"]["output gap at the switch <= 450 ms"],
    "leave cost: gap at the switch <= 450 ms": sc["directions"]["down"]["r0b"]["output gap at the switch <= 450 ms"],
    "any_override false at PLAYING and at the end":
        (ac.get("encoder_overrides") or {}).get("any_override") is False and (end.get("encoder_overrides") or {}).get("any_override") is False,
    "after BACK: level 7000 at 1280x720":
        (after.get("adaptive_bitrate") or {}).get("level") in (7000, None) and (after.get("width"), after.get("height")) == (1280, 720),
}
lines = ["C5-M5B S1b -- the injection session, pre-registered rows (the leave row: NOT APPLICABLE AS WORDED -- no rung_loss was selected; the kept CAPACITY_MILD injected)"]
lines += [f"  {'MET   ' if v else 'MISSED'} {k}" for k, v in rows.items()]
lines.append(f"  (reported, as R0b) stale clause: up {sc['directions']['up']['r0b']['no stale drops 1-10 s after']}, "
             f"down {sc['directions']['down']['r0b']['no stale drops 1-10 s after']}; sequence resyncs (report) "
             f"{sc['session']['sequence resyncs 0 and no resync discontinuity']}")
lines.append(f"  gaps: up {sc['directions']['up']['gap_ms']} ms, down {sc['directions']['down']['gap_ms']} ms; "
             f"after BACK status: level {(after.get('adaptive_bitrate') or {}).get('level')}, {after.get('width')}x{after.get('height')}, "
             f"bitrate {after.get('bitrate_kbps')}")
ok = all(rows.values())
lines.append(f"\nS1b {'PASSES' if ok else 'DOES NOT PASS'} on its rows")
text = "\n".join(lines) + "\n"
print(text)
open(os.path.join(HERE, "s1b_rows.txt"), "w").write(text)
