"""B90: two more synthetic fixtures (no game, no title): a SNES LoROM that loops forever, and a PS-X EXE that loops
forever. Made-up header text only."""
import struct

def snes() -> bytes:
    rom = bytearray(b"\xFF" * 0x8000)
    code = bytes([0x78, 0x18, 0xFB, 0x80, 0xFE])      # SEI; CLC; XCE; BRA -2
    rom[0:len(code)] = code
    rom[0x7FC0:0x7FD5] = b"PRIVYHUB FIXTURE".ljust(21)
    rom[0x7FD5] = 0x20; rom[0x7FD6] = 0x00; rom[0x7FD7] = 0x05; rom[0x7FD8] = 0x00
    rom[0x7FD9] = 0x01; rom[0x7FDA] = 0x00; rom[0x7FDB] = 0x00
    for v in (0x7FE4, 0x7FE6, 0x7FE8, 0x7FEA, 0x7FEE, 0x7FF4, 0x7FF8, 0x7FFA, 0x7FFC, 0x7FFE):
        rom[v:v + 2] = struct.pack("<H", 0x8003)          # every vector at the loop
    rom[0x7FFC:0x7FFE] = struct.pack("<H", 0x8000)        # reset at the start
    rom[0x7FDC:0x7FE0] = b"\xFF\xFF\x00\x00"
    s = sum(rom) & 0xFFFF
    rom[0x7FDC:0x7FE0] = struct.pack("<HH", s ^ 0xFFFF, s)
    return bytes(rom)

def psx_exe() -> bytes:
    h = bytearray(0x800)
    h[0:8] = b"PS-X EXE"
    struct.pack_into("<IIII", h, 0x10, 0x80010000, 0, 0x80010000, 0x800)
    struct.pack_into("<II", h, 0x30, 0x801FFF00, 0)
    h[0x4C:0x4C + 16] = b"PRIVYHUB FIXTURE"
    body = bytearray(0x800)
    struct.pack_into("<II", body, 0, 0x1000FFFF, 0)       # beq zero, zero, -1; nop
    return bytes(h + body)
