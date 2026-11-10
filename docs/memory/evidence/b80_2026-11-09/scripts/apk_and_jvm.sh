#!/bin/bash
# queue AC: B80's JVM mutations (in the working copy), the JVM suite in the APK tree, the APK twice, the baseline once.
# Offline, --no-configuration-cache; nothing installed; outputs under ~/.cache/b_q19ac_tmp/.
E="$1"; S=~/.cache/b_q19ac_tmp; export TMPDIR=$S
W=/tmp/b_q19ac_work/PrivyHub; A=/tmp/b_q19ac_apk/PrivyHub; O=/tmp/b_q19ac_apko/PrivyHub
M=$E/scripts/mutate_jvm.sh; T=com.safeiot.privyhub.streaming.B80Ps2PatchesTest; F=app/src/main/java/streaming/Ps2Patches.kt
{
bash $M $W $F $T J1 'fun showEntry(on: Boolean, available: List<String>): Boolean = on && known(available).isNotEmpty()' 'fun showEntry(on: Boolean, available: List<String>): Boolean = known(available).isNotEmpty()'
bash $M $W $F $T J2 '(if (patches) listOf(ENTRY_LABEL) else emptyList())' 'listOf(ENTRY_LABEL)'
bash $M $W $F $T J3 'val QUERY_NAMES = mapOf("ws" to "ws", "ni" to "ni", "60" to "fps60")' 'val QUERY_NAMES = mapOf("ws" to "ws", "ni" to "ni", "60" to "60")'
} > $S/jvm_mutations.txt 2>&1
(cd $A && timeout 1800 bash ./gradlew :app:testDebugUnitTest --offline --no-configuration-cache -q > $S/jvm_apk.log 2>&1; echo "rc=$?" >> $S/jvm_apk.log)
for n in 1 2; do
  (cd $A && timeout 1800 bash ./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache -q > $S/apk$n.log 2>&1; echo "rc=$?" >> $S/apk$n.log)
  mkdir -p $S/apk$n && cp $A/app/build/outputs/apk/debug/app-debug.apk $S/apk$n/
done
(cd $O && timeout 1800 bash ./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache -q > $S/apko.log 2>&1; echo "rc=$?" >> $S/apko.log)
mkdir -p $S/apko && cp $O/app/build/outputs/apk/debug/app-debug.apk $S/apko/
sha256sum $S/apk1/app-debug.apk $S/apk2/app-debug.apk $S/apko/app-debug.apk > $S/apk_sums.txt
echo ALLDONE >> $S/apk_sums.txt
