#!/bin/bash
# usage: run_host.sh <copy root> <out file>
root="$1"; out="$2"
cd "$root" || exit 2
{
echo "host suites from $root, $(date -u +%Y-%m-%dT%H:%M:%SZ); units active: $(systemctl --user list-units 'privyhub-*' --state=active --no-legend --plain | awk '{printf "%s ", $1}'); PRIVYHUB_* in this process: $(env | grep -c '^PRIVYHUB_')"
for d in tests/*/; do
  d=${d%/}; [ "$(basename $d)" = "__pycache__" ] && continue
  ls $d/test_*.py >/dev/null 2>&1 || continue
  echo "== $d"
  timeout 900 python3 -B -m unittest discover -s "$d" 2>&1 | grep -E "^Ran |^OK|^FAILED" | tail -2
done
for f in tools/test_*.py; do
  echo "== $f"
  timeout 900 python3 -B -m unittest discover -s tools -p "$(basename $f)" 2>&1 | grep -E "^Ran |^OK|^FAILED" | tail -2
done
} > "$out" 2>&1
