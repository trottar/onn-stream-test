#!/usr/bin/env python3
"""C5-CLOSE section 1: the rung-window rule (reports while recovery is not PLAYING are skipped),
replayed. Read-only; offline.

    python3 tools/c5_close_replay.py [out_dir]   -> c5_close_stop_rule.txt, c5_close_s2b_replay.txt / .json

1. THE STOP RULE: the flag absent, the built policy vs the closed controller (c5_m5_replay's
   BASELINE_COMMIT, loaded from git) on every series C5-M5 / C5-M5B compared (c5_m5_replay.stop_rule,
   imported, not copied).
2. FLAG ON, BEFORE vs AFTER: the same series with the rung flag, C5-M5B's policy (4493e68, loaded from
   git) vs the built one. Only series that held a report while recovery was not PLAYING may differ.
3. THE S2b REPLAY: S2b's own decision log (C5-M5B, 2026-10-03), recovery's state per report from the
   recovery logs, the policy with the flag from the session's start, before and after the rule. The
   window must not qualify during the pause.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import c5_m5_replay as m5  # noqa: E402
import c3_l4_n2_replay as n2  # noqa: E402

EVID = REPO / "docs" / "memory" / "evidence"
M5B_COMMIT = "4493e68"
S2B_LOG = EVID / "c5_m5b_2026-10-03" / "s2b" / "decision_log_S2b.jsonl"


def load_at(commit: str, name: str):
    src = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:companion/adaptive_bitrate_live.py"],
                         capture_output=True, text=True, check=True).stdout
    p = Path(tempfile.mkdtemp()) / f"{name}.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def all_groups(rec):
    """The stop rule's series, rebuilt the same way (labels and steps)."""
    groups = []
    for lab, d, n in m5.LEAVE_SET + m5.ENTRY_SET + m5.ENTRY_BESIDE:
        src, tels = m5.series(d, n, "x")
        if tels:
            groups.append((f"{lab} [{src}]", m5.steps_from_series(tels)))
    for si, sess in enumerate(n2.exact_sessions(n2.live_log_rows()), 1):
        groups.append((f"live log session {si} {sess[0]['at_utc'][:19]}Z", m5.steps_from_exact(sess, rec)))
    return groups


def strip_new_key(row: str) -> str:
    """The rule adds one key to the holds snapshot in decision rows (`rung_skipped_not_playing`);
    it is removed before the flag-on comparison so that only decisions are compared."""
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items() if k != "rung_skipped_not_playing"}
        if isinstance(o, list):
            return [walk(v) for v in o]
        return o
    return json.dumps(walk(json.loads(row)), sort_keys=True, default=str)


def flag_on_before_after(lines, rec, m5b):
    diffs, paused_series, n = [], 0, 0
    for lab, steps in all_groups(rec):
        n += 1
        paused = sum(1 for s in steps if s[0] == "feed" and s[2]["guards"].get("recovery_playing") is False)
        paused_series += bool(paused)
        a, b = [], []
        m5.drive(m5b.LivePolicy(top_1080p=True), steps, a)
        m5.drive(live.LivePolicy(top_1080p=True), steps, b)
        b = [strip_new_key(x) for x in b]
        if a != b:
            diffs.append((lab, paused, len(a), len(b)))
    lines.append(f"series: {n}; series holding >= 1 report while recovery was not PLAYING: {paused_series}")
    lines.append(f"series whose events differ (flag on, C5-M5B {M5B_COMMIT} vs built; the new holds key "
                 f"`rung_skipped_not_playing` removed before comparing): {len(diffs)}")
    for lab, paused, la, lb in diffs:
        lines.append(f"   {lab}: {paused} reports not PLAYING; events {la} -> {lb}")
    unexplained = [d for d in diffs if d[1] == 0]
    lines.append(f"differing series with no not-PLAYING report: {len(unexplained)}"
                 + ("  -> OK" if not unexplained else "  -> UNEXPLAINED"))
    return not unexplained, diffs


def s2b_steps(rec):
    rows = [json.loads(x) for x in S2B_LOG.read_text().splitlines() if x.strip()]
    start = max(i for i, r in enumerate(rows) if r.get("event") == "controller_start")
    sess = [r for r in rows[start + 1:] if r.get("mode") == "live" and r.get("at_utc")]
    recorded = {}
    for r in sess:
        if r.get("event") == "refused" and r.get("trigger") == "increase_1080p":
            recorded[r["at_utc"]] = r.get("guards") or {}
    return sess, m5.steps_from_exact(sess, rec), recorded


def replay_s2b(policy, sess, steps):
    """Feed S2b; per report record the window, the recovery guard and any entry decision."""
    trace, entries = [], []
    feeds = [r for r in sess if r.get("event") == "sample" and r.get("disposition") != "dropped_actuating"]
    fi = 0
    for st in steps:
        if st[0] == "feed":
            evs = policy.feed(ab._sample(st[1]), st[2])
            at = feeds[fi]["at_utc"]
            fi += 1
            playing = st[2]["guards"].get("recovery_playing")
            qualified = (len(policy.rung_window) >= live.RUNG_WINDOW_REPORTS
                         and sum(policy.rung_window) >= live.RUNG_CLEAN_NEEDED)
            trace.append({"at_utc": at, "recovery_playing": playing, "window": len(policy.rung_window),
                          "clean": sum(policy.rung_window), "qualified": qualified})
            for e in evs:
                if e.get("trigger") == "increase_1080p":
                    entries.append({"at_utc": at, "event": e["event"], "reason": e.get("reason")})
            if policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
        elif st[0] == "ssrc":
            policy.note_ssrc_change(st[1], clock_ms=st[2])
        elif st[0] == "disable":
            policy.acting = False
    return trace, entries


