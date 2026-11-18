"""B137 settle (B61's form): a made-up N64 fixture ROM (no game) built on B61's VI loop. Every frame it:
  1. reads pad 1 through the PIF (the joybus "read buttons" command; the core asks the frontend for the pad here),
  2. draws with the RDP (fill rectangles sent by the CPU through DPC_START / DPC_END - the hub's GLideN64 renders them):
     the top three quarters in a colour that encodes a frame counter mod 64 (two bits a channel, 4 coarse levels),
     the bottom quarter white when any pad-1 button is down, else black,
  3. shows that buffer (VI_ORIGIN), waits for the vertical interrupt, counter + 1.
The counter is a CPU register, so it is part of a saved state: a picture shows which frame of which run it is.
usage: python3 fixture_counter_rom.py  -> prints the words (a self-check of the branch targets)."""
import struct

R = {"zero": 0, "t0": 8, "t1": 9, "t2": 10, "t3": 11, "t4": 12, "t5": 13, "t6": 14, "t7": 15,
     "s0": 16, "s1": 17, "s2": 18, "s3": 19, "s4": 20, "s5": 21, "a0": 4, "a1": 5, "a2": 6, "a3": 7, "v0": 2, "v1": 3}


def _i(op, rs, rt, imm):
    return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xFFFF)


def _r(rs, rt, rd, sa, funct):
    return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | (sa << 6) | funct


class Asm:
    def __init__(self):
        self.items = []

    def label(self, name):
        self.items.append(("label", name))

    def w(self, word):
        self.items.append(("w", word))

    def br(self, op, rs, rt, target):
        self.items.append(("br", op, rs, rt, target))
        self.w(0)                                   # the delay slot: a nop

    # instructions
    def lui(self, rt, imm): self.w(_i(0x0F, "zero", rt, imm))
    def ori(self, rt, rs, imm): self.w(_i(0x0D, rs, rt, imm))
    def andi(self, rt, rs, imm): self.w(_i(0x0C, rs, rt, imm))
    def addiu(self, rt, rs, imm): self.w(_i(0x09, rs, rt, imm))
    def sw(self, rt, off, base): self.w(_i(0x2B, base, rt, off))
    def lw(self, rt, off, base): self.w(_i(0x23, base, rt, off))
    def sll(self, rd, rt, sa): self.w(_r("zero", rt, rd, sa, 0x00))
    def srl(self, rd, rt, sa): self.w(_r("zero", rt, rd, sa, 0x02))
    def or_(self, rd, rs, rt): self.w(_r(rs, rt, rd, 0, 0x25))
    def beq(self, rs, rt, target): self.br(0x04, rs, rt, target)
    def bne(self, rs, rt, target): self.br(0x05, rs, rt, target)

    def li(self, rt, value):
        value &= 0xFFFFFFFF
        self.lui(rt, value >> 16)
        if value & 0xFFFF:
            self.ori(rt, rt, value & 0xFFFF)

    def assemble(self):
        pos, labels = 0, {}
        for it in self.items:
            if it[0] == "label":
                labels[it[1]] = pos
            else:
                pos += 1
        out, pos = [], 0
        for it in self.items:
            if it[0] == "label":
                continue
            if it[0] == "w":
                out.append(it[1] & 0xFFFFFFFF)
            else:
                _k, op, rs, rt, target = it
                off = labels[target] - (pos + 1)
                out.append(_i(op, rs, rt, off))
            pos += 1
        return out


VI, MI, SI, DPC = 0xA4400000, 0xA4300000, 0xA4800000, 0xA4100000
PIF_RAM = 0x1FC007C0
JOY = 0x00300000          # the joybus block (64 bytes), physical
CMD = 0x00300100          # the RDP list, physical
FB = (0x00100000, 0x00200000)
W, H, SPLIT = 320, 240, 180


