#!/bin/bash

## Usage
# bash scripts/record.sh [A|B]
## 

set -Eeuo pipefail

trap 'echo "[ERROR] line $LINENO: $BASH_COMMAND" >&2' ERR

: "${JETSON_IP:?set JETSON_IP (e.g. 10.0.0.50)}"
: "${SEGMENT_LEN:?set SEGMENT_LEN seconds (e.g. 300)}"
: "${RECORDINGS_PATH:?set RECORDINGS_PATH (e.g. /recordings)}"
: "${FILE_FMT:?set FILE_FMT (e.g. %Y-%m-%d_%H-%M-%S)}"

# check to see if only one argument passed in
if [[ $# -ne 1 || ! "$1" =~ ^[01]$ ]]; then
    echo "[ERROR] Invalid input. Usage: $0 [0|1]" >&2
    exit 1
fi

CAMERA_ID="$1"


echo "[INFO] Recording camera $CAMERA_ID stream"
echo "[INFO] Using segment length=$SEGMENT_LEN"
echo "[INFO] Using jetson ip=$JETSON_IP"
echo "[INFO] Using data directory=$RECORDINGS_PATH"
echo "[INFO] Using file format=$FILE_FMT-$CAMERA_ID.mp4"

SAVE_DIR=$RECORDINGS_PATH

# making sure that the directory exists
mkdir -p $SAVE_DIR

echo "[INFO] Saving files to $SAVE_DIR"

sleep "$(awk "BEGIN {print 1 - ($(date +%s.%N) % 1)}")"

echo -e "\n[INFO] Starting aligned recording at $(date +%T.%3N)\n"


ffmpeg \
      -rw_timeout 15000000 \
      -f flv \
      -i "rtmp://$JETSON_IP/live/stream${CAMERA_ID}" \
      -c copy \
      -f segment \
      -segment_time "$SEGMENT_LEN" \
      -segment_atclocktime 1 \
      -strftime 1 \
      -reset_timestamps 1 \
      -movflags +faststart \
      -loglevel info \
      "$SAVE_DIR/$FILE_FMT-$CAMERA_ID.mp4"

echo -e "\n[WARN] FFmpeg exited unexpectedly at $(date +%T.%3N). Retrying...\n"


MAX_RETRIES=5

for attempt in $(seq 1 $MAX_RETRIES); do
    sleep "$(awk "BEGIN {print 0.99 - ($(date +%s.%N) % 1)}")"

    echo "[INFO] Attempt $attempt of $MAX_RETRIES at $(date +%T.%3N)"

    ffmpeg \
        -rw_timeout 15000000 \
        -f flv \
        -i "rtmp://$JETSON_IP/live/stream${CAMERA_ID}" \
        -c copy \
        -f segment \
        -segment_time "$SEGMENT_LEN" \
        -segment_atclocktime 1 \
        -strftime 1 \
        -reset_timestamps 1 \
        -movflags +faststart \
        -loglevel info \
        "$SAVE_DIR/$FILE_FMT-$CAMERA_ID.mp4" && break

    echo -e "\n[WARN] FFmpeg exited unexpectedly at $(date +%T.%3N). Retrying ($attempt/$MAX_RETRIES)...\n"

done