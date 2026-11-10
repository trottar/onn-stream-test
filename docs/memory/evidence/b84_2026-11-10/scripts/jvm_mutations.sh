#!/bin/bash
# queue AE: B84's and B86's JVM mutations in the working copy (each restored after its run).
W=/tmp/b_q20ae_work/PrivyHub; E=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence
M=$E/b84_2026-11-10/scripts/mutate_jvm.sh
T=com.safeiot.privyhub.streaming.B84CheatPickerTest; F=app/src/main/java/streaming/CheatPicker.kt
{
bash $M $W $F $T J1 '                if (focus == 0) {
                    barButton = 0
                } else {' '                if (true) {
                    barButton = 0
                } else {'
bash $M $W $F $T J2 '            PickerKey.START -> return PickerAction.LAUNCH' '            PickerKey.START -> return PickerAction.NONE'
bash $M $W $F $T J3 '                val open = group in opened' '                val open = true'
bash $M $W $F $T J4 '                if (focus == 1) toggleSelectedOnly()          // the filter row: Right = "Selected only" on / off' ''
bash $M $W $F $T J5 '        return words.all { it in label }' '        return words.any { it in label }'
bash $M $W $F $T J6 '                if (focus > 1) moveTo((focus - pageSize).coerceAtLeast(2))' '                moveTo(focus - pageSize)'
} > $E/b84_2026-11-10/tests_mutations_jvm.txt 2>&1
T=com.safeiot.privyhub.streaming.B86MappingPictureTest; F=app/src/main/java/streaming/MappingPicture.kt
{
bash $M $W $F $T K1 '"a" to "Bottom (✕)", "b" to "Right (○)", "x" to "Left (□)", "y" to "Top (△)",' '"a" to "A", "b" to "B", "x" to "X", "y" to "Y",'
bash $M $W $F $T K2 '        for ((s, labels) in sends) out[s] = labels.joinToString("+")' '        for ((s, labels) in sends) out[s] = labels.first()'
bash $M $W $F $T K3 '        return now.keys.filter { now[it] != before[it] }.toSet()' '        return emptySet()'
bash $M $W $F $T K4 '        "${if (source.isNullOrBlank()) "nothing" else padLabel(source)} → ${gameLabel(target)}"' '        "${gameLabel(target)} ← ${if (source.isNullOrBlank()) "nothing" else gameLabel(source)}"'
} > $E/b86_2026-11-10/tests_mutations_jvm.txt 2>&1
echo JVMMUTDONE
