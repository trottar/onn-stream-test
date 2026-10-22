#!/usr/bin/env python3
"""B4: the generated privyhub-session.cfg, masked hash (network_cmd_port masked; one synthetic project root), from the
predecessor emulator_manager.py and from B4's, flag absent / partial / on per core. Writes config_hashes.txt.
    python3 -B docs/memory/evidence/b4_2026-10-22/config_hashes.py"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tests" / "input_hold_rewind"))
import test_hold_rewind as T  # noqa: E402
pred, new = HERE / "predecessors/companion/games/emulator_manager.py", ROOT / "companion/games/emulator_manager.py"
ON = {"PRIVYHUB_INPUT_HOLD": "250", "PRIVYHUB_INPUT_HOLD_REWIND": "1"}
rows = [("predecessor (HEAD), no flag", pred, {}, None), ("B4, no flag", new, {}, None),
        ("B4, PRIVYHUB_INPUT_HOLD=250 only", new, {"PRIVYHUB_INPUT_HOLD": "250"}, None),
        ("B4, HOLD=250 + REWIND=yes (ignored)", new, dict(ON, PRIVYHUB_INPUT_HOLD_REWIND="yes"), None),
        ("B4, REWIND=1 without HOLD", new, {"PRIVYHUB_INPUT_HOLD_REWIND": "1"}, None),
        ("B4, HOLD=0 (invalid) + REWIND=1", new, {"PRIVYHUB_INPUT_HOLD": "0", "PRIVYHUB_INPUT_HOLD_REWIND": "1"}, None)]
for core in ("snes9x_libretro.so", "bsnes_libretro.so", "mednafen_psx_hw_libretro.so", "fceumm_libretro.so"):
    rows.append((f"B4, flag on, {core}", new, ON, core))
rows.append(("B4, flag on, CAP=10, mednafen_psx_hw_libretro.so", new, dict(ON, PRIVYHUB_INPUT_HOLD_REWIND_CAP="10"),
             "mednafen_psx_hw_libretro.so"))
out, base = [], None
for name, mod, env, core in rows:
    r = T.generate(mod, env, core)
    base = base or r["text"]
    extra = r["text"][len(base):] if r["text"].startswith(base) else "(not a suffix of the predecessor's)"
    size = [l for l in extra.splitlines() if l.startswith("rewind_buffer_size")]
    out.append(f"{r['sha256']}  {name}" + (f"  [+{len(extra.splitlines()) - 2} lines; {size[0]}]" if extra else ""))
out.append("")
out.append("The block appended with the flag on (snes9x, cap 30):")
out.append(T.hr.config_block("snes9x_libretro.so", ON))
(HERE / "config_hashes.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
