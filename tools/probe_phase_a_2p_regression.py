#!/usr/bin/env python3
from __future__ import annotations
import argparse, ctypes, json, os, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any

BASE = "http://localhost:8765"
XINPUT_A = 0x1000
FACE_MASK = 0xF000

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_=[("wButtons",ctypes.c_ushort),("bLeftTrigger",ctypes.c_ubyte),("bRightTrigger",ctypes.c_ubyte),("sThumbLX",ctypes.c_short),("sThumbLY",ctypes.c_short),("sThumbRX",ctypes.c_short),("sThumbRY",ctypes.c_short)]
class XINPUT_STATE(ctypes.Structure):
    _fields_=[("dwPacketNumber",ctypes.c_uint32),("Gamepad",XINPUT_GAMEPAD)]

def request_json(path:str)->dict[str,Any]:
    req=urllib.request.Request(BASE+path,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=5) as r: payload=json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body=exc.read().decode("utf-8",errors="replace"); raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except OSError as exc:
        raise RuntimeError("Companion API is unavailable on localhost:8765. Start the companion before running this probe.") from exc
    if not isinstance(payload,dict): raise RuntimeError("Companion API returned a non-object payload")
    return payload

def load_xinput():
    if os.name!="nt": raise RuntimeError("This runtime probe is Windows-only")
    errors=[]
    for name in ("xinput1_4.dll","xinput1_3.dll","xinput9_1_0.dll"):
        try:
            dll=ctypes.WinDLL(name); fn=dll.XInputGetState; fn.argtypes=[ctypes.c_uint,ctypes.POINTER(XINPUT_STATE)]; fn.restype=ctypes.c_uint; return fn,name
        except Exception as exc: errors.append(f"{name}: {exc}")
    raise RuntimeError("Unable to load XInputGetState: "+"; ".join(errors))

def states(get_state)->dict[int,int]:
    out={}
    for i in range(4):
        st=XINPUT_STATE()
        if int(get_state(i,ctypes.byref(st)))==0: out[i]=int(st.Gamepad.wButtons)
    return out

def snapshot(get_state,slots:list[int])->dict[int,int]:
    s=states(get_state); return {slot:int(s.get(slot,0))&FACE_MASK for slot in slots}

def capture_a(get_state,slots:list[int],timeout:float=12.0):
    deadline=time.monotonic()+timeout; neutral=0; last={slot:0 for slot in slots}
    while time.monotonic()<deadline:
        last=snapshot(get_state,slots)
        if all(v==0 for v in last.values()):
            neutral+=1
            if neutral>=5: break
        else: neutral=0
        time.sleep(0.01)
    press_slot=-1; press_mask=0; press=dict(last)
    while time.monotonic()<deadline:
        snap=snapshot(get_state,slots); active=[(slot,mask) for slot,mask in snap.items() if mask]
        if active: press=dict(snap); press_slot,press_mask=active[0]; break
        time.sleep(0.01)
    if press_slot<0: return -1,0,press,False,False
    ambiguous=sum(1 for mask in press.values() if mask & XINPUT_A)!=1
    release_deadline=time.monotonic()+timeout; neutral=0; released=False
    while time.monotonic()<release_deadline:
        snap=snapshot(get_state,slots)
        if all(v==0 for v in snap.values()):
            neutral+=1
            if neutral>=5: released=True; break
        else: neutral=0
        time.sleep(0.01)
    return press_slot,press_mask,press,released,ambiguous

def yes(prompt:str)->bool: return input(prompt).strip().casefold() in {"y","yes"}

