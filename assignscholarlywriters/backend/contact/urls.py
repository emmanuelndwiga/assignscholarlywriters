from django.urls import path
from .views import CreateContactView

urlpatterns = [
    path('', CreateContactView.as_view(), name='create-contact'),
]
