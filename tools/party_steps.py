#!/usr/bin/env python3
"""B208-B209 (queue BP): the front of the add-a-game path, rebuilt once around the user's five steps — survey, label
on the surveyed regions, plan, train. Called by `tools/party_add_game.py` (its stages `survey`, `plan`, `train`, and
`label` for a binding that has a survey); a binding without a survey never reaches this file.

    python3 tools/party_add_game.py survey <code>                               the boxes picture; the answer's grammar
    python3 tools/party_add_game.py survey <code> score <P1> <P2>               a box number or x0,y0,x1,y1 per player
    python3 tools/party_add_game.py survey <code> letters <WORD> <P1> <P2>
    python3 tools/party_add_game.py survey <code> winner|places                 recorded; the path goes on as today
    python3 tools/party_add_game.py survey <code> ok | again P<k> | P<k> <box or rectangle>
    python3 tools/party_add_game.py label <code> <role>=<P1>-<P2>,<P1>-<P2> ... [look=all|look=<symbol>:<i>]
    python3 tools/party_add_game.py plan <code>
    python3 tools/party_add_game.py train <code>

Where the result is comes from the survey (the session's answer, kept in the binding as numbers); nothing here
searches a picture for where a number or a letter is. What is missing is said once, as plan's last line. The gates
(design: docs/memory/evidence/b208_2026-11-24/design_written_before_code.md): a symbol two or more real pictures show
is read right by a reader learnt without its save; a symbol one real picture shows counts ("seen once") when the
title's font is rigid (`rigidity` >= BARS["rigid_min"]), every synthetic variant of it is read as itself and no other
symbol's real glyph is read as it; a symbol never shown is never learnt and is asked for.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import party_add_game as pag

KINDS = ("winner", "places", "score", "letters")
SURVEY_MARGIN = 6           # px of the reader's 640 x 480 picture around a numbered box
SURVEY_GRID = 40            # px: the ruled grid's step (reader pixels)
SURVEY_SCALE = 2            # the boxes picture is drawn at this scale
REGION_ZOOM = 4             # the regions picture: each region at this scale
SYN_PER_GLYPH = 8           # synthetic variants of each real glyph (training and gate 2)
SYN_DX, SYN_DY = 3, 1       # px: the synthetic shift's range
VARIANTS_NEEDED = 8         # B214: valid test variants the once rule reads (each the glyph that was pasted)
VARIANT_DRAWS = 24          # B214: at most this many draws a glyph
SYN_OWN = 0.85              # B214: B192's share — a variant's cut ink at least this much pasted ink
RECT = re.compile(r"^(\d{1,3}),(\d{1,3}),(\d{1,3}),(\d{1,3})$")
SCORE_LABEL = re.compile(r"^\d{1,4}(?:-\d{1,4}){1,3}$")


def es():
    return pag._endscreen()


# --- places on disk (off the repo) ----------------------------------------------------------------------------------
def survey_folder(code: str) -> Path:
    return pag.home(code) / "survey"


def label_path(code: str) -> Path:
    return pag.home(code) / "regions_label.json"


def label_folder(code: str) -> Path:
    return pag.home(code) / "regions"


def save_binding(code: str, b: dict) -> None:
    pag.write_if_changed(pag.binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")


def end_roles(kept) -> list:
    return sorted(r for r in kept if r.startswith("end_P"))


def final_pictures(code: str, b: dict, kept: dict, role: str) -> list[Path]:
    pics = pag._pictures(code, b, kept)
    return [pics / role / n for n in pag._two_pictures(pics, role)]


def grey(path) -> "np.ndarray":
    from PIL import Image
    with Image.open(path) as im:
        return es().score_picture(im)


def colour(path) -> "np.ndarray":
    from PIL import Image
    with Image.open(path) as im:
        return es().letters_area(im)


# --- B208: survey -----------------------------------------------------------------------------------------------------
def survey_boxes(a) -> list[list[int]]:
    """Every string today's segmentation (`score_strings`) finds, as [x0, y0, x1, y1] (inclusive, reader pixels); the
    strings of each polarity and radius merged when they overlap by half of the smaller; numbered by (top, left)."""
    boxes = [[s["x0"], s["top"], s["x1"], s["bot"]] for s in es().score_strings(a)]
    merged: list[list[int]] = []
    for bx in sorted(boxes, key=lambda q: -((q[2] - q[0] + 1) * (q[3] - q[1] + 1))):
        for m in merged:
            ix = min(m[2], bx[2]) - max(m[0], bx[0]) + 1
            iy = min(m[3], bx[3]) - max(m[1], bx[1]) + 1
            small = min((m[2] - m[0] + 1) * (m[3] - m[1] + 1), (bx[2] - bx[0] + 1) * (bx[3] - bx[1] + 1))
            if ix > 0 and iy > 0 and ix * iy * 2 >= small:
                m[:] = [min(m[0], bx[0]), min(m[1], bx[1]), max(m[2], bx[2]), max(m[3], bx[3])]
                break
        else:
            merged.append(list(bx))
    return sorted(merged, key=lambda q: (q[1], q[0]))


def draw_boxes(col, boxes: list, path: Path) -> None:
    import numpy as np
    from PIL import Image, ImageDraw
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize(
        (col.shape[1] * SURVEY_SCALE, col.shape[0] * SURVEY_SCALE), Image.NEAREST)
    d = ImageDraw.Draw(im)
    W, H = im.size
    for x in range(0, col.shape[1] + 1, SURVEY_GRID):
        d.line([(x * SURVEY_SCALE, 0), (x * SURVEY_SCALE, H)], fill=(0, 160, 255), width=1)
        d.text((x * SURVEY_SCALE + 2, 2), str(x), fill=(0, 200, 255))
    for y in range(0, col.shape[0] + 1, SURVEY_GRID):
        d.line([(0, y * SURVEY_SCALE), (W, y * SURVEY_SCALE)], fill=(0, 160, 255), width=1)
        d.text((2, y * SURVEY_SCALE + 2), str(y), fill=(0, 200, 255))
    for i, (x0, y0, x1, y1) in enumerate(boxes, 1):
        d.rectangle([x0 * SURVEY_SCALE - 2, y0 * SURVEY_SCALE - 2, x1 * SURVEY_SCALE + 2, y1 * SURVEY_SCALE + 2],
                    outline=(255, 40, 40), width=2)
        d.text((x0 * SURVEY_SCALE, max(0, y0 * SURVEY_SCALE - 14)), str(i), fill=(255, 255, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def draw_regions(col, regions: list, path: Path) -> None:
    import numpy as np
    from PIL import Image, ImageDraw
    crops = []
    for (x0, y0, x1, y1) in regions:
        c = Image.fromarray(np.clip(col[y0:y1 + 1, x0:x1 + 1], 0, 255).astype(np.uint8))
        crops.append(c.resize((c.size[0] * REGION_ZOOM, c.size[1] * REGION_ZOOM), Image.NEAREST))
    W = sum(c.size[0] for c in crops) + 20 * (len(crops) + 1)
    H = max(c.size[1] for c in crops) + 40
    sheet = Image.new("RGB", (W, H), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    x = 20
    for k, c in enumerate(crops, 1):
        sheet.paste(c, (x, 30))
        d.text((x, 8), f"P{k}", fill=(255, 255, 0))
        x += c.size[0] + 20
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def region_of(answer: str, boxes: list, size=(640, 480)) -> list[int] | None:
    """A box number's box grown by SURVEY_MARGIN (clipped), or a rectangle x0,y0,x1,y1 as given; None: neither."""
    W, H = size
    if answer.isdigit():
        i = int(answer)
        if not 1 <= i <= len(boxes):
            return None
        x0, y0, x1, y1 = boxes[i - 1]
        return [max(0, x0 - SURVEY_MARGIN), max(0, y0 - SURVEY_MARGIN), min(W - 1, x1 + SURVEY_MARGIN),
                min(H - 1, y1 + SURVEY_MARGIN)]
    m = RECT.match(answer)
    if not m:
        return None
    x0, y0, x1, y1 = (int(v) for v in m.groups())
    if not (0 <= x0 < x1 < W and 0 <= y0 < y1 < H):
        return None
    return [x0, y0, x1, y1]


