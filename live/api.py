from django.http import HttpResponse, JsonResponse, Http404
from django.conf import settings
from celery.result import AsyncResult

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import logging
import json

from .tasks import generate_clip_task
# extract_frame_task

logger = logging.getLogger(__name__)


def clip(request):
    start_ts = request.GET.get("start")
    end_ts = request.GET.get("end")
    camera = request.GET.get("camera", "BOTH")

    logger.info(f"Received clip request for camera {camera}: start={start_ts}, end={end_ts}")

    start_utc = datetime.fromisoformat(start_ts)
    end_dt = datetime.fromisoformat(end_ts)

    start_tz = start_utc.astimezone(ZoneInfo(settings.TIME_ZONE))
    end_tz = end_dt.astimezone(ZoneInfo(settings.TIME_ZONE))

    task = generate_clip_task.delay(start_tz, end_tz, camera)
    return JsonResponse({"task_id": task.id}, status=202)



def download_file(request, task_id):
    result = AsyncResult(task_id)

    if not result.ready():
        return HttpResponse(status=425)   # 425 Too Early

    file_name = result.result        
    file_path = Path("/tmp") / file_name  

    if not file_path.is_file():  
        raise Http404("File not found")

    # 3. Build the X-Accel-Redirect response
    resp = HttpResponse()
    resp["Content-Type"] = "application/octet-stream"
    resp["Content-Disposition"] = f'attachment; filename="{file_name}"'
    resp["X-Accel-Redirect"] = f"/serving/{file_name}"
    return resp






from .tasks import write_message_file, write_message_file


def trigger_write(request):
    message = request.GET.get("msg", "Hello world!")
    task = write_message_file.delay(message)
    return JsonResponse({"task_id": task.id})

def task_progress(request, task_id):
    
    print("Task progress: Using Redis DB", r.connection_pool.connection_kwargs.get("db"))

    data = r.get(f"progress:{task_id}")
    if data:
        return JsonResponse(json.loads(data))
    return JsonResponse({"status": "waiting", "progress": 0})


def get_result_message(request, task_id):
    result = AsyncResult(task_id)

    print("get_result_message: Using Redis DB", r.connection_pool.connection_kwargs.get("db"))

    print("this is the result", result)
    if result.ready():
        return JsonResponse({"status": "done", "message": result.result})
    return JsonResponse({"status": "pending"})


def download_result(request, task_id):
    result = AsyncResult(task_id)

    if not result.ready():
        return HttpResponse(status=425)   # 425 Too Early

    file_name = result.result        
    file_path = Path("/tmp") / file_name  

    if not file_path.is_file():  
        raise Http404("File not found")

    # 3. Build the X-Accel-Redirect response
    resp = HttpResponse()
    resp["Content-Type"] = "application/octet-stream"
    resp["Content-Disposition"] = f'attachment; filename="{file_name}"'
    resp["X-Accel-Redirect"] = f"/serving/{file_name}"
    return resp



# def clip(request):
#     start_ts = request.GET.get("start")
#     end_ts = request.GET.get("end")
#     camera = request.GET.get("camera", "BOTH")

#     logger.info(f"Received clip request for camera {camera}: start={start_ts}, end={end_ts}")

#     task = generate_clip_task.delay(start_ts, end_ts, camera)
#     return JsonResponse({"task_id": task.id}, status=202)


# def frame(request):
#     ts = request.GET.get("ts")
#     camera = request.GET.get("camera", "BOTH")

#     task = extract_frame_task.delay(ts, camera)
#     return JsonResponse({"task_id": task.id}, status=202)


# def task_progress(request, task_id):
#     data = r.get(f"progress:{task_id}")
#     if data:
#         return JsonResponse(json.loads(data))
#     return JsonResponse({"status": "unknown", "progress": 0})


# def get_task_result(request, task_id):
#     task = AsyncResult(task_id)

#     if task.state == "PENDING":
#         return JsonResponse({"status": "pending"}, status=202)

#     if task.state == "SUCCESS":
#         result_path = task.result
#         if result_path and os.path.exists(result_path):
#             return FileResponse(open(result_path, "rb"),
#                                 as_attachment=True,
#                                 filename=os.path.basename(result_path),
#                                 content_type="application/zip")
#         return JsonResponse({"status": "error", "message": "File not found"}, status=500)

#     if task.state == "FAILURE":
#         return JsonResponse({"status": "failed", "message": str(task.result)}, status=500)

#     return JsonResponse({"status": task.state})


# from django.http import HttpResponseBadRequest, FileResponse
# from django.conf import settings
# from celery import shared_task
# import redis
# import numpy as np

# from datetime import datetime
# import zipfile
# import json
# import os

# from .utils import create_clip, extract_frame


