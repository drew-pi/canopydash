from django.http import FileResponse, HttpResponseBadRequest
from django.conf import settings
import numpy as np

from datetime import datetime
import zipfile
import os

from .utils import create_clip, extract_frame


def clip(request):
    """
    API route that returns a video recording from a specified start to end point
    """

    start_ts = request.GET.get("start")  # e.g., 2025-06-20T13:00:00
    end_ts = request.GET.get("end")      # e.g., 2025-06-20T13:01:30
    camera = request.GET.get("camera") # A, B or BOTH (assumes that if it is not A or B then want both)

    # logging.info(f"Received clip request for camera {camera}: start={start_ts}, end={end_ts}")

    # convert to datetime objects
    start = datetime.fromisoformat(start_ts)
    end = datetime.fromisoformat(end_ts)

    # used later for how long to record the concatenated video file
    duration = (end - start).total_seconds()
    start_offset = f"{start.strftime('00:00:%S')}"

    start = start.replace(second=0, microsecond=0)
    # start.replace(minute=0, second=0, microsecond=0)

    # logging.info(f"Start time aligned to boundry is {start}")

    # make sure the end is after start
    if start > end:
        return HttpResponseBadRequest("ERROR IN /clip API ENPOINT: Start time must be before end time.")
    
    RECORDINGS_PATH=settings.RECORDINGS_PATH
    SEGMENT_LEN=settings.SEGMENT_LEN

    raw_clips = np.arange(start, end, np.timedelta64(SEGMENT_LEN, "s"))

    # paths
    zip_path = f"/tmp/clip-AB-{start.isoformat().replace(':', '-')}.zip"

    output_clipped_path_A = f"/tmp/{start.isoformat().replace(':', '-')}-cameraA.mp4"
    output_clipped_path_B = f"/tmp/{start.isoformat().replace(':', '-')}-cameraB.mp4"

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        if camera == "A":
            create_clip(start, start_offset, duration, "A", RECORDINGS_PATH, raw_clips, output_clipped_path_A)
            zipf.write(output_clipped_path_A, arcname="cameraA.mp4")
        elif camera == "B":
            create_clip(start, start_offset, duration, "B", RECORDINGS_PATH, raw_clips, output_clipped_path_B)
            zipf.write(output_clipped_path_B, arcname="cameraB.mp4")
        else: # both
            create_clip(start, start_offset, duration, "A", RECORDINGS_PATH, raw_clips, output_clipped_path_A)
            create_clip(start, start_offset, duration, "B", RECORDINGS_PATH, raw_clips, output_clipped_path_B)

            zipf.write(output_clipped_path_A, arcname="cameraA.mp4")
            zipf.write(output_clipped_path_B, arcname="cameraB.mp4")

        # remove intermediate files after zipping (if they exist)
        os.path.exists(output_clipped_path_A) and os.remove(output_clipped_path_A)
        os.path.exists(output_clipped_path_B) and os.remove(output_clipped_path_B)

    return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=os.path.basename(zip_path), content_type="application/zip")




def frame(request):
    """
    API route that returns specified frame
    """

    ts = datetime.fromisoformat(request.GET.get("ts"))   
    camera  = request.args.get("camera")  # default to camera A
    
    RECORDINGS_PATH=os.getenv("RECORDINGS_PATH", "/recordings")

    FILE_FMT='%Y-%m-%dT%H:%M:00.000000'
    # FILE_FMT=settings.FILE_FMT

    output_frame_path_A = f"/tmp/{ts.isoformat().replace(':', '-')}-frameA.jpg"
    output_frame_path_B = f"/tmp/{ts.isoformat().replace(':', '-')}-frameB.jpg"
    zip_path = f"/tmp/frame-AB-{ts.isoformat().replace(':', '-')}.zip"

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        if camera == "A":
            extract_frame(ts, output_frame_path_A, "A", RECORDINGS_PATH, FILE_FMT)
            zipf.write(output_frame_path_A, arcname="cameraA.jpg")
        elif camera == "B":
            extract_frame(ts, output_frame_path_B, "B", RECORDINGS_PATH, FILE_FMT)
            zipf.write(output_frame_path_B, arcname="cameraB.jpg")
        else: # both
            extract_frame(ts, output_frame_path_A, "A", RECORDINGS_PATH, FILE_FMT)
            extract_frame(ts, output_frame_path_B, "B", RECORDINGS_PATH, FILE_FMT)

            zipf.write(output_frame_path_A, arcname="cameraA.jpg")
            zipf.write(output_frame_path_B, arcname="cameraB.jpg")

         # remove intermediate files after zipping (if they exist)
        os.path.exists(output_frame_path_A) and os.remove(output_frame_path_A)
        os.path.exists(output_frame_path_B) and os.remove(output_frame_path_B)

    return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=os.path.basename(zip_path), content_type="application/zip")