#!/usr/bin/env python3
"""H7 (B94): from a few labelled save states, find the memory that says who won — candidate rules in B93's rule JSON.

    python3 tools/h7_rule_search.py --content <game> --system ps1|snes --states <states.json> [--players 2] [--loads 3]

states.json: [{"state": "<file>", "label": "begin" | "end", "winner": "P1" | "P2" | ... | null}, ...]  (2 to 4 players)

Each state is loaded PAUSED in a headless RetroArch (B93's session: temp folders, the hub's saves untouched) --loads
times; its whole main memory is read in 16 KiB chunks; an address that differs between loads of one state is dropped.
Three templates are searched, each candidate holding in EVERY labelled state:
  (a) a per-player counter — one field per player at a constant stride; every value <= 31; all equal at "begin"; at
      "end" the winner's strictly the largest and above its "begin" value;
  (b) a per-player level that empties — all equal and >= 8 at "begin"; at "end" none above its "begin" value, the
      winner's strictly the largest and > 0, every loser at 0;
  (c) a single winner field — constant over "begin"; one value per winner at "end", different winners different
      values, the "begin" value none of them (needs ends won by at least two players).
The answer is "decided" only when a template leaves exactly one candidate; otherwise the counts and the state that would
split them. It never names a rule when more than one fits. Prints one JSON document.
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
def _fields(mem: bytes, size: int) -> np.ndarray:
    b = np.frombuffer(mem, dtype=np.uint8).astype(np.int32)
    if size == 1:
        return b
    return b[:-1] | (b[1:] << 8)


def _stable(stable: np.ndarray, size: int) -> np.ndarray:
    return stable if size == 1 else (stable[:-1] & stable[1:])


def _player(w: str | None) -> int | None:
    return None if w is None else int(str(w).lstrip("Pp")) - 1


def search(states: list[dict], players: int) -> dict:
    """states: [{"label", "winner", "mem": bytes, "stable": bool array}] — the pure search (no emulator)."""
    begins = [i for i, s in enumerate(states) if s["label"] == "begin"]
    ends = [(i, _player(s["winner"])) for i, s in enumerate(states) if s["label"] == "end"]
    if not begins or not ends:
        raise SearchError("at least one 'begin' and one 'end' state are needed")
    if any(w is None or not 0 <= w < players for _, w in ends):
        raise SearchError("every 'end' state needs its winner (P1 … P%d)" % players)
    winners = sorted({w for _, w in ends})
    out: dict = {"players": players, "states": [{"label": s["label"], "winner": s["winner"]} for s in states],
                 "unstable_bytes": int(sum(int((~s["stable"]).sum()) for s in states)), "templates": {}}
    block: dict[str, list] = {"a": [], "b": []}
    taken: set[int] = set()
    for kind in ("a", "b"):
        found = []
        for size in (1, 2):
            V = [_fields(s["mem"], size) for s in states]
            ok = np.ones(len(V[0]), dtype=bool)
            for s in states:
                ok &= _stable(s["stable"], size)
            if kind == "a":
                small = ok.copy()
                for v in V:
                    small &= v <= SMALL
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
                        m &= (V[e] > 0) if w == k else (V[e] == 0)
                    masks.append(m)
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
                vals = [np.stack([V[i][base + k * d] for k in range(players)]) for i in range(len(states))]
                keep = np.ones(len(base), dtype=bool)
                for b in begins:
                    keep &= np.all(vals[b] == vals[b][0], axis=0)
                for e, w in ends:
                    others = np.delete(vals[e], w, axis=0)
                    keep &= np.all(vals[e][w] > others, axis=0)
                for a in base[keep]:
                    found.append({"size": size, "base": int(a), "stride": d,
                                  "values": [[int(vals_i) for vals_i in [V[i][int(a) + k * d] for k in range(players)]]
                                             for i in range(len(states))]})
        merged = _merge(found, states, players)
        merged.sort(key=lambda c: (not c["all_vary"], c["base"] % c["size"] != 0, c["stride"] % 4 != 0, c["stride"],
                                   c["base"]))
        block[kind] = merged
        for c in merged:
            for k in range(players):
                taken.update(range(c["base"] + k * c["stride"], c["base"] + k * c["stride"] + c["size"]))
    for kind, label in (("a", "a per-player counter"), ("b", "a per-player level that empties")):
        cands = block[kind]
        out["templates"][kind] = {"name": label, "count": len(cands),
                                  "candidates": [_rule_of(c, players, kind) for c in cands[:SHOWN]]}
    out["templates"]["c"] = _single_field(states, begins, ends, winners, taken)
    return _verdict(out, ends, winners, players)


def _merge(found: list[dict], states: list[dict], players: int) -> list[dict]:
    """Reads of the same memory are one candidate: two candidates whose CHANGING bytes (a byte that differs between the
    states) are the same addresses are one field read two ways — a 1- and a 2-byte read, or a 2-byte read one byte early
    (the value × 256). The aligned, wider read is kept. `all_vary`: every player's field changes in some state."""
    mems = np.stack([np.frombuffer(s["mem"], dtype=np.uint8) for s in states])
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