def summarize(name, trace, entries, lines):
    t0 = n2.ts(trace[0]["at_utc"])
    paused = [t for t in trace if t["recovery_playing"] is False]
    q_paused = [t for t in paused if t["qualified"]]
    first_q = next((t for t in trace if t["qualified"]), None)
    lines.append(f"  [{name}] reports {len(trace)}; not PLAYING {len(paused)}"
                 + (f" (first {(n2.ts(paused[0]['at_utc']) - t0) / 60:.1f} min)" if paused else ""))
    lines.append(f"     window at the end: {trace[-1]['window']} reports, {trace[-1]['clean']} clean; "
                 f"best clean {max(t['clean'] for t in trace)}")
    lines.append(f"     first qualified (full and >= {live.RUNG_CLEAN_NEEDED}): "
                 + (f"{(n2.ts(first_q['at_utc']) - t0) / 60:.1f} min" if first_q else "never"))
    lines.append(f"     reports with the window qualified while recovery was not PLAYING: {len(q_paused)}")
    kinds = {}
    for e in entries:
        kinds[(e["event"], e["reason"])] = kinds.get((e["event"], e["reason"]), 0) + 1
    lines.append(f"     entry decisions: {len(entries)} {dict((f'{k[0]}:{k[1]}', v) for k, v in kinds.items())}")
    return {"reports": len(trace), "not_playing": len(paused), "qualified_while_not_playing": len(q_paused),
            "first_qualified_min": (n2.ts(first_q["at_utc"]) - t0) / 60 if first_q else None,
            "entry_decisions": len(entries), "end_window": trace[-1]["window"], "end_clean": trace[-1]["clean"]}


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = n2.RecoveryTimeline(n2.recovery_rows())
    base = m5.load_baseline()
    m5b = load_at(M5B_COMMIT, "adaptive_bitrate_live_m5b")

    sr = ["C5-CLOSE stop rule: PRIVYHUB_ADAPTIVE_BITRATE_TOP absent, the built live policy (the rung-window "
          f"rule) vs the closed controller ({m5.BASELINE_COMMIT}, loaded from git), every series C5-M5 / "
          "C5-M5B compared", ""]
    ok, ngroups, feeds, events = m5.stop_rule(sr, base)
    sr.append(f"-> {'PASS' if ok else 'FAIL'}: {'zero' if ok else 'NON-ZERO'} differences "
              f"({ngroups} series, {feeds} reports, {events} events)")
    sr += ["", "== flag ON: C5-M5B's policy vs the built policy (reported; only not-PLAYING series may differ)"]
    ok2, diffs = flag_on_before_after(sr, rec, m5b)
    (out_dir / "c5_close_stop_rule.txt").write_text("\n".join(sr) + "\n")

    sess, steps, recorded = s2b_steps(rec)
    lines = [f"C5-CLOSE S2b replay: {S2B_LOG.relative_to(REPO)}, recovery state per report from the recovery "
             "logs, the rung flag on from the session's start", ""]
    feeds_ = [s for s in steps if s[0] == "feed"]
    # the timeline vs what the companion itself recorded on its refused entries
    by_at = {r["at_utc"]: s for r, s in zip([r for r in sess if r.get("event") == "sample"
                                             and r.get("disposition") != "dropped_actuating"], feeds_)}
    agree = sum(1 for at, g in recorded.items()
                if at in by_at and by_at[at][2]["guards"]["recovery_playing"] == g.get("recovery_playing"))
    lines.append(f"recorded refused entries (live log): {len(recorded)}; the timeline's recovery_playing agrees "
                 f"on {agree} of those that match a report by time ({sum(1 for at in recorded if at in by_at)})")
    lines.append("")
    tr_a, en_a = replay_s2b(m5b.LivePolicy(top_1080p=True), sess, steps)
    tr_b, en_b = replay_s2b(live.LivePolicy(top_1080p=True), sess, steps)
    res = {"before": summarize(f"before (C5-M5B {M5B_COMMIT})", tr_a, en_a, lines),
           "after": summarize("after (the rule)", tr_b, en_b, lines)}
    s2b_ok = res["after"]["qualified_while_not_playing"] == 0 and res["after"]["entry_decisions"] == 0
    lines += ["", f"-> S2b: the window {'does NOT' if s2b_ok else 'DOES'} qualify during the pause under the rule"
              f" ({res['after']['qualified_while_not_playing']} qualified reports, "
              f"{res['after']['entry_decisions']} entry decisions)"]
    (out_dir / "c5_close_s2b_replay.txt").write_text("\n".join(lines) + "\n")
    (out_dir / "c5_close_s2b_replay.json").write_text(json.dumps(res, indent=1) + "\n")
    print("\n".join(sr))
    print()
    print("\n".join(lines))
    return 0 if (ok and ok2 and s2b_ok) else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(Path(args[0]) if args else EVID / "c5_close_2026-10-05"))
