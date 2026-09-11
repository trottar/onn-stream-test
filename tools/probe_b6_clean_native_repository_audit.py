#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b6_clean_native_repository_audit_v4"
READY = "B6_CLEAN_NATIVE_REPOSITORY_AUDIT_READY"
REVIEW = "B6_CLEAN_NATIVE_REPOSITORY_AUDIT_REVIEW_REQUIRED"
BASE_HEAD = "6b7c74f417e2ef14e252b9ea19afc16bdefaa50a"
ROADMAP_BASE_SHA = "2e754402c40a080b5ef906a8c200d7a3d5e1538764964ac6ef2fb82658f07294"
MAINACTIVITY_B5_SHA = "394d2b839fdb01f2988a0054b42e139e419e02207728f914e1713287992733cc"
KNOWN_INERT_LEGACY_HIT = {
    "path": "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt",
    "line": 7683,
    "pattern": "legacy_stream_host",
}

EXACT_EXPECTED = {
    "PrivyHub/app/src/main/AndroidManifest.xml",
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt",
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/diagnostics/DiagnosticsActivity.kt",
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt",
    "companion/privyhub_service.py",
    "companion/diagnostics/client_feedback.py",
    "companion/diagnostics/event_history.py",
    "companion/diagnostics/health_model.py",
    "companion/diagnostics/retention.py",
    "companion/diagnostics/runtime_health.py",
    "companion/diagnostics/self_test.py",
    "companion/diagnostics/support_bundle.py",
    "companion/plugins/games.py",
    "companion/games/stream_manager.py",
    "docs/ROADMAP.md",
    "scripts/setup_sunshine_portable.ps1",
    "scripts/install_sunshine_firewall.ps1",
    "scripts/remove_sunshine_firewall.ps1",
    "scripts/open_sunshine_web_ui.ps1",
    "scripts/install_moonlight_onn.ps1",
}
TOOL_RE = re.compile(
    r"^tools/(?:probe_b[1-6][^/]*\.py|remove_b4_8_device_moonlight_package\.py|diagnostic_retention\.py)$"
)

LEGACY_TARGETS = (
    "runtime/streaming/sunshine",
    "runtime/downloads/sunshine",
    "runtime/downloads/moonlight",
    "data/games/sunshine",
    "scripts/setup_sunshine_portable.ps1",
    "scripts/install_sunshine_firewall.ps1",
    "scripts/remove_sunshine_firewall.ps1",
    "scripts/open_sunshine_web_ui.ps1",
    "scripts/install_moonlight_onn.ps1",
    "companion/games/stream_manager.py",
)
NON_TARGETS = (
    "runtime/emulators/retroarch-nightly-20260907/info/moonlight_libretro.info",
    "runtime/emulators/retroarch-nightly-20260907/shaders/shaders_glsl/procedural/stellabialek-moonlight-sillyness.glsl",
    "runtime/emulators/retroarch-nightly-20260907/shaders/shaders_slang/procedural/stellabialek-moonlight-sillyness.slang",
    "runtime/emulators/retroarch/info/moonlight_libretro.info",
    "runtime/emulators/retroarch/RetroArch-Win64/info/moonlight_libretro.info",
    "runtime/emulators/retroarch/RetroArch-Win64/shaders/shaders_glsl/procedural/stellabialek-moonlight-sillyness.glsl",
    "runtime/emulators/retroarch/RetroArch-Win64/shaders/shaders_slang/procedural/stellabialek-moonlight-sillyness.slang",
    "runtime/emulators/retroarch/shaders/shaders_glsl/procedural/stellabialek-moonlight-sillyness.glsl",
    "runtime/emulators/retroarch/shaders/shaders_slang/procedural/stellabialek-moonlight-sillyness.slang",
)

EVIDENCE_REQUIREMENTS = {
    "docs/memory/evidence/B1_B2_COMPLETION_RUNTIME_2026-09-10.md": "B1_B2_COMPLETION_RUNTIME_CONFIRMED",
    "docs/memory/evidence/B2_GUI_ACTION_FEEDBACK_RUNTIME_2026-09-10.md": "B1_B2_GUI_ACTION_FEEDBACK_INSTALLED",
    "docs/memory/evidence/B4_8_DEVICE_MOONLIGHT_FINAL_STATE_2026-09-11.md": "B4_8_DEVICE_MOONLIGHT_REMOVAL_CONFIRMED",
    "docs/memory/evidence/B5_NATIVE_ONLY_REGRESSION_2026-09-11.md": "B5_NATIVE_ONLY_REGRESSION_RUNTIME_CONFIRMED",
}

