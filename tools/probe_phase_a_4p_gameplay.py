#!/usr/bin/env python3
from __future__ import annotations
import argparse, ctypes, json, re, time, urllib.request
from pathlib import Path
from ctypes import wintypes

XINPUT_A=0x1000
FACE_MASK=0xF000

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_=[('wButtons',wintypes.WORD),('bLeftTrigger',ctypes.c_ubyte),('bRightTrigger',ctypes.c_ubyte),('sThumbLX',ctypes.c_short),('sThumbLY',ctypes.c_short),('sThumbRX',ctypes.c_short),('sThumbRY',ctypes.c_short)]
class XINPUT_STATE(ctypes.Structure):
    _fields_=[('dwPacketNumber',wintypes.DWORD),('Gamepad',XINPUT_GAMEPAD)]

def load_xinput():
    for name in ('xinput1_4.dll','xinput1_3.dll','xinput9_1_0.dll'):
        try:
            dll=ctypes.WinDLL(name)
            fn=dll.XInputGetState; fn.argtypes=[wintypes.DWORD,ctypes.POINTER(XINPUT_STATE)]; fn.restype=wintypes.DWORD
            return fn,name
        except Exception: pass
    raise RuntimeError('No usable XInput DLL found')

def states(get_state):
    out={}
    for slot in range(4):
        s=XINPUT_STATE(); rc=int(get_state(slot,ctypes.byref(s)))
        if rc==0: out[slot]=int(s.Gamepad.wButtons)&FACE_MASK
    return out

def snapshot(get_state,slots):
    all_states=states(get_state); return {slot:all_states.get(slot,0) for slot in slots}

def capture_a(get_state,slots:list[int],timeout:float=12.0):
    deadline=time.monotonic()+timeout; neutral=0; last={slot:0 for slot in slots}
    while time.monotonic()<deadline:
        last=snapshot(get_state,slots)
        if all(v==0 for v in last.values()): neutral+=1
        else: neutral=0
        if neutral>=5: break
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
        if all(v==0 for v in snap.values()): neutral+=1
        else: neutral=0
        if neutral>=5: released=True; break
        time.sleep(0.01)
    return press_slot,press_mask,press,released,ambiguous

def request_json(path:str):
    with urllib.request.urlopen('http://localhost:8765'+path,timeout=10) as r:
        obj=json.loads(r.read().decode('utf-8'))
    if not isinstance(obj,dict): raise RuntimeError('Companion returned non-object JSON')
    return obj

def yes(prompt:str)->bool: return input(prompt).strip().casefold() in {'y','yes'}

