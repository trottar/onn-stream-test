#!/bin/bash
# C3-L4-N2: `--only F1` (night 3) with the FAKE sudo (never real sudo or nft): the harness's real command path,
# 60 s holds (--fast). N1's n1_fake_tests.sh with the subset changed; FULL only was run (the always-clear paths are
# unchanged since N1's FULL and ABORT). Checked by n2_check.py (L2B's l2b_check.py + the subset checks).
# Usage: n2_fake_tests.sh [FULL]
set -u
cd "$(dirname "$0")/../../../.." || exit 1
B=logs/streaming/c3_l4_n2_tests
HERE=docs/memory/evidence/c3_l4_n2_2026-09-29
FAKE=tools/c3_l4_fake_sudo.py
mkdir -p "$B"
run() {  # name, extra args...
  local name=$1; shift
  rm -rf "$B/$name" "$B/${name}_sudo"; mkdir -p "$B/${name}_sudo"
  printf '\n' | FAKE_SUDO_DIR="$B/${name}_sudo" python3 tools/c3_l4_nft_night.py --fast --sudo-cmd "$FAKE" \
      --only F1 --out "$B/$name" "$@" > "$B/${name}_console.txt" 2>&1
  local rc=$?
  echo "exit $rc" >> "$B/${name}_console.txt"
  echo "== $name: harness exit $rc"
  python3 "$HERE/n2_check.py" "$B/$name" "$B/${name}_sudo" "$rc"
}
[ $# -eq 0 ] && set -- FULL ABORT
for t in "$@"; do
  case $t in
  FULL)  run N2_full_only_F1 ;;
  ABORT) run N1_abort_exception_f3_drop --test-fail-at F3_drop ;;
  esac
done
