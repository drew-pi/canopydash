#!/bin/bash
set -euo pipefail
trap 'echo "[ERROR] Command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

# local env variables (inside of container)
export RECORDINGS_DIR="/recordings"
LOGGING_DIR="/logs"

mkdir -p $RECORDINGS_DIR
mkdir -p  /var/www/hls
mkdir -p  $LOGGING_DIR


echo "[INFO] Starting FFmpeg live jobs"

setsid bash scripts/live.sh /dev/video0 A > "$LOGGING_DIR/live_cameraA.log" 2>&1 &
live_pid_A=$!
echo "Started background live process A with pid $live_pid_A"

setsid bash scripts/live.sh /dev/video1 B > "$LOGGING_DIR/live_cameraB.log" 2>&1 &
live_pid_B=$!
echo "Started background live process B with pid $live_pid_B"

sleep 1

echo "[INFO] Starting FFmpeg record jobs"

setsid bash scripts/record.sh A > $LOGGING_DIR/record_cameraA.log 2>&1 &
rec_pid_A=$!
echo "[INFO] Started background recording process A with pid $rec_pid_A"

setsid bash scripts/record.sh B > $LOGGING_DIR/record_cameraB.log 2>&1 &
rec_pid_B=$!
echo "[INFO] Started background recording process B with pid $rec_pid_B"

# Keep the container alive
# wait $live_pid_A $live_pid_B $rec_pid_A $rec_pid_B
tail -f /logs/*.log


