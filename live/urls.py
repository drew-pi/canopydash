from django.urls import path

from . import views, api

urlpatterns = [
    path("", views.index, name="index"),
    path('recordings/', views.list_recordings, name='list_recordings'),
    path('clip-form/', views.clip_form, name='clip_form'),

    # paths for downloading a clip/frame
    path('clip/', views.load_recording, name='load_recording'),
    path('api/clip/', api.clip, name='clip'),
    # path('/api/frame/', api.frame, name='frame'),
    path("api/download/<str:task_id>/", api.download_file, name="download_file"),

    path("message/", views.message_page, name="message_page"),
    path("api/message/", api.trigger_write, name='trigger_write'),
    path("api/message/<str:task_id>/", api.get_result_message),
    path("api/progress/<str:task_id>/", api.task_progress),
    path("api/download/<str:task_id>/", api.download_result, name="download_result"),
]