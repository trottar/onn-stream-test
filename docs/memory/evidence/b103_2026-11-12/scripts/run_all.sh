#!/bin/bash
# B103: 3 runs of tests/b103_h7_minigame on a work copy of the snapshot (/tmp/b_q25am: companion/ tools/ tests/
# PrivyHub/ — PrivyHub/ for the contract's scan), then tests/b99_h7_live_read, tests/b101_h7_contest,
# tests/b102_h7_endscreen, tests/client_contract and tests/b90_cheat_staged once; then the mutations from the snapshot.
# No RetroArch: B101's fake. The flag-absent case compares with `git archive 8b43a266` (H7_GIT_REPO).
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b103_2026-11-12; S=/tmp/b_q25am
export TMPDIR=~/.cache/b_q25am_tmp/t H7_GIT_REPO=$R
W=$(mktemp -d -p ~/.cache/b_q25am_tmp b103_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B103 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/b103_h7_minigame 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  for t in b99_h7_live_read b101_h7_contest b102_h7_endscreen client_contract b90_cheat_staged; do echo "tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "RetroArch left: $(ps -eo args | grep -c '[R]etroArch-Linux') (the B103 settle's second run may be running beside this batch)"
  echo "temp dirs left by the runs (b103_* / b99_head_*): $(ls $TMPDIR | grep -c -E '^(b103_|b99_head_)')"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/b103_h7_minigame 'test_*.py' > $E/tests_mutations.txt 2>&1
echo "RetroArch left after the mutations: $(ps -eo args | grep -c '[R]etroArch-Linux')" >> $E/tests_mutations.txt
