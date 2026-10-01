#!/bin/bash
# C3-L4-D1: the nft harness with the FAKE sudo (never real sudo or nft), on the default-live companion:
#   D1-FULL   every session (F1 F2 F3 K) end to end, 60 s holds (--fast)
#   D1-ABORT  --only F1 with an exception raised at F1's cap (the test hook)
# Each checked by d1_check.py (L2B's fault checks + the new end state: live by default, restored).
# Derived from c3_l4_n1_2026-09-29/n1_fake_tests.sh. Usage: d1_fake_tests.sh [FULL ABORT]
set -u
cd "$(dirname "$0")/../../../.." || exit 1
B=logs/streaming/c3_l4_d1_tests
HERE=docs/memory/evidence/c3_l4_d1_2026-10-01
FAKE=tools/c3_l4_fake_sudo.py
mkdir -p "$B"
run() {  # name, extra args...
  local name=$1; shift
  rm -rf "$B/$name" "$B/${name}_sudo"; mkdir -p "$B/${name}_sudo"
  printf '\n' | FAKE_SUDO_DIR="$B/${name}_sudo" python3 tools/c3_l4_nft_night.py --fast --sudo-cmd "$FAKE" \
      --out "$B/$name" "$@" > "$B/${name}_console.txt" 2>&1
  local rc=$?
  echo "exit $rc" >> "$B/${name}_console.txt"
  echo "== $name: harness exit $rc"
  python3 "$HERE/d1_check.py" "$B/$name" "$B/${name}_sudo" "$rc"
}
[ $# -eq 0 ] && set -- FULL ABORT
for t in "$@"; do
  case $t in
  FULL)  run D1_full_all_sessions --only F1,F2,F3,K ;;
  ABORT) run D1_abort_exception_f1_cap --only F1 --test-fail-at F1_cap_on ;;
  esac
done
