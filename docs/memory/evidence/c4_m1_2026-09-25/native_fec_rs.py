"""C4-M1: the second parity of the `xor8_2` comparison arm (8 data + 2 parity).

The first parity is today's XOR parity (`PHF1` version 1), byte for byte.
The second is a Reed-Solomon "Q" parity over GF(2^8) (polynomial 0x11d,
generator 2, the RAID-6 construction): Q = sum over i of g^i * D_i, with
each payload zero-padded to the group's longest. It travels as its own
datagram, `PHF1` version 2, same 23-byte header, with `length_xor`
replaced by the Q-combination of the payload lengths (each length's high
and low byte combined separately).

With P and Q a receiver recovers any two missing data packets of a group,
or one missing packet whose P was lost. A receiver that does not know
version 2 drops the Q datagram and decodes P exactly as before.

`q_parity` uses `bytes.translate` with one 256-byte table per multiplier and
big-integer XOR, so the per-group cost stays in C, not in a per-byte Python
loop. `recover_*` are the reference decoder for the tests; the client's
decoder is `FecRs82.kt`.
"""

from __future__ import annotations

from typing import Sequence

POLY = 0x11D

EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= POLY
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def gf_inv(a: int) -> int:
    if a == 0:
        raise ZeroDivisionError("GF(256) inverse of 0")
    return EXP[255 - LOG[a]]


_MUL_TABLES: dict[int, bytes] = {}


def mul_table(c: int) -> bytes:
    t = _MUL_TABLES.get(c)
    if t is None:
        t = bytes(gf_mul(c, v) for v in range(256))
        _MUL_TABLES[c] = t
    return t


def gen_pow(i: int) -> int:
    return EXP[i % 255]


def _xor(a: bytes, b: bytes) -> bytes:
    n = len(a)
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(n, "big")


def q_parity(payloads: Sequence[bytes], length: int) -> bytes:
    """Q = sum g^i * D_i over GF(256), each payload zero-padded to `length`."""
    acc = bytes(length)
    for i, p in enumerate(payloads):
        padded = bytes(p) + bytes(length - len(p))
        acc = _xor(acc, padded.translate(mul_table(gen_pow(i))))
    return acc


def length_q(lengths: Sequence[int]) -> int:
    hi = lo = 0
    for i, n in enumerate(lengths):
        g = gen_pow(i)
        hi ^= gf_mul(g, (n >> 8) & 0xFF)
        lo ^= gf_mul(g, n & 0xFF)
    return (hi << 8) | lo


def p_parity(payloads: Sequence[bytes], length: int) -> bytes:
    acc = bytes(length)
    for p in payloads:
        acc = _xor(acc, bytes(p) + bytes(length - len(p)))
    return acc


def _scale(b: bytes, c: int) -> bytes:
    return b.translate(mul_table(c))


def recover_one_from_q(q: bytes, lq: int, known: dict[int, bytes], missing: int) -> tuple[bytes, int]:
    """One missing packet, P lost: D_x = g^-x (Q + sum_{i != x} g^i D_i)."""
    n = len(q)
    acc = q
    hi, lo = (lq >> 8) & 0xFF, lq & 0xFF
    for i, p in known.items():
        g = gen_pow(i)
        acc = _xor(acc, _scale(bytes(p) + bytes(n - len(p)), g))
        hi ^= gf_mul(g, (len(p) >> 8) & 0xFF)
        lo ^= gf_mul(g, len(p) & 0xFF)
    inv = gf_inv(gen_pow(missing))
    length = (gf_mul(inv, hi) << 8) | gf_mul(inv, lo)
    return _scale(acc, inv)[:length], length


def recover_two(p: bytes, lp_xor: int, q: bytes, lq: int, known: dict[int, bytes],
                x: int, y: int) -> tuple[tuple[bytes, int], tuple[bytes, int]]:
    """Two missing packets x < y with P and Q:
    D_x = (g^y * Pxy + Qxy) / (g^x + g^y), D_y = Pxy + D_x."""
    n = max(len(p), len(q))
    pxy, qxy = bytes(p) + bytes(n - len(p)), bytes(q) + bytes(n - len(q))
    lxy = lp_xor
    qhi, qlo = (lq >> 8) & 0xFF, lq & 0xFF
    for i, d in known.items():
        g = gen_pow(i)
        pad = bytes(d) + bytes(n - len(d))
        pxy = _xor(pxy, pad)
        qxy = _xor(qxy, _scale(pad, g))
        lxy ^= len(d)
        qhi ^= gf_mul(g, (len(d) >> 8) & 0xFF)
        qlo ^= gf_mul(g, len(d) & 0xFF)
    gx, gy = gen_pow(x), gen_pow(y)
    inv = gf_inv(gx ^ gy)
    dx = _scale(_xor(_scale(pxy, gy), qxy), inv)
    dy = _xor(pxy, dx)
    phi, plo = (lxy >> 8) & 0xFF, lxy & 0xFF
    lx = (gf_mul(inv, gf_mul(gy, phi) ^ qhi) << 8) | gf_mul(inv, gf_mul(gy, plo) ^ qlo)
    ly = lxy ^ lx
    return (dx[:lx], lx), (dy[:ly], ly)
