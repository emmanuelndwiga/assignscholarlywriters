from django.urls import path
from . import views

app_name = "admin_panel"
urlpatterns = [
    path("", views.overview, name="overview"),
    path("users/", views.users, name="users"),
    path("analytics/", views.analytics, name="analytics"),
    path("reports/", views.reports, name="reports"),
]
