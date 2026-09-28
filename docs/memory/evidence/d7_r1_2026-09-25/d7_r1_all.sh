#!/bin/bash
# D7-R1: two full passes of tools/d7_regression.py, >= 10 minutes apart.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd /home/privyhub/Projects/onn-stream-test || exit 1
echo "[d7 $(date -u +%H:%M:%SZ)] pass P1"
python3 tools/d7_regression.py --out "$HERE" --pass-label P1
echo "[d7 $(date -u +%H:%M:%SZ)] P1 exit $?; waiting 10 min"
sleep 600
echo "[d7 $(date -u +%H:%M:%SZ)] pass P2"
python3 tools/d7_regression.py --out "$HERE" --pass-label P2
echo "[d7 $(date -u +%H:%M:%SZ)] P2 exit $?"
echo "[d7] done"
