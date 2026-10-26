#!/usr/bin/env python3
"""B25: B14's link-notice rule replayed over every heartbeat carrying the link keys since G-A3 (read-only).

The rule is LinkNotice.update() (PrivyHub/app/src/main/java/streaming/LinkNotice.kt) ported line for line.
Each heartbeat's link reading is held until the next heartbeat; the rule ticks every 500 ms on the host's
received_at_utc clock (the activity's UI tick). Usage: replay_link_notice.py REPO_ROOT  (prints JSON + a table).
"""
import hashlib, json, os, statistics, sys
from datetime import datetime

ROOT = sys.argv[1]
EV = os.path.join(ROOT, "docs/memory/evidence")
GATE_SETS = [
    ("G-A3", "g_a3_2026-10-23/runs/logs_run1"),
    ("CL-B10 c1", "cl_b10_2026-10-23/runs/1_snes_5ghz_restart_guard/logs_run1"),
    ("CL-B10 c2", "cl_b10_2026-10-23/runs/2_snes_blackout_both_state_stall/logs_run1"),
    ("CL-B10 c3", "cl_b10_2026-10-23/runs/3_snes_blackout_down_state_stall/logs_run1"),
    ("CL-B10 c4", "cl_b10_2026-10-23/runs/4_snes_24ghz_notice/logs_run1"),
    ("CL-B11 c1", "cl_b11_2026-10-24/runs/1_snes_5ghz_restart_guard_all_paths/logs_run1"),
    ("CL-B11 c2", "cl_b11_2026-10-24/runs/2_snes_blackout_both_fast_ready/logs_run1"),
    ("CL-B11 c3", "cl_b11_2026-10-24/runs/3_snes_blackout_down_fast_ready/logs_run1"),
    ("CL-B12 c1", "cl_b12_2026-10-24/runs/1_snes_5ghz_two_home_presses/logs_run1"),
    ("CL-B12 c2", "cl_b12_2026-10-24/runs/2_snes_blackout_both_umbrella/logs_run1"),
    ("CL-B12 c3", "cl_b12_2026-10-24/runs/3_snes_blackout_down_umbrella/logs_run1"),
    ("G-A4", "g_a4_2026-10-24/runs/logs_run1"),
    ("G4-S4", "g4_s4_2026-10-24/copies/logs/games"),
    ("CL-B13 c1a", "cl_b13_2026-10-25/runs/1_snes_home_presses_restart_fast_attempt1_no_presses/logs_run1"),
    ("CL-B13 c1", "cl_b13_2026-10-25/runs/1_snes_home_presses_restart_fast/logs_run1"),
    ("CL-B13 c2", "cl_b13_2026-10-25/runs/2_snes_home_presses_no_flag/logs_run1"),
    ("CL-B13 c3a", "cl_b13_2026-10-25/runs/3a_snes_blackout_both_wan/logs_run1"),
    ("CL-B13 c3b", "cl_b13_2026-10-25/runs/3b_snes_blackout_down_wan/logs_run1"),
    ("G-A5", "g_a5_2026-10-26/runs/logs_run1"),
]
REF_SETS = [  # before G-A3: reference only, outside the gate
    ("LINK-R1 (ref)", "link_r1_2026-10-23/runs/logs_run1"),
    ("BENCH-R3 (ref)", "bench_r3_2026-10-22/record/logs_whole_run"),
    ("UX-R4 (ref)", "ux_r4_2026-10-23/session/logs/games"),
]
LIVE = os.path.join(ROOT, "logs/games/native_stream_heartbeat.log")

RSSI_T, TX_T, SUSTAIN, CLEAR = -72, 54, 10_000, 30_000
BAND_24, WEAK, SLOW = 1, 2, 4


def band(mhz):
    if mhz is None:
        return None
    if 2400 <= mhz <= 2500:
        return 24
    if 4900 <= mhz <= 5900:
        return 5
    if 5925 <= mhz <= 7125:
        return 6
    return None


