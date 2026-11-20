#!/bin/bash
# Queue BG: the add-a-game suites again on the final code (the first copy lacked the learner's docstring paragraph and
# the label stage's culprit rule, both on the score path only). usage: run_final_addgame.sh <work copy> <out> <temp> <repo>
W="$1"; O="$2"; export TMPDIR="$3"; export H7_GIT_REPO="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O"
for t in b157_add_game b163_rehearse b175_left_out b171_more_saves; do echo "run 1 $t (final code): $(one $t)" >> "$O"; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
