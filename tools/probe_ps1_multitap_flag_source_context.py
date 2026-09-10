#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'logs/games/ps1_multitap_flag_source_context.txt'

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(obj:object)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def excerpt(path:Path, needle:str, before:int, after:int)->list[str]:
    lines=path.read_text(encoding='utf-8-sig').splitlines()
    hits=[i for i,line in enumerate(lines) if needle in line]
    if len(hits)!=1:
        return [f'<needle {needle!r}: expected 1 hit, found {len(hits)}>']
    lo=max(0,hits[0]-before); hi=min(len(lines),hits[0]+after+1)
    return [f'{i+1:6d}: {lines[i]}' for i in range(lo,hi)]

def get_json(path:str)->dict:
    with urlopen('http://127.0.0.1:8765'+path, timeout=10) as r:
        obj=json.loads(r.read().decode('utf-8'))
    if not isinstance(obj,dict): raise RuntimeError('companion response is not an object')
    return obj

def candidates()->tuple[bool,list[dict],str]:
    try:
        first=get_json('/plugins/games/games?system=ps1&offset=0&limit=80')
        total=int(first.get('total',0)); nodes=list(first.get('nodes') or [])
        offset=len(nodes)
        while offset<total:
            page=get_json(f'/plugins/games/games?system=ps1&offset={offset}&limit=80')
            more=list(page.get('nodes') or [])
            if not more: break
            nodes.extend(more); offset+=len(more)
        rows=[]
        ctrl_path=ROOT/'data/games/retroarch/controller_overrides.json'
        ctrl=json.loads(ctrl_path.read_text(encoding='utf-8-sig')) if ctrl_path.is_file() else {'games':{}}
        overrides=ctrl.get('games',{}) if isinstance(ctrl,dict) else {}
        for node in nodes:
            if not isinstance(node,dict): continue
            lazy=str(node.get('lazy_path',''))
            if not lazy: continue
            detail=get_json(lazy)
            mp=int(detail.get('max_players',0) or 0)
            if mp>2:
                gid=str(detail.get('id',''))
                raw=overrides.get(gid,{}) if isinstance(overrides,dict) else {}
                mt=str(raw.get('ps1_multitap','')) if isinstance(raw,dict) else ''
                rows.append({
                    'id':gid,
                    'title':str(detail.get('title','')),
                    'max_players':mp,
                    'metadata_available':bool(detail.get('metadata_available',False)),
                    'metadata_provider':str(detail.get('metadata_provider','')),
                    'multitap_override':mt or '<unset>',
                })
        rows.sort(key=lambda x:(x['title'].casefold(),x['id']))
        return True,rows,f'total_ps1={total}'
    except Exception as exc:
        return False,[],f'{type(exc).__name__}: {exc}'

def main()->int:
    backend=ROOT/'companion/games/emulator_manager.py'
    games=ROOT/'companion/plugins/games.py'
    android=ROOT/'PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt'
    ctrl=ROOT/'data/games/retroarch/controller_overrides.json'
    lines=['PrivyHub Phase A PS1 multitap On/Off source/context + library candidate audit',
           'Production files modified by probe: NONE','Network addresses collected/logged: NONE','']
    lines+=['=== EXACT CURRENT HASHES ===',f'emulator_manager.py: {sha(backend)}',f'games.py: {sha(games)}',f'MainActivity.kt: {sha(android)}']
    try: lines.append('controller_overrides semantic sha256: '+canonical(json.loads(ctrl.read_text(encoding='utf-8-sig'))))
    except Exception as exc: lines.append('controller_overrides semantic sha256: <unavailable> '+type(exc).__name__)
    lines+=['','=== EMULATOR MANAGER: EXISTING MULTITAP ADAPTER ===',*excerpt(backend,'PS1_MULTITAP_CORE_LIBRARY',8,205),
            '','=== EMULATOR MANAGER: CONTROLLER OVERRIDE SETTER ===',*excerpt(backend,'def set_controller_profile(',6,105),
            '','=== GAMES PLUGIN: DETAILS CONTROLLER PAYLOAD ===',*excerpt(games,'# PrivyHub Phase A PS1 controller profiles',8,80),
            '','=== GAMES PLUGIN: CONTROLLER PROFILE ACTION ===',*excerpt(games,'if action == "controller-profile":',12,80),
            '','=== ANDROID: GAME OPTIONS MENU ===',*excerpt(android,'private fun showGameLibraryOptionsDialog(',8,210),
            '','=== ANDROID: CONTROLLER PROFILE UI ===',*excerpt(android,'private fun showGameControllerProfileDialog(',8,235)]
    ok,rows,note=candidates()
    lines+=['','=== LIVE PS1 MULTITAP CANDIDATES (max_players > 2) ===',f'Companion catalog available: {ok}',note,f'Candidate count: {len(rows)}']
    for row in rows:
        lines.append(json.dumps(row,sort_keys=True,ensure_ascii=True))
    ctr=any('crash team racing' in r['title'].casefold() for r in rows)
    crash=any('crash bash' in r['title'].casefold() for r in rows)
    required_context=all(x.is_file() for x in (backend,games,android)) and 'PS1_MULTITAP_CORE_LIBRARY' in backend.read_text(encoding='utf-8-sig')
    classification=('PS1_MULTITAP_FLAG_SOURCE_CONTEXT_CAPTURED_CANDIDATES_FOUND' if required_context and ok and rows else
                    'PS1_MULTITAP_FLAG_SOURCE_CONTEXT_CAPTURED_NO_CANDIDATES' if required_context and ok else
                    'PS1_MULTITAP_FLAG_SOURCE_CONTEXT_CAPTURED_METADATA_UNAVAILABLE' if required_context else
                    'PS1_MULTITAP_FLAG_SOURCE_CONTEXT_NOT_CONFIRMED')
    lines.insert(1,'Classification: '+classification)
    lines+=['',f'CTR candidate observed: {ctr}',f'Crash Bash candidate observed: {crash}']
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(classification); print('Log:',OUT)
    return 0 if required_context else 2
if __name__=='__main__': raise SystemExit(main())
