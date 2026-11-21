"""B191 / B192 (tests): a made-up letters title's pictures — no title, nothing from the hub.

Two players' letters in the top corners (P1 blue, P2 pink, a dark shadow), a made-up 5 x 7 font at 3x for W, O and the
not-yet mark '-', each corner's string centred under its player's header; every match's end screen over a background of
its own (`bg`: plain, stripes, blocks, noise — none in the letters' colours unless a test asks); the begin and the
mid-match screen over one fixed scene with different middle text; the end screens' fixed text (a banner) the same in
every end save. A state file is JSON: {"kind": "begin" | "other" | "end", "l": ["---", "WOW"], "bg": n, ...}.

`capture` is the add-a-game tool's picture source (PARTY_ADD_GAME_CAPTURE=letters_capture:capture)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 640, 480
P1, P2 = (90, 96, 206), (206, 118, 158)
SHADOW = (12, 10, 18)
FONT = {
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "-": ["00000", "00000", "00000", "11111", "11111", "00000", "00000"],
    "X": ["10001", "01010", "00100", "00100", "00100", "01010", "10001"],
}
S = 3                    # px per font unit
CENTRES = {1: 106, 2: 530}
TOP = 88


def glyph(ch: str) -> np.ndarray:
    return np.kron(np.array([[c == "1" for c in row] for row in FONT[ch]]), np.ones((S, S), bool))


def background(bg: int, rng) -> np.ndarray:
    """Every match's own background: plain, stripes, blocks or noise (from `bg`), never in the letters' colours."""
    r = np.random.default_rng(1000 + bg)
    kind = bg % 4
    a = np.ones((H, W, 3), np.float32) * r.integers(40, 200, 3).astype(np.float32)
    if kind == 1:                                            # stripes
        w = int(r.integers(6, 20))
        a[:, (np.arange(W) // w) % 2 == 1] = r.integers(20, 220, 3)
    elif kind == 2:                                          # blocks
        for _ in range(40):
            y, x = int(r.integers(0, H - 40)), int(r.integers(0, W - 60))
            a[y:y + int(r.integers(10, 40)), x:x + int(r.integers(10, 60))] = r.integers(20, 220, 3)
    elif kind == 3:                                          # noise
        a += r.normal(0, 30, (H, W, 3))
    a[H // 2:] *= 0.6                                         # a ground
    a = np.clip(a, 0, 255)
    hue = (a[..., 2] > a[..., 0] + 25) | ((a[..., 0] > a[..., 1] + 40) & (a[..., 2] > a[..., 1] + 15))
    a[hue] = a[hue].mean(axis=1, keepdims=True)               # the letters' colours left to the letters
    return a


def scene() -> np.ndarray:
    a = np.zeros((H, W, 3), np.float32)
    a[: H // 2] = (205, 170, 110)
    a[H // 2:] = (70, 90, 60)
    return a


def put(a: np.ndarray, ch: str, x: int, y: int, colour) -> None:
    g = glyph(ch)
    h, w = g.shape
    a[y + 2:y + 2 + h, x + 2:x + 2 + w][g] = SHADOW
    a[y:y + h, x:x + w][g] = colour


def corner(a: np.ndarray, p: int, text: str, colour=None) -> None:
    if text == "_":
        return
    adv = 5 * S + 6
    x = CENTRES[p] - (len(text) * adv - 6) // 2
    for i, ch in enumerate(text):
        put(a, ch, x + i * adv, TOP if ch != "-" else TOP, colour or (P1 if p == 1 else P2))


def header(a: np.ndarray, p: int) -> None:
    c = P1 if p == 1 else P2
    x = CENTRES[p] - 50
    for i in range(6):                                       # "PLAYER n": six blocks
        a[60:78, x + i * 17:x + i * 17 + 13] = c


def picture(st: dict, t: float = 0.0, k: int = 0, rng=None) -> Image.Image:
    rng = rng or np.random.default_rng(0)
    kind = st["kind"]
    if kind in ("begin", "other"):
        a = scene()
        a[200:220, 180:460] = (60, 60, 160) if kind == "begin" else (60, 60, 160)
        if kind == "other":
            a[230:250, 260:380] = (60, 60, 160)                # the mid-match screen's extra line
        else:
            a[200:220, 400:460] = (230, 230, 230)
    else:
        a = background(int(st.get("bg", 0)), rng)
        a[150:180, 220:420] = (240, 200, 40)                 # the end screens' fixed banner
        a[156:174, 226:414] = (60, 30, 10)
    for p in (1, 2):
        header(a, p)
        corner(a, p, st.get("l", ["---", "---"])[p - 1], tuple(st["colour"][p - 1]) if st.get("colour") and
               st["colour"][p - 1] else None)
    if st.get("blobs"):                                      # a test's background shapes in a player's colour
        for p, x, y, w_, h_ in st["blobs"]:
            a[y:y + h_, x:x + w_] = P1 if p == 1 else P2
    noise = np.random.default_rng(7 + int(st.get("n", 0)) + k).integers(-2, 3, a.shape)
    return Image.fromarray(np.clip(a + noise, 0, 255).astype(np.uint8))


def capture(state_path, binding, out_dir, seconds, every):
    st = json.loads(Path(state_path).read_text())
    rows = []
    for k in range(int(seconds / every) + 1):
        if k % 2:
            continue
        t = round(k * every, 2)
        name = f"f{k:04d}.png"
        picture(st, t, 0).save(Path(out_dir) / name)          # a still screen: the same picture every tick
        rows.append((t, name))
    return rows
