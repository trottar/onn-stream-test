"""B200's tests: a made-up final screen whose numbers are drawn with two digits, a leading 0 (no title; every picture
made-up) — the add-a-game tool's picture source for it (PARTY_ADD_GAME_CAPTURE=pad_capture:capture). A made-up kept
state is JSON:

  {"kind": "end_pad", "s": [P1's final, P2's final], "q": [[P1's cells], [P2's cells]], "look": m}
        the final screen, shaped like the one the queue settled: each side's final large and padded ("03"), either side
        of a box of five period rows — P1's cell, a heading (a digit-like glyph, the same in every save), P2's cell —
        each cell small and padded ("01"), a blank cell a flat dash; under it a stats table of "00" (the same in every
        save: a panel shaped like digits); emblems whose place, size and grey change by match (`look`). Every final
        "0" has a hollow, the same shape in every save. Held, then a loading screen, then the game moves on
        (score_capture's timing).
  begin / other / ...  as score_capture.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "b178_score_kind"))
import score_capture as sc  # noqa: E402

W, H = sc.W, sc.H
FINAL_X = (190, 450)
FINAL_TOP = 120
BOX = (270, 96, 370, 196)
CELL_X = (292, 348)
HEAD = "12121"                                   # each row's heading: a digit-like glyph, the same in every save
FONT = {**sc.FONT, "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"]}   # a 0 with a plain hollow


def number(d: ImageDraw.ImageDraw, cx: int, top: int, text: str, scale: int = 4, fill: int = 235) -> None:
    """score_capture's `number` in this screen's font (its 0 hollow, as T92's)."""
    gw, gap = 5 * scale, scale
    x = cx - (len(text) * gw + (len(text) - 1) * gap) // 2
    for ch in text:
        for r, row in enumerate(FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    d.rectangle((x + c * scale, top + r * scale, x + (c + 1) * scale - 1, top + (r + 1) * scale - 1),
                                fill=fill)
        x += gw + gap


def pad(v) -> str:
    return f"{int(v):02d}"


def pad_screen(s, q, look: int, rng) -> Image.Image:
    im = Image.fromarray(sc.BACK.copy(), "L")
    d = ImageDraw.Draw(im)
    m = np.random.default_rng(20000 + look)
    for _k in range(3):                                                 # the emblems: place and size by match
        x, y, r = int(m.integers(10, 500)), int(m.integers(8, 40)), int(m.integers(25, 60))
        d.ellipse((x, y, x + 2 * r, y + min(r, 40)), fill=int(m.integers(20, 240)))
        x, y = int(m.integers(10, 560)), int(m.integers(400, 440))
        d.rectangle((x, y, x + int(m.integers(30, 80)), y + int(m.integers(15, 35))), fill=int(m.integers(20, 240)))
    d.rectangle(BOX, outline=200, width=3)                              # the box
    for i in range(5):
        top = BOX[1] + 6 + 18 * i
        number(d, (BOX[0] + BOX[2]) // 2, top, HEAD[i], scale=2, fill=200)
        for k, cx in enumerate(CELL_X):
            v = q[k][i] if k < len(q) and i < len(q[k]) else None
            if v is None:
                d.rectangle((cx - 6, top + 6, cx + 6, top + 7), fill=220)   # a blank cell: a flat dash
            else:
                number(d, cx, top, pad(v), scale=2, fill=235)
    for i in range(4):                                                  # the stats table: "00" for both sides
        for cx in FINAL_X:
            number(d, cx, 250 + 30 * i, "00", scale=2, fill=225)
    for cx, v in zip(FINAL_X, s):
        number(d, cx, FINAL_TOP, pad(v), scale=6)
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def picture(st: dict, t: float, k: int, rng) -> Image.Image:
    if st["kind"] == "end_pad":
        if t >= sc.HOLD_S + sc.LOADING_S:
            return sc.other_screen(k, rng)
        if t >= sc.HOLD_S:
            return sc.loading_screen(rng)
        return pad_screen(st["s"], st["q"], st.get("look", 0), rng)
    return sc.picture(st, t, k, rng)


def capture(state_path, binding, out_dir, seconds, every):
    st = json.loads(Path(state_path).read_text())
    rng = np.random.default_rng(200 + 7 * int(st.get("look", 0)) + 101 * int(st.get("n", 0)) + len(st["kind"]))
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        t = round(k * every, 2)
        name = f"f{k:04d}.png"
        picture(st, t, k, rng).save(Path(out_dir) / name)
        rows.append((t, name))
    return rows
