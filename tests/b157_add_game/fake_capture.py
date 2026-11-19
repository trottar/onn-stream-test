"""B157's tests: the add-a-game tool's picture source replaced by made-up pictures (PARTY_ADD_GAME_CAPTURE). A made-up
kept state is B103's fake RetroArch state ({"P1": code, "P2": 0}); its code names the screen it shows:

    100 start, 101 other, 102 end_P1, 103 end_P2           (B102's synthetic two-player screens)
    200 s4start, 201 s4other, 210 + k: a results row ROWS[k] (B122's synthetic four-player screens)

Every picture made-up (no title, nothing read from the hub)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
for sub in ("b102_h7_endscreen", "b122_h7_places"):
    sys.path.insert(0, str(HERE.parent / sub))
import test_b102 as b102  # noqa: E402
import test_b122 as b122  # noqa: E402

ROWS = ["1234", "2341", "3412", "4123", "2143"]
CODES = {100: "start", 101: "other", 102: "end_P1", 103: "end_P2", 200: "s4start", 201: "s4other",
         **{210 + k: f"s4r{r}" for k, r in enumerate(ROWS)}}
TALLY = {"start": "00", "end_P1": "10", "end_P2": "01"}


def token_of(state: Path) -> str:
    return CODES[int(json.loads(Path(state).read_text())["P1"])]


def picture(token: str, k: int, rng):
    if token in TALLY:
        return b102.screen(50 + k % 6, TALLY[token], rng)
    if token == "other":
        return b102.other(900 + k, rng)
    if token == "s4start":
        return b122.start(k % 6, rng)
    if token == "s4other":
        return b122.other(k % 6, rng)
    return b122.results(0, token[3:], 40, rng)          # a results screen held still: one layout, its noise


def capture(state, binding, out_dir, seconds, every):
    token = token_of(state)
    rng = np.random.default_rng(157 + sum(map(ord, token)))
    rows = []
    for k in range(int(seconds / every) + 1):
        name = f"f{k:04d}.png"
        picture(token, k, rng).save(Path(out_dir) / name)
        rows.append((round(k * every, 2), name))
    return rows