class LinkNotice:  # LinkNotice.kt, line for line
    def __init__(self, rssi_t=RSSI_T, tx_t=TX_T):
        self.rssi_t, self.tx_t = rssi_t, tx_t
        self.shown = False; self.reasons = 0; self.shown_count = 0; self.last_reasons = 0
        self.on_session_start()

    def on_session_start(self):
        self.shown = False; self.reasons = 0; self.shown_this_session = False; self.last_band = None
        self.weak_since = None; self.slow_since = None; self.good_since = None

    def update(self, s, now):
        if s is None:
            return None
        rssi, tx, mhz = s
        b = band(mhz)
        if b is not None and self.last_band is not None and b != self.last_band:
            self.shown_this_session = False
        if b is not None:
            self.last_band = b
        is24 = b == 24
        weak_now = rssi is not None and rssi <= self.rssi_t
        slow_now = tx is not None and tx <= self.tx_t
        self.weak_since = (self.weak_since if self.weak_since is not None else now) if weak_now else None
        self.slow_since = (self.slow_since if self.slow_since is not None else now) if slow_now else None
        bits = 0
        if is24: bits |= BAND_24
        if self.weak_since is not None and now - self.weak_since >= SUSTAIN: bits |= WEAK
        if self.slow_since is not None and now - self.slow_since >= SUSTAIN: bits |= SLOW
        good_now = not is24 and not weak_now and not slow_now
        if not self.shown:
            if bits != 0 and not self.shown_this_session:
                self.shown = True; self.shown_this_session = True; self.reasons = bits; self.last_reasons = bits
                self.shown_count += 1; self.good_since = None
                return ("shown", bits)
            return None
        if not good_now:
            self.good_since = None
            return None
        if self.good_since is None:
            self.good_since = now
        if now - self.good_since >= CLEAR:
            self.shown = False; self.reasons = 0; self.good_since = None
            return ("cleared", 0)
        return None


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)


def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if "received_at_utc" not in r:
                continue
            rows.append(r)
    return rows


def sessions(rows):
    out, cur, prev = [], [], None
    for r in rows:
        t = ts(r["received_at_utc"])
        if prev is not None and (r.get("sequence", 0) <= prev.get("sequence", 0) or t - ts(prev["received_at_utc"]) > 30_000):
            out.append(cur); cur = []
        cur.append(r); prev = r
    if cur:
        out.append(cur)
    return out


def reading(r):
    if not any(k in r for k in ("link_rssi_dbm", "link_tx_mbps", "link_frequency_mhz")):
        return None
    return (r.get("link_rssi_dbm"), r.get("link_tx_mbps"), r.get("link_frequency_mhz"))


def replay(sess, rssi_t=RSSI_T, tx_t=TX_T):
    n = LinkNotice(rssi_t, tx_t)
    n.on_session_start()
    t0 = ts(sess[0]["received_at_utc"])
    tend = ts(sess[-1]["received_at_utc"])
    events, per_hb = [], []
    held, i, t = None, 0, t0
    while t <= tend:
        while i < len(sess) and ts(sess[i]["received_at_utc"]) <= t:
            rd = reading(sess[i])
            if rd is not None:
                held = rd
            ev = n.update(held, t)  # a heartbeat's arrival is also a tick
            if ev:
                events.append((t - t0, ev))
            per_hb.append((sess[i], n.reasons if n.shown else 0))
            i += 1
        ev = n.update(held, t)
        if ev:
            events.append((t - t0, ev))
        t += 500
    shown_ms, on_at = 0, None
    for at, (kind, _) in events:
        if kind == "shown":
            on_at = at
        elif on_at is not None:
            shown_ms += at - on_at; on_at = None
    if on_at is not None:
        shown_ms += (tend - t0) - on_at
    return events, shown_ms, per_hb, n


def describe(label, sess):
    rds = [reading(r) for r in sess]
    rds = [x for x in rds if x is not None]
    bands = sorted({band(m) for _, _, m in rds if band(m) is not None})
    rssis = [x for x, _, _ in rds if x is not None]
    txs = [x for _, x, _ in rds if x is not None]
    events, shown_ms, per_hb, n = replay(sess)
    first = next((at for at, (k, _) in events if k == "shown"), None)
    reasons = 0
    for _, (k, b) in events:
        if k == "shown":
            reasons |= b
    client = [r.get("link_notice") for r in sess if "link_notice" in r]
    d = dict(set=label, start=sess[0]["received_at_utc"][:16] + "Z", heartbeats=len(sess), with_link=len(rds),
             bands=bands, rssi_min=min(rssis) if rssis else None,
             rssi_median=statistics.median(rssis) if rssis else None, tx_min=min(txs) if txs else None,
             duration_s=round((ts(sess[-1]["received_at_utc"]) - ts(sess[0]["received_at_utc"])) / 1000),
             would_show=first is not None, reasons=reasons,
             reason_names=[nm for bit, nm in ((1, "band 2.4 GHz"), (2, "RSSI <= -72 for 10 s"), (4, "tx <= 54 for 10 s")) if reasons & bit],
             first_shown_s=None if first is None else round(first / 1000, 1),
             shown_for_s=round(shown_ms / 1000, 1), shows=sum(1 for _, (k, _) in events if k == "shown"),
             clears=sum(1 for _, (k, _) in events if k == "cleared"),
             client_link_notice_key=bool(client))
    if client:  # the port's check against the real client's own bits
        dis = [(r["received_at_utc"], r["link_notice"], mine) for r, mine in per_hb if "link_notice" in r and r["link_notice"] != mine]
        d["client_bits_seen"] = sorted(set(client))
        d["client_vs_replay_disagreements"] = len(dis)
        d["client_vs_replay_disagreement_rows"] = [(a[11:23], c, m) for a, c, m in dis][:10]
    # the lowest RSSI / tx held >= 10 s by this session (for the threshold that keeps it quiet)
    d["rssi_floor_held_10s"] = held_floor(sess, 0)
    d["tx_floor_held_10s"] = held_floor(sess, 1)
    return d


