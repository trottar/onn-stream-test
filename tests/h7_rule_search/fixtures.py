"""B94: synthetic fixtures for the win-rule search (no game, made-up header text only).

Both programs make **noise** — a counter that advances continuously and a xorshift pseudo-random buffer rewritten as it
runs — and leave alone the areas the tests plant through B93's `--make-state --write`: a **per-player block** (a round
counter and a level per player, at a constant stride) and **decoys** (a block where player 1 is larger in every state;
a block that fits begin + a player-1 end but not a player-2 end).

PS1 (a PS-X EXE at 0x80010000): the counter at 0x080000, the xorshift word at 0x080004, the buffer 0x080100-0x0810FF.
SNES (a LoROM): the frame counter at $0000, the xorshift word at $0002, the buffer $1000-$13FF (one word per frame).
"""
import struct

# --- the plan the tests plant (addresses as the read commands take them) ---------------------------------------------
PS1 = {"block": 0x0C0000, "stride": 0x40, "rounds": 0x08, "level": 0x0C, "size": 2,
       "decoy_always_p1": 0x0D0000, "decoy_two_states": 0x0E0000, "decoy_stride": 0x20,
       "noise": [(0x080000, 0x080008), (0x080100, 0x081100)]}
SNES = {"block": 0x0800, "stride": 0x20, "rounds": 0x04, "level": 0x06, "size": 2,
        "decoy_always_p1": 0x0A00, "decoy_two_states": 0x0B00, "decoy_stride": 0x10,
        "noise": [(0x0000, 0x0004), (0x1000, 0x1400)]}


def _i(op, rs=0, rt=0, imm=0):
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)


def _r(rs, rt, rd, sa, fn):
    return (rs << 21) | (rt << 16) | (rd << 11) | (sa << 6) | fn


def psx_exe() -> bytes:
    S0, T0, T1, T2, T3 = 16, 8, 9, 10, 11
    lw = lambda rt, off, b: _i(0x23, b, rt, off)
    sw = lambda rt, off, b: _i(0x2B, b, rt, off)
    c = [_i(0x0F, 0, S0, 0x8008),                 # lui s0, 0x8008
         _i(0x0D, 0, T1, 0x1234), sw(T1, 4, S0)]  # the xorshift seed
    loop = len(c)
    c += [lw(T0, 0, S0), 0, _i(0x09, T0, T0, 1), sw(T0, 0, S0),                 # counter += 1
          lw(T1, 4, S0), 0,
          _r(0, T1, T2, 13, 0x00), _r(T1, T2, T1, 0, 0x26),                     # x ^= x << 13
          _r(0, T1, T2, 17, 0x02), _r(T1, T2, T1, 0, 0x26),                     # x ^= x >> 17
          _r(0, T1, T2, 5, 0x00), _r(T1, T2, T1, 0, 0x26),                      # x ^= x << 5
          sw(T1, 4, S0),
          _i(0x0C, T0, T3, 0x3FF), _r(0, T3, T3, 2, 0x00), _r(T3, S0, T3, 0, 0x21),
          sw(T1, 0x100, T3)]                                                     # buffer[counter & 1023] = x
    c += [_i(0x04, 0, 0, (loop - (len(c) + 1)) & 0xFFFF), 0]                    # b loop ; nop
    body = b"".join(struct.pack("<I", w) for w in c).ljust(0x800, b"\0")
    h = bytearray(0x800)
    h[0:8] = b"PS-X EXE"
    struct.pack_into("<IIII", h, 0x10, 0x80010000, 0, 0x80010000, len(body))
    struct.pack_into("<II", h, 0x30, 0x801FFF00, 0)
    h[0x4C:0x4C + 16] = b"PRIVYHUB FIXTURE"
    return bytes(h + body)


def snes() -> bytes:
    code = bytearray(); labels = {}; fix = []
    def emit(*b): code.extend(b)
    def label(n): labels[n] = len(code)
    def branch(op, t): emit(op, 0); fix.append((len(code) - 1, t))
    emit(0x78, 0x18, 0xFB, 0xC2, 0x30)                       # SEI CLC XCE REP #$30 (16-bit A, X)
    emit(0xA9, 0x34, 0x12, 0x8F, 0x02, 0x00, 0x7E)           # LDA #$1234 ; STA $7E0002 (seed)
    label("frame")
    emit(0xE2, 0x20)                                         # SEP #$20
    label("vb"); emit(0xAD, 0x12, 0x42); branch(0x10, "vb")
    label("vbe"); emit(0xAD, 0x12, 0x42); branch(0x30, "vbe")
    emit(0xC2, 0x20)                                         # REP #$20
    emit(0xAF, 0x00, 0x00, 0x7E, 0x1A, 0x8F, 0x00, 0x00, 0x7E)   # frame counter += 1
    # xorshift16: x ^= x << 7 ; x ^= x >> 9 ; x ^= x << 8
    emit(0xAF, 0x02, 0x00, 0x7E)                             # LDA x
    for shifts, op in ((7, 0x0A), (9, 0x4A), (8, 0x0A)):
        emit(0x85, 0x10)                                     # STA $10 (direct page scratch)
        emit(*([op] * shifts))                               # ASL / LSR × n
        emit(0x45, 0x10)                                     # EOR $10
    emit(0x8F, 0x02, 0x00, 0x7E)                             # STA x
    emit(0x48)                                               # PHA
    emit(0xAF, 0x00, 0x00, 0x7E, 0x29, 0xFF, 0x01, 0x0A, 0xAA)   # LDA counter ; AND #$01FF ; ASL ; TAX
    emit(0x68)                                               # PLA
    emit(0x9F, 0x00, 0x10, 0x7E)                             # STA $7E1000,X
    branch(0x80, "frame")
    for at, t in fix:
        rel = labels[t] - (at + 1); assert -128 <= rel <= 127; code[at] = rel & 0xFF
    rom = bytearray(b"\xFF" * 0x8000)
    rom[0:len(code)] = code
    rom[0x7FC0:0x7FD5] = b"PRIVYHUB FIXTURE".ljust(21)
    rom[0x7FD5] = 0x20; rom[0x7FD6] = 0; rom[0x7FD7] = 5; rom[0x7FD8] = 0; rom[0x7FD9] = 1
    for v in (0x7FE4, 0x7FE6, 0x7FE8, 0x7FEA, 0x7FEE, 0x7FF4, 0x7FF8, 0x7FFA, 0x7FFE):
        rom[v:v + 2] = struct.pack("<H", 0x8000 + labels["frame"])
    rom[0x7FFC:0x7FFE] = struct.pack("<H", 0x8000)
    rom[0x7FDC:0x7FE0] = b"\xFF\xFF\x00\x00"; s = sum(rom) & 0xFFFF
    rom[0x7FDC:0x7FE0] = struct.pack("<HH", s ^ 0xFFFF, s)
    return bytes(rom)
