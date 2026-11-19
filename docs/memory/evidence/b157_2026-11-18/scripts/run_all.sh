#!/bin/bash
# Queue BB: B157 and B158 three times each, then the recent party suites once and the earlier ones once (B137's
# run_others.sh list) — in the /tmp work copy, TMPDIR on the main disk, HEAD's code read by git; the board's repo not
# named (B111's Godot parts skip). usage: run_all.sh <work copy> <repo> <out dir>
W="$1"; REPO="$2"; O="$3"
export H7_GIT_REPO="$REPO"
cd "$W" || exit 1
: > "$O/tests_x3.txt"
for run in 1 2 3; do for t in b157_add_game b158_winner_only; do
  r=$( (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' ')
  echo "run $run $t: $r" >> "$O/tests_x3.txt"
done; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
: > "$O/tests_recent.txt"
for t in b155_party_keys_written b153_party_switch_length b151_party_select_leaves b148_party_board_prepared \
         b147_party_band_inside b145_party_small_things b144_party_practice_banner b143_party_audio_switch \
         b141_party_select_held b140_party_begin_shown b139_party_clean_window b137_party_no_press \
         b134_party_practice b133_party_prepare_go start_rung encoder_rc; do
  r=$( (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' ')
  echo "$t: $r" >> "$O/tests_recent.txt"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_recent.txt"
env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO bash "$REPO/docs/memory/evidence/b137_2026-11-17/scripts/run_others.sh" "$W" "$REPO" "$O/tests_others.txt"