def latest_log(root:Path,game_id:str)->Path|None:
    d=root/'logs'/'games'
    if not d.is_dir() or not game_id: return None
    c=sorted(d.glob(f"*-{game_id}.log"),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    return c[0] if c else None

def wait_inactive(timeout=12.0):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            if not bool(request_json('/plugins/games/status').get('active')): return True
        except Exception: pass
        time.sleep(0.15)
    return False

def wait_slots_removed(get_state,timeout=8.0):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if not states(get_state): return True
        time.sleep(0.10)
    return not bool(states(get_state))

def self_test():
    assert FACE_MASK & XINPUT_A == XINPUT_A
    return 0

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: return self_test()
    root=Path(a.root).resolve(); out=root/'logs'/'games'/'phase_a_2p_regression_probe.txt'; out.parent.mkdir(parents=True,exist_ok=True)
    lines=['PrivyHub Phase A two-player regression probe',f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",'Production files modified by probe: NONE','Network addresses collected/logged: NONE','','=== RAW MEASUREMENTS ===']; classification='PHASE_A_2P_REGRESSION_NOT_CONFIRMED'
    try:
        get_state,dll=load_xinput(); request_json('/plugins/games/status')
        print('\nPHASE A — 2P REGRESSION')
        print('Start a previously working two-player-capable game normally from the onn with two controllers connected.')
        input('When both players can be tested in gameplay, press Enter here: ')
        status=request_json('/plugins/games/status'); active=bool(status.get('active')); game=status.get('game') if isinstance(status.get('game'),dict) else {}; game_id=str(game.get('id','')).strip(); title=str(game.get('title','')).strip() or game_id or '<unknown>'; system=str(game.get('system','')).strip() or '<unknown>'; slots=sorted(states(get_state))
        print('\nPress and release physical A once on the controller intended as Player 1.')
        p1_slot,p1_mask,p1_snap,p1_release,p1_amb=capture_a(get_state,slots)
        print('\nPress and release physical A once on the controller intended as Player 2.')
        p2_slot,p2_mask,p2_snap,p2_release,p2_amb=capture_a(get_state,slots)
        gameplay_ok=yes('Did both Player 1 and Player 2 independently control the intended in-game players normally? [y/n]: ')
        cross_control=yes('Did either controller unexpectedly control/take over the other player? [y/n]: ')
        extras_interfere=yes('Did Player 3 or Player 4 / unused controllers interfere with this two-player check? [y/n]: ')
        game_log=latest_log(root,game_id); age=None; p1cfg=p2cfg=fallback=None
        if game_log is not None:
            age=max(0.0,time.time()-game_log.stat().st_mtime); text=game_log.read_text(encoding='utf-8',errors='replace'); p1cfg='Xbox 360 Controller configured in port 1.' in text; p2cfg='Xbox 360 Controller configured in port 2.' in text; fallback='Configured joypad driver "xinput" failed to initialise' in text
        fmt=lambda snap:', '.join(f'slot {slot+1}=0x{mask:04X}' for slot,mask in sorted(snap.items()))
        lines += [f'XInput DLL: {dll}',f'Game active during capture: {active}',f'Game: {title}',f'System: {system}','Live XInput slots during gameplay: '+(', '.join(str(s+1) for s in slots) if slots else 'none'),f'Physical Player 1 A observed slot: {p1_slot+1 if p1_slot>=0 else "none"}',f'Player 1 press snapshot: {fmt(p1_snap)}',f'Player 1 A mask observed: {bool(p1_mask & XINPUT_A)}',f'Player 1 release confirmed: {p1_release}',f'Player 1 ambiguous simultaneous A: {p1_amb}',f'Physical Player 2 A observed slot: {p2_slot+1 if p2_slot>=0 else "none"}',f'Player 2 press snapshot: {fmt(p2_snap)}',f'Player 2 A mask observed: {bool(p2_mask & XINPUT_A)}',f'Player 2 release confirmed: {p2_release}',f'Player 2 ambiguous simultaneous A: {p2_amb}',f'User two-player gameplay controls normal: {gameplay_ok}',f'Unexpected P1/P2 cross-control observed: {cross_control}',f'Unused P3/P4 interference observed: {extras_interfere}',f'RetroArch game log: {str(game_log.relative_to(root)) if game_log else "<not found>"}',f'RetroArch game log age seconds: {round(age,1) if age is not None else "n/a"}',f'Port 1 Xbox autoconfig observed: {p1cfg}',f'Port 2 Xbox autoconfig observed: {p2cfg}',f'XInput startup fallback observed: {fallback}']
        print('\nNow use PrivyHub End/Exit normally. When the game is gone, press Enter.')
        input(); inactive=wait_inactive(); removed=wait_slots_removed(get_state); lines += [f'Companion session inactive after normal End/Exit: {inactive}',f'Session XInput slots removed after End/Exit: {removed}']
        ok=all([active,slots==[0,1,2,3],p1_slot==0,bool(p1_mask&XINPUT_A),p1_release,not p1_amb,p2_slot==1,bool(p2_mask&XINPUT_A),p2_release,not p2_amb,gameplay_ok,not cross_control,not extras_interfere,p1cfg is True,p2cfg is True,fallback is False,age is not None and age<=900,inactive,removed])
        if ok: classification='PHASE_A_2P_REGRESSION_CONFIRMED'
    except Exception as exc: lines.append(f'ERROR: {type(exc).__name__}: {exc}')
    lines.insert(2,f'Classification: {classification}'); out.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'\nClassification: {classification}\nProbe log: {out}'); return 0 if classification=='PHASE_A_2P_REGRESSION_CONFIRMED' else 1
if __name__=='__main__': raise SystemExit(main())
