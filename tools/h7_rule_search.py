#!/usr/bin/env python3
"""H7 (B94): from a few labelled save states, find the memory that says who won — candidate rules in B93's rule JSON.

    python3 tools/h7_rule_search.py --content <game> --system ps1|snes --states <states.json> [--players 2] [--loads 3]
                                    [--hints <cheat list>]

states.json: [{"state": "<file>", "label": "begin" | "end", "winner": "P1" | "P2" | ... | null}, ...]  (2 to 4 players)

Each state is loaded PAUSED in a headless RetroArch (B93's session: temp folders, the hub's saves untouched) --loads
times; its whole main memory is read in 16 KiB chunks; an address that differs between loads of one state is dropped.
Three templates are searched, each candidate holding in EVERY labelled state:
  (a) a per-player counter — one field per player at a constant stride; every value <= 31; all equal at "begin"; at
      "end" the winner's strictly the largest and above its "begin" value;
  (b) a per-player level that empties — all equal and >= 8 at "begin"; at "end" none above its "begin" value, the
      winner's strictly the largest and > 0, every loser at 0;
  (c) a single winner field — constant over "begin"; one value per winner at "end", different winners different
      values, the "begin" value none of them (needs ends won by at least two players); B96: the values a player number
      or flag (index from 0, number from 1, or bit flag — one scheme), the "begin" value none of the scheme's.
B96 — families and held-out folds: candidates that are one place read another way (an overlapping read; a copy with
identical values in every state within WINDOW bytes) are one family, its rule the lowest aligned member. For every
"end" state in turn the search runs on the others and each family's rule must name the held-out winner (a fold whose
winner has no other example is skipped and counted). Evidence per template: "strong" (every winner seen has two ends,
a family passes every fold — the top family is the answer), "weak" (families pass, a winner seen once), "none".
"decided" = "strong" only; otherwise the states that would make it strong.
B97 — (b2) a per-player level, the winner's the larger: equal and >= 8 at "begin", none above it at "end", the
winner's strictly the largest (a loser may be above 0); --hints FILE (a cheat list in the hub's stored form, read by
tools/h7_cheat_hints.py): a family covering a hinted address for the right player is hinted and ranked first; every
per-player set of hints (one kind, one width, one stride) is also tested directly as a rule (template h), with its
values in every state. A hint is evidence, not a verdict: the folds and evidence levels apply as to any family.
The answer's template order: a hinted top family first, then a, b, c, b2, h. Prints one JSON document.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h7_minigame_proof as proof  # noqa: E402

MEMORY = {"snes": 0x20000, "ps1": 0x200000}     # the main memory READ_CORE_RAM reads, per system
CHUNK = 16384                                   # one command answers up to ~21,000 bytes (settled, B94)
MAX_STRIDE = 0x400
SMALL = 31
HIGH = 8
SHOWN = 10                                      # candidates listed per template (the count is always given)


class SearchError(RuntimeError):
    pass


# --- reading ---------------------------------------------------------------------------------------------------------
LOADING = re.compile(r'\[State\] Loading state ".*", (\d+) bytes\.')


def load_paused(s: "proof.Session", state: Path, bound: float = 10.0, settle: float = 1.0) -> None:
    """Pause, then load the state. RetroArch 1.22.2 logs `[State] Loading state "…", N bytes.` (N > 0 when read) and,
    on a failure, `Failed to load state from "…"` (seen on a fixture: a corrupt file reads 0 bytes, then fails)."""
    s.pause()
    shutil_copy(state, s.state_path())
    before = len(s.text())
    s.send("LOAD_STATE_SLOT 0")
    end = time.monotonic() + bound
    seen = None
    while time.monotonic() < end:
        new = s.text()[before:]
        if "Failed to load state" in new:
            raise SearchError("RetroArch failed to load a state")
        m = LOADING.search(new)
        if m and seen is None:
            if int(m.group(1)) == 0:
                raise SearchError("RetroArch read 0 bytes of a state")
            seen = time.monotonic()
        if seen is not None and time.monotonic() - seen >= settle:
            return
        time.sleep(0.05)
    raise SearchError("RetroArch did not report a state loaded")


def shutil_copy(src: Path, dst: Path) -> None:
    import shutil
    shutil.copyfile(src, dst)


def read_memory(s: "proof.Session", size: int) -> bytes:
    out = bytearray()
    for a in range(0, size, CHUNK):
        n = min(CHUNK, size - a)
        parts = (s.ask(f"READ_CORE_RAM {a:x} {n}", 3.0) or "").split()
        if len(parts) != n + 2 or parts[2] == "-1":
            raise SearchError(f"memory not readable at {a:#x}")
        out += bytes(int(b, 16) for b in parts[2:])
    return bytes(out)


def read_state(content: Path, system: str, state: Path, loads: int = 3) -> tuple[bytes, np.ndarray]:
    """The state's memory as it stands, and the mask of bytes equal on every load."""
    import shutil
    import tempfile
    if system not in MEMORY:
        raise SearchError(f"system not supported: {system}")
    dumps = []
    for _ in range(loads):
        work = Path(tempfile.mkdtemp(prefix="h7_search_"))
        s = proof.Session(content, system, work)
        try:
            s.wait_playing()
            load_paused(s, state)
            dumps.append(read_memory(s, MEMORY[system]))
        except proof.ProofError as exc:
            raise SearchError(str(exc)) from exc
        finally:
            s.close()
            shutil.rmtree(work, ignore_errors=True)
    arr = np.stack([np.frombuffer(d, dtype=np.uint8) for d in dumps])
    stable = np.all(arr == arr[0], axis=0)
    return dumps[0], stable


