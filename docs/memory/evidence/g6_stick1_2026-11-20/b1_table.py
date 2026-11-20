"""G6-STICK1 B1: a touch stick's push -> what the PS2 game receives, today (G6-HM4b's mapping) and new (Ds2Stick), by the
chain in the record: the sent int16 -> the hub's uinput axis unchanged (ABS_Y sign-flipped, `_invert_axis`) -> SDL
(value / 32767, or / 32768 below 0) -> PCSX2's DualShock 2 pad, AxisScale 1.33, Deadzone 0 (PCSX2.ini [Pad1]):
per direction raw = min(255, floor(v x 1.33 x 255)), merged 127 + (raw + 1) // 2 (positive) or 127 - raw // 2.
The PCSX2 step is PCSX2 2.x's DualShock 2 handling as understood, not read from its source (nothing fetched).
Run: python3 docs/memory/evidence/g6_stick1_2026-11-20/b1_table.py"""
import math

SCALE = 1.33


def today(frac, deg):
    """G6-HM4b: stickVector (dead zone 0.1, no ramp, the unit-circle clamp), then round(v x 32767)."""
    m = frac
    if m < 0.1:
        return 0, 0
    m = min(m, 1.0)
    a = math.radians(deg)
    return round(m * math.cos(a) * 32767), round(m * math.sin(a) * 32767)


def new(frac, deg, full_at=0.75):
    """G6-STICK1: dead zone 0.1, linear to full at `full_at` (0.9 first; 0.75 the user's choice), the circle to the
    square, the target / 1.33 (full sent full)."""
    if frac < 0.1:
        return 0, 0
    eff = min(1.0, max(0.0, (frac - 0.1) / (full_at - 0.1)))
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    k = 1 / max(abs(c), abs(s))
    def axis(t):
        if abs(t) >= 1 - 1e-4:
            return int(math.copysign(32767, t))
        return int(math.copysign(round(abs(t) / SCALE * 32767), t))
    return axis(eff * c * k), axis(eff * s * k)


def ds2(sent):
    """The DualShock 2 byte (0-255, centre 127) PCSX2 gives for a sent axis value, and its fraction of full."""
    if sent == 0:
        return 127, 0.0
    v = abs(sent) / (32767 if sent > 0 else 32768)
    raw = min(255, math.floor(v * SCALE * 255))
    if sent > 0:
        b = 127 + (raw + 1) // 2
        return b, (b - 127) / 128
    b = 127 - raw // 2
    return b, (127 - b) / 127


print("push (of the throw) | direction | today | STICK1 full at 0.9 (pre-registration v1) | STICK1 full at 0.75 (v2): each sent -> DS2 byte (fraction) per axis")
for deg, name in ((0, "cardinal (right)"), (45, "45-degree diagonal (up-right)")):
    for frac in (0.5, 0.75, 0.9, 1.0):
        t = today(frac, deg)
        n9 = new(frac, deg, 0.9)
        n = new(frac, deg, 0.75)
        def show(pair, axes):
            return "; ".join(f"{ax} {v} -> {ds2(v)[0]} ({ds2(v)[1]:.3f})" for ax, v in zip(axes, pair))
        axes = ("x",) if deg == 0 else ("x", "y")
        tt = t[:1] if deg == 0 else t
        nn9 = n9[:1] if deg == 0 else n9
        nn = n[:1] if deg == 0 else n
        print(f"{int(frac * 100):3d} % | {name} | {show(tt, axes)} | {show(nn9, axes)} | {show(nn, axes)}")
# where today saturates
sat = next(f / 1000 for f in range(100, 1001) if ds2(today(f / 1000, 0)[0])[1] >= 1.0)
print(f"today a cardinal push is full in PCSX2 from {sat:.3f} of the throw (1 / 1.33 = {1 / SCALE:.3f}); "
      f"a full diagonal reaches {ds2(today(1.0, 45)[0])[1]:.3f} per axis")
