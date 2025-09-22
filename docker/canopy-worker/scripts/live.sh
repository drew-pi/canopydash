#!/bin/bash

## Usage
# bash scripts/live.sh [0|1]
## 

set -euo pipefail
trap 'echo "[ERROR] Command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

: "${JETSON_IP:?set JETSON_IP (e.g. 10.0.0.50)}"
: "${SEGMENT_LEN:?set SEGMENT_LEN seconds (e.g. 300)}"
: "${FRAME_RATE:?set FRAME_RATE (e.g. 30)}"

if [[ "$#" -ne 1 || ! "$1" =~ ^[01]$ ]]; then
    echo "[ERROR] Usage: $0 [0|1]" >&2
    exit 1
fi

CAMERA_ID="$1"
CAMERA="/dev/video${CAMERA_ID}"

echo "[INFO] Using framerate=$FRAME_RATE"
echo "[INFO] Using camera $CAMERA_ID with source=$CAMERA"
echo "[INFO] Using segment length=$SEGMENT_LEN"
echo "[INFO] Using jetson ip=$JETSON_IP"

echo "[INFO] beginning live camera$CAMERA_ID feed"

ffmpeg -re -f v4l2 -fflags +discardcorrupt \
    -input_format mjpeg -video_size 1280x960 -framerate "$FRAME_RATE" \
    -use_wallclock_as_timestamps 1 \
    -i "$CAMERA" \
    -vf "format=yuv420p,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:
       text='%{localtime}':x=10:y=10:fontsize=32:fontcolor=white:box=1:boxcolor=black@0.5" \
    -c:v libx264 -preset medium -crf 25 -tune zerolatency \
    -g 1 -keyint_min 1 -sc_threshold 0 \
    -force_key_frames "expr:gte(t,n_forced*${SEGMENT_LEN})" \
    -movflags +faststart -an \
    -loglevel warning \
    -f flv "rtmp://$JETSON_IP/live/stream${CAMERA_ID}"