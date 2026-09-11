#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = 'privyhub_b3_sunshine_moonlight_inventory_v1'
CLASSIFICATION = 'B3_SUNSHINE_MOONLIGHT_INVENTORY_CAPTURED'
LEGACY_TERMS = ('sunshine','moonlight','limelight','streammanager','stream manager','com.limelight')
PRESERVE_TERMS = ('windows graphics capture','h264_nvenc','nvenc','native stream','nativestreamactivity','fec','phi1','vigem','xinput')
TEXT_SUFFIXES = {'.py','.ps1','.psm1','.kt','.kts','.java','.xml','.json','.md','.txt','.toml','.yaml','.yml','.ini','.cfg','.properties','.gradle','.bat','.cmd','.sh'}
EXCLUDED_DIR_NAMES = {'.git','.gradle','__pycache__','.idea','.venv','venv','node_modules','build','out','dist'}
EXCLUDED_PREFIXES = ('archive/patch_backups/','logs/','docs/memory/evidence/raw/','media/','data/games/')
SELF_REL = 'tools/probe_b3_sunshine_moonlight_inventory.py'
INSTALL_NAME_HINTS = ('install','uninstall','setup','remove','cleanup','firewall','scheduled','task','bootstrap','provision')
PRODUCTION_PREFIXES = ('companion/','PrivyHub/app/src/')
NATIVE_PATH_HINTS = ('native','capture','encoder','audio','controller','input','udp','fec','retroarch','emulator','games/')
ADDRESS_RE = re.compile(r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)')
MAC_RE = re.compile(r'(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])')
USER_PATH_RE = re.compile(r'(?i)\b[A-Z]:\\(?:Users|Documents and Settings)\\[^\\\s]+')
ACTIVE_CODE_HINTS = ('import ','from ','new ','intent(','setpackage(','setcomponent(','startactivity(','queryintent','getpackage','package=','popen(','subprocess.','start-process','start-service','get-service','sc.exe','schtasks','streammanager(','streammanager.','sunshine.exe','moonlight.exe')
DEAD_HINTS = ('legacy','deprecated','compat','obsolete','unused','dead','historical','superseded')
SYSTEM_CATEGORIES = ('processes','services','scheduled_tasks','firewall_rules','installed_software')

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024), b''): h.update(c)
    return h.hexdigest()

def redact(text: str) -> str:
    return USER_PATH_RE.sub('<redacted-user-path>', MAC_RE.sub('<redacted-address>', ADDRESS_RE.sub('<redacted-address>', text)))

def rel(root: Path, path: Path) -> str: return path.relative_to(root).as_posix()

def excluded(relative: str, path: Path) -> bool:
    return relative == SELF_REL or any(relative.startswith(p) for p in EXCLUDED_PREFIXES) or any(part in EXCLUDED_DIR_NAMES for part in path.parts)

def safe_read(path: Path) -> str|None:
    try: data=path.read_bytes()
    except OSError: return None
    if b'\x00' in data[:8192]: return None
    for enc in ('utf-8-sig','utf-16','cp1252'):
        try: return data.decode(enc)
        except UnicodeError: pass
    return None

def is_doc(relative: str) -> bool:
    x=relative.casefold(); return x.startswith('docs/') or x.endswith('.md') or '/readme' in x or x.startswith('readme') or 'roadmap' in x or 'handoff' in x

def is_install(relative: str) -> bool:
    x=relative.casefold(); n=Path(relative).name.casefold()
    return (x.startswith('tools/') or x.startswith('scripts/') or x.startswith('install') or x.startswith('setup')) and any(h in n for h in INSTALL_NAME_HINTS)

def protected_native(relative: str, text: str) -> bool:
    x=relative.casefold()
    if not any(x.startswith(p.casefold()) for p in PRODUCTION_PREFIXES): return False
    return any(h in x for h in NATIVE_PATH_HINTS) and any(t in text.casefold() for t in PRESERVE_TERMS)

