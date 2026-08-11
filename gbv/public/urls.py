from django.urls import path
from . import views

app_name = "public"
urlpatterns = [
    path("", views.submit_report, name="landing"),  # or a separate landing view
    path("report/", views.submit_report, name="submit"),
    path("track/", views.track_case, name="track"),
]