# --- the search ------------------------------------------------------------------------------------------------------
TEMPLATES = {"a": "a per-player counter", "b": "a per-player level that empties", "c": "a single winner field",
             "b2": "a per-player level, the winner's the larger", "h": "a hinted pair, tested directly"}
ORDER = ("a", "b", "c", "b2", "h")              # the answer's template order after "hinted first" (B96; B97: b2, h)
SETS_CAP = 200                                  # B97: hinted sets tested directly, at most
B2_PAIRS = True                                 # B97: (b2) pairs by equal "begin" values (False = the stride loop)
B2_CAP = 200_000                                # B97 addendum 2: more (b2) candidates than this → not testable
WINDOW = 0x100                                  # B96: copies with identical values this close are one family
MEMBERS_SHOWN = 5
C_PLAYER_VALUES = True                          # B96: (c) tightened; False = B94's (c), for the before / after count
SCHEMES = (("index from 0", lambda k: k), ("number from 1", lambda k: k + 1), ("bit flag", lambda k: 1 << k))


def _fields(mem: bytes, size: int) -> np.ndarray:
    b = np.frombuffer(mem, dtype=np.uint8).astype(np.int32)
    if size == 1:
        return b
    return b[:-1] | (b[1:] << 8)


def _stable(stable: np.ndarray, size: int) -> np.ndarray:
    return stable if size == 1 else (stable[:-1] & stable[1:])


def _player(w: str | None) -> int | None:
    return None if w is None else int(str(w).lstrip("Pp")) - 1


class _Ctx:
    """The labelled states read once: fields per width, the stable mask over every state and every load."""

    def __init__(self, states: list[dict], players: int):
        self.states, self.players = states, players
        self.V = [{1: _fields(s["mem"], 1), 2: _fields(s["mem"], 2)} for s in states]
        self.ok = {}
        for size in (1, 2):
            ok = np.ones(len(self.V[0][size]), dtype=bool)
            for s in states:
                ok &= _stable(s["stable"], size)
            self.ok[size] = ok
        self.mems = np.stack([np.frombuffer(s["mem"], dtype=np.uint8) for s in states])
        self.label = [s["label"] for s in states]
        self.win = [_player(s["winner"]) if s["label"] == "end" else None for s in states]


def search(states: list[dict], players: int, hints: list[dict] | None = None) -> dict:
    """states: [{"label", "winner", "mem": bytes, "stable": bool array}] — the pure search (no emulator).
    hints (B97): h7_cheat_hints' hints [{"player", "address", "bytes", "value", "kind", "code", "pair_group"}]."""
    begins = [i for i, s in enumerate(states) if s["label"] == "begin"]
    ends = [(i, _player(s["winner"])) for i, s in enumerate(states) if s["label"] == "end"]
    if not begins or not ends:
        raise SearchError("at least one 'begin' and one 'end' state are needed")
    if any(w is None or not 0 <= w < players for _, w in ends):
        raise SearchError("every 'end' state needs its winner (P1 … P%d)" % players)
    ctx = _Ctx(states, players)
    ctx.sets = _hinted_sets(ctx, hints or [])
    every = list(range(len(states)))
    full = _run(ctx, every)
    fams = {k: _families(full[k], k) for k in ORDER}
    for k in ("a", "b", "b2"):
        _mark_hinted(fams[k], hints or [], players)
    for f in fams["h"]:                                   # a set tested directly is hinted by construction
        f["hinted"] = True
        f["same_code_name"] = any(c["same_code_name"] for c in f["members"])
    fams["h"].sort(key=_order)
    folds = {k: [] for k in ORDER}
    for e, w in ends:
        if not any(j != e and x == w for j, x in ends):
            for k in ORDER:
                folds[k].append({"held_out": e, "winner": f"P{w + 1}", "skipped": True,
                                 "why": f"no other 'end' won by P{w + 1}"})
            continue
        train = [i for i in every if i != e]
        tc = _run(ctx, train)
        for k in ORDER:
            folds[k].append(_fold(ctx, k, e, w, train, tc[k], fams[k]))
    out: dict = {"players": players, "states": [{"label": s["label"], "winner": s["winner"]} for s in states],
                 "unstable_bytes": int(sum(int((~s["stable"]).sum()) for s in states)), "templates": {}}
    epw = {f"P{w + 1}": sum(1 for _, x in ends if x == w) for w in sorted({w for _, w in ends})}
    for k in ORDER:
        out["templates"][k] = _report(ctx, k, full[k], fams[k], folds[k], epw, every)
    out["hinted_sets"] = _sets_report(ctx, fams)
    return _verdict(out, epw)


