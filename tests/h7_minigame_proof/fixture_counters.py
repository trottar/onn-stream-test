"""B93: a synthetic SNES LoROM (no game) for the mini-game proof. Two 16-bit counters in work RAM ($0100 = P1,
$0102 = P2) advance once per frame (the vertical-blank flag polled); the mode byte ($0104) decides who runs at twice
the rate: 0 → P1, 1 → P2. Made-up header text only."""
import struct


def build() -> bytes:
    code = bytearray()
    labels: dict[str, int] = {}
    fix: list[tuple[int, str]] = []

    def emit(*b):
        code.extend(b)

    def label(n):
        labels[n] = len(code)

    def branch(op, target):
        emit(op, 0)
        fix.append((len(code) - 1, target))

    P1, P2, MODE = (0x00, 0x01, 0x7E), (0x02, 0x01, 0x7E), (0x04, 0x01, 0x7E)
    emit(0x78, 0x18, 0xFB, 0xC2, 0x30, 0xA9, 0x00, 0x00)        # SEI CLC XCE REP #$30 LDA #0
    for a in (P1, P2, MODE):
        emit(0x8F, *a)                                          # STA long
    label("frame")
    emit(0xE2, 0x20)                                            # SEP #$20
    label("vb")
    emit(0xAD, 0x12, 0x42); branch(0x10, "vb")                  # LDA $4212 ; BPL vb (wait for vblank)
    label("vbe")
    emit(0xAD, 0x12, 0x42); branch(0x30, "vbe")                 # LDA $4212 ; BMI vbe (wait for its end)
    emit(0xC2, 0x20, 0xAF, *MODE, 0x29, 0xFF, 0x00)             # REP #$20 ; LDA mode ; AND #$00FF
    branch(0xF0, "p1fast")                                      # BEQ p1fast
    for addr, inc in ((P2, 2), (P1, 1)):
        emit(0xAF, *addr, *([0x1A] * inc), 0x8F, *addr)         # LDA ; INC A × n ; STA
    branch(0x80, "frame")
    label("p1fast")
    for addr, inc in ((P1, 2), (P2, 1)):
        emit(0xAF, *addr, *([0x1A] * inc), 0x8F, *addr)
    branch(0x80, "frame")
    for at, target in fix:
        rel = labels[target] - (at + 1)
        assert -128 <= rel <= 127
        code[at] = rel & 0xFF
    rom = bytearray(b"\xFF" * 0x8000)
    rom[0:len(code)] = code
    rom[0x7FC0:0x7FD5] = b"PRIVYHUB FIXTURE".ljust(21)
    rom[0x7FD5] = 0x20; rom[0x7FD6] = 0; rom[0x7FD7] = 5; rom[0x7FD8] = 0; rom[0x7FD9] = 1
    for v in (0x7FE4, 0x7FE6, 0x7FE8, 0x7FEA, 0x7FEE, 0x7FF4, 0x7FF8, 0x7FFA, 0x7FFE):
        rom[v:v + 2] = struct.pack("<H", 0x8000 + labels["frame"])
    rom[0x7FFC:0x7FFE] = struct.pack("<H", 0x8000)
    rom[0x7FDC:0x7FE0] = b"\xFF\xFF\x00\x00"
    s = sum(rom) & 0xFFFF
    rom[0x7FDC:0x7FE0] = struct.pack("<HH", s ^ 0xFFFF, s)
    return bytes(rom)