def build():
    a = Asm()
    a.lui("t0", VI >> 16)
    a.lui("t6", MI >> 16)
    a.lui("s1", SI >> 16)
    a.lui("s4", DPC >> 16)
    a.li("s2", 0xA0000000 | JOY)
    a.li("s5", 0xA0000000 | CMD)
    for off, val in ((0x00, 0x320E), (0x08, 320), (0x0C, 0x200), (0x18, 525), (0x1C, 0x0C15), (0x20, 0x0C150C15),
                     (0x24, 0x006C02EC), (0x28, 0x002501FF), (0x2C, 0x000E0204), (0x30, 0x200), (0x34, 0x400)):
        a.li("t1", val)
        a.sw("t1", off, "t0")                        # B61's VI set-up (320 x 240, 16-bit)
    a.li("s0", 0)                                    # the frame counter
    for k in range(16):                              # the joybus block's constant part
        a.sw("zero", 4 * k, "s2")
    a.label("loop")
    for n, fb in enumerate(FB):
        # 1. pad 1 through the PIF: the block written, sent, read back
        a.li("t1", 0xFF010401); a.sw("t1", 0, "s2")
        a.li("t1", 0xFFFFFFFF); a.sw("t1", 4, "s2")
        a.li("t1", 0xFE000000); a.sw("t1", 8, "s2")
        a.li("t1", 0x00000001); a.sw("t1", 60, "s2")
        a.li("t1", JOY); a.sw("t1", 0x00, "s1")      # SI_DRAM_ADDR
        a.li("t1", PIF_RAM); a.sw("t1", 0x10, "s1")  # SI_PIF_ADDR_WR64B
        a.label(f"si_w{n}")
        a.lw("t4", 0x18, "s1"); a.w(0); a.andi("t4", "t4", 3); a.bne("t4", "zero", f"si_w{n}")
        a.sw("zero", 0x18, "s1")                     # the SI interrupt cleared
        a.li("t1", JOY); a.sw("t1", 0x00, "s1")
        a.li("t1", PIF_RAM); a.sw("t1", 0x04, "s1")  # SI_PIF_ADDR_RD64B
        a.label(f"si_r{n}")
        a.lw("t4", 0x18, "s1"); a.w(0); a.andi("t4", "t4", 3); a.bne("t4", "zero", f"si_r{n}")
        a.sw("zero", 0x18, "s1")
        a.lw("t1", 4, "s2"); a.w(0); a.srl("s3", "t1", 16)          # the buttons (0 = none down)
        # 2. the colours: top = the counter, bottom = white when a button is down
        # RGBA5551 from the counter mod 64, two bits per channel, each at 5-bit level 0 / 10 / 20 / 30
        a.andi("t1", "s0", 0x30); a.srl("t1", "t1", 4); a.li("t3", 0); a.label(f"r{n}")   # t1 = R level (0-3)
        a.beq("t1", "zero", f"rd{n}"); a.addiu("t3", "t3", 10); a.addiu("t1", "t1", -1); a.beq("zero", "zero", f"r{n}")
        a.label(f"rd{n}"); a.sll("t3", "t3", 11)
        a.andi("t1", "s0", 0x0C); a.srl("t1", "t1", 2); a.li("t5", 0); a.label(f"g{n}")
        a.beq("t1", "zero", f"gd{n}"); a.addiu("t5", "t5", 10); a.addiu("t1", "t1", -1); a.beq("zero", "zero", f"g{n}")
        a.label(f"gd{n}"); a.sll("t5", "t5", 6); a.or_("t3", "t3", "t5")
        a.andi("t1", "s0", 0x03); a.li("t5", 0); a.label(f"b{n}")
        a.beq("t1", "zero", f"bd{n}"); a.addiu("t5", "t5", 10); a.addiu("t1", "t1", -1); a.beq("zero", "zero", f"b{n}")
        a.label(f"bd{n}"); a.sll("t5", "t5", 1); a.or_("t3", "t3", "t5"); a.ori("t1", "t3", 1)
        a.sll("a0", "t1", 16); a.or_("a0", "a0", "t1")                         # two pixels
        a.li("a1", 0x00010001)
        a.beq("s3", "zero", f"black{n}")
        a.li("a1", 0xFFFFFFFF)
        a.label(f"black{n}")
        # the RDP list: colour image, scissor, fill mode, fill colour, rectangle, fill colour, rectangle, sync full
        words = [(0x3F10013F, fb), (0x2D000000, (W * 4 << 12) | (H * 4)), (0x2F300000, 0),
                 (0x37000000, "a0"), (0x36000000 | ((W - 1) * 4 << 12) | ((SPLIT - 1) * 4), 0),
                 (0x37000000, "a1"), (0x36000000 | ((W - 1) * 4 << 12) | ((H - 1) * 4), SPLIT * 4),
                 (0x29000000, 0)]
        for k, (hi, lo) in enumerate(words):
            a.li("t1", hi); a.sw("t1", 8 * k, "s5")
            if isinstance(lo, str):
                a.sw(lo, 8 * k + 4, "s5")
            else:
                a.li("t1", lo); a.sw("t1", 8 * k + 4, "s5")
        a.li("t1", 0x0001); a.sw("t1", 0x0C, "s4")                 # DPC_STATUS: clear xbus (the list is in RDRAM)
        a.li("t1", CMD); a.sw("t1", 0x00, "s4")                    # DPC_START
        a.li("t1", CMD + 8 * len(words)); a.sw("t1", 0x04, "s4")   # DPC_END: the list runs
        # 3. shown, the vertical interrupt waited for, the counter + 1
        a.li("t2", fb); a.sw("t2", 0x04, "t0")                     # VI_ORIGIN
        a.label(f"vi{n}")
        a.lw("t4", 0x08, "t6"); a.w(0); a.andi("t4", "t4", 8); a.beq("t4", "zero", f"vi{n}")
        a.sw("zero", 0x10, "t0")                                   # the VI interrupt cleared
        a.addiu("s0", "s0", 1)
    a.beq("zero", "zero", "loop")
    c = a.assemble()
    assert len(c) * 4 <= 0x1000 - 0x40, "the code must fit in the ROM's first 4 KB (run from SP DMEM)"
    h = bytearray(64)
    h[0:4] = bytes.fromhex("80371240")
    h[4:8] = struct.pack(">I", 0xF)
    h[8:12] = struct.pack(">I", 0x80000400)
    h[12:16] = struct.pack(">I", 0x1449)
    h[0x20:0x34] = b"PRIVYHUB FIXTURE B137".ljust(20)[:20]
    h[0x3B:0x40] = b"NPFE\x00"
    body = bytearray(1 << 20)
    body[:64] = h
    code = b"".join(struct.pack(">I", x) for x in c)
    body[0x40:0x40 + len(code)] = code
    return bytes(body), c


LEVELS = (0, 145, 204, 251)     # the four levels as the hub's N64 core shows them (measured, probe 2)


def decode(rgb, levels=LEVELS):
    """(r, g, b) 0-255 of the top area -> the counter mod 64 (two bits a channel: the nearest of the four levels)."""
    lv = [min(range(4), key=lambda k: abs(c - levels[k])) for c in rgb]
    return (lv[0] << 4) | (lv[1] << 2) | lv[2]


if __name__ == "__main__":
    _, c = build()
    print("words", len(c), "bytes", 4 * len(c))