def _run(ctx: _Ctx, idx: list[int]) -> dict:
    """B94's candidate search on the states `idx` (every template): {template: merged candidates}."""
    begins = [i for i in idx if ctx.label[i] == "begin"]
    ends = [(i, ctx.win[i]) for i in idx if ctx.label[i] == "end"]
    res = {k: _block(ctx, idx, begins, ends, k) for k in ("a", "b", "b2")}
    taken: set[int] = set()
    for k in ("a", "b"):
        for c in res[k]:
            for k2 in range(ctx.players):
                taken.update(range(c["base"] + k2 * c["stride"], c["base"] + k2 * c["stride"] + c["size"]))
    res["c"] = _single(ctx, idx, begins, ends, taken)
    res["h"] = _sets_holding(ctx, idx, begins, ends)
    return res


def _block(ctx: _Ctx, idx, begins, ends, kind) -> list[dict]:
    players, found = ctx.players, []
    for size in (1, 2):
        V = [ctx.V[i][size] for i in range(len(ctx.states))]
        ok = ctx.ok[size]
        if kind == "a":
            small = ok.copy()
            for i in idx:
                small &= V[i] <= SMALL
            masks = []
            for k in range(players):
                m = small.copy()
                for e, w in ends:
                    if w == k:
                        for b in begins:
                            m &= V[e] > V[b]
                masks.append(m)
        else:
            masks = []
            for k in range(players):
                m = ok.copy()
                for b in begins:
                    m &= V[b] >= HIGH
                for e, w in ends:
                    for b in begins:
                        m &= V[e] <= V[b]
                    if kind == "b":
                        m &= (V[e] > 0) if w == k else (V[e] == 0)
                    elif w == k:                          # b2: the winner's above 0; a loser may be too (B97)
                        m &= V[e] > 0
                    else:                                 # b2: a loser's below its begin (below the winner's ≤ it)
                        for b in begins:
                            m &= V[e] < V[b]
                masks.append(m)
        if kind == "b2" and B2_PAIRS:
            found += _b2_found(V, idx, begins, ends, masks, size, players, B2_CAP - len(found))
            if len(found) > B2_CAP:
                return {"not_testable": f"too many (b2) candidates to rank: more than {B2_CAP:,} — the template "
                                        "cannot decide here"}
            continue
        j = ends[0][1]
        seeds = np.nonzero(masks[j])[0]
        n = len(V[0])
        for d in range(size, MAX_STRIDE + 1):
            base = seeds - j * d
            base = base[(base >= 0) & (base + (players - 1) * d < n)]
            if not len(base):
                continue
            keep = np.ones(len(base), dtype=bool)
            for k in range(players):
                keep &= masks[k][base + k * d]
            base = base[keep]
            if not len(base):
                continue
            vals = {i: np.stack([V[i][base + k * d] for k in range(players)]) for i in idx}
            keep = np.ones(len(base), dtype=bool)
            for b in begins:
                keep &= np.all(vals[b] == vals[b][0], axis=0)
            for e, w in ends:
                others = np.delete(vals[e], w, axis=0)
                keep &= np.all(vals[e][w] > others, axis=0)
            for a in base[keep]:
                found.append({"size": size, "base": int(a), "stride": d,
                              "values": [[int(V[i][int(a) + k * d]) for k in range(players)] for i in idx]})
    return _merge(found, ctx.mems[idx], players)


