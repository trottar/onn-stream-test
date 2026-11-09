#!/bin/sh
# HOME-11: the seventeen client properties, read only (adb getprop; no setprop) — HOME-10's fifteen + paused_bar_fit, disc_safe
for p in restart_guard stall_signal link_notice link_report loss_guard wifi_lock opus_decode surface_hold pad_slots vod_retry player_prompt start_gate_rearm pointer_hide disc_change n64_card_top paused_bar_fit disc_safe; do
  echo "debug.privyhub.$p=[$(adb shell getprop debug.privyhub.$p | tr -d '\r')]"
done
