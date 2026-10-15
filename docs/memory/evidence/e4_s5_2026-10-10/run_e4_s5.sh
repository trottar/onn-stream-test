#!/usr/bin/env bash
# E4-S5: §2 three 10-min SNES sessions (verbose RetroArch log via the counter override), then §3 SNES x2 at 20 min with
# PRIVYHUB_SNES_CAPTURE_FIX=output_rate; e4_s5_sidecar.py beside each phase.
set -u
R=/home/privyhub/Projects/onn-stream-test
D=$R/docs/memory/evidence/e4_s5_2026-10-10
cd "$R"
python3 $D/e4_s5_sidecar.py $D/runs_sessions > $D/sidecar_sessions.log 2>&1 &
E1_COUNTER_EXTRA='log_verbosity = "true"\nfrontend_log_level = "0"\n' python3 tools/e1_suite.py run --out $D/runs_sessions \
  --prereg $D/e4_s5_preregistration.txt --e2 --window 600 --gap 120 --plan "E1-SNES-STREAM:3:120" > $D/runs_sessions_console.log 2>&1
touch $D/runs_sessions/sidecar.stop; wait
python3 $D/e4_s5_sidecar.py $D/runs_flag > $D/sidecar_flag.log 2>&1 &
python3 tools/e1_suite.py run --out $D/runs_flag --prereg $D/e4_s5_preregistration.txt --e2 --window 1200 --gap 120 \
  --plan "E1-SNES-STREAM:2:120:PRIVYHUB_SNES_CAPTURE_FIX=output_rate" > $D/runs_flag_console.log 2>&1
touch $D/runs_flag/sidecar.stop; wait
echo done
