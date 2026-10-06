#!/usr/bin/env bash
# E3: h2_prep_redact.py --check over every text file under the given paths (stdin per file); prints OK/HIT per file
R=docs/memory/evidence/h2_prep_2026-09-22/h2_prep_redact.py
echo "E3 redactor check (h2_prep_redact.py --check, stdin per file), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for p in "$@"; do
  find "$p" -type f \( -name '*.md' -o -name '*.txt' -o -name '*.json' -o -name '*.jsonl' -o -name '*.py' -o -name '*.sh' -o -name '*.log' -o -name '*.sha256' -o -name '*.diff' -o -name '*.conf' \) -print0 | sort -z |
  while IFS= read -r -d '' f; do
    if python3 "$R" --check < "$f" > /dev/null 2>&1; then echo "OK   $f"; else echo "HIT  $f"; fi
  done
done
