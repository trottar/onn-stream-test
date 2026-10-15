#!/usr/bin/env python3
"""E4-S4B -- the four controls tabled (read-only over runs/E1-PS1-STREAM/run*): the gate's figures plus host CPU, the
companion's CPU, underruns, pauses, socket W and comparability to E4-S1 (reported). -> controls.json, validity.json,
e4_s4b_table.md (the gate-only verdict; e4_s4b_analysis.py's path for a gate with no clean control)."""
import json, glob, os
D = os.path.dirname(os.path.abspath(__file__))
rows, val = [], {}
for p in sorted(glob.glob(D + '/runs/E1-PS1-STREAM/run*/summary.json')):
    s = json.load(open(p)); h = s['host']['host']; hb = s['key']['heartbeat']; td = s['teardown']
    r = {'run': os.path.relpath(p, D), 'window': s['window'], 'host_cpu': h['cpu.mean_pct']['mean'],
         'companion_cpu': h.get('procs.companion.cpu_pct', {}).get('mean'), 'rendered': hb['rendered_fps'],
         'loss_per_min': hb['video_loss_per_min'], 'resyncs': hb['stream_resyncs'], 'underruns': hb['audio_underruns'],
         'retroarch': s['key']['retroarch'].get('frames_per_s'), 'socket_w': h.get('gpu.socket_power_w', {}).get('mean'),
         'client_pauses': len((s['key'].get('recovery') or {}).get('client_pauses') or []),
         'controller_pauses': len((s['key'].get('recovery') or {}).get('controller_pauses') or [])}
    r['comparable_to_E4S1'] = abs(r['host_cpu'] - 10.9) <= 2 and abs(r['rendered'] - 59.53) <= 0.5
    rows.append(r)
    val[r['run']] = {'status': s['status'], 'replaced_attempts': len(glob.glob(os.path.dirname(p) + '/summary_failed_attempt*')),
                     'flags_absent': td.get('flags_absent'), 'apk': td.get('apk'), 'ps1_files_identical': td.get('ps1_files_identical')}
json.dump(val, open(D + '/validity.json', 'w'), indent=1)
json.dump(rows, open(D + '/controls.json', 'w'), indent=1)
md = ['# E4-S4B — the four controls (the clean-link gate: loss/min < 10, rendered >= 59.5, resyncs <= 10)', '',
      '| control | window (UTC) | loss/min | rendered | resyncs | RetroArch | host CPU | companion % of a core | underruns | client / controller pauses | socket W | clean | within E1 bands of E4-S1 |',
      '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for i, r in enumerate(rows, 1):
    md.append(f"| {i} | {r['window']['from'][11:16]}-{r['window']['to'][11:16]} | {r['loss_per_min']} | {r['rendered']} | {r['resyncs']} | {r['retroarch']} | {round(r['host_cpu'], 2)} | {round(r['companion_cpu'], 1)} | {r['underruns']} | {r['client_pauses']} / {r['controller_pauses']} | {round(r['socket_w'], 1)} | {r['loss_per_min'] < 10 and r['rendered'] >= 59.5 and r['resyncs'] <= 10} | {r['comparable_to_E4S1']} |")
md += ['', '**Verdict: INCONCLUSIVE (link)** -- no clean control in four; no flagged run (pre-registration §1).']
open(D + '/e4_s4b_table.md', 'w').write('\n'.join(md) + '\n')
print('\n'.join(md))
