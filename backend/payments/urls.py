from django.urls import path
from .views import CreatePaymentView, ExecutePaymentView

urlpatterns = [
    path('create/', CreatePaymentView.as_view(), name='create-payment'),
    path('execute/', ExecutePaymentView.as_view(), name='execute-payment'),
]
