from django.http import HttpResponseBadRequest
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import redis

import os
import subprocess
import logging
import json

r = redis.Redis.from_url(settings.CELERY_BROKER_URL)

logger = logging.getLogger(__name__)



def ws_update(id, **data):
    """
    Sends a websocket update to all listeners in the group "progress_<task_id>".
    Accepts arbitrary keyword arguments to populate the data payload.
    Example:
        ws_update(task_id, status="Started", progress=50)
    """

    # access global channels layer — enables communication with WebSocket consumers
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"progress_{id}",
        {
            "type": "update",  # Triggers the `update` method in the consumer
            "data": data      
        }
    )
        

def create_clip(task, start, start_offset, duration, camera, RECORDINGS_PATH, raw_clips, output_clipped_path):
    """
    Generates a video clip of specified duration from a sequence of raw video segments.

    This helper function is used by the /clip API endpoint to:
      - Concatenate a set of raw video files recorded by a specific camera
      - Trim the concatenated video to the exact desired clip using start offset and duration
      - Clean up all intermediate files created during processing

    Parameters:
        start (datetime): The timestamp representing the start of the clip request (used in filenames).
        start_offset (str): The offset (in format 'HH:MM:SS' or seconds) from the start of the concatenated video where the clip should begin.
        duration (float or str): The length of the final video clip in seconds.
        camera (str): The camera identifier (e.g., 'A', 'B') used in naming the input and output files.
        RECORDINGS_PATH (str): Directory path where raw video recordings are stored.
        raw_clips (List[str]): List of timestamp strings representing the raw segment filenames (without extensions).
        output_clipped_path (str): Full path to the final output video clip.

    Raises:
        subprocess.CalledProcessError: If ffmpeg fails during concatenation or trimming.

    Side Effects:
        Creates temporary intermediate files under /tmp and deletes them after the final clip is saved.
    """

    task_id = task.request.id

    # file names
    clip_files_path = f"/tmp/concat_list_{camera}_{start.isoformat().replace(':', '-')}.txt"
    full_clip_path = f"/tmp/full_clip-{camera}-{start.isoformat().replace(':', '-')}.mp4"

    clip_full_file_names = [os.path.join(RECORDINGS_PATH, f"{_clip}-{camera}.mp4") for _clip in raw_clips]

    logger.debug(f"Clips that are needed: {clip_full_file_names}")

    valid_clip_full_file_names = [f"file '{p}'" for p in clip_full_file_names if os.path.isfile(p)]

    logger.debug(f"Missing {len(clip_full_file_names) - len(valid_clip_full_file_names)} clips")

    valid_clip_files = "\n".join(valid_clip_full_file_names)

    with open(clip_files_path, "w") as f:
        f.write(valid_clip_files)

    ws_update(task_id, status="Starting process of concatenated video clips together", progress=15)

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", clip_files_path,
        "-c", "copy",
        "-y",
        full_clip_path
    ]

    subprocess.run(cmd, check=True)

    logger.debug(f"Concatenated {len(valid_clip_full_file_names)} existing clips into {full_clip_path}")

    ws_update(task_id, status="Finished concatenating video clips, beginning trimming of full clip", progress=50)

    cmd = [
        "ffmpeg",
        "-ss", start_offset,
        # "-ss", f"{start.strftime('00:%M:%S')}", # use when SEGMENT_LEN=3600 because also have to worry about minutes
        "-i", full_clip_path,
        "-t", str(duration),
        "-c", "copy",
        "-y", # answer yes to any pop ups
        output_clipped_path
    ]

    subprocess.run(cmd, check=True)

    ws_update(task_id, status="Finished trimming full clip, cleaning up temporary files and zipping", progress=95)

    # remove intermediate steps (if they exist)
    os.path.exists(clip_files_path) and os.remove(clip_files_path)
    os.path.exists(full_clip_path) and os.remove(full_clip_path)


def extract_frame(task, timestamp, output_path, camera, RECORDINGS_PATH, FILE_FMT):
    """
    Extracts a single video frame from a recorded segment at the specified timestamp.

    This helper function supports the /frame API endpoint by:
      - Locating the corresponding video segment based on timestamp and camera
      - Using ffmpeg to extract a high-quality single frame at the specified second
      - Writing the resulting image to the output path
      - Logging the operation and ensuring the segment exists

    Parameters:
        timestamp (datetime): The timestamp indicating which second of the video to extract the frame from.
        output_path (str): The full path where the extracted image will be saved.
        camera (str): The camera identifier (e.g., 'A', 'B') used in the video file naming convention.
        RECORDINGS_PATH (str): Directory where raw video segments are stored.
        FILE_FMT (str): Format string used to convert `timestamp` to the video filename prefix.

    Raises:
        werkzeug.exceptions.HTTPException: Returns a 404 error if the video segment is not found.
        subprocess.CalledProcessError: If ffmpeg fails to extract the frame.

    Notes:
        This function currently extracts only the second-level portion of the timestamp (`00:00:SS`).
        If segments span longer (e.g., 1 hour), the logic for formatting `-ss` will need to be updated accordingly.
    """
    
    path = os.path.join(RECORDINGS_PATH, f"{timestamp.strftime(FILE_FMT)}-{camera}.mp4")

    if not os.path.isfile(path):
        return HttpResponseBadRequest(f"Video segment for timestamp {timestamp} and camera {camera} not found.")
    
    r.set(f"progress:{task.request.id}", json.dumps({"progress": 80, "step": "Getting frame from correct clip"}))

    cmd  = [
        "ffmpeg", 
        "-ss", f"{timestamp.strftime('00:00:%S')}",
        # "-ss", f"{start.strftime('00:%M:%S')}", # use when SEGMENT_LEN=3600 because also have to worry about minutes
        "-i", str(path),
        "-frames:v", "1", 
        "-q:v", "2", 
        "-y", 
        output_path
    ]
    subprocess.run(cmd, check=True)

    r.set(f"progress:{task.request.id}", json.dumps({"progress": 95, "step": "Captured frame, cleaning up temporary files and zipping"}))

    logger.debug(f"Sucessfully captured frame {path} and loaded into {output_path}")