def classify(relative: str, line: str, preserve: bool):
    f=line.casefold(); s=line.strip().casefold()
    if is_doc(relative): return ('DOCUMENTATION/HISTORY','Documentation or durable engineering history.','PRESERVE_AS_HISTORY_UNLESS_DOC_CLEANUP_IS_SEPARATELY_DECIDED')
    if is_install(relative): return ('INSTALL/UNINSTALL ARTIFACT','Setup/install/removal tooling.','REMOVE_OR_REWRITE_ONLY_AFTER_RUNTIME_DEPENDENCIES_ARE_CLEARED')
    if preserve: return ('MUST PRESERVE','Containing file participates in a validated native path; do not delete the file.','INSPECT_REFERENCE_ONLY_FILE_IS_PROTECTED_NATIVE_PATH')
    if s.startswith(('#','//','/*','*','<!--')) or any(h in f for h in DEAD_HINTS): return ('DEAD COMPATIBILITY CODE','Comment/deprecation/compatibility context, not a proven execution edge.','REVIEW_FOR_REFERENCE_LEVEL_REMOVAL_IN_B4')
    if any(h in f for h in ACTIVE_CODE_HINTS) or any(relative.casefold().startswith(p.casefold()) for p in PRODUCTION_PREFIXES): return ('ACTIVE DEPENDENCY','Executable/source configuration context; conservatively treated as live.','TRACE_CALLER_OR_RUNTIME_USE_BEFORE_REMOVAL')
    return ('DEAD COMPATIBILITY CODE','Outside production code with no live execution signal.','REVIEW_FOR_REFERENCE_LEVEL_REMOVAL_IN_B4')

def scan_text(root: Path):
    occ=[]; preserve_files=[]
    for path in sorted(root.rglob('*'), key=lambda p:p.as_posix().casefold()):
        if not path.is_file(): continue
        try: relative=rel(root,path)
        except ValueError: continue
        if excluded(relative,path) or path.suffix.lower() not in TEXT_SUFFIXES: continue
        text=safe_read(path)
        if text is None: continue
        folded=text.casefold()
        legacy=[t for t in LEGACY_TERMS if t in folded]; preserve_hits=[t for t in PRESERVE_TERMS if t in folded]
        if not legacy and not preserve_hits: continue
        pguard=protected_native(relative,text)
        digest=sha256(path)
        if pguard:
            preserve_files.append({'classification':'MUST PRESERVE','path':relative,'sha256':digest,'signals':preserve_hits,'reason':'Validated native-path guard; B4 may remove specific obsolete references but must not delete this file.'})
        if not legacy: continue
        for i,line in enumerate(text.splitlines(),1):
            matched=[t for t in LEGACY_TERMS if t in line.casefold()]
            if not matched: continue
            c,r,a=classify(relative,line,pguard)
            occ.append({'classification':c,'path':relative,'line':i,'terms':matched,'text':redact(line.strip())[:700],'reason':r,'recommended_action':a,'file_sha256':digest,'protected_native_file':pguard})
    return occ,preserve_files

def scan_named(root: Path, occurrences):
    external=defaultdict(set)
    for item in occurrences:
        for term in item['terms']: external[term].add(item['path'])
    result=[]
    for path in sorted(root.rglob('*'), key=lambda p:p.as_posix().casefold()):
        try: relative=rel(root,path)
        except ValueError: continue
        if excluded(relative,path): continue
        terms=[t for t in LEGACY_TERMS if t in relative.casefold()]
        if not terms: continue
        if is_doc(relative): c='DOCUMENTATION/HISTORY'; reason='Legacy-named documentation/history artifact.'
        elif is_install(relative): c='INSTALL/UNINSTALL ARTIFACT'; reason='Legacy-named setup/install/removal artifact.'
        else:
            refs={r for t in terms for r in external.get(t,set()) if r != relative and not is_doc(r)}
            if not refs and not any(relative.casefold().startswith(p.casefold()) for p in PRODUCTION_PREFIXES): c='SAFE TO REMOVE'; reason='Dedicated legacy-named artifact has no static external non-documentation reference.'
            else: c='ACTIVE DEPENDENCY'; reason='Legacy-named artifact is referenced elsewhere or located in production source.'
        result.append({'classification':c,'path':relative,'kind':'directory' if path.is_dir() else 'file','terms':terms,'reason':reason,'sha256':sha256(path) if path.is_file() else None})
    return result

