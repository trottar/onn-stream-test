#!/bin/bash
# B108: 3 runs of tests/b108_party_launch on a work copy of the snapshot (/tmp/b_q27ao: companion/ tools/ tests/
# PrivyHub/), then B90, the client contract, B103, B105, the PS2 and GameCube sessions' suites once; then the mutations.
# No Godot, no emulator: the stand-in board, B101's fake RetroArch. The flag-absent case compares with
# `git archive f302f8a8` (H7_GIT_REPO).
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b108_2026-11-16; S=/tmp/b_q27ao
export TMPDIR=~/.cache/b_q27ao_tmp/t H7_GIT_REPO=$R
W=$(mktemp -d -p ~/.cache/b_q27ao_tmp b108_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B108 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/b108_party_launch 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  for t in b90_cheat_staged client_contract b103_h7_minigame b105_h7_watcher ps2_session gamecube_session; do echo "tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "board stand-ins / RetroArch left: $(ps -eo args | grep -c '[b]oard_standin') / $(ps -eo args | grep -c '[R]etroArch-Linux')"
  echo "temp dirs left by the runs (b108_* / b99_head_* / b82_*): $(ls $TMPDIR | grep -c -E '^(b108_|b99_head_|b82_)')"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/b108_party_launch,tests/gamecube_session 'test_*.py' > $E/tests_mutations.txt 2>&1
echo "board stand-ins left after the mutations: $(ps -eo args | grep -c '[b]oard_standin'); temp dirs left (b_q27ao_mut_*): $(ls $TMPDIR | grep -c '^b_q27ao_mut_')" >> $E/tests_mutations.txt
