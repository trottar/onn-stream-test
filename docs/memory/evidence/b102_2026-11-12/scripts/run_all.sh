#!/bin/bash
# B102: 3 runs of tests/b102_h7_endscreen on a work copy of the snapshot (/tmp/b_q25am: companion/ tools/ tests/
# PrivyHub/), then the mutations from the snapshot. No RetroArch, no game picture: synthetic pictures only.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b102_2026-11-12; S=/tmp/b_q25am
export TMPDIR=~/.cache/b_q25am_tmp/t H7_GIT_REPO=$R
W=$(mktemp -d -p ~/.cache/b_q25am_tmp b102_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B102 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/b102_h7_endscreen 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "temp dirs left by the runs (b102_*): $(ls $TMPDIR | grep -c '^b102_')"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/b102_h7_endscreen 'test_*.py' > $E/tests_mutations.txt 2>&1
