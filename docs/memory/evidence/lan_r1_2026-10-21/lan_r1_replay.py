#!/usr/bin/env python3
"""LAN-R1 §1.1-1.2 (and §2's proof): the two evenings through the real controller, in process, offline.

    python3 -B lan_r1_replay.py [out_dir] [--lan-loss]

Reuses G5-S2's harness (`../g5_s2_2026-10-16/replay.py`: `replay_recorded`, `drive_controller`,
`load_head_module`), fed from the copies in inputs/ only (the ladder log, the recovery log).

1. FLAG ABSENT: every client session of each evening through `policy.feed` (the hook's flag-absent path): every
   recorded sample row's decision fields and every recorded decision / state event reproduced key for key; and
   HEAD's controller (from git) against the working tree's, through `LiveController.observe`, row for row.
2. PRIVYHUB_WAN_ADAPTATION=1 (WanAdaptation.feed), read as LAN (as recorded) and as remote: every suggestion by
   rule id per minute; the forced step-downs; open loop (later reports are the recorded ones). The evenings have no
   per-report stale-drop field (no run telemetry), so G5-S1's `starved` class cannot be met here (disclosed).
3. --lan-loss (after the LAN-R1 code exists): the same sessions through the LAN loss rule's feed, the same table.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lan_r1_series as L  # noqa: E402

tempfile.tempdir = str(Path(tempfile.gettempdir()) / "b_lan_r1_replay_tmp")
Path(tempfile.tempdir).mkdir(parents=True, exist_ok=True)

_spec = importlib.util.spec_from_file_location("g5_s2_replay", HERE.parent / "g5_s2_2026-10-16" / "replay.py")
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)          # puts companion/ and tools/ on the path; runs nothing
live, wa, n2, ab = H.live, H.wa, H.n2, H.ab

EVENINGS = L.SPANS[:2]


def evening_sessions(rows, span):
    ta, tb = L.ts(span[2]), L.ts(span[3])
    out = []
    for s in n2.exact_sessions(rows):
        smp = [r for r in s if r.get("event") == "sample"]
        if smp and L.ts(smp[-1]["at_utc"]) >= ta and L.ts(smp[0]["at_utc"]) < tb:
            out.append(s)
    return out


def per_minute(items):
    c = collections.defaultdict(collections.Counter)
    for at, key in items:
        c[at[11:16]][key] += 1
    return {m: dict(v) for m, v in sorted(c.items())}


def lan_loss_section(rows, rec) -> list[str]:
    """The rule on: each span's companion sessions through LanLossRule.feed, the heartbeat's unrecoverable groups
    injected per report (nearest heartbeat, lan_r1_series). Closed on the rung: a decision is actuated at once and
    the stream follows the ladder (stream_kbps = the policy's level), except that a new client session starts at
    the recorded rung (a full start is 7000, C1). Later reports are still the recorded ones (open loop on the link)."""
    import lan_loss_rule as llr
    hb = L.heartbeat_deltas()
    spans = list(EVENINGS) + list(L.SPANS[2:]) + list(L.G8_SPANS)
    unrec_at = {}
    for sp in spans:
        for x in L.series(sp, rows, hb):
            unrec_at[x["at_utc"]] = x["unrec"] or 0
    orig_tel = H.tel_from_sample

    def tel_with_fec(r, stale):
        t = orig_tel(r, stale)
        t["fec"] = {"unrecoverable_groups_delta": unrec_at.get(r.get("at_utc"), 0)}
        return t

    H.tel_from_sample = tel_with_fec
    out = ["## PRIVYHUB_LAN_LOSS_RULE=1 (T 4 unrecoverable groups per 10-s window on K 2 windows; one rung; floor 5000)",
           "", "| span | client sessions | asks | taken (rung path) | refused (by reason) | the ladder's own transitions |",
           "| --- | ---: | ---: | --- | --- | --- |"]
    detail = []
    try:
        for sp in spans:
            ta, tb = L.ts(sp[2]), L.ts(sp[3])
            sess = evening_sessions(rows, sp)
            asks, taken, refused, own = [], [], collections.Counter(), []
            for s in sess:
                rule = llr.LanLossRule()
                at_by_el = {r.get("session_elapsed_ms"): r["at_utc"] for r in s if r.get("event") == "sample"}

                def feed(policy, smp, ctx, tel, rule=rule, at_by_el=at_by_el):
                    el = smp.get("elapsed_ms")
                    new = (policy.last_elapsed_ms is not None and isinstance(el, (int, float))
                           and el < policy.last_elapsed_ms)
                    if policy.last_elapsed_ms is not None and not new:
                        ctx = dict(ctx, stream_kbps=policy.level_kbps)
                    evs = rule.feed(policy, smp, ctx, tel)
                    if policy.pending is not None:
                        policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
                    at = at_by_el.get(el, "?")
                    if not (ta <= L.ts(at) < tb) if at != "?" else True:
                        return evs
                    for e in evs:
                        if e.get("event") == "lan_loss_rule":
                            asks.append(at)
                            res = e["ladder_result"]
                            if res == "transition":
                                taken.append(f"{at[11:19]} {e['level_kbps']}->"
                                             f"{policy.level_kbps}")
                            else:
                                refused[res] += 1
                            detail.append(f"{sp[0]} {at} ask windows {e['unrec_windows']} at {e['level_kbps']} -> {res}")
                        elif e.get("event") == "transition" and e.get("reason") != llr.SOURCE:
                            own.append(f"{at[11:19]} {e.get('from_kbps')}->{e.get('to_kbps')} {e.get('reason')}")
                    return evs

                H.replay_recorded(s, rec, {}, feed)
            out.append(f"| {sp[0]} | {len(sess)} | {len(asks)} | {'; '.join(taken) or '—'} | "
                       f"{', '.join(f'{k} {v}' for k, v in refused.items()) or '—'} | {'; '.join(own) or '—'} |")
    finally:
        H.tel_from_sample = orig_tel
    return out + ["", "Every ask:", ""] + ["    " + d for d in detail] + [""]


def main(out_dir: Path, lan_loss: bool) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = L.ladder_rows()
    rec = n2.RecoveryTimeline(L.recovery_rows())
    head = H.load_head_module()
    lines, tables, ok_all = [], {}, True
    lines += ["# LAN-R1 replay: the two evenings through the real controller (inputs/ copies only)", "",
              "## 1. Flag absent", "",
              "| evening | client sessions | sample rows | recorded decision / state events | recorded reproduced | "
              "controller HEAD vs working tree (rows) |", "| --- | ---: | ---: | ---: | --- | --- |"]
    per_ev = []
    for span in EVENINGS:
        sess = evening_sessions(rows, span)
        smp = ev = mism_n = 0
        same_all, nrows = True, 0
        first_mism = []
        for s in sess:
            mism, decs, _, cnt = H.replay_recorded(s, rec, {}, H.flag_absent_feed)
            smp += cnt["samples"]
            ev += cnt["events"]
            mism_n += len(mism)
            first_mism += mism[:3]
            a = H.drive_controller(head, s, rec, {})
            b = H.drive_controller(live, s, rec, {})
            same_all &= a == b
            nrows += len(a)
        ok = mism_n == 0 and same_all
        ok_all &= ok
        lines.append(f"| {span[0]} | {len(sess)} | {smp} | {ev} | {'exact' if not mism_n else f'{mism_n} MISMATCH'} | "
                     f"{'identical' if same_all else 'DIFFER'} ({nrows}) |")
        for m in first_mism[:5]:
            lines.append(f"    mismatch: {m}")
        per_ev.append((span, sess))
    lines += ["", f"-> flag absent: {'PASS' if ok_all else 'FAIL'}", ""]

    if lan_loss:
        lines += lan_loss_section(rows, rec)
    feeds = [] if lan_loss else [("PRIVYHUB_WAN_ADAPTATION=1", lambda: wa.WanAdaptation().feed)]
    for flag, make in feeds:
        lines += [f"## {flag}, open loop (later reports are the recorded ones); no claim of improvement", ""]
        for path_label, path_ctx in (("LAN (as recorded)", {}), ("read as remote", {"path_class": "remote"})):
            for span, sess in per_ev:
                sugg_items, dec_rows = [], []
                for s in sess:
                    feed = make()
                    tel_s = {}
                    _, decs, sugg, _ = H.replay_recorded(s, rec, tel_s, feed, path_ctx=path_ctx)
                    at_by_el = {r.get("session_elapsed_ms"): r["at_utc"] for r in s if r.get("event") == "sample"}
                    for el, e in sugg:
                        sugg_items.append((at_by_el.get(el, "?" * 16), f"{e.get('rule')}:{e.get('ladder_result')}"))
                    for el, e in decs:
                        dec_rows.append({"at_utc": at_by_el.get(el), "event": e.get("event"), "class": e.get("class"),
                                         "from": e.get("from_kbps"), "to": e.get("to_kbps"),
                                         "reason": e.get("reason"), "trigger": e.get("trigger")})
                key = f"{flag} / {path_label} / {span[0]}"
                pm = per_minute(sugg_items)
                tables[key] = {"suggestions_per_minute": pm, "decisions": dec_rows}
                lines.append(f"### {span[0]} — {path_label}")
                lines.append("")
                by_rule = collections.Counter(k for _, k in sugg_items)
                lines.append(f"- suggestions {len(sugg_items)}: " + (", ".join(f"{k} {v}" for k, v in sorted(by_rule.items()))
                                                                     or "none"))
                downs = [d for d in dec_rows if d["event"] in ("transition", "would_act", "refused", "hold")]
                lines.append(f"- decisions ({len(downs)}):")
                for d in downs:
                    lines.append(f"    {d['at_utc']} {d['event']} {d['class']} {d['from']}->{d['to']} "
                                 f"reason {d['reason']} trigger {d['trigger']}")
                if pm:
                    lines.append("- per minute: " + "; ".join(f"{m} " + ",".join(f"{k}×{v}" for k, v in c.items())
                                                              for m, c in pm.items()))
                lines.append("")
    (out_dir / ("replay_after_code.md" if lan_loss else "replay_head.md")).write_text("\n".join(lines) + "\n")
    (out_dir / ("replay_after_code.json" if lan_loss else "replay_head.json")).write_text(
        json.dumps(tables, indent=1, default=str) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    raise SystemExit(main(Path(args[0]) if args else HERE, "--lan-loss" in sys.argv))
