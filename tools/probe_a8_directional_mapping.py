#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); a=p.parse_args()
    root=Path(a.root).resolve(); sys.path.insert(0,str(root))
    from companion.games.emulator_manager import EmulatorManager
    profile=root/"data/games/input_profiles.json"; cfg=root/"data/games/retroarch/config/privyhub-input.cfg"; log=root/"logs/games/a8_directional_mapping_probe.txt"
    originals={x:(x.read_bytes() if x.is_file() else None) for x in (profile,cfg)}
    out=["PrivyHub A8 generalized directional mapping probe","Purpose: validate complete editor permutation capabilities and RetroArch directional bind generation."]
    result="FAIL"; restored=False
    try:
        m=EmulatorManager(root); caps=m.input_profiles()["capabilities"]
        targets=list(caps.get("editor_targets",[])); sources=list(caps.get("editor_sources",[])); default=dict(caps.get("editor_default_mapping",{}))
        if caps.get("editor_model")!="directional_permutation_v1": raise RuntimeError("directional editor model missing")
        if len(targets)!=24 or len(sources)!=24: raise RuntimeError(f"expected 24 endpoints, got {len(targets)}/{len(sources)}")
        if set(default)!=set(targets) or set(default.values())!=set(sources) or len(set(default.values()))!=24: raise RuntimeError("default mapping is not a complete permutation")
        if not (default.get("a")=="b" and default.get("b")=="a" and default.get("x")=="y" and default.get("y")=="x"): raise RuntimeError("default Xbox/RetroPad face layout is wrong")
        out.append("24-endpoint complete Default permutation: PASS")
        p1=dict(default); p2=dict(default)
        p1["l2"]="right_stick_left"; p1["right_stick_left"]="l2"; p1["r2"]="right_stick_right"; p1["right_stick_right"]="r2"
        if len(set(p1.values()))!=24: raise RuntimeError("camera test mapping is not one-to-one")
        created=m.create_input_profile("A8 Directional Camera Probe",{"player1":p1,"player2":p2}); pid=str(created["id"])
        game={"id":"game_a8_directional_probe_000001","system":"ps1"}; m.assign_input_profile(game,pid)
        runtime=m._runtime_details(); path,metadata=m._prepare_input_override(game,runtime); text=path.read_text(encoding="utf-8")
        expected=(
            'input_player1_l2_btn = "nul"',
            'input_player1_l2_axis = "-2"',
            'input_player1_r2_btn = "nul"',
            'input_player1_r2_axis = "+2"',
            'input_player1_r_x_minus_btn = "nul"',
            'input_player1_r_x_minus_axis = "+4"',
            'input_player1_r_x_plus_btn = "nul"',
            'input_player1_r_x_plus_axis = "+5"',
        )
        missing=[x for x in expected if x not in text]
        if missing: raise RuntimeError("generated camera mapping missing: "+", ".join(missing))
        if metadata.get("input_profile_id")!=pid: raise RuntimeError("profile metadata mismatch")
        out.append("Right-stick Left -> RetroPad L2 generation: PASS")
        out.append("Right-stick Right -> RetroPad R2 generation: PASS")
        out.append("Displaced LT/RT -> RetroPad right-stick directions: PASS")
        # Existing backend must still reject duplicate physical sources.
        bad=dict(default); bad["a"]=bad["b"]
        rejected=False
        try: m.create_input_profile("A8 Duplicate Source Probe",{"player1":bad,"player2":p2})
        except Exception: rejected=True
        if not rejected: raise RuntimeError("duplicate physical source was accepted")
        out.append("Duplicate physical source rejected: PASS")
        m.assign_input_profile(game,"default"); dpath,dmeta=m._prepare_input_override(game,runtime); dtext=dpath.read_text(encoding="utf-8")
        if "PrivyHub A8.2 named gameplay input profile" in dtext: raise RuntimeError("Default emitted explicit profile binds")
        out.append("Built-in Default still preserves RetroArch autoconfig: PASS")
        result="PASS"
    except Exception as e:
        out.append(f"ERROR: {type(e).__name__}: {e}")
    finally:
        ok=True
        for path,raw in originals.items():
            try:
                if raw is None: path.unlink(missing_ok=True)
                else: path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
            except Exception as e: ok=False; out.append(f"RESTORE ERROR: {path}: {type(e).__name__}: {e}")
        restored=ok and all((path.read_bytes()==raw if raw is not None and path.is_file() else (not path.exists() if raw is None else False)) for path,raw in originals.items())
    out.append("Result: "+result); out.append("Files restored: "+str(restored)); log.parent.mkdir(parents=True,exist_ok=True); log.write_text("\n".join(out)+"\n",encoding="utf-8"); print("\n".join(out)); print("Probe log: "+str(log)); return 0 if result=="PASS" and restored else 1

if __name__=="__main__": raise SystemExit(main())
