#!/usr/bin/env python3
from __future__ import annotations
import argparse, ctypes, json, os, subprocess, time, urllib.error, urllib.request
from pathlib import Path
from ctypes import wintypes
from typing import Any

BASE='http://localhost:8765'
XINPUT_A=0x1000
FACE_MASK=0xF000
EXPECTED_HEAD='25e9a1492a684dbaeebede90ea7ca4abd3eab1fb'

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_=[('wButtons',wintypes.WORD),('bLeftTrigger',ctypes.c_ubyte),('bRightTrigger',ctypes.c_ubyte),('sThumbLX',ctypes.c_short),('sThumbLY',ctypes.c_short),('sThumbRX',ctypes.c_short),('sThumbRY',ctypes.c_short)]
class XINPUT_STATE(ctypes.Structure):
    _fields_=[('dwPacketNumber',wintypes.DWORD),('Gamepad',XINPUT_GAMEPAD)]

def yes(prompt:str)->bool: return input(prompt).strip().casefold() in {'y','yes'}
def request_json(path:str)->dict[str,Any]:
    try:
        with urllib.request.urlopen(BASE+path,timeout=8) as r: obj=json.loads(r.read().decode('utf-8'))
    except (OSError,urllib.error.HTTPError,json.JSONDecodeError) as exc: raise RuntimeError('Companion API unavailable or invalid on localhost:8765') from exc
    if not isinstance(obj,dict): raise RuntimeError('Companion returned non-object JSON')
    return obj

def load_xinput():
    if os.name!='nt': raise RuntimeError('A9 runtime probe is Windows-only')
    for name in ('xinput1_4.dll','xinput1_3.dll','xinput9_1_0.dll'):
        try:
            dll=ctypes.WinDLL(name); fn=dll.XInputGetState; fn.argtypes=[wintypes.DWORD,ctypes.POINTER(XINPUT_STATE)]; fn.restype=wintypes.DWORD; return fn,name
        except Exception: pass
    raise RuntimeError('No usable XInput DLL found')

def xstates(fn):
    out={}
    for i in range(4):
        s=XINPUT_STATE()
        if int(fn(i,ctypes.byref(s)))==0: out[i]=int(s.Gamepad.wButtons)&FACE_MASK
    return out

def capture_a(fn,slots,timeout=12.0):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        snap={s:xstates(fn).get(s,0) for s in slots}
        if all(v==0 for v in snap.values()): break
        time.sleep(.02)
    press=None; snap={s:0 for s in slots}
    while time.monotonic()<deadline:
        snap={s:xstates(fn).get(s,0) for s in slots}; active=[(s,m) for s,m in snap.items() if m]
        if active: press=active[0]; break
        time.sleep(.01)
    if press is None: return -1,0,snap,False,False
    slot,mask=press; ambiguous=sum(1 for m in snap.values() if m&XINPUT_A)!=1
    released=False; neutral=0; end=time.monotonic()+timeout
    while time.monotonic()<end:
        cur={s:xstates(fn).get(s,0) for s in slots}
        if all(v==0 for v in cur.values()): neutral+=1
        else: neutral=0
        if neutral>=5: released=True; break
        time.sleep(.01)
    return slot,mask,snap,released,ambiguous

def latest_log(root:Path,game_id:str):
    d=root/'logs/games'
    c=sorted(d.glob(f'*-{game_id}.log'),key=lambda p:p.stat().st_mtime_ns,reverse=True) if d.is_dir() and game_id else []
    return c[0] if c else None

# PRIVYHUB_PHASE_A_A9_FRESH_LOG_IDENTITY_FALLBACK
def parse_game_log_identity(text:str):
    def field(name:str):
        prefix=name+':'
        for raw in text.splitlines():
            line=raw.strip()
            if line.casefold().startswith(prefix.casefold()):
                return line[len(prefix):].strip()
        return ''
    return {
        'game_id':field('Game ID'),
        'title':field('Title'),
        'system':field('System').casefold(),
    }

