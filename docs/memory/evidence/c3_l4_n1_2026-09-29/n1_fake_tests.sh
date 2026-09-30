#!/bin/bash
# C3-L4-N1: `--only F1,F3` with the FAKE sudo (never real sudo or nft): the harness's real command path,
# 60 s holds (--fast). Derived from c3_l4_l2_2026-09-29/l2b/l2b_abort_tests.sh.
#   N1-FULL   --only F1,F3 end to end
#   N1-ABORT  --only F1,F3 with an exception raised during F3's drop (the test hook), after F1 ran whole
# Each is checked by n1_check.py (L2B's l2b_check.py + the subset checks).
# Usage: n1_fake_tests.sh [FULL ABORT]
set -u
cd "$(dirname "$0")/../../../.." || exit 1
B=logs/streaming/c3_l4_n1_tests
HERE=docs/memory/evidence/c3_l4_n1_2026-09-29
FAKE=tools/c3_l4_fake_sudo.py
mkdir -p "$B"
run() {  # name, extra args...
  local name=$1; shift
  rm -rf "$B/$name" "$B/${name}_sudo"; mkdir -p "$B/${name}_sudo"
  printf '\n' | FAKE_SUDO_DIR="$B/${name}_sudo" python3 tools/c3_l4_nft_night.py --fast --sudo-cmd "$FAKE" \
      --only F1,F3 --out "$B/$name" "$@" > "$B/${name}_console.txt" 2>&1
  local rc=$?
  echo "exit $rc" >> "$B/${name}_console.txt"
  echo "== $name: harness exit $rc"
  python3 "$HERE/n1_check.py" "$B/$name" "$B/${name}_sudo" "$rc"
}
[ $# -eq 0 ] && set -- FULL ABORT
for t in "$@"; do
  case $t in
  FULL)  run N1_full_only_F1_F3 ;;
  ABORT) run N1_abort_exception_f3_drop --test-fail-at F3_drop ;;
  esac
done
