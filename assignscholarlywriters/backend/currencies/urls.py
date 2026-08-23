from django.urls import path
from .views import CurrencyListView

urlpatterns = [
    path('', CurrencyListView.as_view(), name='currencies'),
]