def _rule_of(c: dict, players: int, kind: str) -> dict:
    rule = {"players": [{"name": f"P{k + 1}", "address": hex(c["base"] + k * c["stride"]), "bytes": c["size"],
                         "endian": "little"} for k in range(players)],
            "winner": "max", "memory": "ram", "none_when": "equal"}
    why = ("the same field per player at stride %#x: equal at every 'begin', the winner's the largest at every 'end'"
           if kind == "a" else
           "a level per player at stride %#x: equal and high at every 'begin', the losers at 0 at every 'end'") % c["stride"]
    return {"rule": rule, "why": why, "values_per_state": c["values"], "every_player_changes": c["all_vary"],
            **({"also_read_as": c["also_read_as"]} if c.get("also_read_as") else {})}


def _single_field(states, begins, ends, winners, taken) -> dict:
    name = "a single winner field"
    if len(winners) < 2:
        return {"name": name, "count": None, "candidates": [],
                "not_testable": "needs 'end' states won by at least two different players"}
    cands = []
    for size in (1, 2):
        V = [_fields(s["mem"], size) for s in states]
        ok = np.ones(len(V[0]), dtype=bool)
        for s in states:
            ok &= _stable(s["stable"], size)
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
        for a in np.nonzero(ok)[0]:
            if any(int(a) + i in taken for i in range(size)):
                continue
            cands.append({"size": size, "address": int(a),
                          "values": {f"P{w + 1}": int(V[rep[w]][a]) for w in ws}, "begin": int(V[begins[0]][a])})
    seen, uniq = set(), []
    for c in sorted(cands, key=lambda c: (-c["size"], c["address"])):
        key = (c["address"], json.dumps(c["values"]), c["begin"])
        if (c["address"], c["begin"]) in seen:
            continue
        seen.add((c["address"], c["begin"]))
        uniq.append(c)
    uniq.sort(key=lambda c: (c["address"] % c["size"] != 0, c["address"]))
    return {"name": name, "count": len(uniq), "candidates": [
        {"rule": {"players": [], "address": hex(c["address"]), "bytes": c["size"], "endian": "little",
                  "values": c["values"], "none_value": c["begin"], "memory": "ram"},
         "why": "one value per winner at 'end', another at 'begin'"} for c in uniq[:SHOWN]]}


def _verdict(out: dict, ends, winners, players) -> dict:
    ones = [k for k in ("a", "b", "c") if out["templates"][k].get("count") == 1]
    if ones:
        out["decided"] = True
        out["rule"] = out["templates"][ones[0]]["candidates"][0]["rule"]
        out["template"] = ones[0]
        out["also_fits"] = [{"template": k, "rule": out["templates"][k]["candidates"][0]["rule"]} for k in ones[1:]]
    else:
        out["decided"] = False
        unseen = [f"P{k + 1}" for k in range(players) if k not in winners]
        repeat = [f"P{w + 1}" for w in winners if sum(1 for _, x in ends if x == w) < 2]
        out["not_decided"] = {
            "counts": {k: out["templates"][k]["count"] for k in ("a", "b", "c")},
            "would_split": (f"an 'end' state won by {unseen[0]}" if unseen else
                            f"a second 'end' state won by {repeat[0]}" if repeat else "another labelled state")}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--content", required=True, type=Path)
    ap.add_argument("--system", required=True, choices=sorted(MEMORY))
    ap.add_argument("--states", required=True, type=Path)
    ap.add_argument("--players", type=int)
    ap.add_argument("--loads", type=int, default=3)
    ap.add_argument("--time", action="store_true")
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
        t1 = time.monotonic()
        out = search(states, players)
        if a.time:
            out["seconds"] = {"read": round(t1 - t0, 2), "search": round(time.monotonic() - t1, 2)}
        print(json.dumps(out))
        return 0
    except (SearchError, proof.ProofError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
