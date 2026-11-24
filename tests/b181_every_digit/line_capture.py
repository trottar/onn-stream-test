"""B181's tests: made-up final screens with a line score (no title; every picture made-up). The add-a-game tool's
picture source for made-up `score` titles (PARTY_ADD_GAME_CAPTURE=line_capture:capture). A made-up kept state is JSON:

  {"kind": "end_line", "q": [[P1's cells], [P2's cells]], "s": [P1's final, P2's final], "look": m}
        the final screen: a fixed heading and row labels; two emblems that change by match; a line-score table — a row
        per side, its cells (None = blank) in fixed columns, the final in the last column, a separator bar of the
        digits' own height between columns (the same glyph whatever the score: B181 must refuse it as a column);
        every number in the 5 x 7 font drawn x3, centred in its column. Held HOLD_S seconds, then a loading screen,
        then the game moves on (score_capture's timing).
  {"kind": "end_short", ...}  the same screen held only SHORT_S seconds, then one still screen for the rest of the run
        (B184: the old anchor took the later screen, the most-held)
  begin / other / end ...    as score_capture.

Every frame of a still screen is the same picture with +-2 noise; a picture every other 0.5-s tick (B167's cadence)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "b178_score_kind"))
import score_capture as sc  # noqa: E402

W, H = sc.W, sc.H
COLS = (190, 250, 310, 370, 430, 490)          # Q1-Q4, OT1, OT2 (centres, px at 640 x 480)
FINAL_X = 570
ROWS = (300, 360)                              # the two sides' rows (tops)
SCALE = 3
SHORT_S = 4.0


def line_screen(q, s, look: int, rng, moved: int = 0) -> Image.Image:
    im = Image.fromarray(sc.BACK.copy(), "L")
    d = ImageDraw.Draw(im)
    d.rectangle((140, 16, 500, 56), fill=210)                          # the heading
    for i in range(6):                                                 # the row labels (fixed)
        d.rectangle((250, 80 + 26 * i, 390, 96 + 26 * i), fill=170)
    m = np.random.default_rng(7000 + look)
    for x0 in (40, 480):                                               # the emblems: the match's sides
        d.ellipse((x0, 80, x0 + 110, 190), fill=int(m.integers(30, 220)))
    d.rectangle((20, 280, 620, 400), fill=30)                          # the table
    for k, top in enumerate(ROWS):
        d.rectangle((30, top, 150, top + 20), fill=int(m.integers(90, 200)))       # the side's name (a block)
        for x in [c + 30 for c in COLS] + [FINAL_X - 50]:              # the separators: the digits' own height
            d.rectangle((x, top, x + 2, top + 7 * SCALE - 1), fill=200)
        for cx, v in zip(COLS, q[k]):
            if v is not None:
                sc.number(d, cx, top + moved, str(int(v)), scale=SCALE, fill=235)
        sc.number(d, FINAL_X, top + moved, str(int(s[k])), scale=SCALE, fill=235)
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def picture(st: dict, t: float, k: int, rng) -> Image.Image:
    kind = st["kind"]
    if kind == "end_short":
        if t >= SHORT_S:
            return _still(rng)
        return line_screen(st["q"], st["s"], st.get("look", 0), rng)
    if kind == "end_line_moved":                    # the final screen whose numbers sit a few px off their line
        return line_screen(st["q"], st["s"], st.get("look", 0), rng, moved=6)  # (B182: a number not read)
    if kind == "end_line":
        if t >= sc.HOLD_S + sc.LOADING_S:
            return sc.other_screen(k, rng)
        if t >= sc.HOLD_S:
            return sc.loading_screen(rng)
        return line_screen(st["q"], st["s"], st.get("look", 0), rng)
    return sc.picture(st, t, k, rng)


def _still(rng) -> Image.Image:
    """A screen held for the rest of the run after a short final screen (a menu the game stays on)."""
    im = Image.new("L", (W, H), 70)
    ImageDraw.Draw(im).rectangle((100, 100, 540, 380), fill=150)
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def capture(state_path, binding, out_dir, seconds, every):
    st = json.loads(Path(state_path).read_text())
    seed = [181, int(st.get("look", 0)), int(st.get("n", 0)), len(st["kind"])]   # B212: noise drawn per picture
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        t = round(k * every, 2)
        name = f"f{k:04d}.png"
        picture(st, t, k, np.random.default_rng(seed + [k])).save(Path(out_dir) / name)
        rows.append((t, name))
    return rows


# B114's harness (B178's scenario, from B181 on): B103's fake RetroArch state {"P1": code, "P2": n} names the screen
_ = None
CODES = {300: {"kind": "begin"}, 301: {"kind": "other"},
         310: {"kind": "end_line", "q": [[1, 2, 3, 4, _, _], [0, 5, 0, 1, _, _]], "s": [10, 6], "look": 1},
         311: {"kind": "end_line", "q": [[7, 8, 9, 0, _, _], [6, 5, 4, 3, _, _]], "s": [24, 18], "look": 2},
         312: {"kind": "end_line", "q": [[2, 0, 1, 3, _, _], [9, 8, 7, 0, _, _]], "s": [6, 24], "look": 3},
         313: {"kind": "end_line", "q": [[5, 6, 0, 0, _, _], [7, 8, 9, 1, _, _]], "s": [11, 25], "look": 4},
         320: {"kind": "end_line", "q": [[7, 7, 0, 0, _, _], [0, 7, 7, 0, _, _]], "s": [14, 14], "look": 5},   # a tie
         321: {"kind": "end_line_moved", "q": [[3, 0, 0, 0, _, _], [0, 0, 0, 0, _, _]], "s": [3, 0], "look": 6}}
SCORES = {c: v["s"] for c, v in CODES.items() if "s" in v}


def text_of(code: int) -> str:
    st = CODES[code]
    return "-".join("+".join("_" if c is None else str(c) for c in cells) + "=" + str(fin)
                    for cells, fin in zip(st["q"], st["s"]))


def frames(folder: Path) -> None:
    """Six pictures of every screen in CODES for the harness's scripted pictures (the still screens as held)."""
    for code, st in CODES.items():
        rng = np.random.default_rng(900 + code)
        for i in range(6):
            picture({"look": 0, **st}, 0.0, i, rng).save(Path(folder) / f"sc{code}_{i}.png")


def capture_codes(state_path, binding, out_dir, seconds, every):
    st = json.loads(Path(state_path).read_text())
    rng = np.random.default_rng(181 + int(st["P1"]) + 101 * int(st.get("P2") or 0))
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        t = round(k * every, 2)
        name = f"f{k:04d}.png"
        picture({"look": 0, **CODES[int(st["P1"])]}, t, k, rng).save(Path(out_dir) / name)
        rows.append((t, name))
    return rows