def ps_json(script: str):
    if os.name != 'nt': return False,[], 'NOT_WINDOWS'
    exe=shutil.which('powershell.exe') or shutil.which('pwsh.exe')
    if not exe: return False,[], 'POWERSHELL_NOT_FOUND'
    try:
        cp=subprocess.run([exe,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-Command',script],text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,check=False,creationflags=int(getattr(subprocess,'CREATE_NO_WINDOW',0)))
    except Exception as e: return False,[],type(e).__name__
    if cp.returncode != 0: return False,[],'COMMAND_FAILED'
    raw=cp.stdout.strip()
    if not raw: return True,[],''
    try: val=json.loads(raw)
    except json.JSONDecodeError: return False,[],'JSON_DECODE_FAILED'
    return True,(val if isinstance(val,list) else [val] if isinstance(val,dict) else []),''

def system_inventory():
    cmds={
      'processes':r'''$x=@(Get-Process -ErrorAction SilentlyContinue | ? { $_.ProcessName -match '(?i)sunshine|moonlight|limelight' } | select @{n='name';e={$_.ProcessName}},@{n='id';e={$_.Id}}); $x|ConvertTo-Json -Compress''',
      'services':r'''$x=@(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | ? { $_.Name -match '(?i)sunshine|moonlight|limelight' -or $_.DisplayName -match '(?i)sunshine|moonlight|limelight' } | select @{n='name';e={$_.Name}},@{n='display_name';e={$_.DisplayName}},@{n='state';e={$_.State}},@{n='start_mode';e={$_.StartMode}}); $x|ConvertTo-Json -Compress''',
      'scheduled_tasks':r'''$x=@(Get-ScheduledTask -ErrorAction SilentlyContinue | ? { $_.TaskName -match '(?i)sunshine|moonlight|limelight' -or $_.TaskPath -match '(?i)sunshine|moonlight|limelight' } | select @{n='task_name';e={$_.TaskName}},@{n='task_path';e={$_.TaskPath}},@{n='state';e={''+$_.State}}); $x|ConvertTo-Json -Compress''',
      'firewall_rules':r'''$x=@(Get-NetFirewallRule -ErrorAction SilentlyContinue | ? { $_.Name -match '(?i)sunshine|moonlight|limelight' -or $_.DisplayName -match '(?i)sunshine|moonlight|limelight' } | select @{n='name';e={$_.Name}},@{n='display_name';e={$_.DisplayName}},@{n='enabled';e={''+$_.Enabled}},@{n='direction';e={''+$_.Direction}},@{n='action';e={''+$_.Action}},@{n='profile';e={''+$_.Profile}}); $x|ConvertTo-Json -Compress''',
      'installed_software':r'''$r=@('HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'); $x=@(Get-ItemProperty $r -ErrorAction SilentlyContinue | ? { $_.DisplayName -match '(?i)sunshine|moonlight|limelight' } | select @{n='display_name';e={$_.DisplayName}},@{n='display_version';e={$_.DisplayVersion}},@{n='publisher';e={$_.Publisher}}); $x|ConvertTo-Json -Compress'''
    }
    out={}
    for cat in SYSTEM_CATEGORIES:
        available,items,error=ps_json(cmds[cat]); safe=[]
        for item in items:
            if not isinstance(item,dict): continue
            item={str(k):redact(v) if isinstance(v,str) else v for k,v in item.items()}
            if cat=='processes': c='ACTIVE DEPENDENCY'; reason='Matching legacy process is currently running.'
            elif cat=='services':
                state=str(item.get('state','')).casefold(); mode=str(item.get('start_mode','')).casefold(); c='ACTIVE DEPENDENCY' if state=='running' or mode in {'auto','automatic'} else 'INSTALL/UNINSTALL ARTIFACT'; reason='Legacy service registration.'
            elif cat=='scheduled_tasks':
                c='INSTALL/UNINSTALL ARTIFACT' if str(item.get('state','')).casefold()=='disabled' else 'ACTIVE DEPENDENCY'; reason='Legacy scheduled task registration.'
            else: c='INSTALL/UNINSTALL ARTIFACT'; reason='Legacy installed/system configuration artifact.'
            safe.append({'classification':c,'reason':reason,**item})
        out[cat]={'available':available,'error_code':error,'count':len(safe),'items':safe}
    return out

def file_summary(occ):
    g=defaultdict(list)
    for x in occ:g[x['path']].append(x)
    out=[]
    for p in sorted(g,key=str.casefold):
        rows=g[p]; out.append({'path':p,'occurrence_count':len(rows),'classification_counts':dict(sorted(Counter(r['classification'] for r in rows).items())),'protected_native_file':any(r['protected_native_file'] for r in rows),'file_sha256':rows[0]['file_sha256']})
    return out

def format_text(report):
    lines=['PrivyHub Phase B3 Sunshine/Moonlight dependency inventory',f'Classification: {CLASSIFICATION}',f'Schema: {SCHEMA}','Production files modified by probe: NONE','Files deleted by probe: 0','Network addresses collected/logged: NONE','','=== SUMMARY ===',f"Text occurrences: {len(report['text_occurrences'])}",f"Legacy-named artifacts: {len(report['named_artifacts'])}",f"MUST PRESERVE native guard files: {len(report['must_preserve_files'])}"]
    for c in ('ACTIVE DEPENDENCY','DEAD COMPATIBILITY CODE','INSTALL/UNINSTALL ARTIFACT','DOCUMENTATION/HISTORY','SAFE TO REMOVE','MUST PRESERVE'): lines.append(f"{c}: {report['classification_counts'].get(c,0)}")
    lines+=['',f"Disposition: {report['disposition']}",'','=== SYSTEM STATE ===']
    for cat in SYSTEM_CATEGORIES:
        s=report['system_state'][cat]; lines.append(f"{cat}: available={s['available']} count={s['count']} error={s['error_code'] or '<none>'}")
        for item in s['items']:
            display=', '.join(f'{k}={v}' for k,v in item.items() if k not in {'classification','reason'}); lines.append(f"  [{item['classification']}] {display}")
    lines+=['','=== MUST PRESERVE NATIVE GUARD ===']
    if not report['must_preserve_files']: lines.append('<none detected>')
    for x in report['must_preserve_files']: lines.append(f"[MUST PRESERVE] {x['path']} | signals={','.join(x['signals'])} | sha256={x['sha256']}")
    lines+=['','=== FILE SUMMARY ===']
    for x in report['file_summary']:
        cs=', '.join(f'{k}={v}' for k,v in x['classification_counts'].items()); lines.append(f"{x['path']} | occurrences={x['occurrence_count']} | {cs} | protected_native={x['protected_native_file']} | sha256={x['file_sha256']}")
    lines+=['','=== LEGACY-NAMED ARTIFACTS ===']
    if not report['named_artifacts']: lines.append('<none>')
    for x in report['named_artifacts']: lines.append(f"[{x['classification']}] {x['kind']} {x['path']} | terms={','.join(x['terms'])} | {x['reason']}")
    lines+=['','=== CLASSIFIED TEXT OCCURRENCES ===']
    if not report['text_occurrences']: lines.append('<none>')
    for x in report['text_occurrences']:
        lines.append(f"[{x['classification']}] {x['path']}:{x['line']} | terms={','.join(x['terms'])}"); lines.append('  text: '+(x['text'] or '<blank>')); lines.append('  reason: '+x['reason']); lines.append('  action: '+x['recommended_action'])
    lines+=['','=== NEXT STEP ===','Inspect ACTIVE DEPENDENCY and MUST PRESERVE entries before any deletion.','Use the exhaustive JSON plus this text to design the first coherent B4 removal patch.','Do not remove Sunshine/Moonlight infrastructure from this B3 probe.']
    return '\n'.join(lines)+'\n'

def self_test():
    assert classify('companion/example.py',"subprocess.run(['sunshine.exe'])",False)[0]=='ACTIVE DEPENDENCY'
    assert classify('docs/memory/MEMORY.md','Sunshine was previously used.',False)[0]=='DOCUMENTATION/HISTORY'
    assert classify('tools/remove_sunshine.ps1','Get-Service Sunshine',False)[0]=='INSTALL/UNINSTALL ARTIFACT'
    assert classify('PrivyHub/app/src/main/java/com/safeiot/privyhub/NativeStreamActivity.kt','// Moonlight compatibility',True)[0]=='MUST PRESERVE'
    sample='.'.join(('192','0','2','5')); assert '<redacted-address>' in redact('target '+sample)
    return 0

def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',default='.'); p.add_argument('--self-test',action='store_true'); a=p.parse_args()
    if a.self_test:return self_test()
    root=Path(a.root).resolve(); occ,preserve=scan_text(root); artifacts=scan_named(root,occ); system=system_inventory()
    allc=[x['classification'] for x in occ]+[x['classification'] for x in artifacts]+[x['classification'] for x in preserve]+[x['classification'] for cat in SYSTEM_CATEGORIES for x in system[cat]['items']]
    counts=Counter(allc); active=counts.get('ACTIVE DEPENDENCY',0); disp='B3_ACTIVE_DEPENDENCIES_REQUIRE_TRACE_BEFORE_B4_REMOVAL' if active else 'B3_NO_ACTIVE_DEPENDENCIES_FOUND_REVIEW_SAFE_REMOVAL_SET'
    report={'schema':SCHEMA,'classification':CLASSIFICATION,'production_files_modified_by_probe':'NONE','files_deleted_by_probe':0,'network_addresses_collected_or_logged':'NONE','classification_counts':dict(sorted(counts.items())),'file_summary':file_summary(occ),'text_occurrences':occ,'named_artifacts':artifacts,'must_preserve_files':preserve,'system_state':system,'disposition':disp}
    out=root/'logs/diagnostics'; out.mkdir(parents=True,exist_ok=True); jp=out/'b3_sunshine_moonlight_inventory.json'; tp=out/'b3_sunshine_moonlight_inventory.txt'; jp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n'); tp.write_text(format_text(report),encoding='utf-8',newline='\n'); print(CLASSIFICATION); print('Text:',tp); print('JSON:',jp); return 0

if __name__=='__main__': raise SystemExit(main())
