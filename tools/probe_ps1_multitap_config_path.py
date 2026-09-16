#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys
from pathlib import Path

ROOT_BOOTSTRAP=Path(__file__).resolve().parents[1]
if str(ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0,str(ROOT_BOOTSTRAP))
from companion.games.emulator_manager import EmulatorManager


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='/home/privyhub/Projects/onn-stream-test')
    a=ap.parse_args()
    root=Path(a.root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0,str(root))

    manager=EmulatorManager(root)
    runtime=manager._runtime_details()
    linux_config=manager._retroarch_config_directory(runtime)

    raw_xdg=str(os.environ.get('XDG_CONFIG_HOME','')).strip()
    if raw_xdg:
        expected_home=Path(os.path.expanduser(raw_xdg))
        if not expected_home.is_absolute():
            raise RuntimeError('XDG_CONFIG_HOME is relative')
        expected_home=expected_home.resolve()
    else:
        expected_home=(Path.home()/'.config').resolve()
    expected_linux=(expected_home/'retroarch'/'config').resolve()

    seed=linux_config/manager.PS1_MULTITAP_CORE_LIBRARY/(manager.PS1_MULTITAP_CORE_LIBRARY+'.opt')
    linux_example=(linux_config/manager.PS1_MULTITAP_CORE_LIBRARY/'Example Game.opt').resolve()
    linux_metadata=manager._retroarch_options_metadata_path(
        linux_example,linux_config,'linux'
    )

    fake_exe=(root/'runtime/emulators/_d087_windows_path_probe/retroarch.exe').resolve()
    windows_runtime={'runtime_platform':'windows','executable':fake_exe}
    windows_config=manager._retroarch_config_directory(windows_runtime)
    windows_example=(windows_config/manager.PS1_MULTITAP_CORE_LIBRARY/'Example Game.opt').resolve()
    windows_metadata=manager._retroarch_options_metadata_path(
        windows_example,windows_config,'windows'
    )
    windows_expected=str(windows_example.relative_to(root)).replace('\\','/')

    checks={
        'runtime_platform_linux': runtime.get('runtime_platform')=='linux',
        'resolved_matches_xdg_default': linux_config==expected_linux,
        'seed_exists': seed.is_file(),
        'linux_metadata_config_relative': linux_metadata=='retroarch-config/Beetle PSX HW/Example Game.opt',
        'windows_portable_config_preserved': windows_config==(fake_exe.parent/'config').resolve(),
        'windows_metadata_project_relative_preserved': windows_metadata==windows_expected,
    }
    if seed.is_file():
        text=seed.read_text(encoding='utf-8-sig',errors='replace')
        checks['port1_key_present']=manager.PS1_MULTITAP_OPTION_KEYS['port1'] in text
        checks['port2_key_present']=manager.PS1_MULTITAP_OPTION_KEYS['port2'] in text
    else:
        checks['port1_key_present']=False
        checks['port2_key_present']=False

    passed=all(checks.values())
    out=root/'logs/games/ps1_multitap_config_path_probe.txt'
    out.parent.mkdir(parents=True,exist_ok=True)
    lines=[
        'PrivyHub D-087R1 PS1 multitap Config/metadata path probe',
        'Production files modified by probe: NONE',
        'Network addresses collected/logged: NONE',
        f'Linux Config directory: {linux_config}',
        f'Linux metadata example: {linux_metadata}',
        f'Windows metadata example: {windows_metadata}',
        '',
    ]+[f'{k}={v}' for k,v in checks.items()]+['','Result: '+('PASS' if passed else 'FAIL')]
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Result:','PASS' if passed else 'FAIL')
    print('Log:',out)
    return 0 if passed else 1

if __name__=='__main__':
    raise SystemExit(main())
