from django.urls import path
from . import views

app_name = "cases"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("<int:pk>/", views.case_detail, name="detail"),
    path("<int:pk>/status/", views.update_status, name="update_status"),
    path("<int:pk>/escalate/", views.escalate, name="escalate"),
]