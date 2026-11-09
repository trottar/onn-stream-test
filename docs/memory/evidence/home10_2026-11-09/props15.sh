#!/bin/sh
# HOME-10: the fifteen client properties, read only (adb getprop; no setprop)
for p in restart_guard stall_signal link_notice link_report loss_guard wifi_lock opus_decode surface_hold pad_slots vod_retry player_prompt start_gate_rearm pointer_hide disc_change n64_card_top; do
  echo "debug.privyhub.$p=[$(adb shell getprop debug.privyhub.$p | tr -d '\r')]"
done
