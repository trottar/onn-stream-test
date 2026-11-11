#!/bin/bash
# B92: JVM mutations, 3 runs, the full JVM suite (work copy), the APK twice + the baseline (queue AG's APK tree) once.
S=~/.cache/b_q21ag_tmp; export TMPDIR=$S/t; E=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence/b92_2026-11-11
M=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence/b91_2026-11-11/scripts/mutate_jvm.sh
W=/tmp/b_q21ag_work/PrivyHub; C=com.safeiot.privyhub.streaming.B92ChangedRowsTest; F=app/src/main/java/streaming/MappingPicture.kt
{ bash $M $W $F $C N1_no_changed_rows '        return (mapping.keys + default.keys).filter { norm(mapping[it]) != norm(default[it]) }.toSet()' '        return emptySet()'
  bash $M $W $F $C N2_no_trim_or_case '        fun norm(v: String?) = v?.trim()?.lowercase().orEmpty()' '        fun norm(v: String?) = v.orEmpty()'
  bash $M $W $F $C N3_only_the_mappings_keys '        return (mapping.keys + default.keys).filter' '        return (mapping.keys).filter'
  bash $M $W $F $C N4_another_colour '    const val CHANGED_COLOR = 0xFFFFC107.toInt()' '    const val CHANGED_COLOR = 0xFFFF5252.toInt()'
} > $E/tests_mutations_jvm.txt 2>&1
R=$W/app/build/test-results/testDebugUnitTest
{ echo "B92 / B91 / B89 / B86 JVM, 3 runs, /tmp/b_q21ag_work/PrivyHub (HEAD's client + B92), $(date -u +%FT%TZ)"
  for i in 1 2 3; do (cd $W && timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q --tests '*B92*' --tests '*B91*' --tests '*B89*' --tests '*B86*' >/dev/null 2>&1; echo "rc=$?")
    for c in B92ChangedRowsTest B91MappingBesideTest B89MappingPictureTest B86MappingPictureTest; do echo "run $i $c $(grep -o 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' $R/TEST-com.safeiot.privyhub.streaming.$c.xml)"; done; done; } > $E/tests_x3.txt 2>&1
(cd $W && timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q >/dev/null 2>&1; echo "full rc=$?") > $E/tests_jvm_work_full.txt
cat $R/*.xml | grep -o '<testsuite [^>]*' | grep -o 'tests="[0-9]*"\|failures="[0-9]*"\|errors="[0-9]*"' | awk -F'"' '{s[$1]+=$2} END {for (k in s) print k, s[k]}' >> $E/tests_jvm_work_full.txt
B=$S/apkbuild_ah; mkdir -p $B; A=/tmp/b_q21ah_apk/PrivyHub; O=/tmp/b_q21ah_apko/PrivyHub
(cd $A && timeout 1800 bash ./gradlew :app:testDebugUnitTest --offline --no-configuration-cache -q > $B/jvm_apk.log 2>&1; echo "rc=$?" >> $B/jvm_apk.log)
cat $A/app/build/test-results/testDebugUnitTest/*.xml | grep -o '<testsuite [^>]*' | grep -o 'tests="[0-9]*"\|failures="[0-9]*"\|errors="[0-9]*"' | awk -F'"' '{s[$1]+=$2} END {for (k in s) print k, s[k]}' >> $B/jvm_apk.log
for n in 1 2; do (cd $A && timeout 1800 bash ./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache -q > $B/apk$n.log 2>&1; echo "rc=$?" >> $B/apk$n.log); mkdir -p $B/apk$n && cp $A/app/build/outputs/apk/debug/app-debug.apk $B/apk$n/; done
(cd $O && timeout 1800 bash ./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache -q > $B/apko.log 2>&1; echo "rc=$?" >> $B/apko.log); mkdir -p $B/apko && cp $O/app/build/outputs/apk/debug/app-debug.apk $B/apko/
sha256sum $B/apk1/app-debug.apk $B/apk2/app-debug.apk $B/apko/app-debug.apk > $B/apk_sums.txt; echo ALLDONE >> $B/apk_sums.txt
