"""B50: a formatted 8 MB PS2 memory card for PCSX2, and a checker that reads one back.

Used only by the PS2 launch kind (`ps2_session`, behind `PRIVYHUB_PS2=1`); nothing imports it otherwise.

H3-P2: the hub's cards were PCSX2's unformatted image (all `0xFF`), so a game's save failed. PCSX2 2.8.2 offers no CLI
or ini path that creates a formatted card, so the companion writes one -- only where a slot's card is absent or all
`0xFF`. A card with any other byte (a user's saves) is never touched.

The layout (16,384 pages of 512 data bytes + 16 spare bytes = 8,650,752 bytes):
- page 0: the superblock;
- cluster 8: the indirect FAT, naming FAT clusters 9-40;
- the FAT: the root's cluster as the end of its chain, the rest free;
- absolute cluster 41: the root directory (`.` / `..`);
- every written page carries its ECC (4 x 3-byte Hamming codes over 128-byte chunks, then 4 zero bytes); unwritten
  pages are all `0xFF`.

The ECC tables equal the two 256-byte tables in PCSX2 2.8.2's own binary
(`docs/memory/evidence/b50_2026-11-08/ecc_table_check.txt`). Design:
`docs/memory/evidence/b50_2026-11-08/design_written_before_code.md` §S2.
"""

from __future__ import annotations

import struct
import time
from pathlib import Path
from typing import Any

