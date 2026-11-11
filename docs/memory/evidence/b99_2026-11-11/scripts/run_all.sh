#!/bin/bash
# B99: 3 runs of tests/b99_h7_live_read on a work copy of the B99 snapshot (/tmp/b_q23ak_b99: companion/ tools/ tests/
# PrivyHub/), then tests/client_contract and tests/b90_cheat_staged once (the same harness, the changed plugin), then
# the mutations from the snapshot. No RetroArch: the fake. H7_GIT_REPO: the repo, for the baseline's companion.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b99_2026-11-11; S=/tmp/b_q23ak_b99
export TMPDIR=~/.cache/b_q22ak_tmp/t H7_GIT_REPO=$R
W=$(mktemp -d -p ~/.cache/b_q22ak_tmp b99_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B99 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the B99 snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/b99_h7_live_read 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "tests/client_contract: $(python3 -B -m unittest discover -s tests/client_contract 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"
  echo "tests/b90_cheat_staged: $(python3 -B -m unittest discover -s tests/b90_cheat_staged 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"
  echo "RetroArch left: $(ps -eo args | grep -c '[R]etroArch-Linux') (B98's batch may run beside this one)"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/b99_h7_live_read 'test_*.py' > $E/tests_mutations.txt 2>&1
echo "RetroArch left after the mutations: $(ps -eo args | grep -c '[R]etroArch-Linux') (B98's batch may run beside this one)" >> $E/tests_mutations.txt
