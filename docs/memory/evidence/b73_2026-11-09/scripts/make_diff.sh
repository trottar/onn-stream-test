#!/bin/bash
# usage: make_diff.sh <before root> <after root>  -> a git-apply-able unified diff (a/ b/ repo-relative) on stdout
# compares companion/ tools/ tests/ PrivyHub/ sources (build outputs, caches and local.properties excluded)
b="$1"; a="$2"
list() { (cd "$1" && find companion tools tests PrivyHub -type f \
  -not -path '*/build/*' -not -path '*/.gradle/*' -not -path '*/__pycache__/*' -not -name 'local.properties' \
  -not -name '*.orig' -not -path '*/.kotlin/*' | sort); }
{ list "$b"; list "$a"; } | sort -u | while read -r f; do
  if [ -f "$b/$f" ] && [ -f "$a/$f" ]; then
    cmp -s "$b/$f" "$a/$f" || { echo "diff --git a/$f b/$f"; diff -u --label "a/$f" --label "b/$f" "$b/$f" "$a/$f"; }
  elif [ -f "$a/$f" ]; then
    echo "diff --git a/$f b/$f"; echo "new file mode 100644"; diff -u --label /dev/null --label "b/$f" /dev/null "$a/$f"
  else
    echo "diff --git a/$f b/$f"; echo "deleted file mode 100644"; diff -u --label "a/$f" --label /dev/null "$b/$f" /dev/null
  fi
done
