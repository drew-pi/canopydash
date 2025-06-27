from django.urls import path

from . import views, api

urlpatterns = [
    path("", views.index, name="index"),
    path('recordings/', views.list_recordings, name='list_recordings'),
    path('clip-form/', views.clip_form, name='clip_form'),
    # path('clip/', api.clip, name='clip'),
    # path('frame/', api.frame, name='frame'),

    path("message/", views.message_page, name="message_page"),
    path("api/message/", api.trigger_write, name='trigger_write'),
    path("api/message/<str:task_id>/", api.get_result_message),
    path("api/progress/<str:task_id>/", api.task_progress),

    path("api/download/<str:task_id>/", api.download_result, name="download_result"),
]