def held_floor(sess, idx):
    """The lowest value v such that the reading stayed <= v for >= 10 s (held readings); None if never 10 s."""
    pts = [(ts(r["received_at_utc"]), reading(r)) for r in sess]
    pts = [(t, rd[idx]) for t, rd in pts if rd is not None and rd[idx] is not None]
    best = None
    for a in range(len(pts)):
        mx = pts[a][1]
        for b in range(a + 1, len(pts)):
            mx = max(mx, pts[b - 1][1])
            if pts[b][0] - pts[a][0] >= SUSTAIN:
                best = mx if best is None else min(best, mx)
                break
    return best


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    out = dict(rule=dict(rssi_dbm=RSSI_T, tx_mbps=TX_T, sustain_ms=SUSTAIN, clear_ms=CLEAR, tick_ms=500),
               inputs=[], sessions=[], reference=[], live_supplement=[])
    seen = set()
    for label, rel in GATE_SETS + REF_SETS:
        p = os.path.join(EV, rel, "native_stream_heartbeat.log")
        rows = load(p)
        is_ref = (label, rel) in REF_SETS
        out["inputs"].append(dict(set=label, file=os.path.relpath(p, ROOT), sha256=sha(p), rows=len(rows), reference=is_ref))
        for s in sessions(rows):
            if not any(reading(r) for r in s):
                continue
            (out["reference"] if is_ref else out["sessions"]).append(describe(label, s))
        if not is_ref:
            seen.update(r["received_at_utc"] for r in rows)
    if os.path.exists(LIVE):
        rows = load(LIVE)
        out["inputs"].append(dict(set="live (supplement)", file=os.path.relpath(LIVE, ROOT), sha256=sha(LIVE), rows=len(rows), reference=False))
        for s in sessions(rows):
            if not any(reading(r) for r in s):
                continue
            overlap = sum(1 for r in s if r["received_at_utc"] in seen)
            if overlap:  # already counted from an evidence file
                out["live_supplement"].append(dict(start=s[0]["received_at_utc"][:16] + "Z", heartbeats=len(s), in_evidence=overlap))
                continue
            out["sessions"].append(describe("live", s))
    g = out["sessions"]
    s24 = [d for d in g if 24 in d["bands"]]
    s5 = [d for d in g if d["bands"] and 24 not in d["bands"]]
    out["gate"] = dict(
        sessions=len(g), sessions_24=len(s24), sessions_24_shown=sum(d["would_show"] and d["reasons"] & 1 != 0 for d in s24),
        sessions_24_not_shown=[(d["set"], d["start"]) for d in s24 if not (d["would_show"] and d["reasons"] & 1)],
        sessions_5=len(s5), sessions_5_shown=[(d["set"], d["start"], d["reason_names"], d["first_shown_s"], d["shown_for_s"]) for d in s5 if d["would_show"]])
    floors5 = [d["rssi_floor_held_10s"] for d in s5 if d["rssi_floor_held_10s"] is not None]
    txf5 = [d["tx_floor_held_10s"] for d in s5 if d["tx_floor_held_10s"] is not None]
    out["quiet_thresholds_5ghz"] = dict(
        rssi_lowest_held_10s=min(floors5) if floors5 else None,
        rssi_threshold_quiet=(min(floors5) - 1) if floors5 else None,
        tx_lowest_held_10s=min(txf5) if txf5 else None,
        tx_threshold_quiet=(min(txf5) - 1) if txf5 else None)
    print(json.dumps(out, indent=1))


main()
