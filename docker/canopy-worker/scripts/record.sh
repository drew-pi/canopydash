#!/bin/bash

## Usage
# bash scripts/record.sh [A|B]
## 

set -Eeuo pipefail

trap 'echo "[ERROR] line $LINENO: $BASH_COMMAND" >&2' ERR

# check to see if only one argument passed in
if [[ $# -ne 1 ]]; then
    echo "[ERROR] Invalid input, found $# parameters."
    exit 1
fi

if [[ "$1" =~ ^[AB]$ ]]; then
    CAMERA_ID="$1"
else
    echo "[ERROR] Invalid camera ID. Used ID $1 instead"
    exit 1
fi

: "${JETSON_IP:?set JETSON_IP (e.g. 10.0.0.50)}"
: "${SEGMENT_LEN:?set SEGMENT_LEN seconds (e.g. 300)}"
: "${RECORDINGS_PATH:?set RECORDINGS_PATH (e.g. /recordings)}"
: "${FILE_FMT:?set FILE_FMT (e.g. %Y-%m-%d_%H-%M-%S)}"

echo "[INFO] Recording camera $CAMERA_ID stream"
echo "[INFO] Using segment length=$SEGMENT_LEN"
echo "[INFO] Using jetson ip=$JETSON_IP"
echo "[INFO] Using data directory=$RECORDINGS_PATH"
echo "[INFO] Using file format=$FILE_FMT-$CAMERA_ID.mp4"

SAVE_DIR=$RECORDINGS_PATH

# making sure that the directory exists
mkdir -p $SAVE_DIR

echo "[INFO] Saving files to $SAVE_DIR"

for i in {1..10}; do
  # synchronize to next second
  sleep "$(awk "BEGIN {print 1 - ($(date +%s.%N) % 1)}")"

  echo -e "\n[INFO] Attempt $i/10 — starting aligned recording at $(date +%T.%3N)\n"

  if ffmpeg \
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
      "$SAVE_DIR/$FILE_FMT-$CAMERA_ID.mp4"; then
    echo "[INFO] FFmpeg exited cleanly on attempt $i"
    exit 0
  else
    echo -e "\n[WARN] FFmpeg exited unexpectedly at $(date). Retrying...\n"
    sleep 1
  fi
done

echo "[ERROR] FFmpeg failed after 10 attempts. Giving up."
exit 1

