#!/bin/bash
# G6-SCREEN1b: every companion suite under tests/ (each directory by unittest discover), TMPDIR on the main disk.
# usage (repo root): bash docs/memory/evidence/g6_screen1b_2026-11-20/run_companion_suites.sh <out file> <temp dir>
O="$1"; export TMPDIR="$2"; mkdir -p "$TMPDIR"
echo "companion suites $(date -u +%FT%TZ)" > "$O"
for d in tests/*/; do
  d=${d%/}; n=$(basename "$d")
  ls "$d"/test_*.py >/dev/null 2>&1 || continue
  r=$( (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 2400 python3 -W ignore -m unittest discover -s "$d" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' ')
  echo "$n: $r" >> "$O"
done
echo "done $(date -u +%FT%TZ); temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
