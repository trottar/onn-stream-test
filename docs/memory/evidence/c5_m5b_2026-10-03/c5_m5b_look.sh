#!/bin/bash
# C5-M5B section 5 -- the PS1 look's smoke and cost holds (pre-registered, c5_m5b_preregistration.txt).
# Every hold is c5_m5b_hold.sh (Tekken 3 attract, zero input, the adopted 7000 stream, live by default, the
# counter-only game override, T2 at 10 s, c5_m4_sampler at 1 s with the C2 telemetry), with
# PRIVYHUB_PS1_LOOK=<lever> set in the user manager for that hold only and unset by its teardown, which
# also checks the adopted PS1 files byte-identical. After each hold the RetroArch session log's look line and
# render target, and the companion's ps1_look_sessions.jsonl record (removed / rewritten keys), are kept.
#   c5_m5b_look.sh smoke                     -> look_smoke/  (measure-smoke-2x, 60 s: the render target must read 2048^2)
#   c5_m5b_look.sh table                     -> look/        (b_base4x, b_dither_off, b_filter_*, b_pgxp; 300 s each)
#   c5_m5b_look.sh full                      -> look/        (b_full: measure-full, 300 s)
#   c5_m5b_look.sh rung                      -> look_rung/   (c_full_rung: measure-full + TOP=1080p + INJECT=1;
#                                                             INCREASE_1080P after 90 s at PLAYING, then 300 s)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO=/home/privyhub/Projects/onn-stream-test
log() { echo "[look $(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$HERE/look.log"; }
keep() {  # dir name: the RetroArch session log's look line + render target, the look end record
  local D="$1" N="$2" GL
  GL=$(ls -t "$REPO"/logs/games/*-game_ps1_*.log 2>/dev/null | head -1)
  { echo "# $N: $(basename "$GL")"
    grep -h "PS1 look (C5-M5B)\|Initializing HW render\|Using windowed fullscreen\|Using resolution" "$GL"
    echo "# ps1_look_sessions.jsonl (last record)"
    tail -1 "$REPO/logs/games/ps1_look_sessions.jsonl" 2>/dev/null
  } > "$D/look_check_${N}.txt"
  log "$N: $(grep -c 'PS1 look (C5-M5B)' "$D/look_check_${N}.txt") look line(s); $(grep -o 'Initializing HW render ([0-9x]*)' "$D/look_check_${N}.txt" | head -1); end record: $(tail -1 "$D/look_check_${N}.txt" | python3 -c 'import sys,json
try:
    r=json.loads(sys.stdin.read()); print("preset", r.get("preset"), "removed", r.get("removed"), "rewritten", r.get("rewritten_keys"))
except Exception as e: print("none")')"
}
hold() {  # dir name secs flags [hook]
  local D="$HERE/$1" N="$2" S="$3" F="$4" H="${5:-}"
  mkdir -p "$D"
  log "$N begins: flags '$F', ${S}s"
  SESSION_FLAGS="$F" HOLD_HOOK="$H" COLD_MIN=1 "$HERE/c5_m5b_hold.sh" "$D" "$N" "$S" > "$D/hold_${N}.log" 2>&1
  log "$N exit $?; $(grep -o 'ADOPTED PS1 FILES [A-Z -]*' "$D/hold_${N}.log" | tail -1); $(grep -o 'FLAGS UNSET AND ABSENT\|FLAGS NOT CLEAN' "$D/hold_${N}.log" | tail -1)"
  keep "$D" "$N"
}
case "${1:?smoke|table|full|rung}" in
  smoke) hold look_smoke b_smoke2x 60 "PRIVYHUB_PS1_LOOK=measure-smoke-2x" ;;
  table)
    hold look b_base4x 300 ""
    hold look b_dither_off 300 "PRIVYHUB_PS1_LOOK=measure-dither-off"
    for f in xbr sabr bilinear 3point jinc2; do hold look "b_filter_$f" 300 "PRIVYHUB_PS1_LOOK=measure-filter-$f"; done
    hold look b_pgxp 300 "PRIVYHUB_PS1_LOOK=measure-pgxp" ;;
  full) hold look b_full 300 "PRIVYHUB_PS1_LOOK=measure-full" ;;
  rung) hold look_rung c_full_rung 0 "PRIVYHUB_PS1_LOOK=measure-full PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1" "$HERE/c5_m5b_rung_hook.sh" ;;
esac
log "$1 done"