def latest_log(root:Path,game_id:str)->Path|None:
    d=root/'logs'/'games'
    if not d.is_dir() or not game_id: return None
    c=sorted(d.glob(f'*-{game_id}.log'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
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

def core_option_evidence(root:Path):
    keys=('beetle_psx_hw_enable_multitap_port1','beetle_psx_hw_enable_multitap_port2')
    found=[]
    base=root/'data'/'games'/'retroarch'
    if not base.is_dir(): return found
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.stat().st_size>2*1024*1024: continue
        if p.suffix.casefold() not in {'.cfg','.opt','.txt',''}: continue
        try: text=p.read_text(encoding='utf-8-sig',errors='replace')
        except OSError: continue
        for line in text.splitlines():
            stripped=line.strip()
            for key in keys:
                if re.match(r'^\s*'+re.escape(key)+r'\s*=',line,re.I):
                    value=stripped.split('=',1)[1].strip().strip('"\'') if '=' in stripped else '<unparsed>'
                    try: rel=p.relative_to(root).as_posix()
                    except ValueError: rel=p.name
                    found.append((key,value,rel))
    return found

def self_test():
    assert XINPUT_A==0x1000
    return 0

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: return self_test()
    root=Path(a.root).resolve(); out=root/'logs'/'games'/'phase_a_4p_gameplay_probe.txt'; out.parent.mkdir(parents=True,exist_ok=True)
    lines=['PrivyHub Phase A representative four-player gameplay probe',f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",'Production files modified by probe: NONE','Network addresses collected/logged: NONE','','=== RAW MEASUREMENTS ===']; classification='PHASE_A_4P_GAMEPLAY_NOT_CONFIRMED'
    try:
        get_state,dll=load_xinput(); request_json('/plugins/games/status')
        print('\nPHASE A — REPRESENTATIVE 4P GAMEPLAY')
        print('On the onn, start Crash Bash (USA) normally with all four controllers connected.')
        print('Enter Battle Mode and reach a screen/session where four human players can participate.')
        input('When ready to test all four controllers, press Enter here: ')
        status=request_json('/plugins/games/status'); active=bool(status.get('active')); game=status.get('game') if isinstance(status.get('game'),dict) else {}; game_id=str(game.get('id','')).strip(); title=str(game.get('title','')).strip() or game_id or '<unknown>'; system=str(game.get('system','')).strip() or '<unknown>'; slots=sorted(states(get_state))
        captures=[]
        for player in range(1,5):
            print(f'\nPress and release physical A once on the controller intended as Player {player}.')
            captures.append(capture_a(get_state,slots))
        four_player_available=yes('Did Crash Bash Battle Mode expose four human players in this session? [y/n]: ')
        gameplay_ok=yes('Did Players 1-4 each independently control their intended in-game player? [y/n]: ')
        cross_control=yes('Did any controller unexpectedly control/take over another player? [y/n]: ')
        game_log=latest_log(root,game_id); age=None; cfg=[None]*4; fallback=None
        if game_log is not None:
            age=max(0.0,time.time()-game_log.stat().st_mtime); text=game_log.read_text(encoding='utf-8',errors='replace')
            cfg=[f'Xbox 360 Controller configured in port {i}.' in text for i in range(1,5)]
            fallback='Configured joypad driver "xinput" failed to initialise' in text
        fmt=lambda snap:', '.join(f'slot {slot+1}=0x{mask:04X}' for slot,mask in sorted(snap.items()))
        lines += [f'XInput DLL: {dll}',f'Game active during capture: {active}',f'Game: {title}',f'System: {system}','Live XInput slots during gameplay: '+(', '.join(str(s+1) for s in slots) if slots else 'none')]
        routing_ok=True
        for idx,(slot,mask,snap,released,ambiguous) in enumerate(captures,1):
            lines += [f'Physical Player {idx} A observed slot: {slot+1 if slot>=0 else "none"}',f'Player {idx} press snapshot: {fmt(snap)}',f'Player {idx} A mask observed: {bool(mask & XINPUT_A)}',f'Player {idx} release confirmed: {released}',f'Player {idx} ambiguous simultaneous A: {ambiguous}']
            routing_ok = routing_ok and slot==idx-1 and bool(mask & XINPUT_A) and released and not ambiguous
        lines += [f'Four distinct expected host routes confirmed: {routing_ok}',f'Crash Bash four-human-player exposure observed: {four_player_available}',f'User four-player gameplay controls independently normal: {gameplay_ok}',f'Unexpected cross-control observed: {cross_control}',f'RetroArch game log: {str(game_log.relative_to(root)) if game_log else "<not found>"}',f'RetroArch game log age seconds: {round(age,1) if age is not None else "n/a"}']
        for i,val in enumerate(cfg,1): lines.append(f'Port {i} Xbox autoconfig observed: {val}')
        lines.append(f'XInput startup fallback observed: {fallback}')
        opts=core_option_evidence(root)
        if opts:
            for key,value,rel in opts: lines.append(f'Core option observed: {key}={value} [{rel}]')
        else:
            lines.append('Core option observed: no explicit Beetle PSX HW multitap setting found under data/games/retroarch')
        print('\nNow use PrivyHub End/Exit normally. When the game is gone, press Enter.')
        input(); inactive=wait_inactive(); removed=wait_slots_removed(get_state); lines += [f'Companion session inactive after normal End/Exit: {inactive}',f'Session XInput slots removed after End/Exit: {removed}']
        infra_ok=all([active,system.casefold()=='ps1','crash bash' in title.casefold(),slots==[0,1,2,3],routing_ok,*[x is True for x in cfg],fallback is False,age is not None and age<=900,inactive,removed])
        if infra_ok and four_player_available and gameplay_ok and not cross_control:
            classification='PHASE_A_4P_GAMEPLAY_REGRESSION_CONFIRMED'
        elif infra_ok:
            classification='PHASE_A_4P_HOST_ROUTING_CONFIRMED_GAMEPLAY_NOT_CONFIRMED'
    except Exception as exc:
        lines.append(f'ERROR: {type(exc).__name__}: {exc}')
    lines.insert(2,f'Classification: {classification}'); out.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(f'\nClassification: {classification}\nProbe log: {out}'); return 0 if classification=='PHASE_A_4P_GAMEPLAY_REGRESSION_CONFIRMED' else 1
if __name__=='__main__': raise SystemExit(main())
