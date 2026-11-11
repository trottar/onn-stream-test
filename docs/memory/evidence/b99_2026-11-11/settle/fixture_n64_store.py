"""B99 settle: B61's N64 fixture ROM (docs/memory/evidence/b90_2026-11-11/measure/fixture_n64.py) with a second program
at ROM 0x1000 — the part the boot copies to RDRAM 0x400 and runs: store the word 0x12345678 at RDRAM 0x300000 and a
counter word at 0x300004 that it increments in a loop; then its own VI loop is not needed. No game."""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "b90_2026-11-11" / "measure"))
import fixture_n64

def _i(op, rs=0, rt=0, imm=0):
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

def build() -> bytes:
    T0, T1, T2 = 8, 9, 10
    c = [_i(0x0F, 0, T0, 0x8030),                     # lui t0, 0x8030
         _i(0x0F, 0, T1, 0x1234), _i(0x0D, T1, T1, 0x5678), _i(0x2B, T0, T1, 0),   # sw 0x12345678, 0(t0)
         _i(0x09, 0, T2, 0)]                          # addiu t2, zero, 0
    loop = len(c)
    c += [_i(0x09, T2, T2, 1), _i(0x2B, T0, T2, 4)]   # t2 += 1 ; sw t2, 4(t0)
    c += [_i(0x04, 0, 0, (loop - (len(c) + 1)) & 0xFFFF), 0]
    rom = bytearray(fixture_n64.build()[0])
    code = b"".join(struct.pack(">I", w & 0xFFFFFFFF) for w in c)
    rom[0x1000:0x1000 + len(code)] = code
    return bytes(rom)
