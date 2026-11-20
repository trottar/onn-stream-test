"""B171's tests: the add-a-game tool's picture source replaced by made-up near-alike end screens
(PARTY_ADD_GAME_CAPTURE=near_capture:capture). A made-up kept state is JSON {"kind": k, "look": m, "far": bool}:

  start   the select screen before anyone picks: a still textured screen, both portraits empty, the tally 0-0
  end_P1 / end_P2   the same screen after a match: the two portraits of the match's characters (their shades drawn
          from the look `m`: the same look = the same characters), a cursor, the tally 1-0 / 0-1 in 2-px segments —
          the endings differ only in a few pixels; `far`: a large banner on the winner's side as well (far apart)
  same    an ending whose screen does not show who won (the tally 1-1 for either player)
  other / mid   the middle of a match (moving shapes on another background)

Every frame of a save is the same picture with +-2 noise (a still save); a picture every other 0.5-s tick (about half
the ticks give one on the hub, B167). CALLS lists every capture (the state's kind and look). Every picture made-up."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

W, H = 320, 240
TALLY = {"start": "00", "end_P1": "10", "end_P2": "01", "same": "11"}
SEG = {"0": "abcdef", "1": "bc"}
_g = np.random.default_rng(88)
BACK = np.clip(np.add.outer(np.linspace(20, 140, H), np.linspace(0, 80, W))
               + _g.integers(-25, 26, size=(H // 8, W // 8)).repeat(8, 0).repeat(8, 1), 0, 255).astype(np.uint8)
CALLS: list = []


def state(kind: str, look: int = 0, far: bool = False, n: int = 0) -> str:
    """`n`: another save of the same screen (other bytes, the same picture)."""
    return json.dumps({"kind": kind, "look": look, "far": far, "n": n})


def _digit(d, x, y, ch, s=2):
    w, h = 4 * s, 7 * s
    boxes = {"a": (x, y, x + w, y + s), "b": (x + w - s, y, x + w, y + h // 2), "c": (x + w - s, y + h // 2, x + w, y + h),
             "d": (x, y + h - s, x + w, y + h), "e": (x, y + h // 2, x + s, y + h), "f": (x, y, x + s, y + h // 2)}
    for k in SEG[ch]:
        d.rectangle(boxes[k], fill=235)


def screen(kind: str, look: int, rng, far: bool = False, cur=None, mark: int = 0) -> Image.Image:
    im = Image.fromarray(BACK.copy(), "L")
    d = ImageDraw.Draw(im)
    d.rectangle((120, 90, 200, 125), fill=90)                     # the tally's panel
    m = np.random.default_rng(1000 + look)
    for x0 in (10, 230):                                          # the two portraits: the match's characters
        if kind == "start":
            d.rectangle((x0, 40, x0 + 80, 180), fill=60)
            continue
        d.rectangle((x0, 40, x0 + 80, 180), fill=int(m.integers(20, 230)))
        d.ellipse((x0 + 10, 60, x0 + 70, 120), fill=int(m.integers(20, 230)))
        d.rectangle((x0 + 20, 130, x0 + 60, 170), fill=int(m.integers(20, 230)))
    cx = int(m.integers(0, 4)) if cur is None else int(cur)      # the cursor (`cur`: placed by hand)
    d.rectangle((110 + 25 * cx, 190, 130 + 25 * cx, 210), fill=200)
    t = TALLY[kind]
    _digit(d, 140, 100, t[0])
    _digit(d, 170, 100, t[1])
    if mark and kind == "start":                                  # a large mark the begin alone shows (B175)
        d.rectangle((0, 0, mark, 34), fill=250)
    if far and kind in ("end_P1", "end_P2"):
        x = 100 if kind == "end_P1" else 160
        d.rectangle((x, 30, x + 60, 90), fill=250)
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def other(i: int, rng) -> Image.Image:
    im = Image.new("L", (W, H), int(rng.integers(100, 180)))
    d = ImageDraw.Draw(im)
    for _ in range(6):
        x, y = int(rng.integers(0, W - 60)), int(rng.integers(0, H - 60))
        d.ellipse((x, y, x + int(rng.integers(20, 90)), y + int(rng.integers(20, 90))), fill=int(rng.integers(0, 255)))
    return im


def capture(state_path, binding, out_dir, seconds, every):
    s = json.loads(Path(state_path).read_text())
    CALLS.append((s["kind"], s["look"]))
    rng = np.random.default_rng(171 + 7 * s["look"] + len(s["kind"]))
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        name = f"f{k:04d}.png"
        pic = other(k, rng) if s["kind"] in ("other", "mid") else screen(s["kind"], s["look"], rng, s.get("far", False), s.get("cur"), s.get("mark", 0))
        pic.save(Path(out_dir) / name)
        rows.append((round(k * every, 2), name))
    return rows


def fails(state_path, binding, out_dir, seconds, every):
    """A picture source that does not run (learn: a "pictures made" cell, never a line)."""
    raise RuntimeError("made-up: the picture source did not start")
