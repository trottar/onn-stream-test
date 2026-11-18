#!/bin/bash
# Queue AY: B147 / B148 (and B144's updated suite) three times — without Godot named, so B148's one real-board run
# (done once, disclosed, its own record) is skipped here — then the recent suites and the earlier ones once (B137's
# run_others.sh list; B111 with Godot and the board's repo named), in the /tmp work copy, TMPDIR on the main disk, HEAD's
# code by git. usage: run_all.sh <work copy> <repo> <out dir> <board repo>
W="$1"; REPO="$2"; O="$3"; BOARD="$4"
export H7_GIT_REPO="$REPO"
G=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/privyhub/party.json')))['godot'])")
cd "$W" || exit 1
: > "$O/tests_x3.txt"
for run in 1 2 3; do for t in b147_party_band_inside b148_party_board_prepared b144_party_practice_banner; do
  r=$( (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED" | tr '\n' ' ')
  echo "run $run $t: $r" >> "$O/tests_x3.txt"
done; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
export PRIVYPARTY_REPO="$BOARD" PRIVYPARTY_GODOT="$G"
: > "$O/tests_recent.txt"
for t in b143_party_audio_switch b145_party_small_things b141_party_select_held b140_party_begin_shown \
         b139_party_clean_window b137_party_no_press b133_party_prepare_go b134_party_practice start_rung encoder_rc; do
  r=$( (env -u PRIVYPARTY_GODOT timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED" | tr '\n' ' ')
  echo "$t: $r" >> "$O/tests_recent.txt"
done
bash "$REPO/docs/memory/evidence/b137_2026-11-17/scripts/run_others.sh" "$W" "$REPO" "$O/tests_others.txt"
