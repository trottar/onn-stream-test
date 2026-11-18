#!/bin/bash
# B139: every core x shape x variant once, one after another. usage: run_matrix.sh <repo> <scratch>
R="$1"; S="$2"
for core in n64 ps1; do for shape in full window; do for v in today font_off anim_off widgets_off notif_off all; do
  W="$S/osd_${core}_${shape}_${v}"; rm -rf "$W"; mkdir -p "$W"
  [ "$v" = all ] || [ "$v" = today ] && mkdir -p "$W/keep"
  timeout 120 python3 "$R/docs/memory/evidence/b139_2026-11-17/scripts/osd_probe.py" "$R" "$W" $core $shape $v > "$W/out.txt" 2>&1
  echo "$core $shape $v done"
done; done; done
