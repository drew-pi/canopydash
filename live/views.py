from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

import os

def index(request):
    return render(request, "viewer.html", {
        "ip": settings.JETSON_IP,
        "cameras": ["A", "B"],
    })

def list_recordings(request):
    files = sorted(os.listdir(settings.RECORDINGS_PATH))
    return JsonResponse(files, safe=False)

def clip_form(request):
    return render(request, "_clip.html")

def message_page(request):
    return render(request, "message.html")

def load_recording(request):
    return render(request, "clip.html")


    