def _b2_found(V, idx, begins, ends, masks, size, players, room: int) -> list[dict]:
    """(b2) without a loop over every stride: P1 / P2 positions are paired only when their "begin" values are equal
    (sorted by value, then address; strides size … MAX_STRIDE), then every condition is checked as in the loop.
    The same candidates as the loop (tested); far fewer element reads where memory is varied."""
    n = len(V[0])
    b0 = begins[0]
    A = np.nonzero(masks[0])[0]
    B = np.nonzero(masks[1])[0]
    if not len(A) or not len(B):
        return []
    span = np.int64(n + MAX_STRIDE + 2)
    keyB = V[b0][B].astype(np.int64) * span + B
    order = np.argsort(keyB, kind="stable")
    keyB, B = keyB[order], B[order]
    found = []
    for c0 in range(0, len(A), 1 << 18):
        a = A[c0:c0 + (1 << 18)]
        base_key = V[b0][a].astype(np.int64) * span + a
        lo = np.searchsorted(keyB, base_key + size)
        hi = np.searchsorted(keyB, base_key + MAX_STRIDE, side="right")
        cnt = hi - lo
        total = int(cnt.sum())
        if not total:
            continue
        start = np.repeat(lo, cnt)
        offs = np.arange(total) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        p1 = np.repeat(a, cnt)
        d = B[start + offs] - p1
        keep = p1 + (players - 1) * d < n
        p1, d = p1[keep], d[keep]
        for k in range(2, players):
            ok = masks[k][p1 + k * d]
            p1, d = p1[ok], d[ok]
        vals = {i: np.stack([V[i][p1 + k * d] for k in range(players)]) for i in idx}
        keep = np.ones(len(p1), dtype=bool)
        for b in begins:
            keep &= np.all(vals[b] == vals[b][0], axis=0)
        for e, w in ends:
            others = np.delete(vals[e], w, axis=0)
            keep &= np.all(vals[e][w] > others, axis=0)
        if len(found) + int(keep.sum()) > room:          # addendum 2: stop before building more than the cap
            return found + [None] * (room + 1 - len(found))
        for x, dd in zip(p1[keep], d[keep]):
            found.append({"size": size, "base": int(x), "stride": int(dd),
                          "values": [[int(V[i][int(x) + k * int(dd)]) for k in range(players)] for i in idx]})
    return found


def _merge(found: list[dict], mems: np.ndarray, players: int) -> list[dict]:
    """B94: reads of the same memory are one candidate: two candidates whose CHANGING bytes (a byte that differs between
    the states) are the same addresses are one field read two ways — a 1- and a 2-byte read, or a 2-byte read one byte
    early (the value × 256). The aligned, wider read is kept. `all_vary`: every player's field changes in some state."""
    changing = np.any(mems != mems[0], axis=0)
    by: dict = {}
    for c in found:
        fields = [range(c["base"] + k * c["stride"], c["base"] + k * c["stride"] + c["size"]) for k in range(players)]
        key = tuple(sorted(a for f in fields for a in f if changing[a]))
        c = dict(c, all_vary=all(any(changing[a] for a in f) for f in fields))
        rank = (c["base"] % c["size"] != 0, -c["size"])
        if key not in by:
            by[key] = c
        else:
            keep, other = (c, by[key]) if rank < (by[key]["base"] % by[key]["size"] != 0, -by[key]["size"]) else (by[key], c)
            keep = dict(keep, also_read_as=sorted(set(keep.get("also_read_as", [])) | {f"{other['size']}@{other['base']:#x}"}))
            by[key] = keep
    return list(by.values())


def _single(ctx: _Ctx, idx, begins, ends, taken) -> dict:
    """(c): constant over "begin"; one value per winner at "end"; B96: the values a player number or flag (one scheme
    for every seen winner), the "begin" value none of the scheme's values. {"not_testable"} with fewer than 2 winners."""
    winners = sorted({w for _, w in ends})
    if len(winners) < 2:
        return {"not_testable": "needs 'end' states won by at least two different players"}
    players, cands = ctx.players, []
    for size in (1, 2):
        V = [ctx.V[i][size] for i in range(len(ctx.states))]
        ok = ctx.ok[size].copy()
        for b in begins[1:]:
            ok &= V[b] == V[begins[0]]
        rep = {}
        for e, w in ends:
            if w in rep:
                ok &= V[e] == V[rep[w]]
            else:
                rep[w] = e
        ws = sorted(rep)
        for x in range(len(ws)):
            ok &= V[rep[ws[x]]] != V[begins[0]]
            for y in range(x + 1, len(ws)):
                ok &= V[rep[ws[x]]] != V[rep[ws[y]]]
        scheme = np.full(len(ok), -1, dtype=np.int8)
        if C_PLAYER_VALUES:
            for si, (_name, f) in enumerate(SCHEMES):
                m = ok.copy()
                for w in ws:
                    m &= V[rep[w]] == f(w)
                for k in range(players):
                    m &= V[begins[0]] != f(k)
                scheme[m & (scheme < 0)] = si
            ok &= scheme >= 0
        for a in np.nonzero(ok)[0]:
            if any(int(a) + i in taken for i in range(size)):
                continue
            si = int(scheme[a])
            values = ({f"P{k + 1}": SCHEMES[si][1](k) for k in range(players)} if si >= 0 else
                      {f"P{w + 1}": int(V[rep[w]][a]) for w in ws})
            cands.append({"size": size, "address": int(a), "values": values, "begin": int(V[begins[0]][a]),
                          "scheme": SCHEMES[si][0] if si >= 0 else None,
                          "series": tuple(int(V[i][a]) for i in idx)})
    seen, uniq = set(), []
    for c in sorted(cands, key=lambda c: (-c["size"], c["address"])):
        if (c["address"], c["begin"]) in seen:
            continue
        seen.add((c["address"], c["begin"]))
        uniq.append(c)
    return {"cands": uniq}


