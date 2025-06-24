from django.urls import path

from . import views, api

urlpatterns = [
    path("", views.index, name="index"),
    path('recordings/', views.list_recordings, name='list_recordings'),
    path('clip-form/', views.clip_form, name='clip_form'),
    path('clip/', api.clip, name='clip'),
    path('frame/', api.frame, name='frame'),
]