#!/bin/bash
# Queue BC: B162 and B163 three runs each, B157 and B158 twice, then BB's recent party suites once — in the /tmp work
# copy, TMPDIR on the main disk, HEAD's code read by git; the board's repo not named (B111's Godot parts skip).
# usage: run_suites.sh <work copy> <repo> <out dir> <temp dir on the main disk>
W="$1"; O="$3"; export H7_GIT_REPO="$2" TMPDIR="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 2400 python3 -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O/tests_x3.txt"
for run in 1 2 3; do for t in b162_solo_safe b163_rehearse; do echo "run $run $t: $(one $t)" >> "$O/tests_x3.txt"; done; done
for run in 1 2; do for t in b157_add_game b158_winner_only; do echo "run $run $t: $(one $t)" >> "$O/tests_x3.txt"; done; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
: > "$O/tests_recent.txt"
for t in b114_party_minigame_hang b155_party_keys_written b153_party_switch_length b151_party_select_leaves \
         b148_party_board_prepared b147_party_band_inside b145_party_small_things b144_party_practice_banner \
         b143_party_audio_switch b141_party_select_held b140_party_begin_shown b139_party_clean_window \
         b137_party_no_press b134_party_practice b133_party_prepare_go b127_party_cheat_setups b124_party_four_seats \
         b123_h7_n64_start b131_party_save_load b108_party_launch b110_party_minigame b112_no_client_bench b115_party_handovers; do
  echo "$t: $(one $t)" >> "$O/tests_recent.txt"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_recent.txt"
