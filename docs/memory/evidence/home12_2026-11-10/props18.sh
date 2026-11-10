#!/bin/sh
# HOME-12: the eighteen client properties, read only (adb getprop; no setprop) — HOME-11's seventeen + ps2_patches
for p in restart_guard stall_signal link_notice link_report loss_guard wifi_lock opus_decode surface_hold pad_slots vod_retry player_prompt start_gate_rearm pointer_hide disc_change n64_card_top paused_bar_fit disc_safe ps2_patches; do
  echo "debug.privyhub.$p=[$(adb shell getprop debug.privyhub.$p | tr -d '\r')]"
done