MAGIC = b"Sony PS2 Memory Card Format "
VERSION = b".".join((b"1", b"2", b"0", b"0"))   # the format's version, dotted
PAGE = 512
SPARE = 16
RAW_PAGE = PAGE + SPARE
PAGES = 16384
CARD_BYTES = PAGES * RAW_PAGE                 # 8,650,752
PAGES_PER_CLUSTER = 2
PAGES_PER_BLOCK = 16
CLUSTER = PAGE * PAGES_PER_CLUSTER
CLUSTERS = PAGES // PAGES_PER_CLUSTER         # 8192
EPC = CLUSTER // 4                            # FAT entries per cluster
IFC = 8                                       # the indirect FAT's cluster
FAT_CLUSTERS = 32
ALLOC_OFFSET = IFC + 1 + FAT_CLUSTERS         # 41
ALLOC_END = CLUSTERS - ALLOC_OFFSET - 2 * (PAGES_PER_BLOCK // PAGES_PER_CLUSTER)   # 8135
BACKUP1, BACKUP2 = 1023, 1022
CARD_TYPE, CARD_FLAGS = 2, 0x52
FREE, END = 0x7FFFFFFF, 0xFFFFFFFF
MODE_DOT, MODE_DOTDOT = 0x8427, 0xA426

_SB = struct.Struct("<28s12sHHHHIIIIII8x128s128sBBxx")
_DIRENT = struct.Struct("<HHI8sII8sI28x448s")


def _parity(a: int) -> int:
    a ^= a >> 1
    a ^= a >> 2
    a ^= a >> 4
    return a & 1


def _cpmask(a: int) -> int:
    return ((_parity(a & 0x55) << 0) | (_parity(a & 0x33) << 1) | (_parity(a & 0x0F) << 2)
            | (_parity(a & 0xAA) << 4) | (_parity(a & 0xCC) << 5) | (_parity(a & 0xF0) << 6))


PARITY = bytes(_parity(b) for b in range(256))
COLUMN_MASKS = bytes(_cpmask(b) for b in range(256))


def ecc128(chunk: bytes) -> bytes:
    """The 3-byte Hamming code of a 128-byte chunk (column parity, line parity 0, line parity 1)."""
    cp, lp0, lp1 = 0x77, 0x7F, 0x7F
    for i, b in enumerate(chunk):
        cp ^= COLUMN_MASKS[b]
        if PARITY[b]:
            lp0 ^= ~i
            lp1 ^= i
    return bytes((cp & 0xFF, lp0 & 0x7F, lp1 & 0xFF))


def spare_for(page: bytes) -> bytes:
    return b"".join(ecc128(page[i:i + 128]) for i in range(0, PAGE, 128)) + b"\x00" * 4


def _tod(t: float) -> bytes:
    """The card's time of day (Japan time, as the console keeps it): pad, sec, min, hour, day, month, year."""
    g = time.gmtime(t + 9 * 3600)
    return struct.pack("<xBBBBBH", g.tm_sec, g.tm_min, g.tm_hour, g.tm_mday, g.tm_mon, g.tm_year)


def superblock() -> bytes:
    ifc = struct.pack("<32I", IFC, *([0] * 31))
    bad = struct.pack("<32i", *([-1] * 32))
    sb = _SB.pack(MAGIC, VERSION, PAGE, PAGES_PER_CLUSTER, PAGES_PER_BLOCK, 0xFF00, CLUSTERS, ALLOC_OFFSET, ALLOC_END,
                  0, BACKUP1, BACKUP2, ifc, bad, CARD_TYPE, CARD_FLAGS)
    return sb + b"\xFF" * (PAGE - len(sb))


def _dirent(mode: int, length: int, name: bytes, t: float) -> bytes:
    tod = _tod(t)
    return _DIRENT.pack(mode, 0, length, tod, 0, 0, tod, 0, name)


def format_card(now: float | None = None) -> bytes:
    """A whole formatted 8 MB card image (`.ps2`, with ECC)."""
    t = time.time() if now is None else now
    pages: dict[int, bytes] = {0: superblock()}
    ifc_entries = list(range(IFC + 1, IFC + 1 + FAT_CLUSTERS)) + [END] * (EPC - FAT_CLUSTERS)
    ifc = struct.pack(f"<{EPC}I", *ifc_entries)
    pages[IFC * 2], pages[IFC * 2 + 1] = ifc[:PAGE], ifc[PAGE:]
    fat = [END] + [FREE] * (ALLOC_END - 1) + [END] * (FAT_CLUSTERS * EPC - ALLOC_END)
    for k in range(FAT_CLUSTERS):
        raw = struct.pack(f"<{EPC}I", *fat[k * EPC:(k + 1) * EPC])
        c = IFC + 1 + k
        pages[c * 2], pages[c * 2 + 1] = raw[:PAGE], raw[PAGE:]
    root = ALLOC_OFFSET
    pages[root * 2] = _dirent(MODE_DOT, 2, b".", t)
    pages[root * 2 + 1] = _dirent(MODE_DOTDOT, 0, b"..", t)
    blank = b"\xFF" * RAW_PAGE
    out = bytearray()
    for n in range(PAGES):
        data = pages.get(n)
        out += blank if data is None else data + spare_for(data)
    return bytes(out)


def is_unformatted(data: bytes) -> bool:
    """PCSX2's unformatted image: the full size, every byte 0xFF."""
    return len(data) == CARD_BYTES and data.count(0xFF) == CARD_BYTES


def _page(data: bytes, n: int) -> tuple[bytes, bytes]:
    raw = data[n * RAW_PAGE:(n + 1) * RAW_PAGE]
    return raw[:PAGE], raw[PAGE:]


def check(data: bytes) -> dict[str, Any]:
    """Read a card back: {"formatted": bool, "problems": [...], ...}. Never raises."""
    problems: list[str] = []
    out: dict[str, Any] = {"bytes": len(data)}
    if len(data) != CARD_BYTES:
        return {**out, "formatted": False, "problems": ["size"]}
    if is_unformatted(data):
        return {**out, "formatted": False, "problems": ["unformatted (all 0xFF)"]}
    sb_page, _ = _page(data, 0)
    f = _SB.unpack(sb_page[:_SB.size])
    names = ("magic", "version", "page_len", "pages_per_cluster", "pages_per_block", "unknown", "clusters",
             "alloc_offset", "alloc_end", "rootdir", "backup1", "backup2", "ifc", "bad", "card_type", "card_flags")
    sb = dict(zip(names, f))
    expect = {"magic": MAGIC, "page_len": PAGE, "pages_per_cluster": PAGES_PER_CLUSTER,
              "pages_per_block": PAGES_PER_BLOCK, "clusters": CLUSTERS, "alloc_offset": ALLOC_OFFSET,
              "alloc_end": ALLOC_END, "rootdir": 0, "backup1": BACKUP1, "backup2": BACKUP2, "card_type": CARD_TYPE}
    for k, v in expect.items():
        if sb[k] != v:
            problems.append(f"superblock {k}")
    if not sb["version"].startswith(VERSION):
        problems.append("superblock version")
    ecc_bad = 0
    for n in range(PAGES):
        page, spare = _page(data, n)
        if page == b"\xFF" * PAGE and spare == b"\xFF" * SPARE:
            continue
        if spare[:12] != spare_for(page)[:12]:
            ecc_bad += 1
    if ecc_bad:
        problems.append(f"ecc on {ecc_bad} page(s)")
    ifc_cluster = struct.unpack_from("<I", sb["ifc"], 0)[0]
    ifc_raw = b"".join(_page(data, ifc_cluster * 2 + i)[0] for i in range(PAGES_PER_CLUSTER))
    fat_clusters = list(struct.unpack(f"<{EPC}I", ifc_raw))[:FAT_CLUSTERS]
    fat: list[int] = []
    for c in fat_clusters:
        raw = b"".join(_page(data, c * 2 + i)[0] for i in range(PAGES_PER_CLUSTER))
        fat += struct.unpack(f"<{EPC}I", raw)
    if not fat or fat[0] != END:
        problems.append("fat: the root's cluster not an end of chain")
    free = sum(1 for e in fat[:sb["alloc_end"]] if e == FREE)
    out["free_clusters"] = free
    root = sb["alloc_offset"] + sb["rootdir"]
    e0 = _DIRENT.unpack(_page(data, root * 2)[0])
    e1 = _DIRENT.unpack(_page(data, root * 2 + 1)[0])
    if (e0[0], e0[2], e0[8].rstrip(b"\x00")) != (MODE_DOT, 2, b"."):
        problems.append("root: '.' entry")
    if (e1[0], e1[8].rstrip(b"\x00")) != (MODE_DOTDOT, b".."):
        problems.append("root: '..' entry")
    return {**out, "formatted": not problems, "problems": problems}


def ensure_cards(folder: Path, names: list[str], now: float | None = None) -> dict[str, str]:
    """Each named card: `created` (absent), `formatted` (was all 0xFF), or `kept` (holds data; never touched)."""
    folder.mkdir(parents=True, exist_ok=True)
    result: dict[str, str] = {}
    for name in names:
        p = folder / name
        if p.exists():
            if not p.is_file():
                result[name] = "kept"          # a folder card, PCSX2's own: not ours
                continue
            if not is_unformatted(p.read_bytes()):
                result[name] = "kept"
                continue
            how = "formatted"
        else:
            how = "created"
        tmp = p.with_name(p.name + ".privyhub.tmp")
        tmp.write_bytes(format_card(now))
        tmp.replace(p)
        result[name] = how
    return result
