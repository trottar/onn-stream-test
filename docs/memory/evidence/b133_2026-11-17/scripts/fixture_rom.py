"""B61: a synthetic N64 fixture ROM (no game): a header and a VI loop. The VI is set for 320x240 and the framebuffer
origin is flipped at every vertical interrupt (MI_INTR's VI bit polled, then cleared by a VI_CURRENT write), so the
video plugin swaps each frame and the core returns to the frontend every frame."""
import struct

def _i(op, rs=0, rt=0, imm=0):
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

def build() -> bytes:
    lui = lambda rt, imm: _i(0x0F, 0, rt, imm)
    ori = lambda rt, rs, imm: _i(0x0D, rs, rt, imm)
    sw = lambda rt, off, b: _i(0x2B, b, rt, off)
    lw = lambda rt, off, b: _i(0x23, b, rt, off)
    andi = lambda rt, rs, imm: _i(0x0C, rs, rt, imm)
    beq = lambda rs, rt, off: _i(0x04, rs, rt, off)
    T0, T1, T2, T3, T4, T6 = 8, 9, 10, 11, 12, 14
    c = [lui(T0, 0xA440), lui(T6, 0xA430)]
    for off, val in ((0x00, 0x320E), (0x08, 320), (0x0C, 0x200), (0x18, 525), (0x1C, 0x0C15), (0x20, 0x0C150C15),
                     (0x24, 0x006C02EC), (0x28, 0x002501FF), (0x2C, 0x000E0204), (0x30, 0x200), (0x34, 0x400)):
        c += [lui(T1, val >> 16), ori(T1, T1, val & 0xFFFF), sw(T1, off, T0)]
    c += [lui(T2, 0x0010), lui(T3, 0x0020)]
    loop = len(c)
    for org in (T2, T3):
        c.append(sw(org, 0x04, T0))                  # VI_ORIGIN
        w = len(c)
        c += [lw(T4, 0x08, T6), 0, andi(T4, T4, 8)]  # MI_INTR & VI
        c.append(beq(T4, 0, w - (len(c) + 1)))       # back to the lw while clear
        c.append(0)
        c.append(sw(0, 0x10, T0))                    # clear the VI interrupt
    c.append(beq(0, 0, loop - (len(c) + 1)))
    c.append(0)
    h = bytearray(64)
    h[0:4] = bytes.fromhex("80371240")
    h[4:8] = struct.pack(">I", 0xF)
    h[8:12] = struct.pack(">I", 0x80000400)
    h[12:16] = struct.pack(">I", 0x1449)
    h[0x20:0x34] = b"PRIVYHUB FIXTURE".ljust(20)
    h[0x3B:0x40] = b"NPFE\x00"
    body = bytearray(1 << 20)
    body[:64] = h
    code = b"".join(struct.pack(">I", w & 0xFFFFFFFF) for w in c)
    body[0x40:0x40 + len(code)] = code
    return bytes(body), c

if __name__ == "__main__":
    _, c = build()
    for i, w in enumerate(c):
        if w >> 26 == 4:
            off = w & 0xFFFF
            off -= 0x10000 if off & 0x8000 else 0
            print(i, "beq rs", (w >> 21) & 31, "rt", (w >> 16) & 31, "-> target", i + 1 + off, "word", hex(c[i + 1 + off]))
    print("words", len(c))