def survey_inputs(b: dict) -> str:
    return pag.digest({"register": b["register_inputs"], "survey": b.get("survey")})


def _survey_cells(b: dict) -> pag.Cells:
    s = b.get("survey") or {}
    cells = pag.Cells()
    cells.add("the kind as register's", s.get("kind"), b["result"], s.get("kind") == b["result"])
    if s.get("kind") in ("score", "letters"):
        regs = s.get("regions") or []
        n = int(b["players"])
        whole = len(regs) == n and all(r is not None for r in regs)
        cells.add("one region per player, P1 first", sum(r is not None for r in regs), n, whole)
        if whole:
            inside = all(0 <= r[0] < r[2] < 640 and 0 <= r[1] < r[3] < 480 for r in regs)
            cells.add("every region inside the picture", inside, True, inside)
            apart = all(min(p[2], q[2]) < max(p[0], q[0]) or min(p[3], q[3]) < max(p[1], q[1])
                        for i, p in enumerate(regs) for q in regs[i + 1:])
            cells.add("the regions do not overlap", apart, True, apart)
        cells.add("the regions confirmed by the session", bool(s.get("confirmed")), True, bool(s.get("confirmed")))
    return cells


def registered(code: str, b: dict, kept: dict) -> None:
    """Survey runs once register holds the three saves (begin, other, one ending) — register's verdict for these saves,
    whatever it says about more endings (register is today's: it still names a second save of each ending)."""
    v = pag.load_verdict(code, "register")
    if not v or v.get("inputs") != pag.register_inputs(b, kept):
        raise pag.Refused("register has not kept these saves: run register first")
    if "begin" not in kept or not any(r.startswith("other") for r in kept) or not end_roles(kept):
        raise pag.Refused("survey needs register's three saves: begin, other and one ending")


def cmd_survey(code: str, a: dict) -> int:
    b = pag.load_binding(code)
    kept = pag.kept_states(code)
    registered(code, b, kept)
    words = list(a.get("words") or [])
    ends = end_roles(kept)
    role = ends[0]
    folder = survey_folder(code)
    first = final_pictures(code, b, kept, role)[0]
    boxes = survey_boxes(grey(first))
    pag.write_if_changed(folder / "boxes.json", json.dumps({"from": role, "boxes": boxes}, sort_keys=True))
    if not (folder / "boxes.png").is_file() or not words:
        draw_boxes(colour(first), boxes, folder / "boxes.png")
    n = int(b["players"])
    s = dict(b.get("survey") or {})
    if not words:
        pag.out(f"survey {code}: look at survey/boxes.png ({len(boxes)} numbered boxes, a grid every {SURVEY_GRID} "
                f"px) — answer: survey {code} <kind> " + ("<WORD> " if b["result"] == "letters" else "")
                + " ".join(f"<P{k}: a box number or x0,y0,x1,y1>" for k in range(1, n + 1)))
        return 3
    if words[0] in KINDS:
        kind = words[0]
        if kind != b["result"]:
            raise pag.Refused(f"register named this title {b['result']}, the survey says {kind}: one of them is wrong")
        rest = words[1:]
        if kind == "letters":
            if not rest or rest[0] != b.get("word"):
                raise pag.Refused("the word is not register's --word")
            rest = rest[1:]
        if kind in ("winner", "places"):
            b["survey"] = {"kind": kind}
            save_binding(code, b)
            rc = pag.finish(code, "survey", _survey_cells(b), survey_inputs(b))
            pag.out(f"survey {code}: {kind} — the path goes on as today (label, learn)")
            return rc
        if len(rest) != n:
            raise pag.Usage(f"survey {code} {kind}: one region per player ({n}), P1 first")
        regs = [region_of(x, boxes) for x in rest]
        bad = [f"P{k}" for k, r in enumerate(regs, 1) if r is None]
        if bad:
            raise pag.Usage(f"not a box number (1-{len(boxes)}) or x0,y0,x1,y1 inside 640 x 480: {', '.join(bad)}")
        s = {"kind": kind, "regions": regs, "margin": SURVEY_MARGIN, "size": [640, 480], "from": role,
             "confirmed": False}
    elif words[0] == "ok":
        if not s.get("regions") or any(r is None for r in s["regions"]):
            raise pag.Refused("no region to confirm: answer the survey first")
        s["confirmed"] = True
    elif words[0] == "again" and len(words) == 2 and re.match(r"^P[1-4]$", words[1]):
        k = int(words[1][1])
        if not s.get("regions") or k > len(s["regions"]):
            raise pag.Refused("no such region")
        s["regions"][k - 1] = None
        s["confirmed"] = False
    elif re.match(r"^P[1-4]$", words[0]) and len(words) == 2:
        k = int(words[0][1])
        if not s.get("regions") or k > len(s["regions"]):
            raise pag.Refused("no such region")
        r = region_of(words[1], boxes)
        if r is None:
            raise pag.Usage(f"not a box number (1-{len(boxes)}) or x0,y0,x1,y1 inside 640 x 480")
        s["regions"][k - 1] = r
        s["confirmed"] = False
    else:
        raise pag.Usage(f"survey {code} <kind> ... | ok | again P<k> | P<k> <box or rectangle>")
    b["survey"] = s
    save_binding(code, b)
    missing = [f"P{k}" for k, r in enumerate(s["regions"], 1) if r is None]
    if missing:
        pag.out(f"survey {code}: mark {', '.join(missing)} again — survey {code} {missing[0]} <a box number or "
                "x0,y0,x1,y1>")
        return 3
    if not s["confirmed"]:
        draw_regions(colour(first), s["regions"], folder / "regions.png")
        pag.out(f"survey {code}: look at survey/regions.png — answer survey {code} ok, or survey {code} again P<k>")
        return 3
    return pag.finish(code, "survey", _survey_cells(b), survey_inputs(b))