# --- families and folds (B96) ----------------------------------------------------------------------------------------
def _cands(res) -> list[dict]:
    return res.get("cands", []) if isinstance(res, dict) else res


def _keys(c: dict) -> set:
    """Every read a candidate stands for: (stride, width, address) — (c) has stride 0."""
    if "address" in c:
        return {(0, c["size"], c["address"])}
    ks = {(c["stride"], c["size"], c["base"])}
    for r in c.get("also_read_as", []):
        n, a = r.split("@")
        ks.add((c["stride"], int(n), int(a, 16)))
    return ks


def _families(res, kind: str) -> list[dict]:
    """Candidates linked when they are one place read another way: (1) an overlapping read (the same stride, P1's
    fields overlapping, bases at most 1 byte apart); (2) a copy (the same stride and width, identical values for every
    player in every labelled state, bases at most WINDOW apart). A family = a connected set; its rule = the lowest
    aligned member (at one base the wider read)."""
    cands = _cands(res)
    if not cands:
        return []
    single = "address" in cands[0]
    base = (lambda c: c["address"]) if single else (lambda c: c["base"])
    stride = (lambda c: 0) if single else (lambda c: c["stride"])
    parent = list(range(len(cands)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        x, y = find(x), find(y)
        if x != y:
            parent[max(x, y)] = min(x, y)

    at: dict = {}
    for i, c in enumerate(cands):
        at.setdefault((stride(c), base(c)), []).append(i)
    for i, c in enumerate(cands):
        for d in (-1, 0, 1):
            for j in at.get((stride(c), base(c) + d), ()):
                if j != i:
                    lo, hi = (c, cands[j]) if base(c) <= base(cands[j]) else (cands[j], c)
                    if base(lo) + lo["size"] > base(hi):                    # the reads overlap
                        union(i, j)
    groups: dict = {}
    for i, c in enumerate(cands):
        sig = (stride(c), c["size"], c["series"] if single else json.dumps(c["values"]))
        groups.setdefault(sig, []).append(i)
    for members in groups.values():
        members.sort(key=lambda i: base(cands[i]))
        for x, y in zip(members, members[1:]):
            if base(cands[y]) - base(cands[x]) <= WINDOW:
                union(x, y)
    fam: dict = {}
    for i in range(len(cands)):
        fam.setdefault(find(i), []).append(cands[i])
    out = []
    for members in fam.values():
        rule = min(members, key=lambda c: (base(c) % c["size"] != 0, base(c), -c["size"]))
        keys = set().union(*(_keys(c) for c in members))
        out.append({"rule_member": rule, "members": members, "keys": keys, "hinted": False,
                    "all_vary": True if single else any(c["all_vary"] for c in members)})
    out.sort(key=_order)
    return out


def _order(f: dict) -> tuple:
    """B96's order: hinted first, every player's field changing, aligned, stride a multiple of 4, smaller stride, lower
    address."""
    c = f["rule_member"]
    b, d = (c["address"], 0) if "address" in c else (c["base"], c["stride"])
    return (not f["hinted"], not f.get("same_code_name", False), not f["all_vary"], b % c["size"] != 0, d % 4 != 0,
            abs(d), b)


def _names(ctx: _Ctx, i: int, c: dict) -> int | None:
    """The player a rule names in state i (B93's reading): the field strictly the largest; (c) the value given to one
    winner. None when it names nobody."""
    V = ctx.V[i][c["size"]]
    if "address" in c:
        hits = [int(k.lstrip("P")) - 1 for k, v in c["values"].items() if v == int(V[c["address"]])]
        return hits[0] if len(hits) == 1 else None
    vals = [int(V[c["base"] + k * c["stride"]]) for k in range(ctx.players)]
    top = max(vals)
    return vals.index(top) if vals.count(top) == 1 else None


def _fold(ctx: _Ctx, kind: str, e: int, w: int, train: list[int], res, fams: list[dict]) -> dict:
    row = {"held_out": e, "winner": f"P{w + 1}", "skipped": False}
    if isinstance(res, dict) and "not_testable" in res:
        row.update(skipped=True, why="the template is not testable on the other states")
        return row
    tf = _families(res, kind)
    owner = {}
    for n, f in enumerate(tf):
        for key in f["keys"]:
            owner[key] = n
    named = [_names(ctx, e, f["rule_member"]) == w for f in tf]
    for f in fams:
        n = next((owner[key] for key in f["keys"] if key in owner), None)
        f.setdefault("fold_results", []).append(n is not None and named[n])
    missed = [f for f, ok in zip(tf, named) if not ok]
    row.update(training_families=len(tf), named_the_winner=sum(named), did_not_name=len(missed),
               did_not_name_first=[_rule_of(f, ctx.players, kind)["rule"] for f in missed[:SHOWN]])
    return row


def _rule_of(f: dict, players: int, kind: str) -> dict:
    c = f["rule_member"]
    reads = sorted({(n, a) for (_d, n, a) in f["keys"]}, key=lambda r: (r[1], r[0]))
    common = {"members": len(f["members"]), "member_reads": [f"{n}@{a:#x}" for n, a in reads[:MEMBERS_SHOWN]],
              "hinted": f["hinted"], **({"hinted_by": f["hinted_by"]} if f.get("hinted_by") else {}),
              **({"same_code_name": f["same_code_name"]} if "same_code_name" in f else {})}
    if "address" in c:
        rule = {"players": [], "address": hex(c["address"]), "bytes": c["size"], "endian": "little",
                "values": c["values"], "none_value": c["begin"], "memory": "ram"}
        why = ("one value per winner at 'end' (%s), another at 'begin'" % c["scheme"] if c.get("scheme") else
               "one value per winner at 'end', another at 'begin'")
        return {"rule": rule, "why": why, "values_per_state": list(c["series"]), **common}
    rule = {"players": [{"name": f"P{k + 1}", "address": hex(c["base"] + k * c["stride"]), "bytes": c["size"],
                         "endian": "little"} for k in range(players)],
            "winner": "max", "memory": "ram", "none_when": "equal"}
    why = {"a": "the same field per player at stride %#x: equal at every 'begin', the winner's the largest at every "
                "'end'",
           "b": "a level per player at stride %#x: equal and high at every 'begin', the losers at 0 at every 'end'",
           "b2": "a level per player at stride %#x: equal and high at every 'begin', none above it at 'end', the "
                 "winner's strictly the largest (a loser may be above 0)",
           "h": "the cheat list's per-player addresses (stride %#x), read as a rule: equal at every 'begin', the "
                "winner's the largest at every 'end'"}
    return {"rule": rule, "why": why.get(kind, "a field per player at stride %#x") % c["stride"],
            "values_per_state": c["values"], "every_player_changes": f["all_vary"], **common}


def _report(ctx: _Ctx, kind: str, res, fams: list[dict], folds: list[dict], epw: dict, every: list[int]) -> dict:
    name = TEMPLATES[kind]
    ran = [r for r in folds if not r["skipped"]]
    skipped = [r for r in folds if r["skipped"]]
    if isinstance(res, dict) and "not_testable" in res:
        return {"name": name, "count": None, "families_found": None, "families": [], "passing_count": 0,
                "passing": [], "candidates": [], "not_testable": res["not_testable"], "folds": folds,
                "evidence": {"level": "none", "words": "none: " + res["not_testable"], "ends_per_winner": epw,
                             "folds_run": 0, "folds_skipped": len(folds),
                             "would_make_strong": _more(epw, ctx.players)}}
    for f in fams:
        f["passes"] = all(f.get("fold_results", []))
    passing = [f for f in fams if f["passes"]]
    once = [p for p, n in epw.items() if n < 2]
    if passing and not once and ran and len(epw) >= 2:          # addendum 1: two different winners seen
        level = "strong"
        words = (f"strong: every winner seen has at least two 'end' states; {len(passing)} famil"
                 f"{'y passes' if len(passing) == 1 else 'ies pass'} all {len(ran)} folds; the answer is the top one")
    elif passing:
        level = "weak"
        why = (f"{' and '.join(once)} {'was' if len(once) == 1 else 'were'} seen winning only once" if once else
               "only one player was seen winning")
        words = (f"weak: {len(passing)} famil{'y holds' if len(passing) == 1 else 'ies hold'} in every state, but "
                 f"{why} — {len(skipped)} fold{'' if len(skipped) == 1 else 's'} skipped (no other example of that "
                 f"winner), {len(ran)} run")
    else:
        level = "none"
        words = "none: no family holds in every state and every fold"
    rules = [_rule_of(f, ctx.players, kind) for f in fams[:SHOWN]]
    for r, f in zip(rules, fams):
        r["passes_every_fold"] = f["passes"]
    return {"name": name, "count": len(_cands(res)), "families_found": len(fams), "families": rules,
            "passing_count": len(passing),
            "passing": [dict(_rule_of(f, ctx.players, kind), passes_every_fold=True) for f in passing[:SHOWN]],
            "candidates": rules, "folds": folds,
            "evidence": {"level": level, "words": words, "ends_per_winner": epw, "folds_run": len(ran),
                         "folds_skipped": len(skipped),
                         "would_make_strong": None if level == "strong" else _more(epw, ctx.players)}}


def _more(epw: dict, players: int) -> str:
    """The states that would make the evidence strong, in the user's terms."""
    need = []
    if len(epw) < 2:
        unseen = next(f"P{k + 1}" for k in range(players) if f"P{k + 1}" not in epw)
        need.append(f"an 'end' won by {unseen} and another one won by {unseen}")
    need += [f"one more 'end' won by {p}" for p, n in epw.items() if n < 2]
    if not need:
        return "another labelled state (every winner already has two 'end' states)"
    return " and ".join(need)


def _verdict(out: dict, epw: dict) -> dict:
    t = out["templates"]
    strong = [k for k in ORDER if t[k]["evidence"]["level"] == "strong"]
    strong.sort(key=lambda k: (not t[k]["passing"][0].get("hinted"), ORDER.index(k)))
    levels = [t[k]["evidence"]["level"] for k in ORDER]
    out["evidence"] = "strong" if "strong" in levels else "weak" if "weak" in levels else "none"
    if strong:
        out["decided"] = True
        out["rule"] = t[strong[0]]["passing"][0]["rule"]
        out["template"] = strong[0]
        out["also_fits"] = [{"template": k, "rule": t[k]["passing"][0]["rule"]} for k in strong[1:]]
    else:
        out["decided"] = False
        more = _more(epw, out["players"])
        out["not_decided"] = {"passing": {k: t[k]["passing_count"] for k in ORDER},
                              "counts": {k: t[k]["count"] for k in ORDER},
                              "evidence": {k: t[k]["evidence"]["level"] for k in ORDER},
                              "would_make_strong": more, "would_split": more}
    return out


# --- hints (B97) -----------------------------------------------------------------------------------------------------
def load_hints(path: Path, system: str) -> tuple[list[dict], dict]:
    """The hints from a cheat list (through h7_cheat_hints) or from that tool's JSON. Unreadable / empty → no hints and
    the reason; the search then runs exactly as without. The returned info is counts only (no address, no text)."""
    import h7_cheat_hints as ch
    res = None
    try:
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict) and isinstance(data.get("hints"), list):
            res = {"hints": data["hints"], "codes": data.get("codes", 0), "skipped": data.get("skipped", {}),
                   "unreadable": data.get("unreadable")}
    except (OSError, UnicodeDecodeError, ValueError):
        pass
    if res is None:
        res = ch.read_hints(path, system)
    good = []
    for h in res["hints"]:
        try:
            good.append({"player": str(h["player"]), "address": int(str(h["address"]), 0), "bytes": int(h["bytes"]),
                         "value": h.get("value"), "kind": str(h.get("kind", "other")), "code": h.get("code"),
                         "pair_group": h.get("pair_group")})
        except (KeyError, TypeError, ValueError):
            continue
    info = {"read": len(good), "codes": res.get("codes", 0),
            "by_player_kind": ch.counts({"hints": good, "codes": res.get("codes", 0),
                                         "skipped": res.get("skipped", {})})["by_player_kind"]}
    if not good:
        info["why"] = res.get("unreadable") or "no per-player constant RAM write in the list"
    return good, info


def _hint_bytes(hints: list[dict], players: int) -> dict[int, dict[int, list[dict]]]:
    by: dict = {}
    for h in hints:
        k = _player(h["player"])
        if k is None or not 0 <= k < players:
            continue
        a = int(str(h["address"]), 0)
        for x in range(a, a + int(h["bytes"])):
            by.setdefault(k, {}).setdefault(x, []).append(h)
    return by


def _mark_hinted(fams: list[dict], hints: list[dict], players: int) -> None:
    """A family is hinted when one of its member reads covers, for some player k, a byte of a hint for player k."""
    if not hints:
        return
    by = _hint_bytes(hints, players)
    for f in fams:
        hit = []
        for (d, n, base) in f["keys"]:
            for k in range(players):
                for x in range(base + k * d, base + k * d + n):
                    hit += by.get(k, {}).get(x, [])
        if hit:
            f["hinted"] = True
            f["hinted_by"] = sorted({(h["kind"], h["code"]) for h in hit if h.get("code") is not None})
            f["hinted_by"] = [{"kind": kd, "code": c} for kd, c in f["hinted_by"]]
    fams.sort(key=_order)


def _hinted_sets(ctx: _Ctx, hints: list[dict]) -> list[dict]:
    """Every choice of one hint per player, the same kind and width, at a constant stride (2 players: every P1 / P2
    pair of a kind) — at most SETS_CAP, in a stable order (matching code names first)."""
    players, n = ctx.players, {1: len(ctx.V[0][1]), 2: len(ctx.V[0][2])}
    by: dict = {}
    for h in hints:
        k = _player(h["player"])
        if k is not None and 0 <= k < players and int(h["bytes"]) in (1, 2):
            by.setdefault((h["kind"], int(h["bytes"])), {}).setdefault(k, []).append(h)
    sets, seen = [], set()
    for (kind, size), per in sorted(by.items()):
        if len(per) < players:
            continue
        for h0 in per[0]:
            a0 = int(str(h0["address"]), 0)
            for h1 in per[1]:
                d = int(str(h1["address"]), 0) - a0
                if d == 0:
                    continue
                chosen = [h0, h1]
                for k in range(2, players):
                    nxt = [h for h in per.get(k, []) if int(str(h["address"]), 0) == a0 + k * d]
                    if not nxt:
                        break
                    chosen.append(nxt[0])
                if len(chosen) < players or (size, a0, d) in seen:
                    continue
                if not all(0 <= a0 + k * d < n[size] for k in range(players)):
                    continue
                seen.add((size, a0, d))
                groups = {h.get("pair_group") for h in chosen}
                sets.append({"size": size, "base": a0, "stride": d, "kind": kind,
                             "same_code_name": len(groups) == 1 and None not in groups,
                             "codes": [h.get("code") for h in chosen]})
    sets.sort(key=lambda s: (not s["same_code_name"], s["kind"], s["base"], s["stride"]))
    ctx.sets_found = len(sets)
    return sets[:SETS_CAP]


def _set_values(ctx: _Ctx, s: dict, i: int) -> list[int]:
    V = ctx.V[i][s["size"]]
    return [int(V[s["base"] + k * s["stride"]]) for k in range(ctx.players)]


def _set_failing(ctx: _Ctx, s: dict, idx: list[int]) -> list[int]:
    """The states where the set, read as a rule (winner max, none_when equal), is wrong; an unstable byte fails all."""
    ok = ctx.ok[s["size"]]
    if not all(ok[s["base"] + k * s["stride"]] for k in range(ctx.players)):
        return list(idx)
    bad = []
    for i in idx:
        v = _set_values(ctx, s, i)
        if ctx.label[i] == "begin":
            if len(set(v)) != 1:
                bad.append(i)
        else:
            w = ctx.win[i]
            if not all(v[w] > x for k, x in enumerate(v) if k != w):
                bad.append(i)
    return bad


def _sets_holding(ctx: _Ctx, idx, begins, ends) -> list[dict] | dict:
    if not getattr(ctx, "sets", None):
        return {"not_testable": "no hints given (or none pairs up per player)"}
    out = []
    for s in ctx.sets:
        if not _set_failing(ctx, s, idx):
            out.append({"size": s["size"], "base": s["base"], "stride": s["stride"], "kind": s["kind"],
                        "same_code_name": s["same_code_name"],
                        "values": [_set_values(ctx, s, i) for i in idx],
                        "all_vary": all(len({_set_values(ctx, s, i)[k] for i in idx}) > 1 for k in range(ctx.players))})
    return out


def _sets_report(ctx: _Ctx, fams: dict) -> dict:
    """Every hinted set tested directly, with its values in every state and where it fails (B97)."""
    sets = getattr(ctx, "sets", None) or []
    every = list(range(len(ctx.states)))
    rows = []
    for s in sets:
        bad = _set_failing(ctx, s, every)
        key = (s["stride"], s["size"], s["base"])
        found_by = [k for k in ("a", "b", "b2") for f in fams[k] if key in f["keys"]]
        rows.append({"rule": {"players": [{"name": f"P{k + 1}", "address": hex(s["base"] + k * s["stride"]),
                                           "bytes": s["size"], "endian": "little"} for k in range(ctx.players)],
                              "winner": "max", "memory": "ram", "none_when": "equal"},
                     "kind": s["kind"], "same_code_name": s["same_code_name"], "codes": s["codes"],
                     "values_per_state": [_set_values(ctx, s, i) for i in every],
                     "holds": not bad, "failing_states": bad, "found_by": sorted(set(found_by))})
    rows.sort(key=lambda r: (not r["holds"], not r["same_code_name"]))
    return {"found": getattr(ctx, "sets_found", 0), "tested": len(sets), "cap": SETS_CAP,
            "hold": sum(r["holds"] for r in rows), "sets": rows[:SHOWN]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--content", required=True, type=Path)
    ap.add_argument("--system", required=True, choices=sorted(MEMORY))
    ap.add_argument("--states", required=True, type=Path)
    ap.add_argument("--players", type=int)
    ap.add_argument("--loads", type=int, default=3)
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--hints", type=Path, help="B97: a cheat list (.cht, the hub's stored form) or h7_cheat_hints' JSON")
    a = ap.parse_args(argv)
    try:
        listed = json.loads(a.states.read_text())
        named = [_player(s.get("winner")) for s in listed if s.get("winner")]
        players = a.players or max([1] + [w + 1 for w in named if w is not None])
        players = max(players, 2)
        if not 2 <= players <= 4:
            raise SearchError("2 to 4 players")
        t0 = time.monotonic()
        states = []
        for s in listed:
            mem, stable = read_state(a.content, a.system, Path(s["state"]), a.loads)
            states.append({"label": s["label"], "winner": s.get("winner"), "mem": mem, "stable": stable})
        hints, hinfo = load_hints(a.hints, a.system) if a.hints else ([], None)
        t1 = time.monotonic()
        out = search(states, players, hints)
        if hinfo is not None:
            out["hints"] = hinfo
        if a.time:
            out["seconds"] = {"read": round(t1 - t0, 2), "search": round(time.monotonic() - t1, 2)}
        print(json.dumps(out))
        return 0
    except (SearchError, proof.ProofError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
