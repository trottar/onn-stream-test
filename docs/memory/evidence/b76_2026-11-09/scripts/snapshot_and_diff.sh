#!/bin/bash
# usage: snapshot_and_diff.sh <item> <previous snapshot> <out diff>
# copies companion/ tools/ tests/ PrivyHub/ (no build outputs, caches or local.properties) to /tmp/b_q19ac_after_<item>,
# then writes the unified diff previous -> this snapshot (paths a/ b/ relative to the repo root)
set -e
item="$1"; prev="$2"; out="$3"
snap=/tmp/b_q19ac_after_$item
rm -rf "$snap"; mkdir -p "$snap"
cd "$(git rev-parse --show-toplevel)"
tar -c --exclude=__pycache__ --exclude=build --exclude=.gradle --exclude=local.properties --exclude=.pytest_cache \
  companion tools tests PrivyHub | tar -x -C "$snap"
cd /tmp
( cd "$prev" && find . -type f | sort ) > /tmp/b_q19ac_prev_files.txt
rm -f "$out.tmp"
git diff --no-index --no-color "$(basename "$prev")" "$(basename "$snap")" > "$out.tmp" || true
sed -e "s#a/$(basename "$prev")/#a/#g; s#a/$(basename "$snap")/#a/#g; s#b/$(basename "$prev")/#b/#g; s#b/$(basename "$snap")/#b/#g" "$out.tmp" > "$out"; rm -f "$out.tmp" /tmp/b_q19ac_prev_files.txt
echo "snapshot $snap; diff $(wc -l < "$out") lines"
