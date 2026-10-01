#!/bin/bash
# C5-M4 section 3 -- the offline captures, one at a time, no stream. Candidate scale 4x (the highest
# that HOLDS 60 in (b); 8x missed R1). Work dir runtime/c5_m4 (outside git).
#   G (the 3D demo segment, 125 s after the unpause, 60 s): ref1080_G (4x), ref1080_G_rep (4x, the
#     alignment control), refT_G (1x, today's 879x720 window, through the companion's scale/pad).
#   F (the intro FMV, C5-M3's segment): ref1080_F (4x, from the unpause, 75 s); T_F = C5-M3's reference.
# Trap: the measurement source files cleared, the game stopped.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; W=/home/privyhub/Projects/onn-stream-test/runtime/c5_m4
export DISPLAY=:0
trap '"$HERE/c5_m4_source.sh" clear; curl -s -X POST localhost:8765/plugins/games/stop >/dev/null; echo "[offline] trap: source cleared, game stopped"' EXIT
cap() { echo "[offline $(date -u +%H:%M:%SZ)] $*"; python3 "$HERE/c5_m4_offline.py" capture "$W" "$@"; sleep 15; }
"$HERE/c5_m4_source.sh" set 4x && cap ref1080_G 1080 125 60
"$HERE/c5_m4_source.sh" set 4x && cap ref1080_G_rep 1080 125 60
"$HERE/c5_m4_source.sh" window720 1x && cap refT_G 720 125 60
"$HERE/c5_m4_source.sh" set 4x && cap ref1080_F 1080 0 75
echo "[offline $(date -u +%H:%M:%SZ)] captures done"
