from django.urls import path
from .views import SampleListView, SampleDetailView

urlpatterns = [
    path('', SampleListView.as_view(), name='sample-list'),
    path('<int:pk>/', SampleDetailView.as_view(), name='sample-detail'),
]
