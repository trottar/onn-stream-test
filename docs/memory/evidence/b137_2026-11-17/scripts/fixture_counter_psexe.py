"""B137 settle (B61's form): a made-up PS1 program (a PS-EXE, no game) for the hub's PS1 core. Every frame it:
  1. reads pad 1 through SIO0 (the pad's "read buttons" exchange: 01 42 00 00 00; the core asks the frontend here),
  2. fills the top three quarters with a colour that encodes a frame counter mod 64 (two bits a channel, levels
     0 / 80 / 160 / 240) and the bottom quarter white when any pad-1 button is down, else black (GPU fill rectangles),
  3. waits for the vertical blank (I_STAT bit 0, interrupts off), counter + 1.
The counter is a CPU register: part of a saved state. usage: python3 fixture_counter_psexe.py -> the size."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_counter_rom import Asm, R, _i  # noqa: E402  (the same MIPS encodings: the R3000A is MIPS I)

LOAD = 0x80010000


class Asm1(Asm):
    def sh(self, rt, off, base): self.w(_i(0x29, base, rt, off))
    def lbu(self, rt, off, base): self.w(_i(0x24, base, rt, off))
    def lhu(self, rt, off, base): self.w(_i(0x25, base, rt, off))
    def mtc0(self, rt, rd): self.w((0x10 << 26) | (0x04 << 21) | (R[rt] << 16) | (rd << 11))


def build():
    a = Asm1()
    a.mtc0("zero", 12)                                  # SR = 0: interrupts off
    a.lui("t0", 0xBF80)                                 # I/O base (KSEG1 0x1F800000)
    a.sw("zero", 0x1074, "t0")                          # I_MASK = 0
    a.sw("zero", 0x1070, "t0")                          # I_STAT acknowledged

    def gp1(v):
        a.li("t1", v); a.sw("t1", 0x1814, "t0")

    def gp0(v, reg=None):
        lbl = f"gw{len(a.items)}"
        a.label(lbl)                                    # GPUSTAT bit 26: ready for a command word
        a.lw("t4", 0x1814, "t0"); a.w(0); a.li("t5", 0x04000000); a.w(_r_and("t4", "t4", "t5")); a.beq("t4", "zero", lbl)
        if reg is None:
            a.li("t1", v); a.sw("t1", 0x1810, "t0")
        else:
            a.sw(reg, 0x1810, "t0")

    for v in (0x00000000, 0x03000000, 0x08000001, 0x05000000, 0x06C60260, 0x07040010):
        gp1(v)
    for v in (0xE1000400, 0xE3000000, 0xE403BD3F, 0xE5000000):
        gp0(v)
    a.li("t1", 0x000D); a.sh("t1", 0x1048, "t0")        # JOY_MODE
    a.li("t1", 0x0088); a.sh("t1", 0x104E, "t0")        # JOY_BAUD
    a.li("s0", 0)
    a.label("loop")
    # 1. pad 1: 01 42 00 00 00, the last two answers are the buttons (active low)
    a.li("t1", 0x1003); a.sh("t1", 0x104A, "t0")        # JOY_CTRL: TX on, /JOY1 selected
    a.li("s3", 0xFFFF)
    for k, byte in enumerate((0x01, 0x42, 0x00, 0x00, 0x00)):
        a.li("t2", 4000)                                # every wait bounded: the picture never stops on the pad
        a.label(f"tx{k}")
        a.lhu("t4", 0x1044, "t0"); a.w(0); a.andi("t4", "t4", 1); a.bne("t4", "zero", f"txok{k}")
        a.addiu("t2", "t2", -1); a.bne("t2", "zero", f"tx{k}")
        a.beq("zero", "zero", "padend")
        a.label(f"txok{k}")
        a.li("t1", byte)
        a.w(_i(0x28, "t0", "t1", 0x1040))               # sb t1, JOY_TX_DATA
        a.li("t2", 4000)
        a.label(f"rx{k}")
        a.lhu("t4", 0x1044, "t0"); a.w(0); a.andi("t4", "t4", 2); a.bne("t4", "zero", f"rxok{k}")
        a.addiu("t2", "t2", -1); a.bne("t2", "zero", f"rx{k}")
        a.beq("zero", "zero", "padend")
        a.label(f"rxok{k}")
        a.lbu("t1", 0x1040, "t0"); a.w(0)
        if k == 3:
            a.or_("s3", "t1", "zero")                   # buttons low byte
        if k == 4:
            a.sll("t1", "t1", 8); a.or_("s3", "s3", "t1")
        a.li("t1", 0x1013); a.sh("t1", 0x104A, "t0")    # acknowledge (bit 4), still selected
        a.li("t2", 300)                                 # a short gap for the pad's /ACK
        a.label(f"gap{k}")
        a.addiu("t2", "t2", -1); a.bne("t2", "zero", f"gap{k}")
    a.label("padend")
    a.sh("zero", 0x104A, "t0")                          # deselected
    a.li("t1", 0xFFFF); a.w(_r_xor("s3", "s3", "t1"))   # s3 = buttons down (0 = none)
    # 2. the colours
    for shift, reg in ((4, "a2"), (2, "a3"), (0, "v1")):
        a.srl("t1", "s0", shift); a.andi("t1", "t1", 3); a.li(reg, 0)
        lbl = f"lv{shift}"
        a.label(lbl)
        a.beq("t1", "zero", lbl + "d"); a.addiu(reg, reg, 80); a.addiu("t1", "t1", -1); a.beq("zero", "zero", lbl)
        a.label(lbl + "d")
    a.sll("v1", "v1", 16); a.sll("a3", "a3", 8); a.or_("a0", "v1", "a3"); a.or_("a0", "a0", "a2")
    a.li("t1", 0x02000000); a.or_("a0", "a0", "t1")    # GP0 02 BBGGRR
    a.li("a1", 0x02000000)
    a.beq("s3", "zero", "black")
    a.li("a1", 0x02FFFFFF)
    a.label("black")
    gp0(None, "a0"); gp0(0x00000000); gp0(0x00B40140)  # top: y 0, h 180, w 320
    gp0(None, "a1"); gp0(0x00B40000); gp0(0x003C0140)  # bottom: y 180, h 60
    # 3. the vertical blank
    a.label("vb")
    a.lw("t4", 0x1070, "t0"); a.w(0); a.andi("t4", "t4", 1); a.beq("t4", "zero", "vb")
    a.li("t1", 0xFFFFFFFE); a.sw("t1", 0x1070, "t0")   # acknowledged
    a.addiu("s0", "s0", 1)
    a.beq("zero", "zero", "loop")
    c = a.assemble()
    code = b"".join(struct.pack("<I", x) for x in c)
    size = (len(code) + 0x7FF) // 0x800 * 0x800
    h = bytearray(0x800)
    h[0:8] = b"PS-X EXE"
    struct.pack_into("<IIII", h, 0x10, LOAD, 0, LOAD, size)
    struct.pack_into("<II", h, 0x30, 0x801FFF00, 0)
    h[0x4C:0x4C + 55] = b"Sony Computer Entertainment Inc. for North America area"
    return bytes(h) + code.ljust(size, b"\0"), c


def _r_and(rd, rs, rt):
    return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | 0x24


def _r_xor(rd, rs, rt):
    return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | 0x26


if __name__ == "__main__":
    b, c = build()
    print("words", len(c), "bytes", len(b))
