from django.urls import path
from .views import DeadlineMultiplierListView

urlpatterns = [
    path('deadlines/', DeadlineMultiplierListView.as_view(), name='deadline-multipliers'),
]
