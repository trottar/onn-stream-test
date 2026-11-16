#!/bin/bash
# B114 / B115 / B116: 3 runs each of tests/b114_party_minigame_hang, tests/b115_party_handovers, tests/b110_party_minigame,
# tests/b112_no_client_bench and tests/b111_party_board (the board's check under Godot headless in a scratch copy of the
# board's repo) on a work copy of the snapshot (/tmp/b_q28aq: companion/ tools/ tests/ PrivyHub/); B108, B103, B105,
# the stall / recovery suites, the client contract, PS2, GameCube once. The flag-absent cases compare with
# `git archive 8fa398c8`; B114's HEAD run (B114_AGAINST) once more, to show it still hangs there.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence; S=/tmp/b_q28aq
mkdir -p ~/.cache/b_q28aq_tmp/x3; export TMPDIR=~/.cache/b_q28aq_tmp/x3 H7_GIT_REPO=$R
export PRIVYPARTY_GODOT=$HOME/tools/godot-4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64 PRIVYPARTY_REPO=$(cd $R/.. && pwd)/privyparty
W=$(mktemp -d -p ~/.cache/b_q28aq_tmp aq_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B114 / B115 / B116 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do for t in b114_party_minigame_hang b115_party_handovers b110_party_minigame b112_no_client_bench b111_party_board; do echo "run $i tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED|^FAIL:|^ERROR:' | tr '\n' ' ')"; done; done
  echo "temp dirs left by these five suites' 15 runs: $(ls $TMPDIR | wc -l)"
  for t in b108_party_launch b103_h7_minigame b105_h7_watcher stall_signal stall_owner stall_resume_speed session_end input_hold_b8 b61_n64_hold rewind_cores rewind_needs_loss link_recovery link_recovery_wan restart_fast restart_fast_unlock client_contract ps2_session gamecube_session; do echo "tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED|^FAIL:|^ERROR:' | tr '\n' ' ')"; done
  echo "B114's test against HEAD 8fa398c8's companion: $(B114_AGAINST=8fa398c8 python3 -B -m unittest tests/b114_party_minigame_hang/test_b114.py -k NoHang 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"
  echo "board stand-ins / Godot / RetroArch left: $(ps -eo args | grep -c '[b]oard_standin') / $(ps -eo args | grep -c '[G]odot_v4') / $(ps -eo args | grep -c '[R]etroArch-Linux')"
  echo "temp dirs left after the other suites (theirs: the stall-signal suites leave b7_*): $(ls $TMPDIR | wc -l) ($(ls $TMPDIR | sed 's/_[^_]*$//' | sort | uniq -c | tr '\n' ' '))"; } > $E/b115_2026-11-16/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE $(date -u +%FT%TZ)" >> $E/b115_2026-11-16/tests_x3.txt
