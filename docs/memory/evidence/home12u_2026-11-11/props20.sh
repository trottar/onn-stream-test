#!/bin/sh
# HOME-12U (copied from HOME-12T): the twenty client properties, read only (adb getprop; no setprop) — HOME-12's eighteen + cheat_picker, mapping_picture
for p in restart_guard stall_signal link_notice link_report loss_guard wifi_lock opus_decode surface_hold pad_slots vod_retry player_prompt start_gate_rearm pointer_hide disc_change n64_card_top paused_bar_fit disc_safe ps2_patches cheat_picker mapping_picture; do
  echo "debug.privyhub.$p=[$(adb shell getprop debug.privyhub.$p | tr -d '\r')]"
done
