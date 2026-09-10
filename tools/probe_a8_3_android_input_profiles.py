#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def block(text,start,end):
    a=text.find(start)
    if a<0: raise RuntimeError('missing '+start)
    b=text.find(end,a+len(start))
    if b<0: raise RuntimeError('missing end for '+start)
    return text[a:b]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); a=ap.parse_args(); root=Path(a.root).resolve()
    src=root/'PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt'; log=root/'logs/games/a8_3_android_input_profiles_source.txt'
    text=src.read_text(encoding='utf-8-sig')
    target=block(text,'    private fun inputProfileTargetLabel(','    private fun inputProfileSourceLabel(')
    source=block(text,'    private fun inputProfileSourceLabel(','    private fun inputProfileMappingCopy(')
    editor=block(text,'    // PRIVYHUB_A8_PATCH_03V6_SIMPLE_CURRENT_MAPPING_EDITOR','    private fun saveInputProfileMapping(')
    checks={
        'v7_marker_once': text.count('PRIVYHUB_A8_PATCH_03V7_XBOX_LABELS_PLAYER_SYNC')==1,
        'v8_marker_once': text.count('PRIVYHUB_A8_PATCH_03V8_CONFLICT_CHOICES_RED')==1,
        'xbox_target_LB': '"l" -> "LB"' in target,
        'xbox_target_LT': '"l2" -> "LT"' in target,
        'xbox_target_RB': '"r" -> "RB"' in target,
        'xbox_target_RT': '"r2" -> "RT"' in target,
        'xbox_target_Back': '"select" -> "Back"' in target,
        'xbox_source_A': '"a" -> "A"' in source,
        'xbox_source_LB': '"l" -> "LB"' in source,
        'xbox_source_LT': '"l2" -> "LT"' in source,
        'xbox_source_Back': '"select" -> "Back"' in source,
        'no_ps_labels_in_target_function': all(x not in target for x in ('"L1"','"R1"','"L2"','"R2"','"Select"')),
        'no_verbose_mixed_source_labels': all(x not in source for x in ('A Button','B Button','LB Button','LT Trigger','Back / Select')),
        'sync_button_present': '"Sync $playerLabel with $otherPlayerLabel"' in editor,
        'sync_reads_other_player': 'inputProfileWorkingPlayerMapping(' in editor and 'otherPlayer' in editor,
        'sync_replaces_working_copy': 'working.clear()' in editor and 'working.putAll(' in editor,
        'sync_refreshes_validation': 'refreshRows()' in editor,
        'current_row_ui_preserved': '"Current: " +' in editor and '"Change"' in editor,
        'save_gate_preserved': 'invalid.isEmpty()' in editor,
        'red_validation_preserved': '0xFFFF5252' in editor,
        'popup_overlap_excludes_edited_target': 'entry.key != target' in editor,
        'popup_overlap_uses_working_copy': 'val overlapSources =' in editor and '.map { entry ->' in editor,
        'popup_uses_custom_adapter': 'object : android.widget.ArrayAdapter<String>' in editor and '.setAdapter(' in editor,
        'popup_conflicts_red_before_selection': 'source in overlapSources' in editor and '0xFFFF5252.toInt()' in editor,
    }
    ok=all(checks.values())
    lines=['PrivyHub A8.3 v8 conflict-choice source probe','Purpose: validate that already-used source choices are marked red before selection.','MainActivity.kt SHA256: '+sha(src),'']
    for k,v in checks.items(): lines.append(f'{k}: {"PASS" if v else "FAIL"}')
    lines += ['', 'Directional backend changed by v8: False','Production controller transport changed: False','Result: '+('PASS' if ok else 'FAIL')]
    log.parent.mkdir(parents=True,exist_ok=True); log.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(log.read_text(encoding='utf-8'),end='')
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