# --- the place from a region (score; no search) ---------------------------------------------------------------------
def region_place(a, region: list) -> dict | None:
    """The region's own line of glyphs: today's ink and parts, inside the region only; the line the most parts share
    (tops and bottoms within SCORE_TOL; the tallest on a tie), the first polarity / radius that has one. The place's
    x0 / x1 the region's edges brought in by `place_glyphs`'s own pad, so its window is the region."""
    E = es()
    x0, y0, x1, y1 = region
    contrast = E._contrast(a)
    for pol in (1, -1):
        for r in E.SCORE_RS:
            m = E._ink(a, pol, r, contrast)[y0:y1 + 1, x0:x1 + 1]
            parts = [c for c in E._components(m) if c[2] - c[0] + 1 >= E.SCORE_HMIN
                     and c[3] - c[1] + 1 <= 1.5 * (c[2] - c[0] + 1)]
            if not parts:
                continue
            lines: list[list] = []
            for c in sorted(parts, key=lambda c: c[0]):
                for ln in lines:
                    if abs(ln[0][0] - c[0]) <= E.SCORE_TOL and abs(ln[0][2] - c[2]) <= E.SCORE_TOL:
                        ln.append(c)
                        break
                else:
                    lines.append([c])
            best = max(lines, key=lambda ln: (len(ln), ln[0][2] - ln[0][0]))
            top = int(sorted(c[0] for c in best)[len(best) // 2]) + y0
            bot = int(sorted(c[2] for c in best)[len(best) // 2]) + y0
            h = bot - top + 1
            pad = int(round(h * E.SCORE_CELL[1] / E.SCORE_CELL[0])) + 2
            px0, px1 = x0 + pad, x1 - pad
            if px1 < px0:
                px0 = px1 = (x0 + x1) // 2
            return {"top": top, "bot": bot, "pol": pol, "r": r, "x0": px0, "x1": px1, "group": "",
                    "align": "region"}
    return None


def region_glyphs(a, place: dict) -> list:
    return es().place_glyphs(a, place) or []


def letters_text(col, region: list) -> bool:
    """Letters: a region holds text when the existing cut (today's letter strings over the region's own off-colour
    pixels) finds a part there — the corner's own pixels off its commonest colour, never a dark one."""
    import numpy as np
    E = es()
    x0, y0, x1, y1 = region
    sub = col[y0:y1 + 1, x0:x1 + 1]
    q = (sub // 16).astype(int)
    keyv = q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2]
    vals, counts = np.unique(keyv, return_counts=True)
    common = vals[int(np.argmax(counts))]
    m = (keyv != common) & (sub.sum(axis=2) >= E.LETTERS_FILL)
    return bool(E.letter_strings(m, 0, 0))


def regions_hold(code: str, b: dict, kept: dict) -> dict:
    """{role: [P<k> whose region holds no text]} for every end save's final picture."""
    s = b["survey"]
    out = {}
    for role in end_roles(kept):
        p = final_pictures(code, b, kept, role)[0]
        miss = []
        if s["kind"] == "score":
            a = grey(p)
            for k, reg in enumerate(s["regions"], 1):
                if region_place(a, reg) is None:
                    miss.append(f"P{k}")
        else:
            col = colour(p)
            for k, reg in enumerate(s["regions"], 1):
                if not letters_text(col, reg):
                    miss.append(f"P{k}")
        if miss:
            out[role] = miss
    return out


def hold_cell(cells: pag.Cells, code: str, held: dict) -> None:
    words = [f"{r}: no text in {', '.join(m)}'s region — mark it again (survey {code} again {m[0]})"
             for r, m in sorted(held.items())]
    cells.add("every end save shows text in every region", words or "yes", "yes", not held)


def score_places(code: str, b: dict, kept: dict) -> list:
    """The places, from the regions on the ending the survey was made on (the same for every save)."""
    s = b["survey"]
    a = grey(final_pictures(code, b, kept, s["from"])[0])
    return [region_place(a, reg) for reg in s["regions"]]


# --- B209: label on the regions -------------------------------------------------------------------------------------
def label_record(code: str) -> dict:
    rec = pag.read_json(label_path(code), {}) or {}
    rec.setdefault("saves", {})
    return rec


def label_inputs(code: str, b: dict) -> str:
    return pag.digest({"register": b["register_inputs"], "survey": b.get("survey"), "kept": pag.kept_states(code),
                       "labels": {r: v.get("readings") for r, v in sorted(label_record(code)["saves"].items())}})


def sides_of(kind: str, text: str) -> list[str]:
    return text.split("-") if kind == "score" else text.split("/")


def _fits(kind: str, text: str, n: int, word: str | None) -> bool:
    if kind == "score":
        return bool(SCORE_LABEL.match(text)) and len(text.split("-")) == n
    parts = text.split("/")
    return len(parts) == n and all(re.match(r"^(?:[A-Z-]{1,12}|_)$", p) for p in parts)


def role_agrees(kind: str, role: str, sides: list, word: str | None) -> bool:
    k = int(role[5])
    if kind == "score":
        vals = [int(x) for x in sides]
        return vals[k - 1] == max(vals) and vals.count(max(vals)) == 1
    other = [p for i, p in enumerate(sides, 1) if i != k]
    return all(p == word for p in other) and sides[k - 1] != word


def glyph_items(code: str, b: dict, kept: dict, roles=None) -> list:
    """Every glyph in the regions as read: [(role, picture index, player, position, symbol, cell)] — score: B178's
    cells at the region's place; letters: B191's cells from the corner the region is."""
    rec = label_record(code)["saves"]
    s = b["survey"]
    items = []
    if s["kind"] == "score":
        places = score_places(code, b, kept)
        for role in roles or end_roles(kept):
            if role not in rec:
                continue
            sides = sides_of("score", rec[role]["readings"][0])
            for pi, p in enumerate(final_pictures(code, b, kept, role)):
                a = grey(p)
                for k, pl in enumerate(places):
                    gl = region_glyphs(a, pl) if pl else []
                    if len(gl) != len(sides[k]):
                        items.append((role, pi, k + 1, None, None, None))
                        continue
                    for j, (ch, g) in enumerate(zip(sides[k], gl)):
                        items.append((role, pi, k + 1, j, ch, es().glyph_cell(a, g, pl)))
    return items


def draw_look(items: list, path: Path, scale: int = 3) -> list:
    """The last look: every glyph grouped by the symbol it was read as, one row a symbol, numbered from 1."""
    import numpy as np
    from PIL import Image, ImageDraw
    rows: dict = {}
    for it in items:
        if it[4] is not None:
            rows.setdefault(it[4], []).append(it)
    if not rows:
        return []
    ch, cw = items[[i for i, it in enumerate(items) if it[5] is not None][0]][5].shape
    width = 40 + max(len(v) for v in rows.values()) * (cw * scale + 6)
    sheet = Image.new("RGB", (width, len(rows) * (ch * scale + 20) + 10), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    order = []
    for r_i, sym in enumerate(sorted(rows)):
        y = 10 + r_i * (ch * scale + 20)
        d.text((6, y + 4), sym, fill=(255, 255, 0))
        for j, it in enumerate(rows[sym], 1):
            c = Image.fromarray((np.clip(it[5], 0, 1) * 255).astype(np.uint8)).resize((cw * scale, ch * scale),
                                                                                     Image.NEAREST)
            x = 40 + (j - 1) * (cw * scale + 6)
            sheet.paste(c.convert("RGB"), (x, y + 14))
            d.text((x, y), str(j), fill=(160, 200, 255))
            order.append((sym, j, it[0]))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return order


def cmd_label(code: str, a: dict) -> int:
    b = pag.load_binding(code)
    kept = pag.kept_states(code)
    s = b.get("survey") or {}
    pag.require(code, "survey", survey_inputs(b))
    if s.get("kind") not in ("score", "letters"):
        raise pag.Refused(f"a {s.get('kind')} title's label is today's: run learn")
    n, word, kind = int(b["players"]), b.get("word"), s["kind"]
    rec = label_record(code)
    folder = label_folder(code)
    ends = end_roles(kept)
    for role in ends:                                       # the pictures: two of each final screen, each region x4
        for pi, p in enumerate(final_pictures(code, b, kept, role), 1):
            if not (folder / f"{role}.{pi}.png").is_file():
                draw_regions(colour(p), s["regions"], folder / f"{role}.{pi}.png")
    look = None
    for item in a.get("readings") or []:
        k, _, v = item.partition("=")
        if k == "look":
            look = v
            continue
        if k not in ends:
            raise pag.Usage(f"{k}: not an end save of {code}")
        pair = v.split(",")
        if len(pair) != 2 or not all(_fits(kind, x, n, word) for x in pair):
            raise pag.Usage(f"{k}=<reading>,<reading>: two readings of its two pictures, "
                            + ("<P1>-<P2> numbers as drawn" if kind == "score" else "<P1>/<P2> corners"))
        rec["saves"][k] = {"readings": pair, "sha": kept[k]}
    rec["saves"] = {r: v for r, v in rec["saves"].items() if r in ends and v.get("sha") == kept[r]}
    pag.write_if_changed(label_path(code), json.dumps(rec, indent=1, sort_keys=True) + "\n")
    cells = pag.Cells()
    missing = [r for r in ends if r not in rec["saves"]]
    if missing:
        cells.add("every end save read (two pictures each)", missing, [], False)
        pag.finish(code, "label", cells, label_inputs(code, b))
        pag.out(f"label {code}: read the regions on label pictures regions/<role>.1.png and .2.png — label {code} "
                + " ".join(f"{r}=<reading>,<reading>" for r in missing))
        return 1
    for role in ends:
        pair = rec["saves"][role]["readings"]
        cells.add(f"{role}: the two readings the same", pair, "the same", pair[0] == pair[1])
        cells.add(f"{role}: the role agrees", pair[0], "its player won", role_agrees(kind, role, sides_of(kind, pair[0]),
                                                                                       word))
        if kind == "letters":
            fits = all(p == "_" or p == word or (len(p) == len(word) and all(c in (w, "-") for c, w in zip(p, word)))
                       for p in sides_of(kind, pair[0]))
            cells.add(f"{role}: each corner fits the word", pair[0], "letters of the word or -", fits)
    held = regions_hold(code, b, kept)
    hold_cell(cells, code, held)
    if kind == "score":
        items = glyph_items(code, b, kept)
        wrong = sorted({(it[0], f"P{it[2]}") for it in items if it[5] is None})
        cells.add("every region's glyphs as many as its reading", [f"{r} {p}" for r, p in wrong] or "yes", "yes",
                  not wrong)
        order = draw_look([it for it in items if it[1] == 0], folder / "look.png")
    else:
        order = letters_look(code, b, kept, rec, folder / "look.png")
    key = pag.digest({r: v["readings"] for r, v in sorted(rec["saves"].items())})
    if look is not None:
        m = re.match(r"^(all|([A-Z0-9-]):(\d+(?:\.\d+)*))$", look)
        if not m:
            raise pag.Usage("look=all, or look=<symbol>:<i>[.<j>] (the glyphs read wrong)")
        bad = {} if m.group(1) == "all" else {m.group(2): [int(x) for x in m.group(3).split(".")]}
        rec["look"] = {"for": key, "bad": bad}
        pag.write_if_changed(label_path(code), json.dumps(rec, indent=1, sort_keys=True) + "\n")
    lk = rec.get("look") or {}
    fresh = lk.get("for") == key
    bad_roles = sorted({role for sym, js in (lk.get("bad") or {}).items() for (s_, j, role) in order
                        if s_ == sym and j in js}) if fresh else []
    cells.add("the last look (regions/look.png): every glyph in the row of what it was read as",
              "all" if fresh and not lk.get("bad") else (bad_roles or "not looked at"), "all",
              fresh and not lk.get("bad"))
    rc = pag.finish(code, "label", cells, label_inputs(code, b))
    if not fresh:
        pag.out(f"label {code}: look at regions/look.png — label {code} look=all, or look=<symbol>:<i> for a glyph in "
                "the wrong row")
    elif bad_roles:
        pag.out(f"label {code}: read again: {', '.join(bad_roles)}")
    return rc


def letters_look(code: str, b: dict, kept: dict, rec: dict, path: Path) -> list:
    """Letters' last look: today's letters learner (B191 / B192) on the regions as surveyed, then each end save's
    first picture cut by its own colours inside each region; every glyph grouped by the letter read."""
    import numpy as np
    E = es()
    ends = [r for r in end_roles(kept) if r in rec["saves"]]
    pdir = pag._pictures(code, b, kept)
    starts, others, endp = pag._letters_inputs_of(pdir, kept)
    sides = {r: sides_of("letters", rec["saves"][r]["readings"][0]) for r in ends}
    regions = {k + 1: list(reg) for k, reg in enumerate(b["survey"]["regions"])}
    try:
        spec, arrays, _rep = E.learn_letters(starts, others, {r: endp[r] for r in ends}, sides, b["word"],
                                             b["players"], regions=regions)
    except ValueError:
        return []
    lt = spec["letters"]
    if not lt.get("found") or "places" not in lt:
        return []
    places = {int(p_): tuple(v) for p_, v in lt["places"].items()}
    bins = {p_: arrays["letters_bins"][i].astype(bool) for i, p_ in enumerate(sorted(places))}
    items = []
    for role in ends:
        a = colour(endp[role][0])
        for p_, box in places.items():
            text = sides[role][p_ - 1]
            if text == "_":
                continue
            m, gl = E.letters_glyphs(a, box, bins[p_], float(lt["glyph_min"]), len(text))
            if len(gl) == len(text):
                for j, (ch, g) in enumerate(zip(text, gl)):
                    items.append((role, 0, p_, j, ch, E.letter_cell(m.astype(np.float32), g)))
    return draw_look(items, path)


# --- B209: plan -----------------------------------------------------------------------------------------------------
def plan_symbols(b: dict, texts: dict) -> list[str]:
    s = b["survey"]
    if s["kind"] == "score":
        seen = [int(x) for t in texts.values() for x in t.split("-")]
        if b.get("max_score") is None:
            return list("0123456789")
        top = max([int(b["max_score"])] + seen)
        return sorted(set("".join(str(i) for i in range(top + 1))))
    word = b["word"]
    syms = sorted(set(word))
    if any("-" in t for t in texts.values()):
        syms.append("-")
    return syms


def shown_counts(kind: str, texts: dict, symbols: list) -> dict:
    """{symbol: how many end saves' readings show it in a result region}."""
    return {sym: sum(1 for t in texts.values() if sym in "".join(sides_of(kind, t))) for sym in symbols}


def ask_line(kind: str, never: list) -> str:
    if not never:
        return "Nothing more is needed."
    if kind == "score":
        parts = [f"a final score with a {d} in it" for d in never]
        tail = " (either player)." if len(parts) == 1 else " (either player; one match may show more than one)."
        return "Still needed: " + " and ".join(parts) + tail
    parts = [f"a match where a player's corner shows {c}" for c in never]
    return "Still needed: " + " and ".join(parts) + "."


def plan_inputs(code: str, b: dict) -> str:
    return pag.digest({"label": label_inputs(code, b)})


def texts_of(code: str) -> dict:
    return {r: v["readings"][0] for r, v in sorted(label_record(code)["saves"].items())}


def cmd_plan(code: str, a: dict) -> int:
    b = pag.load_binding(code)
    kept = pag.kept_states(code)
    pag.require(code, "label", label_inputs(code, b))
    s = b["survey"]
    texts = texts_of(code)
    syms = plan_symbols(b, texts)
    counts = shown_counts(s["kind"], texts, syms)
    cells = pag.Cells()
    held = regions_hold(code, b, kept)
    hold_cell(cells, code, held)
    rows = {x: ("twice or more" if counts[x] >= 2 else "once" if counts[x] == 1 else "never") for x in syms}
    gates = pag.Cells()                                       # B215: train's gates 2-3, nothing written
    g = (score_gates if s["kind"] == "score" else letters_gates)(code, b, kept, gates) if not held else {}
    if "stop" in g:
        cells.add("train's gates can run", g["stop"], "yes", False)
    ask = g.get("ask") if "ask" in g else [x for x in syms if counts[x] == 0]
    line = ask_line(s["kind"], ask)
    for x in g.get("seen_once", []):
        rows[x] = "once (counted: seen once)"
    for x in g.get("dropped", []):
        rows[x] = "once (not counted: asked)"
    recorded = {"symbols": rows, "pictures showing": counts, "ask": line,
                "train's gates": {"seen once": g.get("seen_once"), "not counted": g.get("dropped"),
                                  "once": g.get("once"), "rigidity": g.get("rig")}}
    note = "\n".join(["| symbol | real pictures showing it in a result region |", "| --- | --- |"]
                     + [f"| {x} | {counts[x]} ({rows[x]}) |" for x in syms] + ["", line])
    rc = pag.finish(code, "plan", cells, plan_inputs(code, b), note=note, recorded=recorded)
    for x in syms:
        pag.out(f"  {x}: {rows[x]}")
    pag.out(line)
    return rc


# --- B209: the measure ------------------------------------------------------------------------------------------------
def pair_distance(kind: str, c1, c2) -> float:
    E = es()
    if kind == "score":
        return max(float(E.cell_dists(c1, c2[None])[0]), float(E.cell_dists(c2, c1[None])[0]))
    return max(float(E.letter_dists(c1[None], c2)[0]), float(E.letter_dists(c2[None], c1)[0]))


def rigidity(kind: str, cells: dict, shown: dict) -> dict:
    """1 - (the farthest pair of one symbol's real glyphs) / (the nearest pair of two symbols' real glyphs), over the
    symbols two or more saves show. None (with why) when fewer than two such symbols."""
    syms = sorted(k for k in cells if shown.get(k, 0) >= 2 and len(cells[k]) >= 2)
    if len(syms) < 2:
        return {"rigidity": None, "why": "fewer than two symbols shown by two saves", "symbols": syms}
    same = max(pair_distance(kind, x, y) for k in syms for i, x in enumerate(cells[k]) for y in cells[k][i + 1:])
    diff = min(pair_distance(kind, x, y) for i, k in enumerate(syms) for k2 in syms[i + 1:]
               for x in cells[k] for y in cells[k2])
    return {"rigidity": round(1.0 - same / diff, 4) if diff > 0 else None, "farthest same": round(same, 4),
            "nearest different": round(diff, 4), "symbols": syms}


# --- B209: train (score) --------------------------------------------------------------------------------------------
def seed_of(texts: dict) -> int:
    return int(hashlib.sha256(json.dumps(texts, sort_keys=True).encode()).hexdigest()[:8], 16)


def erase(a, place: dict, region: list):
    """The region with its own ink filled by the region's median non-ink grey (a background for a pasted glyph)."""
    import numpy as np
    E = es()
    out = a.copy()
    x0, y0, x1, y1 = region
    ink = E._ink(a, place["pol"], int(place["r"]), E._contrast(a))[y0:y1 + 1, x0:x1 + 1]
    ink = ink | np.pad(ink, 1)[2:, 1:-1] | np.pad(ink, 1)[:-2, 1:-1] | np.pad(ink, 1)[1:-1, 2:] | np.pad(ink, 1)[1:-1, :-2]
    sub = out[y0:y1 + 1, x0:x1 + 1]
    if (~ink).any():
        sub[ink] = float(np.median(sub[~ink]))
    return out


def synthetic_glyphs(sources: list, backgrounds: list, place: dict, region: list, rng, per: int) -> dict:
    """{source index: [cells]} — each real glyph's ink pixels pasted on an erased background region at a shift, cut
    again by `place_glyphs` (exactly one glyph, else no cell) and `glyph_cell`."""
    E = es()
    out: dict = {}
    for si, (a, g) in enumerate(sources):
        contrast = E._contrast(a)
        t, l, bt, r_ = g[0], g[1], g[2], g[3]
        ink = E._ink(a, place["pol"], int(place["r"]), contrast)[t:bt + 1, l:r_ + 1]
        pix = a[t:bt + 1, l:r_ + 1]
        cells = []
        for _ in range(per):
            bg = backgrounds[int(rng.integers(len(backgrounds)))]
            dx, dy = int(rng.integers(-SYN_DX, SYN_DX + 1)), int(rng.integers(-SYN_DY, SYN_DY + 1))
            pic = bg.copy()
            cx = (region[0] + region[2]) // 2 - (r_ - l + 1) // 2 + dx
            ty = t + dy
            if cx < 0 or ty < 0 or cx + (r_ - l + 1) > pic.shape[1] or ty + (bt - t + 1) > pic.shape[0]:
                cells.append(None)
                continue
            dst = pic[ty:ty + bt - t + 1, cx:cx + r_ - l + 1]
            dst[ink] = pix[ink]
            gl = E.place_glyphs(pic, place)
            cells.append(E.glyph_cell(pic, gl[0], place) if gl and len(gl) == 1 else None)
        out[si] = cells
    return out


def read_cell(cell, score: dict, refs) -> str:
    """B178's rule on one cell (group ""): its digit, or '?'."""
    import numpy as np
    E = es()
    keys = list(score["keys"])
    if not keys or cell is None:
        return "?"
    d = E.cell_dists(cell, refs)
    order = np.argsort(d, kind="stable")
    best = keys[int(order[0])]
    margin = float(d[order[1]] - d[order[0]]) if len(keys) > 1 else float("inf")
    thr = score["thresholds"].get(best)
    need = score.get("margin_needed")
    ok = (score["separable"].get(best) and thr is not None and float(d[order[0]]) <= thr and need is not None
          and margin >= need)
    return best if ok else "?"


def fit_score(real: dict, shown: dict, train: dict | None = None) -> tuple:
    E = es()
    keys, refs, gaps, need, noise, small = E._digit_stats(real, shown, train or {})
    return {**E._stat_score(keys, gaps, need), "noise": round(noise, 4), "smallest_margin_seen": small}, refs


def screens_v4(pics: Path, kept: dict, name: str):
    """Today's screens for a version-4 spec (`_learn_v4`'s own calls): start, end (every end save), other."""
    import numpy as np
    from PIL import Image
    E = es()
    labels = pag._labels(pics, kept, E, {r: "end" for r in kept if r.startswith("end_P")})
    pag.write_if_changed(pics / "regions_labels.json", json.dumps(labels, sort_keys=True))
    paths, _ps, _ids = E._paths(E._sources(pics, pics / "regions_labels.json"), "first")
    aspect = E._cut_aspect([p for ps in paths.values() for p in ps])
    frames = {}
    for c, ps in paths.items():
        if c in ("ignore",):
            continue
        frames[c] = []
        for p in ps:
            with Image.open(p) as im:
                frames[c].append(E._final(E.mid(im)))
    for c in (E.START, E.END, E.OTHER):
        if not frames.get(c):
            raise pag.Refused(f"the pictures have no {c} frames")
    st = {c: np.stack(v).astype(np.float32) for c, v in frames.items()}
    screens, arrays = {}, {}
    for c, other_screen in ((E.START, E.END), (E.END, E.START)):
        mask, ref, gap = E._learn_one_screen(st[c], [st[E.OTHER], st[other_screen]])
        screens[c] = gap
        arrays[f"{c}_mask"], arrays[f"{c}_ref"] = mask, ref
    spec = {
        "version": E.VERSION_SCORE, "kind": "privyhub-h7-endscreen", "measure": E.MEASURE, "size": list(E.SIZE),
        "aspect": round(float(aspect), 5), "classes": [E.START, E.END], "start_class": E.START,
        "end_classes": [E.END], "screens": {c: {"threshold": g["threshold"], "own_worst": g["worst_own"],
                                                "mask_px": g["mask_px"]} for c, g in screens.items()},
        "usable": False, "steady_r": E.STEADY_R, "shared_near": E.SHARED_NEAR, "shared_share": E.SHARED_SHARE,
        "tol": E.TOL, "quant": 1.0 / E.QUANT, "flat": E.FLAT, "bar_max": E.BAR_MAX, "bar_share": E.BAR_SHARE,
        "k": E.K, "search_every_s": E.SEARCH_EVERY,
        "search": {"coarse_scales": list(E.COARSE_SCALES), "coarse_shifts_px_320": list(E.COARSE_SHIFTS),
                   "fine_scale": E.FINE_SCALE, "fine_shift_px_320": E.FINE_SHIFT},
        "score_size": list(E.SCORE_SIZE), "score_ink": E.SCORE_INK, "score_tol": E.SCORE_TOL,
        "frames": {c: len(v) for c, v in frames.items()}, "arrays": f"{name}.endscreen.npz" if name else None,
        "arrays_sha256": None,
    }
    return spec, arrays, screens


def replay(spec: dict, arrays: dict, run: Path, loaded: bool) -> tuple:
    """A run's pictures through one Reader and Ended: (seconds from its first picture, the end class, its numbers)
    of the first end, or None; and the first second the start was read (None: never)."""
    from PIL import Image
    E = es()
    with (run / "index.csv").open() as fh:
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader(fh)]
    now = [0.0]
    reader = E.Reader(spec, arrays, clock=lambda: now[0])
    ended = E.Ended(spec)
    if loaded:
        ended.start_loaded()
    first = None
    for t, f in rows:
        now[0] = t
        with Image.open(run / f) as im:
            r = reader.read(pag._for_reader(im, spec), now=t)
        if r["class"] == spec["start_class"] and first is None:
            first = round(t - rows[0][0], 2)
        done = ended.feed(r["class"], r.get("scores"))
        if done:
            sc = getattr(ended, "scores", None)
            return (round(t - rows[0][0], 2), done, [str(x) for x in sc] if sc is not None else None), first
    return None, first


def replay_cells(cells: pag.Cells, spec: dict, arrays: dict, pics: Path, kept: dict, want: dict) -> None:
    bar_end, bar_start = pag.BARS["ended_within_s"][0], pag.BARS["start_within_s"][0]
    for role in sorted(kept):
        cls = pag._role_class(role)
        if cls == "start":
            got, first = replay(spec, arrays, pics / role, False)
            cells.add(f"{role}: never ended", got is None, True, got is None)
            cells.add(f"{role}: recognised within", first, f"<= {bar_start} s", first is not None and first <= bar_start)
        elif cls == "other":
            got, _f = replay(spec, arrays, pics / role, True)
            cells.add(f"{role}: never ended", got is None, True, got is None)
        else:
            got, _f = replay(spec, arrays, pics / role, True)
            w = want[role]
            ok = got is not None and (got[2] == w if spec["version"] == 4 else got[1] == w)
            cells.add(f"{role}: ended as itself", None if got is None else (got[2] or got[1]), w, ok)
            cells.add(f"{role}: ended within", None if got is None else got[0], f"<= {bar_end} s",
                      got is not None and got[0] <= bar_end)


def train_inputs(code: str, b: dict) -> str:
    return pag.digest({"plan": plan_inputs(code, b)})


def _write_rules(code: str, b: dict, spec: dict, arrays: dict, cells: pag.Cells, key: str) -> bool:
    r = pag.rules_folder()
    spec_path = r / f"{b['game']}.endscreen.json"
    begin = r / pag._begin_name(b)
    side_path = r / f"{b['game']}.party.json"
    side = json.dumps({**pag._sidecar(b, spec), "code": code}, indent=1, sort_keys=True) + "\n"
    made = b.get("learnt") or {}
    for p_, want in ((begin, (pag.kept_folder(code) / "begin.state").read_bytes()), (side_path, side.encode())):
        if p_.exists() and p_.read_bytes() != want and not made:
            cells.add("rules folder: no other title's file overwritten", False, True, False)
            return False
    es().save_spec(spec, arrays, spec_path)
    pag.write_if_changed(begin, (pag.kept_folder(code) / "begin.state").read_bytes())
    pag.write_if_changed(side_path, side)
    b["learnt"] = {"from": key, "spec": pag.sha(spec_path), "by": "train"}
    save_binding(code, b)
    return True


def cmd_train(code: str, a: dict) -> int:
    b = pag.load_binding(code)
    kept = pag.kept_states(code)
    pag.require(code, "plan", plan_inputs(code, b))
    if b["survey"]["kind"] == "letters":
        return train_letters(code, b, kept)
    return train_score(code, b, kept)


def _once_rule(kind: str, sym: str, rig: dict, variants: list, real_others: list, read) -> tuple[bool, dict]:
    """The user's once rule: (a) the font rigid, (b) every test variant read as itself — VARIANTS_NEEDED of them, valid
    (B214), else "variants could not be made" — (c) no other symbol's real glyph read as it."""
    bar = pag.BARS.get("rigid_min", (None,))[0]               # B211: absent until T90 and T91 set it
    a_ = bar is not None and rig.get("rigidity") is not None and rig["rigidity"] >= bar
    got = [read(c) for c in variants]
    enough = len(variants) >= VARIANTS_NEEDED
    b_ = enough and all(g == sym for g in got)
    c_ = [o for o, c in real_others if read(c) == sym]
    read_as: dict = {}
    for g in got:
        read_as[g] = read_as.get(g, 0) + 1
    row = {"rigid": rig.get("rigidity"), "bar": bar,
           "variants read as itself": f"{sum(g == sym for g in got)} of {len(got)}",
           "variants read as": dict(sorted(read_as.items())),
           "other symbols' real glyphs read as it": len(c_)}
    if not enough:
        row["variants"] = f"variants could not be made ({len(variants)} valid of {VARIANTS_NEEDED} needed)"
    return bool(a_ and b_ and not c_), row


def test_variants(a, g, backgrounds: list, place: dict, region: list, rng) -> tuple[list, int]:
    """B214: the once rule's test variants of one real glyph — its ink pasted on an erased background region at a
    shift (BP's paste), **valid only when** cut as exactly one glyph with at least SYN_OWN of the cut's ink pasted
    ink; an invalid one thrown away and the next drawn from the same stream; at most VARIANT_DRAWS draws, stopping at
    VARIANTS_NEEDED valid. -> (the valid cells, the draws made)."""
    import numpy as np
    E = es()
    t, l, bt, r_ = g[0], g[1], g[2], g[3]
    ink = E._ink(a, place["pol"], int(place["r"]), E._contrast(a))[t:bt + 1, l:r_ + 1]
    pix = a[t:bt + 1, l:r_ + 1]
    h, w = bt - t + 1, r_ - l + 1
    valid, draws = [], 0
    while draws < VARIANT_DRAWS and len(valid) < VARIANTS_NEEDED:
        draws += 1
        bg = backgrounds[int(rng.integers(len(backgrounds)))]
        dx, dy = int(rng.integers(-SYN_DX, SYN_DX + 1)), int(rng.integers(-SYN_DY, SYN_DY + 1))
        cx = (region[0] + region[2]) // 2 - w // 2 + dx
        ty = t + dy
        if cx < 0 or ty < 0 or cx + w > bg.shape[1] or ty + h > bg.shape[0]:
            continue
        pic = bg.copy()
        pic[ty:ty + h, cx:cx + w][ink] = pix[ink]
        pasted = np.zeros(pic.shape, bool)
        pasted[ty:ty + h, cx:cx + w] = ink
        gl = E.place_glyphs(pic, place)
        if not gl or len(gl) != 1:
            continue
        c = gl[0]
        cut = E._ink(pic, place["pol"], int(place["r"]), E._contrast(pic))[c[0]:c[2] + 1, c[1]:c[3] + 1]
        own = pasted[c[0]:c[2] + 1, c[1]:c[3] + 1]
        if not cut.any() or float((cut & own).sum()) / float(cut.sum()) < SYN_OWN:
            continue
        valid.append(E.glyph_cell(pic, c, place))
    return valid, draws


def score_gates(code: str, b: dict, kept: dict, cells: pag.Cells) -> dict:
    """B215: train's gates 1-3 for a score title, writing nothing — the cells added to `cells`, and the ask (never
    seen, or seen once and not counted). plan and train both call it."""
    import numpy as np
    s = b["survey"]
    texts = texts_of(code)
    ends = end_roles(kept)
    places = score_places(code, b, kept)
    out: dict = {"places": places, "texts": texts}
    if any(p is None for p in places):
        k = places.index(None) + 1
        cells.add("a number in every region", f"none in P{k}'s on {s['from']}", "a number", False)
        out["stop"] = f"{code}: no number in P{k}'s region on {s['from']} — mark it again (survey {code} again P{k})"
        return out
    items = [it for it in glyph_items(code, b, kept) if it[5] is not None]
    pics = {role: [grey(p) for p in final_pictures(code, b, kept, role)] for role in ends}
    syms = plan_symbols(b, texts)
    counts = shown_counts("score", texts, syms)
    real = {}
    for it in items:
        real.setdefault(it[4], []).append(it)
    shown = {k: len({it[0] for it in v}) for k, v in real.items()}
    seed = seed_of(texts)
    rng_t, rng_v = np.random.default_rng([seed, 0]), np.random.default_rng([seed, 1])   # B214: two streams
    backgrounds = {k: [(role, erase(a, places[k], s["regions"][k])) for role in ends for a in pics[role]]
                   for k in range(len(places))}
    syn: dict = {}                                            # item index -> [template cells] (stream 0 only)
    src: dict = {}
    for i, it in enumerate(items):
        if it[1] != 0:
            continue
        role, k, j = it[0], it[2] - 1, it[3]
        a = pics[role][0]
        g = region_glyphs(a, places[k])[j]
        bgs = [bg for r_, bg in backgrounds[k] if r_ != role] or [bg for _r, bg in backgrounds[k]]
        src[i] = (a, g, bgs, k)
        syn[i] = synthetic_glyphs([(a, g)], bgs, places[k], s["regions"][k], rng_t, SYN_PER_GLYPH)[0]

    def fit(without=(), drop=()):
        rc_ = {k: [it[5] for it in v if it[0] not in without] for k, v in real.items() if k not in drop}
        rc_ = {k: v for k, v in rc_.items() if v}
        sh = {k: len({it[0] for it in real[k] if it[0] not in without}) for k in rc_}
        tr = {}
        for i, it in enumerate(items):
            if i in syn and it[0] not in without and it[4] in rc_:
                tr.setdefault(it[4], []).extend(c for c in syn[i] if c is not None)
        return fit_score(rc_, sh, tr)

    full, refs = fit()
    wrong = []                                                # gate 1
    for role in ends:
        sc, rf = fit(without=(role,))
        for it in items:
            if it[0] == role and shown.get(it[4], 0) >= 2:
                got = read_cell(it[5], sc, rf)
                if got != it[4]:
                    wrong.append(f"{role} P{it[2]} {it[4]} read {got}")
    twice = sorted(k for k in real if shown[k] >= 2)
    cells.add("gate 1: every glyph of a symbol two or more saves show, read right without its save", wrong or "all",
              "all", not wrong)
    cells.add("margin_needed", full.get("margin_needed"), f">= {pag.BARS['margin_needed_min'][0]}",
              full.get("margin_needed") is not None and full["margin_needed"] >= pag.BARS["margin_needed_min"][0])
    sep = [k for k in twice if not full["separable"].get(k)]
    cells.add("every symbol two saves show separable", sep or "all", "all", not sep)
    rig = rigidity("score", {k: [it[5] for it in v] for k, v in real.items()}, shown)
    once = sorted(k for k in real if shown[k] == 1)           # gate 2
    dropped, seen_once, once_rows, made = [], [], {}, {}
    for sym in once:
        variants, draws = [], 0
        for i, it in enumerate(items):
            if it[4] == sym and i in src and len(variants) < VARIANTS_NEEDED:
                a, g, bgs, k = src[i]
                v, d = test_variants(a, g, bgs, places[k], s["regions"][k], rng_v)
                variants += v[:VARIANTS_NEEDED - len(variants)]
                draws += d
        made[sym] = {"draws": draws, "valid": len(variants)}
        others = [(it[4], it[5]) for it in items if it[4] != sym]
        ok, row = _once_rule("score", sym, rig, variants, others, lambda c: read_cell(c, full, refs))
        row["draws"] = draws
        once_rows[sym] = {"counted": ok, **row}
        (seen_once if ok else dropped).append(sym)
        cells.add(f"gate 2: {sym}, one real picture", "seen once" if ok else {"not counted": row},
                  f"counted when rigid, {VARIANTS_NEEDED} valid variants all read as itself, no other glyph read as "
                  "it — else asked", True)
    if dropped:
        full, refs = fit(drop=dropped)
    never = sorted(x for x in syms if counts.get(x, 0) == 0)  # gate 3
    ask = sorted(set(never) | set(dropped))
    cells.add("gate 3: every symbol the result can show learnt (none never seen)", ask or "all", "all", not ask)
    out.update(full=full, refs=refs, real=real, shown=shown, counts=counts, rig=rig, seen_once=seen_once,
               dropped=dropped, once=once_rows, ask=ask, never=never,
               synthetic={"templates per glyph": SYN_PER_GLYPH, "seed": seed, "variants": made,
                          "made": sum(1 for v in syn.values() for c in v if c is not None),
                          "not cut": sum(1 for v in syn.values() for c in v if c is None)})
    return out


def train_score(code: str, b: dict, kept: dict) -> int:
    s = b["survey"]
    ends = end_roles(kept)
    cells = pag.Cells()
    g = score_gates(code, b, kept, cells)
    if "stop" in g:
        rc = pag.finish(code, "train", cells, train_inputs(code, b))
        pag.out(g["stop"])
        return rc
    texts, places, full, refs = g["texts"], g["places"], g["full"], g["refs"]
    pdir = pag._pictures(code, b, kept)
    spec, arrays, screens = screens_v4(pdir, kept, b["game"])
    spec["score"] = {"sides": len(places), "places": places, "found": True, "pooled": False, "columns": [],
                     **{k: full[k] for k in ("keys", "thresholds", "separable", "margin_needed")},
                     "max_score": int(max([int(b["max_score"])] + [int(x) for t in texts.values() for x in t.split("-")]))
                     if b.get("max_score") is not None else None,
                     "region_source": "survey", "regions": s["regions"], "seen_once": g["seen_once"],
                     "glyphs": {k: len(g["real"][k]) for k in full["keys"]}, "saves_showing": g["shown"]}
    if spec["score"]["max_score"] is None:
        spec["score"].pop("max_score")
    spec["usable"] = bool(all(x["threshold"] is not None for x in screens.values()) and full["keys"]
                          and full["margin_needed"] is not None)
    arrays["digit_refs"] = refs
    cells.add("the screens: start and end thresholds", {c: x["threshold"] for c, x in screens.items()}, "both set",
              all(x["threshold"] is not None for x in screens.values()))
    want = {r: sides_of("score", texts[r]) for r in ends}
    replay_cells(cells, spec, arrays, pdir, kept, want)
    recorded = {"rigidity": g["rig"], "seen once": g["seen_once"], "once": g["once"], "not counted": g["dropped"],
                "pictures showing": g["counts"], "margin_needed": full.get("margin_needed"), "synthetic": g["synthetic"]}
    line = ask_line("score", g["ask"])
    key = train_inputs(code, b)
    if cells.passed:
        _write_rules(code, b, spec, arrays, cells, key)
    rc = pag.finish(code, "train", cells, key, note=line, recorded=recorded)
    pag.out(line)
    return rc


# --- B209: train (letters) ------------------------------------------------------------------------------------------
def letters_gates(code: str, b: dict, kept: dict, cells: pag.Cells) -> dict:
    """B215: train's gates 1-3 for a letters title, writing nothing (as `score_gates`)."""
    import numpy as np
    E = es()
    s = b["survey"]
    texts = texts_of(code)
    ends = end_roles(kept)
    pdir = pag._pictures(code, b, kept)
    starts, others, endp = pag._letters_inputs_of(pdir, kept)
    sides = {r: texts[r].split("/") for r in ends}
    regions = {k + 1: list(reg) for k, reg in enumerate(s["regions"])}

    def learn(without=()):
        use = {r: p for r, p in endp.items() if r not in without}
        return E.learn_letters(starts, others, use, {r: sides[r] for r in use}, b["word"], b["players"],
                               name=b["game"], regions=regions)

    spec, arrays, rep = learn()
    out: dict = {"spec": spec, "arrays": arrays, "rep": rep, "pdir": pdir}
    syms = plan_symbols(b, texts)
    counts = shown_counts("letters", texts, syms)
    found = bool(spec["letters"].get("found")) and "places" in spec["letters"]
    cells.add("the letters found in every region", found, True, found)
    if not found:
        out["stop"] = f"{code}: {spec['letters'].get('not_found')} — mark the regions again (survey {code} again P1)"
        return out
    places = {int(p): tuple(v) for p, v in spec["letters"]["places"].items()}
    bins = {p: arrays["letters_bins"][i].astype(bool) for i, p in enumerate(sorted(places))}
    glyph_min = float(spec["letters"]["glyph_min"])
    checks = [(colour(p), sides[r]) for r in ends for p in endp[r]]
    real, _bad = E._letter_cells(places, bins, checks, b["word"], glyph_min)
    shown = {k: counts.get(k, 0) for k in real}
    rig = rigidity("letters", real, shown)
    wrong = []
    for role in ends:
        lspec, larr, _r = learn(without=(role,))
        if not lspec.get("usable"):
            wrong.append(f"{role}: no reader without it")
            continue
        rd = E.Reader(lspec, larr)
        for p in endp[role]:
            from PIL import Image
            with Image.open(p) as im:
                got = rd.sides(im.convert("RGB"))
            for k, (g_, w) in enumerate(zip(got, sides[role]), 1):
                if all(counts.get(c, 0) >= 2 for c in w if c != "_") and g_ != w:
                    wrong.append(f"{role} P{k} read {g_}")
    cells.add("gate 1: every corner of symbols two or more saves show, read right without its save", wrong or "all",
              "all", not wrong)
    fitted = {"keys": list(spec["letters"]["keys"]), "refs": arrays["letters_refs"].astype(np.float32),
              "thresholds": dict(spec["letters"]["thresholds"]), "margin_needed": spec["letters"]["margin_needed"]}

    def read_letter(c):
        if c is None:
            return "?"
        d = E.letter_dists(fitted["refs"], c)
        order = np.argsort(d, kind="stable")
        best = fitted["keys"][int(order[0])]
        thr = fitted["thresholds"].get(best)
        margin = float(d[order[1]] - d[order[0]]) if len(d) > 1 else float("inf")
        return best if thr is not None and float(d[order[0]]) <= thr and margin >= (fitted["margin_needed"] or 0) \
            else "?"

    once = sorted(k for k in real if shown.get(k, 0) == 1)
    rng_v = np.random.default_rng([seed_of(texts), 1])       # B214: the test stream (letters' templates are B192's)
    dropped, seen_once, once_rows = [], [], {}
    for sym in once:
        variants = []
        for c in real[sym]:                                    # the glyph's own cell at a shift: the pasted glyph
            while len(variants) < VARIANTS_NEEDED:             # by construction (the colour bins take the background)
                dy, dx = int(rng_v.integers(-2, 3)), int(rng_v.integers(-SYN_DX, SYN_DX + 1))
                variants.append(np.roll(np.roll(c, dy, 0), dx, 1))
        others_ = [(k, c) for k, v in real.items() if k != sym for c in v]
        ok, row = _once_rule("letters", sym, rig, variants, others_, read_letter)
        once_rows[sym] = {"counted": ok, **row}
        (seen_once if ok else dropped).append(sym)
        cells.add(f"gate 2: {sym}, one real picture", "seen once" if ok else {"not counted": row},
                  f"counted when rigid, {VARIANTS_NEEDED} valid variants all read as itself, no other glyph read as "
                  "it — else asked", True)
    never = sorted(x for x in syms if counts.get(x, 0) == 0)
    ask = sorted(set(never) | set(dropped))
    cells.add("gate 3: every symbol the result can show learnt (none never seen)", ask or "all", "all", not ask)
    out.update(counts=counts, rig=rig, seen_once=seen_once, dropped=dropped, once=once_rows, ask=ask, never=never)
    return out


def train_letters(code: str, b: dict, kept: dict) -> int:
    ends = end_roles(kept)
    cells = pag.Cells()
    g = letters_gates(code, b, kept, cells)
    if "stop" in g:
        rc = pag.finish(code, "train", cells, train_inputs(code, b), note=g["stop"])
        pag.out(g["stop"])
        return rc
    spec, arrays = g["spec"], g["arrays"]
    cells.add("the reader usable", spec.get("usable"), True, bool(spec.get("usable")))
    want = {r: pag._role_class(r) for r in ends}
    replay_cells(cells, spec, arrays, g["pdir"], kept, want)
    recorded = {"rigidity": g["rig"], "seen once": g["seen_once"], "once": g["once"], "not counted": g["dropped"],
                "pictures showing": g["counts"], "synthetic": (g["rep"].get("synthetic") or {})}
    line = ask_line("letters", g["ask"])
    key = train_inputs(code, b)
    if cells.passed:
        _write_rules(code, b, spec, arrays, cells, key)
    rc = pag.finish(code, "train", cells, key, note=line, recorded=recorded)
    pag.out(line)
    return rc
