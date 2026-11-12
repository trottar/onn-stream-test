#!/bin/bash
# B101: 3 runs of tests/b101_h7_contest on a work copy of the B101 snapshot (/tmp/b_q24al_b101: companion/ tools/
# tests/ PrivyHub/ — PrivyHub/ copied into the work copy too, for the contract's scan), then tests/b99_h7_live_read,
# tests/client_contract and tests/b90_cheat_staged once; then the mutations from the snapshot. No RetroArch: the fake.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b101_2026-11-12; S=/tmp/b_q24al_b101
export TMPDIR=~/.cache/b_q23al_tmp/t H7_GIT_REPO=$R
W=$(mktemp -d -p ~/.cache/b_q23al_tmp b101_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B101 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the B101 snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/b101_h7_contest 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  for t in b99_h7_live_read client_contract b90_cheat_staged; do echo "tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "RetroArch left: $(ps -eo args | grep -c '[R]etroArch-Linux') (B100's batch may run beside this one)"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/b101_h7_contest 'test_*.py' > $E/tests_mutations.txt 2>&1
echo "RetroArch left after the mutations: $(ps -eo args | grep -c '[R]etroArch-Linux') (B100's batch may run beside this one)" >> $E/tests_mutations.txt
