#!/bin/bash
# Queue BG: B178's suite three runs on the final code (after the label stage's culprit rule, addendum 3), in a second
# /tmp work copy, TMPDIR on the main disk. usage: run_b178_x3.sh <work copy> <out file> <temp dir> <repo>
W="$1"; O="$2"; export TMPDIR="$3"; export H7_GIT_REPO="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O"
for run in 1 2 3; do echo "run $run b178_score_kind (final code): $(one b178_score_kind)" >> "$O"; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