LEGACY_PATTERNS = (
    ("com_limelight", re.compile(r"com\.limelight", re.I)),
    ("open_game_stream_client", re.compile(r"\bopenGameStreamClient\b")),
    ("stream_manager_module", re.compile(r"(?:games[./]stream_manager|companion[./]games[./]stream_manager)", re.I)),
    ("stream_manager_ctor", re.compile(r"\bStreamManager\s*\(")),
    ("legacy_stream_host", re.compile(r"(?<!native_)\bstream_host\b")),
    ("sunshine_runtime_path", re.compile(r"runtime[\\/]streaming[\\/]sunshine", re.I)),
    ("legacy_download_path", re.compile(r"runtime[\\/]downloads[\\/](?:sunshine|moonlight)", re.I)),
    ("sunshine_term", re.compile(r"\bSunshine\b")),
    ("moonlight_term", re.compile(r"\bMoonlight\b")),
)


def sha_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(root: Path, args: list[str], timeout: float=120.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, text=True, encoding='utf-8', errors='replace',
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, check=False)


def git(root: Path, *args: str, timeout: float=120.0) -> subprocess.CompletedProcess[str]:
    return run(root, ['git', *args], timeout=timeout)


def git_bytes(root: Path, *args: str, timeout: float=120.0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ['git', *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def status_entries(root: Path) -> list[dict[str,str]]:
    p=git(root,'status','--porcelain=v1','--untracked-files=all')
    if p.returncode != 0:
        raise RuntimeError('git status failed')
    out=[]
    for raw in p.stdout.splitlines():
        if not raw: continue
        status=raw[:2]
        path=raw[3:]
        if ' -> ' in path: path=path.split(' -> ',1)[1]
        out.append({'status':status,'path':path.replace('\\','/')})
    return out


def path_class(path: str, status: str) -> str:
    if path.startswith('docs/memory/evidence/raw/'):
        return 'FORBIDDEN_RAW_TRACKED_OR_VISIBLE'
    if path.startswith('docs/memory/'):
        return 'EXPECTED_DURABLE_MEMORY'
    if path in EXACT_EXPECTED:
        if path in LEGACY_TARGETS and 'D' not in status:
            return 'UNEXPECTED_LEGACY_PATH_NOT_DELETED'
        return 'EXPECTED_B_PHASE'
    if TOOL_RE.fullmatch(path):
        return 'EXPECTED_B_PHASE_TOOL'
    return 'UNEXPECTED'


def scan_legacy(root: Path) -> list[dict[str,Any]]:
    files=[]
    android=root/'PrivyHub/app/src/main'
    if android.exists():
        files += [p for p in android.rglob('*') if p.is_file() and p.suffix.lower() in {'.kt','.xml'}]
    companion=root/'companion'
    if companion.exists():
        files += [p for p in companion.rglob('*.py') if p.is_file()]
    scripts=root/'scripts'
    if scripts.exists():
        files += [p for p in scripts.glob('*.ps1') if p.is_file()]

    hits=[]
    for path in sorted(set(files)):
        try: text=path.read_text(encoding='utf-8-sig', errors='replace')
        except OSError: continue
        for lineno,line in enumerate(text.splitlines(),1):
            for name,rx in LEGACY_PATTERNS:
                if rx.search(line):
                    hits.append({'path':path.relative_to(root).as_posix(),'line':lineno,'pattern':name})
    return hits


def memory_manifest_check(root: Path) -> tuple[bool,list[str],int]:
    path=root/'docs/memory/manifest.json'
    if not path.is_file(): return False,['manifest missing'],0
    try: value=json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return False,[f'manifest invalid: {type(exc).__name__}'],0
    errors=[]
    if value.get('current_step') not in {
        'B6 clean-native repository audit',
        'C1 explicit stream profiles',
    }:
        errors.append('current_step is neither B6 audit nor C1')
    entries=value.get('files',[])
    checked=0
    for item in entries:
        if not isinstance(item,dict) or not isinstance(item.get('path'),str): continue
        rel=item['path']
        if rel.startswith('evidence/raw/'):
            continue
        # Historical manifests included manifest.json itself. Conventional
        # full-file hash/size validation of a serialized self-entry is
        # recursive, so B6 excludes/removes that self-entry.
        if rel == 'manifest.json':
            continue
        full=root/'docs/memory'/rel
        checked += 1
        if not full.is_file():
            errors.append(f'missing:{rel}')
            continue
        if item.get('sha256') != sha_file(full):
            errors.append(f'hash:{rel}')
        if item.get('bytes') != full.stat().st_size:
            errors.append(f'bytes:{rel}')
    return not errors,errors,checked


def compile_python(root: Path) -> tuple[bool,str,int]:
    targets=[]
    comp=root/'companion'
    if comp.exists(): targets += [p for p in comp.rglob('*.py') if p.is_file()]
    tools=root/'tools'
    if tools.exists(): targets += [p for p in tools.glob('*.py') if p.is_file()]
    targets=sorted(set(targets))
    try:
        with tempfile.TemporaryDirectory(prefix='privyhub_b6_pycompile_') as td:
            td=Path(td)
            for i,path in enumerate(targets):
                py_compile.compile(str(path), cfile=str(td/f'{i}.pyc'), doraise=True)
    except Exception as exc:
        return False, f'{type(exc).__name__}: {exc}', len(targets)
    return True,'',len(targets)


def compile_android(root: Path) -> tuple[bool,str]:
    project=root/'PrivyHub'
    wrapper=project/'gradlew.bat'
    if not wrapper.is_file(): return False,'Gradle wrapper missing'
    p=run(project,['cmd.exe','/d','/s','/c','gradlew.bat :app:compileDebugKotlin --no-daemon'],timeout=300.0)
    if p.returncode != 0:
        tail=p.stdout[-4000:].replace('\r',' ')
        return False, f'exit {p.returncode}: {tail}'
    return True,''


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:
        assert path_class('docs/memory/CURRENT.md',' M') == 'EXPECTED_DURABLE_MEMORY'
        assert path_class('docs/memory/evidence/raw/x.txt',' M').startswith('FORBIDDEN')
        assert path_class('tools/probe_b6_x.py','??') == 'EXPECTED_B_PHASE_TOOL'
        assert path_class('docs/ROADMAP.md',' M') == 'EXPECTED_B_PHASE'
        assert path_class('ROADMAP.md',' M') == 'UNEXPECTED'
        assert path_class('random.txt','??') == 'UNEXPECTED'
        assert not LEGACY_PATTERNS[3][1].search('NativeStreamManager(')
        assert LEGACY_PATTERNS[3][1].search('StreamManager(')
        assert KNOWN_INERT_LEGACY_HIT["line"] == 7683
        return 0

    root=Path(args.root).resolve()
    outdir=root/'logs/diagnostics'; outdir.mkdir(parents=True,exist_ok=True)
    txt=outdir/'b6_clean_native_repository_audit.txt'; js=outdir/'b6_clean_native_repository_audit.json'

    head_p=git(root,'rev-parse','HEAD'); branch_p=git(root,'branch','--show-current')
    head=head_p.stdout.strip() if head_p.returncode==0 else ''
    branch=branch_p.stdout.strip() if branch_p.returncode==0 else ''

    entries=status_entries(root)
    classified=[]
    for e in entries:
        c=path_class(e['path'],e['status']); classified.append({**e,'classification':c})
    unexpected=[e for e in classified if e['classification'].startswith('UNEXPECTED') or e['classification'].startswith('FORBIDDEN')]
    staged=[e for e in classified if e['status']!='??' and len(e['status'])>=1 and e['status'][0] != ' ']

    diff=git(root,'diff','--check')
    diff_ok=diff.returncode==0

    raw=git(root,'ls-files','--','docs/memory/evidence/raw')
    raw_tracked=[x.strip() for x in raw.stdout.splitlines() if x.strip()] if raw.returncode==0 else ['<git-ls-files-failed>']
    ignore=git(root,'check-ignore','-q','--no-index','docs/memory/evidence/raw/b6_placeholder.txt')
    raw_ignore_ok=ignore.returncode==0

    remote=git(root,'ls-remote','--heads','origin','refs/heads/main',timeout=30.0)
    remote_head=''; remote_error=''
    if remote.returncode==0 and remote.stdout.strip(): remote_head=remote.stdout.split()[0]
    else: remote_error=f'ls-remote exit {remote.returncode}'

    legacy_hits_all=scan_legacy(root)
    main_activity=root/KNOWN_INERT_LEGACY_HIT["path"]
    main_activity_sha=sha_file(main_activity) if main_activity.is_file() else ""
    inert_legacy_hits=[]
    legacy_hits=[]
    for hit in legacy_hits_all:
        if hit == KNOWN_INERT_LEGACY_HIT and main_activity_sha == MAINACTIVITY_B5_SHA:
            inert_legacy_hits.append(hit)
        else:
            legacy_hits.append(hit)
    legacy_paths_remaining=[rel for rel in LEGACY_TARGETS if (root/rel).exists()]
    non_targets_missing=[rel for rel in NON_TARGETS if not (root/rel).is_file()]

    evidence_missing=[]
    for rel,needle in EVIDENCE_REQUIREMENTS.items():
        p=root/rel
        if not p.is_file() or needle not in p.read_text(encoding='utf-8',errors='replace'):
            evidence_missing.append(rel)

    mem_ok,mem_errors,mem_checked=memory_manifest_check(root)

    roadmap=root/'docs/ROADMAP.md'
    roadmap_sha=sha_file(roadmap) if roadmap.is_file() else ''

    head_roadmap=git_bytes(root,'show','HEAD:docs/ROADMAP.md')
    head_roadmap_sha=(
        hashlib.sha256(head_roadmap.stdout).hexdigest()
        if head_roadmap.returncode==0
        else ''
    )
    head_roadmap_is_baseline=(
        head_roadmap.returncode==0
        and head_roadmap_sha==ROADMAP_BASE_SHA
    )

    roadmap_diff=git(root,'diff','--quiet','--','docs/ROADMAP.md')
    roadmap_diff_check_available=roadmap_diff.returncode in (0,1)
    roadmap_has_substantive_diff=roadmap_diff.returncode==1
    roadmap_no_substantive_diff=roadmap_diff.returncode==0

    roadmap_numstat=git(root,'diff','--numstat','--','docs/ROADMAP.md')
    roadmap_numstat_text=(
        roadmap_numstat.stdout.strip()
        if roadmap_numstat.returncode==0
        else '<unavailable>'
    )

    core_hashes={}
    for rel in (
        'PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt',
        'PrivyHub/app/src/main/AndroidManifest.xml',
        'companion/plugins/games.py',
        'tools/probe_b5_native_only_regression.py',
    ):
        p=root/rel; core_hashes[rel]=sha_file(p) if p.is_file() else '<missing>'

    py_ok,py_error,py_count=compile_python(root)
    android_ok,android_error=compile_android(root)

    checks={
        'head_expected': head==BASE_HEAD,
        'branch_main': branch=='main',
        'remote_main_expected': remote_head==BASE_HEAD,
        'no_unexpected_status_entries': not unexpected,
        'nothing_pre_staged': not staged,
        'git_diff_check': diff_ok,
        'raw_evidence_untracked': not raw_tracked,
        'raw_evidence_ignore_rule': raw_ignore_ok,
        'no_active_legacy_production_refs': not legacy_hits,
        'legacy_artifact_paths_absent': not legacy_paths_remaining,
        'retroarch_non_targets_preserved': not non_targets_missing,
        'required_phase_b_evidence_present': not evidence_missing,
        'durable_memory_manifest_consistent': mem_ok,
        'root_roadmap_present': roadmap.is_file(),
        'head_roadmap_at_pushed_v2_baseline': head_roadmap_is_baseline,
        'roadmap_diff_check_available': roadmap_diff_check_available,
        'roadmap_no_substantive_diff_from_head': roadmap_no_substantive_diff,
        'python_compile': py_ok,
        'android_kotlin_compile': android_ok,
    }
    classification=READY if all(checks.values()) else REVIEW

    data={
        'schema':SCHEMA,'classification':classification,
        'production_files_modified_by_probe':'NONE','network_addresses_collected_or_logged':'NONE',
        'head':head,'branch':branch,'remote_main_head':remote_head,'remote_error':remote_error,
        'checks':checks,'status_entries':classified,'unexpected_status_entries':unexpected,'staged_entries':staged,
        'raw_tracked':raw_tracked,'legacy_hits':legacy_hits,
        'known_inert_legacy_hits':inert_legacy_hits,
        'legacy_paths_remaining':legacy_paths_remaining,
        'non_targets_missing':non_targets_missing,'evidence_missing':evidence_missing,
        'memory_manifest_errors':mem_errors,'memory_manifest_entries_checked':mem_checked,
        'roadmap_worktree_sha256':roadmap_sha,
        'roadmap_head_blob_sha256':head_roadmap_sha,
        'roadmap_pushed_v2_baseline_sha256':ROADMAP_BASE_SHA,
        'roadmap_head_is_pushed_v2_baseline':head_roadmap_is_baseline,
        'roadmap_has_substantive_diff_from_head':roadmap_has_substantive_diff,
        'roadmap_numstat':roadmap_numstat_text,
        'core_hashes':core_hashes,'python_compile_count':py_count,'python_compile_error':py_error,
        'android_compile_error':android_error,
    }
    js.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')

    lines=[
        'PrivyHub B6 clean-native repository audit',
        f'Classification: {classification}',
        f'Schema: {SCHEMA}',
        'Production files modified by probe: NONE',
        'Network addresses collected/logged: NONE','',
        '=== CHECKPOINT PREDECESSOR ===',
        f'HEAD: {head}',f'Expected HEAD: {BASE_HEAD}',f'Branch: {branch}',
        f'Remote main HEAD: {remote_head or "<unverified>"}',f'Remote error: {remote_error or "<none>"}','',
        '=== WORKING TREE ===',f'Status entry count: {len(classified)}',f'Unexpected entry count: {len(unexpected)}',
        f'Pre-staged entry count: {len(staged)}',f'git diff --check: {diff_ok}',
    ]
    for e in classified:
        lines.append(f"  {e['status']} {e['path']} [{e['classification']}]")
    lines += ['', '=== LEGACY BOUNDARY ===',
              f'Active production legacy reference count: {len(legacy_hits)}',
              f'Known inert legacy-text count: {len(inert_legacy_hits)}',
              f'Legacy artifact paths remaining: {legacy_paths_remaining}',
              f'Preserved RetroArch non-targets missing: {non_targets_missing}']
    for h in legacy_hits:
        lines.append(f"  ACTIVE {h['path']}:{h['line']} [{h['pattern']}]")
    for h in inert_legacy_hits:
        lines.append(f"  INERT {h['path']}:{h['line']} [{h['pattern']}]")
    lines += ['', '=== DURABLE MEMORY / EVIDENCE ===',
              f'Required Phase B evidence missing: {evidence_missing}',
              f'Memory manifest consistent: {mem_ok}',f'Memory manifest entries checked: {mem_checked}',
              f'Memory manifest errors: {mem_errors}',f'Tracked raw evidence count: {len(raw_tracked)}',
              f'Raw evidence ignore rule active: {raw_ignore_ok}','','=== ROOT ROADMAP ===',
              f'Working docs/ROADMAP.md SHA-256: {roadmap_sha}',
              f'HEAD docs/ROADMAP.md blob SHA-256: {head_roadmap_sha or "<unavailable>"}',
              f'Pushed v2 baseline SHA-256: {ROADMAP_BASE_SHA}',
              f'HEAD docs/ROADMAP.md is pushed v2 baseline: {head_roadmap_is_baseline}',
              f'Working docs/ROADMAP.md has substantive Git diff: {roadmap_has_substantive_diff}',
              f'docs/ROADMAP.md diff numstat: {roadmap_numstat_text or "<clean>"}',
              'Final checkpoint should update Phase B -> COMPLETE and Phase C -> NEXT: True','',
              '=== COMPILE / BUILD ===',f'Python files compiled: {py_count}',f'Python compile passed: {py_ok}',
              f'Python compile error: {py_error or "<none>"}',f'Android Kotlin compile passed: {android_ok}',
              f'Android compile error: {android_error or "<none>"}','','=== CORE HASHES ===']
    for rel,digest in core_hashes.items(): lines.append(f'{rel}: {digest}')
    failed=[k for k,v in checks.items() if not v]
    lines += ['',f'Failed readiness checks: {failed}',
              'Next step: '+('B6_AUDIT_READY_PREPARE_EXACT_CHECKPOINT_PACKAGE' if classification==READY else 'REVIEW_B6_AUDIT_BEFORE_CHECKPOINT')]
    txt.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print(classification); print('Text:',txt); print('JSON:',js)
    return 0 if classification==READY else 1

if __name__=='__main__': raise SystemExit(main())
