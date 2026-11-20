"""B178's tests: made-up score screens (no title; every picture made-up). The add-a-game tool's picture source for a
made-up `score` title (PARTY_ADD_GAME_CAPTURE=score_capture:capture), and the frames B114's harness shows.

A made-up kept state is JSON {"kind": k, "s": [P1's number, P2's number], "look": m, "n": i}:

  begin       the select screen: a still layout, no numbers
  other       the middle of a match: moving shapes (every picture another)
  mid_score   the middle of a match with a score bug at the top showing `s` (moving shapes; never the final screen)
  end         the final screen: a fixed frame and headings; two emblems and two columns of small stats that change by
              match (`look`); each side's number large, centred in its panel (P1 left, P2 right) in a 5 x 7 pixel
              font drawn x4; held HOLD_S seconds, then a loading screen for LOADING_S, then moving pictures (as T90's
              final screen is held, then loads, then the game moves on)
  end_offset  the final screen with every number one row lower (a layout that is not the learnt one)

Every frame of a still screen is the same picture with +-2 noise; a picture every other 0.5-s tick (B167's cadence).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

W, H = 640, 480
HOLD_S = 9.0
LOADING_S = 4.0                  # then a loading screen, then the game moves on (as T90's runs do)
FONT = {"0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
        "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
        "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
        "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
        "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
        "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
        "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
        "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
        "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
        "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"]}
_g = np.random.default_rng(178)
BACK = np.clip(np.add.outer(np.linspace(30, 120, H), np.linspace(0, 60, W))
               + _g.integers(-20, 21, size=(H // 16, W // 16)).repeat(16, 0).repeat(16, 1), 0, 255).astype(np.uint8)
CALLS: list = []


def state(kind: str, s=(0, 0), look: int = 0, n: int = 0) -> str:
    return json.dumps({"kind": kind, "s": list(s), "look": look, "n": n})


def number(d: ImageDraw.ImageDraw, cx: int, top: int, text: str, scale: int = 4, fill: int = 235) -> None:
    """`text` centred on cx, its top at `top`, in the 5 x 7 font drawn `scale` times larger, one column apart."""
    gw, gap = 5 * scale, scale
    x = cx - (len(text) * gw + (len(text) - 1) * gap) // 2
    for ch in text:
        for r, row in enumerate(FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    d.rectangle((x + c * scale, top + r * scale, x + (c + 1) * scale - 1, top + (r + 1) * scale - 1),
                                fill=fill)
        x += gw + gap


def _noise(im: Image.Image, rng) -> Image.Image:
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def end_screen(s, look: int, rng, offset: int = 0) -> Image.Image:
    im = Image.fromarray(BACK.copy(), "L")
    d = ImageDraw.Draw(im)
    d.rectangle((140, 16, 500, 56), fill=210)                           # the heading
    for x in range(150, 490, 24):
        d.rectangle((x, 28, x + 12, 44), fill=60)
    for i in range(8):                                                  # the row labels (fixed)
        d.rectangle((250, 90 + 26 * i, 390, 106 + 26 * i), fill=170)
        d.rectangle((262, 95 + 26 * i, 378, 101 + 26 * i), fill=80)
    m = np.random.default_rng(5000 + look)
    for x0 in (40, 480):                                                # the emblems: the match's sides
        d.ellipse((x0, 80, x0 + 120, 200), fill=int(m.integers(30, 220)))
        d.rectangle((x0 + 30, 110, x0 + 90, 170), fill=int(m.integers(30, 220)))
    for i in range(8):                                                  # the small stats: change every match
        for cx in (200, 440):
            number(d, cx, 92 + 26 * i, str(int(m.integers(0, 400))), scale=2, fill=225)
    for cx, v in ((100, s[0]), (540, s[1])):                            # each side's number, centred in its panel
        d.rectangle((cx - 60, 250, cx + 60, 330), fill=35)
        number(d, cx, 276 + offset, str(int(v)))
    return _noise(im, rng)


def begin_screen(rng) -> Image.Image:
    im = Image.fromarray(BACK.copy(), "L")
    d = ImageDraw.Draw(im)
    d.rectangle((60, 40, 580, 120), fill=150)
    for k in range(4):
        d.rectangle((70 + 130 * k, 180, 170 + 130 * k, 400), fill=60 + 40 * k)
    return _noise(im, rng)


def loading_screen(rng) -> Image.Image:
    im = Image.new("L", (W, H), 90)
    ImageDraw.Draw(im).rectangle((220, 220, 420, 260), fill=200)
    return _noise(im, rng)


def other_screen(i: int, rng, s=None) -> Image.Image:
    im = Image.new("L", (W, H), int(rng.integers(100, 170)))
    d = ImageDraw.Draw(im)
    for _ in range(8):
        x, y = int(rng.integers(0, W - 120)), int(rng.integers(60, H - 120))
        d.ellipse((x, y, x + int(rng.integers(40, 160)), y + int(rng.integers(40, 160))), fill=int(rng.integers(0, 255)))
    if s is not None:                                                   # a score bug during play
        d.rectangle((220, 6, 420, 50), fill=30)
        number(d, 280, 14, str(int(s[0])), scale=4)
        number(d, 360, 14, str(int(s[1])), scale=4)
    return im


def picture(st: dict, t: float, k: int, rng) -> Image.Image:
    kind = st["kind"]
    if kind == "begin":
        return begin_screen(rng)
    if kind == "other":
        return other_screen(k, rng)
    if kind == "mid_score":
        return other_screen(k, rng, st["s"])
    if t >= HOLD_S + LOADING_S:
        return other_screen(k, rng)
    if t >= HOLD_S:
        return loading_screen(rng)
    return end_screen(st["s"], st["look"], rng, offset=4 if kind == "end_offset" else 0)


# B114's harness: B103's fake RetroArch state {"P1": code, "P2": n} names the screen (the fake shows token sc<code>)
CODES = {300: {"kind": "begin"}, 301: {"kind": "other"},
         310: {"kind": "end", "s": [21, 14], "look": 1}, 311: {"kind": "end", "s": [42, 12], "look": 2},
         312: {"kind": "end", "s": [14, 24], "look": 3}, 313: {"kind": "end", "s": [12, 41], "look": 4},
         320: {"kind": "end", "s": [14, 14], "look": 5},      # a tie
         321: {"kind": "end", "s": [17, 3], "look": 6},       # digits the four saves never show
         322: {"kind": "mid_score", "s": [21, 14]}}
SCORES = {c: v["s"] for c, v in CODES.items() if "s" in v}


def frames(folder: Path) -> None:
    """Six pictures of every screen in CODES for the harness's scripted pictures (the still screens as held)."""
    for code, st in CODES.items():
        rng = np.random.default_rng(900 + code)
        for i in range(6):
            picture({"look": 0, **st}, 0.0, i, rng).save(Path(folder) / f"sc{code}_{i}.png")


def capture_codes(state_path, binding, out_dir, seconds, every):
    st = json.loads(Path(state_path).read_text())
    return _capture({"look": 0, **CODES[int(st["P1"])], "n": int(st.get("P2") or 0)}, out_dir, seconds, every)


def capture(state_path, binding, out_dir, seconds, every):
    return _capture(json.loads(Path(state_path).read_text()), out_dir, seconds, every)


def _capture(st: dict, out_dir, seconds, every):
    CALLS.append((st["kind"], tuple(st.get("s") or ())))
    rng = np.random.default_rng(178 + 7 * int(st.get("look", 0)) + 101 * int(st.get("n", 0)) + len(st["kind"]))
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        t = round(k * every, 2)
        name = f"f{k:04d}.png"
        picture(st, t, k, rng).save(Path(out_dir) / name)
        rows.append((t, name))
    return rows
