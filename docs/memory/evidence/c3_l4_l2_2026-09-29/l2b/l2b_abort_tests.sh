#!/bin/bash
# C3-L4-L2B: the forced-abort tests of tools/c3_l4_nft_night.py with the FAKE sudo (never real sudo or nft).
#   A1 Ctrl-C (SIGINT) during F1's cap     A2 SIGHUP during F2's loss     A3 an exception during F3's drop
#   A4 the keepalive refused during F2 (the password asked again; the fault removed and re-applied; run continues)
#   A5 a verification mismatch at F2's apply (the listing shows no rule: the night stops cleanly)
# Usage: l2b_abort_tests.sh [A1 A2 A3 A4 A5]
set -u
cd "$(dirname "$0")/../../../../.." || exit 1
B=logs/streaming/c3_l4_l2b_tests
CHECK=docs/memory/evidence/c3_l4_l2_2026-09-29/l2b/l2b_check.py
FAKE=tools/c3_l4_fake_sudo.py
mkdir -p "$B"

wait_event() {  # run dir, grep pattern, timeout s
  local end=$(( $(date +%s) + $3 ))
  until grep -q "$2" "$1/events.jsonl" 2>/dev/null; do
    [ "$(date +%s)" -ge "$end" ] && return 1
    sleep 1
  done
}

run() {  # name, sessions, extra args...
  local name=$1 sessions=$2; shift 2
  rm -rf "$B/$name" "$B/${name}_sudo"; mkdir -p "$B/${name}_sudo"
  printf '\n' | FAKE_SUDO_DIR="$B/${name}_sudo" python3 tools/c3_l4_nft_night.py --fast --sudo-cmd "$FAKE" \
      --sessions "$sessions" --out "$B/$name" "$@" > "$B/${name}_console.txt" 2>&1 &
  PID=$!
}

finish() {  # name
  wait "$PID"; local rc=$?
  echo "exit $rc" >> "$B/${1}_console.txt"
  echo "== $1: harness exit $rc"
  python3 "$CHECK" "$B/$1" "$B/${1}_sudo"
}

[ $# -eq 0 ] && set -- A1 A2 A3 A4 A5
for t in "$@"; do
  case $t in
  A1) run A1_sigint_f1_cap F1
      wait_event "$B/A1_sigint_f1_cap" '"fault_on".*F1 cap' 400 && sleep 10
      echo "A1: SIGINT to $PID at $(date -u +%H:%M:%SZ)"; kill -INT "$PID"; finish A1_sigint_f1_cap ;;
  A2) run A2_sighup_f2 F2
      wait_event "$B/A2_sighup_f2" '"fault_on".*F2 2% loss' 400 && sleep 10
      echo "A2: SIGHUP to $PID at $(date -u +%H:%M:%SZ)"; kill -HUP "$PID"; finish A2_sighup_f2 ;;
  A3) run A3_exception_f3_drop F3 --test-fail-at F3_drop
      finish A3_exception_f3_drop ;;
  A4) run A4_keepalive_refused_f2 F2 --keepalive-s 20
      wait_event "$B/A4_keepalive_refused_f2" '"fault_on".*F2 2% loss' 400 && sleep 2
      echo "A4: deny (sudo -n refused) from $(date -u +%H:%M:%SZ)"; touch "$B/A4_keepalive_refused_f2_sudo/deny"
      finish A4_keepalive_refused_f2 ;;
  A5) run A5_mismatch_f2 F2
      touch "$B/A5_mismatch_f2_sudo/mangle"
      finish A5_mismatch_f2 ;;
  esac
done
