#!/bin/bash
# usage: mutate_jvm.sh <PrivyHub dir> <file rel> <test class> <name> <python expr old> <new>  -- one mutation, restored after
ph="$1"; rel="$2"; cls="$3"; name="$4"; old="$5"; new="$6"
cd "$ph" || exit 2
cp "$rel" "$rel.orig"
python3 -c "import sys;p=sys.argv[1];s=open(p).read();o=sys.argv[2];n=sys.argv[3];assert s.count(o)==1,('not once',o);open(p,'w').write(s.replace(o,n))" "$rel" "$old" "$new" || { mv "$rel.orig" "$rel"; echo "$name: NOT APPLIED"; exit 3; }
TMPDIR=~/.cache/b_q19ac_tmp timeout 1200 bash ./gradlew :app:testDebugUnitTest --offline --no-configuration-cache --tests "$cls" -q >/dev/null 2>&1
rc=$?
x=app/build/test-results/testDebugUnitTest/TEST-$cls.xml
res=$(grep -o 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' "$x" 2>/dev/null)
mv "$rel.orig" "$rel"
if [ $rc -ne 0 ]; then echo "$name: CAUGHT (gradle rc $rc; $res)"; else echo "$name: NOT CAUGHT ($res)"; fi
