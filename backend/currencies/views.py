from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Currency
from .serializers import CurrencySerializer


class CurrencyListView(generics.ListAPIView):
    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    permission_classes = [AllowAny]
    pagination_class = None
