from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery import shared_task
import redis
import numpy as np

from datetime import datetime
import logging
import zipfile
import json
import os

from .utils import create_clip, extract_frame

r = redis.Redis.from_url(settings.CELERY_BROKER_URL)







import time


@shared_task(bind=True)
def write_message_file(self, message):
    task_id = self.request.id

    # access global channels layer — enables communication with WebSocket consumers
    channel_layer = get_channel_layer()

    for step, msg in enumerate(["Initializing", "Writing", "Finalizing"]):
        time.sleep(5)

        print(f"{msg}: Using Redis DB", r.connection_pool.connection_kwargs.get("db"))

        # sends progress update message to the WebSocket group with this task ID
        async_to_sync(channel_layer.group_send)(
            f"progress_{task_id}",
            {
                "type": "update", # calls the 'update' method on all connected consumers
                "data": {
                    "status": msg,             
                    "progress":  int((step + 1) / 3 * 100) - 1      
                }
            }
        )

    file_name = f"{datetime.now().strftime("%Y%m%dT%H%M%S")}-msg.txt"
    output_file_path = f"/tmp/{file_name}"

    print(f"This is the message: {message}")

    with open(output_file_path, "w") as f:
        f.write(message)

    print("Done: Using Redis DB", r.connection_pool.connection_kwargs.get("db"))

    # sends progress update message to the WebSocket group with this task ID
    async_to_sync(channel_layer.group_send)(
        f"progress_{task_id}",
        {
            "type": "update", # calls the 'update' method on all connected consumers
            "data": {
                "status": "Done",             
                "progress":  100,
                "file": file_name  
            }
        }
    )
    return file_name


# logger = logging.getLogger(__name__)


# @shared_task(bind=True)
# def generate_clip_task(self, start_ts, end_ts, camera):
#     """
#     Celery task to generate a video clip for one or both cameras over a given time range.

#     Steps:
#     - Computes the duration and starting offset based on the timestamps.
#     - Identifies which video segments (raw_clips) are needed from the filesystem.
#     - Uses helper function `create_clip` to concatenate and trim video for camera(s).
#     - Packages the resulting .mp4(s) into a single .zip archive for download.
#     - Cleans up intermediate clip files after writing to the zip.

#     Parameters:
#         start_ts (str): ISO-format string indicating the clip start time.
#         end_ts (str): ISO-format string indicating the clip end time.
#         camera (str): One of 'A', 'B', or 'BOTH' to select which camera(s) to include.

#     Returns:
#         str: The full path to the resulting ZIP archive containing the clip(s).
#     """

#     # Compute duration and align start time to segment boundary
#     start = datetime.fromisoformat(start_ts)
#     end = datetime.fromisoformat(end_ts)
#     duration = (end - start).total_seconds()
#     start_offset = f"{start.strftime('00:00:%S')}"
#     start = start.replace(second=0, microsecond=0)

#     logger.debug(f"Start time aligned to boundry is {start}")

#     r.set(f"progress:{self.request.id}", json.dumps({"progress": 5, "step": "Computed aligned start time, duration, and starting offset"}))

#     RECORDINGS_PATH = settings.RECORDINGS_PATH
#     SEGMENT_LEN = settings.SEGMENT_LEN

#     # Generate list of raw segments spanning the clip duration
#     raw_clips = np.arange(start, end, np.timedelta64(SEGMENT_LEN, "s")).tolist()

#     r.set(f"progress:{self.request.id}", json.dumps({"progress": 10, "step": "Generated list of raw video segments"}))

#     zip_path = f"/tmp/clip-AB-{start.isoformat().replace(':', '-')}.zip"
#     output_A = f"/tmp/{start.isoformat().replace(':', '-')}-cameraA.mp4"
#     output_B = f"/tmp/{start.isoformat().replace(':', '-')}-cameraB.mp4"

#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         if camera == "A":
#             create_clip(start, start_offset, duration, "A", RECORDINGS_PATH, raw_clips, output_A)
#             zipf.write(output_A, arcname="cameraA.mp4")
#         elif camera == "B":
#             create_clip(start, start_offset, duration, "B", RECORDINGS_PATH, raw_clips, output_B)
#             zipf.write(output_B, arcname="cameraB.mp4")
#         else:
#             create_clip(start, start_offset, duration, "A", RECORDINGS_PATH, raw_clips, output_A)
#             create_clip(start, start_offset, duration, "B", RECORDINGS_PATH, raw_clips, output_B)
#             zipf.write(output_A, arcname="cameraA.mp4")
#             zipf.write(output_B, arcname="cameraB.mp4")

#     # Remove temporary files
#     os.remove(output_A) if os.path.exists(output_A) else None
#     os.remove(output_B) if os.path.exists(output_B) else None

#     return zip_path


# @shared_task(bind=True)
# def extract_frame_task(self, ts_str, camera):
#     """
#     Celery task to extract a single frame from one or both camera feeds at a given timestamp.

#     Steps:
#     - Converts the timestamp to datetime and formats it for filename lookup.
#     - Calls the `extract_frame` helper to extract a high-quality JPEG from the relevant video segment.
#     - Packages one or both resulting images into a ZIP archive.
#     - Cleans up temporary image files after zipping.

#     Parameters:
#         ts_str (str): ISO-format string indicating the timestamp to extract the frame from.
#         camera (str): One of 'A', 'B', or 'BOTH' to select which camera(s) to extract from.

#     Returns:
#         str: The full path to the resulting ZIP archive containing the frame(s).
#     """
    
#     ts = datetime.fromisoformat(ts_str)
#     RECORDINGS_PATH = settings.RECORDINGS_PATH
#     FILE_FMT = settings.FILE_FMT

#     # Format filenames for output images and zip archive
#     output_A = f"/tmp/{ts.isoformat().replace(':', '-')}-frameA.jpg"
#     output_B = f"/tmp/{ts.isoformat().replace(':', '-')}-frameB.jpg"
#     zip_path = f"/tmp/frame-AB-{ts.isoformat().replace(':', '-')}.zip"

#     r.set(f"progress:{self.request.id}", json.dumps({"progress": 40, "step": "Completed all preliminary steps beginning clip finding step"}))

#     # Extract and zip frame(s) based on camera selection
#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         if camera == "A":
#             extract_frame(ts, output_A, "A", RECORDINGS_PATH, FILE_FMT)
#             zipf.write(output_A, arcname="cameraA.jpg")
#         elif camera == "B":
#             extract_frame(ts, output_B, "B", RECORDINGS_PATH, FILE_FMT)
#             zipf.write(output_B, arcname="cameraB.jpg")
#         else:
#             extract_frame(ts, output_A, "A", RECORDINGS_PATH, FILE_FMT)
#             extract_frame(ts, output_B, "B", RECORDINGS_PATH, FILE_FMT)
#             zipf.write(output_A, arcname="cameraA.jpg")
#             zipf.write(output_B, arcname="cameraB.jpg")

#     # Remove temporary files
#     os.remove(output_A) if os.path.exists(output_A) else None
#     os.remove(output_B) if os.path.exists(output_B) else None

#     return zip_path