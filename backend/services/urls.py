from django.urls import path
from .views import AcademicLevelListView, ServiceTypeListView

urlpatterns = [
    path('levels/', AcademicLevelListView.as_view(), name='academic-levels'),
    path('types/', ServiceTypeListView.as_view(), name='service-types'),
]
