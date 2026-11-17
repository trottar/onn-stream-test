#!/bin/bash
# B122 / B123 / B124: 3 runs each of tests/b122_h7_places, b123_h7_n64_start, b124_party_four_seats, b114_party_minigame_hang,
# b115_party_handovers, b110_party_minigame, b112_no_client_bench and b111_party_board (the board's check under Godot
# headless in a scratch copy of the board's repo) on a work copy of the snapshot (/tmp/b_q29ar: companion/ tools/ tests/
# PrivyHub/); the neighbouring suites once. The flag-absent cases compare with `git archive cb16e0c8`.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence; S=/tmp/b_q29ar
mkdir -p ~/.cache/b_q29ar_tmp/x3; export TMPDIR=~/.cache/b_q29ar_tmp/x3 H7_GIT_REPO=$R
export PRIVYPARTY_GODOT=$HOME/tools/godot-4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64 PRIVYPARTY_REPO=$(cd $R/.. && pwd)/privyparty
W=$(mktemp -d -p ~/.cache/b_q29ar_tmp ar_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B122 / B123 / B124 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do for t in b122_h7_places b123_h7_n64_start b124_party_four_seats b114_party_minigame_hang b115_party_handovers b110_party_minigame b112_no_client_bench b111_party_board; do echo "run $i tests/$t: $(nice python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED|^FAIL:|^ERROR:' | tr '\n' ' ')"; done; done
  echo "temp dirs left by these suites' 24 runs: $(ls $TMPDIR | wc -l)"
  for t in b102_h7_endscreen b104_h7_tone b103_h7_minigame b105_h7_watcher b101_h7_contest b99_h7_live_read b108_party_launch b65_n64_continue b61_n64_hold player_prompt players_session relaunch_ports pad_slots stall_signal stall_owner link_recovery restart_fast client_contract ps2_session gamecube_session n64_session; do [ -d tests/$t ] && echo "tests/$t: $(nice python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED|^FAIL:|^ERROR:' | tr '\n' ' ')"; done
  echo "board stand-ins / Godot / RetroArch left: $(ps -eo args | grep -c '[b]oard_standin') / $(ps -eo args | grep -c '[G]odot_v4') / $(ps -eo args | grep -c '[R]etroArch-Linux')"
  echo "temp dirs left after the other suites: $(ls $TMPDIR | wc -l) ($(ls $TMPDIR | sed 's/_[^_]*$//' | sort | uniq -c | tr '\n' ' '))"; } > $E/b124_2026-11-17/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE $(date -u +%FT%TZ)" >> $E/b124_2026-11-17/tests_x3.txt
