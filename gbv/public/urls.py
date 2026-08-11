from django.urls import path
from . import views

app_name = "public"
urlpatterns = [
    path("", views.landing, name="landing"),
    path("report/", views.submit_report, name="submit"),
    path("track/", views.track_case, name="track"),
    path("track/<int:pk>/reply/", views.reply_to_case, name="reply"),
    path("push/subscribe/", views.push_subscribe, name="push_subscribe"),
    path("sw.js", views.service_worker, name="service_worker"),
]