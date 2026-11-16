#!/bin/bash
# B110 / B111 / B112: 3 runs each of tests/b110_party_minigame, tests/b112_no_client_bench and tests/b111_party_board
# (the board's check under Godot headless in a scratch copy of the board's repo) on a work copy of the snapshot
# (/tmp/b_q28ap: companion/ tools/ tests/ PrivyHub/); B108, B103, B105, B90, the client contract, PS2, GameCube once;
# then B110's and B112's mutations from the snapshot. The flag-absent cases compare with `git archive 0a3d78e2`.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence; S=/tmp/b_q28ap
export TMPDIR=~/.cache/b_q28ap_tmp/t H7_GIT_REPO=$R
export PRIVYPARTY_GODOT=$HOME/tools/godot-4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64 PRIVYPARTY_REPO=$(cd $R/.. && pwd)/privyparty
W=$(mktemp -d -p ~/.cache/b_q28ap_tmp ap_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B110 / B111 / B112 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do for t in b110_party_minigame b112_no_client_bench b111_party_board; do echo "run $i tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done; done
  for t in b108_party_launch b103_h7_minigame b105_h7_watcher b90_cheat_staged client_contract ps2_session gamecube_session; do echo "tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "board stand-ins / Godot / RetroArch left: $(ps -eo args | grep -c '[b]oard_standin') / $(ps -eo args | grep -c '[G]odot_v4') / $(ps -eo args | grep -c '[R]etroArch-Linux')"
  echo "temp dirs left by the runs: $(ls $TMPDIR | wc -l)"; } > $E/b110_2026-11-16/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/b110_2026-11-16/tests_x3.txt
for d in b110 b112; do
  suite=tests/b110_party_minigame; [ $d = b112 ] && suite=tests/b112_no_client_bench,tests/b110_party_minigame
  python3 -u -B $E/${d}_2026-11-16/scripts/mutate.py $S $R $E/${d}_2026-11-16/scripts/mutations.json $suite 'test_*.py' > $E/${d}_2026-11-16/tests_mutations.txt 2>&1
  echo "stand-ins left: $(ps -eo args | grep -c '[b]oard_standin'); temp dirs left (b_q28ap_mut_*): $(ls $TMPDIR | grep -c '^b_q28ap_mut_')" >> $E/${d}_2026-11-16/tests_mutations.txt
done