# def clip(request):
#     """
#     API route that returns a video recording from a specified start to end point
#     """

#     start_ts = request.GET.get("start")  # e.g., 2025-06-20T13:00:00
#     end_ts = request.GET.get("end")      # e.g., 2025-06-20T13:01:30
#     camera = request.GET.get("camera") # A, B or BOTH (assumes that if it is not A or B then want both)

#     logger.info(f"Received clip request for camera {camera}: start={start_ts}, end={end_ts}")
    
#     # convert to datetime objects
#     start = datetime.fromisoformat(start_ts)
#     end = datetime.fromisoformat(end_ts)

#     # used later for how long to record the concatenated video file
#     duration = (end - start).total_seconds()
#     start_offset = f"{start.strftime('00:00:%S')}"

#     start = start.replace(second=0, microsecond=0)
#     # start.replace(minute=0, second=0, microsecond=0)

#     logger.info(f"Start time aligned to boundry is {start}")

#     # make sure the end is after start
#     if start > end:
#         return HttpResponseBadRequest("ERROR IN /clip API ENPOINT: Start time must be before end time.")
    
#     RECORDINGS_PATH=settings.RECORDINGS_PATH
#     SEGMENT_LEN=settings.SEGMENT_LEN

#     raw_clips = np.arange(start, end, np.timedelta64(SEGMENT_LEN, "s"))

#     # paths
#     zip_path = f"/tmp/clip-AB-{start.isoformat().replace(':', '-')}.zip"
#     output_clipped_path_A = f"/tmp/{start.isoformat().replace(':', '-')}-cameraA.mp4"
#     output_clipped_path_B = f"/tmp/{start.isoformat().replace(':', '-')}-cameraB.mp4"

#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         if camera == "A":
#             create_clip(start, start_offset, duration, "A", RECORDINGS_PATH, raw_clips, output_clipped_path_A)
#             zipf.write(output_clipped_path_A, arcname="cameraA.mp4")
#         elif camera == "B":
#             create_clip(start, start_offset, duration, "B", RECORDINGS_PATH, raw_clips, output_clipped_path_B)
#             zipf.write(output_clipped_path_B, arcname="cameraB.mp4")
#         else: # both
#             create_clip(start, start_offset, duration, "A", RECORDINGS_PATH, raw_clips, output_clipped_path_A)
#             create_clip(start, start_offset, duration, "B", RECORDINGS_PATH, raw_clips, output_clipped_path_B)

#             zipf.write(output_clipped_path_A, arcname="cameraA.mp4")
#             zipf.write(output_clipped_path_B, arcname="cameraB.mp4")

#         # remove intermediate files after zipping (if they exist)
#         os.path.exists(output_clipped_path_A) and os.remove(output_clipped_path_A)
#         os.path.exists(output_clipped_path_B) and os.remove(output_clipped_path_B)

#     return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=os.path.basename(zip_path), content_type="application/zip")




# def frame(request):
#     """
#     API route that returns specified frame
#     """

#     ts = datetime.fromisoformat(request.GET.get("ts"))   
#     camera  = request.args.get("camera")  # default to camera A
    
#     RECORDINGS_PATH=settings.RECORDINGS_PATH
#     FILE_FMT=settings.FILE_FMT

#     output_frame_path_A = f"/tmp/{ts.isoformat().replace(':', '-')}-frameA.jpg"
#     output_frame_path_B = f"/tmp/{ts.isoformat().replace(':', '-')}-frameB.jpg"
#     zip_path = f"/tmp/frame-AB-{ts.isoformat().replace(':', '-')}.zip"

#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         if camera == "A":
#             extract_frame(ts, output_frame_path_A, "A", RECORDINGS_PATH, FILE_FMT)
#             zipf.write(output_frame_path_A, arcname="cameraA.jpg")
#         elif camera == "B":
#             extract_frame(ts, output_frame_path_B, "B", RECORDINGS_PATH, FILE_FMT)
#             zipf.write(output_frame_path_B, arcname="cameraB.jpg")
#         else: # both
#             extract_frame(ts, output_frame_path_A, "A", RECORDINGS_PATH, FILE_FMT)
#             extract_frame(ts, output_frame_path_B, "B", RECORDINGS_PATH, FILE_FMT)

#             zipf.write(output_frame_path_A, arcname="cameraA.jpg")
#             zipf.write(output_frame_path_B, arcname="cameraB.jpg")

#          # remove intermediate files after zipping (if they exist)
#         os.path.exists(output_frame_path_A) and os.remove(output_frame_path_A)
#         os.path.exists(output_frame_path_B) and os.remove(output_frame_path_B)

#     return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=os.path.basename(zip_path), content_type="application/zip")