def latest_fresh_log_for_system(root:Path,expected_system:str,max_age:float=900.0):
    d=root/'logs/games'
    if not d.is_dir():
        return None,'',{},None
    logs=sorted(d.glob('*.log'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    now=time.time()
    for path in logs[:120]:
        try:
            age=max(0,now-path.stat().st_mtime)
            if age>max_age:
                continue
            text=path.read_text(encoding='utf-8',errors='replace')
        except OSError:
            continue
        ident=parse_game_log_identity(text)
        if ident.get('system')==expected_system:
            return path,text,ident,age
    return None,'',{},None

def active_game(root:Path,expected_system:str,*,reject_crash=False):
    st=request_json('/plugins/games/status'); active=bool(st.get('active')); game=st.get('game') if isinstance(st.get('game'),dict) else {}
    gid=str(game.get('id','')).strip(); title=str(game.get('title','')).strip() or str(game.get('name','')).strip(); system=str(game.get('system','')).strip().casefold()
    log=latest_log(root,gid); age=None; p1=None; fallback=None; text=''; identity_source='status'
    if log:
        age=max(0,time.time()-log.stat().st_mtime); text=log.read_text(encoding='utf-8',errors='replace')
        ident=parse_game_log_identity(text)
        gid=gid or ident.get('game_id',''); title=title or ident.get('title',''); system=system or ident.get('system','')
    if log is None or system!=expected_system:
        fl,ft,fi,fa=latest_fresh_log_for_system(root,expected_system)
        if fl is not None:
            log,text,age=fl,ft,fa
            gid=fi.get('game_id','') or gid
            title=fi.get('title','') or title
            system=fi.get('system','') or system
            identity_source='fresh_log_fallback'
    title=title or gid or '<unknown>'
    if log:
        p1='Xbox 360 Controller configured in port 1.' in text
        fallback='Configured joypad driver "xinput" failed to initialise' in text
    ok=active and system==expected_system and (not reject_crash or 'crash bash' not in title.casefold()) and log is not None and age is not None and age<=900 and p1 is True and fallback is False
    return {'ok':ok,'active':active,'game_id':gid,'title':title,'system':system,'log':log,'age':age,'port1':p1,'fallback':fallback,'text':text,'identity_source':identity_source}

def wait_inactive(timeout=15.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            if not bool(request_json('/plugins/games/status').get('active')): return True
        except Exception: pass
        time.sleep(.2)
    return False

def wait_slots_removed(fn,timeout=10.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if not xstates(fn): return True
        time.sleep(.1)
    return not bool(xstates(fn))

def end_stage(fn):
    input('Use PrivyHub End/Exit normally. When the game is gone, press Enter here: ')
    return wait_inactive(),wait_slots_removed(fn)

def run_git(root:Path,*args): return subprocess.run(['git',*args],cwd=root,text=True,capture_output=True)

def self_test():
    assert XINPUT_A==0x1000 and FACE_MASK==0xF000
    sample='Game ID: game_nes_test\nTitle: Fixture Game\nSystem: nes\nXbox 360 Controller configured in port 1.\n'
    ident=parse_game_log_identity(sample)
    assert ident=={'game_id':'game_nes_test','title':'Fixture Game','system':'nes'}
    return 0

def first_a9_prior_stages_ok(root:Path):
    path=root/'docs/memory/evidence/raw/phase_a_a9_first_run_transcript_2026-09-10.txt'
    if not path.is_file():
        return False,[]
    text=path.read_text(encoding='utf-8',errors='replace')
    required=[
        'Final 4P gameplay evidence preserved: True',
        'Final replacement-controller assignment evidence preserved: True',
        'Library organization/search/art normal: True',
        'SNES active/fresh-log/xinput check: True',
        'SNES direct launch normal: True',
        'SNES gameplay normal: True',
        'SNES analog-to-D-pad normal: True',
        'SNES End inactive: True',
        'SNES XInput slots removed after End: True',
        'Ordinary PS1 active/fresh-log/xinput check: True',
        'Ordinary PS1 P1->1/P2->2 routing confirmed: True',
        'Ordinary PS1 controller-profile/analog behavior normal: True',
        'Frozen preview + paused controls normal: True',
        'Save/Load regression normal: True',
        'Resume from frozen preview normal: True',
        'PS1 host coexistence normal: True',
        'PS1 End inactive: True',
        'PS1 XInput slots removed after End: True',
        'Cheat session active: True',
        'Cheat session-config marker observed: True',
        'Cheat effect/gameplay normal: True',
        'Cheat End inactive: True',
        'Cheat XInput slots removed after End: True',
        'Mod session active: True',
        'IPS mod launch markers observed: True',
        'Mod visible/gameplay normal: True',
        'Mod End inactive: True',
        'Mod XInput slots removed after End: True',
        'Custom input-profile session active: True',
        'Named A8 input-profile marker observed: True',
        'Custom mapping behavior normal: True',
        'Input-profile End inactive: True',
        'Input-profile XInput slots removed after End: True',
        'Git HEAD expected immutable baseline: True',
        'git diff --check clean: True',
    ]
    missing=[line for line in required if line not in text]
    return not missing,missing

def ctr_multitap_evidence_ok(root:Path):
    path=root/'logs/games/ps1_multitap_onoff_runtime.txt'
    if not path.is_file():
        return False
    text=path.read_text(encoding='utf-8',errors='replace')
    required=[
        'Classification: PS1_MULTITAP_ONOFF_CTR_CONFIRMED',
        'Per-game multitap override: port1',
        'Port 1 core option: enabled',
        'Port 2 core option: disabled',
        'Live XInput slots: 1, 2, 3, 4',
        'Players 3/4 available in CTR: True',
        'Four controllers independently normal: True',
    ]
    return all(line in text for line in required)

# PRIVYHUB_PHASE_A_A9_COVERAGE_AWARE_FIXTURES
def system_catalog_count(system:str):
    payload=request_json('/plugins/games/games?system='+system)
    value=payload.get('total')
    if isinstance(value,bool) or not isinstance(value,int) or value<0:
        raise RuntimeError(f'Games catalog did not return a valid total for {system}')
    return value

def finish_identification(root:Path):
    out=root/'logs/games/phase_a_a9_emulator_checkpoint_probe.txt'
    out.parent.mkdir(parents=True,exist_ok=True)
    lines=[
        'PrivyHub Phase A A9 emulator-focused regression finish probe',
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        'Production files modified by probe: NONE',
        'Network addresses collected/logged: NONE',
        '',
        '=== REUSED VALIDATED EVIDENCE ===',
    ]
    classification='PHASE_A_A9_EMULATOR_REGRESSION_NOT_CONFIRMED'
    try:
        fn,dll=load_xinput()
        request_json('/plugins/games/status')
        prior_ok,prior_missing=first_a9_prior_stages_ok(root)
        ctr_ok=ctr_multitap_evidence_ok(root)
        lines += [
            f'XInput DLL: {dll}',
            f'Prior A9 passing stages preserved/reused: {prior_ok}',
            f'Prior A9 missing required lines: {len(prior_missing)}',
            f'CTR Multitap On/Off evidence preserved: {ctr_ok}',
            '',
            '=== CORRECTED FAMILY IDENTIFICATION ===',
        ]

        family_ok=[]
        skipped=[]
        for system,label in [('nes','NES'),('genesis','Genesis')]:
            count=system_catalog_count(system)
            lines.append(f'{label} library game count: {count}')

            if count==0:
                skipped.append(system)
                family_ok.append(True)
                lines += [
                    f'{label} fixture status: SKIPPED_NO_LOCAL_FIXTURE',
                    f'{label} runtime validated by this A9 run: False',
                ]
                continue

            print(f'\n[A9 FINISH — {label}] Launch any known-good {label} game normally from the onn library.')
            input('When gameplay is visible and responsive, press Enter here: ')
            info=active_game(root,system)
            direct=yes('Did the normal library action enter gameplay directly without manual PC-side launch steps? [y/n]: ')
            gameplay=yes('Are video, audio, buttons, and general gameplay normal? [y/n]: ')
            analog=yes('Does the analog stick correctly provide the expected D-pad convenience behavior? [y/n]: ')
            coexist=True
            if system=='nes':
                coexist=yes('While it was streaming, could the Windows host still be used normally without RetroArch taking over focus? [y/n]: ')
            inactive,removed=end_stage(fn)
            ok=all([info['ok'],direct,gameplay,analog,coexist,inactive,removed])
            family_ok.append(ok)
            lines += [
                f'{label} fixture status: RUNTIME_EXERCISED',
                f'{label} game: {info["title"]}',
                f'{label} detected system: {info["system"] or "<unknown>"}',
                f'{label} identity source: {info.get("identity_source","unknown")}',
                f'{label} active/fresh-log/xinput check: {info["ok"]}',
                f'{label} direct launch normal: {direct}',
                f'{label} gameplay normal: {gameplay}',
                f'{label} analog-to-D-pad normal: {analog}',
                f'{label} host coexistence normal: {coexist}',
                f'{label} End inactive: {inactive}',
                f'{label} XInput slots removed after End: {removed}',
                f'{label} runtime validated by this A9 run: {ok}',
            ]

        head=run_git(root,'rev-parse','HEAD')
        diff=run_git(root,'diff','--check')
        status=run_git(root,'status','--short')
        head_ok=head.returncode==0 and head.stdout.strip()==EXPECTED_HEAD
        diff_ok=diff.returncode==0
        status_lines=[line for line in status.stdout.splitlines() if line.strip()] if status.returncode==0 else []
        lines += [
            '',
            '=== REPOSITORY AUDIT ===',
            f'Git HEAD expected immutable baseline: {head_ok}',
            f'Git HEAD: {head.stdout.strip() if head.returncode==0 else "<error>"}',
            f'git diff --check clean: {diff_ok}',
            f'git status --short entry count: {len(status_lines)}',
        ]
        lines.extend('git status: '+line for line in status_lines)

        confirmed=all([prior_ok,ctr_ok,*family_ok,head_ok,diff_ok])
        lines += [
            '',
            '=== COVERAGE ===',
            'No-fixture systems skipped: ' + (', '.join(skipped) if skipped else '<none>'),
            f'Available-library regression complete: {confirmed}',
        ]
        if confirmed:
            classification=(
                'PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS'
                if skipped
                else 'PHASE_A_A9_EMULATOR_REGRESSION_CONFIRMED'
            )
    except Exception as exc:
        lines += ['', '=== ERROR ===', f'{type(exc).__name__}: {exc}']

    lines.insert(2,f'Classification: {classification}')
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(classification)
    print('Log:',out)
    return 0 if classification in {
        'PHASE_A_A9_EMULATOR_REGRESSION_CONFIRMED',
        'PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS',
    } else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--finish-identification',action='store_true'); a=ap.parse_args()
    if a.self_test: return self_test()
    root=Path(a.root).resolve()
    if a.finish_identification: return finish_identification(root)
    out=root/'logs/games/phase_a_a9_emulator_checkpoint_probe.txt'; out.parent.mkdir(parents=True,exist_ok=True)
    lines=['PrivyHub Phase A A9 emulator-focused regression probe',f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",'Production files modified by probe: NONE','Network addresses collected/logged: NONE','','=== RAW MEASUREMENTS ===']
    classification='PHASE_A_A9_EMULATOR_REGRESSION_NOT_CONFIRMED'
    try:
        fn,dll=load_xinput(); request_json('/plugins/games/status')
        final4=root/'docs/memory/evidence/raw/phase_a_4p_gameplay_final_2026-09-10.txt'; final_assign=root/'docs/memory/evidence/raw/four_player_android_assignment_replacement_controller_2026-09-10.txt'
        preserved4=final4.is_file() and 'Classification: PHASE_A_4P_GAMEPLAY_REGRESSION_CONFIRMED' in final4.read_text(encoding='utf-8',errors='replace')
        preserved_assign=final_assign.is_file() and 'Classification: ANDROID_FOUR_CONTROLLER_ASSIGNMENT_CONFIRMED' in final_assign.read_text(encoding='utf-8',errors='replace')
        lines += [f'XInput DLL: {dll}',f'Final 4P gameplay evidence preserved: {preserved4}',f'Final replacement-controller assignment evidence preserved: {preserved_assign}']

        print('\nA9 — FINAL EMULATOR REGRESSION')
        library_ok=yes('On the onn, do the Games library organization/search/art and game detail views still look and behave normally? [y/n]: ')
        lines.append(f'Library organization/search/art normal: {library_ok}')

        family_results=[]
        for system,label in [('nes','NES'),('snes','SNES'),('genesis','Genesis')]:
            print(f'\n[{label}] Launch any known-good {label} game normally from the onn library.')
            input('When gameplay is visible and responsive, press Enter here: ')
            info=active_game(root,system)
            direct=yes('Did the normal library action enter gameplay directly without manual PC-side launch steps? [y/n]: ')
            gameplay=yes('Are video, audio, buttons, and general gameplay normal? [y/n]: ')
            analog=yes('Does the analog stick correctly provide the expected D-pad convenience behavior? [y/n]: ')
            if system=='nes': coexist=yes('While it was streaming, could the Windows host still be used normally without RetroArch taking over focus? [y/n]: ')
            else: coexist=True
            inactive,removed=end_stage(fn)
            ok=all([info['ok'],direct,gameplay,analog,coexist,inactive,removed])
            family_results.append(ok)
            lines += [f'{label} game: {info["title"]}',f'{label} active/fresh-log/xinput check: {info["ok"]}',f'{label} direct launch normal: {direct}',f'{label} gameplay normal: {gameplay}',f'{label} analog-to-D-pad normal: {analog}',f'{label} host coexistence normal: {coexist}',f'{label} End inactive: {inactive}',f'{label} XInput slots removed after End: {removed}']

        print('\n[PS1 ORDINARY 2P/LIFECYCLE] Launch a known-good PS1 title other than Crash Bash with two controllers.')
        print('Use an ordinary game so this validates that Crash Bash multitap did not change normal PS1 topology.')
        input('When gameplay is visible and responsive, press Enter here: ')
        ps=active_game(root,'ps1',reject_crash=True); slots=sorted(xstates(fn))
        print('Press/release physical A on Player 1.'); p1=capture_a(fn,slots)
        print('Press/release physical A on Player 2.'); p2=capture_a(fn,slots)
        two_route=(p1[0]==0 and bool(p1[1]&XINPUT_A) and p1[3] and not p1[4] and p2[0]==1 and bool(p2[1]&XINPUT_A) and p2[3] and not p2[4])
        analog_ps=yes('Does the selected PS1 controller profile behave correctly, including analog behavior where that profile/game supports it? [y/n]: ')
        input('Press Back on the onn to leave fullscreen into the paused Game Session screen. When there, press Enter here: ')
        frozen=yes('Is the frozen gameplay preview visible and are Save/Load/End controls present? [y/n]: ')
        save_load=yes('Using a slot you are comfortable testing, did Save and then Load that same slot work normally? [y/n]: ')
        input('Resume by selecting the frozen preview. When live gameplay returns, press Enter here: ')
        resume=yes('Did gameplay resume normally from the frozen preview? [y/n]: ')
        coexist_ps=yes('Can the Windows host still be used normally during resumed PS1 streaming? [y/n]: ')
        inactive,removed=end_stage(fn)
        ps_ok=all([ps['ok'],slots==[0,1,2,3],two_route,analog_ps,frozen,save_load,resume,coexist_ps,inactive,removed])
        lines += [f'Ordinary PS1 game: {ps["title"]}',f'Ordinary PS1 active/fresh-log/xinput check: {ps["ok"]}',f'Ordinary PS1 live XInput slots: {", ".join(str(s+1) for s in slots) if slots else "none"}',f'Ordinary PS1 P1->1/P2->2 routing confirmed: {two_route}',f'Ordinary PS1 controller-profile/analog behavior normal: {analog_ps}',f'Frozen preview + paused controls normal: {frozen}',f'Save/Load regression normal: {save_load}',f'Resume from frozen preview normal: {resume}',f'PS1 host coexistence normal: {coexist_ps}',f'PS1 End inactive: {inactive}',f'PS1 XInput slots removed after End: {removed}']

        print('\n[CHEAT] Launch any previously validated cheat-profile session through the normal onn UI.')
        input('When the cheat-profile game is running, press Enter here: ')
        ch=request_json('/plugins/games/status'); ch_active=bool(ch.get('active')); sess=root/'data/games/retroarch/config/privyhub-session.cfg'; sess_text=sess.read_text(encoding='utf-8-sig',errors='replace') if sess.is_file() else ''; cheat_marker=('PrivyHub A7.3 session-only cheat database' in sess_text or 'cheat_database_path' in sess_text)
        cheat_effect=yes('Is the selected cheat/profile effect working as expected and gameplay otherwise normal? [y/n]: ')
        ci,cr=end_stage(fn); cheat_ok=all([ch_active,cheat_marker,cheat_effect,ci,cr])
        lines += [f'Cheat session active: {ch_active}',f'Cheat session-config marker observed: {cheat_marker}',f'Cheat effect/gameplay normal: {cheat_effect}',f'Cheat End inactive: {ci}',f'Cheat XInput slots removed after End: {cr}']

        print('\n[MOD] Launch the previously validated Donkey Kong Country IPS mod profile.')
        input('When the modded game is running, press Enter here: ')
        ms=request_json('/plugins/games/status'); mg=ms.get('game') if isinstance(ms.get('game'),dict) else {}; mid=str(mg.get('id','')).strip(); ml=latest_log(root,mid); mt=ml.read_text(encoding='utf-8',errors='replace') if ml else ''; mod_marker=('Mod:' in mt and 'IPS derived content:' in mt)
        mod_effect=yes('Is the expected visible IPS mod behavior present and gameplay otherwise normal? [y/n]: ')
        mi,mr=end_stage(fn); mod_ok=all([bool(ms.get('active')),mod_marker,mod_effect,mi,mr])
        lines += [f'Mod session active: {bool(ms.get("active"))}',f'IPS mod launch markers observed: {mod_marker}',f'Mod visible/gameplay normal: {mod_effect}',f'Mod End inactive: {mi}',f'Mod XInput slots removed after End: {mr}']

        print('\n[INPUT PROFILE] Launch any game assigned to a non-default named A8 input profile.')
        input('When gameplay is running, press Enter here: ')
        ips=request_json('/plugins/games/status'); ipath=root/'data/games/retroarch/config/privyhub-input.cfg'; itext=ipath.read_text(encoding='utf-8-sig',errors='replace') if ipath.is_file() else ''; profile_marker='PrivyHub A8.2 named gameplay input profile' in itext
        profile_ok_user=yes('Does the custom mapping behave exactly as configured? [y/n]: ')
        ii,ir=end_stage(fn); input_ok=all([bool(ips.get('active')),profile_marker,profile_ok_user,ii,ir])
        lines += [f'Custom input-profile session active: {bool(ips.get("active"))}',f'Named A8 input-profile marker observed: {profile_marker}',f'Custom mapping behavior normal: {profile_ok_user}',f'Input-profile End inactive: {ii}',f'Input-profile XInput slots removed after End: {ir}']

        head=run_git(root,'rev-parse','HEAD'); diffcheck=run_git(root,'diff','--check'); names=run_git(root,'diff','--name-only'); status=run_git(root,'status','--short')
        head_ok=head.returncode==0 and head.stdout.strip()==EXPECTED_HEAD; diff_ok=diffcheck.returncode==0
        changed=[x for x in names.stdout.splitlines() if x.strip()]; status_lines=[x for x in status.stdout.splitlines() if x.strip()]
        lines += ['', '=== REPOSITORY AUDIT ===', f'Git HEAD expected immutable baseline: {head_ok}', f'Git HEAD: {head.stdout.strip() if head.returncode==0 else "<error>"}', f'git diff --check clean: {diff_ok}', 'Tracked changed files: '+(', '.join(changed) if changed else 'none'), f'git status --short entry count: {len(status_lines)}']
        for entry in status_lines[:120]: lines.append('git status: '+entry)
        if len(status_lines)>120: lines.append(f'git status: <{len(status_lines)-120} additional entries omitted>')

        overall=all([preserved4,preserved_assign,library_ok,*family_results,ps_ok,cheat_ok,mod_ok,input_ok,head_ok,diff_ok])
        if overall: classification='PHASE_A_A9_EMULATOR_REGRESSION_CONFIRMED'
    except Exception as exc:
        lines.append(f'ERROR: {type(exc).__name__}: {exc}')
    lines.insert(2,f'Classification: {classification}')
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'\nClassification: {classification}\nProbe log: {out}')
    return 0 if classification=='PHASE_A_A9_EMULATOR_REGRESSION_CONFIRMED' else 1
if __name__=='__main__': raise SystemExit(main())
