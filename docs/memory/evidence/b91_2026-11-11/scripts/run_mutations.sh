#!/bin/bash
# B91's JVM mutations, each applied once to the work copy's source, the class run, then restored.
S=$(dirname "$0")/mutate_jvm.sh; P=/tmp/b_q21ag_work/PrivyHub; C=com.safeiot.privyhub.streaming.B91MappingBesideTest
MP=app/src/main/java/streaming/MappingPicture.kt; ML=app/src/main/java/streaming/MappingEditorLayout.kt
$S $P $ML $C K1_label_text_smaller 'const val LABEL_TEXT_SP = ROW_TEXT_SP' 'const val LABEL_TEXT_SP = 11f'
$S $P $MP $C K2_no_overlap_check_against_placed '                placed.none { it.box.overlaps(b) } &&' '                true &&'
$S $P $MP $C K3_no_bounds_check '            b.x >= 0f && b.y >= 0f && b.x + b.w <= viewW && b.y + b.h <= viewH &&' '            true &&'
$S $P $MP $C K4_moved_label_without_leader '            if (found != null) placed += Placed(id, text, found, ax, ay, true, id in changed)' '            if (found != null) placed += Placed(id, text, found, ax, ay, false, id in changed)'
$S $P $ML $C K5_picture_above_again '        val beside = screenW > screenH' '        val beside = false'
$S $P $ML $C K6_rows_under_the_picture '        val besideRows = ((contentH - header) / row).coerceAtLeast(0)' '        val besideRows = ((contentH - header - pictureH) / row).coerceAtLeast(0)'
$S $P $MP $C K7_switch_ignored '    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }' '    fun parse(value: String?): Boolean = true'
