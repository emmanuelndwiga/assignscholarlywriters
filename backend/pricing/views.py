from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import DeadlineMultiplier, PricingSeason
from .serializers import DeadlineMultiplierSerializer, PricingSeasonSerializer


class DeadlineMultiplierListView(generics.ListAPIView):
    queryset = DeadlineMultiplier.objects.filter(is_active=True)
    serializer_class = DeadlineMultiplierSerializer
    permission_classes = [AllowAny]
    pagination_class = None
