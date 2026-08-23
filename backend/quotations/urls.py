from django.urls import path
from .views import CalculatePriceView, CreateQuotationView, QuotationListView, QuotationDetailView

urlpatterns = [
    path('calculate/', CalculatePriceView.as_view(), name='calculate-price'),
    path('create/', CreateQuotationView.as_view(), name='create-quotation'),
    path('list/', QuotationListView.as_view(), name='quotation-list'),
    path('<str:request_id>/', QuotationDetailView.as_view(), name='quotation-detail'),
]
