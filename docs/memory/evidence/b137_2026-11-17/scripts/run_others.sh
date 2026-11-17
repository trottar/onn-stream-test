#!/bin/bash
# B137: the earlier suites once, in the /tmp work copy (companion/, tools/, tests/, PrivyHub/), TMPDIR on the main
# disk, HEAD's code read from the repo by git (H7_GIT_REPO). One line per suite: its unittest summary.
# usage: run_others.sh <work copy> <repo> <out file>
W="$1"; REPO="$2"; OUT="$3"
export H7_GIT_REPO="$REPO"
cd "$W" || exit 1
: > "$OUT"
for t in b129_h7_game_window b130_h7_recognise_setup b131_party_save_load b127_party_cheat_setups b124_party_four_seats \
         b114_party_minigame_hang b115_party_handovers b110_party_minigame b112_no_client_bench b123_h7_n64_start \
         b122_h7_places b111_party_board b108_party_launch b105_h7_watcher b103_h7_minigame b102_h7_endscreen \
         b104_h7_tone b101_h7_contest b99_h7_live_read b65_n64_continue b61_n64_hold player_prompt players_session \
         relaunch_ports pad_slots pad_slots_changes stall_signal stall_owner link_recovery restart_fast client_contract \
         input_hold input_hold_rewind keyframe_request lan_loss_rule_bidir impairment audio_codec b72_small_readings \
         art_systems ps2_session gamecube_session n64_session; do
  r=$( (timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED" | tr '\n' ' ')
  echo "$t: $r" >> "$OUT"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$OUT"
