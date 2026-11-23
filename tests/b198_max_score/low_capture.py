"""B198's tests: a made-up low-scoring title's final screen (no title; every picture made-up). The add-a-game tool's
picture source for it (PARTY_ADD_GAME_CAPTURE=low_capture:capture). A made-up kept state is JSON:

  {"kind": "end_low", "s": [P1's final, P2's final], "look": m}
        the final screen: a heading of six blocks and each side's name as four blocks (strings of several glyphs);
        eight emblems whose place, size and grey change by match (`look`); each side's final large (B178's 5 x 7
        font x4) on the plain background, P1 left, P2 right. Held, then a loading screen, then the game moves on
        (score_capture's timing).
  begin / other / ...  as score_capture.

Disclosed (the record): no fixed single shape but the two numbers. On B178's own made-up final screen (a dark panel
under each number, fixed emblems) single-digit finals are not found: B178's place choice takes a fixed single shape
(a panel) — every reading fits it, and it is the tallest. That is B178's limit, not B198's; T92 may meet it."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "b178_score_kind"))
import score_capture as sc  # noqa: E402

W, H = sc.W, sc.H
FINAL_X = (200, 440)
TOP = 260


def low_screen(s, look: int, rng) -> Image.Image:
    im = Image.fromarray(sc.BACK.copy(), "L")
    d = ImageDraw.Draw(im)
    for i in range(6):                                                  # the heading: six blocks, one string
        d.rectangle((150 + 58 * i, 20, 194 + 58 * i, 50), fill=210)
    for cx in FINAL_X:                                                  # the sides' names: four blocks each
        for i in range(4):
            d.rectangle((cx - 64 + 34 * i, 200, cx - 42 + 34 * i, 214), fill=170)
    m = np.random.default_rng(9800 + look)
    for _k in range(4):                                                 # the emblems: place and size by match
        x, y, r = int(m.integers(10, 480)), int(m.integers(64, 150)), int(m.integers(30, 75))
        d.ellipse((x, y, x + 2 * r, y + min(r, 45)), fill=int(m.integers(20, 240)))
        x, y = int(m.integers(10, 560)), int(m.integers(330, 400))      # and below the numbers
        d.rectangle((x, y, x + int(m.integers(30, 80)), y + int(m.integers(20, 60))), fill=int(m.integers(20, 240)))
    for cx, v in zip(FINAL_X, s):
        sc.number(d, cx, TOP, str(int(v)))
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def picture(st: dict, t: float, k: int, rng) -> Image.Image:
    if st["kind"] == "end_low":
        if t >= sc.HOLD_S + sc.LOADING_S:
            return sc.other_screen(k, rng)
        if t >= sc.HOLD_S:
            return sc.loading_screen(rng)
        return low_screen(st["s"], st.get("look", 0), rng)
    return sc.picture(st, t, k, rng)


def capture(state_path, binding, out_dir, seconds, every):
    st = json.loads(Path(state_path).read_text())
    rng = np.random.default_rng(198 + 7 * int(st.get("look", 0)) + 101 * int(st.get("n", 0)) + len(st["kind"]))
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        t = round(k * every, 2)
        name = f"f{k:04d}.png"
        picture(st, t, k, rng).save(Path(out_dir) / name)
        rows.append((t, name))
    return rows
