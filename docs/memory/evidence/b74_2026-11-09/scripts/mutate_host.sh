#!/bin/bash
# usage: mutate_host.sh <copy root> <file rel> <name> <old> <new> -- one mutation, tests/b74_disc_safe run, file restored
root="$1"; rel="$2"; name="$3"; old="$4"; new="$5"
cd "$root" || exit 2
cp "$rel" "$rel.orig"
python3 -c "import sys;p=sys.argv[1];s=open(p).read();o=sys.argv[2];n=sys.argv[3];assert s.count(o)==1,('not once',o);open(p,'w').write(s.replace(o,n))" "$rel" "$old" "$new" || { mv "$rel.orig" "$rel"; echo "$name: NOT APPLIED"; exit 3; }
out=$(TMPDIR=~/.cache/b_q19aa_tmp timeout 600 python3 -B -m unittest discover -s tests/b74_disc_safe 2>&1 | grep -E "^Ran |^OK|^FAILED" | tr '\n' ' ')
mv "$rel.orig" "$rel"
case "$out" in *FAILED*) echo "$name: CAUGHT ($out)";; *) echo "$name: NOT CAUGHT ($out)";; esac
