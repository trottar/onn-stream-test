#!/usr/bin/env python3
"""LAN-R2: the replay as LAN-R1's, through the real controller, in process, offline, read-only.

    python3 -B lan_r2_replay.py     -> replay_lan_r2.md / .json, replay_console.txt

Reuses LAN-R1's replay (`../lan_r1_2026-10-21/lan_r1_replay.py`: G5-S2's harness `replay_recorded` /
`drive_controller` / `load_head_module`, its `evening_sessions`) on LAN-R2's series (`lan_r2_analysis`: LAN-R1's
inputs + BENCH-R1's logs_bench + the frozen gap logs).
1. Flag absent: each span's client sessions through `flag_absent_feed` -- every recorded decision reproduced -- and
   HEAD's controller against the tree's, row for row (the evenings and cells 1-4; the ladder module is untouched).
2. The rule on, `1` (LAN-R1) and `bidir` (LAN-R2), every span: the evenings, the clean windows, G8-S1's cells,
   BENCH-R1 cells 1-4. The unrecoverable groups injected per report (nearest heartbeat); for `bidir` the uplink sink
   holds every logged silence (wall start / end) and the rule's clock is the report's own time, so its counts are
   the code's own (silences that ENDED since the previous evaluated report). Closed on the rung (a decision is
   actuated at once); open loop on the link (later reports are the recorded ones).
"""
from __future__ import annotations

import collections
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EV / "lan_r1_2026-10-21"))
import lan_r2_analysis as R  # noqa: E402
import lan_r1_series as L  # noqa: E402

tempfile.tempdir = str(Path(tempfile.gettempdir()) / "b_lan_r2_replay_tmp")
Path(tempfile.tempdir).mkdir(parents=True, exist_ok=True)
_s = importlib.util.spec_from_file_location("lan_r1_replay", EV / "lan_r1_2026-10-21" / "lan_r1_replay.py")
P = importlib.util.module_from_spec(_s)
_s.loader.exec_module(P)                         # runs nothing; brings H (G5-S2's harness)
H, n2 = P.H, P.n2
import lan_loss_rule as llr  # noqa: E402  (the tree's: H put companion/ on the path)


class WallClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def main() -> int:
    rows = R.ladder_rows()
    bench_rec = [r for r in L.jl(R.BENCH / "logs_bench" / "native_stream_recovery.log") if r.get("at_utc") and r.get("event")]
    rec = n2.RecoveryTimeline(sorted({(r["at_utc"], r["event"]): r for r in L.recovery_rows() + bench_rec}.values(),
                                     key=lambda r: r["at_utc"]))
    hb, gl = R.heartbeats(), R.gaps()
    spans = list(L.SPANS) + list(L.G8_SPANS) + list(R.CELL_SPANS)
    unrec_at = {}
    for sp in spans:
        for x in R.series(sp, rows, hb, gl):
            unrec_at[x["at_utc"]] = R.num(x["unrec"])
    sink = llr.UplinkSilences(maxlen=100_000)
    for s0, ms in gl:
        sink.note(s0, s0 + ms / 1000.0)

    out = {"flag_absent": [], "rules": {}}
    lines = ["# LAN-R2 replay: through the real controller (LAN-R1's harness), offline, read-only", "",
             "## 1. Flag absent", "", "| span | client sessions | samples | recorded events | reproduced | HEAD vs tree |",
             "| --- | ---: | ---: | ---: | --- | --- |"]
    head = H.load_head_module()
    for sp in list(L.SPANS[:2]) + list(R.CELL_SPANS):
        sess = P.evening_sessions(rows, sp)
        smp = ev = mism = 0
        same, n = True, 0
        for s in sess:
            m, _d, _sg, cnt = H.replay_recorded(s, rec, {}, H.flag_absent_feed)
            smp += cnt["samples"]; ev += cnt["events"]; mism += len(m)
            a, b = H.drive_controller(head, s, rec, {}), H.drive_controller(P.live, s, rec, {})
            same &= a == b; n += len(a)
        out["flag_absent"].append({"span": sp[0], "sessions": len(sess), "samples": smp, "events": ev, "mismatch": mism,
                                   "head_vs_tree_identical": same, "rows": n})
        lines.append(f"| {sp[0]} | {len(sess)} | {smp} | {ev} | {'exact' if not mism else f'{mism} MISMATCH'} | "
                     f"{'identical' if same else 'DIFFER'} ({n}) |")

    orig_tel = H.tel_from_sample

    def tel_with_fec(r, stale):
        t = orig_tel(r, stale)
        t["fec"] = {"unrecoverable_groups_delta": unrec_at.get(r.get("at_utc"), 0)}
        return t
    H.tel_from_sample = tel_with_fec
    try:
        lines += ["", "### 1b. Cells 2-4 ran with `PRIVYHUB_LAN_LOSS_RULE=1` live: their recorded run through LAN-R1's rule",
                  "", "| span | samples | recorded events | reproduced |", "| --- | ---: | ---: | --- |"]
        out["flag_1_cells"] = []
        for sp in R.CELL_SPANS[1:]:
            mism_n = smp = ev = 0
            first = []
            for s in P.evening_sessions(rows, sp):
                rule = llr.LanLossRule()
                m, _d, _sg, cnt = H.replay_recorded(s, rec, {}, lambda pol, smp_, ctx, tel, rule=rule: rule.feed(pol, smp_, ctx, tel))
                mism_n += len(m); smp += cnt["samples"]; ev += cnt["events"]; first += m[:2]
            out["flag_1_cells"].append({"span": sp[0], "samples": smp, "events": ev, "mismatch": mism_n, "first": [str(x)[:300] for x in first]})
            lines.append(f"| {sp[0]} | {smp} | {ev} | {'exact' if not mism_n else f'{mism_n} mismatch'} |")
        for value in ("1", "bidir"):
            table = []
            for sp in spans:
                ta, tb = L.ts(sp[2]), L.ts(sp[3])
                sess = P.evening_sessions(rows, sp)
                asks, taken, refused, own = [], [], collections.Counter(), []
                for s in sess:
                    clock = WallClock()
                    rule = llr.LanBidirRule(uplink=sink, clock=clock) if value == "bidir" else llr.LanLossRule()
                    at_by_el = {r.get("session_elapsed_ms"): r["at_utc"] for r in s if r.get("event") == "sample"}

                    def feed(policy, smp, ctx, tel, rule=rule, at_by_el=at_by_el, clock=clock):
                        el = smp.get("elapsed_ms")
                        new = (policy.last_elapsed_ms is not None and isinstance(el, (int, float))
                               and el < policy.last_elapsed_ms)
                        if policy.last_elapsed_ms is not None and not new:
                            ctx = dict(ctx, stream_kbps=policy.level_kbps)
                        at = at_by_el.get(el, "?")
                        if at != "?":
                            clock.t = L.ts(at)
                        evs = rule.feed(policy, smp, ctx, tel)
                        if policy.pending is not None:
                            policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
                        if at == "?" or not ta <= L.ts(at) < tb:
                            return evs
                        for e in evs:
                            if e.get("event") == "lan_loss_rule":
                                asks.append(at)
                                res = e["ladder_result"]
                                if res == "transition":
                                    taken.append(f"{at[11:19]} {e['level_kbps']}->{policy.level_kbps}")
                                else:
                                    refused[res] += 1
                            elif e.get("event") == "transition" and e.get("reason") not in (llr.SOURCE, llr.SOURCE_BIDIR):
                                own.append(f"{at[11:19]} {e.get('from_kbps')}->{e.get('to_kbps')} {e.get('reason')}")
                        return evs
                    H.replay_recorded(s, rec, {}, feed)
                table.append({"span": sp[0], "kind": sp[1], "sessions": len(sess), "asks": len(asks),
                              "first_ask": asks[0][11:19] if asks else None, "taken": taken, "refused": dict(refused),
                              "own": own})
            out["rules"][value] = table
    finally:
        H.tel_from_sample = orig_tel
    for value, label in (("1", "`=1` (LAN-R1: unrec T 4 K 2)"), ("bidir", "`=bidir` (LAN-R2: unrec T 4 K 2 AND >= 2 uplink silences >= 400 ms in each window)")):
        lines += ["", f"## 2. {label}", "", "| span | kind | sessions | asks | first ask | taken (rung path) | refused | the ladder's own transitions |",
                  "| --- | --- | ---: | ---: | --- | --- | --- | --- |"]
        for t in out["rules"][value]:
            lines.append(f"| {t['span']} | {t['kind']} | {t['sessions']} | {t['asks']} | {t['first_ask'] or '—'} | "
                         f"{'; '.join(t['taken']) or '—'} | {', '.join(f'{k} {v}' for k, v in t['refused'].items()) or '—'} | "
                         f"{'; '.join(t['own'][:4]) or '—'} |")
    # the false-trigger table: asks where the rule must not act
    lines += ["", "## 3. The false-trigger table (asks; must be 0)", "", "| span | `=1` | `=bidir` |", "| --- | ---: | ---: |"]
    must0 = [sp[0] for sp in L.SPANS[2:]] + [sp[0] for sp in R.CELL_SPANS[:2]]
    by = {v: {t["span"]: t for t in out["rules"][v]} for v in ("1", "bidir")}
    for name in must0:
        lines.append(f"| {name} | {by['1'][name]['asks']} | {by['bidir'][name]['asks']} |")
    lines += ["", "Shown, not counted as false (random / burst downlink loss at 5 % and 50x20; the ladder may act there): "
              + "; ".join(f"{n}: `=1` {by['1'][n]['asks']}, `=bidir` {by['bidir'][n]['asks']}" for n in [sp[0] for sp in R.CELL_SPANS[2:]])]
    sun = L.SPANS[0][0]
    lines += ["", f"**Sunday:** `=1` first ask {by['1'][sun]['first_ask']} (taken: {'; '.join(by['1'][sun]['taken']) or '—'}); "
              f"`=bidir` first ask {by['bidir'][sun]['first_ask']} (taken: {'; '.join(by['bidir'][sun]['taken']) or '—'})."]
    (HERE / "replay_lan_r2.json").write_text(json.dumps(out, indent=1) + "\n")
    (HERE / "replay_lan_r2.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
